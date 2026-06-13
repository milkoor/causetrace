# Research Index

This directory groups the research tracks and branch studies that sit alongside the main `causetrace` runtime-morphology work.

## Research Phase Status

| Phase | Status | Summary |
|-------|--------|---------|
| Phase 2.5 | complete | Baseline infrastructure |
| Phase 3A | complete | Descriptive corpus |
| Phase 3B | complete | Topology taxonomy |
| Phase 3C | complete | Metadata & provenance |
| [Phase 3D](phase3d/README.md) | **complete** | Hypothesis registry + Tier 1 validation |
| [Phase 3E](phase3e/README.md) | **active** | Controlled transition & intervention-aware validation |
| Phase 4 | **not open** | Theory finalization |

## Current Corpus Snapshot

- sessions: `1351`
- events: `128,552`
- strict research-grade sessions: `157`
- native strict sessions: `100`
- agent field coverage: `100%` (inline)
- provider field coverage: `99.8%` (inline)
- runtime breadth: `7`
- task breadth: `9`

## Phase 3D Closure Summary

Phase 3D delivered the hypothesis registry (19 hypotheses, 8 categories), completed Tier 1 validation (3 supported, 1 inconclusive, 1 not supported), and honestly deferred Tier 2 (failure samples genuinely rare in real agent behavior: 1/100 native failure, 0/100 near-failure). See [closure report](phase3d/closure_report_v0.2.5.md).

## Phase 3E Active Scope

Controlled transition and intervention-aware validation. Lanes kept separate:

- `direct_prompt_native`
- `routed_prompt_intervention`
- `superpowers_workflow_intervention`
- `controlled_prompt_morphology`

Deferred hypotheses from Phase 3D Tier 2/3/4 carried forward. Tier 2 validation is opportunistic (background acquisition), not a phase gate. See [Phase 3E README](phase3e/README.md).

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
