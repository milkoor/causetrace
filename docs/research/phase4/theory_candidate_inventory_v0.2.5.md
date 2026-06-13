# Phase 4 Theory Candidate Inventory v0.2.5

This document lists all current runtime morphology theory candidates with evidence grades, supporting data, caveats, and falsification conditions. It consolidates Phase 3D hypothesis validation results and Phase 3E intervention-aware findings.

No candidate here is a finalized theory. All are drafts with explicit evidence boundaries.

## Corpus Snapshot

- Date: 2026-06-13
- Metadata sessions: 992
- Data sessions: 1,517
- Events: 131,952
- Runtime breadth: 7
- Task breadth: 9
- Native strict sessions: 100
- Lanes: direct_prompt_native (101), superpowers_workflow_intervention (8), controlled_prompt_morphology (3), routed_prompt_intervention (0)

---

## T-RM-001: Dominant Chain as Default Native Morphology

| Field | Value |
|-------|-------|
| **Claim** | In the current native strict lane, `dominant_chain` is the default runtime morphology. |
| **Evidence grade** | `supported` |
| **Lane** | `direct_prompt_native` |
| **Denominator** | 100 native strict sessions |
| **Supporting data** | 93/100 native strict sessions exhibit dominant_chain topology. |
| **Runtime distribution** | claude-code (50), opencode (46), codex (3), aider (1), Sisyphus (1) — 5 runtimes |
| **Task distribution** | 8 task types represented; feature_add (37), exploration (28), bug_fix (12) are top 3 |
| **Caveats** | Runtime distribution is uneven (claude-code + opencode = 96%). Aider and Sisyphus under-represented. |
| **Falsification condition** | If >=15% of native strict sessions in a new runtime show non-dominant_chain default morphology, this candidate must be qualified per-runtime. |
| **Status** | `active` |
| **Source hypotheses** | H-RM-001 (Phase 3D Tier 1, supported) |

## T-RM-002: Multi-Root Exploration as Minority Morphology

| Field | Value |
|-------|-------|
| **Claim** | `multi_root_exploration` is a minority morphology in native real_work sessions, not a default path. |
| **Evidence grade** | `supported` |
| **Lane** | `direct_prompt_native` |
| **Denominator** | 100 native strict sessions |
| **Supporting data** | 1/100 native strict sessions exhibit multi_root_exploration. |
| **Runtime distribution** | The single multi_root session is opencode. |
| **Task distribution** | N/A (single session) |
| **Caveats** | Low incidence rate may be a property of the current task mix (dominated by feature_add and exploration), not a universal property. |
| **Falsification condition** | If >=5% of native sessions in exploration or review task types show multi_root_exploration, the "minority" claim needs qualification. |
| **Status** | `active` |
| **Source hypotheses** | H-RM-003 (Phase 3D Tier 1, supported) |

## T-RM-003: Feature_Add Tendency Toward Dominant Chain

| Field | Value |
|-------|-------|
| **Claim** | In the current native lane, `feature_add` tasks tend toward `dominant_chain` topology. |
| **Evidence grade** | `supported_with_caveat` |
| **Lane** | `direct_prompt_native` |
| **Denominator** | 37 feature_add sessions in native strict |
| **Supporting data** | 37/37 feature_add sessions exhibit dominant_chain. Branch collapse was not testable (insufficient collapse samples). |
| **Runtime distribution** | Primarily claude-code and opencode |
| **Caveats** | Single topology outcome may be an artifact of task simplicity in the current corpus, not a structural property of feature_add. Branch collapse claim could not be evaluated. |
| **Falsification condition** | If a feature_add session with >=100 events shows non-dominant_chain topology, or if a multi-file feature_add session shows multi_root or branchy topology, the claim must be qualified. |
| **Status** | `active` |
| **Source hypotheses** | H-TT-002 (Phase 3D Tier 1, supported with caveat) |

## T-WI-001: Superpowers Workflow May Amplify Trace Volume

| Field | Value |
|-------|-------|
| **Claim** | `superpowers_workflow_intervention` sessions may exhibit amplified event density and long-chain structure compared to native direct-prompt sessions, but sample size is insufficient for stable comparison. |
| **Evidence grade** | `exploratory` |
| **Lane** | `superpowers_workflow_intervention` |
| **Denominator** | 8 sessions (5 tagged, 3 manual annotation) |
| **Supporting data** | 3 large SP sessions account for 41,221 of 42,465 lane events (avg ~13,740 events/session). Native lane avg: 318 events/session. No formal comparison performed (cross-lane comparison restricted to trend reporting only). |
| **Runtime distribution** | claude-code only (8/8) |
| **Task distribution** | Not annotated for SP lane sessions |
| **Caveats** | Single-runtime. 3 outlier sessions dominate lane metrics. Not a validated finding — exploratory observation only. Must not be generalized to "superpowers always amplifies trace volume." |
| **Falsification condition** | If 10+ additional SP sessions across >=2 runtimes show event density within native range (200-500 events/session), the amplification signal may be an artifact of the 3 large annotation sessions. |
| **Status** | `active` |
| **Source hypotheses** | None direct; derived from Phase 3E-1 lane baseline observation |

## T-FM-001: Failure Morphology Underdetermined

| Field | Value |
|-------|-------|
| **Claim** | Current failure and near-failure sample density is insufficient to characterize failure morphology. Failure topology cannot be typed. |
| **Evidence grade** | `deferred` |
| **Lane** | `direct_prompt_native` |
| **Denominator** | 1 native failure (success=False), 5 near-failure (human_intervention=True) out of 101 native sessions |
| **Supporting data** | 1/101 native failure, 5/101 near-failure. Tier 2 readiness: failure 1/10 NOT MET, near-failure 5/10 NOT MET. |
| **Runtime distribution** | N/A |
| **Task distribution** | N/A |
| **Caveats** | Low failure rate may reflect genuine agent effectiveness for current task types, or insufficient coverage of failure-prone task categories. |
| **Falsification condition** | When native failure >= 10 and near-failure >= 10, re-evaluate. If failure topology is then characterizable, this deferral is resolved. |
| **Status** | `active` |
| **Source hypotheses** | H-FM-001, H-FM-002, H-EV-004, H-EV-005 (Phase 3D Tier 2, all deferred) |

## T-RP-001: Routed-Prompt Morphology Unobserved

| Field | Value |
|-------|-------|
| **Claim** | `routed_prompt_intervention` morphology is currently unobserved. No theory statement can be made about the effect of prompt routing on topology. |
| **Evidence grade** | `deferred` |
| **Lane** | `routed_prompt_intervention` |
| **Denominator** | 0 sessions |
| **Supporting data** | prompt-routing-skill tag emission spec is defined. Capture path exists. 0 tagged sessions in corpus. Parser detection gate BLOCKED. |
| **Runtime distribution** | N/A |
| **Task distribution** | N/A |
| **Caveats** | Absence is a corpus gap, not evidence that routing has no effect. |
| **Falsification condition** | When >=5 routed sessions carry causetrace_tags, gate opens and basic lane characterization can begin. |
| **Status** | `active` |
| **Source hypotheses** | None (lane unpopulated) |

## T-PM-001: Controlled Prompt Morphology at Pilot-Level Evidence

| Field | Value |
|-------|-------|
| **Claim** | Controlled prompt morphology comparison is at pilot-level evidence only. Prompt posture effects on topology are not characterized. |
| **Evidence grade** | `deferred` |
| **Lane** | `controlled_prompt_morphology` |
| **Denominator** | 3 pilot sessions |
| **Supporting data** | 3 sessions, 135 events total, avg 45 events/session. No prompt variant labeling. Parser detection gate BLOCKED. |
| **Runtime distribution** | claude-code only |
| **Task distribution** | Not annotated |
| **Caveats** | Pilot sessions are minimal and lack variant tagging. Cannot distinguish A/B/C prompt postures. |
| **Falsification condition** | When controlled benchmark protocol is operational and >=5 sessions per variant carry prompt tags, re-evaluate. |
| **Status** | `active` |
| **Source hypotheses** | H-EG-001 (Phase 3D Tier 3, deferred) |

---

## Evidence Grade Distribution

| Grade | Count | Candidates |
|-------|-------|------------|
| `supported` | 2 | T-RM-001, T-RM-002 |
| `supported_with_caveat` | 1 | T-RM-003 |
| `exploratory` | 1 | T-WI-001 |
| `deferred` | 3 | T-FM-001, T-RP-001, T-PM-001 |
| `inconclusive` | 0 | — |

## Theory Domain Map

```
Runtime Morphology (T-RM)
├── T-RM-001: dominant_chain as default        [supported]
├── T-RM-002: multi_root as minority            [supported]
└── T-RM-003: feature_add → dominant_chain      [supported_with_caveat]

Workflow Intervention (T-WI)
└── T-WI-001: SP may amplify trace volume       [exploratory]

Failure Morphology (T-FM)
└── T-FM-001: failure morphology underdetermined [deferred]

Routed Prompt (T-RP)
└── T-RP-001: routed-prompt unobserved          [deferred]

Prompt Morphology (T-PM)
└── T-PM-001: controlled prompt pilot-only      [deferred]
```

## Operating Rules

- Do not promote a candidate beyond its evidence grade without new corpus evidence.
- Do not remove deferred candidates — they document gaps, not failures.
- Do not merge T-WI-001 into native morphology conclusions.
- Do not use T-RM-001 as a universal claim — it is scoped to the current native strict lane.
- All deferred candidates carry explicit re-evaluation criteria.
- Negative spaces (T-FM-001, T-RP-001, T-PM-001) are first-class entries.

## What Is NOT Here

- Prediction models or anomaly scorers
- Automatic diagnosis rules
- Universal prompt policy recommendations
- Cross-lane aggregated claims
- Claims without denominators
- Claims without falsification conditions
- Tool-specific topology prescriptions
