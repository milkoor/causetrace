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
    "classified_from_explicit_metadata",
    "unknown",
}

_DATA_ORIGINS = {
    "native",
    "controlled_benchmark",
    "external_trajectory",
    "unknown",
}

INTERVENTION_LANES = {
    "direct_prompt_native",
    "routed_prompt_intervention",
    "superpowers_workflow_intervention",
    "controlled_prompt_morphology",
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
    "intervention_lane",
    "causetrace_tags",
    "intervention_evidence_source",
    "intervention_evidence_level",
    "behavior_distribution_tag",
    "bde_generated",
    "experiment_id",
    "control_group_id",
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
    intervention_lane: str | None = None
    causetrace_tags: list[str] | None = None
    intervention_evidence_source: str | None = None
    intervention_evidence_level: str | None = None
    behavior_distribution_tag: str | None = None
    bde_generated: bool | None = None
    experiment_id: str | None = None
    control_group_id: str | None = None

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
    if meta.intervention_lane is not None and meta.intervention_lane not in INTERVENTION_LANES:
        raise ValueError(f"Unknown intervention_lane: {meta.intervention_lane}")

    meta.success = _coerce_bool(meta.success, "success")
    meta.human_intervention = _coerce_bool(meta.human_intervention, "human_intervention")
    meta.bde_generated = _coerce_bool(meta.bde_generated, "bde_generated")
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


_TAGS_DATA_DIR = os.path.expanduser("~/.causetrace/data")

_TAG_BLOCK_RE = re.compile(r"causetrace_tags:\s*\n((?:\s+-\s+\S+\n?)+)", re.IGNORECASE)
_LANE_RE = re.compile(r"intervention_lane:\s*(\S+)", re.IGNORECASE)
_LEVEL_RE = re.compile(r"evidence_level:\s*(\S+)", re.IGNORECASE)


def _extract_tags_from_text(text: str) -> dict[str, Any]:
    """Extract causetrace_tags structured metadata from a text blob."""
    tags: list[str] = []
    m = _TAG_BLOCK_RE.search(text)
    if m:
        for line in m.group(1).strip().split("\n"):
            stripped = line.strip()
            if stripped.startswith("- "):
                tags.append(stripped[2:].strip())
    lane: str | None = None
    m = _LANE_RE.search(text)
    if m:
        lane = m.group(1)
    level: str | None = None
    m = _LEVEL_RE.search(text)
    if m:
        level = m.group(1)
    return {"tags": tags, "intervention_lane": lane, "evidence_level": level}


def detect_causetrace_tags(session_id: str) -> dict[str, Any]:
    """Scan a session's events for causetrace_tags YAML block patterns.

    Searches tool_input and tool_output of each event for causetrace_tags
    blocks and extracts tags, intervention_lane, and evidence_level.

    Returns:
        dict with keys: found (bool), tags (list[str]),
        intervention_lane (str|None), evidence_level (str|None)
    """
    result: dict[str, Any] = {
        "found": False,
        "tags": [],
        "intervention_lane": None,
        "evidence_level": None,
    }
    path = Path(_TAGS_DATA_DIR) / f"{session_id}.jsonl"
    if not path.exists():
        return result

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            for field_name in ("tool_input", "tool_output"):
                value = event.get(field_name)
                if value is None:
                    continue
                text = json.dumps(value) if not isinstance(value, str) else value
                text = text.replace("\\n", "\n")  # unescape JSON-embedded newlines
                if "causetrace_tags" not in text:
                    continue
                extracted = _extract_tags_from_text(text)
                if not any(extracted.values()):
                    continue
                result["found"] = True
                if extracted.get("tags"):
                    result["tags"] = extracted["tags"]
                if extracted.get("intervention_lane"):
                    result["intervention_lane"] = extracted["intervention_lane"]
                if extracted.get("evidence_level"):
                    result["evidence_level"] = extracted["evidence_level"]
                return result

    return result
