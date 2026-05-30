# Prompt Morphology Branch Protocol v0.1

This protocol defines the controlled study setup for comparing prompt structure across active repositories.

## Scope

The study compares prompt form, not model identity alone. The goal is to determine whether prompt structure changes runtime morphology and project outcomes under matched tasks.

## Prompt Variants

- `minimal_prompt`: original short prompt.
- `expanded_constrained_prompt`: AI-expanded strong-constraint prompt.
- `human_structured_prompt`: medium-detail human-written prompt.

The expanded prompt is not assumed to be superior. It is a treatment group under test.

## Task Selection

Eligible task types:

- `bug_fix`
- `test_repair`
- `refactor`
- `review`
- `dependency_upgrade`

Preferred source repositories:

- `Project A`
- `Project B`
- other active repos only if they offer a real task, a real review surface, and a direct reuse benefit.

## Control Rules

- Use the same task across prompt variants.
- Use the same repository and the same code baseline where possible.
- Use the same runtime where possible.
- Reset the workspace between prompt variants.
- Record prompt order.
- Avoid reusing patches from earlier variants.
- Prefer randomized A/B/C order when possible.

## Minimum Pilot

- 5 real tasks
- 2 to 3 prompt variants per task
- 1 fixed runtime where possible
- 15 sessions as the initial pilot target

The pilot goal is workflow validation, not a strong conclusion.

## Data Capture

Each session should record:

- repository
- task id or task label
- prompt variant
- runtime
- baseline commit or workspace reset point
- execution order
- outcome
- morphology summary
- intervention summary
- project-level notes

## Result Boundaries

- `causetrace` computes morphology comparisons and cross-project trend summaries.
- Each project computes its own application decision page.
- Cross-project reports compare trends, but do not collapse project outcomes into one truth.
