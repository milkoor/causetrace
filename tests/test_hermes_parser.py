"""Tests for the Hermes Agent session parser."""

import json
import sys
import tempfile
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from causetrace.hooks.hermes_parser import (
    parse_session,
    list_sessions,
    _detect_provider,
    _parse_timestamp,
    HERMES_DB,
)


def test_detect_provider():
    assert _detect_provider("deepseek-v4-pro") == "deepseek"
    assert _detect_provider("deepseek-r1-250120") == "deepseek"
    assert _detect_provider("doubao-seed-2-0-pro-260215") == "bytedance"
    assert _detect_provider("claude-sonnet-4") == "anthropic"
    assert _detect_provider("gpt-4o") == "openai"
    assert _detect_provider("gemini-2.5-pro") == "google"
    assert _detect_provider("") == ""
    assert _detect_provider(None) == ""


def test_parse_timestamp():
    ts = _parse_timestamp(1777032617.90543)
    assert ts.startswith("2026-")
    assert "T" in ts


def test_list_sessions_empty():
    tmpdir = Path(tempfile.mkdtemp())
    db_path = tmpdir / "state.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT, model TEXT, "
                 "started_at REAL, ended_at REAL, message_count INTEGER DEFAULT 0, "
                 "tool_call_count INTEGER DEFAULT 0, title TEXT, cwd TEXT, git_branch TEXT)")
    conn.commit()
    conn.close()

    import causetrace.hooks.hermes_parser as mod
    original = mod.HERMES_DB
    mod.HERMES_DB = db_path
    try:
        sessions = list_sessions()
        assert sessions == []
    finally:
        mod.HERMES_DB = original


def test_parse_session_causal_chain():
    tmpdir = Path(tempfile.mkdtemp())
    db_path = tmpdir / "state.db"

    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT, model TEXT, "
                 "started_at REAL, ended_at REAL, message_count INTEGER DEFAULT 0, "
                 "tool_call_count INTEGER DEFAULT 0, title TEXT, cwd TEXT, git_branch TEXT)")
    conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                 "session_id TEXT NOT NULL REFERENCES sessions(id), "
                 "role TEXT NOT NULL, content TEXT, tool_call_id TEXT, tool_calls TEXT, "
                 "tool_name TEXT, timestamp REAL NOT NULL, "
                 "token_count INTEGER, finish_reason TEXT, reasoning TEXT, "
                 "reasoning_content TEXT, reasoning_details TEXT, "
                 "active INTEGER NOT NULL DEFAULT 1)")

    sid = "test_chain"
    conn.execute("INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 (sid, "cli", "deepseek-v4-pro", 1000.0, 2000.0, 3, 2, None, None, None))

    # user message
    conn.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                 (sid, "user", "run ls and read a file", 1000.0))

    # assistant message with reasoning + tool_calls
    conn.execute("INSERT INTO messages (session_id, role, tool_calls, timestamp, reasoning) VALUES (?, ?, ?, ?, ?)",
                 (sid, "assistant",
                  json.dumps([{"id": "call_1", "call_id": "call_1", "type": "function",
                               "function": {"name": "bash", "arguments": '{"command":"ls"}'}}]),
                  2000.0, "I should list files first."))

    # tool result
    conn.execute("INSERT INTO messages (session_id, role, tool_call_id, content, tool_name, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                 (sid, "tool", "call_1", "file1.txt\nfile2.txt", "bash", 3000.0))

    # second assistant with tool_call
    conn.execute("INSERT INTO messages (session_id, role, tool_calls, timestamp) VALUES (?, ?, ?, ?)",
                 (sid, "assistant",
                  json.dumps([{"id": "call_2", "call_id": "call_2", "type": "function",
                               "function": {"name": "read", "arguments": '{"filePath":"file1.txt"}'}}]),
                  4000.0))

    # tool result
    conn.execute("INSERT INTO messages (session_id, role, tool_call_id, content, tool_name, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                 (sid, "tool", "call_2", "content here", "read", 5000.0))

    conn.commit()
    conn.close()

    import causetrace.hooks.hermes_parser as mod
    original = mod.HERMES_DB
    mod.HERMES_DB = db_path
    try:
        events = parse_session(sid)
        assert len(events) == 3  # 1 thinking + 2 tool calls

        # First event: thinking
        assert events[0].tool_name == "Thinking"
        assert events[0].event_type == "reasoning"
        assert events[0].parent_event_id is None  # root
        assert events[0].model == "deepseek-v4-pro"
        assert events[0].provider == "deepseek"
        assert events[0].agent == "hermes"

        # Second event: bash tool call
        assert events[1].tool_name == "bash"
        assert events[1].event_type == "tool_call"
        assert events[1].tool_input == {"command": "ls"}
        assert events[1].tool_output == "file1.txt\nfile2.txt"
        assert events[1].parent_event_id == events[0].event_id

        # Third event: read tool call
        assert events[2].tool_name == "read"
        assert events[2].event_type == "tool_call"
        assert events[2].tool_input == {"filePath": "file1.txt"}
        assert events[2].tool_output == "content here"
        assert events[2].parent_event_id == events[1].event_id
    finally:
        mod.HERMES_DB = original


def test_parse_session_only_tools():
    """Session without reasoning blocks."""
    tmpdir = Path(tempfile.mkdtemp())
    db_path = tmpdir / "state.db"

    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT, model TEXT, "
                 "started_at REAL, ended_at REAL, message_count INTEGER DEFAULT 0, "
                 "tool_call_count INTEGER DEFAULT 0, title TEXT, cwd TEXT, git_branch TEXT)")
    conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                 "session_id TEXT NOT NULL REFERENCES sessions(id), "
                 "role TEXT NOT NULL, content TEXT, tool_call_id TEXT, tool_calls TEXT, "
                 "tool_name TEXT, timestamp REAL NOT NULL, "
                 "token_count INTEGER, finish_reason TEXT, reasoning TEXT, "
                 "reasoning_content TEXT, reasoning_details TEXT, "
                 "active INTEGER NOT NULL DEFAULT 1)")

    sid = "test_tools"
    conn.execute("INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 (sid, "cli", "doubao-seed-2-0-pro-260215", 1000.0, 2000.0, 2, 2, None, None, None))

    conn.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                 (sid, "user", "edit the file", 1000.0))

    conn.execute("INSERT INTO messages (session_id, role, tool_calls, timestamp) VALUES (?, ?, ?, ?)",
                 (sid, "assistant",
                  json.dumps([{"id": "call_a", "call_id": "call_a", "type": "function",
                               "function": {"name": "edit", "arguments": '{"path":"x.py","old":"a","new":"b"}'}}]),
                  2000.0))

    conn.commit()
    conn.close()

    import causetrace.hooks.hermes_parser as mod
    original = mod.HERMES_DB
    mod.HERMES_DB = db_path
    try:
        events = parse_session(sid)
        assert len(events) == 1
        assert events[0].tool_name == "edit"
        assert events[0].event_type == "tool_call"
        assert events[0].provider == "bytedance"
        assert events[0].agent == "hermes"
    finally:
        mod.HERMES_DB = original


def test_parse_session_nonexistent():
    tmpdir = Path(tempfile.mkdtemp())
    db_path = tmpdir / "state.db"

    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT, model TEXT, "
                 "started_at REAL, ended_at REAL, message_count INTEGER DEFAULT 0, "
                 "tool_call_count INTEGER DEFAULT 0, title TEXT, cwd TEXT, git_branch TEXT)")
    conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                 "session_id TEXT NOT NULL REFERENCES sessions(id), "
                 "role TEXT NOT NULL, content TEXT, tool_call_id TEXT, tool_calls TEXT, "
                 "tool_name TEXT, timestamp REAL NOT NULL, "
                 "token_count INTEGER, finish_reason TEXT, reasoning TEXT, "
                 "reasoning_content TEXT, reasoning_details TEXT, "
                 "active INTEGER NOT NULL DEFAULT 1)")
    conn.commit()
    conn.close()

    import causetrace.hooks.hermes_parser as mod
    original = mod.HERMES_DB
    mod.HERMES_DB = db_path
    try:
        events = parse_session("nonexistent")
        assert events == []
    finally:
        mod.HERMES_DB = original


def test_parse_session_no_db():
    tmpdir = Path(tempfile.mkdtemp())
    import causetrace.hooks.hermes_parser as mod
    original = mod.HERMES_DB
    mod.HERMES_DB = tmpdir / "nonexistent.db"
    try:
        events = parse_session("any")
        assert events == []
        sessions = list_sessions()
        assert sessions == []
    finally:
        mod.HERMES_DB = original


def test_parse_session_multiple_tools_per_message():
    """Assistant message with multiple tool calls."""
    tmpdir = Path(tempfile.mkdtemp())
    db_path = tmpdir / "state.db"

    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT, model TEXT, "
                 "started_at REAL, ended_at REAL, message_count INTEGER DEFAULT 0, "
                 "tool_call_count INTEGER DEFAULT 0, title TEXT, cwd TEXT, git_branch TEXT)")
    conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                 "session_id TEXT NOT NULL REFERENCES sessions(id), "
                 "role TEXT NOT NULL, content TEXT, tool_call_id TEXT, tool_calls TEXT, "
                 "tool_name TEXT, timestamp REAL NOT NULL, "
                 "token_count INTEGER, finish_reason TEXT, reasoning TEXT, "
                 "reasoning_content TEXT, reasoning_details TEXT, "
                 "active INTEGER NOT NULL DEFAULT 1)")

    sid = "test_multi"
    conn.execute("INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 (sid, "cli", "claude-sonnet-4", 1000.0, 2000.0, 2, 2, None, None, None))

    conn.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                 (sid, "user", "do two things", 1000.0))

    conn.execute("INSERT INTO messages (session_id, role, tool_calls, timestamp) VALUES (?, ?, ?, ?)",
                 (sid, "assistant",
                  json.dumps([
                      {"id": "c1", "call_id": "c1", "type": "function",
                       "function": {"name": "bash", "arguments": '{"command":"ls"}'}},
                      {"id": "c2", "call_id": "c2", "type": "function",
                       "function": {"name": "read", "arguments": '{"filePath":"f.txt"}'}},
                  ]),
                  2000.0))

    conn.commit()
    conn.close()

    import causetrace.hooks.hermes_parser as mod
    original = mod.HERMES_DB
    mod.HERMES_DB = db_path
    try:
        events = parse_session(sid)
        assert len(events) == 2
        assert events[0].tool_name == "bash"
        assert events[1].tool_name == "read"
        assert events[1].parent_event_id == events[0].event_id
    finally:
        mod.HERMES_DB = original
