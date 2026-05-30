# Phase 3B: Stratified Runtime Morphology

Status: complete for the v0.2.5 corpus snapshot.

This directory contains the first stratified follow-up to Phase 3A. The goal is
to check whether the descriptive signals from the strict research-grade corpus
remain after splitting the corpus by confounders.

## Reports

- [Stratified Baseline v0.2.5](stratified_baseline_v0.2.5.md)
- [Demo vs Non-demo v0.2.5](demo_vs_non_demo_v0.2.5.md)
- [Success vs Failure v0.2.5](success_failure_v0.2.5.md)
- [Human Intervention v0.2.5](human_intervention_v0.2.5.md)
- [Runtime Signal After Controls v0.2.5](runtime_signal_after_controls_v0.2.5.md)

## What Phase 3B established

- `demo` is a major confounder and must be treated as a first-class split.
- The non-demo strict subset is much smaller than the full strict subset.
- `success` is heavily imbalanced in the strict subset.
- `human_intervention` is sparse and has no positive strict-case examples in this snapshot.
- Runtime-level differences remain visible, but the evidence is still descriptive.

## What Phase 3B did not do

- No prediction model.
- No anomaly classifier.
- No runtime ranking.
- No causal interpretation beyond observation.

## Next phase entry point

Phase 3C should only begin after deciding whether to:

1. expand the non-demo corpus,
2. collect failed sessions deliberately, or
3. treat the current signal as insufficient for fingerprinting.
