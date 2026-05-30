"""Markdown research report templates for trace sessions."""
from __future__ import annotations

from collections import Counter

from .analysis import (
    compute_stats,
    detect_common_transitions,
    detect_topology_shift,
    find_roots,
    longest_path,
)
from .corpus import assess_phase3_readiness, build_corpus_source_facts, summarize_corpus_health
from .core import _fmt_input
from .metadata import load_metadata, load_metadata_provenance


_STRICT_RESEARCH_FIELDS = ("runtime", "task_type", "task_source", "success")
_OPTIONAL_RESEARCH_FIELDS = ("model", "repo_language", "repo_size", "duration", "human_intervention")
_TRUSTED_PROVENANCE_SOURCES = {"explicit_sidecar", "annotation"}


def _field_provenance_audit(store) -> dict[str, dict[str, int]]:
    audit: dict[str, Counter[str]] = {
        field: Counter() for field in (*_STRICT_RESEARCH_FIELDS, *_OPTIONAL_RESEARCH_FIELDS)
    }
    for sid in store.list_sessions():
        metadata = load_metadata(sid).to_dict()
        provenance = load_metadata_provenance(sid)
        for field in audit:
            if metadata.get(field) in (None, "", [], {}):
                audit[field]["missing"] += 1
                continue
            source = provenance.get(field, "unknown")
            audit[field][source] += 1
    return {field: dict(counts) for field, counts in audit.items()}


def _research_grade_candidates(store, *, limit: int = 10) -> dict[str, object]:
    candidates: list[dict[str, object]] = []
    strict_total = 0
    strict_passing = 0
    for sid in store.list_sessions():
        metadata = load_metadata(sid).to_dict()
        provenance = load_metadata_provenance(sid)
        missing_strict: list[str] = []
        untrusted_strict: list[str] = []
        missing_optional: list[str] = []

        for field in _STRICT_RESEARCH_FIELDS:
            value = metadata.get(field)
            source = provenance.get(field, "unknown")
            if value in (None, "", [], {}):
                missing_strict.append(field)
                continue
            if source not in _TRUSTED_PROVENANCE_SOURCES:
                untrusted_strict.append(field)

        for field in _OPTIONAL_RESEARCH_FIELDS:
            if metadata.get(field) in (None, "", [], {}):
                missing_optional.append(field)

        if not missing_strict and not untrusted_strict:
            strict_passing += 1
        else:
            candidates.append({
                "session_id": sid,
                "missing_strict": missing_strict,
                "untrusted_strict": untrusted_strict,
                "missing_optional": missing_optional,
                "missing_total": len(missing_strict) + len(untrusted_strict) + len(missing_optional),
            })

        strict_total += 1

    candidates.sort(
        key=lambda item: (
            item["missing_total"],
            len(item["missing_strict"]),
            len(item["untrusted_strict"]),
            len(item["missing_optional"]),
            item["session_id"],
        )
    )
    return {
        "strict_research_grade_sessions": strict_passing,
        "strict_research_grade_total": strict_total,
        "near_misses": candidates[:limit],
    }


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
    provenance_audit = _field_provenance_audit(store)
    research_grade = _research_grade_candidates(store)

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
        f"- research-grade sessions: {summary['research_grade_sessions']}",
        f"- strict research-grade sessions: {research_grade['strict_research_grade_sessions']}",
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
        "- metadata provenance counts:",
    ])
    provenance_counts = summary.get("metadata_provenance_counts", {})
    if provenance_counts:
        for label, count in sorted(provenance_counts.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"  - {label}: {count}")
    else:
        lines.append("  - none")

    lines.extend([
        "",
        "## Metadata Provenance Audit",
        "",
    ])
    for field in (*_STRICT_RESEARCH_FIELDS, *_OPTIONAL_RESEARCH_FIELDS):
        lines.append(f"- {field}:")
        field_counts = provenance_audit.get(field, {})
        for source, count in sorted(field_counts.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"  - {source}: {count}")

    lines.extend([
        "",
        "## Missing Metadata Coverage",
        "",
    ])
    missing_counts = summary.get("metadata_missing_counts", {})
    for field in (*_STRICT_RESEARCH_FIELDS, *_OPTIONAL_RESEARCH_FIELDS):
        count = missing_counts.get(field, 0)
        lines.append(f"- {field}: {count}")

    lines.extend([
        "",
        "## Near Research-Grade Sessions",
        "",
        f"- strict research-grade sessions: {research_grade['strict_research_grade_sessions']}/{research_grade['strict_research_grade_total']}",
    ])
    near_misses = research_grade["near_misses"]
    if near_misses:
        for item in near_misses:
            missing = ", ".join(item["missing_strict"]) or "none"
            untrusted = ", ".join(item["untrusted_strict"]) or "none"
            optional = ", ".join(item["missing_optional"]) or "none"
            lines.append(
                f"- {item['session_id']}: missing={missing}; "
                f"untrusted={untrusted}; optional_missing={optional}"
            )
    else:
        lines.append("- none")

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


def generate_corpus_origin_report(store) -> str:
    """Render a markdown report for corpus source-origin coverage."""
    summary = build_corpus_source_facts(store)
    task_source_counts = summary.get("task_source_counts", {})
    lane_hint_counts: dict[str, int] = {}
    lane_hints = {
        "demo": "demo-lane candidate (keep separate from controlled_benchmark)",
        "real_work": "native candidate",
        "proxy": "proxy-mediated candidate",
        "unknown": "manual classification needed",
    }
    for source, count in task_source_counts.items():
        hint = lane_hints.get(source, "manual classification needed")
        lane_hint_counts[hint] = lane_hint_counts.get(hint, 0) + count

    lines: list[str] = [
        "# Corpus origin report",
        "",
        "## Snapshot",
        "",
        f"- sessions: {summary['session_count']}",
        f"- data-origin labeled sessions: {sum(summary['data_origin_counts'].values())}",
        f"- missing data_origin: {summary['missing_data_origin']}",
        "",
        "## Data Origin Counts",
        "",
    ]

    data_origin_counts = summary.get("data_origin_counts", {})
    if data_origin_counts:
        for label, count in sorted(data_origin_counts.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Data Origin Provenance",
        "",
    ])
    provenance_counts = summary.get("data_origin_provenance_counts", {})
    if provenance_counts:
        for label, count in sorted(provenance_counts.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Task Source Counts",
        "",
    ])
    if task_source_counts:
        for label, count in sorted(task_source_counts.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Task Source Lane Hints",
        "",
    ])
    if lane_hint_counts:
        for label, count in sorted(lane_hint_counts.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Missing Data Origin Candidates",
        "",
    ])
    missing_sessions = summary.get("missing_data_origin_sessions", [])
    if missing_sessions:
        for item in missing_sessions:
            parts = [
                f"runtime={item['runtime'] or 'unknown'}",
                f"task_type={item['task_type'] or 'unknown'}",
                f"task_source={item['task_source'] or 'unknown'}",
                f"success={item['success'] if item['success'] != '' else 'unknown'}",
                f"topology={item['topology'] or 'unknown'}",
                f"score={item['score']}",
            ]
            lines.append(f"- {item['session_id']}: " + "; ".join(parts))
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Phase 3C Guidance",
        "",
        "- Treat data_origin as a top-level source tier, separate from task_source.",
        "- Keep native corpus, controlled benchmark corpus, and external trajectories in separate provenance lanes.",
        "- Prefer labeling missing data_origin on research-grade sessions before adding new taxonomy labels.",
        "",
    ])
    return "\n".join(lines)


def generate_phase3_readiness_report(store) -> str:
    """Render a markdown report for phase-3 research readiness."""
    readiness = assess_phase3_readiness(store)
    summary = readiness["summary"]
    research_grade = _research_grade_candidates(store)

    lines: list[str] = [
        "# Phase 3 readiness report",
        "",
        "## Snapshot",
        "",
        f"- ready: {readiness['ready']}",
        f"- sessions: {readiness['session_count']}",
        f"- explicit metadata sessions: {readiness['metadata_sessions']}",
        f"- explicit runtime sessions: {readiness['explicit_runtime_sessions']}",
        f"- task-type sessions: {readiness['task_type_sessions']}",
        f"- research-grade sessions: {readiness['research_grade_sessions']}",
        f"- strict research-grade sessions: {research_grade['strict_research_grade_sessions']}",
        f"- runtime breadth: {readiness['runtime_breadth']}",
        f"- task breadth: {readiness['task_breadth']}",
        "",
        "## Research Protocol",
        "",
        "- Canonical metadata fields:",
    ]

    for field in readiness["canonical_metadata_fields"]:
        lines.append(f"  - {field}")

    lines.extend([
        "- Taxonomy protocol:",
    ])
    for label, description in readiness["taxonomy_protocol"].items():
        lines.append(f"  - {label}: {description}")

    lines.extend([
        "- Taxonomy is observational, not ontological.",
        "- Negative results must be recorded alongside positive findings.",
        "",
        "## Criteria",
        "",
    ])

    for item in readiness["criteria"]:
        marker = "[x]" if item["passed"] else "[ ]"
        lines.append(
            f"- {marker} {item['label']}: {item['current']}/{item['target']} (remaining {item['remaining']})"
        )

    lines.extend([
        "",
        "## Blockers",
        "",
    ])
    if readiness["blockers"]:
        for item in readiness["blockers"]:
            lines.append(f"- {item['label']} still short by {item['remaining']}")
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Explicit Metadata Coverage",
        "",
    ])
    for field in readiness["canonical_metadata_fields"]:
        count = readiness["explicit_metadata_field_counts"].get(field, 0)
        lines.append(f"- {field}: {count}")

    lines.extend([
        "",
        "## Missing Metadata Coverage",
        "",
    ])
    missing_counts = summary.get("metadata_missing_counts", {})
    for field in readiness["canonical_metadata_fields"]:
        lines.append(f"- {field}: {missing_counts.get(field, 0)}")

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
        "## Near Research-Grade Sessions",
        "",
    ])
    near_misses = research_grade["near_misses"]
    if near_misses:
        for item in near_misses:
            missing = ", ".join(item["missing_strict"]) or "none"
            untrusted = ", ".join(item["untrusted_strict"]) or "none"
            optional = ", ".join(item["missing_optional"]) or "none"
            lines.append(
                f"- {item['session_id']}: missing={missing}; "
                f"untrusted={untrusted}; optional_missing={optional}"
            )
    else:
        lines.append("- none")

    lines.extend([
        "",
    ])
    return "\n".join(lines)
