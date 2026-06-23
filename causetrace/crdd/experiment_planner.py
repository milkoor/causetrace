"""CERC experiment requirement planner."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from causetrace.core import JSONStore

from .execution_queue import build_execution_queue
from .gap_analyzer import analyze_gaps
from .scenario_mapper import map_scenarios
from .subset_registry import get_subset_definition


DEFAULT_PLAN_OUTPUT_DIR = Path("docs/research/dataset_design/plans")


DEFAULT_DISTRIBUTION_TARGETS: dict[str, dict[str, dict[str, float]]] = {
    "failure_enriched": {
        "runtime": {"codex": 0.4, "claude": 0.4, "aider": 0.2},
        "task_type": {"bug_fix": 0.5, "refactor": 0.3, "review": 0.2},
    },
    "intervention_lane": {
        "runtime": {"claude": 0.5, "codex": 0.3, "opencode": 0.2},
        "task_type": {"exploration": 0.4, "feature_add": 0.4, "review": 0.2},
        "intervention_lane": {
            "superpowers_workflow_intervention": 0.5,
            "routed_prompt_intervention": 0.25,
            "controlled_prompt_morphology": 0.25,
        },
    },
    "balanced_cross_runtime": {
        "runtime": {"claude": 0.25, "codex": 0.25, "opencode": 0.25, "aider": 0.25},
        "task_type": {"bug_fix": 0.25, "feature_add": 0.25, "refactor": 0.25, "review": 0.25},
    },
    "strict_research_grade": {
        "runtime": {"claude": 0.35, "codex": 0.35, "opencode": 0.2, "aider": 0.1},
        "task_type": {"bug_fix": 0.3, "feature_add": 0.3, "refactor": 0.2, "review": 0.2},
    },
}


def _experiment_id(target_subset: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"exp_{target_subset}_{stamp}"


def _plan_markdown(plan: dict[str, Any]) -> str:
    queue = plan["experiment_queue"]
    gap = plan["gap"]
    lines = [
        f"# CERC experiment plan: {queue['experiment_id']}",
        "",
        f"- target subset: `{queue['target_subset']}`",
        f"- required sessions: `{queue['required_sessions']}`",
        f"- current sessions: `{gap['current_sessions']}`",
        f"- target sessions: `{gap['target_sessions']}`",
        f"- evidence status: `{queue['evidence_status']}`",
        f"- execution mode: `{queue['execution_mode']}`",
        f"- must not execute: `{queue['must_not_execute']}`",
        f"- Phase 4 grade effect: `{queue['phase4_grade_effect']}`",
        "",
        "## Distribution Targets",
        "",
    ]
    for field, targets in queue["distribution_targets"].items():
        lines.append(f"### {field}")
        for label, weight in targets.items():
            lines.append(f"- {label}: {weight}")
        lines.append("")
    lines.extend([
        "## BDE Scenarios",
        "",
    ])
    for scenario in queue["bde_scenarios"]:
        lines.append(f"- `{scenario['scenario_id']}`: {scenario['purpose']}")
    lines.extend([
        "",
        "## Safety Boundary",
        "",
        "This plan is an external-only requirement queue. It is not observed evidence, does not run agents, and does not change Phase 4 evidence grades.",
    ])
    return "\n".join(lines) + "\n"


def plan_experiments(
    store: JSONStore,
    *,
    target_subset: str = "failure_enriched",
    required_sessions: int | None = None,
    output_dir: str | Path | None = None,
    name: str | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Plan missing experimental work without executing runtimes."""
    get_subset_definition(target_subset)
    gap_report = analyze_gaps(store, subset_ids=[target_subset])
    gap = gap_report["subset_gaps"][0]
    required = required_sessions if required_sessions is not None else int(gap["missing_sessions"])
    experiment_id = name or _experiment_id(target_subset)
    queue = build_execution_queue(
        experiment_id=experiment_id,
        target_subset=target_subset,
        required_sessions=max(required, 0),
        distribution_targets=DEFAULT_DISTRIBUTION_TARGETS.get(target_subset, {}),
        bde_scenarios=map_scenarios(target_subset),
    )
    plan = {
        "schema": "causetrace.cerc.experiment_plan.v0.1",
        "generated_at": datetime.now().isoformat(),
        "target_subset": target_subset,
        "gap": gap,
        "gap_report": gap_report,
        "experiment_queue": queue,
        "claim_boundary": {
            "planned_is_not_observed": True,
            "phase4_grade_effect": "none",
            "may_trigger_future_sampling": True,
        },
    }

    root = Path(output_dir) if output_dir else DEFAULT_PLAN_OUTPUT_DIR
    run_dir = root / experiment_id
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "gap_report.json").write_text(json.dumps(gap_report, indent=2, sort_keys=True), encoding="utf-8")
        (run_dir / "experiment_queue.json").write_text(json.dumps(queue, indent=2, sort_keys=True), encoding="utf-8")
        (run_dir / "experiment_plan.md").write_text(_plan_markdown(plan), encoding="utf-8")

    return {
        "output_dir": str(run_dir),
        "written": write,
        "plan": plan,
    }
