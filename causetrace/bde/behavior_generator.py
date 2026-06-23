"""Interfaces for controlled behavior scenario generation.

This module is intentionally passive. It creates scenario descriptors that can
be logged as metadata, but it does not execute prompts or call agent runtimes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class PromptVariant:
    """A named prompt/task variant in an experiment design."""

    variant_id: str
    prompt: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BehaviorScenario:
    """Metadata-only description of a generated behavior scenario."""

    scenario_id: str
    task: str
    behavior_distribution_tag: str | None = None
    prompt_variants: tuple[PromptVariant, ...] = ()
    experiment_id: str | None = None
    control_group_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BehaviorGenerator(Protocol):
    """Protocol for BDE scenario generators."""

    def generate(self) -> list[BehaviorScenario]:
        """Return scenario descriptors without executing them."""
