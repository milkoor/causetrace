"""Tests for the OpenCode DB session parser."""

import json
import sys
import tempfile
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from causetrace.hooks.opencode_parser import (
    parse_session,
    list_sessions,
    _parse_part,
    _extract_ts,
    _normalize_tool,
    DB_PATH,
)


def test_normalize_tool():
    assert _normalize_tool("bash") == "Bash"
    assert _normalize_tool("read") == "Read"
    assert _normalize_tool("edit") == "Edit"
    assert _normalize_tool("write") == "Write"
    assert _normalize_tool("grep") == "Grep"
    assert _normalize_tool("glob") == "Glob"
    assert _normalize_tool("todowrite") == "TodoWrite"
    assert _normalize_tool("skill_mcp") == "Skill"
    assert _normalize_tool("unknowntool") == "unknowntool"


def test_extract_ts_from_part_time():
    part = {"time": {"start": 1778724854161}}
    ts = _extract_ts(part, "start")
    assert ts is not None
    # 1778724854161 ms → 2026-05-14
    assert ts.startswith("2026-05-14")


def test_extract_ts_from_state_time():
    part = {"state": {"time": {"start": 1778724854161}}}
    ts = _extract_ts(part, "start")
    assert ts is not None
    assert ts.startswith("2026-05-14")


def test_extract_ts_fallback():
    ts = _extract_ts({}, "start", fallback_ms=1778724854161)
    assert ts is not None
    assert ts.startswith("2026-05-14")


def test_extract_ts_none():
    assert _extract_ts({}, "start") is None


def test_parse_part_reasoning():
    part = {"type": "reasoning", "text": "I should read the file first"}
    event = _parse_part(part, {}, {}, 0)
    assert event is not None
    assert event.event_type == "reasoning"
    assert event.tool_name == "Thinking"


def test_parse_part_text():
    part = {"type": "text", "text": "Hello, I can help."}
    event = _parse_part(part, {}, {}, 0)
    assert event is not None
    assert event.event_type == "reasoning"
    assert event.tool_name == "Response"


def test_parse_part_empty_text():
    part = {"type": "text", "text": "   "}
    assert _parse_part(part, {}, {}, 0) is None


def test_parse_part_tool():
    part = {
        "type": "tool", "tool": "bash",
        "state": {"status": "completed", "input": {"command": "ls"}, "output": "file1.txt"}
    }
    event = _parse_part(part, {}, {}, 0)
    assert event is not None
    assert event.event_type == "tool_call"
    assert event.tool_name == "Bash"
    assert event.tool_input == {"command": "ls"}


def test_parse_part_patch():
    part = {"type": "patch", "files": ["/tmp/test.txt"]}
    event = _parse_part(part, {}, {}, 0)
    assert event is not None
    assert event.event_type == "tool_call"
    assert event.tool_name == "Edit"


def test_parse_part_unknown():
    assert _parse_part({"type": "step-start"}, {}, {}, 0) is None
    assert _parse_part({"type": "step-finish"}, {}, {}, 0) is None
    assert _parse_part({"type": "compaction"}, {}, {}, 0) is None


def test_parse_session_causal_chain():
    """Full integration test with proper DB_PATH override."""
    tmpdir = Path(tempfile.mkdtemp())
    db_path = tmpdir / "opencode.db"

    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE session (id TEXT PRIMARY KEY, slug TEXT, title TEXT, project_id TEXT, "
                 "time_created INTEGER, time_updated INTEGER)")
    conn.execute("CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT NOT NULL, "
                 "time_created INTEGER NOT NULL, time_updated INTEGER NOT NULL, data TEXT NOT NULL)")
    conn.execute("CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT NOT NULL, session_id TEXT NOT NULL, "
                 "time_created INTEGER NOT NULL, time_updated INTEGER NOT NULL, data TEXT NOT NULL)")

    sid = "test_chain"
    conn.execute("INSERT INTO session VALUES (?, ?, ?, ?, ?, ?)",
                 (sid, "chain", "Chain Test", "p1", 1000, 2000))

    # user message with model info
    conn.execute("INSERT INTO message VALUES (?, ?, ?, ?, ?)",
                 ("m0", sid, 1000, 1000,
                  json.dumps({"role": "user", "model": {"modelID": "m1", "providerID": "p1"}, "agent": "a1"})))
    conn.execute("INSERT INTO part VALUES (?, ?, ?, ?, ?, ?)",
                 ("p0", "m0", sid, 1000, 1000,
                  json.dumps({"type": "text", "text": "hello"})))

    # assistant message with reasoning + tool + text
    conn.execute("INSERT INTO message VALUES (?, ?, ?, ?, ?)",
                 ("m1", sid, 2000, 2000,
                  json.dumps({"role": "assistant", "parentID": "m0"})))
    conn.execute("INSERT INTO part VALUES (?, ?, ?, ?, ?, ?)",
                 ("p1", "m1", sid, 2000, 2000,
                  json.dumps({"type": "reasoning", "text": "thinking..."})))
    conn.execute("INSERT INTO part VALUES (?, ?, ?, ?, ?, ?)",
                 ("p2", "m1", sid, 3000, 3000,
                  json.dumps({"type": "tool", "tool": "bash", "state": {"input": {"command": "ls"}, "output": "files"}})))
    conn.execute("INSERT INTO part VALUES (?, ?, ?, ?, ?, ?)",
                 ("p3", "m1", sid, 4000, 4000,
                  json.dumps({"type": "text", "text": "done"})))
    conn.commit()
    conn.close()

    import causetrace.hooks.opencode_parser as mod
    original = mod.DB_PATH
    mod.DB_PATH = db_path
    try:
        events = parse_session(sid)
        assert len(events) == 3
        assert events[0].tool_name == "Thinking"
        assert events[0].event_type == "reasoning"
        assert events[0].model == "m1"
        assert events[0].provider == "p1"
        assert events[0].agent == "a1"
        assert events[1].tool_name == "Bash"
        assert events[1].event_type == "tool_call"
        assert events[2].tool_name == "Response"
        assert events[2].event_type == "reasoning"
        # Causal chain
        assert events[1].parent_event_id == events[0].event_id
        assert events[2].parent_event_id == events[1].event_id
    finally:
        mod.DB_PATH = original


def test_parse_session_only_tools():
    """Session without reasoning blocks."""
    tmpdir = Path(tempfile.mkdtemp())
    db_path = tmpdir / "opencode.db"

    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE session (id TEXT PRIMARY KEY, slug TEXT, title TEXT, project_id TEXT, "
                 "time_created INTEGER, time_updated INTEGER)")
    conn.execute("CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT NOT NULL, "
                 "time_created INTEGER NOT NULL, time_updated INTEGER NOT NULL, data TEXT NOT NULL)")
    conn.execute("CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT NOT NULL, session_id TEXT NOT NULL, "
                 "time_created INTEGER NOT NULL, time_updated INTEGER NOT NULL, data TEXT NOT NULL)")

    sid = "test_tools"
    conn.execute("INSERT INTO session VALUES (?, ?, ?, ?, ?, ?)",
                 (sid, "tools", "Tools Only", "p1", 1000, 2000))
    conn.execute("INSERT INTO message VALUES (?, ?, ?, ?, ?)",
                 ("m0", sid, 1000, 1000, json.dumps({"role": "user"})))
    conn.execute("INSERT INTO part VALUES (?, ?, ?, ?, ?, ?)",
                 ("p0", "m0", sid, 1000, 1000, json.dumps({"type": "text", "text": "do it"})))
    conn.execute("INSERT INTO message VALUES (?, ?, ?, ?, ?)",
                 ("m1", sid, 2000, 2000, json.dumps({"role": "assistant", "parentID": "m0"})))
    conn.execute("INSERT INTO part VALUES (?, ?, ?, ?, ?, ?)",
                 ("p1", "m1", sid, 2000, 2000, json.dumps({"type": "tool", "tool": "bash", "state": {"input": {"command": "ls"}}})))
    conn.execute("INSERT INTO part VALUES (?, ?, ?, ?, ?, ?)",
                 ("p2", "m1", sid, 3000, 3000, json.dumps({"type": "tool", "tool": "read", "state": {"input": {"file_path": "x.txt"}}})))
    conn.commit()
    conn.close()

    import causetrace.hooks.opencode_parser as mod
    original = mod.DB_PATH
    mod.DB_PATH = db_path
    try:
        events = parse_session(sid)
        assert len(events) == 2
        assert events[0].tool_name == "Bash"
        assert events[1].tool_name == "Read"
        assert events[1].parent_event_id == events[0].event_id
    finally:
        mod.DB_PATH = original


def test_parse_session_not_found():
    """Non-existent session returns empty list."""
    tmpdir = Path(tempfile.mkdtemp())
    db_path = tmpdir / "opencode.db"

    import causetrace.hooks.opencode_parser as mod
    original = mod.DB_PATH
    mod.DB_PATH = db_path
    try:
        events = parse_session("nonexistent")
        assert events == []
    finally:
        mod.DB_PATH = original


def test_parse_session_no_db():
    """When DB doesn't exist, returns empty list."""
    import causetrace.hooks.opencode_parser as mod
    original = mod.DB_PATH
    mod.DB_PATH = Path("/nonexistent/opencode.db")
    try:
        events = parse_session("x")
        assert events == []
    finally:
        mod.DB_PATH = original


def test_list_sessions():
    """list_sessions returns sessions from DB."""
    tmpdir = Path(tempfile.mkdtemp())
    db_path = tmpdir / "opencode.db"

    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE session (id TEXT PRIMARY KEY, slug TEXT, title TEXT, project_id TEXT, "
                 "time_created INTEGER, time_updated INTEGER)")
    conn.execute("INSERT INTO session VALUES (?, ?, ?, ?, ?, ?)",
                 ("s1", "slug1", "Title One", "p1", 1000, 2000))
    conn.execute("INSERT INTO session VALUES (?, ?, ?, ?, ?, ?)",
                 ("s2", "slug2", "Title Two", "p1", 3000, 4000))
    conn.commit()
    conn.close()

    import causetrace.hooks.opencode_parser as mod
    original = mod.DB_PATH
    mod.DB_PATH = db_path
    try:
        sessions = list_sessions()
        assert len(sessions) == 2
        assert sessions[0]["session_id"] == "s2"  # newest first
        assert sessions[1]["slug"] == "slug1"
        assert sessions[0]["title"] == "Title Two"
    finally:
        mod.DB_PATH = original


def test_list_sessions_no_db():
    """When DB doesn't exist, returns empty list."""
    import causetrace.hooks.opencode_parser as mod
    original = mod.DB_PATH
    mod.DB_PATH = Path("/nonexistent/opencode.db")
    try:
        assert list_sessions() == []
    finally:
        mod.DB_PATH = original
