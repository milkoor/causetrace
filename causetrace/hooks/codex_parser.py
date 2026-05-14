"""Codex CLI rollout parser: extracts reasoning + tool calls from session JSONL.

Codex CLI stores session data as rollout JSONL files at:
    ~/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<uuid>.jsonl

Actual format (validated against real session 019e2553-ade5, Codex v0.130.0):

    Timeline:
        TokenCount ──┐
        FunctionCall ─┼── (paired by call_id)
        TokenCount ──┘
        FunctionCallOutput ── (result, same call_id, appears after)
        TokenCount
        ...

    The core pattern is alternating function_call → function_call_output
    linked by call_id, interspersed with token_count events.

Format (from real session data):
    {"timestamp":"...","type":"session_meta","payload":{"model_provider":"...","cli_version":"..."}}
    {"timestamp":"...","type":"event_msg","payload":{"type":"task_started",...}}
    {"timestamp":"...","type":"response_item","payload":{"type":"message","role":"developer","content":[...]}}
    {"timestamp":"...","type":"turn_context","payload":{"model":"deepseek-chat",...}}
    {"timestamp":"...","type":"event_msg","payload":{"type":"token_count",...}}
    {"timestamp":"...","type":"response_item","payload":{"type":"function_call","name":"exec_command","arguments":"{}","call_id":"..."}}
    {"timestamp":"...","type":"response_item","payload":{"type":"function_call_output","call_id":"...","output":"..."}}
    {"timestamp":"...","type":"response_item","payload":{"type":"message","role":"assistant","content":[{"type":"output_text","text":"..."}]}}
    {"timestamp":"...","type":"event_msg","payload":{"type":"agent_message","message":"..."}}
    {"timestamp":"...","type":"event_msg","payload":{"type":"task_complete",...}}

Usage:
    from causetrace.hooks.codex_parser import parse_session
    events = parse_session("session_id")
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from causetrace.core import ToolEvent

CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
_SESSION_DIR = CODEX_HOME / "sessions"

# Rollout line types
_SESSION_META = "session_meta"
_RESPONSE_ITEM = "response_item"
_EVENT_MSG = "event_msg"
_TURN_CONTEXT = "turn_context"
_COMPACTED = "compacted"

# ResponseItem payload types
_FUNCTION_CALL = "function_call"
_FUNCTION_CALL_OUTPUT = "function_call_output"
_MESSAGE = "message"

# EventMsg payload types
_AGENT_MESSAGE = "agent_message"
_TOKEN_COUNT = "token_count"
_TASK_STARTED = "task_started"
_TASK_COMPLETE = "task_complete"
_USER_MESSAGE = "user_message"


def _find_session_dirs() -> List[Path]:
    """Find Codex session directories, newest first."""
    if not _SESSION_DIR.exists():
        return []
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


def list_sessions() -> List[Dict[str, Any]]:
    """List all available Codex sessions with metadata."""
    sessions: List[Dict[str, Any]] = []
    for session_dir in _find_session_dirs():
        for f in sorted(session_dir.glob("rollout*.jsonl"), reverse=True):
            m = re.search(r"rollout-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-(.+)\.jsonl", f.name)
            session_id = m.group(1) if m else f.stem
            try:
                line_count = sum(1 for _ in f.open())
            except OSError:
                line_count = 0
            sessions.append({
                "session_id": session_id,
                "path": str(f),
                "lines": line_count,
            })
    return sessions


def _find_session_file(session_id: str) -> Optional[Path]:
    """Find a rollout file by session ID."""
    for session_dir in _find_session_dirs():
        for f in sorted(session_dir.glob("rollout*.jsonl"), reverse=True):
            m = re.search(r"rollout-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-(.+)\.jsonl", f.name)
            if m and m.group(1) == session_id:
                return f
            if f.stem == session_id or session_id in f.stem:
                return f
    return None


def _load_rollout(path: Path) -> List[Dict[str, Any]]:
    """Load and parse all lines from a rollout JSONL file."""
    lines = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    lines.append(obj)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return lines


def _parse_iso_timestamp(ts_str: str) -> Optional[str]:
    """Parse and normalize an ISO timestamp."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.isoformat()
    except (ValueError, AttributeError):
        return ts_str


def parse_session(session_id: str) -> List[ToolEvent]:
    """Parse a Codex CLI rollout session into causally-linked events.

    Real format (validated v0.130.0):
    - response_item/function_call → tool_call events
    - response_item/function_call_output → linked to function_call by call_id
    - event_msg/agent_message → reasoning events
    - response_item/message (assistant) → Response text events

    Returns:
        List of ToolEvents in chronological order, with causal links.
    """
    path = _find_session_file(session_id)
    if not path:
        return []

    lines = _load_rollout(path)
    if not lines:
        return []

    events: List[ToolEvent] = []
    last_event_id: Optional[str] = None

    # Track model/provider/agent from session_meta / turn_context
    model_info: Dict[str, str] = {}

    # Track in-flight function_calls by call_id to pair with function_call_output
    pending_calls: Dict[str, dict] = {}

    for obj in lines:
        item_type = obj.get("type", "")
        payload = obj.get("payload") or {}
        timestamp = _parse_iso_timestamp(obj.get("timestamp", ""))

        if item_type == _SESSION_META:
            model_info["provider"] = payload.get("model_provider", "")
            model_info["agent"] = "codex"
            continue

        if item_type == _TURN_CONTEXT:
            model_info["model"] = payload.get("model", "")
            continue

        if item_type == _COMPACTED:
            continue

        if item_type == _EVENT_MSG:
            msg_type = payload.get("type", "")

            if msg_type == _AGENT_MESSAGE:
                text = payload.get("message", "")
                if text and text.strip():
                    event = ToolEvent(
                        tool_name="Thinking",
                        tool_input={"content": text[:2000]},
                        event_type="reasoning",
                        timestamp=timestamp,
                        parent_event_id=last_event_id,
                        model=model_info.get("model"),
                        provider=model_info.get("provider"),
                        agent="codex",
                    )
                    events.append(event)
                    last_event_id = event.event_id

            # Skip token_count, task_started, task_complete, user_message
            continue

        if item_type == _RESPONSE_ITEM:
            resp_type = payload.get("type", "")

            if resp_type == _FUNCTION_CALL:
                call_id = payload.get("call_id", "")
                name = payload.get("name", "unknown")
                try:
                    arguments = json.loads(payload.get("arguments", "{}"))
                except (json.JSONDecodeError, TypeError):
                    arguments = {"raw": payload.get("arguments", "")}

                # Store pending call for output pairing
                pending_calls[call_id] = {
                    "tool_name": name,
                    "tool_input": arguments,
                    "timestamp": timestamp,
                    "event_id": None,  # will be set after event creation
                }

                event = ToolEvent(
                    tool_name=name,
                    tool_input=arguments,
                    event_type="tool_call",
                    timestamp=timestamp,
                    parent_event_id=last_event_id,
                    model=model_info.get("model"),
                    provider=model_info.get("provider"),
                    agent="codex",
                )
                events.append(event)
                pending_calls[call_id]["event_id"] = event.event_id
                last_event_id = event.event_id

            elif resp_type == _FUNCTION_CALL_OUTPUT:
                call_id = payload.get("call_id", "")
                output = payload.get("output", "")
                pre = pending_calls.pop(call_id, None)

                tool_output = output[:2000] if output else None

                if pre:
                    # Find the function_call event and update its output
                    event_id = pre["event_id"]
                    for e in events:
                        if e.event_id == event_id:
                            e.tool_output = tool_output
                            break
                else:
                    # Orphan output (no matching function_call found)
                    event = ToolEvent(
                        tool_name="unknown",
                        tool_output=tool_output,
                        event_type="tool_call",
                        timestamp=timestamp,
                        parent_event_id=last_event_id,
                        model=model_info.get("model"),
                        provider=model_info.get("provider"),
                        agent="codex",
                    )
                    events.append(event)
                    last_event_id = event.event_id

            elif resp_type == _MESSAGE:
                role = payload.get("role", "")
                if role == "assistant":
                    content = payload.get("content") or []
                    texts = []
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "output_text":
                                texts.append(c.get("text", ""))
                    text = "\n".join(texts)
                    if text and text.strip():
                        event = ToolEvent(
                            tool_name="Response",
                            tool_input={"text": text[:500]},
                            event_type="reasoning",
                            timestamp=timestamp,
                            parent_event_id=last_event_id,
                            model=model_info.get("model"),
                            provider=model_info.get("provider"),
                            agent="codex",
                        )
                        events.append(event)
                        last_event_id = event.event_id

    return events
