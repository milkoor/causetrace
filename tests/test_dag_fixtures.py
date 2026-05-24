"""Topology invariant tests against DAG fixtures.

Each fixture is a JSONL file in tests/fixtures/dags/ with known topological
properties.  These tests assert those properties hold — they guard against
regression in analysis.py primitives (compute_stats, find_roots, longest_path,
connected_components) and validate_session.

Run:  python3 -m pytest tests/test_dag_fixtures.py -v
"""
import json
from pathlib import Path

import pytest

from causetrace.core import ToolEvent, validate_session
from causetrace.invariants import check_invariants
from causetrace.analysis import (
    compute_stats, find_roots, longest_path, connected_components,
    detect_common_transitions, detect_fan_in_patterns, detect_repeated_paths,
    windowed,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "dags"


def load_fixture(name: str) -> list[ToolEvent]:
    """Load a DAG fixture JSONL file and return parsed ToolEvents."""
    path = FIXTURE_DIR / f"{name}.jsonl"
    if not path.exists():
        pytest.fail(f"Fixture not found: {path}")
    events = []
    for line in path.read_text().splitlines():
        if line.strip():
            events.append(ToolEvent.from_dict(json.loads(line)))
    return events


# ── Fixture loading ──

def test_fixtures_exist():
    """All expected fixture files load without error."""
    for name in ("chain", "fan-in", "deep-merge", "diamond", "cycle",
                 "multi-parent-cycle", "forest", "deep-chain", "fork",
                 "timed-fan-in"):
        evs = load_fixture(name)
        assert len(evs) >= 2, f"{name}: too few events"


# ── Simple chain (root → a → b → c) ──

def test_chain_basic_counts():
    evs = load_fixture("chain")
    s = compute_stats(evs)
    assert s["event_count"] == 4
    assert s["root_count"] == 1
    assert s["leaf_count"] == 1

def test_chain_depths():
    evs = load_fixture("chain")
    s = compute_stats(evs)
    assert s["max_depth"] == 3
    assert s["avg_depth"] == 1.5

def test_chain_longest_path():
    evs = load_fixture("chain")
    path = longest_path(evs)
    assert len(path) == 4, f"Expected 4, got {len(path)}: {path}"

def test_chain_acyclic():
    evs = load_fixture("chain")
    r = validate_session(evs)
    assert r["valid"] is True
    assert len(r["cycles"]) == 0

def test_chain_single_component():
    evs = load_fixture("chain")
    comps = connected_components(evs)
    assert len(comps) == 1
    assert comps[0]["size"] == 4


# ── Fan-in: two roots → one child ──

def test_fan_in_roots_and_leaves():
    evs = load_fixture("fan-in")
    s = compute_stats(evs)
    assert s["root_count"] == 2
    assert s["leaf_count"] == 1

def test_fan_in_depths():
    evs = load_fixture("fan-in")
    s = compute_stats(evs)
    assert s["max_depth"] == 1
    assert s["avg_depth"] == pytest.approx(0.33, abs=0.01)

def test_fan_in_longest_path():
    evs = load_fixture("fan-in")
    path = longest_path(evs)
    assert len(path) == 2

def test_fan_in_valid():
    evs = load_fixture("fan-in")
    r = validate_session(evs)
    assert r["valid"] is True
    assert len(r["cycles"]) == 0

def test_fan_in_multi_parent():
    """fan-in fixture uses comma-separated parent_event_id."""
    evs = load_fixture("fan-in")
    multi = sum(1 for e in evs if e.parent_event_id and "," in e.parent_event_id)
    assert multi >= 1

def test_fan_in_roots_identified():
    evs = load_fixture("fan-in")
    roots = find_roots(evs)
    assert len(roots) == 2


# ── Deep merge: root → a → c, root → b → c ──

def test_deep_merge_counts():
    evs = load_fixture("deep-merge")
    s = compute_stats(evs)
    assert s["event_count"] == 4
    assert s["root_count"] == 1
    assert s["leaf_count"] == 1

def test_deep_merge_depths():
    evs = load_fixture("deep-merge")
    s = compute_stats(evs)
    assert s["max_depth"] == 2
    assert s["avg_depth"] == 1.0

def test_deep_merge_longest_path():
    evs = load_fixture("deep-merge")
    path = longest_path(evs)
    assert len(path) == 3  # root → a (or b) → c


# ── Diamond: root → a → c → target, root → b → d → target ──

def test_diamond_counts():
    evs = load_fixture("diamond")
    s = compute_stats(evs)
    assert s["event_count"] == 6
    assert s["root_count"] == 1
    assert s["leaf_count"] == 1

def test_diamond_depths():
    evs = load_fixture("diamond")
    s = compute_stats(evs)
    assert s["max_depth"] == 3
    assert s["avg_depth"] == 1.5

def test_diamond_longest_path():
    evs = load_fixture("diamond")
    path = longest_path(evs)
    assert len(path) == 4  # root → a → c → target or root → b → d → target

def test_diamond_valid():
    evs = load_fixture("diamond")
    r = validate_session(evs)
    assert r["valid"] is True
    assert len(r["cycles"]) == 0


# ── Cycle: a → b → c → a ──

def test_cycle_detected():
    evs = load_fixture("cycle")
    r = validate_session(evs)
    assert r["valid"] is False
    assert len(r["cycles"]) >= 1

def test_cycle_no_roots():
    evs = load_fixture("cycle")
    # All nodes have parents, so no roots; all have children, so no leaves
    roots = find_roots(evs)
    assert len(roots) == 0


# ── Multi-parent cycle: a.parent="root,b", b.parent="a" ──

def test_multi_parent_cycle_detected():
    evs = load_fixture("multi-parent-cycle")
    r = validate_session(evs)
    assert r["valid"] is False
    assert len(r["cycles"]) >= 1

def test_multi_parent_cycle_stats():
    evs = load_fixture("multi-parent-cycle")
    s = compute_stats(evs)
    assert s["event_count"] == 3
    assert s["root_count"] == 1   # root is the only root


# ── Forest: a → b, c → d → e ──

def test_forest_counts():
    evs = load_fixture("forest")
    s = compute_stats(evs)
    assert s["event_count"] == 5
    assert s["root_count"] == 2
    assert s["leaf_count"] == 2

def test_forest_depths():
    evs = load_fixture("forest")
    s = compute_stats(evs)
    assert s["max_depth"] == 2  # c → d → e
    assert s["avg_depth"] == 0.8

def test_forest_two_components():
    evs = load_fixture("forest")
    comps = connected_components(evs)
    assert len(comps) == 2
    assert {c["size"] for c in comps} == {2, 3}

def test_forest_longest_path():
    evs = load_fixture("forest")
    path = longest_path(evs)
    assert len(path) == 3  # c → d → e


# ── Deep chain: 10 nodes ──

def test_deep_chain_counts():
    evs = load_fixture("deep-chain")
    s = compute_stats(evs)
    assert s["event_count"] == 10
    assert s["root_count"] == 1
    assert s["leaf_count"] == 1

def test_deep_chain_depths():
    evs = load_fixture("deep-chain")
    s = compute_stats(evs)
    assert s["max_depth"] == 9
    assert s["avg_depth"] == 4.5

def test_deep_chain_longest_path():
    evs = load_fixture("deep-chain")
    path = longest_path(evs)
    assert len(path) == 10

def test_deep_chain_acyclic():
    evs = load_fixture("deep-chain")
    r = validate_session(evs)
    assert r["valid"] is True


# ── Fork: root → a, root → b ──

def test_fork_counts():
    evs = load_fixture("fork")
    s = compute_stats(evs)
    assert s["event_count"] == 3
    assert s["root_count"] == 1
    assert s["leaf_count"] == 2

def test_fork_depths():
    evs = load_fixture("fork")
    s = compute_stats(evs)
    assert s["max_depth"] == 1
    assert s["avg_depth"] == pytest.approx(0.67, abs=0.01)

def test_fork_longest_path():
    evs = load_fixture("fork")
    path = longest_path(evs)
    assert len(path) == 2  # root → a or root → b

def test_fork_roots_correct():
    evs = load_fixture("fork")
    roots = find_roots(evs)
    assert len(roots) == 1
    assert roots[0]["downstream_count"] == 2


# ── Timed fan-in: r1→w1←r2, w1→e1 ──

def test_timed_fan_in_counts():
    evs = load_fixture("timed-fan-in")
    s = compute_stats(evs)
    assert s["event_count"] == 4
    assert s["root_count"] == 2
    assert s["leaf_count"] == 1

def test_timed_fan_in_depths():
    evs = load_fixture("timed-fan-in")
    s = compute_stats(evs)
    assert s["max_depth"] == 2

def test_timed_fan_in_longest_path():
    evs = load_fixture("timed-fan-in")
    path = longest_path(evs)
    assert len(path) == 3  # r1→w1→e1 or r2→w1→e1


def _uneven_merge() -> list[ToolEvent]:
    return [
        ToolEvent("Root", {}, event_id="r"),
        ToolEvent("A", {}, event_id="a", parent_event_id="r"),
        ToolEvent("B", {}, event_id="b", parent_event_id="r"),
        ToolEvent("L1", {}, event_id="l1", parent_event_id="a"),
        ToolEvent("L2", {}, event_id="l2", parent_event_id="l1"),
        ToolEvent("Merge", {}, event_id="m", parent_event_id="b,l2"),
        ToolEvent("After", {}, event_id="z", parent_event_id="m"),
    ]


def test_uneven_merge_propagates_long_branch_depth():
    stats = compute_stats(_uneven_merge())
    assert stats["max_depth"] == 5
    assert stats["avg_depth"] == pytest.approx(2.29, abs=0.01)
    assert stats["chain_length_avg"] == 6.0


def test_uneven_merge_root_metrics_count_unique_descendants():
    roots = find_roots(_uneven_merge())
    assert roots[0]["downstream_count"] == 6
    assert roots[0]["max_subtree_depth"] == 5


def test_multi_parent_cycle_critical_path_is_bounded():
    path = longest_path(load_fixture("multi-parent-cycle"))
    assert len(path) <= 3


def test_patterns_follow_causal_edges_not_event_order():
    events = [
        ToolEvent("Read", {}, event_id="r1"),
        ToolEvent("Write", {}, event_id="r2"),
        ToolEvent("Read", {}, event_id="r3"),
        ToolEvent("Write", {}, event_id="r4"),
    ]
    assert detect_common_transitions(events) == []
    assert detect_repeated_paths(events) == []


def test_time_windows_retain_overlapping_events():
    events = [
        ToolEvent(str(second), {}, timestamp=f"2026-05-24T00:00:{second:02d}+00:00")
        for second in (0, 5, 8, 11)
    ]
    windows = [[event.tool_name for event in items]
               for items in windowed(events, strategy="time", size=10, overlap=5)]
    assert windows[:2] == [["0", "5", "8"], ["5", "8", "11"]]


def test_external_parent_reference_becomes_local_root():
    events = [
        ToolEvent("Read", {}, event_id="a", parent_event_id="outside"),
        ToolEvent("Edit", {}, event_id="b", parent_event_id="a"),
    ]
    stats = compute_stats(events)
    assert stats["root_count"] == 1
    assert stats["max_depth"] == 1
    assert find_roots(events)[0]["event_id"] == "a"
    assert longest_path(events) == ["a", "b"]
    assert connected_components(events) == [{
        "size": 2,
        "root_count": 1,
        "event_ids": ["a", "b"],
    }]


def test_fan_in_parent_tools_are_tool_names():
    events = [
        ToolEvent("Read", {}, event_id="r1"),
        ToolEvent("Grep", {}, event_id="r2"),
        ToolEvent("Edit", {}, event_id="m", parent_event_id="r1,r2"),
    ]
    patterns = detect_fan_in_patterns(events)
    assert patterns[0]["parent_tools"] == ["Read", "Grep"]


# ── Invariant battery (parametrized over fixtures) ──

INVARIANT_FIXTURES = [
    ("chain",          True),   # acyclic valid
    ("fan-in",         True),
    ("deep-merge",     True),
    ("diamond",        True),
    ("forest",         True),
    ("deep-chain",     True),
    ("fork",           True),
    ("timed-fan-in",   True),
    ("cycle",          False),  # cycle corruption
    ("multi-parent-cycle", False),
]


@pytest.mark.parametrize("name,expect_valid", INVARIANT_FIXTURES)
def test_invariant_battery(name, expect_valid):
    """All fixtures pass through the full invariant checker battery."""
    events = load_fixture(name)
    result = check_invariants(events)

    # If fixture has no unique-id violation, assert it
    if result["checks"]["unique_ids"]["violations"]:
        pytest.fail(f"{name}: duplicate event_ids")

    # Cycle check
    if expect_valid:
        if not result["valid"]:
            details = "; ".join(
                f"{k}: {v['violations'][:3]}"
                for k, v in result["checks"].items()
                if v["violations"]
            )
            pytest.fail(f"{name}: expected valid, got violations: {details}")
    else:
        # Known-corrupt fixtures — must have cycle violations
        cycle_vios = result["checks"]["acyclicity"]["violations"]
        assert len(cycle_vios) >= 1, \
            f"{name}: expected cycle detection, got none"
    events = [
        ToolEvent("Read", {}, event_id="r1"),
        ToolEvent("Grep", {}, event_id="r2"),
        ToolEvent("Edit", {}, event_id="m", parent_event_id="r1,r2"),
    ]
    patterns = detect_fan_in_patterns(events)
    assert patterns[0]["parent_tools"] == ["Read", "Grep"]
