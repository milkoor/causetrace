"""Session metadata annotation — lightweight sidecar system.

Stores task-type labels and other context alongside each session.
Annotations live in ~/.causetrace/meta/<session_id>.json.
Manual labeling only — no automated inference.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


ANNOTATION_DIR = os.path.expanduser("~/.causetrace/meta")

# Same safe session_id pattern as core.py
_VALID_ID_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")


def _validate_session_id(session_id: str) -> None:
    if not _VALID_ID_RE.match(session_id):
        raise ValueError(
            f"Invalid session_id: {session_id!r}. "
            "Only alphanumeric, underscore, hyphen, and dot allowed."
        )


TASK_TYPES = {
    "bug_fix": "Fixing a specific bug or error",
    "feature_add": "Adding new functionality",
    "refactor": "Restructuring existing code without changing behavior",
    "exploration": "Reading/searching code to understand it",
    "debug_test": "Debugging test failures",
    "doc_gen": "Generating documentation",
    "migration": "Porting code between frameworks, versions, or languages",
    "project_init": "Starting a new project or module",
    "review": "Code review or audit",
    "unknown": "Cannot determine task type",
}

SOURCES = {
    "real_work": "Actual development work by the user",
    "demo": "Demo/example session for testing",
    "proxy": "Session routed through a proxy (e.g., DeepSeek)",
    "unknown": "Unknown source",
}


def _meta_path(session_id: str) -> Path:
    _validate_session_id(session_id)
    return Path(ANNOTATION_DIR) / f"{session_id}.json"


def load_annotation(session_id: str) -> dict:
    """Load annotation for a session. Returns empty dict if none exists."""
    path = _meta_path(session_id)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_annotation(session_id: str, metadata: dict) -> dict:
    """Save annotation for a session, merging with existing data."""
    existing = load_annotation(session_id)
    existing.update(metadata)
    existing["session_id"] = session_id
    existing["annotated_at"] = datetime.now().isoformat()
    Path(ANNOTATION_DIR).mkdir(parents=True, exist_ok=True)
    _meta_path(session_id).write_text(json.dumps(existing, indent=2))
    return existing


def list_annotated() -> list[dict]:
    """List all annotated sessions with their metadata."""
    path = Path(ANNOTATION_DIR)
    if not path.exists():
        return []
    results = []
    for f in sorted(path.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            results.append(data)
        except (json.JSONDecodeError, OSError):
            pass
    return results


def list_unannotated(session_ids: list[str]) -> list[str]:
    """Return session IDs that have no annotation yet."""
    annotated = {a.get("session_id") for a in list_annotated()}
    return [sid for sid in session_ids if sid not in annotated]