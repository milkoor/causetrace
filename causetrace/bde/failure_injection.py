"""Failure-injection scenario descriptors.

The descriptors here define experimental intent only. They must not mutate
runtime execution or agent configuration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FailureInjection:
    """Metadata-only failure or near-failure design descriptor."""

    injection_id: str
    failure_mode: str
    target_task_type: str | None = None
    expected_observable_signal: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
