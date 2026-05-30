# Phase 3A: Descriptive Runtime Cognition

Status: complete for the v0.2.5 corpus snapshot.

This directory holds the first descriptive analysis set for Phase 3A. The
reports are intentionally observational and limited to the strict
research-grade subset unless stated otherwise.

## Reports

- [Baseline v0.2.5](baseline_v0.2.5.md)
- [Fingerprint Metrics v0.2.5](fingerprint_metrics_v0.2.5.md)
- [Non-demo Bias Check v0.2.5](non_demo_bias_v0.2.5.md)

## What Phase 3A established

- The strict subset is dominated by `dominant_chain` topology.
- `demo` and `anthropic` dominate the strict runtime set.
- `debug_test` dominates the strict task set.
- `multi_root_exploration` exists, but only as a minority shape.
- No stable runtime fingerprint is justified yet from this corpus alone.
- No stable topology-to-task conclusion is justified yet from this corpus alone.

## What Phase 3A did not do

- No prediction model.
- No anomaly classifier.
- No runtime ranking.
- No causal interpretation beyond observation.

## Next phase entry point

Phase 3B should begin by splitting the strict subset into:

1. success vs failure
2. human_intervention vs no_intervention
3. demo-heavy vs non-demo subsets
