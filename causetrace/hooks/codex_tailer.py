"""OpenAI Codex CLI log tailer: extracts tool calls from Codex session logs.

Codex CLI stores per-session structured logs as JSONL files at:
    $CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl

CODEX_HOME defaults to ~/.codex if not set.

Usage:
    from causetrace.hooks.codex_tailer import scan_logs
    events = scan_logs()
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from causetrace.core import ToolEvent, TraceRecorder
from causetrace.causality import infer_relations

CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
_SESSION_DIR = CODEX_HOME / "sessions"

# Map Codex action names to causetrace tool names
_ACTION_MAP: Dict[str, str] = {
    "bash": "Bash",
    "shell": "Bash",
    "command": "Bash",
    "run": "Bash",
    "exec_command": "Bash",
    "read": "Read",
    "read_file": "Read",
    "view": "Read",
    "write": "Write",
    "write_file": "Write",
    "create": "Write",
    "edit": "Edit",
    "edit_file": "Edit",
    "apply_patch": "Edit",
    "search": "Grep",
    "grep": "Grep",
    "glob": "Glob",
    "web_fetch": "WebFetch",
    "web_search": "WebSearch",
    "fetch": "WebFetch",
    "web": "WebFetch",
    "think": "Reasoning",
    "reason": "Reasoning",
}


def _normalize_action(name: str) -> str:
    """Map Codex action names to causetrace tool names."""
    key = name.lower().strip().replace(" ", "_").replace("-", "_")
    return _ACTION_MAP.get(key, name)


def _find_session_dirs() -> List[Path]:
    """Find Codex session directories, newest first."""
    if not _SESSION_DIR.exists():
        return []
    # Walk YYYY/MM/DD directories
    dirs: List[Path] = []
    for year_dir in sorted(_SESSION_DIR.iterdir(), reverse=True):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        for month_dir in sorted(year_dir.iterdir(), reverse=True):
            if not month_dir.is_dir() or not month_dir.name.isdigit():
                continue
            for day_dir in sorted(month_dir.iterdir(), reverse=True):
                if not day_dir.is_dir() or not day_dir.name.isdigit():
                    continue
                dirs.append(day_dir)
    return dirs


def _find_rollout_files(max_sessions: int = 5) -> List[Path]:
    """Find rollout JSONL files from recent sessions."""
    files: List[Path] = []
    for session_dir in _find_session_dirs()[:max_sessions]:
        for f in sorted(session_dir.glob("rollout*.jsonl"), reverse=True):
            files.append(f)
    return files


def _parse_jsonl_line(line: str) -> Optional[dict]:
    """Parse a JSONL line."""
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def _parse_new_format(entry: dict) -> Optional[dict]:
    """Parse Codex v0.130.0+ response_item format.

    New format splits tool calls across response_item entries:
      {"type": "response_item", "payload": {"type": "function_call", "name": "...", "arguments": "{...}", "call_id": "..."}}
      {"type": "response_item", "payload": {"type": "function_call_output", "call_id": "...", "output": "..."}}
      {"type": "response_item", "payload": {"type": "custom_tool_call", "status": "completed", "call_id": "...", "name": "...", "input": "..."}}
      {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "...", "output": "..."}}

    Returns dict with kind/call_id/tool_name/tool_input/tool_output, or None.
    """
    if entry.get("type") != "response_item":
        return None

    payload = entry.get("payload", {})
    ptype = payload.get("type", "")

    if ptype == "function_call":
        name = payload.get("name", "")
        args_str = payload.get("arguments", "{}")
        try:
            args = json.loads(args_str) if isinstance(args_str, str) else args_str
        except json.JSONDecodeError:
            args = {"raw": args_str}
        return {
            "kind": "call",
            "call_id": payload.get("call_id", ""),
            "tool_name": _normalize_action(name),
            "tool_input": args if isinstance(args, dict) else str(args),
            "timestamp": entry.get("timestamp"),
        }

    if ptype == "function_call_output":
        return {
            "kind": "output",
            "call_id": payload.get("call_id", ""),
            "tool_output": payload.get("output", ""),
        }

    if ptype == "custom_tool_call":
        name = payload.get("name", "")
        inp = payload.get("input", payload.get("arguments", {}))
        return {
            "kind": "call",
            "call_id": payload.get("call_id", ""),
            "tool_name": _normalize_action(name),
            "tool_input": inp if isinstance(inp, dict) else str(inp),
            "timestamp": entry.get("timestamp"),
        }

    if ptype == "custom_tool_call_output":
        return {
            "kind": "output",
            "call_id": payload.get("call_id", ""),
            "tool_output": payload.get("output", ""),
        }

    return None


def _extract_codex_tool_call(entry: dict) -> Optional[Tuple[str, dict, str]]:
    """Extract (tool_name, tool_input, tool_output) from a Codex log entry.

    Codex logs have actions and observations:
      {"type": "action", "action": {"name": "Bash", "input": {...}}}
      {"type": "observation", "observation": {"name": "Bash", "output": {...}}}
    """
    entry_type = entry.get("type", "")

    if entry_type == "action":
        action = entry.get("action") or entry.get("content") or {}
        if isinstance(action, dict):
            name = action.get("name") or action.get("function") or action.get("tool") or ""
            inp = action.get("input") or action.get("arguments") or action.get("args") or {}
            if name:
                return _normalize_action(str(name)), inp, ""

    if entry_type == "observation":
        obs = entry.get("observation") or entry.get("content") or {}
        if isinstance(obs, dict):
            name = obs.get("name") or obs.get("function") or ""
            out = obs.get("output") or obs.get("result") or obs.get("content") or ""
            if name:
                return _normalize_action(str(name)), {}, str(out)

    # Fallback: try role/content structure (some Codex versions)
    role = entry.get("role", "")
    content = entry.get("content", "")
    if role == "assistant" and isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                name = item.get("type") or item.get("name") or ""
                if name:
                    inp = item.get("input") or item.get("arguments") or {}
                    return _normalize_action(str(name)), inp, ""

    # Direct tool call field
    tool = entry.get("tool") or entry.get("tool_call") or {}
    if isinstance(tool, dict):
        name = tool.get("name") or tool.get("function") or ""
        inp = tool.get("input") or tool.get("arguments") or tool.get("args") or {}
        out = tool.get("output") or tool.get("result") or ""
        if name:
            return _normalize_action(str(name)), inp, str(out)

    return None


def _parse_timestamp(entry: dict) -> Optional[str]:
    """Extract ISO timestamp from a Codex log entry."""
    ts = entry.get("timestamp") or entry.get("time") or entry.get("createdAt") or entry.get("ts")
    if not ts:
        return None
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts).isoformat()
        return str(ts)
    except (ValueError, OSError):
        return str(ts)


def _entry_fingerprint(entry: dict) -> str:
    """Return a stable fingerprint for a parsed Codex log entry."""
    payload = json.dumps(entry, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def scan_logs(max_sessions: int = 3) -> List[ToolEvent]:
    """Scan Codex CLI session logs and extract all tool calls as ToolEvents.

    Handles both old format (action/observation) and new v0.130.0+ format
    (response_item function_call/function_call_output paired by call_id).

    Args:
        max_sessions: Number of most recent session directories to scan.

    Returns:
        List of ToolEvents with inferred causal relations.
    """
    files = _find_rollout_files(max_sessions=max_sessions)
    events: List[ToolEvent] = []
    seen: set = set()

    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Two-pass for new format: collect calls and outputs keyed by call_id
        calls: Dict[str, dict] = {}
        outputs: Dict[str, str] = {}

        for line in content.splitlines():
            entry = _parse_jsonl_line(line)
            if not entry:
                continue

            # Try new format first (response_item)
            parsed = _parse_new_format(entry)
            if parsed:
                if parsed["kind"] == "call":
                    calls[parsed["call_id"]] = parsed
                elif parsed["kind"] == "output":
                    outputs[parsed["call_id"]] = parsed["tool_output"]
                continue

            # Fall back to old format (action/observation)
            result = _extract_codex_tool_call(entry)
            if result is None:
                continue

            tool_name, tool_input, tool_output = result
            if not tool_name:
                continue

            dedup_key = f"{f}:{_entry_fingerprint(entry)}"
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            timestamp = _parse_timestamp(entry)
            event = ToolEvent(
                tool_name=tool_name,
                tool_input=tool_input if isinstance(tool_input, dict) else str(tool_input),
                tool_output=tool_output or None,
                timestamp=timestamp,
                agent="codex",
            )
            events.append(event)

        # Pair new-format calls with outputs and create events
        for call_id, call in calls.items():
            tool_name = call["tool_name"]
            tool_input = call["tool_input"]
            output = outputs.get(call_id, "")

            dedup_key = f"{f}:{call_id or _entry_fingerprint(call)}"
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            event = ToolEvent(
                tool_name=tool_name,
                tool_input=tool_input if isinstance(tool_input, dict) else str(tool_input),
                tool_output=output or None,
                timestamp=call.get("timestamp"),
                agent="codex",
            )
            events.append(event)

    # 按时间戳排序事件，确保因果推断的顺序正确
    events.sort(key=lambda x: x.timestamp or "")
    # 过滤掉没有时间戳的无效事件
    events = [ev for ev in events if ev.timestamp]
    infer_relations(events)
    return events


def scan_session(
    session_label: str = "codex_latest",
) -> Tuple[str, List[ToolEvent]]:
    """Convenience: scan Codex logs and save as a causetrace session.

    Returns (session_id, events) with inferred causality.
    """
    events = scan_logs()
    if not events:
        return ("", [])

    recorder = TraceRecorder()
    for ev in events:
        recorder.record(ev)
    return recorder.session_id, events
