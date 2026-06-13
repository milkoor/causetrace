# Phase 3E: Controlled Transition & Intervention-aware Validation

Phase 3E validates selected runtime morphology hypotheses under controlled or intervention-aware conditions. It does not enter Phase 4 theory finalization.

## Position

- Phase 3D: complete
- Phase 3E: active
- Phase 4: not open

## Mission

Validate the relationship between events, observations, interventions, workflow conditions and topology transitions. Specifically:

```
event / observation / intervention / workflow condition
→ topology transition
```

## Scope

### Active lanes (all kept separate)

| Lane | Description | Merge into native? |
|------|-------------|-------------------|
| `direct_prompt_native` | User gave the agent a task directly | Baseline |
| `routed_prompt_intervention` | `prompt-routing-skill` selected posture first | No |
| `superpowers_workflow_intervention` | Structured workflow plugin changed execution shape | No |
| `controlled_prompt_morphology` | Controlled prompt comparison or pilot run | No |
| `external_trajectory` | External data source | No |

### Validation targets

- controlled benchmark protocol activation
- intervention lane comparison (routed vs superpowers vs controlled)
- correction-trigger studies (test failure, tool error, human correction, explicit correction mark)
- observation-triggered transition studies (contradictory outputs, test failures, shell errors)
- prompt posture / routing impact on retry, branch, and convergence
- workflow intervention impact on topology (superpowers, subagent dispatching, structured workflows)
- Tier 2 sample natural accumulation (failure, near-failure, human-intervention) with opportunistic validation

### Evidence gates

Every Phase 3E claim must report:

- lane
- corpus snapshot
- denominator
- runtime distribution
- task_type distribution
- intervention type (if applicable)
- whether the result is exploratory or validation-grade

## Non-goals

- Phase 4 theory finalization
- Prediction of agent behavior
- Anomaly scoring or detection
- Automatic diagnosis
- Universal prompt policy recommendations
- Cross-lane aggregation without lane disclosure
- Promoting Tier 2 hypotheses to conclusions without sufficient evidence
- Changing topology taxonomy
- Changing readiness gates without explicit justification

## Deferred Hypotheses Carried Forward

### From Phase 3D Tier 2 (failure / intervention morphology)

Registry entries, not validated. Validation deferred until corpus naturally accumulates more samples.

- H-FM-001: failure/near-failure sessions enriched for retry_heavy or branchy topology
- H-FM-002: failed sessions less likely to show branch_collapse
- H-IM-001: human intervention acts as external correction trigger
- H-IM-002: post-intervention traces show topology regime shifts
- H-EV-004: failure sessions may contain silent divergence-like patterns
- H-EV-005: human intervention may produce topology regime shifts

Target: opportunistic validation when native failure >= 10, near-failure >= 10, multi-runtime failure coverage >= 3.

### From Phase 3D Tier 3 (controlled benchmark / external lane)

Activate when controlled benchmark protocol is operational.

- H-OT-001: test failures trigger corrective branch exploration
- H-OT-002: contradictory tool observations precede branch_collapse
- H-EG-001: controlled benchmark lanes show lower branch entropy after task normalization
- H-EG-002: external trajectories over-represent retry-heavy and branchy morphologies
- H-EV-002: external tool observations may substitute for epistemic verbalization as correction triggers
- H-EV-003: branch collapse may occur after uncertainty resolution signals

### From Phase 3D Tier 4 (literature-inspired, registry-only)

Maintain in registry for future corpus expansion.

- H-EV-001: uncertainty verbalization may precede exploratory topology
- H-LH-001: long-horizon tasks produce more fan-in and branch-collapse
- H-LH-002: multi-file tasks increase root spawning and transition entropy

## Operating Rules

- All claims must bind to a specific corpus snapshot and lane.
- Every percentage must include its denominator.
- Every runtime conclusion must disclose runtime distribution.
- Negative results are first-class entries and must not be deleted.
- Do not promote hypotheses to conclusions without corpus-backed validation.
- Do not enter Phase 4.
- Do not implement prediction, anomaly detection, or automatic diagnosis.
- Do not merge intervention lanes into the native direct-prompt baseline.
- Do not change topology taxonomy or readiness gates unless explicitly justified.
- Cross-lane comparison may report trends only.
- Intervention-lane findings do not become universal policy without additional validation.

## Parser Detection Activation Gate

Do not enable causetrace-side parser detection for an intervention lane until that lane has accumulated the minimum explicitly tagged sessions.

| Lane | Minimum Tagged Sessions | Current Tagged |
|------|------------------------|----------------|
| `routed_prompt_intervention` | 5 | 0 |
| `superpowers_workflow_intervention` | 5 | 0 |
| `controlled_prompt_morphology` | 5 or explicit pilot set | 0 |

### Eligible Evidence

Must be explicit and machine-readable:

- `causetrace_tags` in tool output or event content
- `intervention_lane` field with explicit lane value
- `intervention_evidence_source` specifying the source tool
- `prompt_posture` (for routed) or `workflow_label` (for superpowers)

### Ineligible Evidence

Must NOT be used for intervention lane classification:

- `Skill` tool usage alone (without PlanMode/Workflow)
- Prompt length or structured wording
- Checklist-like execution style
- Inferred workflow structure without explicit marker
- Agent self-description of workflow adherence

### Gate Rationale

Premature parser detection on 1-2 samples risks encoding heuristic patterns that mislabel future sessions. Waiting for >=5 tagged sessions per lane ensures detection logic is tested against varied task types, runtimes, and intervention patterns before activation.

## Background Processes

- Intervention-aware acquisition continues (formerly Phase 3D-T2B).
- Native lane maintained as a living baseline.
- Tier 2 failure/intervention opportunistic validation.

## Phase 3E Documents

- [Lane Baseline](lane_baseline_v0.2.5.md) — Per-lane session counts, event counts, distributions (Phase 3E-1)
- [Intervention Validation Plan](intervention_validation_plan_v0.2.5.md) — Validation protocol, hypothesis allocation, readiness assessment (Phase 3E-1)
- [Intervention Lane Annotation Plan](intervention_lane_annotation_plan_v0.2.5.md) — Annotation criteria, non-inference rule, process (Phase 3E-2)
- [Intervention Lane Candidates](intervention_lane_candidates_v0.2.5.md) — Candidate review table with evidence and decisions (Phase 3E-2)
- [Intervention Capture Instrumentation Plan](intervention_capture_instrumentation_plan_v0.2.5.md) — Capture requirements, tag format specs, enrichment recognition plan (Phase 3E-3)

## Current State

**Phase 3E intervention foundation is frozen.**

| Sub-phase | Status | Deliverable |
|-----------|--------|-------------|
| 3E-1 | complete | Lane baseline — 4 lanes characterized |
| 3E-2 | complete | Annotation pass — 3 sp sessions annotated, routed=0 honest |
| 3E-3 | complete | Instrumentation — `SOURCES` expanded, capture tag spec defined, upstream tools updated |

Current bottleneck is upstream tag emission, not causetrace-side lane design. Parser detection remains gated (>=5 tagged sessions per intervention lane).

| Lane | Sessions | Evidence |
|------|----------|----------|
| `direct_prompt_native` | 101 | stable baseline |
| `superpowers_workflow_intervention` | 3 | manual annotation (Phase 3E-2); awaiting workflow tag natural accumulation |
| `controlled_prompt_morphology` | 3 | pilot only; awaiting controlled benchmark expansion |
| `routed_prompt_intervention` | 0 | awaiting prompt-routing-skill tag emission |

### What can be done now

- Analyze `direct_prompt_native` lane (within-lane only)
- Descriptive observation of `superpowers_workflow_intervention` (exploratory, not validation-grade)
- Run real tasks to naturally accumulate tagged sessions
- Upstream tag emission improvements in `prompt-routing-skill` and superpowers

### What must NOT be done now

- Heuristic parser detection in causetrace
- Skill-only automatic lane classification
- routed vs direct comparison or conclusions
- superpowers vs direct comparison or conclusions
- Phase 4 entry
- Universal prompt policy
- Prediction / anomaly / auto-diagnosis
