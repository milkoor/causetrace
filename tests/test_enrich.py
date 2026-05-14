"""Tests for the Claude Code session enrich parser."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from causetrace.hooks.claude_project_parser import (
    _parse_block,
    _shorten_tool_input,
    parse_session,
    list_sessions,
    PROJECTS_DIR,
)


def test_parse_block_thinking():
    block = {"type": "thinking", "thinking": "the model's reasoning", "signature": "sig123"}
    result = _parse_block(block, 0)
    assert result["type"] == "thinking"
    assert result["content"] == "the model's reasoning"
    assert result["signature"] == "sig123"


def test_parse_block_tool_use():
    block = {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}, "id": "tu_1"}
    result = _parse_block(block, 0)
    assert result["type"] == "tool_use"
    assert result["tool_name"] == "Bash"
    assert result["tool_input"] == {"command": "ls"}
    assert result["tool_use_id"] == "tu_1"


def test_parse_block_tool_result():
    block = {"type": "tool_result", "tool_use_id": "tu_1", "content": [{"text": "file1.txt\nfile2.txt"}]}
    result = _parse_block(block, 0)
    assert result["type"] == "tool_result"
    assert result["tool_use_id"] == "tu_1"
    assert "file1.txt" in result["content"]


def test_parse_block_text():
    block = {"type": "text", "text": "Hello, I can help with that."}
    result = _parse_block(block, 0)
    assert result["type"] == "text"
    assert result["content"] == "Hello, I can help with that."


def test_parse_block_unknown():
    block = {"type": "unknown_type", "data": "something"}
    result = _parse_block(block, 0)
    assert result["type"] == "unknown_type"


def test_shorten_tool_input_keeps_relevant():
    inp = {"command": "ls", "file_path": "/tmp", "secret": "dontkeep"}
    result = _shorten_tool_input(inp)
    assert "command" in result
    assert "file_path" in result
    assert "secret" not in result


def test_parse_session_from_jsonl():
    """Parse a real JSONL-like session and verify event structure."""
    lines = [
        json.dumps({
            "message": {
                "content": [
                    {"type": "thinking", "thinking": "I should read the file first", "signature": "s1"}
                ],
                "model": "claude-sonnet-4-20250514"
            },
            "timestamp": "2026-05-14T03:07:51Z"
        }),
        json.dumps({
            "message": {
                "content": [
                    {
                        "type": "tool_use", "name": "Read", "id": "tu_1",
                        "input": {"file_path": "/tmp/test.txt"}
                    }
                ],
                "model": "claude-sonnet-4-20250514"
            },
            "timestamp": "2026-05-14T03:07:52Z"
        }),
        json.dumps({
            "message": {
                "content": [
                    {"type": "text", "text": "Here is the content of the file."}
                ],
                "model": "claude-sonnet-4-20250514"
            },
            "timestamp": "2026-05-14T03:07:53Z"
        }),
    ]

    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp) / "test-project"
        project_dir.mkdir(parents=True)
        session_file = project_dir / "test_session.jsonl"
        session_file.write_text("\n".join(lines))

        # Temporarily override PROJECTS_DIR
        original = PROJECTS_DIR
        import causetrace.hooks.claude_project_parser as mod
        mod.PROJECTS_DIR = Path(tmp)
        try:
            events = parse_session("test_session")
            assert len(events) == 3
            assert events[0].event_type == "reasoning"
            assert events[0].tool_name == "Thinking"
            assert events[1].event_type == "tool_call"
            assert events[1].tool_name == "Read"
            assert events[1].parent_event_id == events[0].event_id
            assert events[2].event_type == "reasoning"
            assert events[2].tool_name == "Response"
            assert events[2].parent_event_id == events[1].event_id
            assert events[0].model == "claude-sonnet-4-20250514"
        finally:
            mod.PROJECTS_DIR = original


def test_parse_session_multiple_tool_calls():
    """Test a sequence with multiple tool calls interleaved with thinking."""
    lines = [
        json.dumps({"message": {"content": [
            {"type": "thinking", "thinking": "First, read the file", "signature": "s1"}
        ]}}),
        json.dumps({"message": {"content": [
            {"type": "tool_use", "name": "Read", "id": "tu_1", "input": {"file_path": "x.txt"}}
        ]}}),
        json.dumps({"message": {"content": [
            {"type": "thinking", "thinking": "Now edit it", "signature": "s2"}
        ]}}),
        json.dumps({"message": {"content": [
            {"type": "tool_use", "name": "Edit", "id": "tu_2", "input": {"file_path": "x.txt", "old_string": "a", "new_string": "b"}}
        ]}}),
        json.dumps({"message": {"content": [
            {"type": "thinking", "thinking": "Done", "signature": "s3"}
        ]}}),
    ]

    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp) / "p"
        project_dir.mkdir(parents=True)
        session_file = project_dir / "multi.jsonl"
        session_file.write_text("\n".join(lines))

        import causetrace.hooks.claude_project_parser as mod
        original = mod.PROJECTS_DIR
        mod.PROJECTS_DIR = Path(tmp)
        try:
            events = parse_session("multi")
            assert len(events) == 5
            # Check causal chain: 0→1→2→3→4
            for i in range(1, len(events)):
                assert events[i].parent_event_id == events[i - 1].event_id, f"Break at {i}"
            assert events[1].tool_name == "Read"
            assert events[3].tool_name == "Edit"
        finally:
            mod.PROJECTS_DIR = original


def test_parse_session_no_thinking_blocks():
    """Session without thinking blocks should still produce tool_call events."""
    lines = [
        json.dumps({"message": {"content": [
            {"type": "tool_use", "name": "Bash", "id": "tu_1", "input": {"command": "ls"}}
        ]}}),
        json.dumps({"message": {"content": [
            {"type": "tool_use", "name": "Read", "id": "tu_2", "input": {"file_path": "x.txt"}}
        ]}}),
    ]

    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp) / "p"
        project_dir.mkdir(parents=True)
        session_file = project_dir / "no_think.jsonl"
        session_file.write_text("\n".join(lines))

        import causetrace.hooks.claude_project_parser as mod
        original = mod.PROJECTS_DIR
        mod.PROJECTS_DIR = Path(tmp)
        try:
            events = parse_session("no_think")
            assert len(events) == 2
            assert events[0].tool_name == "Bash"
            assert events[1].tool_name == "Read"
            # Sequential tool calls are still causally linked
            assert events[1].parent_event_id == events[0].event_id
        finally:
            mod.PROJECTS_DIR = original


def test_parse_session_unknown_block_types():
    """Unknown block types should be skipped without crashing."""
    lines = [
        json.dumps({"message": {"content": [
            {"type": "thinking", "thinking": "Let me do this", "signature": "s1"},
            {"type": "tool_use", "name": "Bash", "id": "tu_1", "input": {"command": "echo hi"}},
            {"type": "weird_format", "data": "unknown"},
        ]}}),
    ]

    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp) / "p"
        project_dir.mkdir(parents=True)
        session_file = project_dir / "weird.jsonl"
        session_file.write_text("\n".join(lines))

        import causetrace.hooks.claude_project_parser as mod
        original = mod.PROJECTS_DIR
        mod.PROJECTS_DIR = Path(tmp)
        try:
            events = parse_session("weird")
            assert len(events) == 2  # weird block skipped
            assert events[1].parent_event_id == events[0].event_id
        finally:
            mod.PROJECTS_DIR = original


def test_list_sessions():
    """list_sessions should find all .jsonl files excluding memory logs."""
    with tempfile.TemporaryDirectory() as tmp:
        for name in ["sess_a", "sess_b"]:
            (Path(tmp) / name).mkdir(parents=True)
            (Path(tmp) / name / "session1.jsonl").write_text("{}")
            (Path(tmp) / name / "session2.jsonl").write_text("{}\n{}")
            (Path(tmp) / name / "memory.jsonl").write_text("{}")

        import causetrace.hooks.claude_project_parser as mod
        original = mod.PROJECTS_DIR
        mod.PROJECTS_DIR = Path(tmp)
        try:
            sessions = list_sessions()
            assert len(sessions) == 4  # 2 sessions × 2 files (memory excluded)
            ids = [s["session_id"] for s in sessions]
            assert "session1" in ids
            assert "session2" in ids
            assert "memory" not in ids
            for s in sessions:
                if s["session_id"] == "session2":
                    assert s["lines"] == 2
        finally:
            mod.PROJECTS_DIR = original


def test_parse_session_not_found():
    """parse_session should return empty list for nonexistent session."""
    with tempfile.TemporaryDirectory() as tmp:
        import causetrace.hooks.claude_project_parser as mod
        original = mod.PROJECTS_DIR
        mod.PROJECTS_DIR = Path(tmp)
        try:
            events = parse_session("nonexistent")
            assert events == []
        finally:
            mod.PROJECTS_DIR = original
