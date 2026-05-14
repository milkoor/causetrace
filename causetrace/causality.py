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
        if ev.tool_name in ("question", "invalid"):
            prev_id = None
            continue
        if prev_id and not ev.parent_event_id:
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
        if ev.tool_name not in _WRITE_TOOLS:
            continue

        read_ids: List[str] = []
        seen_non_read = 0
        for j in range(i - 1, -1, -1):
            prev = turn[j]
            if prev.tool_name in ("question", "invalid"):
                break
            if prev.tool_name in _READ_TOOLS:
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
        elif len(read_ids) == 1 and ev.tool_name in ("bash", "interactive_bash"):
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
