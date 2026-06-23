"""CRDD comparability helpers."""
from __future__ import annotations

from collections import Counter
from typing import Any

from .comparability_score import compute_comparability_score
from .experimental_units import ExperimentalUnit


def distribution(units: list[ExperimentalUnit], field: str) -> dict[str, int]:
    """Count a comparison field across units."""
    counts: Counter[str] = Counter()
    for unit in units:
        if field == "topology":
            value = unit.topology
        elif field == "event_count":
            value = str(unit.event_count)
        else:
            value = str(unit.metadata.get(field) or "")
        counts[value or "unknown"] += 1
    return dict(sorted(counts.items()))


def summarize_comparability(
    units: list[ExperimentalUnit],
    *,
    required_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Return score plus distributions used to inspect subset comparability."""
    return {
        "comparability": compute_comparability_score(units, required_fields=required_fields),
        "distributions": {
            "runtime": distribution(units, "runtime"),
            "task_type": distribution(units, "task_type"),
            "task_source": distribution(units, "task_source"),
            "data_origin": distribution(units, "data_origin"),
            "intervention_lane": distribution(units, "intervention_lane"),
            "topology": distribution(units, "topology"),
        },
    }
