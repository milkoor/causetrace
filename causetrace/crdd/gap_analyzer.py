"""Corpus gap analysis for CERC experiment planning."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from causetrace.core import JSONStore

from .subset_builder import compile_subsets
from .subset_registry import SUBSET_DEFINITIONS


DEFAULT_SUBSET_TARGETS = {
    "strict_research_grade": 150,
    "balanced_cross_runtime": 20,
    "failure_enriched": 50,
    "intervention_lane": 15,
}


def _severity(missing: int, target: int) -> str:
    if missing <= 0:
        return "none"
    ratio = missing / target if target else 0
    if ratio >= 0.75:
        return "high"
    if ratio >= 0.35:
        return "medium"
    return "low"


def analyze_gaps(
    store: JSONStore,
    *,
    subset_ids: list[str] | None = None,
    targets: dict[str, int] | None = None,
    output: str | Path | None = None,
) -> dict[str, Any]:
    """Analyze CRDD subset gaps without mutating corpus data."""
    requested = subset_ids or list(SUBSET_DEFINITIONS)
    target_map = dict(DEFAULT_SUBSET_TARGETS)
    if targets:
        target_map.update(targets)

    compiled = compile_subsets(store, subset_ids=requested, write=False)
    subset_gaps: list[dict[str, Any]] = []
    for manifest in compiled["manifests"]:
        subset_id = manifest["subset_id"]
        current = int(manifest["selected_count"])
        target = int(target_map.get(subset_id, current))
        missing = max(target - current, 0)
        subset_gaps.append({
            "subset_id": subset_id,
            "current_sessions": current,
            "target_sessions": target,
            "missing_sessions": missing,
            "status": "met" if missing == 0 else "under_target",
            "severity": _severity(missing, target),
            "comparability_score": manifest["comparability"]["score"],
            "distributions": manifest["distributions"],
            "bias_register": manifest["bias_register"],
            "prohibited_claims": manifest["prohibited_claims"],
        })

    report = {
        "schema": "causetrace.cerc.gap_report.v0.1",
        "generated_at": datetime.now().isoformat(),
        "source_session_count": compiled["source_session_count"],
        "subset_gaps": subset_gaps,
    }
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report
