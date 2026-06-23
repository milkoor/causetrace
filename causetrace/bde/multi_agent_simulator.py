"""Multi-agent simulation descriptors.

This module does not simulate or launch agents. It only models planned runtime
roles so traces can later be grouped by experimental design.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MultiAgentSimulation:
    """Metadata-only descriptor for a planned multi-agent scenario."""

    simulation_id: str
    agent_roles: tuple[str, ...]
    coordination_pattern: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
