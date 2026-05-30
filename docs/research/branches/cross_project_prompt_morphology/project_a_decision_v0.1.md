# Project A Decision Page v0.1

Status: completed initial pilot pass.

This page summarizes the first `Project A` pilot pass for the cross-project prompt morphology study.

## What was completed

The repository was brought through the safety-sensitive pilot tasks defined in:

- `AS-PM-001` false-positive table control
- `AS-PM-002` `need_review` safety gate
- `AS-PM-003` OCR unavailable / fallback behavior
- `AS-PM-004` `grid_template` security audit
- `AS-PM-005` calibrator auto-match safety

The work focused on the repo's real risk surfaces:

- body-table vs title-block false positives
- `need_review` short-circuiting
- OCR fallback conservatism
- table-like page detection
- calibrator auto-match safety

## Evidence

- Modified files in the pilot worktree:
  - `core/checker.py`
  - `core/pipeline.py`
  - `core/report.py`
  - `gui/calibrator.py`
  - `core/safety.py`
  - `test_integration.py`
- Diff footprint:
  - 5 files modified in the repo core path
  - 201 insertions / 11 deletions
- Validation:
  - `python3 -m py_compile` on the changed workflow path
  - `python3 -m pytest -q test_integration.py test_detector.py`
  - result: `12 passed`
  - `git diff --check`

## Preliminary morphology reading

This repo rewards prompts that explicitly preserve safety gates:

- `need_review` should be treated as a valid terminal review state, not an error to bulldoze through
- OCR unavailability should degrade conservatively
- table-like pages should not be pushed toward auto-signature behavior
- calibrator auto-match should be conservative around false-positive surfaces

## Recommendation for future prompt runs

For safety-sensitive `Project A` tasks:

- prefer `expanded_constrained_prompt`
- keep `human_structured_prompt` as the middle control
- keep `minimal_prompt` as the contrast baseline only

The next comparative run should focus on whether prompt structure changes:

- invalid retry behavior
- `need_review` persistence
- template-matching safety
- false-positive avoidance

## Limitation

This page is a completed initial pilot summary, not a full A/B/C morphology comparison. The actual prompt-variant comparative run remains the next step.
