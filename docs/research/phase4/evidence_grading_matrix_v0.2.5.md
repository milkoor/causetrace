# Phase 4 Evidence Grading Matrix v0.2.5

Systematic evidence-grade review of all 12 Phase 4 theory candidates. This matrix prevents Phase 4 from accumulating ungraded candidates and ensures every claim carries explicit evidence boundaries, blockers, and promotion conditions.

## Corpus Snapshot

- Date: 2026-06-13
- Metadata sessions: 992
- Data sessions: 1,517
- Events: 131,952
- Runtime breadth: 7
- Task breadth: 9
- Native strict: 100

## Grading Rules

| Grade | Requirement | Typical Denominator |
|-------|-------------|---------------------|
| `supported` | Stable lane evidence, denominator disclosed, runtime/task distribution reported, falsification condition stated | >= 10 in lane, >= 2 runtimes |
| `supported_with_caveat` | Evidence present plus known limitation explicitly stated | Any, with disclosed caveat |
| `exploratory` | Visible signal or literature basis, but denominator insufficient for confidence | < 10 in lane, or single-runtime only |
| `inconclusive` | Tested but evidence insufficient to support or refute | Any |
| `deferred` | Insufficient data, blocked lane, or gated on corpus growth | Any |

Additional rules:
- `literature-informed` alone cannot exceed `exploratory`
- A candidate at `exploratory` must not carry policy or product recommendations
- A candidate at `deferred` must state its re-evaluation condition

---

## Default Morphology (T-RM)

### T-RM-001: dominant_chain as Default Native Morphology

| Field | Value |
|-------|-------|
| **Theory area** | Default morphology |
| **Current evidence grade** | `supported` |
| **Supporting lane** | `direct_prompt_native` |
| **Denominator** | 100 native strict sessions |
| **Evidence source** | Phase 3D Tier 1 (H-RM-001): 93/100 native strict exhibit dominant_chain |
| **Runtime distribution** | claude-code (50), opencode (46), codex (3), aider (1), Sisyphus (1) — 5 runtimes |
| **Task distribution** | 8 task types; top 3: feature_add (37), exploration (28), bug_fix (12) |
| **Current blocker** | None for current grade |
| **Promotion condition** | Not applicable; already at `supported` (highest grade under Phase 4 rules) |
| **Demotion/falsification condition** | If >=15% of sessions in a new runtime show non-dominant_chain default, the claim must be qualified per-runtime |
| **Next action** | Maintain as Phase 4 anchor candidate; update denominator as native lane grows |

### T-RM-002: multi_root_exploration as Minority Morphology

| Field | Value |
|-------|-------|
| **Theory area** | Default morphology |
| **Current evidence grade** | `supported` |
| **Supporting lane** | `direct_prompt_native` |
| **Denominator** | 100 native strict sessions |
| **Evidence source** | Phase 3D Tier 1 (H-RM-003): 1/100 native strict exhibit multi_root_exploration |
| **Runtime distribution** | Single multi_root session: opencode |
| **Task distribution** | N/A (single session) |
| **Current blocker** | None for current grade; low incidence rate may be task-mix dependent |
| **Promotion condition** | Not applicable; already at `supported` |
| **Demotion/falsification condition** | If >=5% of sessions in exploration or review task types show multi_root, the "minority" claim needs qualification by task type |
| **Next action** | Monitor for task-type-specific multi_root emergence as corpus diversifies |

### T-RM-003: feature_add Tendency Toward dominant_chain

| Field | Value |
|-------|-------|
| **Theory area** | Default morphology |
| **Current evidence grade** | `supported_with_caveat` |
| **Supporting lane** | `direct_prompt_native` |
| **Denominator** | 37 feature_add sessions in native strict |
| **Evidence source** | Phase 3D Tier 1 (H-TT-002): 37/37 feature_add → dominant_chain; branch_collapse not testable |
| **Runtime distribution** | Primarily claude-code and opencode |
| **Task distribution** | feature_add only |
| **Current blocker** | Single topology outcome may be artifact of task simplicity; branch_collapse claim untested; other task types not compared |
| **Promotion condition** | Demonstrate that non-feature_add tasks at similar event counts show different topology distribution; test branch_collapse on feature_add sessions with >=100 events |
| **Demotion/falsification condition** | If a feature_add session with >=100 events shows non-dominant_chain topology, or a multi-file feature_add session shows multi_root or branchy topology |
| **Next action** | No change; caveat remains valid; await larger feature_add sessions with branch_collapse candidates |

---

## Workflow Intervention (T-WI)

### T-WI-001: Superpowers Workflow May Amplify Trace Volume

| Field | Value |
|-------|-------|
| **Theory area** | Workflow intervention |
| **Current evidence grade** | `exploratory` |
| **Supporting lane** | `superpowers_workflow_intervention` |
| **Denominator** | 8 sessions (5 tagged, 3 manual annotation) |
| **Evidence source** | Phase 3E-1 lane baseline: 3 large SP sessions (41,221 events) vs native avg (318 events/session). Not a formal comparison. |
| **Runtime distribution** | claude-code only (8/8) — single runtime |
| **Task distribution** | Not annotated for SP lane |
| **Current blocker** | Single runtime; 3 outlier sessions dominate lane metrics; no task annotation; cross-lane comparison restricted to trend reporting |
| **Promotion condition** | >=10 SP sessions across >=2 runtimes with task annotation; formal within-lane event density distribution compared to native; safety-control signal annotation present |
| **Demotion/falsification condition** | If 10+ additional SP sessions across >=2 runtimes show event density within native range (200-500 events/session), the amplification signal may be artifact |
| **Next action** | Maintain at `exploratory`; accumulate tagged SP sessions naturally; annotate task types for SP lane |

---

## Failure Morphology (T-FM)

### T-FM-001: Failure Morphology Underdetermined

| Field | Value |
|-------|-------|
| **Theory area** | Failure morphology |
| **Current evidence grade** | `deferred` |
| **Supporting lane** | `direct_prompt_native` |
| **Denominator** | 1 failure, 5 near-failure (human_intervention=True) out of 101 native |
| **Evidence source** | Phase 3D Tier 2 deferral; Phase 3E closure Tier 2 readiness check NOT MET |
| **Runtime distribution** | N/A (insufficient samples) |
| **Task distribution** | N/A |
| **Current blocker** | Tier 2 criteria not met: native failure 1/10, near-failure 5/10 |
| **Promotion condition** | Native failure >= 10 AND near-failure >= 10 AND multi-runtime failure coverage >= 3 |
| **Demotion/falsification condition** | Not applicable; candidate is the absence of evidence, not a positive claim |
| **Next action** | Background acquisition; re-check Tier 2 readiness quarterly; consider expanding near-failure definition beyond human_intervention=True |

---

## Prompt and Routing Morphology (T-RP, T-PM)

### T-RP-001: Routed-Prompt Morphology Unobserved

| Field | Value |
|-------|-------|
| **Theory area** | Prompt and routing morphology |
| **Current evidence grade** | `deferred` |
| **Supporting lane** | `routed_prompt_intervention` |
| **Denominator** | 0 sessions |
| **Evidence source** | Phase 3E-2 annotation pass: 0 routed candidates; Phase 3E-3: tag spec defined, no tagged sessions captured |
| **Runtime distribution** | N/A |
| **Task distribution** | N/A |
| **Current blocker** | Parser detection gate BLOCKED; 0 tagged sessions; prompt-routing-skill tag emission not yet captured in corpus |
| **Promotion condition** | >=5 tagged routed sessions with causetrace_tags; gate OPEN; basic lane characterization complete |
| **Demotion/falsification condition** | Not applicable; candidate is the absence of observation |
| **Next action** | Upstream: prompt-routing-skill tag emission testing; causetrace-side: gate-status monitoring |

### T-PM-001: Controlled Prompt Morphology at Pilot-Level Evidence

| Field | Value |
|-------|-------|
| **Theory area** | Prompt and routing morphology |
| **Current evidence grade** | `deferred` |
| **Supporting lane** | `controlled_prompt_morphology` |
| **Denominator** | 3 pilot sessions, 135 events |
| **Evidence source** | Phase 3E-1 baseline: 3 sessions with data_origin=controlled_benchmark, no prompt variant labeling |
| **Runtime distribution** | claude-code only |
| **Task distribution** | Not annotated |
| **Current blocker** | Parser detection gate BLOCKED; no variant tagging (A/B/C); controlled benchmark protocol not operational |
| **Promotion condition** | Controlled benchmark protocol operational; >=5 sessions per prompt variant with tags; task annotation present |
| **Demotion/falsification condition** | If pilot expansion shows no detectable topology difference across prompt variants, the prompt-posture-as-topology-variable hypothesis is not supported |
| **Next action** | Define controlled benchmark protocol; implement prompt variant tagging |

---

## Safety-Control Morphology (T-SC)

### T-SC-001: Safety-Control Boundaries May Alter Runtime Topology

| Field | Value |
|-------|-------|
| **Theory area** | Safety-control morphology |
| **Current evidence grade** | `exploratory` |
| **Supporting lane** | `direct_prompt_native` (initial) |
| **Denominator** | TBD — requires sessions with identifiable safety-control boundaries |
| **Evidence source** | Literature-informed. No causetrace corpus evidence yet. |
| **Runtime distribution** | N/A |
| **Task distribution** | N/A |
| **Current blocker** | No sessions annotated with safety-control boundary markers; need_review_triggered not instrumented; safety-relevant task types not isolated |
| **Promotion condition** | >=10 sessions with annotated safety-control boundaries; comparison with matched non-safety tasks shows detectable difference in AskUserQuestion rate, branch_collapse rate, or chain length |
| **Demotion/falsification condition** | If sessions with explicit safety boundaries show no detectable topology difference from matched non-safety tasks, the tool-call-level signal may be too weak |
| **Next action** | Identify sessions with safety-relevant task characteristics; annotate pilot set with candidate observable signals |

### T-SC-002: Task-Completion Pressure May Produce Safety-Control Collapse

| Field | Value |
|-------|-------|
| **Theory area** | Safety-control morphology |
| **Current evidence grade** | `exploratory` |
| **Supporting lane** | All lanes (comparative, future) |
| **Denominator** | TBD — requires identification of safety-control collapse patterns |
| **Evidence source** | Literature-informed (frontier-model safety incident reports). No causetrace corpus evidence yet. |
| **Runtime distribution** | N/A |
| **Task distribution** | N/A |
| **Current blocker** | No operational definition of safety-control collapse at tool-call level; no annotated collapse sessions; no baseline rate established |
| **Promotion condition** | Operational definition of safety-control collapse validated on >=5 sessions; collapse rate compared across >=2 lanes; denominator disclosed |
| **Demotion/falsification condition** | If agents consistently stop at safety boundaries regardless of task pressure in annotated sessions, the collapse model is not supported |
| **Next action** | Develop operational definition of safety-control collapse using observable tool-call patterns; pilot-annotate on automatic-signature sessions |

### T-SC-003: Workflow Intervention May Reduce Unsafe Continuation

| Field | Value |
|-------|-------|
| **Theory area** | Safety-control morphology |
| **Current evidence grade** | `exploratory` |
| **Supporting lane** | `superpowers_workflow_intervention` vs `direct_prompt_native` (trend only) |
| **Denominator** | 8 SP sessions, 101 native sessions |
| **Evidence source** | Phase 3E lane baseline (SP event density observation); T-WI-001 (exploratory) |
| **Runtime distribution** | SP: claude-code only; Native: 5 runtimes |
| **Task distribution** | Not comparable (SP task types not annotated) |
| **Current blocker** | Single-runtime SP lane; no safety-control signal annotation on either lane; cross-lane comparison restricted to trend reporting; denominator asymmetry (8 vs 101) |
| **Promotion condition** | Safety-control signal annotation on >=10 sessions per lane; >=2 runtimes in SP lane; cross-lane comparison protocol followed |
| **Demotion/falsification condition** | If SP sessions show same or higher rate of safety-control-relevant signals (unsafe_continuation, retry_after_uncertainty) as native sessions |
| **Next action** | Defer until SP lane has task annotation, runtime diversity, and safety-control signal annotation |

### T-SC-004: Human Intervention as External Safety-Control Signal

| Field | Value |
|-------|-------|
| **Theory area** | Safety-control morphology |
| **Current evidence grade** | `exploratory` |
| **Supporting lane** | `direct_prompt_native` (human_intervention=True subset) |
| **Denominator** | 5 native sessions with human_intervention=True |
| **Evidence source** | Phase 3D Tier 2 (H-IM-001, H-IM-002, H-EV-005 — all deferred); literature on human-in-the-loop safety |
| **Runtime distribution** | claude-code primarily |
| **Task distribution** | Not isolated |
| **Current blocker** | 5-session denominator; human_intervention field captures presence not type; no distinction between safety-driven vs task-driven intervention; no pre/post topology comparison |
| **Promotion condition** | >=10 human_intervention sessions with annotated intervention type (safety-correction vs task-correction); pre/post intervention topology comparison shows detectable regime shift |
| **Demotion/falsification condition** | If human-intervention sessions show same pre/post topology as self-correction (tool error → retry) sessions, human intervention is not a distinguishable regime-shift signal |
| **Next action** | Annotate human_intervention sessions with intervention type; compare pre/post topology within session |

### T-SC-005: Near-Failure and Safety-Control Recovery More Informative Than Final Labels

| Field | Value |
|-------|-------|
| **Theory area** | Safety-control morphology |
| **Current evidence grade** | `exploratory` |
| **Supporting lane** | `direct_prompt_native` |
| **Denominator** | 5 near-failure (human_intervention=True), 1 failure (success=False) |
| **Evidence source** | Phase 3D Tier 2 deferral observation (failure genuinely rare); Phase 3E closure Tier 2 readiness check |
| **Runtime distribution** | claude-code primarily |
| **Task distribution** | Not isolated |
| **Current blocker** | Near-failure definition limited to human_intervention=True; no internal near-failure signal instrumentation; small denominator; no comparison with clean-success internal patterns |
| **Promotion condition** | Expanded near-failure definition (human_intervention + internal signals like retry density, late-stage correction, AskUserQuestion clusters); >=10 near-failure sessions; internal pattern comparison with matched clean-success sessions |
| **Demotion/falsification condition** | If near-failure sessions show no detectable difference from clean-success sessions in internal correction patterns, retry density, or safety-signal frequency, near-failure may not capture safety-relevant information |
| **Next action** | Define expanded near-failure criteria; pilot-annotate near-failure patterns; compare internal topology with clean-success sessions |

---

## Matrix Summary

| Candidate ID | Area | Grade | Denominator | Blocker | Promotion Target |
|-------------|------|-------|-------------|---------|-----------------|
| T-RM-001 | Default morphology | `supported` | 100 | None | N/A (at ceiling) |
| T-RM-002 | Default morphology | `supported` | 100 | None | N/A (at ceiling) |
| T-RM-003 | Default morphology | `supported_with_caveat` | 37 | Branch_collapse untested | Multi-task comparison |
| T-WI-001 | Workflow intervention | `exploratory` | 8 | Single-runtime, no task annotation | >=10 SP across >=2 runtimes |
| T-FM-001 | Failure morphology | `deferred` | 1 failure / 5 near | Tier 2 criteria not met | failure >=10, near-failure >=10 |
| T-RP-001 | Prompt/routing | `deferred` | 0 | Gate BLOCKED | >=5 tagged routed sessions |
| T-PM-001 | Prompt/routing | `deferred` | 3 pilot | No variant tagging, no protocol | Controlled benchmark operational |
| T-SC-001 | Safety-control | `exploratory` | TBD | No annotated safety-boundary sessions | >=10 annotated sessions |
| T-SC-002 | Safety-control | `exploratory` | TBD | No operational collapse definition | >=5 annotated collapse sessions |
| T-SC-003 | Safety-control | `exploratory` | 8 vs 101 | Lane asymmetry, no safety annotation | Safety annotation on >=10/lane |
| T-SC-004 | Safety-control | `exploratory` | 5 | Small denominator, no intervention typing | >=10 typed intervention sessions |
| T-SC-005 | Safety-control | `exploratory` | 5 near / 1 fail | Near-failure definition narrow | Expanded near-failure >=10 |

## Grade Distribution

| Grade | Count | Candidates |
|-------|-------|------------|
| `supported` | 2 | T-RM-001, T-RM-002 |
| `supported_with_caveat` | 1 | T-RM-003 |
| `exploratory` | 6 | T-WI-001, T-SC-001 through T-SC-005 |
| `inconclusive` | 0 | — |
| `deferred` | 3 | T-FM-001, T-RP-001, T-PM-001 |

## Blocker Summary

| Blocker Type | Affected Candidates | Resolution Path |
|-------------|---------------------|-----------------|
| Insufficient lane samples | T-FM-001, T-RP-001, T-PM-001 | Background acquisition; gate monitoring |
| Single-runtime limitation | T-WI-001, T-SC-003 | Natural SP lane diversification |
| No safety annotation | T-SC-001 through T-SC-005 | Pilot annotation on safety-relevant sessions |
| No operational definitions | T-SC-002, T-SC-005 | Define collapse and near-failure criteria |
| No task annotation | T-WI-001, T-PM-001, T-SC-003 | Task type annotation pass |

## Phase 4 Current Ceiling

The evidence ceiling for Phase 4 is currently `supported` (not "validated" or "confirmed"). No candidate can exceed this grade under Phase 4 rules. The two `supported` candidates (T-RM-001, T-RM-002) remain scoped to the current native strict lane and corpus snapshot — they are not universal claims.

## Next Grading Pass

Schedule next grading pass when:
- Native lane reaches 150+ sessions
- SP lane reaches 15+ sessions across >=2 runtimes
- Safety-control pilot annotation complete on >=10 sessions
- Routed lane gate opens
- Controlled benchmark protocol produces first tagged sessions

No date commitment. Grading passes are triggered by corpus growth, not calendar.
