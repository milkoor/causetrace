# Cross-project Prompt Morphology Synthesis v0.1

Status: initial pilot synthesis complete.

## Scope

This page synthesizes the completed initial pilot pass for:

- `Project A`
- `Project B`

It is a planning-and-bounds synthesis, not a full prompt-variant experiment report.

## Shared pattern

Both repositories responded best to explicit boundary language:

- `Project A` needs safety gates around false positives, OCR fallback, and `need_review`
- `Project B` needs workflow gates around extraction deduplication, SMS availability, and role/permission boundaries

That makes prompt structure important even before a formal A/B/C prompt comparison is run.

## Project-level recommendations

### `Project A`

Recommended default prompt posture for future runs:

- `expanded_constrained_prompt` for safety-sensitive work
- `human_structured_prompt` as the middle control
- `minimal_prompt` for contrast only

Reason:

- the repo's highest-risk behavior is unsafe auto-signing or false-positive promotion
- prompts should keep `need_review` visible and conservative

### `Project B`

Recommended default prompt posture for future runs:

- `human_structured_prompt` for workflow and reporting work
- `expanded_constrained_prompt` for SMS / permission / boundary-heavy tasks
- `minimal_prompt` for contrast only

Reason:

- the repo mixes business workflow, extraction, permissions, and documentation-driven integration boundaries
- prompts should keep API availability and role gating explicit

## Cross-project trend

The two repos differ in surface area, but both benefit from prompts that:

- state the boundary before the modification
- keep the smallest safe change in scope
- force a validation step
- avoid over-broad rewrites

That is the main practical takeaway from the completed initial pilot pass.

## What is still missing

The current evidence is enough to justify the pilot setup and the recommended prompt posture, but not enough to claim a measured A/B/C comparative result.

Missing next-step data:

- actual minimal vs expanded vs human-structured comparative runs
- prompt order logs
- session-level morphology metrics
- project-level comparative scores

## Next step

The next pass should run the same task under the three prompt variants and record the morphology metrics defined in:

- `metrics.md`
- `report_template.md`
- `aggregation_rules.md`

Only after that should the study move from initial synthesis to measured comparison.
