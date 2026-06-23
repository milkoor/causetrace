# Research Index

This directory groups the research tracks and branch studies that sit alongside the main `causetrace` runtime-morphology work.

## System Definition

- [AI Behavior Science OS v1.0](ai_behavior_science_os_v1.0.md): system-level architecture for generation, execution, observation, dataset design, and research validation. Current implementation starts with metadata-only BDE interfaces and read-only CRDD subset compilation.

## Research Phase Status

| Phase | Status | Summary |
|-------|--------|---------|
| Phase 2.5 | complete | Baseline infrastructure |
| Phase 3A | complete | Descriptive corpus |
| Phase 3B | complete | Topology taxonomy |
| Phase 3C | complete | Metadata & provenance |
| [Phase 3D](phase3d/README.md) | **complete** | Hypothesis registry + Tier 1 validation |
| [Phase 3E](phase3e/README.md) | **complete** | Controlled transition & intervention-aware validation |
| [Phase 4](phase4/README.md) | **frozen** | Evidence-graded theory drafting complete (4-1, 4-2). 4-3 trigger-gated, 0/8 triggers met. |
| Phase 5 | **not open** | Evaluation, diagnostics, prediction |

## Current Corpus Snapshot

- data sessions: `1625`
- metadata sessions: `992`
- events: `132,671`
- strict research-grade sessions: `157`
- native strict sessions: `100`
- agent field coverage: `100%` (inline)
- provider field coverage: `99.8%` (inline)
- runtime breadth: `7`
- task breadth: `9`

## Phase 3D Closure Summary

Phase 3D delivered the hypothesis registry (19 hypotheses, 8 categories), completed Tier 1 validation (3 supported, 1 inconclusive, 1 not supported), and honestly deferred Tier 2 (failure samples genuinely rare in real agent behavior: 1/100 native failure, 0/100 near-failure). See [closure report](phase3d/closure_report_v0.2.5.md).

## Phase 3E Closure Summary

Phase 3E delivered the intervention lane infrastructure (4 lanes, parser detection gate, auto-detection in enrichment), completed 3 sub-phases (baseline, annotation, instrumentation), opened the superpowers_workflow_intervention gate (5 tagged sessions), and honestly deferred Tier 2 validation (failure samples genuinely rare: 1/101 native failure, 5/101 near-failure). Phase 2 auto-detection is operational for superpowers lane. See [closure report](phase3e/closure_report_v0.2.5.md).

## Phase 4 Freeze Status

Phase 4 is **frozen** after evidence-graded theory drafting. Sub-phases 4-1 (evidence grading) and 4-2 (theory draft skeleton) are complete. Phase 4-3 (evidence refresh) is trigger-gated and will only reopen when corpus growth, intervention tags, failure/near-failure density, or metadata coverage crosses predefined thresholds. Currently 0/8 triggers met.

Phase 4 documents:
- [Runtime Morphology Theory Draft v0.1](phase4/runtime_morphology_theory_draft_v0.1.md) — Consolidated draft: 2 supported, 1 caveated, 6 exploratory, 3 deferred
- [Evidence Grading Matrix](phase4/evidence_grading_matrix_v0.2.5.md) — Full candidate review with blockers and promotion conditions
- [Safety-Control Runtime Morphology](phase4/safety_control_morphology_candidates_v0.2.5.md) — 5 exploratory T-SC candidates
- [Phase 4-3 Trigger Conditions](phase4/phase4_3_trigger_conditions.md) — 8 corpus-growth triggers, 7 non-triggers

Phase 4 must not enter:

- Prediction, anomaly detection, or automatic diagnosis
- Universal prompt policy defaulting
- Cross-lane aggregation without lane disclosure
- Promotion of exploratory findings to stable theory without additional evidence
- Phase 5 (evaluation / diagnostics)
- Jailbreak reproduction or attack research

## Corpus Infrastructure

- [Metadata Capture Hardening v0.2.5](corpus/metadata_capture_hardening_v0.2.5.md) — Upstream capture requirements, source-specific defaults, current baseline (108/992 labeled, 10.9%)
- [Future Run Metadata Checklist v0.2.5](corpus/future_run_metadata_checklist_v0.2.5.md) — Per-capture-type metadata declaration checklists, post-capture verification, non-rules

## Dataset Design

- [Causal Runtime Dataset Design v0.1](dataset_design/crdd_v0.1.md): defines the transition from raw trace volume to comparable experimental corpora. The central bottleneck is comparability, not ingestion volume. Future evidence refresh should build named subsets such as `strict_research_grade`, `balanced_cross_runtime`, `failure_enriched`, and `intervention_lane` before revisiting theory candidates.
- [Subset Manifest Template](dataset_design/subset_manifest_template.md): required structure for comparable and experimental subsets used in Phase 4 candidate revalidation.
- [Causal Experiment Requirement Compiler v0.3](dataset_design/cerc_v0.3.md): experiment planning layer that turns observed subset gaps into external-only execution queues. CERC plans do not execute agents, inflate evidence, or upgrade Phase 4 grades.
- [CERC Feedback Integration v0.4](dataset_design/feedback_v0.4.md): read-only feedback layer that ingests external execution results, updates gap projections, and reprioritizes future experiments without changing runtime authority.
- [CERC Plan Validation v0.3.1](dataset_design/plan_validation_v0.3.1.md): read-only checker for duplicate plans, queue constraints, and whether a planned sampling gap still needs collection.

## Roadmap And Future Directions

- [Agentic Auditability Roadmap](roadmap/agentic_auditability_roadmap_v0.2.5.md): `causetrace` may eventually extend from runtime morphology to auditability morphology, studying performance-auditability trade-offs, opaque communication boundaries, traceability of audit agents, and structured `machine_state` / `human_audit_summary` workflows. Long-term positioning: `causetrace` studies the observable runtime and auditability morphology of high-performance AI agents. This is a future direction only; Phase 4 remains frozen and Phase 5 is not open.
- [Data-Grounded Runtime Method Discovery](roadmap/data_grounded_method_discovery_v0.2.5.md): future method claims should come from recorded runtime traces and separate performance, morphology, and auditability effects. Methods are recorded, compared, and revised before being treated as effective.

## Cross-project Branch Studies

- [Cross-project Prompt Morphology Study](branches/cross_project_prompt_morphology/README.md)
  - public research branch
  - v0.1 / v0.2 complete
  - apply-first phase active

## Related Skill

- [prompt-routing-skill](https://github.com/milkoor/prompt-routing-skill)
  - derived from the cross-project prompt morphology work
  - routes tasks to `minimal_prompt`, `human_structured_prompt`, or `expanded_constrained_prompt`
  - pairs with `causetrace` by selecting prompt posture first and measuring the resulting trace morphology here

## Workflow Interventions

- [Prompt Routing Intervention](branches/cross_project_prompt_morphology/README.md)
  - apply-first phase is active
  - routed tasks should be treated as a distinct prompt-posture lane in later morphology analysis
  - use when the task framing itself is part of the experiment or workflow policy

## Prompt Posture Lanes

Treat prompt posture as a first-class experimental variable, not as part of the native baseline.

| Type | Meaning | Mix into native direct-prompt conclusions? |
| --- | --- | --- |
| direct-prompt native trace | User/developer gave the agent a task directly | Yes, under native rules |
| routed-prompt trace | `prompt-routing-skill` selected the posture first | No, not directly |
| expanded prompt study trace | Controlled prompt morphology comparison | Controlled / intervention lane |
| external trajectory | External data source | External lane |

Rules:

- `routed-prompt` is a workflow intervention, not an original natural prompt.
- Keep direct and routed traces separate in analysis.
- Do not merge routed traces into the native direct-prompt baseline.
- If routed traces are analyzed, label them explicitly as routed.

## Workflow Intervention Lanes

Treat workflow intervention as a separate experimental axis from prompt posture.

| Type | Meaning | Mix into native direct-prompt conclusions? |
| --- | --- | --- |
| direct_prompt_native | User/developer gave the agent a task directly | Yes, under native rules |
| routed_prompt_intervention | `prompt-routing-skill` selected the posture first | No, not directly |
| superpowers_workflow_intervention | A structured workflow plugin changed the execution shape | No, not directly |
| controlled_prompt_morphology | Controlled prompt comparison or pilot run | Controlled / intervention lane |

Rules:

- Analyze each workflow lane independently first.
- Do not merge intervention traces into the native direct-prompt baseline.
- Cross-lane comparison may report trends only.
- Intervention-lane findings do not become universal policy without additional validation.

## Boundary

Branch studies and skills may inform hypotheses and workflow choices, but they do not change the `causetrace` core boundary by themselves.
