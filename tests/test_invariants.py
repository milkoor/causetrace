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
    compress_tree, CompressedRun,
    validate_session, SCHEMA_VERSION,
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


def test_serialization_schema_version():
    """to_dict always includes schema_version; roundtrip preserves it."""
    event = ToolEvent(tool_name="Bash", tool_input={"cmd": "ls"})
    d = event.to_dict()
    assert d.get("schema_version") == SCHEMA_VERSION
    restored = ToolEvent.from_dict(d)
    assert restored.tool_name == "Bash"


def test_validate_clean_session():
    events = make_chain(4)
    result = validate_session(events)
    assert result["valid"] is True
    assert result["broken_refs"] == []
    assert result["cycles"] == []


def test_validate_broken_refs():
    events = [
        ToolEvent(tool_name="Bash", tool_input={}, event_id="a", parent_event_id="nonexistent"),
    ]
    result = validate_session(events)
    assert result["valid"] is True  # broken refs = warning, not error
    assert len(result["broken_refs"]) == 1
    assert "nonexistent" in result["broken_refs"][0]


def test_validate_cycle():
    events = [
        ToolEvent(tool_name="Bash", tool_input={}, event_id="a", parent_event_id="b"),
        ToolEvent(tool_name="Read", tool_input={}, event_id="b", parent_event_id="a"),
    ]
    result = validate_session(events)
    assert result["valid"] is False
    assert len(result["cycles"]) >= 1


def test_validate_malformed_jsonl():
    result = validate_session([], raw_lines=['{"valid": true}', "not json", '{"valid": false}'])
    assert result["malformed_lines"] == 1
    assert result["valid"] is False


def test_validate_orphans():
    """Nodes refs with no local parent are counted as orphans."""
    events = [
        ToolEvent(tool_name="Bash", tool_input={}, event_id="a", parent_event_id="foreign"),
        ToolEvent(tool_name="Read", tool_input={}, event_id="b"),
    ]
    result = validate_session(events)
    assert result["orphan_count"] >= 1


def test_validate_multi_parent_cycle():
    """Multi-parent cycle a->(root,b), b->a is detected across all parent edges."""
    events = [
        ToolEvent(tool_name="Bash", tool_input={}, event_id="a", parent_event_id="root,b"),
        ToolEvent(tool_name="Read", tool_input={}, event_id="b", parent_event_id="a"),
    ]
    result = validate_session(events)
    assert result["valid"] is False
    assert len(result["cycles"]) >= 1


def test_session_id_path_traversal_blocked():
    from causetrace.core import _validate_session_id
    import pytest
    with pytest.raises(ValueError, match="Invalid session_id"):
        _validate_session_id("../escaped")
    with pytest.raises(ValueError, match="Invalid session_id"):
        _validate_session_id("a/b")
    # Valid IDs should pass
    _validate_session_id("normal_123")
    _validate_session_id("codex-2026-05-01")
    _validate_session_id("session.456")


def test_malformed_jsonl_validate_no_crash():
    """Validate command handler parsing malformed JSONL must not crash."""
    import tempfile, json
    from pathlib import Path
    d = tempfile.mkdtemp()
    f = Path(d) / "bad.jsonl"
    f.write_text('{"event_id":"a","tool_name":"Bash","tool_input":{}}\nnot json\n{"event_id":"b","tool_name":"Read","tool_input":{}}\n')
    raw = f.read_text().splitlines()
    events = []
    for line in raw:
        if line.strip():
            try:
                events.append(ToolEvent.from_dict(json.loads(line)))
            except (json.JSONDecodeError, KeyError):
                pass
    result = validate_session(events, raw_lines=raw)
    assert result["malformed_lines"] == 1
    assert result["valid"] is False


def test_avg_depth_correct():
    """3-node chain (root depth 0, child depth 1, grandchild depth 2) => avg_depth=1.0"""
    from causetrace.analysis import compute_stats
    events = [
        ToolEvent(tool_name="Read", tool_input={}, event_id="root"),
        ToolEvent(tool_name="Bash", tool_input={}, event_id="a", parent_event_id="root"),
        ToolEvent(tool_name="Edit", tool_input={}, event_id="b", parent_event_id="a"),
    ]
    stats = compute_stats(events)
    assert stats["avg_depth"] == 1.0
    assert stats["max_depth"] == 2


def test_longest_path_merge_dag():
    """DAG with merge node: longest path must traverse the longer branch through the merge."""
    from causetrace.analysis import longest_path
    events = [
        ToolEvent(tool_name="Read", tool_input={}, event_id="root_a"),
        ToolEvent(tool_name="Bash", tool_input={}, event_id="x", parent_event_id="root_a"),
        ToolEvent(tool_name="Edit", tool_input={}, event_id="y", parent_event_id="x"),
        ToolEvent(tool_name="Read", tool_input={}, event_id="z", parent_event_id="y"),
        ToolEvent(tool_name="Bash", tool_input={}, event_id="root_b"),
        ToolEvent(tool_name="Write", tool_input={}, event_id="w", parent_event_id="root_b"),
    ]
    events[2].parent_event_id = "root_a,w"  # merge: y's parents are both root_a and w
    path = longest_path(events)
    assert len(path) >= 4  # must traverse root_b -> w -> y -> z or root_a -> x -> y -> z


def test_causality_tool_name_case_insensitive():
    """_detect_fan_in should match tool names regardless of case."""
    from causetrace.causality import _detect_fan_in
    from causetrace.core import ToolEvent
    events = [
        ToolEvent(tool_name="Read", tool_input={"file": "a"}, event_id="r1", timestamp="2026-01-01T00:00:01"),
        ToolEvent(tool_name="Grep", tool_input={"pat": "x"}, event_id="r2", timestamp="2026-01-01T00:00:02"),
        ToolEvent(tool_name="Edit", tool_input={"line": "42"}, event_id="w1", timestamp="2026-01-01T00:00:03"),
    ]
    result = _detect_fan_in(events)
    assert len(result) >= 1, "fan-in should detect Edit with Read/Grep parents (capitalized)"


def test_opencode_tailer_preserves_timestamp():
    """OpenCode tailer must pass parsed ts to ToolEvent."""
    import tempfile
    from pathlib import Path
    import causetrace.hooks.opencode_tailer as tailer

    with tempfile.TemporaryDirectory() as tmp:
        log_dir = Path(tmp)
        (log_dir / "tool.log").write_text(
            "INFO  2026-05-01T02:03:04 service=tool.registry status=started read\n"
            "INFO  2026-05-01T02:03:05 service=tool.registry status=completed duration=9 read\n"
        )
        old_log_dir = tailer.LOG_DIR
        tailer.LOG_DIR = log_dir
        try:
            events = tailer.scan_logs(max_files=1)
        finally:
            tailer.LOG_DIR = old_log_dir
    assert events[0].timestamp == "2026-05-01T02:03:05"


def test_validate_cli_returns_failure_for_invalid_session():
    """The validate command must fail when it reports invalid trace data."""
    import subprocess

    with tempfile.TemporaryDirectory() as tmp:
        store_dir = Path(tmp) / ".causetrace" / "data"
        store_dir.mkdir(parents=True)
        (store_dir / "bad.jsonl").write_text("not json\n")
        env = {**os.environ, "HOME": tmp}
        result = subprocess.run(
            [sys.executable, "-m", "causetrace", "validate", "bad"],
            capture_output=True,
            text=True,
            env=env,
        )
    assert result.returncode != 0
    assert "Valid: False" in result.stdout


def test_validate_cli_rejects_non_event_json_without_crashing():
    import subprocess

    with tempfile.TemporaryDirectory() as tmp:
        store_dir = Path(tmp) / ".causetrace" / "data"
        store_dir.mkdir(parents=True)
        (store_dir / "bad.jsonl").write_text("[]\n")
        env = {**os.environ, "HOME": tmp}
        result = subprocess.run(
            [sys.executable, "-m", "causetrace", "validate", "bad"],
            capture_output=True,
            text=True,
            env=env,
        )
    assert result.returncode != 0
    assert "invalid event data" in result.stdout


def test_patterns_cli_csv_selects_csv_without_transitions_only():
    import subprocess

    events = [
        ToolEvent(tool_name="Read", tool_input={}, event_id="r"),
        ToolEvent(tool_name="Edit", tool_input={}, event_id="e", parent_event_id="r"),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        store_dir = Path(tmp) / ".causetrace" / "data"
        store_dir.mkdir(parents=True)
        (store_dir / "csv.jsonl").write_text(
            "\n".join(json.dumps(event.to_dict()) for event in events) + "\n"
        )
        result = subprocess.run(
            [sys.executable, "-m", "causetrace", "patterns", "csv", "--csv"],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": tmp},
        )
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["from,to,count", "Read,Edit,1"]


# ── Tree compression (graph compression — Iter 3) ──

def test_compress_tree_short_run_not_compressed():
    """Consecutive same-tool runs shorter than min_run stay as-is."""
    evs = [
        ToolEvent("Read", {}, event_id="r0"),
        ToolEvent("Bash", {}, event_id="b1", parent_event_id="r0"),
        ToolEvent("Bash", {}, event_id="b2", parent_event_id="b1"),
    ]
    tree = build_tree(evs)
    compressed = compress_tree(tree, min_run=3)
    top = compressed[0]
    assert top["event"].tool_name == "Read"
    middle = top["children"][0]
    assert middle["event"].tool_name == "Bash"
    assert not isinstance(middle["event"], CompressedRun)


def test_compress_tree_long_chain():
    """Consecutive same-tool run >= min_run collapses to CompressedRun."""
    evs = [
        ToolEvent("Bash", {}, event_id="b0"),
        ToolEvent("Bash", {}, event_id="b1", parent_event_id="b0"),
        ToolEvent("Bash", {}, event_id="b2", parent_event_id="b1"),
        ToolEvent("Bash", {}, event_id="b3", parent_event_id="b2"),
    ]
    tree = build_tree(evs)
    compressed = compress_tree(tree, min_run=3)
    run = compressed[0]
    assert isinstance(run["event"], CompressedRun)
    assert run["event"].tool_name == "Bash"
    assert run["event"].count == 4
    assert len(run["event"].events) == 4


def test_compress_tree_fan_out_preserved():
    """Fan-out nodes stop compression even if tool matches."""
    evs = [
        ToolEvent("Bash", {}, event_id="b0"),
        ToolEvent("Bash", {}, event_id="b1", parent_event_id="b0"),
        ToolEvent("Edit", {}, event_id="e1", parent_event_id="b0"),
    ]
    tree = build_tree(evs)
    compressed = compress_tree(tree, min_run=2)
    root = compressed[0]
    assert root["event"].tool_name == "Bash"
    assert len(root["children"]) == 2
    for c in root["children"]:
        assert not isinstance(c["event"], CompressedRun)


def test_compress_tree_mixed_tool_chain():
    """Different tool names break compression."""
    evs = [
        ToolEvent("Read", {}, event_id="r0"),
        ToolEvent("Bash", {}, event_id="b1", parent_event_id="r0"),
        ToolEvent("Bash", {}, event_id="b2", parent_event_id="b1"),
        ToolEvent("Edit", {}, event_id="e3", parent_event_id="b2"),
    ]
    tree = build_tree(evs)
    compressed = compress_tree(tree, min_run=2)
    read_node = compressed[0]
    bash_run = read_node["children"][0]
    assert isinstance(bash_run["event"], CompressedRun)
    assert bash_run["event"].count == 2
    assert bash_run["event"].tool_name == "Bash"
    edit_child = bash_run["children"][0]
    assert edit_child["event"].tool_name == "Edit"


def test_compress_tree_empty():
    """Empty tree returns empty list."""
    assert compress_tree([], min_run=3) == []


def test_render_tree_compress_shows_count():
    """render_tree with compress>0 shows [xN] markers."""
    evs = [
        ToolEvent("Bash", {}, event_id="b0"),
        ToolEvent("Bash", {}, event_id="b1", parent_event_id="b0"),
        ToolEvent("Bash", {}, event_id="b2", parent_event_id="b1"),
    ]
    output = TimelineRenderer.render_tree(evs, compress=3)
    assert "[x3]" in output


def test_print_tree_compress_no_crash():
    """print_tree with compress flag does not crash."""
    evs = [
        ToolEvent("Read", {}, event_id="r0"),
        ToolEvent("Bash", {}, event_id="b1", parent_event_id="r0"),
        ToolEvent("Bash", {}, event_id="b2", parent_event_id="b1"),
        ToolEvent("Edit", {}, event_id="e3", parent_event_id="b2"),
    ]
    import io, sys
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        TimelineRenderer.print_tree(evs, compress=3)
    finally:
        sys.stdout = old
    output = buf.getvalue()
    assert "Read" in output
