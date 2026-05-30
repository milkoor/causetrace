# Cross-project Prompt Morphology Execution Queue v0.1

Status: initial pilot pass complete.

This queue defines the sequential run order for the first pilot pass.

Rules:

- Keep the task order fixed unless a task becomes unavailable.
- Keep prompt variant order recorded for every run.
- Prefer clean repo resets between variants.
- Use the same runtime where possible.
- Do not merge results across projects before each project has its own decision page.

## Execution Order

### Stage 1: `Project A`

Run the first pilot repo in a safety-first order, starting from the strongest false-positive and `need_review` gates.

1. `AS-PM-001` `false_positive_tables`
2. `AS-PM-002` `need_review` safety gate
3. `AS-PM-003` OCR unavailable / fallback behavior
4. `AS-PM-004` `grid_template` security audit
5. `AS-PM-005` calibrator auto-match safety

### Stage 2: `Project B`

Run the second pilot repo after the first pilot repo has a stable read on morphology differences.

6. `LS-PM-001` record extraction / list consistency
7. `LS-PM-002` order / payment reporting
8. `LS-PM-003` SMS signature / template workflow
9. `LS-PM-004` permissions / role-gated business logic
10. `LS-PM-005` workflow / refactor / cleanup

## Prompt Order Inside Each Task

Use the following order where feasible:

1. `minimal_prompt`
2. `human_structured_prompt`
3. `expanded_constrained_prompt`

If full A/B/C triplets are not feasible, keep the order recorded and note the missing variant.

## Pilot Log Fields

For each run, record:

- task id
- repository
- prompt variant
- runtime
- repository commit
- session id
- outcome
- topology label
- event count
- tool call count
- retry density
- branch density
- AskUserQuestion count
- human intervention
- correction trigger
- final patch quality
- notes

## Stop Conditions

Pause the queue if a run shows:

- a repeated safety-gate failure that indicates the task is mis-scoped
- an obviously contaminated workspace
- a prompt variant that over-constrains the task so heavily that the result becomes non-informative
- a repository state change that invalidates the remaining variants

## Reporting

After Stage 1 and Stage 2, produce:

- one project-level decision page for `Project A`
- one project-level decision page for `Project B`
- one cross-project synthesis page

This repository now contains:

- [Project A decision page](project_a_decision_v0.1.md)
- [Project B decision page](project_b_decision_v0.1.md)
- [cross-project synthesis](cross_project_synthesis_v0.1.md)
