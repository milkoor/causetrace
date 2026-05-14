"""Continue.dev log tailer: extracts tool calls from Continue core logs.

Continue.dev logs structured JSON lines to `~/.continue/logs/core.log`
containing tool call events, model info, and step execution data.

Usage:
    from causetrace.hooks.continue_tailer import scan_logs
    events = scan_logs()
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from causetrace.core import ToolEvent, TraceRecorder
from causetrace.causality import infer_relations

LOG_DIR = Path.home() / ".continue" / "logs"
_CORE_LOG = LOG_DIR / "core.log"

# Patterns to identify tool calls in Continue log messages
_TOOL_PATTERNS = [
    re.compile(r"Running\s+(?:tool|step)\s*[:=]\s*(.+?)(?:\s|$)", re.IGNORECASE),
    re.compile(r"tool_call\s*[:=]\s*(.+?)(?:\s|$)", re.IGNORECASE),
    re.compile(r"function_call\s*[:=]\s*(.+?)(?:\s|$)", re.IGNORECASE),
    re.compile(r"using\s+tool\s*[:=]\s*(.+?)(?:\s|$)", re.IGNORECASE),
]

# Map Continue tool names to causetrace tool names
_TOOL_ALIASES: Dict[str, str] = {
    "read": "Read",
    "readfile": "Read",
    "edit": "Edit",
    "editfile": "Edit",
    "write": "Write",
    "create": "Write",
    "bash": "Bash",
    "terminal": "Bash",
    "command": "Bash",
    "run": "Bash",
    "search": "Grep",
    "grep": "Grep",
    "glob": "Glob",
    "file_search": "Grep",
    "web": "WebFetch",
    "web_fetch": "WebFetch",
    "http": "WebFetch",
    "python": "Bash",
    "ipython": "Bash",
}


def _normalize_tool(name: str) -> str:
    """Map Continue's tool names to causetrace tool names."""
    key = name.lower().strip().replace(" ", "_").replace("-", "_")
    return _TOOL_ALIASES.get(key, name)


def _find_log_files() -> List[Path]:
    """Find Continue log files, newest first."""
    if not LOG_DIR.exists():
        return []
    files = []
    for f in LOG_DIR.glob("core*.log*"):
        if f.is_file():
            files.append(f)
    files.sort(reverse=True)
    return files


def _parse_json_line(line: str) -> Optional[dict]:
    """Try to parse a JSON line from Continue's log."""
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def _is_tool_call(log_entry: dict) -> bool:
    """Check if a log entry represents a tool call."""
    message = log_entry.get("message", "")
    if not isinstance(message, str):
        return False
    for pattern in _TOOL_PATTERNS:
        if pattern.search(message):
            return True
    # Also check for structured tool call fields
    if any(k in log_entry for k in ("tool", "tool_call", "function_call")):
        return True
    return False


def _extract_tool_info(log_entry: dict) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract (tool_name, tool_input, tool_output) from a log entry.

    Returns (None, None, None) if extraction fails.
    """
    message = log_entry.get("message", "")
    raw = log_entry.get("raw", "") or ""

    # Try structured fields first
    tool_data = log_entry.get("tool") or log_entry.get("tool_call") or {}
    if isinstance(tool_data, dict):
        name = tool_data.get("name") or tool_data.get("function") or ""
        inp = tool_data.get("input") or tool_data.get("arguments") or ""
        out = tool_data.get("output") or tool_data.get("result") or ""
        if name:
            return _normalize_tool(str(name)), str(inp)[:2000], str(out)[:2000]

    # Try raw field (may contain JSON)
    if raw and isinstance(raw, str):
        try:
            data = json.loads(raw)
            name = data.get("name") or data.get("function") or ""
            inp = data.get("input") or data.get("arguments") or ""
            out = data.get("output") or data.get("result") or ""
            if name:
                return _normalize_tool(str(name)), str(inp)[:2000], str(out)[:2000]
        except json.JSONDecodeError:
            pass

    # Try message text patterns
    for pattern in _TOOL_PATTERNS:
        m = pattern.search(message)
        if m:
            name = m.group(1).split(":")[0].split(" ")[0].strip()
            inp = message[:300]
            return _normalize_tool(name), inp, ""

    return None, None, None


def _parse_timestamp(log_entry: dict) -> Optional[str]:
    """Extract ISO timestamp from a log entry."""
    ts = log_entry.get("timestamp") or log_entry.get("time") or log_entry.get("createdAt")
    if not ts:
        return None
    try:
        # Handle various formats
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts).isoformat()
        return str(ts)
    except (ValueError, OSError):
        return str(ts)


def scan_logs(max_files: int = 3) -> List[ToolEvent]:
    """Scan Continue.dev log files and extract all tool calls as ToolEvents.

    Args:
        max_files: Number of most recent log files to scan.

    Returns:
        List of ToolEvents with inferred causal relations.
    """
    files = _find_log_files()[:max_files]
    events: List[ToolEvent] = []
    seen: set = set()

    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for line in content.splitlines():
            entry = _parse_json_line(line)
            if not entry:
                continue

            if not _is_tool_call(entry):
                continue

            tool_name, tool_input, tool_output = _extract_tool_info(entry)
            if not tool_name:
                continue

            # Deduplicate: same tool + same input within a short window
            dedup_key = f"{tool_name}:{tool_input[:100]}"
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            timestamp = _parse_timestamp(entry)

            event = ToolEvent(
                tool_name=tool_name,
                tool_input=tool_input or {},
                tool_output=tool_output or None,
                timestamp=timestamp,
                agent="continue",
            )
            events.append(event)

    infer_relations(events)
    return events


def scan_session(
    session_label: str = "continue_latest",
) -> Tuple[str, List[ToolEvent]]:
    """Convenience: scan Continue logs and save as a causetrace session.

    Returns (session_id, events) with inferred causality.
    """
    events = scan_logs()
    if not events:
        return ("", [])

    recorder = TraceRecorder()
    for ev in events:
        recorder.record(ev)
    return recorder.session_id, events
