# Phase 4: Runtime Morphology Theory Drafting

Phase 4 consolidates evidence-graded theory candidates from Phase 3D (hypothesis registry) and Phase 3E (intervention-aware validation). It drafts, grades, and organizes theory statements. It does not finalize, productize, or operationalize them.

## Position

- Phase 3D: complete
- Phase 3E: complete
- Phase 4: **active** (theory drafting only)
- Phase 5: not open (evaluation, diagnostics, prediction)

## Mission

Convert the strongest evidence-backed findings from Phase 3D and Phase 3E into graded theory candidates. Each candidate must carry an evidence grade, a corpus snapshot, a lane scope, a denominator, runtime/task caveats, and a falsification condition.

## What Phase 4 Is

- Evidence-graded theory drafting
- Consolidation of Phase 3D + Phase 3E findings into theory statements
- Organization of theory candidates by domain (runtime morphology, workflow intervention, failure, prompt posture)
- Honest documentation of what is underdetermined
- Maintenance of the hypothesis registry as a living document

## What Phase 4 Is NOT

- Theory finalization or publication of stable conclusions
- Prediction of agent behavior
- Anomaly detection or scoring
- Automatic diagnosis of trace quality
- Universal prompt policy recommendations
- Cross-lane aggregation without lane disclosure
- Promotion of exploratory findings to stable theory
- Merging intervention lane findings into native baseline conclusions
- Phase 5 (evaluation / diagnostics)

## Evidence Grades

Every theory candidate must carry exactly one grade:

| Grade | Meaning | Criteria |
|-------|---------|----------|
| `supported` | Evidence sufficient under current corpus constraints | Multiple independent sessions, disclosed denominator, runtime/task distribution reported, falsification condition stated |
| `supported_with_caveat` | Evidence present but sample-limited or lane-restricted | Same as supported but gated on lane scope or corpus size |
| `exploratory` | Trend visible but sample too small for confidence | <10 sessions in relevant lane, or single-runtime only |
| `inconclusive` | Cannot determine from current corpus | Conflicting signals, or insufficient per-condition samples |
| `deferred` | Explicitly not evaluated | Gated on corpus growth, controlled benchmark, or tag accumulation |

## Theory Candidate Structure

Every candidate must include:

- **Claim**: one-sentence theory statement (falsifiable)
- **Evidence grade**: from the table above
- **Supporting corpus snapshot**: date and metrics
- **Lane**: which lane(s) the evidence comes from
- **Denominator**: session count the claim is based on
- **Runtime/task caveats**: distribution limitations
- **Falsification condition**: what evidence would disprove it
- **Status**: `active`, `under_review`, `superseded`, `retracted`
- **Source hypotheses**: Phase 3D registry entries that fed this candidate

## Documents

- [Theory Candidate Inventory](theory_candidate_inventory_v0.2.5.md) — All current theory candidates with evidence grades, supporting data, and caveats
- [Safety-Control Runtime Morphology](safety_control_morphology_candidates_v0.2.5.md) — Phase 4 theory candidate direction studying runtime control morphology at safety boundaries (exploratory, not validated)

## Operating Rules

- Do not remove or downgrade negative results.
- Do not promote a candidate beyond its evidence grade.
- Do not merge intervention lane evidence into native lane theory statements.
- Every claim must bind to a specific corpus snapshot and lane.
- Every percentage must include its denominator.
- Every runtime conclusion must disclose runtime distribution.
- Cross-lane comparison may report trends only.
- Do not enter Phase 5.
- Do not implement prediction, anomaly detection, or auto-diagnosis.
- Do not create universal prompt policy defaults.
- Do not modify topology taxonomy or readiness gates unless explicitly justified by evidence review.

## Current State

Phase 4-1 is active. Two documents published:

- **Theory candidate inventory**: 7 candidates across 4 domains (default morphology, workflow intervention, failure, prompt/routed/controlled)
- **Safety-control runtime morphology**: 5 exploratory candidates (T-SC-001 through T-SC-005) defining a fifth domain studying runtime behavior at safety boundaries

All candidates are evidence-graded. No candidate has been promoted beyond its grade. No new hypotheses are being registered — Phase 4 consolidates and extends, it does not finalize.
