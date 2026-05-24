"""Topology invariants — composable DAG correctness checkers.

Each function is a pure checker: takes events, returns a list of
violation strings (empty list means the invariant holds).

Use ``check_invariants()`` to run the full battery.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple


def _parse_parents(parent_event_id: Optional[str]) -> List[str]:
    if not parent_event_id:
        return []
    return [p.strip() for p in parent_event_id.split(",") if p.strip()]


def _build_indexes(events) -> Tuple[Dict[str, Set[str]], Dict[str, List[str]], Set[str]]:
    """Return (children_map, parents_map, event_ids)."""
    event_ids: Set[str] = {ev.event_id for ev in events}
    children: Dict[str, Set[str]] = defaultdict(set)
    parents: Dict[str, List[str]] = {}
    for ev in events:
        eid = ev.event_id
        local = [pid for pid in _parse_parents(ev.parent_event_id) if pid in event_ids]
        parents[eid] = local
        for pid in local:
            children[pid].add(eid)
    return dict(children), parents, event_ids


def check_unique_ids(events) -> List[str]:
    """Every event_id in the session must be unique."""
    seen: Dict[str, int] = {}
    issues: List[str] = []
    for ev in events:
        eid = ev.event_id
        if eid in seen:
            issues.append(f"Duplicate event_id '{eid}' at position {seen[eid]}")
        else:
            seen[eid] = len(seen)
    return issues


def check_acyclicity(events) -> List[str]:
    """No cycles in parent-event_id chains (local refs only)."""
    _, parents, eids = _build_indexes(events)
    issues: List[str] = []
    visited_global: Set[str] = set()

    for start in eids:
        if start in visited_global:
            continue
        stack = [(start, [start])]
        while stack:
            node_id, path = stack.pop()
            if node_id in visited_global and len(path) == 1:
                continue
            node_parents = parents.get(node_id, [])
            for pid in node_parents:
                if pid in path:
                    cycle_chain = " -> ".join(path[path.index(pid):] + [pid])
                    issues.append(f"Cycle detected: {cycle_chain}")
                else:
                    stack.append((pid, path + [pid]))
            visited_global.add(node_id)
    return issues


def check_local_references(events) -> List[str]:
    """Every parent_event_id must resolve to a known event in the session,
    unless it begins with 'root_' (external reference convention)."""
    _, _, eids = _build_indexes(events)
    issues: List[str] = []
    for ev in events:
        for pid in _parse_parents(ev.parent_event_id):
            if pid not in eids and not pid.startswith("root_"):
                issues.append(
                    f"{ev.event_id}: parent_event_id '{pid}' not found in session"
                )
    return issues


def check_root_definition(events) -> List[str]:
    """Roots are events with indegree 0 (no local parent)."""
    children, parents, eids = _build_indexes(events)
    indegree: Dict[str, int] = {e: 0 for e in eids}
    for pid, kids in children.items():
        for kid in kids:
            indegree[kid] += 1

    issues: List[str] = []
    for ev in events:
        eid = ev.event_id
        has_local_parent = len(parents.get(eid, [])) > 0
        calculated_root = indegree[eid] == 0

        if has_local_parent and calculated_root:
            issues.append(
                f"{eid}: has parent(s) but indegree=0 (indexing bug)"
            )
        if not has_local_parent and not calculated_root:
            issues.append(
                f"{eid}: no parent_event_id but indegree={indegree[eid]} (inconsistent)"
            )
    return issues


# ── Battery runner ──

INVARIANTS: List[tuple[str, str]] = [
    ("unique_ids", "No duplicate event IDs"),
    ("acyclicity", "No cycles in parent chains"),
    ("local_references", "All parent refs resolve to known events"),
    ("root_definition", "Roots defined as indegree-0 nodes"),
]


def check_invariants(events) -> dict:
    """Run all invariant checkers and return a summary dict.

    Returns::

        {
            "valid": bool,
            "checks": {name: {"description": str, "violations": [str, ...]}},
        }
    """
    checkers = {
        "unique_ids": check_unique_ids,
        "acyclicity": check_acyclicity,
        "local_references": check_local_references,
        "root_definition": check_root_definition,
    }
    results: dict = {}
    all_ok = True
    for name in INVARIANTS:
        violations = checkers[name[0]](events)
        results[name[0]] = {"description": name[1], "violations": violations}
        if violations:
            all_ok = False

    return {"valid": all_ok, "checks": results}