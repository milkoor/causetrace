"""Named CRDD subset definitions."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SubsetDefinition:
    """Selection contract for a comparable or experimental subset."""

    subset_id: str
    purpose: str
    required_fields: tuple[str, ...]
    prohibited_claims: tuple[str, ...] = ()


SUBSET_DEFINITIONS: dict[str, SubsetDefinition] = {
    "strict_research_grade": SubsetDefinition(
        subset_id="strict_research_grade",
        purpose="Baseline runtime morphology with declared core metadata.",
        required_fields=("runtime", "task_type", "task_source", "success"),
        prohibited_claims=("runtime-balanced conclusions", "failure dynamics"),
    ),
    "balanced_cross_runtime": SubsetDefinition(
        subset_id="balanced_cross_runtime",
        purpose="Runtime comparison with capped per-runtime counts.",
        required_fields=("runtime", "task_type", "task_source", "success"),
        prohibited_claims=("whole-corpus prevalence",),
    ),
    "failure_enriched": SubsetDefinition(
        subset_id="failure_enriched",
        purpose="Failure and near-failure boundary analysis.",
        required_fields=("runtime", "task_type", "success"),
        prohibited_claims=("overall success-rate estimation",),
    ),
    "intervention_lane": SubsetDefinition(
        subset_id="intervention_lane",
        purpose="Control-vs-intervention morphology study input.",
        required_fields=("runtime", "task_type", "task_source"),
        prohibited_claims=("native baseline conclusions",),
    ),
}


def get_subset_definition(subset_id: str) -> SubsetDefinition:
    """Return a subset definition or raise a clear error."""
    try:
        return SUBSET_DEFINITIONS[subset_id]
    except KeyError as exc:
        known = ", ".join(sorted(SUBSET_DEFINITIONS))
        raise ValueError(f"Unknown CRDD subset: {subset_id}. Known: {known}") from exc
