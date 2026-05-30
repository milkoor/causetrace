# Cross-project Prompt Morphology Pilot v0.2 Completion Note

## Status

v0.2 complete.

## What v0.2 added

This second pass expanded runtime coverage beyond the initial pilot:

- `Project A` GUI runtime coverage
- `Project B` script-level workflow runtime coverage

## Evidence

- `Project A` GUI smoketest:
  - `test_gui.py` passed `6/6`
  - exercised MainWindow, CalibratorDialog, coordinate conversion, template save/round-trip, and undo behavior
- `Project B` full extraction workflow:
  - `project-specific extraction script A` completed successfully
  - record extraction count: `dataset-size redacted; extraction completed successfully`
  - elapsed time: `49.2s`
- `Project B` single-script extraction runtime:
  - `project-specific extraction script B` completed successfully
  - record extraction count: `dataset-size redacted; extraction completed successfully`
  - elapsed time: `81.1s`

## Interpretation boundary

This v0.2 pass improves runtime breadth.

It does not establish a universal prompt morphology law.
Project-level conclusions remain separate.
Cross-project synthesis remains trend-based only.

## Link to detailed note

- [v0.2 runtime expansion note](pilot_v0.2_runtime_expansion_note.md)

## Next step

If the study continues, the next useful directions are:

- more prompt-variant comparisons on the same task set
- more failure / near-failure cases
- more human-intervention-heavy cases
- applying the current prompt templates into real project workflow
