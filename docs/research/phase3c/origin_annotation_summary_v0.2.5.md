# Phase 3C Origin Annotation Summary (v0.2.5)

This document records the completed manual `data_origin` labeling pass for the current native corpus. It does not backfill data automatically.

## Labeling Policy

Verified mapping:

- `task_source=real_work` -> `data_origin=native`
- `task_source=demo` -> `data_origin=unknown`
- `task_source=proxy` -> `data_origin=unknown`
- `task_source=unknown` -> `data_origin=unknown`

This mapping was cross-checked with a sub-agent and aligned with the Phase 3C lane rules.

## Result

- labeled sessions: `930/930`
- `native`: `54`
- `unknown`: `876`
- missing `data_origin`: `0`

## Notes

- `data_origin` is a source-tier label, not a task-purpose label.
- `demo` and `proxy` remain separate review lanes and were not collapsed into `controlled_benchmark`.
- `controlled_benchmark` and `external_trajectory` remain reserved for explicit future imports.
