"""Causal Runtime Dataset Design tools.

CRDD compiles stored traces into comparable subset manifests. It is read-only
over trace data and metadata sidecars.
"""

from .comparability_score import compute_comparability_score
from .feedback import ingest_feedback, reprioritize_experiments, update_gaps
from .experiment_planner import plan_experiments
from .gap_analyzer import analyze_gaps
from .subset_builder import build_subset, compile_subsets
from .subset_registry import SUBSET_DEFINITIONS, get_subset_definition

__all__ = [
    "SUBSET_DEFINITIONS",
    "analyze_gaps",
    "build_subset",
    "compile_subsets",
    "compute_comparability_score",
    "ingest_feedback",
    "get_subset_definition",
    "plan_experiments",
    "reprioritize_experiments",
    "update_gaps",
]
