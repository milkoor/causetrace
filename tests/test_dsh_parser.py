"""Tests for the DeepSeek Harness (DSH) session log parser."""

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from causetrace.hooks.dsh_parser import (
    find_session_file,
    list_sessions,
    load_records,
    parse_session,
    _detect_provider,
    _ms_to_iso,
)

T0 = 1_789_000_000_000  # epoch ms, deterministic session start


def _rec(seq, rtype, time_ms, data):
    return {"type": rtype, "seq": seq, "time": time_ms, "data": data}


def _header(session_id, cwd="/tmp/project"):
    return {
        "type": "session",
        "version": 0,
        "id": session_id,
        "createdAt": T0,
        "cwd": cwd,
        "delegationDepth": 0,
        "agentPreset": "default",
    }


def _user_text(text, kind="user"):
    return {"content": [{"type": "text", "text": text}],
            "source": {"kind": kind}, "role": "user", "id": "msg-1"}


def _assistant(turn, step, blocks):
    return {"turn": turn, "step": step,
            "message": {"role": "assistant", "content": blocks}}


def _call(turn, step, call_id, name, arguments):
    return {"turn": turn, "step": step, "callId": call_id,
            "name": name, "arguments": json.dumps(arguments)}


def _result(turn, step, call_id, text, is_error=False):
    return {"turn": turn, "step": step,
            "message": {
                "source": {"kind": "tool", "callId": call_id},
                "role": "user",
                "content": [{
                    "type": "tool-result", "toolCallId": call_id,
                    "content": [{"type": "text", "text": text}],
                    "isError": is_error,
                }],
            }}


def _write_session(root: Path, session_id: str, records, zstd: bool = False) -> Path:
    sess_dir = root / "--tmp-project--" / session_id
    sess_dir.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(r) for r in records) + "\n"
    if zstd:
        zstandard = pytest.importorskip("zstandard")
        path = sess_dir / "session.jsonl.zstd"
        path.write_bytes(zstandard.ZstdCompressor().compress(text.encode("utf-8")))
    else:
        path = sess_dir / "session.jsonl"
        path.write_text(text, encoding="utf-8")
    return path


def _rich_records(sid: str = "session-abc"):
    """A realistic two-turn session with parallel calls, fan-in, a slash
    command, an injected plugin message, and streaming noise to skip."""
    return [
        _header(sid),
        _rec(1, "permission/preset", T0, {"preset": "workspace-write"}),
        _rec(2, "turn/start", T0 + 10, {"turn": 1}),
        _rec(3, "user/message", T0 + 11, _user_text("do the thing")),
        _rec(4, "user/message", T0 + 12, _user_text("<memory reminder>", kind="plugin")),
        _rec(5, "request/header", T0 + 13,
             {"header": {"config": {"provider": "b", "model": "qwen3.8-flash"}}}),
        _rec(6, "step/start", T0 + 14, {"turn": 1, "step": 1}),
        _rec(7, "assistant/chunk", T0 + 15, {"turn": 1, "step": 1, "chunk": {"type": "block-start"}}),
        _rec(8, "assistant/message", T0 + 20, _assistant(1, 1, [
            {"type": "reasoning", "text": "I should inspect two files in parallel."},
            {"type": "tool-call", "toolCallId": "c1", "toolName": "read", "input": {}},
            {"type": "tool-call", "toolCallId": "c2", "toolName": "read", "input": {}},
        ])),
        _rec(9, "tool/call", T0 + 21, _call(1, 1, "c1", "read", {"file_path": "a.py"})),
        _rec(10, "tool/call", T0 + 21, _call(1, 1, "c2", "read", {"file_path": "b.py"})),
        _rec(11, "step/end", T0 + 22, {"turn": 1, "step": 1}),
        _rec(12, "tool/result", T0 + 30, _result(1, 1, "c1", "A contents")),
        _rec(13, "tool/result", T0 + 31, _result(1, 1, "c2", "B contents")),
        _rec(14, "step/start", T0 + 32, {"turn": 1, "step": 2}),
        _rec(15, "assistant/message", T0 + 40, _assistant(1, 2, [
            {"type": "reasoning", "text": "Both files read; write the fix."},
            {"type": "text", "text": "Fixing now."},
        ])),
        _rec(16, "tool/call", T0 + 41, _call(1, 2, "c3", "edit", {"file_path": "a.py"})),
        _rec(17, "tool/result", T0 + 50, _result(1, 2, "c3", "Error: nope", is_error=True)),
        _rec(18, "command/run", T0 + 55,
             {"commandId": "cmd-1", "name": "permission", "args": " plan", "source": {"kind": "user"}}),
        _rec(19, "command/done", T0 + 56,
             {"commandId": "cmd-1", "kind": "success", "text": "preset plan"}),
        _rec(20, "turn/end", T0 + 60, {"turn": 1, "reason": {"kind": "completed"}}),
        _rec(21, "turn/start", T0 + 70, {"turn": 2}),
        _rec(22, "user/message", T0 + 71, _user_text("thanks")),
        _rec(23, "session/title", T0 + 72, {"title": "Do the thing"}),
    ]


@pytest.fixture
def dsh_home(monkeypatch):
    root = Path(tempfile.mkdtemp())
    import causetrace.hooks.dsh_parser as mod
    monkeypatch.setattr(mod, "SESSIONS_DIR", root)
    return root


def test_detect_provider():
    assert _detect_provider("qwen3.8-flash", "b") == "alibaba"
    assert _detect_provider("deepseek-v4-pro", "deepseek-official") == "deepseek"
    assert _detect_provider("glm-5.3-flash", "b") == "zhipu"
    assert _detect_provider("claude-sonnet-4", "anthropic") == "anthropic"
    assert _detect_provider("weird-model", "my-route") == "my-route"
    assert _detect_provider(None, None) == ""


def test_ms_to_iso():
    iso = _ms_to_iso(T0)
    assert iso is not None and "T" in iso and iso.endswith("+00:00")
    assert _ms_to_iso("bad") is None
    assert _ms_to_iso(None) is None


def test_parse_session_fan_out_and_fan_in(dsh_home):
    sid = "session-abc"
    _write_session(dsh_home, sid, _rich_records())
    events = parse_session(sid)
    by_name = {}
    for e in events:
        by_name.setdefault(e.tool_name, []).append(e)

    # user roots: only kind=user messages become user_input events
    prompts = by_name["Prompt"]
    assert len(prompts) == 2  # plugin injection skipped
    assert prompts[0].event_type == "user_input"
    assert prompts[0].caused_by == "user"
    assert prompts[0].parent_event_id is None

    thinkings = by_name["Thinking"]
    assert thinkings[0].event_type == "reasoning"
    assert thinkings[0].parent_event_id == prompts[0].event_id  # caused by user prompt

    # fan-out: both parallel reads share the step-1 reasoning as parent
    reads = by_name["read"]
    assert len(reads) == 2
    assert reads[0].parent_event_id == thinkings[0].event_id
    assert reads[1].parent_event_id == thinkings[0].event_id
    assert reads[0].caused_by == "reasoning"

    # outputs merged into calls + real duration
    assert reads[0].tool_output == "A contents"
    assert reads[1].tool_output == "B contents"
    assert reads[0].duration_ms == 9.0
    assert reads[1].duration_ms == 10.0

    # fan-in: step-2 reasoning is caused by BOTH parallel calls
    assert thinkings[1].parent_event_id == f"{reads[0].event_id},{reads[1].event_id}"

    # assistant text block becomes Response chained after Thinking
    responses = by_name["Response"]
    assert responses[0].parent_event_id == thinkings[1].event_id

    # second sequential call fans in on step-2 reasoning (previous step had a call: c3 → edit; step1 calls consumed)
    edits = by_name["edit"]
    assert len(edits) == 1
    assert edits[0].parent_event_id == thinkings[1].event_id
    # error marker preserved
    assert "Error: nope" in edits[0].tool_output
    assert "[isError=true]" in edits[0].tool_output

    # slash command as context_update
    cmds = by_name["/permission"]
    assert len(cmds) == 1
    assert cmds[0].event_type == "context_update"
    assert cmds[0].tool_output == "preset plan"

    # second turn roots at its own user message
    assert prompts[1].parent_event_id is None

    # attribution from request/header
    assert reads[0].model == "qwen3.8-flash"
    assert reads[0].provider == "alibaba"
    assert reads[0].agent == "dsh"


def test_out_of_order_result_never_yields_negative_duration(dsh_home):
    """A tool/result stamped before its call (clock-ordered log) still merges
    its output, but duration_ms stays None — durations are never negative."""
    sid = "session-neg"
    _write_session(dsh_home, sid, [
        _header(sid),
        _rec(1, "user/message", T0, _user_text("go")),
        _rec(2, "assistant/message", T0 + 1, _assistant(1, 1, [
            {"type": "reasoning", "text": "run"},
            {"type": "tool-call", "toolCallId": "c1", "toolName": "bash", "input": {}},
        ])),
        _rec(3, "tool/call", T0 + 100, _call(1, 1, "c1", "bash", {"command": "true"})),
        _rec(4, "tool/result", T0 + 50, _result(1, 1, "c1", "ok")),
    ])
    events = parse_session(sid)
    call = next(e for e in events if e.tool_name == "bash")
    assert call.duration_ms is None
    assert call.tool_output == "ok"  # merge still happens


def test_autonomous_turn_chains_from_previous_calls(dsh_home):
    """Goal-continuation turns have no new user message; the next step's
    first event must still be caused by the previous turn's last calls."""
    sid = "session-auto"
    recs = [
        _header(sid),
        _rec(1, "user/message", T0, _user_text("go")),
        _rec(2, "step/start", T0, {"turn": 1, "step": 1}),
        _rec(3, "tool/call", T0 + 1, _call(1, 1, "j1", "bash", {"command": "ls"})),
        _rec(4, "tool/result", T0 + 2, _result(1, 1, "j1", "out")),
        # turn 2 starts with no user message (auto-continuation)
        _rec(5, "turn/start", T0 + 3, {"turn": 2}),
        _rec(6, "assistant/message", T0 + 4, _assistant(2, 1, [
            {"type": "reasoning", "text": "continue"}])),
    ]
    _write_session(dsh_home, sid, recs)
    events = parse_session(sid)
    calls = [e for e in events if e.tool_name == "bash"]
    think = [e for e in events if e.tool_name == "Thinking"]
    assert think[0].parent_event_id == calls[0].event_id


def test_step_without_reasoning_fans_from_prev_calls(dsh_home):
    sid = "session-noreason"
    recs = [
        _header(sid),
        _rec(1, "user/message", T0, _user_text("go")),
        _rec(2, "tool/call", T0 + 1, _call(1, 1, "j1", "bash", {"command": "ls"})),
        _rec(3, "tool/result", T0 + 2, _result(1, 1, "j1", "out")),
        _rec(4, "tool/call", T0 + 3, _call(1, 2, "j2", "read", {"file_path": "x"})),
    ]
    _write_session(dsh_home, sid, recs)
    events = parse_session(sid)
    bash = next(e for e in events if e.tool_name == "bash")
    read = next(e for e in events if e.tool_name == "read")
    prompt = next(e for e in events if e.tool_name == "Prompt")
    assert bash.parent_event_id == prompt.event_id
    assert read.parent_event_id == bash.event_id


def test_zstd_session(dsh_home):
    pytest.importorskip("zstandard")
    sid = "session-zstd"
    _write_session(dsh_home, sid, _rich_records(), zstd=True)
    events = parse_session(sid)
    assert events
    assert any(e.tool_name == "Thinking" for e in events)


def test_partial_frame_tolerated(dsh_home):
    """A live session can end mid-write; parsing must still return events."""
    pytest.importorskip("zstandard")
    import zstandard
    sid = "session-partial"
    text = "\n".join(json.dumps(r) for r in _rich_records()) + "\n"
    sess_dir = dsh_home / "--tmp-project--" / sid
    sess_dir.mkdir(parents=True, exist_ok=True)
    full = zstandard.ZstdCompressor().compress(text.encode("utf-8"))
    # keep header frame but truncate the tail of the second frame
    (sess_dir / "session.jsonl.zstd").write_bytes(full[:30])
    events = parse_session(sid)
    # garbage bytes decode to nothing useful → no events, but no crash
    assert events == []


def test_find_and_list_sessions(dsh_home):
    sid = "session-listed"
    path = _write_session(dsh_home, sid, _rich_records(sid))
    assert find_session_file(sid) == path
    assert find_session_file("session-list") == path  # prefix match
    assert find_session_file("nope") is None

    sessions = list_sessions()
    assert len(sessions) == 1
    s = sessions[0]
    assert s["session_id"] == sid
    assert s["title"] == "Do the thing"
    assert s["model"] == "qwen3.8-flash"
    assert s["cwd"] == "/tmp/project"
    assert s["created"].startswith("2026-")


def test_load_records_skips_garbage(dsh_home):
    sess_dir = dsh_home / "ws" / "session-garbage"
    sess_dir.mkdir(parents=True)
    (sess_dir / "session.jsonl").write_text(
        '{"type":"session","id":"session-garbage"}\nnot json\n\n{"type":"turn/start","seq":1,"time":1,"data":{}}\n',
        encoding="utf-8")
    recs = load_records(sess_dir / "session.jsonl")
    assert [r["type"] for r in recs] == ["session", "turn/start"]


def test_empty_session_dir(dsh_home):
    assert parse_session("missing") == []
    assert list_sessions() == []
