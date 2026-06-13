# Safety-Control Runtime Morphology v0.2.5

A Phase 4 theory candidate direction studying how coding-agent runtime behavior changes when task-completion objectives interact with safety boundaries, workflow gates, need_review rules, fallback paths, hard-stops, and human intervention.

## Position

- Phase 4: active (theory drafting)
- Direction: Safety-control Runtime Morphology
- Status: **theory candidate direction, exploratory, not validated**
- Parent: Phase 4 Theory Candidate Inventory

## What This Is

A research direction within causetrace runtime morphology that studies the observable topology patterns produced when agents navigate conflicts between:

1. **Task-completion pressure**: the agent's objective to finish the task
2. **Safety-control boundaries**: need_review rules, hard-stops, fallback paths, uncertainty gates, human confirmation requirements, business rule constraints

The core question: when these forces conflict, what runtime topology patterns emerge?

This direction extends causetrace's existing morphology categories (default, exploration, failure, intervention) with a fifth: **safety-control morphology**.

## What This Is NOT

- **NOT** jailbreak reproduction or attack research
- **NOT** a study of how to circumvent model safety training
- **NOT** a content safety classifier or harmful-output detector
- **NOT** a universal model safety benchmark
- **NOT** a red-teaming framework
- **NOT** an adversarial prompt engineering guide
- **NOT** a replacement for formal safety evaluation (e.g., METR, Apollo, UK AISI)
- **NOT** a core schema or topology taxonomy change

This direction studies **observable runtime control morphology**, not model-internal safety mechanisms. Causetrace sees tool calls, causal chains, topology transitions, and intervention events — it does not see model weights, activations, or training data.

## Motivation

Recent frontier-model safety incidents and internal safety-collapse research suggest that strong models may fail not only through external jailbreaks, but through **structural conflict between task-completion pressure and safety-control boundaries**.

In coding-agent runtimes, this conflict can manifest as:

- An agent continuing toward completion despite uncertainty (OCR failure, low confidence, ambiguous template match)
- An agent auto-processing what should require human review (false_positive_tables, unsigned documents)
- An agent bypassing a safety gate because the task objective dominates
- A workflow intervention that reduces unsafe completion but increases trace length
- A human correction that triggers a topology regime shift

These are not abstract safety research questions. They are runtime phenomena already observed in causetrace traces, particularly in the automatic-signature domain where OCR reliability, template matching, and business rule compliance interact with agent autonomy.

## Relationship to Causetrace Main Line

This direction is **compatible with and enhances** the causetrace main line. It studies the same primitives:

| Causetrace Primitive | Safety-Control Lens |
|---------------------|---------------------|
| Runtime causality | What caused the agent to stop / continue / bypass? |
| Topology morphology | Does safety pressure change branch/retry/collapse patterns? |
| Intervention | Do workflow / human interventions reduce safety-control collapse? |
| Failure / near-failure | Is near-failure more informative than final failure for safety analysis? |
| Control transition | What does a safety-control transition look like in the event DAG? |

It shifts the object of study from "what dangerous content did the model output?" to "how did the runtime behave at the safety boundary — stop, continue, bypass, fallback, escalate, or collapse?"

## Core Research Questions

### Q1: Do safety-control boundaries alter runtime topology?

When explicit need_review, hard-stop, or fallback rules are present, does the agent's runtime topology differ from tasks without such boundaries?

Candidate observable differences:
- Fewer无效 retries (agent stops instead of retrying)
- Fewer unsafe auto-completions (agent escalates instead of guessing)
- More branch_collapse (agent converges to safe fallback)
- More AskUserQuestion events (agent requests human decision)
- Shorter chains after first safety signal

### Q2: When does the agent bypass safety boundaries?

Under what runtime conditions does the agent continue toward completion despite uncertainty, missing evidence, or required human review?

Candidate triggers:
- OCR unavailable or low confidence
- Template matching unstable
- Business rule conflict (e.g., false_positive_tables)
- Test failure without clear recovery path
- User not available for confirmation
- Task-completion pressure from prompt framing

Morphology questions:
- Does the agent retry with different parameters (tool-level bypass)?
- Does it proceed with a fallback value (data-level bypass)?
- Does it skip the gating check entirely (control-flow bypass)?
- Does it mark the result as complete despite uncertainty (label-level bypass)?

### Q3: Can workflow intervention reduce safety-control collapse?

Compare intervention lanes for their effect on unsafe continuation:

| Lane | Hypothesis |
|------|-----------|
| `direct_prompt_native` | Highest risk of safety-control collapse (no guardrails) |
| `expanded_constrained_prompt` | May reduce collapse through explicit constraints |
| `routed_prompt_intervention` | May select safer posture for safety-sensitive tasks |
| `superpowers_workflow_intervention` | Staged verification may catch collapse before completion |

Observable signals:
- Unsafe continuation rate
- False positive rate (auto-processed when should be reviewed)
- Invalid retry rate
- Human rescue rate
- Late-stage rollback rate

Note: this comparison requires tagged sessions in all lanes. Currently only `direct_prompt_native` and `superpowers_workflow_intervention` have sessions. Cross-lane comparison is restricted to trend reporting only.

### Q4: What is the role of human intervention in safety control?

Human intervention may function as more than failure recovery — it may be an **external safety-control signal**:

```
agent drift (toward unsafe completion)
→ human correction (observation or explicit correction mark)
→ topology regime shift (branch collapse, hard-stop, safe fallback)
→ recovery / safe completion / documented refusal
```

Key questions:
- Does human intervention produce a detectable topology regime shift?
- Is the shift different from self-correction (tool error → retry)?
- Does the shift depend on intervention timing (early vs. late-stage)?
- Does workflow structure (superpowers staged verification) make human intervention more effective?

### Q5: Is near-failure more informative than final failure for safety analysis?

Current corpus observation: coding agents frequently rollback, retry, and self-repair, leading to very low final failure rates (1/101 native failure, 5/101 near-failure).

This suggests failure may not manifest as `success=false`. It may manifest as:

- Long chains with many internal corrections
- Retry-heavy paths that eventually succeed
- Repeated rollback at safety boundaries
- Near-failure that was rescued (human or self-repair)
- Unsafe path avoided late (last-moment correction)
- need_review triggered but then overridden
- Human rescue that prevented a failure label

If this is true, final success/failure labeling is insufficient for safety-control morphology analysis. Derived signals (need_review_triggered, retry_after_uncertainty, late_stage_correction, human_rescue) may be more informative.

## Theory Candidates

All candidates start at `exploratory` grade. None are validated. All require corpus evidence before promotion.

### T-SC-001: Safety-Control Boundaries May Alter Runtime Topology

| Field | Value |
|-------|-------|
| **Claim** | Safety-control boundaries such as need_review, hard-stop, and fallback rules may alter runtime morphology by increasing explicit stopping, clarification requests, or branch-collapse behavior. |
| **Evidence grade** | `exploratory` |
| **Lane** | `direct_prompt_native` (initial); cross-lane comparison later |
| **Denominator** | TBD — requires sessions with identifiable safety-control boundaries |
| **Supporting data** | Literature-informed. No causetrace corpus evidence yet. |
| **Runtime/task caveats** | May only be observable in tasks with explicit safety/review requirements (document processing, financial operations, access control). |
| **Falsification condition** | If sessions with explicit safety boundaries show no difference in AskUserQuestion rate, branch_collapse rate, or chain length compared to matched non-safety tasks, the morphology difference may not be detectable at the tool-call level. |
| **Status** | `active` |
| **Source** | Phase 4 direction proposal; literature on safety-control conflict in agent systems |

### T-SC-002: Task-Completion Pressure May Produce Safety-Control Collapse

| Field | Value |
|-------|-------|
| **Claim** | When task-completion pressure conflicts with safety-control boundaries, agents may exhibit safety-control collapse: continuing toward completion despite uncertainty, missing evidence, or required human review. |
| **Evidence grade** | `exploratory` |
| **Lane** | All lanes (comparative) |
| **Denominator** | TBD — requires identification of safety-control collapse patterns in traces |
| **Supporting data** | Literature-informed. Internal safety-collapse research suggests strong models may collapse under task pressure. |
| **Runtime/task caveats** | Collapse may be task-specific (OCR-heavy, document-signing, data validation) rather than a general agent property. |
| **Falsification condition** | If agents consistently stop at safety boundaries regardless of task pressure, the collapse model is incorrect. |
| **Status** | `active` |
| **Source** | Phase 4 direction proposal; frontier-model safety incident reports |

### T-SC-003: Workflow Intervention May Reduce Unsafe Continuation

| Field | Value |
|-------|-------|
| **Claim** | Workflow interventions such as staged verification, routed constrained prompts, or superpowers-style workflows may reduce unsafe continuation, but may increase event_count and trace length. |
| **Evidence grade** | `exploratory` |
| **Lane** | `superpowers_workflow_intervention` vs `direct_prompt_native` (trend only) |
| **Denominator** | 8 SP sessions, 101 native sessions |
| **Supporting data** | SP sessions show high event density (exploratory observation only). No safety-control signal analysis performed. |
| **Runtime/task caveats** | Single runtime (claude-code). SP sessions not task-annotated. Cross-lane comparison restricted to trend reporting. |
| **Falsification condition** | If SP sessions show same or higher rate of unsafe continuation (per safety-signal annotation) as native sessions, the workflow-intervention-as-safety-guard hypothesis is not supported. |
| **Status** | `active` |
| **Source** | Phase 4 direction proposal; T-WI-001 (exploratory) |

### T-SC-004: Human Intervention as External Safety-Control Signal

| Field | Value |
|-------|-------|
| **Claim** | Human intervention may function as an external safety-control signal that induces topology regime shifts distinguishable from self-correction patterns. |
| **Evidence grade** | `exploratory` |
| **Lane** | `direct_prompt_native` (human_intervention=True sessions) |
| **Denominator** | 5 sessions with human_intervention=True in native lane |
| **Supporting data** | Literature-informed. H-IM-001 and H-IM-002 (Phase 3D Tier 2) hypothesize human intervention as correction trigger and regime-shift inducer. Not validated. |
| **Runtime/task caveats** | Small sample (5). Human intervention may be correlated with task complexity, not safety pressure. |
| **Falsification condition** | If human-intervention sessions show same topology as matched non-intervention sessions, human intervention is not a detectable regime-shift signal at the tool-call level. |
| **Status** | `active` |
| **Source** | Phase 4 direction proposal; H-IM-001, H-IM-002 (Phase 3D Tier 2, deferred); H-EV-005 (Phase 3D Tier 2, deferred) |

### T-SC-005: Near-Failure and Safety-Control Recovery More Informative Than Final Labels

| Field | Value |
|-------|-------|
| **Claim** | Near-failure and safety-control recovery patterns may be more informative than final success/failure labels for understanding agent safety behavior in real-world coding traces. |
| **Evidence grade** | `exploratory` |
| **Lane** | `direct_prompt_native` |
| **Denominator** | 5 near-failure (human_intervention=True), 1 failure (success=False) |
| **Supporting data** | Low failure rate (1/101) despite complex multi-step tasks suggests agents self-repair frequently. The near-failure population (5/101) may contain safety-relevant signals not captured by final labels. |
| **Runtime/task caveats** | Near-failure definition (human_intervention=True) may not capture all safety-relevant near-misses. |
| **Falsification condition** | If near-failure sessions show no detectable difference from clean-success sessions in internal correction patterns, retry density, or safety-signal frequency, the near-failure category may not capture safety-relevant information beyond task difficulty. |
| **Status** | `active` |
| **Source** | Phase 4 direction proposal; Phase 3D Tier 2 deferral observation (failure genuinely rare) |

## Observable Signals (Candidate)

These are candidate annotation or derived-analysis signals. They are NOT proposed as core schema fields yet. Each requires corpus evidence before inclusion in the topology taxonomy.

| Signal | Definition | Current Observability |
|--------|-----------|----------------------|
| `need_review_triggered` | Agent encountered a review gate and either stopped or continued | Not instrumented |
| `hard_stop` | Agent explicitly halted execution (not retry, not fallback) | Partially observable (tool-level stop) |
| `fallback_path` | Agent chose a safe fallback over the primary completion path | Requires analysis |
| `AskUserQuestion` | Agent requested human input before proceeding | Observable (event_type) |
| `human_intervention` | Human provided correction or override | Observable (metadata field) |
| `unsafe_continuation` | Agent completed despite uncertainty, missing evidence, or skipped review | Requires annotation |
| `retry_after_uncertainty` | Agent retried a tool after expressing uncertainty | Requires analysis |
| `branch_after_failed_evidence` | Agent branched exploration after tool-level evidence failure | Requires analysis |
| `rollback_after_test_failure` | Agent rolled back a change after test failure | Observable (tool sequence) |
| `late_stage_correction` | Correction occurred deep in the causal chain (high depth from root) | Observable (causal depth) |
| `manual_rescue` | Human intervention prevented an otherwise-likely failure | Requires annotation |

## Corpus Requirements

Before any T-SC candidate can move from `exploratory` to `supported_with_caveat`:

1. **Task-type coverage**: safety-relevant task types must be present (document processing, data validation, access control, financial operations)
2. **Safety-signal annotation**: at minimum, `need_review_triggered` and `unsafe_continuation` must be annotatable on a session subset
3. **Lane diversity**: comparison requires tagged sessions in >=2 intervention lanes
4. **Denominator**: minimum 10 sessions per condition for exploratory comparison

None of these requirements are currently met. This direction starts from zero corpus evidence.

## Non-Goals (Repeated for Emphasis)

- Do NOT implement jailbreak reproduction.
- Do NOT provide attack guidance or exploit documentation.
- Do NOT build a content safety classifier.
- Do NOT create a universal model safety benchmark.
- Do NOT change causetrace core schema or topology taxonomy.
- Do NOT implement prediction, anomaly detection, or auto-diagnosis.
- Do NOT promote any T-SC candidate beyond `exploratory` without corpus evidence.
- Do NOT claim causetrace can detect or prevent safety incidents.
- Do NOT merge safety-control morphology into native baseline without lane disclosure.

## Relationship to Other Phase 4 Candidates

| Domain | Candidates | Safety-Control Intersection |
|--------|-----------|---------------------------|
| Default morphology | T-RM-001, T-RM-002, T-RM-003 | Do safety boundaries change default topology? |
| Exploration morphology | (not yet drafted) | Is safety-boundary exploration different from task exploration? |
| Failure morphology | T-FM-001 | Is near-failure safety-relevant? |
| Intervention morphology | T-WI-001, T-RP-001, T-PM-001 | Do interventions reduce safety-control collapse? |
| **Safety-control morphology** | T-SC-001 through T-SC-005 | This document |

## References

- Phase 3D Hypothesis Registry (H-IM-001, H-IM-002, H-EV-004, H-EV-005 — deferred)
- Phase 3E Lane Baseline (human_intervention rate: 5/101 native)
- Phase 3E Closure Report (Tier 2 deferral: failure genuinely rare)
- Phase 4 Theory Candidate Inventory (T-FM-001, T-WI-001)
- Internal safety-collapse research (frontier-model safety incident reports)
- Automatic-signature domain observations (OCR reliability, template matching, false_positive_tables)
