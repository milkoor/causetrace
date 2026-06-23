"""Read-only CRDD subset compiler."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from causetrace.core import JSONStore
from causetrace.corpus import list_corpus_records

from .comparability import summarize_comparability
from .experimental_units import ExperimentalUnit, record_to_unit
from .subset_registry import SUBSET_DEFINITIONS, get_subset_definition


DEFAULT_SUBSET_OUTPUT_DIR = Path("docs/research/dataset_design/manifests")
INTERVENTION_SOURCES = {
    "routed_prompt_intervention",
    "superpowers_workflow_intervention",
    "controlled_prompt_morphology",
}


def _manifest_hash(manifest: dict[str, Any]) -> str:
    stable = {
        "subset_id": manifest["subset_id"],
        "session_ids": manifest["session_ids"],
        "selected_count": manifest["selected_count"],
        "excluded_count": manifest["excluded_count"],
        "exclusion_counts": manifest["exclusion_counts"],
        "comparability": manifest["comparability"],
        "distributions": manifest["distributions"],
    }
    payload = json.dumps(stable, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _exclusion(reason_counts: Counter[str], reason: str) -> bool:
    reason_counts[reason] += 1
    return False


def _select_strict(unit: ExperimentalUnit, reason_counts: Counter[str]) -> bool:
    definition = get_subset_definition("strict_research_grade")
    if not unit.has_fields(definition.required_fields):
        return _exclusion(reason_counts, "missing_required_metadata")
    return True


def _select_failure(unit: ExperimentalUnit, reason_counts: Counter[str]) -> bool:
    definition = get_subset_definition("failure_enriched")
    if not unit.has_fields(definition.required_fields):
        return _exclusion(reason_counts, "missing_required_metadata")
    if unit.success is False or unit.human_intervention is True:
        return True
    return _exclusion(reason_counts, "not_failure_or_near_failure")


def _select_intervention(unit: ExperimentalUnit, reason_counts: Counter[str]) -> bool:
    definition = get_subset_definition("intervention_lane")
    if not unit.has_fields(definition.required_fields):
        return _exclusion(reason_counts, "missing_required_metadata")
    if unit.intervention_lane and unit.intervention_lane != "direct_prompt_native":
        return True
    if unit.task_source in INTERVENTION_SOURCES:
        return True
    if unit.human_intervention is True:
        return True
    return _exclusion(reason_counts, "not_intervention_lane")


def _balance_by_runtime(units: list[ExperimentalUnit], reason_counts: Counter[str]) -> list[ExperimentalUnit]:
    definition = get_subset_definition("balanced_cross_runtime")
    buckets: dict[str, list[ExperimentalUnit]] = defaultdict(list)
    for unit in units:
        if not unit.has_fields(definition.required_fields):
            reason_counts["missing_required_metadata"] += 1
            continue
        buckets[unit.runtime].append(unit)

    populated = {runtime: sorted(items, key=lambda unit: unit.session_id) for runtime, items in buckets.items() if runtime}
    if len(populated) < 2:
        reason_counts["insufficient_runtime_breadth"] += sum(len(items) for items in populated.values())
        return []

    target = min(len(items) for items in populated.values())
    selected: list[ExperimentalUnit] = []
    selected_ids: set[str] = set()
    for runtime in sorted(populated):
        chosen = populated[runtime][:target]
        selected.extend(chosen)
        selected_ids.update(unit.session_id for unit in chosen)
        reason_counts["runtime_cap_excluded"] += max(len(populated[runtime]) - target, 0)

    return sorted(selected, key=lambda unit: unit.session_id)


def _bias_register(units: list[ExperimentalUnit], total_units: int) -> dict[str, dict[str, Any]]:
    total = len(units)
    runtime_counts = Counter(unit.runtime or "unknown" for unit in units)
    task_counts = Counter(unit.task_type or "unknown" for unit in units)
    failures = sum(1 for unit in units if unit.success is False)
    interventions = sum(
        1
        for unit in units
        if unit.human_intervention is True
        or unit.intervention_lane not in ("", "direct_prompt_native")
        or unit.task_source in INTERVENTION_SOURCES
    )
    unknown_required = sum(
        1
        for unit in units
        if not unit.runtime or not unit.task_type or unit.success is None
    )
    top_runtime_share = max(runtime_counts.values()) / total if total and runtime_counts else 0.0
    top_task_share = max(task_counts.values()) / total if total and task_counts else 0.0
    return {
        "unlabeled_majority": {
            "present": total < total_units,
            "detail": f"{total}/{total_units} sessions selected",
        },
        "failure_scarcity": {
            "present": failures < 10,
            "detail": f"{failures} failure sessions",
        },
        "intervention_scarcity": {
            "present": interventions < 10,
            "detail": f"{interventions} intervention or near-intervention sessions",
        },
        "runtime_imbalance": {
            "present": top_runtime_share > 0.6 if total else False,
            "detail": f"top runtime share {top_runtime_share:.2f}",
        },
        "task_imbalance": {
            "present": top_task_share > 0.6 if total else False,
            "detail": f"top task share {top_task_share:.2f}",
        },
        "success_label_scarcity": {
            "present": unknown_required > 0,
            "detail": f"{unknown_required} selected sessions missing runtime/task/success",
        },
        "duration_absence": {
            "present": any(unit.metadata.get("duration") in (None, "", [], {}) for unit in units),
            "detail": "one or more selected sessions lacks duration",
        },
        "post_hoc_parsing": {
            "present": True,
            "detail": "subset may include parser-derived causality depending on runtime",
        },
    }


def build_subset(
    records: list[dict[str, Any]],
    subset_id: str,
) -> dict[str, Any]:
    """Build one CRDD subset manifest from corpus records."""
    definition = get_subset_definition(subset_id)
    units = [record_to_unit(record) for record in records]
    reason_counts: Counter[str] = Counter()

    if subset_id == "strict_research_grade":
        selected = [unit for unit in units if _select_strict(unit, reason_counts)]
    elif subset_id == "failure_enriched":
        selected = [unit for unit in units if _select_failure(unit, reason_counts)]
    elif subset_id == "intervention_lane":
        selected = [unit for unit in units if _select_intervention(unit, reason_counts)]
    elif subset_id == "balanced_cross_runtime":
        selected = _balance_by_runtime(units, reason_counts)
    else:
        raise ValueError(f"Unhandled CRDD subset: {subset_id}")

    selected = sorted(selected, key=lambda unit: unit.session_id)
    selected_ids = {unit.session_id for unit in selected}
    reason_counts["not_selected"] += len([unit for unit in units if unit.session_id not in selected_ids]) - sum(reason_counts.values())
    if reason_counts["not_selected"] <= 0:
        reason_counts.pop("not_selected", None)

    comparability = summarize_comparability(selected, required_fields=definition.required_fields)
    manifest = {
        "schema": "causetrace.crdd.subset_manifest.v0.1",
        "subset_id": subset_id,
        "purpose": definition.purpose,
        "generated_at": datetime.now().isoformat(),
        "source": "corpus",
        "source_session_count": len(records),
        "selected_count": len(selected),
        "excluded_count": max(len(records) - len(selected), 0),
        "required_fields": list(definition.required_fields),
        "prohibited_claims": list(definition.prohibited_claims),
        "exclusion_counts": dict(sorted(reason_counts.items())),
        "comparability": comparability["comparability"],
        "distributions": comparability["distributions"],
        "bias_register": _bias_register(selected, len(records)),
        "session_ids": [unit.session_id for unit in selected],
        "sessions": [unit.to_manifest_record() for unit in selected],
    }
    manifest["manifest_hash"] = _manifest_hash(manifest)
    return manifest


def compile_subsets(
    store: JSONStore,
    *,
    subset_ids: list[str] | None = None,
    output_dir: str | Path | None = None,
    name: str | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Compile CRDD subset manifests from the current corpus.

    This function is read-only over trace data and metadata. When ``write`` is
    true it writes generated manifests only.
    """
    selected_ids = subset_ids or list(SUBSET_DEFINITIONS)
    records = list_corpus_records(store)
    manifests = [build_subset(records, subset_id) for subset_id in selected_ids]

    run_name = name or datetime.now().strftime("%Y%m%d-%H%M%S")
    root = Path(output_dir) if output_dir else DEFAULT_SUBSET_OUTPUT_DIR
    run_dir = root / run_name
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
        for manifest in manifests:
            path = run_dir / f"{manifest['subset_id']}.json"
            path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        index = {
            "schema": "causetrace.crdd.compile_index.v0.1",
            "generated_at": datetime.now().isoformat(),
            "source_session_count": len(records),
            "subset_ids": [manifest["subset_id"] for manifest in manifests],
            "manifests": {
                manifest["subset_id"]: f"{manifest['subset_id']}.json"
                for manifest in manifests
            },
        }
        (run_dir / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")

    return {
        "output_dir": str(run_dir),
        "source_session_count": len(records),
        "manifests": manifests,
        "written": write,
    }
