"""Temporal causality inference for OpenCode log events.

Without tool input/output, we infer causality from temporal patterns:
  1. Turn boundaries: question tool = user prompt
  2. Sequential chaining: events in a turn are causally linked
  3. Multi-cause (fan-in): multiple reads → one write/edit depends on all
  4. Agent hierarchy: task tools contain sub-events
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from .core import ToolEvent


def infer_relations(events: List[ToolEvent]) -> List[ToolEvent]:
    """Infer causal relationships from temporal event data.

    Mutates events in-place, setting parent_event_id and adding
    multi_parent_ids metadata. Returns the same list for chaining.
    """
    if not events:
        return events

    # Index by event_id
    by_id: Dict[str, ToolEvent] = {e.event_id: e for e in events}
    # Track additional parents per event (for multi-cause)
    extra_parents: Dict[str, List[str]] = defaultdict(list)

    # Phase 1: Detect turns (user question boundaries)
    turns = _detect_turns(events)

    # Phase 2: Sequential linking within each turn
    for turn in turns:
        _link_sequential(turn, by_id)

    # Phase 3: Multi-cause (fan-in) detection
    for turn in turns:
        fan_ins = _detect_fan_in(turn)
        for child_id, parent_ids in fan_ins.items():
            extra_parents[child_id].extend(parent_ids)

    # Phase 4: Agent subtask hierarchy
    for turn in turns:
        _link_subtasks(turn, by_id)

    # Store extra parents as metadata in parent_event_id chain
    # We serialize them inline using comma separation
    for child_id, parents in extra_parents.items():
        child = by_id.get(child_id)
        if child and parents:
            existing = child.parent_event_id
            # Filter out existing primary parent
            additional = [p for p in parents if p != existing]
            if additional:
                all_parents = [existing] + additional if existing else additional
                child.parent_event_id = ",".join(all_parents)

    # Phase 5: Break any cycles in the causal graph (safety net)
    _break_cycles(events)

    return events


def _detect_turns(events: List[ToolEvent]) -> List[List[ToolEvent]]:
    """Split events into reasoning turns at each 'question' boundary."""
    turns: List[List[ToolEvent]] = []
    current: List[ToolEvent] = []
    for ev in events:
        if ev.tool_name == "question" and current:
            turns.append(current)
            current = []
        current.append(ev)
    if current:
        turns.append(current)
    return turns


def _link_sequential(turn: List[ToolEvent], by_id: Dict[str, ToolEvent]) -> None:
    """Chain events chronologically within a turn."""
    prev_id: Optional[str] = None
    for ev in turn:
        if ev.tool_name.lower() in ("question", "invalid"):
            prev_id = None
            continue
        if prev_id and not ev.parent_event_id:
            # 时间戳检查：确保父事件时间早于子事件
            parent_ev = by_id.get(prev_id)
            if parent_ev and parent_ev.timestamp and ev.timestamp:
                if parent_ev.timestamp <= ev.timestamp:
                    ev.parent_event_id = prev_id
        prev_id = ev.event_id


_READ_TOOLS = {"read", "grep", "glob", "lsp_diagnostics", "lsp_symbols",
               "lsp_find_references", "lsp_goto_definition", "lsp_prepare_rename",
               "look_at", "session_read", "session_search", "session_list",
               "session_info", "webfetch", "websearch", "ast_grep_search"}

_WRITE_TOOLS = {"write", "edit", "bash", "interactive_bash", "skill_mcp",
                "ast_grep_replace", "lsp_rename"}

_AGENT_TOOLS = {"task", "call_omo_agent"}


def _detect_fan_in(turn: List[ToolEvent], max_gap: int = 3) -> Dict[str, List[str]]:
    """Detect multi-cause: multiple reads followed by one write/edit.

    Heuristic: if multiple read-phase tools appear within `max_gap` events
    before a write-phase tool, they're all considered causal parents.
    `max_gap` limits backward search distance (filters out stale reads).
    """
    fan_ins: Dict[str, List[str]] = defaultdict(list)

    for i, ev in enumerate(turn):
        if ev.tool_name.lower() not in _WRITE_TOOLS:
            continue

        read_ids: List[str] = []
        seen_non_read = 0
        for j in range(i - 1, -1, -1):
            prev = turn[j]
            if prev.tool_name.lower() in ("question", "invalid"):
                break
            if prev.tool_name.lower() in _READ_TOOLS:
                # 时间戳检查：确保读事件早于写事件
                if prev.timestamp and ev.timestamp and prev.timestamp <= ev.timestamp:
                    read_ids.append(prev.event_id)
                    seen_non_read = 0
            else:
                seen_non_read += 1
                if seen_non_read > max_gap:
                    break
            if len(read_ids) >= 5:  # Cap at 5 parents max
                break

        if len(read_ids) >= 2:
            fan_ins[ev.event_id] = read_ids
        elif len(read_ids) == 1 and ev.tool_name.lower() in ("bash", "interactive_bash"):
            fan_ins[ev.event_id] = read_ids

    return fan_ins


def _link_subtasks(turn: List[ToolEvent], by_id: Dict[str, ToolEvent]) -> None:
    """Detect agent subtask hierarchy: task tools create parent-child groups.

    Pattern: task → [sub-tools] → non-task
    Events between task and next non-task are children of the task.
    """
    task_stack: List[str] = []
    for ev in turn:
        if ev.tool_name in _AGENT_TOOLS:
            task_stack.append(ev.event_id)
            # Mark sub-tools as children of this task
            continue

        if task_stack and not ev.parent_event_id:
            ev.parent_event_id = task_stack[-1]

        # If this tool is NOT an agent tool, it might close the task scope


def parse_multi_parent(parent_str: Optional[str]) -> List[str]:
    """Parse a multi-parent string back into a list of event IDs."""
    if not parent_str:
        return []
    return [p.strip() for p in parent_str.split(",") if p.strip()]


def build_causal_graph(events: List[ToolEvent]) -> Dict[str, List[str]]:
    """Build a full causal graph: event_id → list of parent event_ids."""
    graph: Dict[str, List[str]] = {}
    for ev in events:
        parents = parse_multi_parent(ev.parent_event_id)
        graph[ev.event_id] = parents
    return graph


def _break_cycles(events: List[ToolEvent]) -> int:
    """Detect and break cycles in the causal graph using DFS.

    When a cycle is found, the back-edge is removed (parent_event_id cleared).
    Returns the number of cycles broken.
    """
    # Build initial graph snapshot
    graph: Dict[str, List[str]] = {}
    for ev in events:
        parents = parse_multi_parent(ev.parent_event_id)
        graph[ev.event_id] = parents

    cycles_broken = 0
    for ev in events:
        parent_ids = parse_multi_parent(ev.parent_event_id)
        if not parent_ids:
            continue

        clean_parents: List[str] = []
        for pid in parent_ids:
            if _would_create_cycle(graph, ev.event_id, pid):
                cycles_broken += 1
            else:
                clean_parents.append(pid)

        if len(clean_parents) == len(parent_ids):
            continue

        if clean_parents:
            ev.parent_event_id = ",".join(clean_parents)
        else:
            ev.parent_event_id = None
        graph[ev.event_id] = clean_parents

    return cycles_broken


def _would_create_cycle(graph: Dict[str, List[str]], child_id: str, parent_id: str) -> bool:
    """Check if setting parent_id as parent of child_id would create a cycle."""
    visited = {child_id}
    stack = [parent_id]
    while stack:
        current = stack.pop()
        if current in visited:
            return True  # Cycle found
        visited.add(current)
        # Traverse parents of current
        for p in graph.get(current, []):
            if p not in visited:
                stack.append(p)
    return False


def causal_quality_report(events: List[ToolEvent]) -> dict:
    """Generate a quality report for the causal graph of a session.

    Returns a dict with:
      - total_events
      - linked_events (events with parent_event_id)
      - root_events (events without parent)
      - multi_parent_events
      - max_depth
      - avg_chain_length
      - cycles_broken
      - score (0.0-1.0 quality score)
    """
    if not events:
        return {
            "total_events": 0,
            "linked_events": 0,
            "root_events": 0,
            "multi_parent_events": 0,
            "max_depth": 0,
            "avg_chain_length": 0.0,
            "cycles_broken": 0,
            "score": 1.0,
        }

    total = len(events)
    linked = sum(1 for ev in events if ev.parent_event_id)
    roots = total - linked
    multi = sum(1 for ev in events if ev.parent_event_id and "," in ev.parent_event_id)

    # Calculate depths from each root
    graph: Dict[str, List[str]] = {}
    children: Dict[str, List[str]] = defaultdict(list)
    for ev in events:
        parents_str = ev.parent_event_id or ""
        parents = parse_multi_parent(parents_str)
        graph[ev.event_id] = parents
        for p in parents:
            children[p].append(ev.event_id)

    def _depth(node_id: str, seen: set) -> int:
        if node_id in seen:
            return 0
        seen.add(node_id)
        max_child = 0
        for c in children.get(node_id, []):
            max_child = max(max_child, 1 + _depth(c, seen))
        seen.discard(node_id)
        return max_child

    root_ids = [ev.event_id for ev in events if not ev.parent_event_id]
    depths = [_depth(rid, set()) for rid in root_ids]
    max_depth = max(depths) if depths else 0
    avg_chain = sum(depths) / len(depths) if depths else 0.0

    # Quality score: linked/root density + chain coherence
    link_ratio = linked / total if total else 0
    chain_score = min(1.0, max_depth / 20)  # deeper is better, cap at 20
    score = max(0.0, min(1.0, link_ratio * 0.5 + chain_score * 0.5))

    # Detect any remaining cycles (should be 0 after _break_cycles)
    cycles_remaining = _count_cycles(graph)

    return {
        "total_events": total,
        "linked_events": linked,
        "root_events": roots,
        "multi_parent_events": multi,
        "max_depth": max_depth,
        "avg_chain_length": round(avg_chain, 2),
        "cycles_remaining": cycles_remaining,
        "score": round(score, 3),
    }


def _count_cycles(graph: Dict[str, List[str]]) -> int:
    """Count remaining cycles in causal graph using DFS."""
    visited: set = set()
    rec_stack: set = set()
    cycles = 0

    def _dfs(node: str) -> None:
        nonlocal cycles
        visited.add(node)
        rec_stack.add(node)
        for parent in graph.get(node, []):
            if parent not in visited:
                _dfs(parent)
            elif parent in rec_stack:
                cycles += 1
        rec_stack.discard(node)

    for node in graph:
        if node not in visited:
            _dfs(node)
    return cycles
