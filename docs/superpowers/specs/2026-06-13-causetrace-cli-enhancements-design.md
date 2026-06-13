# Causetrace CLI Enhancements (5-task batch)

## Scope

Five independent small enhancements to causetrace CLI and docs, each 5-30 lines.

### Task A: annotate --tag filter
- Add `--tag` to `causetrace annotate` parser
- Scan metadata sidecars for `causetrace_tags` field match
- List matching sessions
- ~15 lines in cli.py

### Task B: ea49a219 investigation
- Read source project file line count
- Compare with enrich output (15 lines → 15 events)
- Determine root cause
- No code change

### Task C: corpus lane-count
- Add `lane-count` subcommand under `corpus`
- Group sessions by task_source + data_origin
- Print per-lane table
- ~25 lines in cli.py

### Task D: SOURCES review
- Read annotation.py SOURCES dict
- Cross-reference Phase 3E lane definitions
- Confirm completeness
- No code change

### Task E: README lane table update
- Update phase3e/README.md lane counts
- Current: 101/3/3/0
- 3 numbers changed

## Constraints
- No core schema changes
- No existing CLI behavior changes
- All tests must pass
