"""Session analysis primitives: structural metrics and pattern detection.

Layer 1 — Structural (pure graph/path/topology metrics):
    compute_stats, find_roots, longest_path, fan_out_distribution,
    connected_components

Layer 2 — Pattern (repeated structures, no semantic interpretation):
    detect_repeated_paths, detect_common_transitions,
    detect_fan_in_patterns, detect_branch_collapse

Layer 1.5 — Temporal (time-local analysis support):
    windowed

No Layer 3 (semantic interpretation) here. Let patterns emerge from traces.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, Iterator, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_parents(parent_event_id: Optional[str]) -> List[str]:
    """Split comma-separated parent_event_id into individual IDs."""
    if not parent_event_id:
        return []
    return [p.strip() for p in parent_event_id.split(",") if p.strip()]


def _build_graph_indexes(events) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Build indexes using only parent-child edges present in this session."""
    event_ids = {ev.event_id for ev in events}
    children: Dict[str, List[str]] = defaultdict(list)
    parents: Dict[str, List[str]] = {}
    for ev in events:
        local_parents = [
            pid for pid in _parse_parents(ev.parent_event_id) if pid in event_ids
        ]
        parents[ev.event_id] = local_parents
        for pid in local_parents:
            children[pid].append(ev.event_id)
    return dict(children), parents


def _build_child_index(events) -> Dict[str, List[str]]:
    """Build parent_id -> [child_id, ...] index for local causal edges."""
    return _build_graph_indexes(events)[0]


def _build_parent_map(events) -> Dict[str, List[str]]:
    """Build event_id -> [parent_id, ...] map for local causal edges."""
    return _build_graph_indexes(events)[1]


def _by_id(events) -> Dict[str, Any]:
    return {ev.event_id: ev for ev in events}


def _reachable_from(roots: List[str], children: Dict[str, List[str]]) -> set[str]:
    reachable: set[str] = set()
    stack = list(roots)
    while stack:
        node = stack.pop()
        if node in reachable:
            continue
        reachable.add(node)
        stack.extend(children.get(node, []))
    return reachable


def _topological_order(roots: List[str], children: Dict[str, List[str]]) -> List[str]:
    """Return reachable acyclic nodes in topological order.

    Nodes in cycles are intentionally omitted, which makes analysis bounded on
    invalid traces while `validate_session` reports the integrity failure.
    """
    reachable = _reachable_from(roots, children)
    indegree = {node: 0 for node in reachable}
    for parent in reachable:
        for child in children.get(parent, []):
            if child in indegree:
                indegree[child] += 1

    queue = deque(node for node in reachable if indegree[node] == 0)
    order: List[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for child in children.get(node, []):
            if child not in indegree:
                continue
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    return order


def _depths_from_roots(roots: List[str], children: Dict[str, List[str]]) -> Dict[str, int]:
    depths = {rid: 0 for rid in roots}
    order = _topological_order(roots, children)
    in_order = set(order)
    for node in order:
        if node not in depths:
            continue
        for child in children.get(node, []):
            if child in in_order:
                depths[child] = max(depths.get(child, 0), depths[node] + 1)
    return {node: depths[node] for node in order if node in depths}


def _max_depth_from_node(start_id: str, children: Dict[str, List[str]]) -> int:
    depths = _depths_from_roots([start_id], children)
    return max(depths.values()) if depths else 0


def _max_depth_from_roots(roots: List[str], children: Dict[str, List[str]]) -> int:
    depths = _depths_from_roots(roots, children)
    return max(depths.values()) if depths else 0


def _avg_depth_from_roots(roots: List[str], children: Dict[str, List[str]]) -> float:
    depths = _depths_from_roots(roots, children)
    return sum(depths.values()) / len(depths) if depths else 0.0


# ---------------------------------------------------------------------------
# Layer 1 — Structural primitives
# ---------------------------------------------------------------------------

def compute_stats(events) -> dict:
    """Compute structural session metrics. No semantic interpretation.

    Returns a flat dict with counts, depths, timing, and graph topology.
    """
    if not events:
        return {
            "event_count": 0,
            "tool_count": 0,
            "root_count": 0,
            "leaf_count": 0,
            "max_depth": 0,
            "avg_depth": 0.0,
            "fan_out_avg": 0.0,
            "fan_out_max": 0,
            "chain_length_avg": 0.0,
            "link_ratio": 0.0,
            "multi_parent_count": 0,
            "time_span_s": 0.0,
            "tool_freq": {},
        }

    # ── Basic counts ──
    total = len(events)
    tool_names = [ev.tool_name for ev in events]
    tool_freq = dict(Counter(tool_names).most_common())
    tool_count = len(tool_freq)

    child_index, parent_map = _build_graph_indexes(events)

    # ── Roots and leaves ──
    roots = [ev for ev in events if not parent_map[ev.event_id]]
    root_ids = [ev.event_id for ev in roots]
    root_count = len(roots)

    leaf_ids = [
        ev.event_id for ev in events
        if ev.event_id not in child_index
    ]
    leaf_count = len(leaf_ids)

    # ── Depths ──
    max_depth = _max_depth_from_roots(root_ids, child_index)
    avg_depth = _avg_depth_from_roots(root_ids, child_index) if root_count > 0 else 0.0

    # ── Fan-out distribution ──
    fan_outs: List[int] = []
    for ev in events:
        fan_outs.append(len(child_index.get(ev.event_id, [])))
    fan_out_avg = sum(fan_outs) / len(fan_outs) if fan_outs else 0.0
    fan_out_max = max(fan_outs) if fan_outs else 0

    # ── Link ratio ──
    linked = sum(1 for ev in events if parent_map[ev.event_id])
    link_ratio = linked / total if total else 0.0

    # ── Multi-parent ──
    multi_parent_count = sum(
        1 for ev in events if len(parent_map[ev.event_id]) >= 2
    )

    # ── Chain length ──
    # Compute per-root depths iteratively for chain length stats
    root_depths = [_max_depth_from_node(rid, child_index) for rid in root_ids]
    chain_lengths = [d + 1 for d in root_depths]  # include root itself
    chain_length_avg = sum(chain_lengths) / len(chain_lengths) if chain_lengths else 0.0

    # ── Time span ──
    time_span_s = 0.0
    if len(events) >= 2:
        try:
            t0 = datetime.fromisoformat(events[0].timestamp)
            t1 = datetime.fromisoformat(events[-1].timestamp)
            time_span_s = (t1 - t0).total_seconds()
        except Exception:
            pass

    return {
        "event_count": total,
        "tool_count": tool_count,
        "root_count": root_count,
        "leaf_count": leaf_count,
        "max_depth": max_depth,
        "avg_depth": round(avg_depth, 2),
        "fan_out_avg": round(fan_out_avg, 2),
        "fan_out_max": fan_out_max,
        "chain_length_avg": round(chain_length_avg, 2),
        "link_ratio": round(link_ratio, 3),
        "multi_parent_count": multi_parent_count,
        "time_span_s": round(time_span_s, 1),
        "tool_freq": tool_freq,
    }


def find_roots(events) -> List[dict]:
    """Find all root events with downstream metrics.

    Returns list of dicts, each with:
      event_id, tool_name, tool_input_preview,
      downstream_count, max_subtree_depth
    Sorted by downstream_count descending.
    """
    if not events:
        return []

    child_index, parent_map = _build_graph_indexes(events)
    index = _by_id(events)

    def _count_descendants(node_id: str) -> int:
        """Iterative descendant count."""
        stack = list(child_index.get(node_id, []))
        visited: set = set()
        while stack:
            n = stack.pop()
            if n in visited:
                continue
            visited.add(n)
            stack.extend(child_index.get(n, []))
        return len(visited)

    roots = []
    for ev in events:
        if parent_map[ev.event_id]:
            continue
        downstream = _count_descendants(ev.event_id)
        depth = _max_depth_from_node(ev.event_id, child_index)
        inp = _fmt_input_preview(ev.tool_input)
        roots.append({
            "event_id": ev.event_id,
            "tool_name": ev.tool_name,
            "tool_input_preview": inp,
            "downstream_count": downstream,
            "max_subtree_depth": depth,
            "timestamp": ev.timestamp,
        })

    roots.sort(key=lambda r: -r["downstream_count"])
    return roots


def longest_path(events) -> List[str]:
    """Find the longest root-to-leaf causal chain (critical path).

    Returns list of event_ids forming the deepest chain.
    Uses topological sort + DP for correct handling of DAG merge points.
    """
    if not events:
        return []

    child_index, parent_map = _build_graph_indexes(events)

    # Find roots
    roots = [ev.event_id for ev in events if not parent_map[ev.event_id]]

    order = _topological_order(roots, child_index)
    in_order = set(order)

    # DP in reverse topological order: longest path from each node to a leaf
    longest_from: Dict[str, List[str]] = {}
    for node in reversed(order):
        children = [child for child in child_index.get(node, []) if child in in_order]
        if not children:
            longest_from[node] = [node]
        else:
            best = max(
                (longest_from.get(c, [c]) for c in children),
                key=lambda p: len(p),
                default=[node],
            )
            longest_from[node] = [node] + best

    best_path: List[str] = []
    for r in roots:
        if len(longest_from.get(r, [])) > len(best_path):
            best_path = longest_from[r]
    return best_path


def fan_out_distribution(events) -> dict:
    """Distribution of how many children each event has.

    Returns dict: {fan_out_count: number_of_events_with_that_count}
    """
    child_index = _build_child_index(events)
    hist: Dict[int, int] = defaultdict(int)
    for ev in events:
        n = len(child_index.get(ev.event_id, []))
        hist[n] += 1
    return dict(sorted(hist.items()))


def connected_components(events) -> List[dict]:
    """Find weakly connected components in the causal graph.

    Two nodes are in the same component if connected via parent-child edges
    (traversed undirectionally). Returns list of dicts with:
        size, root_count, event_ids
    Sorted by size descending.
    """
    if not events:
        return []

    _, parent_map = _build_graph_indexes(events)

    # Build undirected adjacency
    adj: Dict[str, List[str]] = defaultdict(list)
    for ev in events:
        eid = ev.event_id
        for pid in parent_map[eid]:
            adj[eid].append(pid)
            adj[pid].append(eid)

    all_ids = {ev.event_id for ev in events}
    visited: set = set()
    components: List[dict] = []

    for eid in all_ids:
        if eid in visited:
            continue
        # BFS
        stack = [eid]
        comp: set = set()
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            comp.add(node)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    stack.append(neighbor)
        root_count_in_comp = sum(
            1 for nid in comp if not parent_map.get(nid)
        )
        components.append({
            "size": len(comp),
            "root_count": root_count_in_comp,
            "event_ids": sorted(comp),
        })

    components.sort(key=lambda c: -c["size"])
    return components


# ---------------------------------------------------------------------------
# Layer 1.5 — Temporal partitioning primitive (no semantics, no state naming)
# ---------------------------------------------------------------------------

def windowed(
    events,
    strategy: str = "count",
    size: int = 100,
    overlap: int = 0,
) -> Iterator[List]:
    """Yield time-local slices of events for temporal analysis.

    Pure temporal partitioning — no phase naming, no state inference.
    Each window is a flat sub-list of ToolEvent, composable with all
    other analysis.py primitives (compute_stats, find_roots, etc.).

    Parameters
    ----------
    strategy:
        "count" — fixed number of events per window (size = event count)
        "time"  — fixed time duration per window (size = seconds)
    size:
        Window size in events (count) or seconds (time).
    overlap:
        Number of events (count) or seconds (time) shared between
        consecutive windows. 0 = non-overlapping.

    Yields
    ------
    List[ToolEvent]  — chronologically sorted, time-local slice.
    """
    if not events:
        return

    # Ensure chronological order
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    if strategy == "count":
        step = size - overlap
        if step < 1:
            step = 1
        for start in range(0, len(sorted_events), step):
            yield sorted_events[start:start + size]

    elif strategy == "time":
        if size < 1:
            return
        t0 = _parse_ts(sorted_events[0].timestamp)
        if t0 is None:
            return
        step = size - overlap
        if step < 1:
            step = 1
        window_end = t0 + timedelta(seconds=size)
        parsed = [(ev, _parse_ts(ev.timestamp)) for ev in sorted_events]
        parsed = [(ev, ts) for ev, ts in parsed if ts is not None]
        if not parsed:
            return
        cursor = parsed[0][1]
        last_ts = parsed[-1][1]
        while cursor <= last_ts:
            window_end = cursor + timedelta(seconds=size)
            current = [ev for ev, ts in parsed if cursor <= ts < window_end]
            if current:
                yield current
            cursor += timedelta(seconds=step)

    else:
        raise ValueError(f"Unknown window strategy: {strategy}")


def _parse_ts(ts: str) -> Optional[datetime]:
    """Parse ISO timestamp string to datetime. Returns None on failure."""
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Layer 2 — Pattern primitives (structural only, no semantic naming)
# ---------------------------------------------------------------------------

def detect_repeated_paths(
    events,
    min_length: int = 2,
    max_length: int = 5,
    min_occurrences: int = 2,
) -> List[dict]:
    """Find tool_name subsequences that repeat across the session.

    Counts simple paths that follow explicit parent-child links.
    Returns patterns sorted by occurrence count descending.

    Each result dict:
      pattern:  [tool_name, ...] (the subsequence)
      occurrences: how many times it appeared
      length:    len(pattern)
    """
    if not events:
        return []

    by_id = _by_id(events)
    children = _build_child_index(events)
    pattern_counter: Counter = Counter()
    for start in by_id:
        stack = [(start, [start])]
        while stack:
            node, path = stack.pop()
            if min_length <= len(path) <= max_length:
                pattern_counter[tuple(by_id[eid].tool_name for eid in path)] += 1
            if len(path) >= max_length:
                continue
            for child in children.get(node, []):
                if child in by_id and child not in path:
                    stack.append((child, path + [child]))

    # Filter by min_occurrences
    results = []
    for pattern, count in pattern_counter.most_common():
        if count < min_occurrences:
            break  # counter.most_common() is sorted descending
        results.append({
            "pattern": list(pattern),
            "occurrences": count,
            "length": len(pattern),
        })

    return results


def detect_common_transitions(
    events,
    top_n: int = 15,
) -> List[dict]:
    """Count (tool_i → tool_j) transitions across the session.

    Returns sorted list of dicts:
      from_tool, to_tool, count
    This is purely structural — no claim about verification/retry/etc.
    """
    if len(events) < 2:
        return []

    by_id = _by_id(events)
    counter: Counter = Counter()
    for ev in events:
        for parent_id in _parse_parents(ev.parent_event_id):
            parent = by_id.get(parent_id)
            if parent:
                counter[(parent.tool_name, ev.tool_name)] += 1

    results = []
    for (a, b), count in counter.most_common(top_n):
        results.append({"from_tool": a, "to_tool": b, "count": count})

    return results


def detect_fan_in_patterns(events) -> List[dict]:
    """Find multi-parent convergence points (events with >= 2 parents).

    Returns list of dicts sorted by parent_count descending:
      event_id, tool_name, parent_count, parent_tools
    """
    index = _by_id(events)
    parent_map = _build_parent_map(events)
    results = []
    for ev in events:
        parents = parent_map[ev.event_id]
        if len(parents) >= 2:
            results.append({
                "event_id": ev.event_id,
                "tool_name": ev.tool_name,
                "parent_count": len(parents),
                "parent_tools": [index[parent_id].tool_name for parent_id in parents],
            })

    results.sort(key=lambda r: -r["parent_count"])
    return results


def detect_branch_collapse(events) -> List[dict]:
    """Find branch convergence: multiple sibling roots → single child.

    Unlike fan-in (same parent), this detects the pattern:
      Root A ──→ Sub A1 ──┐
                           ├──→ Target
      Root B ──→ Sub B1 ──┘

    Returns list of dicts sorted by incoming_branches descending.
    """
    if not events:
        return []

    child_index, parent_map = _build_graph_indexes(events)
    index = _by_id(events)

    # Count how many unique root paths converge to each node
    # A node has branch collapse if its transitive predecessors include
    # events from multiple roots
    roots = [ev for ev in events if not parent_map[ev.event_id]]
    root_ids = [ev.event_id for ev in roots]

    # For each node, find which roots can reach it
    node_roots: Dict[str, set] = defaultdict(set)
    for root_ev in roots:
        rid = root_ev.event_id
        stack = [rid]
        visited: set = set()
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            node_roots[node].add(rid)
            for child_id in child_index.get(node, []):
                stack.append(child_id)

    # Filter: nodes reachable from multiple roots
    collapse_points = []
    for ev in events:
        incoming = node_roots.get(ev.event_id, set())
        if len(incoming) >= 2:
            collapse_points.append({
                "event_id": ev.event_id,
                "tool_name": ev.tool_name,
                "incoming_branches": len(incoming),
                "root_ids": sorted(incoming),
            })

    collapse_points.sort(key=lambda r: -r["incoming_branches"])
    return collapse_points


# ---------------------------------------------------------------------------
# Internal formatters
# ---------------------------------------------------------------------------

def _fmt_input_preview(inp: Any) -> str:
    """Short preview of tool input for display."""
    if isinstance(inp, dict):
        for key in ("command", "file_path", "url", "pattern", "query"):
            if key in inp:
                val = str(inp[key])[:60]
                return f"{key}={val}"
        return str(list(inp.keys())[:2]) if inp else "{}"
    s = str(inp)[:60]
    return s
