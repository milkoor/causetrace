# Phase 3D Tier 2 Human-Intervention Seed List v0.2.5

This document records the native sessions that now support `human_intervention=true`.

The evidence source is explicit `AskUserQuestion` activity in the raw trace. These are genuine interaction markers, not inferred labels.

## Current Native Human-Intervention Exemplars

- `0a2ab964-b056-425b-b7d3-4a04b6e5a4af`
  - runtime: `anthropic`
  - task_type: `feature_add`
  - task_source: `real_work`
  - success: `true`
  - human_intervention: `true`
  - AskUserQuestion count: `1`

- `1a00157a-1359-4981-a11d-21f8164b2130`
  - runtime: `anthropic`
  - task_type: `migration`
  - task_source: `real_work`
  - success: `true`
  - human_intervention: `true`
  - AskUserQuestion count: `1`

- `66808ae5-0da5-4790-b6ac-0158b9f26fae`
  - runtime: `anthropic`
  - task_type: `exploration`
  - task_source: `real_work`
  - success: `true`
  - human_intervention: `true`
  - AskUserQuestion count: `3`

- `e7fc44f1-0bfa-45d5-96b5-2f71dd015cd7`
  - runtime: `anthropic`
  - task_type: `exploration`
  - task_source: `real_work`
  - success: `true`
  - human_intervention: `true`
  - AskUserQuestion count: `1`

- `f4b12241-c80c-4fa3-9201-2d218db6030c`
  - runtime: `anthropic`
  - task_type: `feature_add`
  - task_source: `real_work`
  - success: `true`
  - human_intervention: `true`
  - AskUserQuestion count: `3`

## Interpretation

- The native lane now has real human-intervention examples.
- These are useful for Tier 2 acquisition follow-up and future intervention morphology review.
- They are still too few to support strong intervention morphology conclusions by themselves.

## Next Action

- keep these sessions as the current native human-intervention exemplars
- inspect whether they also contain explicit correction triggers
- re-run Tier 2 readiness after any additional acquisition
