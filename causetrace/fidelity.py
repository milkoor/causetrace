"""Causal fidelity: native runtime links vs temporal-heuristic inference.

Some runtimes (DSH session logs, Claude Code hooks) persist *ground-truth*
causal structure. All log-based ingestion instead falls back to
``causality.infer_relations()``. This module turns the ROADMAP question
"how often do native parent links differ from timestamp-based inference?"
into a repeatable measurement over any session that has native links:

1. keep the session's native parent sets as ground truth,
2. clone the events, strip all parents,
3. re-infer with the temporal heuristics,
4. compare edge sets.

Output metrics (per session):
    - ``child_exact_agreement``: fraction of child events whose *whole*
      inferred parent set equals the native one
    - ``missed_edge_rate`` / ``spurious_edge_rate``: share of native edges
      not recovered / inferred edges absent from native
    - ``fan_in_reproduced``: of the natively multi-parent children, how many
      the heuristics rebuild exactly — the structural capability log-based
      inference claims to provide

Usage:
    from causetrace.fidelity import measure_fidelity
    report = measure_fidelity(events)

Caveat: on sessions ingested by the legacy tailers, the stored parents were
*produced by* ``infer_relations`` at import time — measuring them reproduces
the algorithm's agreement with itself (~100%) and proves nothing. For
parser-chained enrich sessions the number is still informative (each
parser's own chaining vs the shared heuristics), but only runtime-native
links (DSH) constitute ground truth.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .core import ToolEvent, _parse_parents
from .causality import infer_relations

__all__ = ["measure_fidelity", "has_native_ground_truth"]


def has_native_ground_truth(events: List[ToolEvent]) -> bool:
    """True when the session carries persisted causal edges to measure against."""
    return any(e.parent_event_id for e in events)


def _parent_sets(events: List[ToolEvent]) -> Dict[str, frozenset]:
    return {
        e.event_id: frozenset(_parse_parents(e))
        for e in events
        if e.parent_event_id
    }


def measure_fidelity(
    events: List[ToolEvent],
    local_only: bool = True,
) -> Optional[Dict[str, Any]]:
    """Measure temporal inference against native ground-truth links.

    Args:
        events: session events whose ``parent_event_id`` values come from the
            runtime itself (not from ``infer_relations``).
        local_only: restrict comparison to parents present in the session
            (matches session-local analysis boundaries).

    Returns:
        Metrics dict, or None when the session has no native parent links
        (nothing to compare against).
    """
    if not has_native_ground_truth(events):
        return None

    by_id = {e.event_id for e in events}
    native = _parent_sets(events)
    if local_only:
        native = {c: frozenset(p for p in ps if p in by_id) for c, ps in native.items()}
        native = {c: ps for c, ps in native.items() if ps}

    # Clone through serialization so inference cannot observe ground truth.
    clones = [ToolEvent.from_dict(e.to_dict()) for e in events]
    for c in clones:
        c.parent_event_id = None
    infer_relations(clones)

    inferred = _parent_sets(clones)
    if local_only:
        inferred = {c: frozenset(p for p in ps if p in by_id) for c, ps in inferred.items()}
        inferred = {c: ps for c, ps in inferred.items() if ps}

    children = set(native) | set(inferred)
    exact = sum(1 for c in children if native.get(c, frozenset()) == inferred.get(c, frozenset()))

    native_edges = sum(len(ps) for ps in native.values())
    inferred_edges = sum(len(ps) for ps in inferred.values())
    inter = sum(len(native.get(c, frozenset()) & inferred.get(c, frozenset())) for c in children)
    missed = native_edges - inter
    spurious = inferred_edges - inter

    fan_native = {c for c, ps in native.items() if len(ps) > 1}
    fan_inferred = {c for c, ps in inferred.items() if len(ps) > 1}
    fan_exact = {c for c in fan_native if inferred.get(c) == native.get(c)}

    recall = inter / native_edges if native_edges else 0.0
    precision = inter / inferred_edges if inferred_edges else 0.0

    return {
        "event_count": len(events),
        "children_compared": len(children),
        "child_exact_agreement": exact / len(children) if children else 0.0,
        "native_edges": native_edges,
        "inferred_edges": inferred_edges,
        "matched_edges": inter,
        "missed_edge_rate": missed / native_edges if native_edges else 0.0,
        "spurious_edge_rate": spurious / inferred_edges if inferred_edges else 0.0,
        "edge_recall": recall,
        "edge_precision": precision,
        "edge_f1": (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0,
        "fan_in_native": len(fan_native),
        "fan_in_claimed": len(fan_inferred),
        "fan_in_reproduced": len(fan_exact),
    }
