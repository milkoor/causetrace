"""Execution queue manifest generation for CERC.

Queues are external-only requirements. They never contain runnable commands.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from .constraints import (
    EVIDENCE_STATUS,
    EXECUTION_MODE,
    PHASE4_GRADE_EFFECT,
    validate_execution_queue,
)


def _queue_hash(queue: dict[str, Any]) -> str:
    stable = {
        "experiment_id": queue["experiment_id"],
        "target_subset": queue["target_subset"],
        "required_sessions": queue["required_sessions"],
        "distribution_targets": queue["distribution_targets"],
        "bde_scenarios": queue["bde_scenarios"],
        "execution_mode": queue["execution_mode"],
        "must_not_execute": queue["must_not_execute"],
        "evidence_status": queue["evidence_status"],
        "phase4_grade_effect": queue["phase4_grade_effect"],
    }
    payload = json.dumps(stable, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_execution_queue(
    *,
    experiment_id: str,
    target_subset: str,
    required_sessions: int,
    distribution_targets: dict[str, dict[str, float]],
    bde_scenarios: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build and validate an external-only experiment queue."""
    queue = {
        "schema": "causetrace.cerc.execution_queue.v0.1",
        "experiment_id": experiment_id,
        "generated_at": datetime.now().isoformat(),
        "target_subset": target_subset,
        "required_sessions": required_sessions,
        "distribution_targets": distribution_targets,
        "bde_scenarios": bde_scenarios,
        "execution_mode": EXECUTION_MODE,
        "must_not_execute": True,
        "evidence_status": EVIDENCE_STATUS,
        "observed_session_count": 0,
        "phase4_grade_effect": PHASE4_GRADE_EFFECT,
        "may_trigger_future_sampling": True,
        "descriptor_only": True,
        "prohibited_actions": [
            "auto_agent_execution",
            "runtime_mutation",
            "phase4_grade_promotion",
            "treating_plans_as_observed_evidence",
        ],
    }
    queue["validation"] = validate_execution_queue(queue)
    queue["queue_hash"] = _queue_hash(queue)
    return queue
