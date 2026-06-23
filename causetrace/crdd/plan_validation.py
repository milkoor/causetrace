"""CERC plan validation helpers.

This layer validates experiment plans without executing them. It checks for
queue integrity, duplicate plan signatures, and whether the requested sampling
is still needed.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from causetrace.core import JSONStore

from .constraints import validate_execution_queue
from .experiment_planner import DEFAULT_PLAN_OUTPUT_DIR
from .gap_analyzer import analyze_gaps
from .subset_registry import SUBSET_DEFINITIONS


DEFAULT_PLAN_VALIDATION_OUTPUT_DIR = Path.home() / ".causetrace" / "plan_validation"


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return data


def _canonicalize_queue(queue: dict[str, Any]) -> dict[str, Any]:
    def _clean(value: Any) -> Any:
        if isinstance(value, dict):
            cleaned: dict[str, Any] = {}
            for key, item in value.items():
                if key in {"experiment_id", "generated_at", "output_dir", "queue_hash", "validation"}:
                    continue
                cleaned[key] = _clean(item)
            return cleaned
        if isinstance(value, list):
            return [_clean(item) for item in value]
        return value

    return _clean(queue)


def _queue_signature(queue: dict[str, Any]) -> str:
    canonical = _canonicalize_queue(queue)
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _scan_duplicate_plans(plan_root: Path, signature: str, current_plan_dir: Path) -> list[str]:
    duplicates: list[str] = []
    if not plan_root.exists():
        return duplicates
    for queue_path in plan_root.rglob("experiment_queue.json"):
        if queue_path.parent == current_plan_dir:
            continue
        try:
            queue = _load_json(queue_path)
        except Exception:
            continue
        if _queue_signature(queue) == signature:
            duplicates.append(str(queue_path.parent))
    return sorted(duplicates)


def validate_experiment_plan(
    store: JSONStore,
    *,
    plan_dir: str | Path,
    output_dir: str | Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Validate an experiment plan without executing it."""
    plan_path = Path(plan_dir)
    queue_path = plan_path / "experiment_queue.json"
    gap_path = plan_path / "gap_report.json"
    if not queue_path.exists():
        raise FileNotFoundError(f"missing plan queue: {queue_path}")

    queue = _load_json(queue_path)
    gap_report = _load_json(gap_path) if gap_path.exists() else {}
    target_subset = str(queue.get("target_subset") or gap_report.get("target_subset") or "unknown")
    if target_subset in SUBSET_DEFINITIONS:
        current_gap = analyze_gaps(store, subset_ids=[target_subset])["subset_gaps"][0]
    else:
        current_gap = None

    constraint_check = validate_execution_queue(queue)
    signature = _queue_signature(queue)
    plan_root = plan_path.parent if plan_path.parent != plan_path else DEFAULT_PLAN_OUTPUT_DIR
    duplicate_plans = _scan_duplicate_plans(plan_root, signature, plan_path)
    required_sessions = int(queue.get("required_sessions", 0) or 0)
    missing_sessions = int((current_gap or {}).get("missing_sessions", required_sessions))
    needed = missing_sessions > 0 and required_sessions > 0
    valid = constraint_check["ok"] and not duplicate_plans and needed

    report: dict[str, Any] = {
        "schema": "causetrace.cerc.plan_validation.v0.1",
        "generated_at": datetime.now().isoformat(),
        "plan_dir": str(plan_path),
        "target_subset": target_subset,
        "required_sessions": required_sessions,
        "current_gap": current_gap,
        "gap_report": gap_report,
        "queue_signature": signature,
        "duplicate_plans": duplicate_plans,
        "constraint_check": constraint_check,
        "necessity": {
            "missing_sessions": missing_sessions,
            "sampling_needed": needed,
        },
        "validation": {
            "ok": valid,
            "status": "ready" if valid else ("duplicate" if duplicate_plans else "not_needed"),
        },
        "constraints": {
            "external_only": True,
            "no_execution": True,
            "no_evidence_inflation": True,
            "no_phase4_grade_promotion": True,
        },
    }

    if write:
        root = Path(output_dir) if output_dir else DEFAULT_PLAN_VALIDATION_OUTPUT_DIR
        run_dir = root / plan_path.name
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "plan_validation.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        (run_dir / "plan_validation.md").write_text(
            "\n".join([
                f"# Plan validation: {plan_path.name}",
                "",
                f"- target subset: `{target_subset}`",
                f"- required sessions: `{required_sessions}`",
                f"- missing sessions: `{missing_sessions}`",
                f"- sampling needed: `{needed}`",
                f"- duplicate plans: `{len(duplicate_plans)}`",
                f"- validation ok: `{valid}`",
                f"- queue signature: `{signature}`",
                "",
                "## Safety Boundary",
                "",
                "Plan validation is read-only. It does not execute runtimes, alter evidence grades, or emit commands.",
            ])
            + "\n",
            encoding="utf-8",
        )
        report["output_dir"] = str(run_dir)
    else:
        report["output_dir"] = None

    return report
