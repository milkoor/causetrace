"""Hermes Agent parser: extracts reasoning + tool calls from state.db.

Hermes stores session data in a SQLite database at ~/.hermes/state.db.

Schema:
  sessions(id, source, model, started_at, ended_at, ...)
  messages(id, session_id, role, content, tool_call_id, tool_calls,
           tool_name, timestamp, reasoning, ...)

Messages follow OpenAI format:
  - role='assistant' with tool_calls JSON -> tool_call events
  - role='assistant' with reasoning text -> reasoning events
  - role='tool' -> output linked by tool_call_id

Usage:
    from causetrace.hooks.hermes_parser import parse_session
    events = parse_session("session_id")
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from causetrace.core import ToolEvent

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
HERMES_DB = HERMES_HOME / "state.db"


def _get_db() -> Optional[sqlite3.Connection]:
    if not HERMES_DB.exists():
        return None
    conn = sqlite3.connect(str(HERMES_DB))
    conn.row_factory = sqlite3.Row
    return conn


def list_sessions() -> List[Dict[str, Any]]:
    conn = _get_db()
    if not conn:
        return []
    try:
        rows = conn.execute(
            "SELECT id, source, model, started_at, ended_at, message_count, "
            "tool_call_count, title, cwd, git_branch "
            "FROM sessions ORDER BY started_at DESC"
        ).fetchall()
        sessions = []
        for row in rows:
            sessions.append({
                "session_id": row["id"],
                "source": row["source"],
                "model": row["model"],
                "started_at": row["started_at"],
                "ended_at": row["ended_at"],
                "message_count": row["message_count"],
                "tool_call_count": row["tool_call_count"],
                "title": row["title"],
                "cwd": row["cwd"],
                "git_branch": row["git_branch"],
            })
        return sessions
    finally:
        conn.close()


def _parse_timestamp(ts: float) -> str:
    try:
        dt = datetime.fromtimestamp(ts)
        return dt.isoformat()
    except (ValueError, OSError):
        return str(ts)


def _detect_provider(model: str) -> str:
    if not model:
        return ""
    m = model.lower()
    if "claude" in m or "anthropic" in m:
        return "anthropic"
    if "gpt" in m or "openai" in m or "o1" in m or "o3" in m or "o4" in m:
        return "openai"
    if "deepseek" in m:
        return "deepseek"
    if "doubao" in m or "seed" in m:
        return "bytedance"
    if "gemini" in m:
        return "google"
    if "llama" in m or "meta" in m:
        return "meta"
    if "mistral" in m:
        return "mistral"
    if "qwen" in m:
        return "alibaba"
    return ""


def parse_session(session_id: str) -> List[ToolEvent]:
    """Parse a Hermes session into causally-linked events.

    Returns:
        List of ToolEvents in chronological order, with causal links.
    """
    conn = _get_db()
    if not conn:
        return []

    try:
        session = conn.execute(
            "SELECT id, model FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not session:
            return []

        model = session["model"] or ""
        provider = _detect_provider(model)

        messages = conn.execute(
            "SELECT id, role, content, tool_call_id, tool_calls, tool_name, "
            "timestamp, reasoning "
            "FROM messages WHERE session_id = ? AND active = 1 "
            "ORDER BY timestamp, id",
            (session_id,)
        ).fetchall()

        events: List[ToolEvent] = []
        last_event_id: Optional[str] = None

        # Collect tool outputs from 'tool' role messages
        tool_outputs: Dict[str, str] = {}
        for msg in messages:
            if msg["role"] == "tool" and msg["tool_call_id"] and msg["content"]:
                tool_outputs[msg["tool_call_id"]] = msg["content"]

        # Build events from assistant messages
        for msg in messages:
            if msg["role"] != "assistant":
                continue

            timestamp = _parse_timestamp(msg["timestamp"])

            # Reasoning event
            reasoning = msg["reasoning"] or ""
            if reasoning.strip():
                event = ToolEvent(
                    tool_name="Thinking",
                    tool_input={"content": reasoning[:2000]},
                    event_type="reasoning",
                    timestamp=timestamp,
                    parent_event_id=last_event_id,
                    model=model,
                    provider=provider,
                    agent="hermes",
                )
                events.append(event)
                last_event_id = event.event_id

            # Tool call events
            tool_calls_json = msg["tool_calls"] or ""
            if tool_calls_json:
                try:
                    tool_calls = json.loads(tool_calls_json)
                except (json.JSONDecodeError, TypeError):
                    continue

                for tc in tool_calls:
                    func = tc.get("function", {})
                    name = func.get("name", "unknown")
                    try:
                        arguments = json.loads(func.get("arguments", "{}"))
                    except (json.JSONDecodeError, TypeError):
                        arguments = {"raw": func.get("arguments", "")}

                    call_id = tc.get("call_id") or tc.get("id", "")
                    output = tool_outputs.get(call_id)
                    if output:
                        output = output[:2000]

                    event = ToolEvent(
                        tool_name=name,
                        tool_input=arguments,
                        tool_output=output,
                        event_type="tool_call",
                        timestamp=timestamp,
                        parent_event_id=last_event_id,
                        model=model,
                        provider=provider,
                        agent="hermes",
                    )
                    events.append(event)
                    last_event_id = event.event_id

        return events

    finally:
        conn.close()
