# Phase 3E Intervention Validation Plan v0.2.5

This document defines the validation protocol for Phase 3E intervention-aware hypothesis checks. It does not execute validation — it defines how validation will be conducted when each lane accumulates sufficient data.

## Position

- Phase 3D: complete
- Phase 3E: active
- This document: validation protocol scaffolding
- Status: **protocol defined, not yet executed**

## Validation Architecture

Phase 3E validation operates on four independent lanes. Each lane has its own evidence bar, and cross-lane comparison is restricted to trend reporting.

```
Lane 1: direct_prompt_native (baseline)
Lane 2: routed_prompt_intervention (no data yet)
Lane 3: superpowers_workflow_intervention (no data yet)
Lane 4: controlled_prompt_morphology (3 pilot sessions)
```

## Evidence Gates

Every claim must satisfy all gates before being treated as validation-grade:

| Gate | Requirement |
|------|-------------|
| Lane | Explicit lane label |
| Corpus snapshot | Dated snapshot with session/event counts |
| Denominator | Every percentage includes its denominator |
| Runtime distribution | Runtime breakdown for the claim's subset |
| Task type distribution | Task type breakdown for the claim's subset |
| Intervention type | If applicable, what intervention was applied |
| Grade | `exploratory` or `validation-grade` |

## Hypothesis Allocation

### Within-Lane (single lane only)

Hypotheses that apply within a single lane:

| Hypothesis | Lane | Category | Status |
|------------|------|----------|--------|
| H-RM-001: dominant_chain is default | direct_prompt_native | Runtime Morphology | Tier 1 validated (Phase 3D) |
| H-RM-002: runtime differences shrink after control | direct_prompt_native | Runtime Morphology | Tier 1 inconclusive |
| H-RM-003: multi_root is minority | direct_prompt_native | Runtime Morphology | Tier 1 validated (Phase 3D) |
| H-TT-001: review/exploration → multi_root | direct_prompt_native | Task-Topology | Tier 1 not supported |
| H-TT-002: feature_add → dominant_chain/collapse | direct_prompt_native | Task-Topology | Tier 1 supported with caveat |

Within-lane checks for intervention lanes are deferred until those lanes accumulate >=10 sessions each.

### Cross-Lane (two or more lanes)

Cross-lane hypotheses compare topology across lanes. These require both lanes to have sufficient data:

| Hypothesis | Lanes | Category | Status |
|------------|-------|----------|--------|
| H-EG-001: controlled lanes show lower branch entropy | controlled vs native | Entropy/Graph | Tier 3 — deferred |
| H-EG-002: external trajectories over-represent retry-heavy | external vs native | Entropy/Graph | Tier 3 — deferred |

Cross-lane comparison may report trends only. Findings do not become universal policy without additional validation.

### Failure & Intervention (requires failure/intervention density)

| Hypothesis | Trigger | Category | Status |
|------------|---------|----------|--------|
| H-FM-001: failure enriched for retry_heavy/branchy | failure session | Failure Morphology | Tier 2 — deferred |
| H-FM-002: failed sessions less likely branch_collapse | failure session | Failure Morphology | Tier 2 — deferred |
| H-IM-001: human intervention as external correction trigger | human_intervention=true | Intervention Morphology | Tier 2 — deferred |
| H-IM-002: post-intervention topology regime shifts | human_intervention=true | Intervention Morphology | Tier 2 — deferred |
| H-EV-004: failure sessions may contain silent divergence | failure session | Epistemic Verbalization | Tier 2 — deferred |
| H-EV-005: human intervention may produce topology regime shifts | human_intervention=true | Epistemic Verbalization | Tier 2 — deferred |

### Controlled / Tool Observation (requires controlled benchmark)

| Hypothesis | Trigger | Category | Status |
|------------|---------|----------|--------|
| H-OT-001: test failures trigger corrective branch exploration | test failure event | Observation-Triggered | Tier 3 — deferred |
| H-OT-002: contradictory observations precede branch_collapse | contradictory output | Observation-Triggered | Tier 3 — deferred |
| H-EV-002: external observations substitute for epistemic verbalization | external tool observation | Epistemic Verbalization | Tier 3 — deferred |
| H-EV-003: branch collapse after uncertainty resolution | uncertainty signal | Epistemic Verbalization | Tier 3 — deferred |

### Registry-Only (future corpus expansion)

| Hypothesis | Category | Status |
|------------|----------|--------|
| H-EV-001: uncertainty verbalization → exploratory topology | Epistemic Verbalization | Tier 4 |
| H-LH-001: long-horizon → more fan-in and branch-collapse | Long Horizon | Tier 4 |
| H-LH-002: multi-file → increased root spawning and entropy | Long Horizon | Tier 4 |

## Validation Sequence

### Phase 3E-1: Lane Baseline (current)

- Establish per-lane session counts, event counts, distributions
- Identify data gaps (routed_prompt_intervention: 0, superpowers_workflow_intervention: 0)
- Document lane labeling infrastructure needs

### Phase 3E-2: Within-Lane Replication

- Re-run Tier 1 checks from Phase 3D on the native lane with updated corpus
- Verify H-RM-001 and H-RM-003 still hold
- Re-check H-RM-002 if per-runtime sample sizes have improved

### Phase 3E-3: Intervention Lane Onboarding

- Establish labeling pipeline for routed_prompt_intervention
- Establish labeling pipeline for superpowers_workflow_intervention
- Grow controlled_prompt_morphology from 3 pilot sessions to >=10

### Phase 3E-4: Opportunistic Tier 2

- When native failure >=10: validate H-FM-001, H-FM-002
- When native near-failure >=10: validate H-EV-004
- When human_intervention density improves: validate H-IM-001, H-IM-002, H-EV-005

### Phase 3E-5: Controlled Benchmark (Tier 3)

- Activate controlled benchmark protocol
- Validate H-OT-001, H-OT-002, H-EG-001, H-EG-002, H-EV-002, H-EV-003

## Readiness Assessment

| Condition | Current | Target | Ready? |
|-----------|---------|--------|--------|
| Native sessions | 101 | 100 | Yes |
| Native failure | 1 | 10 | No |
| Native near-failure | 0 | 10 | No |
| Native human_intervention | 5 | 5 | Yes |
| Routed sessions | 0 | 10 | No |
| Superpowers sessions | 0 | 10 | No |
| Controlled sessions | 3 | 10 | No |
| Multi-runtime failure coverage | 1 | 3 | No |

## Operating Rules

- Do not execute cross-lane validation when one lane has <10 sessions.
- Do not promote Tier 2 hypotheses without sufficient failure/intervention density.
- Negative results are first-class entries — record them, do not delete them.
- Every percentage must include its denominator.
- Lane labels are mandatory for Phase 3E claims.
- Unlabeled sessions are excluded from validation but retained in the corpus.
- Do not enter Phase 4.

## Next Action

Establish labeling pipelines for `routed_prompt_intervention` and `superpowers_workflow_intervention` lanes. Until those lanes have data, Phase 3E validation is confined to within-lane checks on `direct_prompt_native`.
