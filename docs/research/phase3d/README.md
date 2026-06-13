# Phase 3D: Runtime Morphology Hypothesis Registry

Status: active.

Phase 3D is the hypothesis layer that follows the descriptive and stratified work in Phase 3A, 3B, and 3C.

It does not change the core schema. It does not add prediction. It records falsifiable hypotheses about runtime morphology that can later be tested against the corpus.

## Phase 3D Scope

Phase 3D turns observations from Phase 3A/3B/3C, plus literature-informed ideas, into a structured hypothesis registry.

The registry is for:

- runtime morphology hypotheses
- topology-task hypotheses
- failure / near-failure morphology hypotheses
- human intervention morphology hypotheses
- observation-triggered transition hypotheses
- long-horizon software evolution hypotheses
- external generalization hypotheses
- epistemic runtime morphology hypotheses

The registry is not for:

- conclusions
- prediction
- anomaly modeling
- schema changes
- taxonomy changes
- external trajectory ingestion

The next mainline stage is `Phase 3D-T2B: Intervention-aware Acquisition`.
It keeps Tier 2 acquisition active while separating workflow-intervention lanes from the native direct-prompt baseline.

## Working Documents

- [Execution summary](execution_summary_v0.2.5.md)
- [Status](status.md)
- [Baseline](baseline_v0.2.5.md)
- [Hypothesis registry](hypothesis_registry_v0.2.5.md)
- [Tier 1 validation](tier1_validation_v0.2.5.md)
- [Tier 2 readiness](tier2_readiness_v0.2.5.md)
- [Tier 2 acquisition plan](tier2_acquisition_plan_v0.2.5.md)
- [Tier 2 acquisition sprint](tier2_acquisition_sprint_v0.2.5.md)
- [Tier 2 candidate seed list](tier2_candidate_seedlist_v0.2.5.md)
- [Tier 2 seed review](tier2_seed_review_v0.2.5.md)
- [Tier 2 triage](tier2_triage_v0.2.5.md)
- [Tier 2 human-intervention seed list](tier2_human_intervention_seedlist_v0.2.5.md)
- [Validation protocol](validation_protocol.md)
- [Hypothesis prioritization](hypothesis_prioritization_v0.2.5.md)
- [Cross-project Prompt Morphology Study](../branches/cross_project_prompt_morphology/README.md)

## Intervention Lanes

Phase 3D now treats workflow intervention as a separate analysis axis.

| Lane | Meaning | Direct native baseline? |
| --- | --- | --- |
| `direct_prompt_native` | User/developer gave the agent a task directly | Yes |
| `routed_prompt_intervention` | `prompt-routing-skill` selected the posture first | No |
| `superpowers_workflow_intervention` | A structured workflow plugin changed the execution shape | No |
| `controlled_prompt_morphology` | Controlled prompt comparison or pilot run | No |

Rules:

- Analyze each lane independently first.
- Do not merge intervention traces into the native direct-prompt baseline.
- Cross-lane comparison may report trends only.
- Intervention-lane findings do not become universal policy without additional validation.

## Hypothesis Categories

- runtime morphology hypotheses
- failure morphology hypotheses
- human intervention morphology hypotheses
- observation-triggered transition hypotheses
- long-horizon software evolution morphology hypotheses
- external trajectory generalization hypotheses
- epistemic runtime morphology hypotheses

## Candidate Hypotheses

These are hypotheses only, not conclusions. Canonical entries live in the registry document.

## Operating Rules

- Keep the registry separate from core schema.
- Keep literature-derived ideas in hypothesis form until corpus evidence exists.
- Record negative results alongside positive ones.
- Do not treat the hypotheses as ontology.
- Do not promote external research into conclusions without causetrace corpus evidence.
- Treat workflow intervention lanes as separate from native direct-prompt analysis.
- Do not move into Phase 4 theory finalization yet.

## Metadata Density Warning

Current corpus scale is sufficient for validation-oriented work, but metadata density remains too low for stable theory finalization or default automation policy.

Current gap summary:

- runtime missing: `1136`
- task_type missing: `1150`
- task_source missing: `1150`
- success missing: `1153`
- duration missing: `1315`
- human_intervention missing: `1219`

The next stage should continue acquisition and lane separation before any universal prompt policy or runtime theory is attempted.

## Upstream Reference

- [Literature note: Strategic Information Allocation under Uncertainty](../literature/strategic_information_allocation_2603_15500.md)
