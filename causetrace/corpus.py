"""Corpus management for reproducible trace analysis datasets."""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from .analysis import classify_topology, compute_stats
from .core import JSONStore
from .metadata import load_metadata


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
