"""Session-level runtime metadata sidecars.

Metadata is intentionally separate from the event schema. It describes the
session context needed for corpus comparison without changing trace events.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .annotation import TASK_TYPES, SOURCES, load_annotation


METADATA_DIR = os.path.expanduser("~/.causetrace/metadata")
METADATA_PROVENANCE_SUFFIX = ".provenance.json"

_PROVENANCE_VALUES = {
    "explicit_sidecar",
    "annotation",
    "materialized",
    "inferred_from_runtime_adapter",
    "unknown",
}

_DATA_ORIGINS = {
    "native",
    "controlled_benchmark",
    "external_trajectory",
    "unknown",
}

_VALID_ID_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")
_FIELDS = {
    "data_origin",
    "runtime",
    "model",
    "task_type",
    "task_source",
    "repo_language",
    "repo_size",
    "success",
    "duration",
    "human_intervention",
}


@dataclass
class SessionMetadata:
    """Comparable runtime context for a trace session."""

    data_origin: str | None = None
    runtime: str | None = None
    model: str | None = None
    task_type: str | None = None
    task_source: str | None = None
    repo_language: str | None = None
    repo_size: str | int | None = None
    success: bool | None = None
    duration: float | None = None
    human_intervention: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionMetadata":
        values = {k: data.get(k) for k in _FIELDS if k in data}
        return cls(**values)

    def to_dict(self, *, drop_none: bool = True) -> dict[str, Any]:
        data = asdict(self)
        if drop_none:
            return {k: v for k, v in data.items() if v is not None}
        return data


def _validate_session_id(session_id: str) -> None:
    if not _VALID_ID_RE.match(session_id):
        raise ValueError(
            f"Invalid session_id: {session_id!r}. "
            "Only alphanumeric, underscore, hyphen, and dot allowed."
        )


def _metadata_path(session_id: str) -> Path:
    _validate_session_id(session_id)
    return Path(METADATA_DIR) / f"{session_id}.json"


def _provenance_path(session_id: str) -> Path:
    _validate_session_id(session_id)
    return Path(METADATA_DIR) / f"{session_id}{METADATA_PROVENANCE_SUFFIX}"


def _coerce_bool(value: Any, field: str) -> bool | None:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {"1", "true", "yes", "y"}:
            return True
        if lowered in {"0", "false", "no", "n"}:
            return False
    raise ValueError(f"{field} must be a boolean")


def _coerce_duration(value: Any) -> float | None:
    if value is None:
        return None
    try:
        duration = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("duration must be a number of seconds") from exc
    if duration < 0:
        raise ValueError("duration must be non-negative")
    return duration


def validate_metadata(metadata: SessionMetadata | dict[str, Any]) -> SessionMetadata:
    """Validate and normalize metadata fields."""
    meta = metadata if isinstance(metadata, SessionMetadata) else SessionMetadata.from_dict(metadata)

    if meta.data_origin is not None and meta.data_origin not in _DATA_ORIGINS:
        raise ValueError(f"Unknown data_origin: {meta.data_origin}")
    if meta.task_type is not None and meta.task_type not in TASK_TYPES:
        raise ValueError(f"Unknown task_type: {meta.task_type}")
    if meta.task_source is not None and meta.task_source not in SOURCES:
        raise ValueError(f"Unknown task_source: {meta.task_source}")

    meta.success = _coerce_bool(meta.success, "success")
    meta.human_intervention = _coerce_bool(meta.human_intervention, "human_intervention")
    meta.duration = _coerce_duration(meta.duration)
    return meta


def _load_sidecar(session_id: str) -> dict[str, Any]:
    path = _metadata_path(session_id)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _annotation_metadata(session_id: str) -> dict[str, Any]:
    annotation = load_annotation(session_id)
    mapped: dict[str, Any] = {}
    for key in ("data_origin", "runtime", "model", "task_type", "success", "duration", "human_intervention"):
        if key in annotation:
            mapped[key] = annotation[key]
    if "task_source" in annotation:
        mapped["task_source"] = annotation["task_source"]
    elif "source" in annotation:
        mapped["task_source"] = annotation["source"]
    if "repo_language" in annotation:
        mapped["repo_language"] = annotation["repo_language"]
    if "repo_size" in annotation:
        mapped["repo_size"] = annotation["repo_size"]
    return mapped


def _normalize_provenance_value(value: Any) -> str:
    if value is None:
        return "unknown"
    normalized = str(value).strip().lower()
    if normalized in _PROVENANCE_VALUES:
        return normalized
    return "unknown"


def _load_provenance_file(session_id: str) -> dict[str, str]:
    path = _provenance_path(session_id)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        str(key): _normalize_provenance_value(value)
        for key, value in data.items()
        if str(key) in _FIELDS
    }


def load_metadata_provenance(session_id: str) -> dict[str, str]:
    """Load per-field provenance for a session's metadata."""
    provenance = _load_provenance_file(session_id)
    if provenance:
        return provenance

    explicit = _load_sidecar(session_id)
    annotation = _annotation_metadata(session_id)
    derived: dict[str, str] = {}
    for field in _FIELDS:
        if field in explicit:
            derived[field] = "explicit_sidecar"
        elif field in annotation:
            derived[field] = "annotation"
    return derived


def infer_metadata_provenance(session_id: str) -> dict[str, str]:
    """Infer metadata provenance from persisted sidecars and annotations."""
    return load_metadata_provenance(session_id)


def save_metadata_provenance(session_id: str, provenance: dict[str, Any]) -> dict[str, str]:
    """Persist metadata provenance sidecar."""
    normalized = {
        str(field): _normalize_provenance_value(source)
        for field, source in provenance.items()
        if str(field) in _FIELDS
    }
    Path(METADATA_DIR).mkdir(parents=True, exist_ok=True)
    path = _provenance_path(session_id)
    if normalized:
        path.write_text(json.dumps(normalized, indent=2, sort_keys=True))
    elif path.exists():
        path.unlink()
    return normalized


def merge_metadata_provenance(session_id: str, updates: dict[str, Any]) -> dict[str, str]:
    """Merge provenance updates into a session's provenance sidecar."""
    current = load_metadata_provenance(session_id)
    current.update(
        {
            str(field): _normalize_provenance_value(source)
            for field, source in updates.items()
            if str(field) in _FIELDS
        }
    )
    return save_metadata_provenance(session_id, current)


def load_metadata(session_id: str, *, include_annotation: bool = True) -> SessionMetadata:
    """Load session metadata, optionally merged with legacy annotations."""
    data: dict[str, Any] = {}
    if include_annotation:
        data.update(_annotation_metadata(session_id))
    data.update({k: v for k, v in _load_sidecar(session_id).items() if k in _FIELDS})
    return validate_metadata(data)


def save_metadata(session_id: str, metadata: SessionMetadata | dict[str, Any]) -> SessionMetadata:
    """Save a metadata sidecar, replacing stored comparable fields."""
    meta = validate_metadata(metadata)
    data = meta.to_dict()
    data["session_id"] = session_id
    data["updated_at"] = datetime.now().isoformat()
    Path(METADATA_DIR).mkdir(parents=True, exist_ok=True)
    _metadata_path(session_id).write_text(json.dumps(data, indent=2, sort_keys=True))
    return meta


def merge_metadata(session_id: str, updates: dict[str, Any]) -> SessionMetadata:
    """Merge updates into metadata, preserving existing sidecar and annotations."""
    current = load_metadata(session_id).to_dict()
    current.update({k: v for k, v in updates.items() if k in _FIELDS and v is not None})
    meta = validate_metadata(current)
    save_metadata(session_id, meta)
    return meta
