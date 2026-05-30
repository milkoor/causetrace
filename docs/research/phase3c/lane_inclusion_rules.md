# Phase 3C Lane Inclusion Rules

This document defines what each data lane can and cannot be used for.

## Lane Definitions

| Lane | Description | Typical source | Primary use |
| --- | --- | --- | --- |
| Native lane | Directly captured agent runtime sessions | causetrace hooks, local tailers, direct session capture | Main research conclusions |
| Controlled benchmark lane | Same-task, multi-runtime comparison sessions | SWE-bench Verified, curated local issue sets, reproducible benchmark runs | Controlled contrasts |
| External trajectory lane | Reconstructed or imported runtime trajectories | SWE-bench experiments, SWE-Gym, OpenHands trajectories | Morphology expansion |

## Native Lane

### Allowed

- runtime fingerprint candidates
- topology-task association candidates
- failure topology characterization
- human-intervention analysis
- research-grade and strict research-grade reporting

### Not allowed

- claims based only on benchmark-derived behavior
- claims based only on reconstructed trajectories
- mixing demo-heavy sessions into strong conclusions without explicit controls

## Controlled Benchmark Lane

### Allowed

- same-task, multi-runtime comparisons
- controlled topology contrasts
- success/failure comparisons under the same task
- reproducibility checks across runtimes

### Not allowed

- direct claims about unstructured real-world development behavior
- treating benchmark trajectories as native truth
- cross-lane aggregation without explicit labeling

## External Trajectory Lane

### Allowed

- topology morphology expansion
- failure-shape coverage
- long-session structure comparison
- adapter validation

### Not allowed

- direct inclusion in native strict research-grade conclusions
- source-neutral runtime fingerprint claims
- claims that require captured parent-event fidelity unless reconstructed fidelity is explicitly tracked

## Cross-Lane Rules

1. Do not aggregate lanes by default.
2. If aggregation is required, publish the lane breakdown first.
3. Always retain `data_origin` and provenance in the derived artifact.
4. If a session has unknown `data_origin`, it must remain out of strong claims.
5. Benchmark and external lanes may inform native hypotheses, but they do not override native evidence.

## Publication Rule

Every report that uses multiple lanes must state:

- which lanes were included
- which lanes were excluded
- whether the result is descriptive or inferential
- whether the conclusion is limited to a single lane
