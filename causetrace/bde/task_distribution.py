"""Task distribution descriptors for behavior design experiments."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TaskDistribution:
    """Metadata-only task distribution for a planned experiment."""

    distribution_id: str
    task_types: tuple[str, ...]
    weights: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
