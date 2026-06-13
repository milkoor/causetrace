# Phase 4-3 Trigger Conditions

Phase 4-3 is a trigger-based evidence refresh pass for Runtime Morphology Theory Draft v0.1. It will not be opened by calendar schedule. It opens only when one or more trigger conditions are met by corpus growth.

## Status

- Phase 4-1 (evidence grading): complete
- Phase 4-2 (theory draft skeleton): complete
- Phase 4-3 (evidence refresh): **waiting for corpus growth triggers**
- Phase 5: not open

## Trigger Conditions

Each trigger defines a specific corpus event that, if met, opens a targeted re-evaluation. Not all triggers must fire for Phase 4-3 to open — a single trigger is sufficient for the affected candidate set.

### Trigger 1: Native Strict Lane Growth

| Field | Value |
|-------|-------|
| **Condition** | native strict sessions increase by >=50% from current baseline (100 → 150+) |
| **Affected candidates** | T-RM-001, T-RM-002, T-RM-003 |
| **Re-evaluation** | Re-run topology distribution against expanded native strict set. Check whether dominant_chain rate holds. Check whether multi_root rate stays at minority level. Check whether feature_add → dominant_chain holds in expanded set with larger sessions. |
| **Minimum evidence** | Updated topology distribution with new denominator and runtime/task distribution |

### Trigger 2: Failure and Near-Failure Threshold

| Field | Value |
|-------|-------|
| **Condition** | native failure >= 10 AND near-failure >= 10 AND multi-runtime failure coverage >= 3 |
| **Affected candidates** | T-FM-001, T-SC-004, T-SC-005 |
| **Re-evaluation** | Reopen Tier 2 failure/intervention validation. Characterize failure topology. Compare failure vs near-failure internal patterns. Test H-FM-001, H-FM-002, H-IM-001, H-IM-002, H-EV-004, H-EV-005. |
| **Minimum evidence** | Failure topology characterization with denominator, runtime distribution, and task type breakdown |

### Trigger 3: Routed-Prompt Gate Opens

| Field | Value |
|-------|-------|
| **Condition** | routed_prompt_intervention reaches >=5 explicitly tagged sessions with causetrace_tags |
| **Affected candidates** | T-RP-001 |
| **Re-evaluation** | Open routed lane for basic characterization. Compare routed vs native within-lane topology (trend only). Determine whether routed posture produces detectable topology difference. |
| **Minimum evidence** | Routed lane baseline with session count, event count, runtime/task distribution |

### Trigger 4: Controlled Prompt Morphology Expansion

| Field | Value |
|-------|-------|
| **Condition** | controlled_prompt_morphology reaches >=10 sessions with explicit prompt variant tags (A/B/C) |
| **Affected candidates** | T-PM-001 |
| **Re-evaluation** | Characterize per-variant topology. Test whether prompt posture produces detectable topology differences. |
| **Minimum evidence** | Per-variant baseline with session count, event count, and topology distribution |

### Trigger 5: Superpowers Lane Growth

| Field | Value |
|-------|-------|
| **Condition** | superpowers_workflow_intervention reaches >=15 sessions across >=2 runtimes with task annotation |
| **Affected candidates** | T-WI-001, T-SC-003 |
| **Re-evaluation** | Re-run SP lane event density distribution. Compare with native lane within disclosed bounds. Test whether amplification signal holds with diversified runtimes and task types. |
| **Minimum evidence** | SP lane baseline update with runtime and task diversity |

### Trigger 6: Safety-Control Signal Annotation

| Field | Value |
|-------|-------|
| **Condition** | >=10 sessions annotated with safety-control observable signals AND operational definitions for >=3 safety-control signals validated |
| **Affected candidates** | T-SC-001, T-SC-002, T-SC-003, T-SC-004, T-SC-005 |
| **Re-evaluation** | First safety-control morphology baseline. Test whether annotated safety-boundary sessions differ from matched non-safety sessions. Characterize safety-control collapse patterns if observed. Test human intervention as safety-control regime-shift signal. |
| **Minimum evidence** | Safety-control signal baseline with per-signal frequency, lane distribution, and task type association |

### Trigger 7: Per-Runtime Distribution Improvement

| Field | Value |
|-------|-------|
| **Condition** | any single runtime drops below 60% of native strict lane AND >=4 runtimes have >=5 native strict sessions each |
| **Affected candidates** | T-RM-001, T-RM-002, T-RM-003 |
| **Re-evaluation** | Test whether dominant_chain default rate holds per-runtime. Check whether multi_root rate is runtime-dependent. Test whether feature_add → dominant_chain holds across runtimes. |
| **Minimum evidence** | Per-runtime topology distribution with denominator >=5 per runtime |

### Trigger 8: Metadata Sidecar Density Improvement

| Field | Value |
|-------|-------|
| **Condition** | unlabeled sessions drop below 60% of metadata corpus AND intervention lane metadata coverage reaches >=80% for each lane with sessions |
| **Affected candidates** | All (indirect) |
| **Re-evaluation** | Re-run lane-count with reduced unlabeled population. Check whether lane reclassification shifts any baseline numbers. |
| **Minimum evidence** | Updated lane distribution with reduced unlabeled rate |

## Non-Triggers

The following do NOT trigger Phase 4-3:

| Non-trigger | Rationale |
|-------------|-----------|
| Passage of time | Phase 4 advances by evidence, not calendar |
| New literature alone | Literature can inform candidate registration but does not upgrade evidence grade |
| Isolated anecdotal session | Single interesting trace does not establish pattern |
| Single routed or superpowers example | Gate threshold exists for a reason |
| Pressure to enter Phase 5 | Phase 5 is not open; no external schedule applies |
| New hypothesis idea | Phase 4 does not register new hypotheses without a structural gap |
| Tool or runtime release | New runtime support does not itself change morphology evidence |

## How Triggers Are Checked

Trigger checks are manual, not automated. When corpus growth is suspected, run:

```bash
causetrace corpus lane-count
causetrace corpus gate-status
```

Compare against trigger thresholds. If any trigger fires, open Phase 4-3 for the affected candidate set only. Do not re-grade unaffected candidates.

## Partial Phase 4-3

Phase 4-3 does not need to be a complete re-grade of all 12 candidates. A single trigger opens re-evaluation for its affected candidates only. Unaffected candidates retain their current grades.

Example:
- Trigger 2 fires (failure >= 10). Re-evaluate T-FM-001, T-SC-004, T-SC-005. All other candidates unchanged.
- Trigger 3 fires (routed >= 5). Re-evaluate T-RP-001. All other candidates unchanged.

## Trigger Status (2026-06-13)

| Trigger | Condition | Current | Status |
|---------|-----------|---------|--------|
| 1: Native growth | 150+ native strict | 100 | Not met |
| 2: Failure threshold | failure >= 10, near >= 10 | 1 / 5 | Not met |
| 3: Routed gate | >=5 tagged routed | 0 | Not met |
| 4: Controlled expansion | >=10 with variant tags | 3 (no tags) | Not met |
| 5: SP growth | >=15 across >=2 runtimes | 8 / 1 runtime | Not met |
| 6: Safety annotation | >=10 annotated sessions | 0 | Not met |
| 7: Runtime balance | <60% single runtime, >=4 with >=5 | 96% claude-code+opencode | Not met |
| 8: Metadata density | <60% unlabeled, >=80% lane coverage | 88.7% unlabeled | Not met |

No trigger is currently met. Phase 4-3 is waiting.

## Next Check

No scheduled check date. Trigger check is opportunistic — run when corpus growth is noticed or after a significant acquisition batch.
