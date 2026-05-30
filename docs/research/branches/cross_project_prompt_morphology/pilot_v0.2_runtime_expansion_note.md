# Cross-project Prompt Morphology Pilot v0.2 Runtime Expansion Note

## Status

Runtime expansion pass complete.

## Scope

This second pass expanded runtime coverage beyond the initial pilot by adding:

- `Project A` GUI runtime coverage
- `Project B` script-level workflow runtime coverage

It is a runtime expansion note, not a universal prompt morphology conclusion.

## Evidence

### `Project A`

- GUI smoketest executed successfully under a temporary virtual environment.
- Result: `test_gui.py` passed `6/6`.
- The GUI runtime exercised:
  - `MainWindow` construction
  - `CalibratorDialog` construction
  - coordinate conversion
  - field/template save round-trip
  - `TemplateManager` round-trip
  - undo/clear-all behavior

### `Project B`

- Full extraction workflow executed successfully.
- `project-specific extraction script A`:
  - login succeeded
  - record extraction completed
  - output files were written
  - record count: `dataset-size redacted; extraction completed successfully`
  - elapsed time: `49.2s`
- `project-specific extraction script B`:
  - login succeeded
  - record extraction completed
  - output files were written
  - record count: `dataset-size redacted; extraction completed successfully`
  - elapsed time: `81.1s`

## Interpretation

This pass strengthens the study's runtime breadth:

- `Project A` now has both unit/integration evidence and a GUI runtime path.
- `Project B` now has both unit evidence and full script-based extraction evidence.

The pass still does not establish a universal prompt morphology law.
Project-specific conclusions remain separate.
Cross-project synthesis remains trend-based only.

## Next-step options

- expand prompt-variant comparisons on the same task set
- add more failure / near-failure cases
- add more human-intervention-heavy tasks
- pause here and apply the current prompt templates into real project workflow
