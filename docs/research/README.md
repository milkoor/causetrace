# Research Index

This directory groups the research tracks and branch studies that sit alongside the main `causetrace` runtime-morphology work.

## Active Research Tracks

- [Phase 3A](phase3a/README.md)
- [Phase 3B](phase3b/README.md)
- [Phase 3C](phase3c/README.md)
- [Phase 3D](phase3d/README.md)

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

## Boundary

Branch studies and skills may inform hypotheses and workflow choices, but they do not change the `causetrace` core boundary by themselves.
