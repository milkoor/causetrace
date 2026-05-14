"""OpenCode DB session parser: extracts thinking + tool_use from SQLite DB.

OpenCode stores full session data in a SQLite DB at:
    ~/.local/share/opencode/opencode.db

The DB contains three key tables:
    session  →  message  →  part

Key part types:
    reasoning  — model's internal reasoning (equivalent to Claude Code thinking)
    tool       — tool calls with structured input/output
    text       — text responses
    patch      — file edits

Usage:
    from causetrace.hooks.opencode_parser import parse_session
    events = parse_session("session_id")
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from causetrace.core import ToolEvent

DB_PATH = Path.home() / ".local" / "share" / "opencode" / "opencode.db"

# Part types to include and their event mapping
_INCLUDE_TYPES = frozenset({"reasoning", "text", "tool", "patch"})


def list_sessions() -> List[Dict[str, Any]]:
    """List all sessions in the OpenCode DB with metadata."""
    if not DB_PATH.exists():
        return []

    try:
        conn = sqlite3.connect(str(DB_PATH))
        rows = conn.execute(
            """SELECT id, slug, title, project_id, time_created, time_updated
               FROM session ORDER BY time_created DESC"""
        ).fetchall()
        conn.close()
    except (sqlite3.Error, OSError):
        return []

    sessions = []
    for row in rows:
        sessions.append({
            "session_id": row[0],
            "slug": row[1],
            "title": row[2],
            "project_id": row[3],
            "time_created": row[4],
            "time_updated": row[5],
        })
    return sessions


def _connect() -> Optional[sqlite3.Connection]:
    if not DB_PATH.exists():
        return None
    try:
        return sqlite3.connect(str(DB_PATH))
    except (sqlite3.Error, OSError):
        return None


def _load_model_cache(conn: sqlite3.Connection, session_id: str) -> Dict[str, Any]:
    """Build a message_id → model_info cache from user messages."""
    cache: Dict[str, dict] = {}
    try:
        rows = conn.execute(
            """SELECT id, data FROM message
               WHERE session_id = ? AND json_extract(data, '$.role') = 'user'""",
            (session_id,),
        ).fetchall()
        for msg_id, raw in rows:
            d = json.loads(raw)
            model_info = d.get("model") or {}
            cache[msg_id] = {
                "model": model_info.get("modelID", ""),
                "provider": model_info.get("providerID", ""),
                "agent": d.get("agent", ""),
            }
    except (sqlite3.Error, json.JSONDecodeError):
        pass
    return cache


def _get_parent_model(
    parent_id: Optional[str], model_cache: Dict[str, Any]
) -> Dict[str, str]:
    if not parent_id:
        return {"model": "", "provider": "", "agent": ""}
    return model_cache.get(parent_id, {"model": "", "provider": "", "agent": ""})


def _parse_part(
    part_data: dict, msg_data: dict, model_info: Dict[str, str], index: int
) -> Optional[ToolEvent]:
    """Convert a part entry into a ToolEvent. Returns None for skipped types."""
    ptype = part_data.get("type", "")

    if ptype == "reasoning":
        return ToolEvent(
            tool_name="Thinking",
            tool_input={"content": (part_data.get("text") or "")[:2000]},
            event_type="reasoning",
            timestamp=_extract_ts(part_data, "start"),
            model=model_info.get("model"),
            provider=model_info.get("provider"),
            agent=model_info.get("agent") or "opencode",
        )

    elif ptype == "text":
        text = part_data.get("text") or ""
        if not text.strip():
            return None
        return ToolEvent(
            tool_name="Response",
            tool_input={"text": text[:500]},
            event_type="reasoning",
            timestamp=_extract_ts(part_data, "start"),
            model=model_info.get("model"),
            provider=model_info.get("provider"),
            agent=model_info.get("agent") or "opencode",
        )

    elif ptype == "tool":
        tool_name = part_data.get("tool") or "Unknown"
        state = part_data.get("state") or {}
        tool_input = state.get("input") or {}
        tool_output = _serialize_output(state.get("output"))
        duration = _extract_duration(state)
        return ToolEvent(
            tool_name=_normalize_tool(tool_name),
            tool_input=tool_input if isinstance(tool_input, dict) else {"text": str(tool_input)[:2000]},
            tool_output=tool_output,
            event_type="tool_call",
            timestamp=_extract_ts(part_data, "start"),
            duration_ms=duration,
            model=model_info.get("model"),
            provider=model_info.get("provider"),
            agent=model_info.get("agent") or "opencode",
        )

    elif ptype == "patch":
        files = part_data.get("files") or []
        return ToolEvent(
            tool_name="Edit",
            tool_input={"files": files},
            event_type="tool_call",
            timestamp=_extract_ts(part_data, "start"),
            agent="opencode",
        )

    return None


def _normalize_tool(name: str) -> str:
    """Map OpenCode tool names to canonical names."""
    mapping = {
        "bash": "Bash",
        "read": "Read",
        "edit": "Edit",
        "write": "Write",
        "grep": "Grep",
        "glob": "Glob",
        "todowrite": "TodoWrite",
        "skill_mcp": "Skill",
        "skill": "Skill",
        "task": "Task",
        "question": "Question",
        "websearch": "WebSearch",
        "webfetch": "WebFetch",
        "lsp_diagnostics": "LSPDiagnostics",
        "background_output": "BackgroundOutput",
    }
    return mapping.get(name, name)


def _extract_ts(part_data: dict, field: str = "start", fallback_ms: Optional[int] = None) -> Optional[str]:
    """Extract ISO timestamp from part's time field.

    Checks part_data.time first, then state.time, then fallback_ms.
    OpenCode uses millisecond or microsecond timestamps.
    """
    time_obj = part_data.get("time") or {}
    ts = time_obj.get(field)
    if not ts:
        state = part_data.get("state") or {}
        time_obj = state.get("time") or {}
        ts = time_obj.get(field)
    if not ts:
        ts = fallback_ms
    if not ts:
        return None
    try:
        from datetime import datetime, timezone
        # Timestamp scale detection:
        #   seconds (~1.7e9)         — no conversion needed
        #   milliseconds (~1.7e12)   — / 1000
        #   microseconds (~1.7e15)   — / 1_000_000
        if ts >= 1_000_000_000_000_000:
            ts = ts / 1_000_000  # μs → s
        elif ts >= 1_000_000_000_000:
            ts = ts / 1000  # ms → s
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except (ValueError, OSError):
        return None


def _extract_duration(state: dict) -> Optional[int]:
    """Extract duration in ms from tool state if available."""
    time_obj = state.get("time") or {}
    start = time_obj.get("start")
    end = time_obj.get("end")
    if start and end:
        return int((end - start) / 1000)  # microseconds → ms
    return None


def _serialize_output(output: Any) -> Optional[str]:
    if not output:
        return None
    if isinstance(output, str):
        return output[:2000]
    return str(output)[:2000]


def parse_session(session_id: str) -> List[ToolEvent]:
    """Parse an OpenCode DB session into causally-linked events.

    Extracts reasoning, tool_use, and text blocks from the session's
    part entries and creates ToolEvents with parent_event_id chains.

    Returns:
        List of ToolEvents in chronological order, with causal links.
    """
    conn = _connect()
    if not conn:
        return []

    try:
        rows = conn.execute(
            """SELECT p.id, p.time_created, p.data as part_data,
                      m.id as msg_id, m.data as msg_data
               FROM part p
               JOIN message m ON p.message_id = m.id
               WHERE p.session_id = ?
                 AND json_extract(m.data, '$.role') = 'assistant'
               ORDER BY p.time_created""",
            (session_id,),
        ).fetchall()
    except sqlite3.Error:
        conn.close()
        return []

    if not rows:
        conn.close()
        return []

    model_cache = _load_model_cache(conn, session_id)
    conn.close()

    events: List[ToolEvent] = []
    last_event_id: Optional[str] = None
    last_msg_id: Optional[str] = None

    for part_id, ts_ms, part_raw, msg_id, msg_raw in rows:
        try:
            part_data = json.loads(part_raw)
            msg_data = json.loads(msg_raw)
        except json.JSONDecodeError:
            continue

        ptype = part_data.get("type", "")
        if ptype not in _INCLUDE_TYPES:
            continue

        # When message changes, set parent to last event of previous message
        if msg_id != last_msg_id:
            parent_id = msg_data.get("parentID")
            if parent_id:
                parent_info = _get_parent_model(parent_id, model_cache)
            else:
                parent_info = {"model": "", "provider": "", "agent": ""}
            last_msg_id = msg_id
        else:
            parent_info = _get_parent_model(msg_data.get("parentID"), model_cache)

        event = _parse_part(part_data, msg_data, parent_info, 0)
        if event is None:
            continue

        # Use DB time_created as fallback timestamp if part lacks embedded time
        if event.timestamp is None and ts_ms:
            event.timestamp = _extract_ts({"time": {"start": ts_ms}}, "start")

        event.parent_event_id = last_event_id
        events.append(event)
        last_event_id = event.event_id

    return events


def scan_session(session_id: str) -> Tuple[str, List[ToolEvent]]:
    """Parse an OpenCode DB session and return (session_id, events)."""
    events = parse_session(session_id)
    return session_id, events
