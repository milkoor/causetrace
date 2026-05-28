"""Markdown research report templates for trace sessions."""
from __future__ import annotations

from .analysis import (
    compute_stats,
    detect_common_transitions,
    detect_topology_shift,
    find_roots,
    longest_path,
)
from .core import _fmt_input
from .metadata import load_metadata


def generate_report(session_id: str, events, *, window_size: int = 50, top: int = 10) -> str:
    """Generate a structural report template without automated conclusions."""
    stats = compute_stats(events)
    metadata = load_metadata(session_id).to_dict()
    roots = find_roots(events)
    transitions = detect_common_transitions(events, top_n=top)
    path = longest_path(events)
    by_id = {ev.event_id: ev for ev in events}
    shifts = detect_topology_shift(events, window_size=window_size)

    lines: list[str] = [
        f"# causetrace report: {session_id}",
        "",
        "## Metadata",
        "",
    ]

    if metadata:
        for key in sorted(metadata):
            lines.append(f"- {key}: {metadata[key]}")
    else:
        lines.append("- runtime:")
        lines.append("- model:")
        lines.append("- task_type:")
        lines.append("- task_source:")
        lines.append("- success:")
    lines.extend(["", "## Stats", ""])

    for key in (
        "event_count",
        "tool_count",
        "root_count",
        "leaf_count",
        "max_depth",
        "avg_depth",
        "fan_out_avg",
        "fan_out_max",
        "link_ratio",
        "multi_parent_count",
        "time_span_s",
    ):
        lines.append(f"- {key}: {stats.get(key)}")

    lines.extend(["", "## Roots", ""])
    if roots:
        for root in roots[:top]:
            preview = root["tool_input_preview"].replace("\n", " ")[:80]
            lines.append(
                f"- {root['event_id']} {root['tool_name']} "
                f"downstream={root['downstream_count']} depth={root['max_subtree_depth']} "
                f"input={preview}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Transitions", ""])
    if transitions:
        for transition in transitions:
            lines.append(
                f"- {transition['from_tool']} -> {transition['to_tool']}: {transition['count']}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Critical Path", ""])
    if path:
        for depth, event_id in enumerate(path):
            ev = by_id.get(event_id)
            if not ev:
                continue
            lines.append(f"- depth {depth}: {ev.tool_name}({_fmt_input(ev.tool_input)}) id={event_id}")
    else:
        lines.append("- none")

    lines.extend(["", "## Window Drift", ""])
    if shifts:
        for shift in shifts:
            metrics = ", ".join(f"{k}={v}" for k, v in shift["shifts"].items())
            lines.append(
                f"- window {shift['window']} events "
                f"{shift['event_index_start']}-{shift['event_index_end']}: {metrics}"
            )
    else:
        lines.append(f"- no significant topology shifts detected at window_size={window_size}")

    lines.extend([
        "",
        "## Observations",
        "",
        "- Topology pattern:",
        "- Runtime-specific behavior:",
        "- Retry or repair structure:",
        "- Branching and collapse notes:",
        "- Open questions:",
        "",
    ])
    return "\n".join(lines)
