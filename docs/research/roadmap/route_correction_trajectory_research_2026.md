# Route Correction: Trajectory-Level Research Alignment (2026)

Recent trajectory-level research strengthens the case that agent analysis is shifting toward runtime traces, tool observations, correction triggers, and long-horizon behavior. `causetrace` should absorb this trend critically, without changing its core direction.

## Current Phase Status

| Item | Status | Note |
| --- | --- | --- |
| Phase 2.5 | complete | corpus hardening and governance are in place |
| Phase 3A | complete | descriptive baseline established |
| Phase 3B | complete | stratified comparison established |
| Phase 3C | complete | governed corpus expansion reached the native lane target |
| Phase 3D | active | hypothesis registry is now the next research phase |
| Phase 3E | reserved | controlled transition studies, not yet executed |
| strict research-grade sessions | `157` | enough for Phase 3 entry, still descriptive rather than law-like |
| native strict sessions | `100` | strict native lane reached the target baseline |
| data_origin coverage | `100%` | no missing data_origin remains |
| controlled benchmark | candidate/protocol | not ingested into corpus yet |

Phase 3C governance and corpus expansion are complete.

## Corrected Long-Term Route

### Phase 3C: Targeted Corpus Expansion & Lane Governance

Status: complete.

Goals achieved:

- preserve native / controlled / external lane boundaries
- complete manual origin annotation for the active corpus
- establish lane baseline and runbook
- expand native non-demo strict sessions to the target baseline
- keep controlled benchmark as a separate candidate/protocol lane

Controlled benchmark candidates such as SWE-Gym and SWE-EVO may be tracked here, but only as candidates. They must not be ingested before manual origin annotation, lane baseline confirmation, and controlled benchmark protocol review.

Exit criteria:

- strict data_origin coverage >= 95%
- native non-demo strict >= 100
- strict failure >= 20
- strict human_intervention=true >= 10
- controlled same-task benchmark tasks >= 10
- each main runtime native non-demo strict >= 20

The native lane target has been met; the remaining failure / intervention enrichment is now part of the Phase 3D / 3E research path rather than a blocker for Phase 3C completion.

### Phase 3C Operating Warning

- Do not treat `readiness=True` as a license to collapse lane boundaries.
- Do not use controlled benchmark candidates as native evidence.
- Do not promote Phase 3D hypotheses into conclusions until corpus-backed validation exists.
- Do not move into Phase 3E until controlled transition studies have a real controlled benchmark lane to compare against.

### Phase 3D: Runtime Morphology Hypothesis Registry

Status: active.

Purpose: store falsifiable hypotheses about runtime morphology, failure morphology, human intervention, observation-triggered transitions, long-horizon morphology, and external generalization.

Primary documents:

- [Phase 3D README](../phase3d/README.md)
- [Hypothesis registry](../phase3d/hypothesis_registry_v0.2.5.md)
- [Validation protocol](../phase3d/validation_protocol.md)
- [Hypothesis prioritization](../phase3d/hypothesis_prioritization_v0.2.5.md)

### Phase 3E: Controlled Transition Studies

Status: reserved.

Purpose: test how events, observations, and interventions trigger topology transitions after the registry is populated and a controlled benchmark lane is available.

Examples:

- test failure -> retry loop
- tool contradiction -> branch exploration
- human correction -> branch collapse
- long-horizon task -> fan-in

This remains descriptive and hypothesis-testing only.

### Cross-project Prompt Morphology Study

Status: planned.

This is a controlled branch study between Phase 3D and Phase 3E. It compares minimal, expanded-constrained, and human-structured prompts across active repositories such as `automatic-signature` and `lingjian-saas`, while `causetrace` handles trace capture and morphology analysis.

The study may inform project-level prompt policy and `causetrace` hypotheses, but it does not change the native corpus, core schema, or topology taxonomy.

### Phase 4: Runtime Morphology Theory

Purpose: stabilize a runtime behavior vocabulary across multiple corpora and lanes.

### Phase 5: Evaluation / Diagnostics Branches

These should be split into separate projects if they become real products:

- `causetrace-bench` for controlled benchmark runners
- `causetrace-failure` for failure morphology experiments
- `causetrace-adapters` for external trajectory adapters
- `causetrace-eval` for topology-aware evaluation
- `causetrace-safety` for safety morphology research

## Absorption Rule

External research may inform hypotheses, terminology, and research questions, but it must not directly change core schemas, topology taxonomy, readiness gates, or research conclusions without causetrace corpus evidence.

## Summary

The route is corrected, not redirected:

- topology-first
- causality-first
- hypothesis-driven, not prediction-driven
- corpus-evidence-gated, not literature-gated
- cross-project prompt morphology can run as a controlled branch, not as a core rewrite
