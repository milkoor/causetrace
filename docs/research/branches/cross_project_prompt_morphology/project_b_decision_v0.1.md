# Project B Decision Page v0.1

Status: completed initial pilot pass.

This page summarizes the first `Project B` pilot pass for the cross-project prompt morphology study.

## What was completed

The repository was brought through the pilot tasks defined in:

- `LS-PM-001` record extraction / list consistency
- `LS-PM-002` order / payment reporting
- `LS-PM-003` SMS signature / template workflow
- `LS-PM-004` permissions / role-gated business logic
- `LS-PM-005` workflow / refactor / cleanup

The work focused on the repo's real operational surfaces:

- record and order extraction deduplication
- pagination / no-progress loop protection
- SMS signature/template workflow gating
- permission and role boundary documentation
- shared extraction workflow cleanup

## Evidence

- Modified files in the pilot worktree:
  - `project-specific extraction script B`
  - `project-specific extraction script C`
  - `project-specific extraction script A`
  - `project API reference`
  - `project guide`
  - `project-specific validation tests`
  - `project-specific validation tests`
  - `project-specific validation tests`
- Diff footprint:
  - 5 tracked code/docs files modified
  - 118 insertions / 4 deletions on the core project files/docs side
- Validation:
  - `python3 -m py_compile project-specific extraction script A`
  - `python3 -m pytest -q project-specific validation tests project-specific validation tests project-specific validation tests`
  - result: `4 passed`
  - `git diff --check`

## Preliminary morphology reading

This repo rewards prompts that make business boundaries explicit:

- extraction workflows benefit from dedup and no-progress guards
- SMS work must respect `signContent` and endpoint availability
- role-gated behavior should be named before code changes
- workflow cleanup benefits from keeping capture and extraction behavior explicit

## Recommendation for future prompt runs

For workflow-heavy `Project B` tasks:

- prefer `human_structured_prompt` or `expanded_constrained_prompt`
- mention API availability and permission boundaries explicitly
- keep `minimal_prompt` only as a contrast baseline

The next comparative run should focus on whether prompt structure changes:

- invalid retry behavior
- branchiness / long-session behavior
- business-rule clarification behavior
- refactor safety

## Limitation

This page is a completed initial pilot summary, not a full A/B/C morphology comparison. The actual prompt-variant comparative run remains the next step.
