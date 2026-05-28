"""OpenCode log tailer: extracts tool calls from tool.registry log entries.

OpenCode logs ALL tool calls in its log files:
  INFO  ... service=tool.registry status=started <tool>
  INFO  ... service=tool.registry status=completed duration=<ms> <tool>

Usage:
  from causetrace.hooks.opencode_tailer import scan_logs
  events = scan_logs()
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from causetrace.core import ToolEvent, TraceRecorder
from causetrace.causality import infer_relations

LOG_DIR = Path.home() / ".local" / "share" / "opencode" / "log"
DB_PATH = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
_LOG_PATTERN = re.compile(
    r"INFO\s+"
    r"(?P<date>\d{4}-\d{2}-\d{2})T"
    r"(?P<time>\d{2}:\d{2}:\d{2})"
    r".*?"
    r"service=tool\.registry\s+"
    r"status=(?P<status>started|completed)"
    r"(?:\s+duration=(?P<duration>\d+))?"
    r"\s+(?P<tool>\S+)"
)

_SKIP_TOOLS = {"invalid"}
_MODEL_CACHE: Dict[str, dict] = {}  # session_id → model info dict


def _load_model_info() -> Dict[str, dict]:
    """Extract model/provider/agent info per session from the OpenCode DB."""
    result: Dict[str, dict] = {}
    if not DB_PATH.exists():
        return result
    try:
        conn = sqlite3.connect(str(DB_PATH))
        rows = conn.execute(
            "SELECT session_id, data FROM message WHERE data LIKE '%modelID%' ORDER BY time_created"
        ).fetchall()
        conn.close()
    except (sqlite3.Error, OSError):
        return result

    for sid, raw_data in rows:
        try:
            d = json.loads(raw_data)
            model_info = d.get("model", {})
            if model_info and isinstance(model_info, dict):
                mid = model_info.get("modelID", "")
                pid = model_info.get("providerID", "")
                agent_name = d.get("agent", "")
                if sid not in result:
                    result[sid] = {}
                if mid:
                    result[sid]["model"] = mid
                if pid:
                    result[sid]["provider"] = pid
                if agent_name:
                    result[sid]["agent"] = agent_name
        except (json.JSONDecodeError, KeyError):
            continue
    return result


def get_session_model(session_id: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Get (model, provider, agent) for a session, caching the DB query."""
    if not _MODEL_CACHE:
        all_models = _load_model_info()
        _MODEL_CACHE.update(all_models)
    cached = _MODEL_CACHE.get(session_id, {})
    return cached.get("model"), cached.get("provider"), cached.get("agent")


def _parse_log_line(line: str) -> Optional[dict]:
    m = _LOG_PATTERN.search(line)
    if not m:
        return None
    tool = m.group("tool")
    if tool in _SKIP_TOOLS:
        return None
    return {
        "tool": tool,
        "status": m.group("status"),
        "duration_ms": int(m.group("duration")) if m.group("duration") else None,
        "timestamp": f"{m.group('date')}T{m.group('time')}",
    }


def _duration_from_timestamps(start_ts: Optional[str], end_ts: Optional[str]) -> Optional[float]:
    """Compute elapsed milliseconds between two ISO timestamps."""
    if not start_ts or not end_ts:
        return None
    try:
        start = datetime.fromisoformat(start_ts)
        end = datetime.fromisoformat(end_ts)
    except ValueError:
        return None
    return max((end - start).total_seconds() * 1000.0, 0.0)


def _find_log_files() -> List[Path]:
    if not LOG_DIR.exists():
        return []
    files = sorted(LOG_DIR.glob("*.log"), reverse=True)
    return files


def scan_logs(max_files: int = 3) -> List[ToolEvent]:
    """Scan OpenCode log files and extract all tool calls as ToolEvents.

    Args:
        max_files: Number of most recent log files to scan.
    """
    files = list(reversed(_find_log_files()[:max_files]))
    started: Dict[str, List[str]] = defaultdict(list)
    events: List[ToolEvent] = []

    for f in files:
        try:
            content = f.read_text(errors="replace")
        except OSError:
            continue

        for line in content.splitlines():
            parsed = _parse_log_line(line)
            if not parsed:
                continue

            tool = parsed["tool"]
            ts = parsed["timestamp"]

            if parsed["status"] == "started":
                started[tool].append(ts)
            elif parsed["status"] == "completed":
                start_ts = started[tool].pop(0) if started.get(tool) else None
                if not started.get(tool):
                    started.pop(tool, None)
                duration = parsed["duration_ms"]
                if duration is None:
                    duration = _duration_from_timestamps(start_ts, ts)
                events.append(ToolEvent(
                    tool_name=tool,
                    tool_input={},
                    duration_ms=duration,
                    timestamp=ts,
                ))

    infer_relations(events)
    # Best-effort: annotate with model info from the most recent session
    if events:
        model_info = _load_model_info()
        _MODEL_CACHE.update(model_info)
        if model_info:
            latest_sid = max(model_info.keys())
            info = model_info[latest_sid]
            for ev in events:
                ev.model = info.get("model")
                ev.provider = info.get("provider")
                ev.agent = info.get("agent")
    return events


def scan_session(session_label: str = "opencode") -> Tuple[str, List[ToolEvent]]:
    """Convenience: scan logs and save as a named causetrace session.

    Returns (session_id, events) with inferred causality.
    """
    events = scan_logs()
    if not events:
        return ("", [])

    recorder = TraceRecorder()
    for ev in events:
        recorder.record(ev)
    return recorder.session_id, events
