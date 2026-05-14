"""Integration tests for the Claude Code hook bridge (stdin/stdout flow).

These test the actual hook entry point by simulating PreToolUse/PostToolUse
JSON messages via subprocess, then verifying the stored trace has correct
causal chains.

Run:  python3 -m pytest tests/test_hooks_integration.py -v
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from causetrace.core import JSONStore, ToolEvent, build_tree

HOOK_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "causetrace"
    / "hooks"
    / "claude_code.py"
)


def _hook_run(input_json: dict, home_dir: str) -> dict:
    """Run the hook script as a subprocess with isolated home directory."""
    env = {**os.environ, "HOME": home_dir}
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(input_json),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert result.returncode == 0, f"hook returned {result.returncode}: {result.stderr}"
    if result.stdout.strip():
        return json.loads(result.stdout)
    return {}


def _make_hook_input(
    event_name: str,
    tool_name: str = "Bash",
    tool_input: dict | None = None,
    tool_result: dict | None = None,
    session_id: str = "test_integration",
) -> dict:
    d: dict = {
        "hook_event_name": event_name,
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": tool_input or {"command": "echo hello"},
    }
    if tool_result is not None:
        d["tool_result"] = tool_result
    return d


def test_hook_records_both_pre_and_post():
    """PreToolUse + PostToolUse should produce exactly one stored event."""
    with tempfile.TemporaryDirectory() as tmp:
        store = JSONStore(store_dir=os.path.join(tmp, ".causetrace", "data"))
        sid = "test_simple"
        _hook_run(_make_hook_input("PreToolUse", session_id=sid), home_dir=tmp)
        _hook_run(_make_hook_input("PostToolUse", session_id=sid), home_dir=tmp)

        events = store.load(sid)
        assert len(events) == 1
        assert events[0].tool_name == "Bash"


def test_hook_causal_chain_two_calls():
    """Two consecutive tool calls should form a parent→child chain."""
    with tempfile.TemporaryDirectory() as tmp:
        store = JSONStore(store_dir=os.path.join(tmp, ".causetrace", "data"))
        sid = "test_chain"

        _hook_run(
            _make_hook_input("PreToolUse", "Grep", {"pattern": "TODO"}, session_id=sid),
            home_dir=tmp,
        )
        _hook_run(
            _make_hook_input("PostToolUse", "Grep", session_id=sid,
                             tool_result={"output": "line1"}),
            home_dir=tmp,
        )

        _hook_run(
            _make_hook_input("PreToolUse", "Read", {"file_path": "src/main.py"}, session_id=sid),
            home_dir=tmp,
        )
        _hook_run(
            _make_hook_input("PostToolUse", "Read", session_id=sid,
                             tool_result={"output": "content"}),
            home_dir=tmp,
        )

        events = store.load(sid)
        assert len(events) == 2
        _assert_ordered_chain(events, ["Grep", "Read"])


def test_hook_causal_chain_three_calls():
    """Three chained calls: ev0 → ev1 → ev2."""
    with tempfile.TemporaryDirectory() as tmp:
        store = JSONStore(store_dir=os.path.join(tmp, ".causetrace", "data"))
        sid = "test_chain_3"

        for tool_name, tool_input in [
            ("Bash", {"command": "ls"}),
            ("Read", {"file_path": "a.py"}),
            ("Edit", {"file_path": "a.py", "old_string": "x", "new_string": "y"}),
        ]:
            _hook_run(
                _make_hook_input("PreToolUse", tool_name, tool_input, session_id=sid),
                home_dir=tmp,
            )
            _hook_run(
                _make_hook_input("PostToolUse", tool_name, session_id=sid),
                home_dir=tmp,
            )

        events = store.load(sid)
        assert len(events) == 3

        # Find root (the event with no parent)
        roots = [e for e in events if e.parent_event_id is None]
        assert len(roots) == 1, f"expected 1 root, got {len(roots)}"
        assert roots[0].tool_name == "Bash"

        # Build chain by following parent refs
        by_id = {e.event_id: e for e in events}
        chain = []
        cur = roots[0]
        while cur:
            chain.append(cur)
            children = [e for e in events if e.parent_event_id == cur.event_id]
            cur = children[0] if children else None
        assert len(chain) == 3
        assert [e.tool_name for e in chain] == ["Bash", "Read", "Edit"]


def test_hook_builds_tree():
    """Hook-produced events should form a valid causal tree."""
    with tempfile.TemporaryDirectory() as tmp:
        store = JSONStore(store_dir=os.path.join(tmp, ".causetrace", "data"))
        sid = "test_tree"

        for tool_name, inp in [
            ("Read", {"file_path": "main.py"}),
            ("Grep", {"pattern": "FIXME"}),
            ("Edit", {"file_path": "main.py"}),
            ("Bash", {"command": "pytest"}),
        ]:
            _hook_run(
                _make_hook_input("PreToolUse", tool_name, inp, session_id=sid),
                home_dir=tmp,
            )
            _hook_run(
                _make_hook_input("PostToolUse", tool_name, session_id=sid),
                home_dir=tmp,
            )

        events = store.load(sid)
        trees = build_tree(events)
        assert len(trees) == 1, "one chain = one root"
        assert trees[0]["event"].tool_name == "Read"
        assert len(trees[0]["children"]) == 1


def test_hook_post_without_pre_graceful():
    """PostToolUse without a preceding PreToolUse should not crash."""
    with tempfile.TemporaryDirectory() as tmp:
        store = JSONStore(store_dir=os.path.join(tmp, ".causetrace", "data"))
        sid = "test_orphan_post"

        result = _hook_run(
            _make_hook_input("PostToolUse", session_id=sid),
            home_dir=tmp,
        )
        assert result is not None
        events = store.load(sid)
        assert len(events) == 0


def test_hook_missing_post_leaves_no_event():
    """PreToolUse without matching PostToolUse should leave no stored event."""
    with tempfile.TemporaryDirectory() as tmp:
        store = JSONStore(store_dir=os.path.join(tmp, ".causetrace", "data"))
        sid = "test_missing_post"

        _hook_run(
            _make_hook_input("PreToolUse", session_id=sid),
            home_dir=tmp,
        )
        events = store.load(sid)
        assert len(events) == 0


def test_hook_model_provider_propagated():
    """Model and provider env vars should propagate to the recorded event."""
    with tempfile.TemporaryDirectory() as tmp:
        store = JSONStore(store_dir=os.path.join(tmp, ".causetrace", "data"))
        sid = "test_attrs"

        env = {**os.environ, "ANTHROPIC_MODEL": "claude-4-sonnet", "HOME": tmp}
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=json.dumps(_make_hook_input("PreToolUse", session_id=sid)),
            capture_output=True, text=True, timeout=10, env=env,
        )
        assert result.returncode == 0
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=json.dumps(_make_hook_input("PostToolUse", session_id=sid)),
            capture_output=True, text=True, timeout=10, env=env,
        )
        assert result.returncode == 0

        events = store.load(sid)
        assert len(events) == 1
        assert events[0].model == "claude-4-sonnet"
        assert events[0].provider == "anthropic"


def _assert_ordered_chain(events, expected_tools: list[str]):
    """Verify events form a single chain in the given tool order.

    Uses parent refs (not index ordering) so it's robust to timestamp ties.
    """
    by_id = {e.event_id: e for e in events}
    # Find root
    roots = [e for e in events if e.parent_event_id is None]
    assert len(roots) == 1, f"expected 1 root, got {len(roots)}"
    assert roots[0].tool_name == expected_tools[0]

    # Walk chain
    chain_tools = []
    cur = roots[0]
    while cur and len(chain_tools) < len(events):
        chain_tools.append(cur.tool_name)
        children = [e for e in events if e.parent_event_id == cur.event_id]
        cur = children[0] if children else None
    assert chain_tools == expected_tools, f"expected {expected_tools}, got {chain_tools}"


def test_hook_different_tools_chain():
    """Mixed tool types should still form proper causal chains."""
    with tempfile.TemporaryDirectory() as tmp:
        store = JSONStore(store_dir=os.path.join(tmp, ".causetrace", "data"))
        sid = "test_mixed"

        for tool_name, inp in [
            ("WebSearch", {"query": "python api"}),
            ("Read", {"file_path": "example.py"}),
            ("Bash", {"command": "python example.py"}),
            ("Write", {"file_path": "output.txt", "content": "result"}),
        ]:
            _hook_run(
                _make_hook_input("PreToolUse", tool_name, inp, session_id=sid),
                home_dir=tmp,
            )
            _hook_run(
                _make_hook_input("PostToolUse", tool_name, session_id=sid),
                home_dir=tmp,
            )

        events = store.load(sid)
        _assert_ordered_chain(events, ["WebSearch", "Read", "Bash", "Write"])


def test_hook_chain_validate_via_tree():
    """Hook chain should produce a valid single-root tree."""
    with tempfile.TemporaryDirectory() as tmp:
        store = JSONStore(store_dir=os.path.join(tmp, ".causetrace", "data"))
        sid = "test_valid_tree"

        _hook_run(
            _make_hook_input("PreToolUse", "Read", {"file_path": "x.py"}, session_id=sid),
            home_dir=tmp,
        )
        _hook_run(
            _make_hook_input("PostToolUse", "Read", session_id=sid),
            home_dir=tmp,
        )
        _hook_run(
            _make_hook_input("PreToolUse", "Edit", {"file_path": "x.py"}, session_id=sid),
            home_dir=tmp,
        )
        _hook_run(
            _make_hook_input("PostToolUse", "Edit", session_id=sid),
            home_dir=tmp,
        )

        events = store.load(sid)
        assert len(events) == 2
        _assert_ordered_chain(events, ["Read", "Edit"])
