"""Corpus management for reproducible trace analysis datasets."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime
from collections import Counter
from dataclasses import dataclass
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
from .metadata import (
    infer_metadata_provenance,
    load_metadata,
    load_metadata_provenance,
    merge_metadata,
    save_metadata_provenance,
)
from .annotation import load_annotation


CORPUS_DIR = os.path.expanduser("~/.causetrace/corpus")

PHASE3_CANONICAL_METADATA_FIELDS = (
    "runtime",
    "model",
    "task_type",
    "task_source",
    "repo_language",
    "repo_size",
    "success",
    "duration",
    "human_intervention",
)

PHASE3_TAXONOMY_PROTOCOL = {
    "deep_linear": "Single deep chain with low branching",
    "retry_heavy": "High structural repetition and local loops",
    "branchy": "Wide branching or active frontier width",
    "fan_in": "Multi-parent convergence points",
    "branch_collapse": "Multiple roots converging into shared descendants",
    "multi_root_exploration": "Many shallow independent roots",
    "long_session": "Sessions with at least 100 events",
}


@dataclass(frozen=True)
class Phase3ReadinessRequirements:
    """Thresholds for phase-3 entry qualification."""

    min_sessions: int = 100
    min_metadata_sessions: int = 100
    min_explicit_runtime_sessions: int = 100
    min_task_type_sessions: int = 100
    min_runtime_breadth: int = 4
    min_task_breadth: int = 4
    min_fan_in_sessions: int = 10
    min_branch_collapse_sessions: int = 10
    min_multi_root_sessions: int = 10
    min_long_sessions: int = 10
    min_retry_heavy_sessions: int = 10


def _safe_name(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in name)
    return cleaned.strip(".-") or "snapshot"


def _default_snapshot_name() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _session_digest(path: Path) -> str:
    """Return a stable digest for a stored session file."""
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def _snapshot_digest(records: list[dict[str, Any]]) -> str:
    """Return a stable digest for a dataset/snapshot manifest."""
    payload = json.dumps(
        [
            {
                "session_id": record["session_id"],
                "session_hash": record.get("session_hash", ""),
                "metadata": record.get("metadata", {}),
                "stats": record.get("stats", {}),
                "topology": record.get("topology", ""),
            }
            for record in sorted(records, key=lambda item: item["session_id"])
        ],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_session_record(store: JSONStore, session_id: str) -> dict[str, Any]:
    """Build a structural corpus row for a single session."""
    events = store.load(session_id)
    stats = compute_stats(events) if events else {}
    metadata = load_metadata(session_id).to_dict()
    metadata_provenance = infer_metadata_provenance(session_id)
    source_path = store._path(session_id)
    return {
        "session_id": session_id,
        "session_hash": _session_digest(source_path) if source_path.exists() else "",
        "session_bytes": source_path.stat().st_size if source_path.exists() else 0,
        "metadata": metadata,
        "metadata_provenance": metadata_provenance,
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
        "snapshot_hash": _snapshot_digest(records),
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
        "dataset_hash": _snapshot_digest(sessions),
        "sessions": sessions,
    }
    if output:
        Path(output).write_text(json.dumps(dataset, indent=2, sort_keys=True))
    return dataset


def build_corpus_facts(store: JSONStore) -> dict[str, Any]:
    """Collect corpus facts once so health and readiness share one core count pass."""
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
            "research_grade_sessions": 0,
            "metadata_provenance_counts": {},
            "metadata_missing_counts": {field: 0 for field in PHASE3_CANONICAL_METADATA_FIELDS},
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
            "explicit_metadata_field_counts": {field: 0 for field in PHASE3_CANONICAL_METADATA_FIELDS},
        }

    session_count = len(records)
    event_count = 0
    metadata_sessions = 0
    annotated_sessions = 0
    research_grade_sessions = 0
    explicit_runtime_counts: Counter[str] = Counter()
    heuristic_runtime_counts: Counter[str] = Counter()
    task_type_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    topology_counts: Counter[str] = Counter()
    structural_counts: Counter[str] = Counter()
    explicit_metadata_field_counts: Counter[str] = Counter()
    metadata_provenance_counts: Counter[str] = Counter()
    metadata_missing_counts: Counter[str] = Counter()
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
        explicit_metadata = load_metadata(sid, include_annotation=False).to_dict()
        annotation = load_annotation(sid)
        provenance = record.get("metadata_provenance", {})
        event_count += stats.get("event_count", 0)

        if explicit_metadata:
            metadata_sessions += 1
        if annotation:
            annotated_sessions += 1

        for field in PHASE3_CANONICAL_METADATA_FIELDS:
            value = explicit_metadata.get(field)
            if value in (None, "", [], {}):
                metadata_missing_counts[field] += 1
                continue
            if value not in (None, "", [], {}):
                explicit_metadata_field_counts[field] += 1
            source = provenance.get(field) or "unknown"
            metadata_provenance_counts[str(source)] += 1

        runtime = explicit_metadata.get("runtime") or ""
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

        if (
            explicit_metadata.get("runtime") not in (None, "", [], {})
            and explicit_metadata.get("task_type") not in (None, "", [], {})
            and explicit_metadata.get("task_source") not in (None, "", [], {})
            and explicit_metadata.get("success") not in (None, "", [], {})
        ):
            research_grade_sessions += 1

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

    return {
        "session_count": session_count,
        "event_count": event_count,
        "metadata_sessions": metadata_sessions,
        "annotated_sessions": annotated_sessions,
        "explicit_runtime_sessions": sum(explicit_runtime_counts.values()),
        "heuristic_runtime_sessions": sum(heuristic_runtime_counts.values()),
        "task_type_sessions": sum(1 for record in records if (record.get("metadata", {}).get("task_type") or load_annotation(record["session_id"]).get("task_type"))),
        "source_sessions": sum(1 for record in records if (record.get("metadata", {}).get("task_source") or load_annotation(record["session_id"]).get("source"))),
        "research_grade_sessions": research_grade_sessions,
        "metadata_provenance_counts": dict(metadata_provenance_counts),
        "metadata_missing_counts": dict(metadata_missing_counts),
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
        "explicit_metadata_field_counts": dict(explicit_metadata_field_counts),
    }


def _build_corpus_milestones(facts: dict[str, Any]) -> dict[str, dict[str, int | str]]:
    """Build milestone counters from a corpus-facts payload."""
    return {
        "scale_1000": {
            "label": "Corpus scale",
            "target": 1000,
            "current": facts["session_count"],
            "remaining": max(1000 - facts["session_count"], 0),
        },
        "research_100": {
            "label": "Research-ready labeled corpus",
            "target": 100,
            "current": facts["metadata_sessions"],
            "remaining": max(100 - facts["metadata_sessions"], 0),
        },
        "runtime_4": {
            "label": "Explicit runtime fingerprint set",
            "target": 4,
            "current": len(facts["runtime_counts"]),
            "remaining": max(4 - len(facts["runtime_counts"]), 0),
        },
        "task_4": {
            "label": "Task taxonomy breadth",
            "target": 4,
            "current": len(facts["task_type_counts"]),
            "remaining": max(4 - len(facts["task_type_counts"]), 0),
        },
        "fan_in_10": {
            "label": "Fan-in exemplars",
            "target": 10,
            "current": facts["fan_in_sessions"],
            "remaining": max(10 - facts["fan_in_sessions"], 0),
        },
        "branch_collapse_10": {
            "label": "Branch-collapse exemplars",
            "target": 10,
            "current": facts["branch_collapse_sessions"],
            "remaining": max(10 - facts["branch_collapse_sessions"], 0),
        },
        "multi_root_10": {
            "label": "Multi-root exemplars",
            "target": 10,
            "current": facts["multi_root_sessions"],
            "remaining": max(10 - facts["multi_root_sessions"], 0),
        },
    }


def build_benchmark_manifest(records: list[dict[str, Any]], *, label: str = "task_type") -> dict[str, Any]:
    """Build a benchmark manifest grouped by a metadata label."""
    groups = group_labeled_sessions(records, label=label)
    group_items: list[dict[str, Any]] = []
    runtime_counts: Counter[str] = Counter()
    topology_counts: Counter[str] = Counter()

    records_by_id = {record["session_id"]: record for record in records}
    for record in records:
        metadata = record.get("metadata", {})
        runtime = metadata.get("runtime") or ""
        topology = record.get("topology") or ""
        if runtime:
            runtime_counts[str(runtime)] += 1
        if topology:
            topology_counts[str(topology)] += 1

    for group_label, session_ids in sorted(groups.items(), key=lambda item: (item[0] != "unknown", item[0])):
        canonical_session_ids = sorted(session_ids)
        group_records = [records_by_id[sid] for sid in canonical_session_ids if sid in records_by_id]
        group_runtime_counts: Counter[str] = Counter()
        group_topology_counts: Counter[str] = Counter()
        for record in group_records:
            metadata = record.get("metadata", {})
            runtime = metadata.get("runtime") or ""
            topology = record.get("topology") or ""
            if runtime:
                group_runtime_counts[str(runtime)] += 1
            if topology:
                group_topology_counts[str(topology)] += 1

        group_items.append({
            "label": group_label,
            "session_count": len(canonical_session_ids),
            "session_ids": canonical_session_ids,
            "runtime_counts": dict(group_runtime_counts),
            "topology_counts": dict(group_topology_counts),
        })

    payload = {
        "generated_at": datetime.now().isoformat(),
        "label": label,
        "session_count": len(records),
        "group_count": len(group_items),
        "runtime_counts": dict(runtime_counts),
        "topology_counts": dict(topology_counts),
        "groups": group_items,
    }
    payload["benchmark_hash"] = _benchmark_hash(payload)
    return payload


def _benchmark_hash(manifest: dict[str, Any]) -> str:
    stable_payload = {
        "label": manifest.get("label", "task_type"),
        "session_count": manifest.get("session_count", 0),
        "group_count": manifest.get("group_count", 0),
        "runtime_counts": manifest.get("runtime_counts", {}),
        "topology_counts": manifest.get("topology_counts", {}),
        "groups": manifest.get("groups", []),
    }
    return hashlib.sha256(
        json.dumps(stable_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def benchmark_corpus(
    store: JSONStore,
    *,
    output_dir: str | Path | None = None,
    name: str | None = None,
    label: str = "task_type",
    session_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Create a benchmark manifest from the current corpus."""
    root = Path(output_dir) if output_dir else Path(CORPUS_DIR)
    benchmark_name = _safe_name(name or f"benchmark-{_default_snapshot_name()}")
    benchmark_dir = root / "benchmarks" / benchmark_name
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    selected = session_ids or store.list_sessions()
    records = [build_session_record(store, sid) for sid in selected]
    manifest = build_benchmark_manifest(records, label=label)
    manifest["name"] = benchmark_name
    manifest["source"] = "corpus"
    manifest["session_ids"] = sorted(record["session_id"] for record in records)

    (benchmark_dir / "benchmark.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return {
        "benchmark_dir": str(benchmark_dir),
        "session_count": len(records),
        "manifest": manifest,
    }


def verify_benchmark_manifest(benchmark_dir: str | Path) -> dict[str, Any]:
    """Verify a benchmark manifest and its internal consistency."""
    benchmark_path = Path(benchmark_dir)
    manifest_path = benchmark_path / "benchmark.json"
    result: dict[str, Any] = {
        "benchmark_dir": str(benchmark_path),
        "manifest_exists": manifest_path.exists(),
        "manifest_hash_match": False,
        "session_count": 0,
        "group_count": 0,
        "verified_session_count": 0,
        "issues": [],
        "ok": False,
    }

    if not manifest_path.exists():
        result["issues"].append("benchmark.json not found")
        return result

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result["issues"].append(f"manifest parse failed: {exc}")
        return result

    if not isinstance(manifest, dict):
        result["issues"].append("manifest root is not an object")
        return result

    groups = manifest.get("groups", [])
    if not isinstance(groups, list):
        result["issues"].append("manifest groups field is not a list")
        return result

    result["session_count"] = int(manifest.get("session_count", 0) or 0)
    result["group_count"] = len(groups)
    result["manifest_hash_match"] = manifest.get("benchmark_hash") == _benchmark_hash(manifest)

    flattened_ids: list[str] = []
    seen_ids: set[str] = set()
    verified = 0

    for group in groups:
        if not isinstance(group, dict):
            result["issues"].append("manifest contains a non-dict group")
            continue

        label = group.get("label")
        if not isinstance(label, str) or not label:
            result["issues"].append("group missing label")

        session_ids = group.get("session_ids", [])
        if not isinstance(session_ids, list):
            result["issues"].append(f"group {label or '<unknown>'} session_ids field is not a list")
            continue

        group_session_count = group.get("session_count", 0)
        if group_session_count != len(session_ids):
            result["issues"].append(f"group session_count mismatch: {label or '<unknown>'}")

        for session_id in session_ids:
            if not isinstance(session_id, str) or not session_id:
                result["issues"].append(f"invalid session_id in group {label or '<unknown>'}")
                continue
            flattened_ids.append(session_id)
            if session_id in seen_ids:
                result["issues"].append(f"duplicate session_id in benchmark: {session_id}")
            else:
                seen_ids.add(session_id)
                verified += 1

    top_level_ids = manifest.get("session_ids", [])
    if not isinstance(top_level_ids, list):
        result["issues"].append("manifest session_ids field is not a list")
    elif sorted(top_level_ids) != sorted(flattened_ids):
        result["issues"].append("top-level session_ids do not match grouped session_ids")

    if result["session_count"] != len(flattened_ids):
        result["issues"].append("session_count does not match grouped session total")

    result["verified_session_count"] = verified
    result["ok"] = (
        not result["issues"]
        and result["manifest_hash_match"]
        and result["session_count"] == len(flattened_ids)
    )
    return result


def _distribution_distance(counts_a: dict[str, int], counts_b: dict[str, int]) -> float:
    keys = set(counts_a) | set(counts_b)
    total_a = sum(counts_a.values())
    total_b = sum(counts_b.values())
    if not keys:
        return 0.0
    if total_a == 0 or total_b == 0:
        return 0.0 if total_a == total_b else 1.0

    delta = 0.0
    for key in keys:
        pa = counts_a.get(key, 0) / total_a
        pb = counts_b.get(key, 0) / total_b
        delta += abs(pa - pb)
    return round(delta / 2, 4)


def compare_benchmark_manifests(benchmark_dir_a: str | Path, benchmark_dir_b: str | Path) -> dict[str, Any]:
    """Compare two benchmark manifests structurally."""
    verify_a = verify_benchmark_manifest(benchmark_dir_a)
    verify_b = verify_benchmark_manifest(benchmark_dir_b)

    path_a = Path(benchmark_dir_a) / "benchmark.json"
    path_b = Path(benchmark_dir_b) / "benchmark.json"

    manifest_a = json.loads(path_a.read_text(encoding="utf-8")) if path_a.exists() else {}
    manifest_b = json.loads(path_b.read_text(encoding="utf-8")) if path_b.exists() else {}

    session_ids_a = set(manifest_a.get("session_ids", []) if isinstance(manifest_a, dict) else [])
    session_ids_b = set(manifest_b.get("session_ids", []) if isinstance(manifest_b, dict) else [])

    runtime_counts_a = manifest_a.get("runtime_counts", {}) if isinstance(manifest_a, dict) else {}
    runtime_counts_b = manifest_b.get("runtime_counts", {}) if isinstance(manifest_b, dict) else {}
    topology_counts_a = manifest_a.get("topology_counts", {}) if isinstance(manifest_a, dict) else {}
    topology_counts_b = manifest_b.get("topology_counts", {}) if isinstance(manifest_b, dict) else {}
    groups_a = manifest_a.get("groups", []) if isinstance(manifest_a, dict) else []
    groups_b = manifest_b.get("groups", []) if isinstance(manifest_b, dict) else []

    labels_a = {group.get("label") for group in groups_a if isinstance(group, dict) and group.get("label")}
    labels_b = {group.get("label") for group in groups_b if isinstance(group, dict) and group.get("label")}

    return {
        "benchmark_a": str(Path(benchmark_dir_a)),
        "benchmark_b": str(Path(benchmark_dir_b)),
        "session_count_a": int(manifest_a.get("session_count", 0) or 0) if isinstance(manifest_a, dict) else 0,
        "session_count_b": int(manifest_b.get("session_count", 0) or 0) if isinstance(manifest_b, dict) else 0,
        "group_count_a": int(manifest_a.get("group_count", 0) or 0) if isinstance(manifest_a, dict) else 0,
        "group_count_b": int(manifest_b.get("group_count", 0) or 0) if isinstance(manifest_b, dict) else 0,
        "benchmark_hash_a": manifest_a.get("benchmark_hash", "") if isinstance(manifest_a, dict) else "",
        "benchmark_hash_b": manifest_b.get("benchmark_hash", "") if isinstance(manifest_b, dict) else "",
        "hash_match": isinstance(manifest_a, dict)
        and isinstance(manifest_b, dict)
        and manifest_a.get("benchmark_hash") == manifest_b.get("benchmark_hash"),
        "shared_session_ids": sorted(session_ids_a & session_ids_b),
        "only_in_a": sorted(session_ids_a - session_ids_b),
        "only_in_b": sorted(session_ids_b - session_ids_a),
        "runtime_distance": _distribution_distance(runtime_counts_a, runtime_counts_b),
        "topology_distance": _distribution_distance(topology_counts_a, topology_counts_b),
        "shared_labels": sorted(labels_a & labels_b),
        "only_labels_in_a": sorted(labels_a - labels_b),
        "only_labels_in_b": sorted(labels_b - labels_a),
        "verify_a": verify_a,
        "verify_b": verify_b,
    }


def infer_runtime_label(events) -> str | None:
    """Infer the most likely runtime label from event attribution fields."""
    counts: Counter[str] = Counter()
    for ev in events:
        label = ev.agent or ev.provider
        if label:
            counts[str(label).strip().lower()] += 1
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def materialize_corpus_metadata(
    store: JSONStore,
    *,
    session_ids: list[str] | None = None,
    infer_runtime: bool = True,
) -> dict[str, Any]:
    """Materialize canonical metadata sidecars from annotations and runtime hints."""
    selected = session_ids or store.list_sessions()
    updated = 0
    runtime_inferred = 0
    materialized_from_annotation = 0
    provenance_written = 0
    changed_sessions: list[str] = []
    annotation_fields = {
        "model",
        "task_type",
        "task_source",
        "repo_language",
        "repo_size",
        "success",
        "duration",
        "human_intervention",
    }

    for sid in selected:
        events = store.load(sid)
        combined = load_metadata(sid).to_dict()
        explicit = load_metadata(sid, include_annotation=False).to_dict()
        annotation = load_annotation(sid)
        provenance: dict[str, str] = {}
        provenance_changed = False

        if infer_runtime and not combined.get("runtime"):
            runtime = infer_runtime_label(events)
            if runtime:
                combined["runtime"] = runtime
                runtime_inferred += 1
                provenance["runtime"] = "inferred_from_runtime_adapter"
                provenance_changed = True

        for field in PHASE3_CANONICAL_METADATA_FIELDS:
            value = combined.get(field)
            if value in (None, "", [], {}):
                continue
            if field == "runtime" and provenance.get(field) != "inferred_from_runtime_adapter":
                if explicit.get(field) not in (None, "", [], {}):
                    provenance[field] = "explicit_sidecar"
                elif annotation.get(field) not in (None, "", [], {}):
                    provenance[field] = "materialized"
                else:
                    provenance[field] = "unknown"
                provenance_changed = True
            elif field != "runtime":
                if explicit.get(field) not in (None, "", [], {}):
                    provenance[field] = "explicit_sidecar"
                elif annotation.get(field) not in (None, "", [], {}):
                    provenance[field] = "materialized"
                else:
                    provenance[field] = "unknown"
                provenance_changed = True

        if combined != explicit:
            merge_metadata(sid, combined)
            updated += 1
            changed_sessions.append(sid)
            if any(combined.get(field) is not None for field in annotation_fields if combined.get(field) != explicit.get(field)):
                materialized_from_annotation += 1
                for field in annotation_fields:
                    if combined.get(field) not in (None, "", [], {}) and combined.get(field) != explicit.get(field):
                        provenance[field] = "materialized"
                        provenance_changed = True

        if provenance_changed:
            save_metadata_provenance(sid, provenance)
            provenance_written += 1

    return {
        "updated_count": updated,
        "runtime_inferred_count": runtime_inferred,
        "annotation_materialized_count": materialized_from_annotation,
        "provenance_written_count": provenance_written,
        "changed_sessions": changed_sessions,
        "selected_count": len(selected),
    }


def assess_phase3_readiness(
    store: JSONStore,
    *,
    requirements: Phase3ReadinessRequirements | None = None,
) -> dict[str, Any]:
    """Assess whether the corpus is ready for phase-3 runtime intelligence work."""
    req = requirements or Phase3ReadinessRequirements()
    facts = build_corpus_facts(store)
    summary = {**facts, "milestones": _build_corpus_milestones(facts)}
    sessions = store.list_sessions()

    explicit_metadata_field_counts: Counter[str] = Counter()
    for sid in sessions:
        metadata = load_metadata(sid, include_annotation=False).to_dict()
        for field in PHASE3_CANONICAL_METADATA_FIELDS:
            if metadata.get(field) not in (None, "", [], {}):
                explicit_metadata_field_counts[field] += 1

    criteria = [
        {
            "key": "session_scale",
            "label": "Corpus scale",
            "current": summary["session_count"],
            "target": req.min_sessions,
        },
        {
            "key": "metadata_sessions",
            "label": "Explicit metadata sidecars",
            "current": summary["metadata_sessions"],
            "target": req.min_metadata_sessions,
        },
        {
            "key": "explicit_runtime_sessions",
            "label": "Explicit runtime labels",
            "current": summary["explicit_runtime_sessions"],
            "target": req.min_explicit_runtime_sessions,
        },
        {
            "key": "task_type_sessions",
            "label": "Task labels",
            "current": summary["task_type_sessions"],
            "target": req.min_task_type_sessions,
        },
        {
            "key": "runtime_breadth",
            "label": "Runtime family breadth",
            "current": len(summary["runtime_counts"]),
            "target": req.min_runtime_breadth,
        },
        {
            "key": "task_breadth",
            "label": "Task taxonomy breadth",
            "current": len(summary["task_type_counts"]),
            "target": req.min_task_breadth,
        },
        {
            "key": "fan_in_sessions",
            "label": "Fan-in exemplars",
            "current": summary["fan_in_sessions"],
            "target": req.min_fan_in_sessions,
        },
        {
            "key": "branch_collapse_sessions",
            "label": "Branch-collapse exemplars",
            "current": summary["branch_collapse_sessions"],
            "target": req.min_branch_collapse_sessions,
        },
        {
            "key": "multi_root_sessions",
            "label": "Multi-root exemplars",
            "current": summary["multi_root_sessions"],
            "target": req.min_multi_root_sessions,
        },
        {
            "key": "long_sessions",
            "label": "Long sessions (>=100 events)",
            "current": summary["long_sessions_100"],
            "target": req.min_long_sessions,
        },
        {
            "key": "retry_heavy_sessions",
            "label": "Retry-heavy sessions",
            "current": summary["retry_heavy_sessions"],
            "target": req.min_retry_heavy_sessions,
        },
    ]

    for item in criteria:
        item["remaining"] = max(item["target"] - item["current"], 0)
        item["passed"] = item["current"] >= item["target"]

    blockers = [item for item in criteria if not item["passed"]]
    ready = not blockers

    return {
        "ready": ready,
        "session_count": summary["session_count"],
        "metadata_sessions": summary["metadata_sessions"],
        "explicit_runtime_sessions": summary["explicit_runtime_sessions"],
        "task_type_sessions": summary["task_type_sessions"],
        "research_grade_sessions": facts["research_grade_sessions"],
        "runtime_breadth": len(summary["runtime_counts"]),
        "task_breadth": len(summary["task_type_counts"]),
        "criteria": criteria,
        "blockers": blockers,
        "canonical_metadata_fields": list(PHASE3_CANONICAL_METADATA_FIELDS),
        "taxonomy_protocol": PHASE3_TAXONOMY_PROTOCOL,
        "explicit_metadata_field_counts": dict(explicit_metadata_field_counts),
        "summary": summary,
    }


def _taxonomy_tags(stats: dict[str, Any], events: list[Any]) -> list[str]:
    """Derive structural taxonomy tags from session-local signals."""
    tags: list[str] = []
    topology = classify_topology(stats)
    retry = detect_retry_density(events)
    fan_in = detect_fan_in_patterns(events)
    branch_collapse = detect_branch_collapse(events)
    frontier = compute_frontier_width(events)

    if topology == "dominant_chain" and stats.get("max_depth", 0) >= 4 and stats.get("fan_out_avg", 0.0) < 1.5:
        tags.append("deep_linear")
    if topology == "fan_out_heavy" or stats.get("fan_out_max", 0) >= 4 or frontier["max_width"] >= 4:
        tags.append("branchy")
    if topology == "collapsed_repair" or branch_collapse:
        tags.append("branch_collapse")
    if fan_in:
        tags.append("fan_in")
    if retry["retry_density"] >= 0.2:
        tags.append("retry_heavy")
    if topology == "multi_root_exploration" or stats.get("root_count", 0) >= 5:
        tags.append("multi_root_exploration")
    if stats.get("event_count", 0) >= 100:
        tags.append("long_session")
    if not tags:
        tags.append(topology)
    return tags


def _primary_taxonomy(stats: dict[str, Any], tags: list[str]) -> str:
    """Pick the most informative single taxonomy label for grouping."""
    priority = (
        "branch_collapse",
        "fan_in",
        "retry_heavy",
        "multi_root_exploration",
        "branchy",
        "deep_linear",
        "long_session",
    )
    for label in priority:
        if label in tags:
            return label
    return classify_topology(stats)


def build_topology_taxonomy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a taxonomy manifest from precomputed topology rows."""
    groups: dict[str, list[dict[str, Any]]] = {}
    tag_counts: Counter[str] = Counter()
    runtime_counts: Counter[str] = Counter()
    topology_counts: Counter[str] = Counter()
    task_type_counts: Counter[str] = Counter()

    for row in rows:
        primary = row.get("primary_taxonomy") or "mixed"
        groups.setdefault(str(primary), []).append(row)
        for tag in row.get("tags", []):
            tag_counts[str(tag)] += 1
        runtime = row.get("runtime") or ""
        topology = row.get("topology") or ""
        task_type = row.get("task_type") or ""
        if runtime:
            runtime_counts[str(runtime)] += 1
        if topology:
            topology_counts[str(topology)] += 1
        if task_type:
            task_type_counts[str(task_type)] += 1

    group_items: list[dict[str, Any]] = []
    for label, group_rows in sorted(groups.items(), key=lambda item: item[0]):
        canonical_rows = sorted(group_rows, key=lambda item: item["session_id"])
        group_runtime_counts: Counter[str] = Counter()
        group_topology_counts: Counter[str] = Counter()
        group_task_counts: Counter[str] = Counter()
        for row in canonical_rows:
            runtime = row.get("runtime") or ""
            topology = row.get("topology") or ""
            task_type = row.get("task_type") or ""
            if runtime:
                group_runtime_counts[str(runtime)] += 1
            if topology:
                group_topology_counts[str(topology)] += 1
            if task_type:
                group_task_counts[str(task_type)] += 1

        group_items.append({
            "label": label,
            "session_count": len(canonical_rows),
            "session_ids": [row["session_id"] for row in canonical_rows],
            "tag_counts": dict(Counter(tag for row in canonical_rows for tag in row.get("tags", []))),
            "runtime_counts": dict(group_runtime_counts),
            "topology_counts": dict(group_topology_counts),
            "task_type_counts": dict(group_task_counts),
        })

    payload = {
        "generated_at": datetime.now().isoformat(),
        "session_count": len(rows),
        "group_count": len(group_items),
        "runtime_counts": dict(runtime_counts),
        "topology_counts": dict(topology_counts),
        "task_type_counts": dict(task_type_counts),
        "tag_counts": dict(tag_counts),
        "groups": group_items,
        "sessions": rows,
    }
    stable_payload = {
        "session_count": payload["session_count"],
        "group_count": payload["group_count"],
        "runtime_counts": payload["runtime_counts"],
        "topology_counts": payload["topology_counts"],
        "task_type_counts": payload["task_type_counts"],
        "tag_counts": payload["tag_counts"],
        "groups": payload["groups"],
        "sessions": [
            {
                "session_id": row["session_id"],
                "primary_taxonomy": row.get("primary_taxonomy", ""),
                "tags": row.get("tags", []),
                "runtime": row.get("runtime", ""),
                "task_type": row.get("task_type", ""),
                "topology": row.get("topology", ""),
            }
            for row in sorted(rows, key=lambda item: item["session_id"])
        ],
    }
    payload["taxonomy_hash"] = hashlib.sha256(
        json.dumps(stable_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return payload


def taxonomy_corpus(
    store: JSONStore,
    *,
    output_dir: str | Path | None = None,
    name: str | None = None,
    session_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Create a structural taxonomy manifest from the current corpus."""
    root = Path(output_dir) if output_dir else Path(CORPUS_DIR)
    taxonomy_name = _safe_name(name or f"taxonomy-{_default_snapshot_name()}")
    taxonomy_dir = root / "taxonomy" / taxonomy_name
    taxonomy_dir.mkdir(parents=True, exist_ok=True)

    selected = session_ids or store.list_sessions()
    rows: list[dict[str, Any]] = []
    for sid in selected:
        source_path = store._path(sid)
        if not source_path.exists():
            continue
        record = build_session_record(store, sid)
        events = store.load(sid)
        tags = _taxonomy_tags(record.get("stats", {}), events)
        rows.append({
            "session_id": sid,
            "runtime": record.get("metadata", {}).get("runtime", "") or "",
            "task_type": record.get("metadata", {}).get("task_type", "") or "",
            "topology": record.get("topology", "") or "",
            "event_count": record.get("stats", {}).get("event_count", 0),
            "root_count": record.get("stats", {}).get("root_count", 0),
            "max_depth": record.get("stats", {}).get("max_depth", 0),
            "fan_out_avg": record.get("stats", {}).get("fan_out_avg", 0.0),
            "fan_out_max": record.get("stats", {}).get("fan_out_max", 0),
            "primary_taxonomy": _primary_taxonomy(record.get("stats", {}), tags),
            "tags": tags,
        })

    manifest = build_topology_taxonomy(rows)
    manifest["name"] = taxonomy_name
    manifest["source"] = "corpus"
    manifest["session_ids"] = sorted(row["session_id"] for row in rows)
    (taxonomy_dir / "taxonomy.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return {
        "taxonomy_dir": str(taxonomy_dir),
        "session_count": len(rows),
        "manifest": manifest,
    }


def verify_snapshot(snapshot_dir: str | Path) -> dict[str, Any]:
    """Verify a corpus snapshot manifest and copied session files."""
    snapshot_path = Path(snapshot_dir)
    manifest_path = snapshot_path / "manifest.json"
    result: dict[str, Any] = {
        "snapshot_dir": str(snapshot_path),
        "manifest_exists": manifest_path.exists(),
        "manifest_hash_match": False,
        "session_count": 0,
        "verified_count": 0,
        "issues": [],
        "ok": False,
    }

    if not manifest_path.exists():
        result["issues"].append("manifest.json not found")
        return result

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result["issues"].append(f"manifest parse failed: {exc}")
        return result

    sessions = manifest.get("sessions", [])
    if not isinstance(sessions, list):
        result["issues"].append("manifest sessions field is not a list")
        return result

    result["session_count"] = len(sessions)
    result["manifest_hash_match"] = manifest.get("snapshot_hash") == _snapshot_digest(sessions)

    verified = 0
    for record in sessions:
        if not isinstance(record, dict):
            result["issues"].append("manifest contains a non-dict session record")
            continue

        sid = record.get("session_id")
        if not sid:
            result["issues"].append("manifest record missing session_id")
            continue

        source_name = f"{sid}.jsonl"
        session_path = snapshot_path / "sessions" / source_name
        metadata_path = snapshot_path / "metadata" / f"{sid}.json"

        if not session_path.exists():
            result["issues"].append(f"missing session file: {source_name}")
            continue

        expected_hash = record.get("session_hash", "")
        expected_size = record.get("session_bytes", 0)
        actual_hash = _session_digest(session_path)
        actual_size = session_path.stat().st_size
        if expected_hash and expected_hash != actual_hash:
            result["issues"].append(f"session hash mismatch: {sid}")
        if expected_size != actual_size:
            result["issues"].append(f"session size mismatch: {sid}")

        if not metadata_path.exists():
            result["issues"].append(f"missing metadata file: {sid}.json")
            continue

        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            result["issues"].append(f"metadata parse failed for {sid}: {exc}")
            continue

        if metadata != record.get("metadata", {}):
            result["issues"].append(f"metadata mismatch: {sid}")
            continue

        verified += 1

    result["verified_count"] = verified
    result["ok"] = (
        not result["issues"]
        and result["manifest_hash_match"]
        and verified == len(sessions)
    )
    return result


def group_labeled_sessions(records: list[dict[str, Any]], label: str = "task_type") -> dict[str, list[str]]:
    """Group session IDs by a metadata label."""
    groups: dict[str, list[str]] = {}
    for record in records:
        value = record.get("metadata", {}).get(label) or "unknown"
        groups.setdefault(str(value), []).append(record["session_id"])
    return groups


def summarize_corpus_health(store: JSONStore) -> dict[str, Any]:
    """Summarize corpus size, coverage, and structure gaps against roadmap targets."""
    facts = build_corpus_facts(store)
    return {**facts, "milestones": _build_corpus_milestones(facts)}
