"""Corpus management for reproducible trace analysis datasets."""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from collections import Counter
from pathlib import Path
from typing import Any

from .analysis import (
    classify_topology,
    compute_stats,
    detect_branch_collapse,
    detect_branch_persistence,
    detect_fan_in_patterns,
    compute_frontier_width,
    detect_retry_density,
)
from .core import JSONStore
from .metadata import load_metadata
from .annotation import load_annotation


CORPUS_DIR = os.path.expanduser("~/.causetrace/corpus")


def _safe_name(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in name)
    return cleaned.strip(".-") or "snapshot"


def _default_snapshot_name() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def build_session_record(store: JSONStore, session_id: str) -> dict[str, Any]:
    """Build a structural corpus row for a single session."""
    events = store.load(session_id)
    stats = compute_stats(events) if events else {}
    metadata = load_metadata(session_id).to_dict()
    return {
        "session_id": session_id,
        "metadata": metadata,
        "stats": stats,
        "topology": classify_topology(stats) if stats else "mixed",
    }


def list_corpus_records(store: JSONStore) -> list[dict[str, Any]]:
    """Return corpus records for all stored sessions."""
    return [build_session_record(store, sid) for sid in store.list_sessions()]


def snapshot_corpus(
    store: JSONStore,
    *,
    output_dir: str | Path | None = None,
    name: str | None = None,
    session_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Create a reproducible snapshot with sessions, metadata, and manifest."""
    root = Path(output_dir) if output_dir else Path(CORPUS_DIR)
    snapshot_name = _safe_name(name or _default_snapshot_name())
    snapshot_dir = root / "snapshots" / snapshot_name
    sessions_dir = snapshot_dir / "sessions"
    metadata_dir = snapshot_dir / "metadata"
    labels_dir = snapshot_dir / "labels"
    benchmarks_dir = snapshot_dir / "benchmarks"

    for path in (sessions_dir, metadata_dir, labels_dir, benchmarks_dir):
        path.mkdir(parents=True, exist_ok=True)

    selected = session_ids or store.list_sessions()
    records: list[dict[str, Any]] = []
    for sid in selected:
        source_path = store._path(sid)
        if not source_path.exists():
            continue
        shutil.copy2(source_path, sessions_dir / source_path.name)
        record = build_session_record(store, sid)
        records.append(record)
        (metadata_dir / f"{sid}.json").write_text(
            json.dumps(record["metadata"], indent=2, sort_keys=True)
        )

    manifest = {
        "name": snapshot_name,
        "created_at": datetime.now().isoformat(),
        "session_count": len(records),
        "sessions": records,
        "layout": {
            "sessions": "sessions/",
            "metadata": "metadata/",
            "labels": "labels/",
            "benchmarks": "benchmarks/",
        },
    }
    (snapshot_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return {
        "snapshot_dir": str(snapshot_dir),
        "session_count": len(records),
        "manifest": manifest,
    }


def export_dataset(
    store: JSONStore,
    *,
    output: str | Path | None = None,
    session_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Export a dataset manifest with metadata and structural metrics."""
    selected = session_ids or store.list_sessions()
    sessions = [build_session_record(store, sid) for sid in selected]
    dataset = {
        "exported_at": datetime.now().isoformat(),
        "session_count": len(sessions),
        "sessions": sessions,
    }
    if output:
        Path(output).write_text(json.dumps(dataset, indent=2, sort_keys=True))
    return dataset


def group_labeled_sessions(records: list[dict[str, Any]], label: str = "task_type") -> dict[str, list[str]]:
    """Group session IDs by a metadata label."""
    groups: dict[str, list[str]] = {}
    for record in records:
        value = record.get("metadata", {}).get(label) or "unknown"
        groups.setdefault(str(value), []).append(record["session_id"])
    return groups


def summarize_corpus_health(store: JSONStore) -> dict[str, Any]:
    """Summarize corpus size, coverage, and structure gaps against roadmap targets."""
    records = list_corpus_records(store)
    if not records:
        return {
            "session_count": 0,
            "event_count": 0,
            "metadata_sessions": 0,
            "annotated_sessions": 0,
            "explicit_runtime_sessions": 0,
            "heuristic_runtime_sessions": 0,
            "task_type_sessions": 0,
            "source_sessions": 0,
            "topology_counts": {},
            "runtime_counts": {},
            "task_type_counts": {},
            "source_counts": {},
            "structural_counts": {},
            "long_sessions_100": 0,
            "branchy_sessions": 0,
            "frontier_wide_sessions": 0,
            "retry_heavy_sessions": 0,
            "fan_in_sessions": 0,
            "branch_collapse_sessions": 0,
            "multi_root_sessions": 0,
            "milestones": {
                "scale_1000": {
                    "label": "Corpus scale",
                    "target": 1000,
                    "current": 0,
                    "remaining": 1000,
                },
                "research_100": {
                    "label": "Research-ready labeled corpus",
                    "target": 100,
                    "current": 0,
                    "remaining": 100,
                },
                "runtime_4": {
                    "label": "Explicit runtime fingerprint set",
                    "target": 4,
                    "current": 0,
                    "remaining": 4,
                },
                "task_4": {
                    "label": "Task taxonomy breadth",
                    "target": 4,
                    "current": 0,
                    "remaining": 4,
                },
                "fan_in_10": {
                    "label": "Fan-in exemplars",
                    "target": 10,
                    "current": 0,
                    "remaining": 10,
                },
                "branch_collapse_10": {
                    "label": "Branch-collapse exemplars",
                    "target": 10,
                    "current": 0,
                    "remaining": 10,
                },
                "multi_root_10": {
                    "label": "Multi-root exemplars",
                    "target": 10,
                    "current": 0,
                    "remaining": 10,
                },
            },
        }

    session_count = len(records)
    event_count = 0
    metadata_sessions = 0
    annotated_sessions = 0
    explicit_runtime_counts: Counter[str] = Counter()
    heuristic_runtime_counts: Counter[str] = Counter()
    task_type_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    topology_counts: Counter[str] = Counter()
    structural_counts: Counter[str] = Counter()
    long_sessions = 0
    branchy_sessions = 0
    frontier_wide_sessions = 0
    retry_heavy_sessions = 0
    fan_in_sessions = 0
    branch_collapse_sessions = 0
    multi_root_sessions = 0

    for record in records:
        sid = record["session_id"]
        events = store.load(sid)
        stats = record["stats"]
        metadata = record.get("metadata", {})
        sidecar_metadata = load_metadata(sid, include_annotation=False).to_dict()
        annotation = load_annotation(sid)
        event_count += stats.get("event_count", 0)
        if sidecar_metadata:
            metadata_sessions += 1
        if annotation:
            annotated_sessions += 1

        runtime = sidecar_metadata.get("runtime") or ""
        if runtime:
            explicit_runtime_counts[str(runtime)] += 1

        heuristic_runtime = ""
        for ev in events:
            if ev.agent:
                heuristic_runtime = ev.agent
                break
            if ev.provider:
                heuristic_runtime = ev.provider
                break
        if heuristic_runtime:
            heuristic_runtime_counts[str(heuristic_runtime)] += 1

        task_type = metadata.get("task_type") or annotation.get("task_type") or ""
        if task_type:
            task_type_counts[str(task_type)] += 1

        source = metadata.get("task_source") or annotation.get("source") or ""
        if source:
            source_counts[str(source)] += 1

        topology = record.get("topology") or classify_topology(stats)
        topology_counts[str(topology)] += 1

        if stats.get("event_count", 0) >= 100:
            long_sessions += 1
        if stats.get("root_count", 0) >= 5:
            multi_root_sessions += 1

        fan_in = len(detect_fan_in_patterns(events))
        collapse = len(detect_branch_collapse(events))
        branches = detect_branch_persistence(events)
        frontier = compute_frontier_width(events)
        retry = detect_retry_density(events)

        if fan_in > 0:
            fan_in_sessions += 1
        if collapse > 0:
            branch_collapse_sessions += 1
        if len(branches) > 1:
            branchy_sessions += 1
        if frontier["max_width"] >= 4:
            frontier_wide_sessions += 1
        if retry["retry_density"] >= 0.2:
            retry_heavy_sessions += 1

        if fan_in > 0:
            structural_counts["fan_in"] += 1
        if collapse > 0:
            structural_counts["branch_collapse"] += 1
        if frontier["max_width"] >= 4:
            structural_counts["frontier_width_ge_4"] += 1
        if retry["retry_density"] >= 0.2:
            structural_counts["retry_density_ge_0.2"] += 1
        if stats.get("root_count", 0) >= 5:
            structural_counts["multi_root_ge_5"] += 1

    milestones = {
        "scale_1000": {
            "label": "Corpus scale",
            "target": 1000,
            "current": session_count,
            "remaining": max(1000 - session_count, 0),
        },
        "research_100": {
            "label": "Research-ready labeled corpus",
            "target": 100,
            "current": metadata_sessions,
            "remaining": max(100 - metadata_sessions, 0),
        },
        "runtime_4": {
            "label": "Explicit runtime fingerprint set",
            "target": 4,
            "current": len(explicit_runtime_counts),
            "remaining": max(4 - len(explicit_runtime_counts), 0),
        },
        "task_4": {
            "label": "Task taxonomy breadth",
            "target": 4,
            "current": len(task_type_counts),
            "remaining": max(4 - len(task_type_counts), 0),
        },
        "fan_in_10": {
            "label": "Fan-in exemplars",
            "target": 10,
            "current": fan_in_sessions,
            "remaining": max(10 - fan_in_sessions, 0),
        },
        "branch_collapse_10": {
            "label": "Branch-collapse exemplars",
            "target": 10,
            "current": branch_collapse_sessions,
            "remaining": max(10 - branch_collapse_sessions, 0),
        },
        "multi_root_10": {
            "label": "Multi-root exemplars",
            "target": 10,
            "current": multi_root_sessions,
            "remaining": max(10 - multi_root_sessions, 0),
        },
    }

    return {
        "session_count": session_count,
        "event_count": event_count,
        "metadata_sessions": metadata_sessions,
        "annotated_sessions": annotated_sessions,
        "explicit_runtime_sessions": sum(explicit_runtime_counts.values()),
        "heuristic_runtime_sessions": sum(heuristic_runtime_counts.values()),
        "task_type_sessions": sum(1 for record in records if (record.get("metadata", {}).get("task_type") or load_annotation(record["session_id"]).get("task_type"))),
        "source_sessions": sum(1 for record in records if (record.get("metadata", {}).get("task_source") or load_annotation(record["session_id"]).get("source"))),
        "runtime_counts": dict(explicit_runtime_counts),
        "heuristic_runtime_counts": dict(heuristic_runtime_counts),
        "task_type_counts": dict(task_type_counts),
        "source_counts": dict(source_counts),
        "topology_counts": dict(topology_counts),
        "structural_counts": dict(structural_counts),
        "long_sessions_100": long_sessions,
        "branchy_sessions": branchy_sessions,
        "frontier_wide_sessions": frontier_wide_sessions,
        "retry_heavy_sessions": retry_heavy_sessions,
        "fan_in_sessions": fan_in_sessions,
        "branch_collapse_sessions": branch_collapse_sessions,
        "multi_root_sessions": multi_root_sessions,
        "milestones": milestones,
    }
