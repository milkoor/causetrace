"""Runtime Invariant Tests for causetrace.

These test Runtime invariants, NOT business logic:
  1. Serialization roundtrip: event == from_dict(to_dict(event))
  2. Causality chain validity: parent_event_id chain is acyclic
  3. Append-only integrity: load(store(append(x))) == x
  4. Renderer stability: never crashes on any input

Run:  python3 -m pytest tests/test_invariants.py -v
"""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from causetrace.core import (
    JSONStore, ReplayEngine, TimelineRenderer, ToolEvent, TraceRecorder, build_tree,
)


def make_chain(length: int = 4) -> list[ToolEvent]:
    """Create a causal chain: ev0 → ev1 → ev2 → ev3"""
    recorder = TraceRecorder()
    for i in range(length):
        recorder.record_call(
            tool_name="Read" if i % 2 == 0 else "Bash",
            tool_input={"key": f"val{i}"},
            tool_output=f"out{i}",
            duration_ms=float(i * 100),
        )
    return recorder.events


def make_fork() -> list[ToolEvent]:
    """Create a fork: root → child1, root → child2"""
    root = ToolEvent(tool_name="Read", tool_input={"file": "x"}, event_id="root")
    c1 = ToolEvent(tool_name="Bash", tool_input={"cmd": "c1"}, event_id="c1", parent_event_id="root")
    c2 = ToolEvent(tool_name="Grep", tool_input={"pat": "c2"}, event_id="c2", parent_event_id="root")
    return [root, c1, c2]


def test_serialization_roundtrip_simple():
    event = ToolEvent(tool_name="Bash", tool_input={"command": "ls -la"}, tool_output="file1\nfile2", duration_ms=42.5)
    restored = ToolEvent.from_dict(event.to_dict())
    assert restored.event_id == event.event_id
    assert restored.tool_name == event.tool_name
    assert restored.duration_ms == event.duration_ms


def test_serialization_roundtrip_tool_output():
    event = ToolEvent(tool_name="Write", tool_input={"file_path": "/tmp/x.py", "content": "..."}, tool_output={"output": "written", "size": 42}, caused_by="task_execution")
    restored = ToolEvent.from_dict(event.to_dict())
    assert restored.event_id == event.event_id
    assert restored.caused_by == "task_execution"


def test_serialization_roundtrip_causal():
    events = make_chain()
    for orig in events:
        restored = ToolEvent.from_dict(orig.to_dict())
        assert restored.event_id == orig.event_id
        assert restored.parent_event_id == orig.parent_event_id
        assert restored.caused_by == orig.caused_by
        assert restored.duration_ms == orig.duration_ms


def test_serialization_model_fields():
    event = ToolEvent(tool_name="Bash", tool_input={}, model="gpt-4o", provider="openai", agent="research")
    d = event.to_dict()
    assert d.get("model") == "gpt-4o"
    assert d.get("provider") == "openai"
    assert d.get("agent") == "research"
    restored = ToolEvent.from_dict(d)
    assert restored.model == "gpt-4o"
    assert restored.provider == "openai"
    assert restored.agent == "research"


def test_serialization_optional_fields_absent():
    event = ToolEvent(tool_name="Bash", tool_input={"cmd": "test"})
    d = event.to_dict()
    assert "parent_event_id" not in d
    assert "caused_by" not in d
    assert "event_type" not in d
    restored = ToolEvent.from_dict(d)
    assert restored.tool_name == "Bash"
    assert restored.parent_event_id is None


def test_causality_chain_links():
    events = make_chain(5)
    for i in range(1, len(events)):
        assert events[i].parent_event_id == events[i - 1].event_id, f"event[{i}] not linked to event[{i-1}]"


def test_causality_no_orphan_references():
    """All parent_event_ids must point to a real event, unless it's the root."""
    events = make_chain(3)
    by_id = {e.event_id for e in events}
    for ev in events:
        if ev.parent_event_id:
            assert ev.parent_event_id in by_id, f"parent_event_id {ev.parent_event_id} not found in events"


def test_causality_tree_roots():
    events = make_fork()
    roots = build_tree(events)
    assert len(roots) == 1, "fork should have exactly 1 root"
    assert roots[0]["event"].event_id == "root"
    assert len(roots[0]["children"]) == 2


def test_causality_new_group_resets_chain():
    recorder = TraceRecorder()
    recorder.record_call(tool_name="Read", tool_input={"f": "a"})
    recorder.new_group()
    recorder.record_call(tool_name="Bash", tool_input={"cmd": "b"})
    events = recorder.events
    assert events[1].parent_event_id != events[0].event_id, "new_group did not reset causality"
    assert events[1].parent_event_id is None, "new_group root should have no parent"


def test_json_store_append_then_load():
    with tempfile.TemporaryDirectory() as tmp:
        store = JSONStore(store_dir=tmp)
        recorder = TraceRecorder(store=store)
        recorder.record_call(tool_name="Read", tool_input={"x": "1"})
        recorder.record_call(tool_name="Bash", tool_input={"cmd": "test"})
        loaded = store.load(recorder.session_id)
        assert len(loaded) == 2
        assert loaded[0].tool_name == "Read"
        assert loaded[1].tool_name == "Bash"


def test_json_store_append_only_preserves_order():
    with tempfile.TemporaryDirectory() as tmp:
        store = JSONStore(store_dir=tmp)
        recorder = TraceRecorder(store=store)
        recorder.record_call(tool_name="Read", tool_input={"x": "a"})
        recorder.record_call(tool_name="Write", tool_input={"y": "b"})
        recorder.record_call(tool_name="Bash", tool_input={"z": "c"})
        loaded = store.load(recorder.session_id)
        names = [e.tool_name for e in loaded]
        assert names == ["Read", "Write", "Bash"], f"order broken: {names}"


def test_json_store_multiple_sessions():
    with tempfile.TemporaryDirectory() as tmp:
        store = JSONStore(store_dir=tmp)
        r1 = TraceRecorder(store=store)
        r1.record_call(tool_name="Read", tool_input={})
        r2 = TraceRecorder(store=store)
        r2.record_call(tool_name="Bash", tool_input={})
        sessions = store.list_sessions()
        assert len(sessions) == 2
        assert r1.session_id in sessions
        assert r2.session_id in sessions


def test_timeline_renderer_never_crashes():
    events = make_chain()
    TimelineRenderer.render(events)
    TimelineRenderer.render(events, show_output=True)
    TimelineRenderer.render_tree(events)


def test_timeline_renderer_empty():
    TimelineRenderer.render([])
    TimelineRenderer.render_tree([])


def test_timeline_renderer_large_output():
    event = ToolEvent(tool_name="Bash", tool_input={"command": "x" * 5000}, tool_output="y" * 5000)
    TimelineRenderer.render([event], show_output=True)


def test_replay_engine_never_crashes():
    events = make_chain()
    engine = ReplayEngine(events)
    engine.trace()
    engine.summary()


def test_replay_engine_empty():
    engine = ReplayEngine([])
    engine.trace()
    assert "0 events" in engine.summary()


def test_build_tree_empty():
    assert build_tree([]) == []


def test_build_tree_disconnected():
    events = [
        ToolEvent(tool_name="Bash", tool_input={}, event_id="a"),
        ToolEvent(tool_name="Read", tool_input={}, event_id="b"),
    ]
    roots = build_tree(events)
    assert len(roots) == 2


def test_replay_parent_links_referenced():
    """Every ← parent reference in replay output should point to an existing event."""
    events = make_chain(6)
    engine = ReplayEngine(events)
    trace_output = engine.trace()
    for ev in events:
        if ev.parent_event_id:
            parent = next(e for e in events if e.event_id == ev.parent_event_id)
            assert parent.tool_name in trace_output
