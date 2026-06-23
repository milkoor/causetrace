"""Safety constraints for CERC experiment planning."""
from __future__ import annotations

from typing import Any


EXECUTION_MODE = "external_only"
EVIDENCE_STATUS = "planned_not_observed"
PHASE4_GRADE_EFFECT = "none"
PROHIBITED_EXECUTION_KEYS = {
    "api_call",
    "agent_command",
    "bash",
    "cmd",
    "command",
    "execute",
    "shell",
    "subprocess",
}


def _find_prohibited_keys(value: Any, *, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in PROHIBITED_EXECUTION_KEYS:
                hits.append(child_path)
            hits.extend(_find_prohibited_keys(child, path=child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_find_prohibited_keys(child, path=f"{path}[{index}]"))
    return hits


def validate_execution_queue(queue: dict[str, Any]) -> dict[str, Any]:
    """Validate that a CERC queue is a plan, not an execution payload."""
    issues: list[str] = []
    if queue.get("execution_mode") != EXECUTION_MODE:
        issues.append("execution_mode must be external_only")
    if queue.get("must_not_execute") is not True:
        issues.append("must_not_execute must be true")
    if queue.get("evidence_status") != EVIDENCE_STATUS:
        issues.append("evidence_status must be planned_not_observed")
    if queue.get("observed_session_count") != 0:
        issues.append("observed_session_count must be 0 for planned queues")
    if queue.get("phase4_grade_effect") != PHASE4_GRADE_EFFECT:
        issues.append("phase4_grade_effect must be none")

    for scenario in queue.get("bde_scenarios", []):
        if scenario.get("descriptor_only") is not True:
            issues.append(f"scenario {scenario.get('scenario_id', '<unknown>')} must be descriptor_only")

    prohibited = _find_prohibited_keys(queue)
    if prohibited:
        issues.append("queue contains prohibited execution keys: " + ", ".join(sorted(prohibited)))

    return {"ok": not issues, "issues": issues}
