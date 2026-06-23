"""Comparability scoring for CRDD subsets."""
from __future__ import annotations

from collections import Counter
from math import log
from typing import Any

from .experimental_units import ExperimentalUnit


def _non_empty(value: Any) -> bool:
    return value not in (None, "", [], {})


def _normalized_entropy(values: list[str]) -> float:
    counts = Counter(value for value in values if value)
    if not counts:
        return 0.0
    total = sum(counts.values())
    if len(counts) == 1:
        return 0.0
    entropy = -sum((count / total) * log(count / total) for count in counts.values())
    return entropy / log(len(counts))


def _saturating_density(count: int, total: int, target: float) -> float:
    if total <= 0 or target <= 0:
        return 0.0
    return min((count / total) / target, 1.0)


def compute_comparability_score(
    units: list[ExperimentalUnit],
    *,
    required_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Compute a bounded comparability score for a session set.

    The score is descriptive. It decides whether a subset is useful for
    comparison; it does not validate or upgrade research claims.
    """
    total = len(units)
    if total == 0:
        metrics = {
            "metadata_completeness": 0.0,
            "runtime_diversity": 0.0,
            "task_variance": 0.0,
            "failure_density": 0.0,
            "intervention_density": 0.0,
            "topology_variance": 0.0,
            "reproducibility": 0.0,
        }
        return {"score": 0.0, "metrics": metrics}

    fields = required_fields or ("runtime", "task_type", "task_source", "success")
    present = 0
    for unit in units:
        for field in fields:
            present += int(_non_empty(unit.metadata.get(field)))
    metadata_completeness = present / (total * len(fields)) if fields else 1.0

    failures = sum(1 for unit in units if unit.success is False)
    interventions = sum(
        1
        for unit in units
        if unit.human_intervention is True
        or unit.intervention_lane not in ("", "direct_prompt_native")
        or unit.task_source in {
            "routed_prompt_intervention",
            "superpowers_workflow_intervention",
            "controlled_prompt_morphology",
        }
    )

    metrics = {
        "metadata_completeness": round(metadata_completeness, 4),
        "runtime_diversity": round(_normalized_entropy([unit.runtime for unit in units]), 4),
        "task_variance": round(_normalized_entropy([unit.task_type for unit in units]), 4),
        "failure_density": round(_saturating_density(failures, total, 0.1), 4),
        "intervention_density": round(_saturating_density(interventions, total, 0.1), 4),
        "topology_variance": round(_normalized_entropy([unit.topology for unit in units]), 4),
        "reproducibility": 1.0,
    }
    score = sum(metrics.values()) / len(metrics)
    return {"score": round(score, 4), "metrics": metrics}
