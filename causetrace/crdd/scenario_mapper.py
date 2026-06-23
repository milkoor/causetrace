"""Map CRDD subset gaps to BDE scenario descriptors."""
from __future__ import annotations

from typing import Any


SCENARIO_MAP: dict[str, list[dict[str, Any]]] = {
    "failure_enriched": [
        {
            "scenario_id": "partial_context_v1",
            "purpose": "increase near-failure coverage through incomplete context tasks",
            "descriptor_only": True,
        },
        {
            "scenario_id": "ambiguous_requirements_v1",
            "purpose": "surface clarification and recovery behavior",
            "descriptor_only": True,
        },
        {
            "scenario_id": "tool_failure_observation_v1",
            "purpose": "observe runtime response to failed tool feedback",
            "descriptor_only": True,
        },
    ],
    "intervention_lane": [
        {
            "scenario_id": "superpowers_workflow_prompt_v1",
            "purpose": "expand explicit workflow-intervention traces",
            "descriptor_only": True,
        },
        {
            "scenario_id": "human_checkpoint_v1",
            "purpose": "collect human intervention boundary observations",
            "descriptor_only": True,
        },
    ],
    "balanced_cross_runtime": [
        {
            "scenario_id": "cross_runtime_matched_task_v1",
            "purpose": "collect matched task traces across runtimes",
            "descriptor_only": True,
        },
    ],
    "strict_research_grade": [
        {
            "scenario_id": "metadata_complete_native_run_v1",
            "purpose": "collect native runs with complete comparison metadata",
            "descriptor_only": True,
        },
    ],
}


def map_scenarios(target_subset: str) -> list[dict[str, Any]]:
    """Return descriptor-only BDE scenarios for a target subset."""
    return [dict(item) for item in SCENARIO_MAP.get(target_subset, [])]
