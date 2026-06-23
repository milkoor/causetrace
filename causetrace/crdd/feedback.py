"""CERC feedback integration.

This layer ingests external execution feedback and turns it into updated gap
reports and reprioritization manifests. It does not execute runtimes or mutate
trace data.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from causetrace.core import JSONStore
from causetrace.corpus import build_session_record

from .experiment_planner import DEFAULT_DISTRIBUTION_TARGETS
from .gap_analyzer import analyze_gaps
from .subset_registry import SUBSET_DEFINITIONS


DEFAULT_FEEDBACK_OUTPUT_DIR = Path("docs/research/dataset_design/feedback")


@dataclass(frozen=True)
class FeedbackObservation:
    """Normalized observation from an external execution feedback payload."""

    session_id: str
    runtime: str = ""
    task_type: str = ""
    task_source: str = ""
    data_origin: str = ""
    intervention_lane: str = ""
    success: bool | None = None
    human_intervention: bool | None = None
    topology: str = ""
    event_count: int = 0
    resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "runtime": self.runtime,
            "task_type": self.task_type,
            "task_source": self.task_source,
            "data_origin": self.data_origin,
            "intervention_lane": self.intervention_lane,
            "success": self.success,
            "human_intervention": self.human_intervention,
            "topology": self.topology,
            "event_count": self.event_count,
            "resolved": self.resolved,
        }


def _load_payload(path: str | Path) -> dict[str, Any]:
    payload_path = Path(path)
    data = json.loads(payload_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("feedback payload must be a JSON object")
    return data


def _as_bool(value: Any) -> bool | None:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y"}:
            return True
        if lowered in {"0", "false", "no", "n"}:
            return False
    return None


def _normalize_observation(store: JSONStore, item: Any) -> FeedbackObservation:
    if isinstance(item, str):
        sid = item
        try:
            record = build_session_record(store, sid)
        except Exception:
            return FeedbackObservation(session_id=sid)
        metadata = record.get("metadata", {})
        stats = record.get("stats", {})
        return FeedbackObservation(
            session_id=sid,
            runtime=str(metadata.get("runtime") or ""),
            task_type=str(metadata.get("task_type") or ""),
            task_source=str(metadata.get("task_source") or ""),
            data_origin=str(metadata.get("data_origin") or ""),
            intervention_lane=str(metadata.get("intervention_lane") or ""),
            success=_as_bool(metadata.get("success")),
            human_intervention=_as_bool(metadata.get("human_intervention")),
            topology=str(record.get("topology") or ""),
            event_count=int(stats.get("event_count", 0) or 0),
            resolved=True,
        )

    if not isinstance(item, dict):
        raise ValueError("observed_sessions must contain strings or objects")

    sid = str(item.get("session_id") or item.get("id") or item.get("observed_session_id") or "")
    resolved = False
    if sid:
        try:
            record = build_session_record(store, sid)
        except Exception:
            record = None
        else:
            metadata = record.get("metadata", {})
            stats = record.get("stats", {})
            resolved = True
            return FeedbackObservation(
                session_id=sid,
                runtime=str(item.get("runtime") or metadata.get("runtime") or ""),
                task_type=str(item.get("task_type") or metadata.get("task_type") or ""),
                task_source=str(item.get("task_source") or metadata.get("task_source") or ""),
                data_origin=str(item.get("data_origin") or metadata.get("data_origin") or ""),
                intervention_lane=str(item.get("intervention_lane") or metadata.get("intervention_lane") or ""),
                success=_as_bool(item.get("success")) if item.get("success") is not None else _as_bool(metadata.get("success")),
                human_intervention=_as_bool(item.get("human_intervention"))
                if item.get("human_intervention") is not None
                else _as_bool(metadata.get("human_intervention")),
                topology=str(item.get("topology") or record.get("topology") or ""),
                event_count=int(item.get("event_count") or stats.get("event_count", 0) or 0),
                resolved=resolved,
            )

    return FeedbackObservation(
        session_id=sid or str(item.get("label") or item.get("name") or "unknown"),
        runtime=str(item.get("runtime") or ""),
        task_type=str(item.get("task_type") or ""),
        task_source=str(item.get("task_source") or ""),
        data_origin=str(item.get("data_origin") or ""),
        intervention_lane=str(item.get("intervention_lane") or ""),
        success=_as_bool(item.get("success")),
        human_intervention=_as_bool(item.get("human_intervention")),
        topology=str(item.get("topology") or ""),
        event_count=int(item.get("event_count") or 0),
        resolved=resolved,
    )


def _distribution(observations: Iterable[FeedbackObservation], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for obs in observations:
        value = getattr(obs, field)
        if isinstance(value, bool):
            key = str(value).lower()
        else:
            key = str(value or "unknown")
        counts[key or "unknown"] += 1
    return dict(sorted(counts.items()))


def _required_target(subset_id: str) -> int:
    defaults = {
        "strict_research_grade": 150,
        "balanced_cross_runtime": 20,
        "failure_enriched": 50,
        "intervention_lane": 15,
    }
    return defaults.get(subset_id, 0)


def _planned_target_sessions(payload: dict[str, Any], plan_queue: dict[str, Any], subset_id: str) -> int:
    planned = plan_queue.get("required_sessions")
    if isinstance(planned, int) and planned >= 0:
        return planned
    fallback = payload.get("required_sessions")
    if isinstance(fallback, int) and fallback >= 0:
        return fallback
    return _required_target(subset_id)


def ingest_feedback(
    store: JSONStore,
    *,
    input_path: str | Path,
    plan_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Ingest an external feedback payload into a normalized report."""
    payload = _load_payload(input_path)
    observations_raw = payload.get("observed_sessions") or payload.get("observed_session_ids") or []
    if not isinstance(observations_raw, list):
        raise ValueError("observed_sessions or observed_session_ids must be a list")

    observations = [_normalize_observation(store, item) for item in observations_raw]
    resolved = sum(1 for obs in observations if obs.resolved)
    unresolved_ids = [obs.session_id for obs in observations if not obs.resolved]
    subset_id = str(payload.get("target_subset") or payload.get("subset_id") or "unknown")
    experiment_id = str(payload.get("experiment_id") or payload.get("name") or "unknown")
    plan_path = Path(plan_dir) if plan_dir else None
    plan_queue = {}
    if plan_path and (plan_path / "experiment_queue.json").exists():
        plan_queue = json.loads((plan_path / "experiment_queue.json").read_text(encoding="utf-8"))

    counts = {
        "runtime": _distribution(observations, "runtime"),
        "task_type": _distribution(observations, "task_type"),
        "task_source": _distribution(observations, "task_source"),
        "data_origin": _distribution(observations, "data_origin"),
        "intervention_lane": _distribution(observations, "intervention_lane"),
        "topology": _distribution(observations, "topology"),
    }

    report: dict[str, Any] = {
        "schema": "causetrace.cerc.feedback_report.v0.1",
        "generated_at": datetime.now().isoformat(),
        "experiment_id": experiment_id,
        "target_subset": subset_id,
        "plan_dir": str(plan_path) if plan_path else None,
        "plan_queue": plan_queue,
        "observed_count": len(observations),
        "resolved_count": resolved,
        "unresolved_session_ids": unresolved_ids,
        "observed_distributions": counts,
        "quality": {
            "resolved_ratio": round(resolved / len(observations), 4) if observations else 0.0,
            "has_failures": any(obs.success is False for obs in observations),
            "has_interventions": any(
                obs.human_intervention is True
                or obs.intervention_lane not in ("", "direct_prompt_native")
                or obs.task_source in {
                    "routed_prompt_intervention",
                    "superpowers_workflow_intervention",
                    "controlled_prompt_morphology",
                }
                for obs in observations
            ),
        },
        "observations": [obs.to_dict() for obs in observations],
        "constraints": {
            "external_only": True,
            "planned_is_not_observed": True,
            "may_affect_future_sampling": True,
        },
    }

    target = _planned_target_sessions(payload, plan_queue, subset_id)
    report["gap_projection"] = {
        "target_sessions": target,
        "observed_sessions": len(observations),
        "remaining_sessions": max(target - len(observations), 0),
        "progress_ratio": round(len(observations) / target, 4) if target else 0.0,
    }

    if write:
        root = Path(output_dir) if output_dir else DEFAULT_FEEDBACK_OUTPUT_DIR
        run_dir = root / experiment_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "feedback_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        report["output_dir"] = str(run_dir)
    else:
        report["output_dir"] = None
    return report


def update_gaps(
    store: JSONStore,
    *,
    feedback_report: dict[str, Any],
    output_dir: str | Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Update gap projections from a normalized feedback report."""
    target_subset = str(feedback_report.get("target_subset") or "unknown")
    current_gap = analyze_gaps(store, subset_ids=[target_subset]) if target_subset in SUBSET_DEFINITIONS else None
    current_subset_gap = (current_gap or {}).get("subset_gaps", [{}])[0]
    observed_count = int(feedback_report.get("observed_count", 0) or 0)
    target = int(feedback_report.get("gap_projection", {}).get("target_sessions", 0) or 0)
    remaining = max(target - observed_count, 0)
    updated = {
        "schema": "causetrace.cerc.gap_update.v0.1",
        "generated_at": datetime.now().isoformat(),
        "experiment_id": feedback_report.get("experiment_id"),
        "target_subset": target_subset,
        "current_gap": current_subset_gap,
        "feedback_gap_projection": feedback_report.get("gap_projection", {}),
        "observed_count": observed_count,
        "remaining_sessions": remaining,
        "status": "met" if remaining == 0 else "under_target",
        "priority_hint": "reprioritize" if remaining > 0 else "hold",
        "quality": feedback_report.get("quality", {}),
    }
    if write:
        root = Path(output_dir) if output_dir else DEFAULT_FEEDBACK_OUTPUT_DIR
        run_dir = root / str(feedback_report.get("experiment_id") or "unknown")
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "gap_update.json").write_text(json.dumps(updated, indent=2, sort_keys=True), encoding="utf-8")
        updated["output_dir"] = str(run_dir)
    else:
        updated["output_dir"] = None
    return updated


def reprioritize_experiments(
    store: JSONStore,
    *,
    feedback_report: dict[str, Any],
    output_dir: str | Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Reprioritize future experiment planning based on feedback."""
    current_gaps = analyze_gaps(store)
    remaining_by_subset = {
        gap["subset_id"]: int(gap["missing_sessions"])
        for gap in current_gaps["subset_gaps"]
    }
    feedback_target = str(feedback_report.get("target_subset") or "unknown")
    feedback_remaining = int(feedback_report.get("gap_projection", {}).get("remaining_sessions", 0) or 0)
    priorities: list[dict[str, Any]] = []
    for gap in current_gaps["subset_gaps"]:
        subset_id = gap["subset_id"]
        remaining = remaining_by_subset.get(subset_id, 0)
        severity = gap["severity"]
        severity_weight = {"high": 3, "medium": 2, "low": 1, "none": 0}.get(severity, 0)
        feedback_boost = 1 if subset_id == feedback_target and feedback_remaining > 0 else 0
        priority_score = remaining + severity_weight + feedback_boost
        priorities.append({
            "subset_id": subset_id,
            "current_sessions": gap["current_sessions"],
            "target_sessions": gap["target_sessions"],
            "remaining_sessions": remaining,
            "severity": severity,
            "comparability_score": gap["comparability_score"],
            "priority_score": priority_score,
            "reason": (
                f"remaining={remaining}, severity={severity}, "
                f"feedback_target={subset_id == feedback_target}"
            ),
            "default_distribution_targets": DEFAULT_DISTRIBUTION_TARGETS.get(subset_id, {}),
        })

    priorities.sort(key=lambda item: (-item["priority_score"], item["subset_id"]))
    report = {
        "schema": "causetrace.cerc.reprioritized_plan.v0.1",
        "generated_at": datetime.now().isoformat(),
        "experiment_id": feedback_report.get("experiment_id"),
        "target_subset": feedback_target,
        "priorities": priorities,
        "feedback_summary": {
            "observed_count": feedback_report.get("observed_count", 0),
            "resolved_count": feedback_report.get("resolved_count", 0),
            "remaining_sessions": feedback_remaining,
        },
        "constraints": {
            "no_execution": True,
            "no_evidence_inflation": True,
            "no_phase4_grade_promotion": True,
        },
    }
    if write:
        root = Path(output_dir) if output_dir else DEFAULT_FEEDBACK_OUTPUT_DIR
        run_dir = root / str(feedback_report.get("experiment_id") or "unknown")
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "reprioritized_plan.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        report["output_dir"] = str(run_dir)
    else:
        report["output_dir"] = None
    return report
