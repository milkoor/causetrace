"""Markdown research report templates for trace sessions."""
from __future__ import annotations

from .analysis import (
    compute_stats,
    detect_common_transitions,
    detect_topology_shift,
    find_roots,
    longest_path,
)
from .corpus import summarize_corpus_health
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


def generate_corpus_health_report(store) -> str:
    """Render a markdown corpus gap report for the current local dataset."""
    summary = summarize_corpus_health(store)
    milestones = summary["milestones"]

    lines: list[str] = [
        "# Corpus health report",
        "",
        "## Snapshot",
        "",
        f"- sessions: {summary['session_count']}",
        f"- events: {summary['event_count']}",
        f"- metadata sessions: {summary['metadata_sessions']}",
        f"- annotated sessions: {summary['annotated_sessions']}",
        f"- explicit runtime sessions: {summary['explicit_runtime_sessions']}",
        f"- heuristic runtime sessions: {summary['heuristic_runtime_sessions']}",
        f"- task-type sessions: {summary['task_type_sessions']}",
        f"- source sessions: {summary['source_sessions']}",
        "",
        "## Milestones",
        "",
    ]

    for key in ("scale_1000", "research_100", "runtime_4", "task_4", "fan_in_10", "branch_collapse_10", "multi_root_10"):
        item = milestones[key]
        lines.append(
            f"- {item['label']}: {item['current']}/{item['target']} (remaining {item['remaining']})"
        )

    lines.extend([
        "",
        "## Coverage",
        "",
        "- explicit runtime counts:",
    ])

    runtime_counts = summary["runtime_counts"]
    if runtime_counts:
        for label, count in sorted(runtime_counts.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"  - {label}: {count}")
    else:
        lines.append("  - none")

    lines.append("- task type counts:")
    task_counts = summary["task_type_counts"]
    if task_counts:
        for label, count in sorted(task_counts.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"  - {label}: {count}")
    else:
        lines.append("  - none")

    lines.append("- topology counts:")
    topo_counts = summary["topology_counts"]
    for label, count in sorted(topo_counts.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"  - {label}: {count}")

    lines.extend([
        "",
        "## Structural Signals",
        "",
        f"- long sessions (>=100 events): {summary['long_sessions_100']}",
        f"- branchy sessions: {summary['branchy_sessions']}",
        f"- frontier-wide sessions (max width >= 4): {summary['frontier_wide_sessions']}",
        f"- retry-heavy sessions (retry density >= 0.2): {summary['retry_heavy_sessions']}",
        f"- fan-in sessions: {summary['fan_in_sessions']}",
        f"- branch-collapse sessions: {summary['branch_collapse_sessions']}",
        f"- multi-root sessions (roots >= 5): {summary['multi_root_sessions']}",
        "",
        "## Missing Conditions",
        "",
        "- Need more metadata-rich sessions to make task/topology comparisons stable.",
        "- Need explicit runtime labels across Claude, Codex, Aider, and OpenCode.",
        "- Need more fan-in, branch-collapse, and multi-root exemplars to prevent the taxonomy from collapsing into mostly linear chains.",
        "- Need a larger labeled corpus before treating topology-task correlations as stable.",
        "",
    ])
    return "\n".join(lines)
