# Runtime Morphology Theory Draft v0.1

**Status**: Draft. Evidence-graded. Not final theory.

This document consolidates all 12 Phase 4 theory candidates into a single structured draft. It separates current supported claims from caveated claims, exploratory directions, and deferred claims. It does not publish conclusions. It does not recommend policy.

## Corpus Snapshot

2026-06-13. 992 metadata sessions, 1,517 data sessions, 131,952 events. 7 runtimes, 9 task types. Native strict: 100 sessions. Lanes: `direct_prompt_native` (101), `superpowers_workflow_intervention` (8), `controlled_prompt_morphology` (3), `routed_prompt_intervention` (0).

---

## 1. Current Supported Claims

These claims have the strongest evidence in the current corpus. They are scoped to the `direct_prompt_native` lane and the current corpus snapshot. They are not universal claims.

### T-RM-001: dominant_chain as Default Native Morphology

| Field | Value |
|-------|-------|
| **Claim** | In the current native strict lane, `dominant_chain` is the default runtime morphology. |
| **Grade** | `supported` |
| **Lane** | `direct_prompt_native` |
| **Denominator** | 100 native strict sessions |
| **Evidence** | 93/100 native strict sessions exhibit dominant_chain. 5 runtimes represented (claude-code, opencode, codex, aider, Sisyphus). 8 task types. |
| **Caveats** | Runtime distribution uneven (claude-code + opencode = 96%). Aider and Sisyphus under-represented (1 session each). |
| **Falsification** | If >=15% of sessions in a new runtime show non-dominant_chain default morphology, the claim must be qualified per-runtime. |

### T-RM-002: multi_root_exploration as Minority Morphology

| Field | Value |
|-------|-------|
| **Claim** | `multi_root_exploration` is a minority morphology in native real_work sessions, not a default path. |
| **Grade** | `supported` |
| **Lane** | `direct_prompt_native` |
| **Denominator** | 100 native strict sessions |
| **Evidence** | 1/100 native strict sessions exhibit multi_root_exploration. Single session is opencode. |
| **Caveats** | Low incidence may be task-mix dependent (current corpus dominated by feature_add and exploration). Not necessarily a universal property. |
| **Falsification** | If >=5% of exploration or review sessions show multi_root, the "minority" claim needs task-type qualification. |

---

## 2. Caveated Claims

These claims have supporting evidence but carry explicit limitations that prevent them from reaching `supported`.

### T-RM-003: feature_add Tendency Toward dominant_chain

| Field | Value |
|-------|-------|
| **Claim** | In the current native lane, `feature_add` tasks tend toward `dominant_chain` topology. |
| **Grade** | `supported_with_caveat` |
| **Lane** | `direct_prompt_native` |
| **Denominator** | 37 feature_add sessions in native strict |
| **Evidence** | 37/37 feature_add sessions exhibit dominant_chain. |
| **Why caveated** | Branch_collapse claim could not be tested. Single topology outcome may be artifact of task simplicity, not structural property of feature_add. Other task types not systematically compared. |
| **Falsification** | If a feature_add session with >=100 events shows non-dominant_chain, or a multi-file feature_add shows multi_root or branchy topology, the claim must be qualified. |

---

## 3. Exploratory Directions

These directions have visible signals or literature support, but denominators are insufficient for confidence. None support policy, product, or strategy recommendations.

### T-WI-001: Superpowers Workflow May Amplify Trace Volume

| Field | Value |
|-------|-------|
| **Claim** | `superpowers_workflow_intervention` sessions may exhibit amplified event density and long-chain structure compared to native direct-prompt sessions. |
| **Grade** | `exploratory` |
| **Denominator** | 8 SP sessions (5 tagged, 3 manual annotation) |
| **Blocker** | Single runtime (claude-code). 3 outlier sessions dominate lane metrics. No task annotation. Cross-lane comparison restricted to trends. |
| **Promotion** | >=10 SP sessions across >=2 runtimes with task annotation and formal within-lane event density distribution. |

### T-SC-001: Safety-Control Boundaries May Alter Runtime Topology

| Field | Value |
|-------|-------|
| **Claim** | Safety-control boundaries such as need_review, hard-stop, and fallback rules may alter runtime morphology by increasing explicit stopping, clarification requests, or branch-collapse behavior. |
| **Grade** | `exploratory` |
| **Denominator** | TBD — no sessions annotated with safety-control boundary markers |
| **Blocker** | No annotated safety-boundary sessions. need_review_triggered not instrumented. Safety-relevant task types not isolated. |
| **Promotion** | >=10 sessions with annotated safety-control boundaries; comparison with matched non-safety tasks shows detectable difference. |

### T-SC-002: Task-Completion Pressure May Produce Safety-Control Collapse

| Field | Value |
|-------|-------|
| **Claim** | When task-completion pressure conflicts with safety-control boundaries, agents may exhibit safety-control collapse: continuing toward completion despite uncertainty, missing evidence, or required human review. |
| **Grade** | `exploratory` |
| **Denominator** | TBD — no operational collapse definition or annotated collapse sessions |
| **Blocker** | No operational definition of safety-control collapse at tool-call level. No annotated collapse sessions. No baseline rate. |
| **Promotion** | Operational collapse definition validated on >=5 sessions; collapse rate compared across >=2 lanes. |

### T-SC-003: Workflow Intervention May Reduce Unsafe Continuation

| Field | Value |
|-------|-------|
| **Claim** | Workflow interventions such as staged verification, routed constrained prompts, or superpowers-style workflows may reduce unsafe continuation, but may increase event_count and trace length. |
| **Grade** | `exploratory` |
| **Denominator** | 8 SP vs 101 native (asymmetric; trend reporting only) |
| **Blocker** | Single-runtime SP lane. No safety-control signal annotation. Cross-lane comparison restricted to trends. |
| **Promotion** | Safety-control signal annotation on >=10 sessions per lane; >=2 runtimes in SP lane. |

### T-SC-004: Human Intervention as External Safety-Control Signal

| Field | Value |
|-------|-------|
| **Claim** | Human intervention may function as an external safety-control signal that induces topology regime shifts distinguishable from self-correction patterns. |
| **Grade** | `exploratory` |
| **Denominator** | 5 native sessions with human_intervention=True |
| **Blocker** | 5-session denominator. No intervention type annotation (safety-correction vs task-correction). No pre/post topology comparison. |
| **Promotion** | >=10 human_intervention sessions with annotated intervention type; detectable regime shift in pre/post comparison. |

### T-SC-005: Near-Failure More Informative Than Final Labels

| Field | Value |
|-------|-------|
| **Claim** | Near-failure and safety-control recovery patterns may be more informative than final success/failure labels for understanding agent safety behavior. |
| **Grade** | `exploratory` |
| **Denominator** | 5 near-failure (human_intervention=True), 1 failure (success=False) |
| **Blocker** | Near-failure definition limited to human_intervention=True. Small denominator. No internal pattern comparison with clean-success sessions. |
| **Promotion** | Expanded near-failure definition; >=10 near-failure sessions; internal pattern comparison with matched clean-success sessions. |

---

## 4. Deferred Claims

These claims cannot be evaluated against the current corpus. They are deferred, not falsified.

### T-FM-001: Failure Morphology Underdetermined

| Field | Value |
|-------|-------|
| **Claim** | Current failure and near-failure sample density is insufficient to characterize failure morphology. |
| **Grade** | `deferred` |
| **Why deferred** | Tier 2 criteria not met: native failure 1/10, near-failure 5/10. |
| **Reopen condition** | Native failure >= 10 AND near-failure >= 10 AND multi-runtime failure coverage >= 3. |

### T-RP-001: Routed-Prompt Morphology Unobserved

| Field | Value |
|-------|-------|
| **Claim** | `routed_prompt_intervention` morphology is currently unobserved. No theory statement can be made. |
| **Grade** | `deferred` |
| **Why deferred** | 0 tagged routed sessions. Parser detection gate BLOCKED. |
| **Reopen condition** | >=5 tagged routed sessions with causetrace_tags; gate OPEN. |

### T-PM-001: Controlled Prompt Morphology at Pilot-Level Evidence

| Field | Value |
|-------|-------|
| **Claim** | Controlled prompt morphology comparison is at pilot-level evidence only. Prompt posture effects on topology are not characterized. |
| **Grade** | `deferred` |
| **Why deferred** | 3 pilot sessions with no variant tagging. Controlled benchmark protocol not operational. Gate BLOCKED. |
| **Reopen condition** | Controlled benchmark protocol operational; >=5 sessions per variant with prompt tags. |

---

## 5. Theory Boundaries

Visible trace length and natural-language rationale density should not be treated as complete proxies for reasoning depth. Future agents may shift reasoning or coordination into compressed or opaque communication channels. Prompt-level compression and structured `machine_state` remain observable text artifacts, while true hidden-state, embedding, or KV-cache transfer would require separate instrumentation. `causetrace` therefore interprets topology as observable runtime morphology, not full internal cognition.

This draft explicitly does NOT support:

| Exclusion | Rationale |
|-----------|-----------|
| Prediction of agent behavior | No model trained; claims are descriptive, not predictive |
| Anomaly detection | No baseline distribution for "normal" morphology across all conditions |
| Automatic diagnosis | Morphology interpretation is contextual, not automatable |
| Universal prompt policy | No evidence that isolated findings generalize across runtimes/tasks |
| Routing default strategy | Routed lane has 0 sessions; no comparison basis |
| Safety-control automation | All T-SC candidates are `exploratory`; no operational definitions validated |
| Cross-lane aggregation without disclosure | Violates Phase 3E lane separation rules |
| Promotion of `exploratory` or `deferred` claims | Violates evidence grading rules |

---

## 6. Known Blockers

| Blocker | Affected Candidates | Resolution |
|---------|---------------------|------------|
| Failure sample scarcity | T-FM-001 | Background acquisition; no timeline commitment |
| Near-failure density | T-FM-001, T-SC-005 | Expand near-failure definition; pilot annotation |
| Routed lane absence | T-RP-001 | Upstream prompt-routing-skill tag emission testing |
| Controlled benchmark gap | T-PM-001 | Define and operationalize benchmark protocol |
| Intervention lane small denominators | T-WI-001, T-SC-003 | Natural accumulation; no forced data generation |
| Single-runtime SP lane | T-WI-001, T-SC-003 | Natural diversification |
| No safety-control annotation | T-SC-001 through T-SC-005 | Pilot annotation on safety-relevant session subset |
| No operational collapse definition | T-SC-002 | Define using observable tool-call patterns |
| No task annotation for intervention lanes | T-WI-001, T-PM-001 | Task type annotation pass (low priority) |
| Per-runtime imbalance | T-RM-001, T-RM-002 | Natural diversification; monitor per-runtime |

---

## 7. Evidence Upgrade Path

| From | To | Required |
|------|----|----------|
| `deferred` | `exploratory` | Gate condition met (denominator threshold, tag accumulation, or protocol operational) |
| `exploratory` | `supported_with_caveat` | Denominator >= 10 in lane, >= 2 runtimes, task annotation present, blocker resolved |
| `supported_with_caveat` | `supported` | Caveat resolved with additional evidence; multi-condition comparison complete |
| `supported` | — | Ceiling. No higher grade under Phase 4 rules. |

Upgrades are triggered by corpus growth, not calendar. No upgrade is automatic.

---

## 8. Maintenance

This draft is a living document. Update when:

- Corpus snapshot changes materially (next grading pass trigger)
- A gate opens (routed or controlled lanes reach threshold)
- A new blocker is identified or an existing blocker is resolved
- A candidate is promoted, demoted, or falsified
- A structural evidence gap is filled (safety-control annotation, task annotation, runtime diversification)

Do NOT update to add new theory candidates without a grading pass that identifies a genuine structural gap.

---

## References

- [Evidence Grading Matrix](evidence_grading_matrix_v0.2.5.md) — Full candidate details with individual blocker/promotion/falsification records
- [Theory Candidate Inventory](theory_candidate_inventory_v0.2.5.md) — Original candidate definitions and domain map
- [Safety-Control Runtime Morphology](safety_control_morphology_candidates_v0.2.5.md) — Full T-SC candidate definitions, observable signals, non-goals
- [Phase 3D Closure Report](../phase3d/closure_report_v0.2.5.md) — Hypothesis registry and Tier 1 validation
- [Phase 3E Closure Report](../phase3e/closure_report_v0.2.5.md) — Intervention lane infrastructure and Tier 2 deferral
