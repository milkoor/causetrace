# Phase 3E Lane Baseline v0.2.5

This document records the first intervention-aware lane baseline for Phase 3E. It is not a validation result. It is the starting point for lane-separated hypothesis tracking.

## Corpus Snapshot

- metadata sessions: `983`
- events: `128,552`
- strict research-grade sessions: `157`
- native strict sessions: `100`
- data_origin coverage: `100%`

## Lane Distribution

| Lane | Sessions | Events | % of corpus |
|------|----------|--------|-------------|
| `direct_prompt_native` | 101 | 32,141 | 25.0% |
| `controlled_prompt_morphology` | 3 | 135 | 0.1% |
| `routed_prompt_intervention` | 0 | 0 | 0% |
| `superpowers_workflow_intervention` | 0 | 0 | 0% |
| unlabeled | 879 | ~96,276 | 74.9% |

## Lane: `direct_prompt_native`

### Session & Event Metrics

| Metric | Value |
|--------|-------|
| Sessions | 101 |
| Events | 32,141 |
| Avg events/session | 318 |
| Long sessions (>=100 events) | 38 (37.6%) |
| Sessions with AskUserQuestion | 5 (5.0%) |
| Human intervention | 5 (5.0%) |
| Failure | 1 (1.0%) |
| Success | 99 (98.0%) |
| Unknown success | 1 (1.0%) |

### Agent Distribution

| Agent | Sessions |
|-------|----------|
| claude-code | 50 |
| opencode | 46 |
| codex | 3 |
| aider | 1 |
| Sisyphus - Ultraworker | 1 |

### Runtime Distribution (metadata)

| Runtime | Sessions |
|---------|----------|
| anthropic | 49 |
| claude-code | 46 |
| claude | 1 |
| codex | 3 |
| aider | 1 |
| sisyphus - ultraworker | 1 |

### Task Type Distribution

| Task Type | Sessions |
|-----------|----------|
| feature_add | 37 |
| exploration | 19 |
| review | 19 |
| bug_fix | 11 |
| project_init | 9 |
| debug_test | 3 |
| migration | 1 |
| doc_gen | 1 |
| unknown | 1 |

### Model Distribution (top)

| Model | Sessions |
|-------|----------|
| deepseek-v4-pro | 14 |
| deepseek-chat | 2 |
| gpt-5.4-mini | 2 |
| ark-code-latest | 1 |
| unknown | 82 |

Note: 81.2% of sessions lack explicit model metadata. Model coverage is low because most sessions use sidecar metadata annotation, which is sparse for model field.

## Lane: `controlled_prompt_morphology`

| Metric | Value |
|--------|-------|
| Sessions | 3 |
| Events | 135 |
| Avg events/session | 45 |
| Long sessions (>=100 events) | 0 |
| AskUserQuestion | 0 |
| Human intervention | 0 |
| Failure | 0 |
| Success | 0 |
| Agent | claude-code (3) |
| Runtime | unknown (3) |
| Task type | unknown (3) |
| Model | unknown (3) |

This lane is minimal — 3 pilot sessions labeled with `data_origin=controlled_benchmark`. Task type and runtime are not yet annotated.

## Lane: `routed_prompt_intervention`

No sessions explicitly labeled with `task_source=routed_prompt_intervention`.

The `prompt-routing-skill` is deployed but routing metadata has not yet been propagated into the causetrace metadata system. This lane is defined and scoped but carries zero labeled sessions at this baseline.

## Lane: `superpowers_workflow_intervention`

No sessions explicitly labeled with `task_source=superpowers_workflow_intervention`.

Structured workflow plugins (superpowers) are in active use, but workflow intervention metadata has not yet been propagated into the causetrace metadata system. This lane is defined and scoped but carries zero labeled sessions at this baseline.

## Unlabeled Sessions

879 sessions (74.9% of metadata corpus) lack explicit lane labels. These sessions have `data_origin` set but do not match any of the four Phase 3E lane criteria:

- No `direct_prompt_native` / `native` / `real_work` data_origin
- No `controlled_benchmark` data_origin
- No `routed_prompt_intervention` task_source
- No `superpowers_workflow_intervention` task_source

These sessions remain in the corpus but are excluded from lane-separated analysis until labeled.

## Lane Comparison Summary

| Metric | direct_prompt_native | controlled_prompt_morphology | routed_prompt_intervention | superpowers_workflow_intervention |
|--------|---------------------|------------------------------|---------------------------|----------------------------------|
| Sessions | 101 | 3 | 0 | 0 |
| Events | 32,141 | 135 | 0 | 0 |
| Avg events/session | 318 | 45 | - | - |
| Long sessions | 38 | 0 | 0 | 0 |
| AUQ sessions | 5 | 0 | 0 | 0 |
| Human intervention | 5 | 0 | 0 | 0 |
| Failure | 1 | 0 | 0 | 0 |
| Agent breadth | 5 | 1 | 0 | 0 |
| Runtime breadth | 6 | 0 | 0 | 0 |
| Task breadth | 8 | 0 | 0 | 0 |

## Current Cautions

- `direct_prompt_native` is the only lane with sufficient sample size for any hypothesis check.
- `controlled_prompt_morphology` (3 sessions) is too small for validation — it exists only as a lane marker.
- `routed_prompt_intervention` and `superpowers_workflow_intervention` are definitionally scoped but carry no labeled data — they are placeholder lanes.
- Do not merge intervention lanes into the native baseline.
- Do not draw cross-lane conclusions when only one lane has data.
- The 879 unlabeled sessions are not a lane — they are a labeling gap.

## Next Action

Establish a labeling pipeline so that `routed_prompt_intervention` and `superpowers_workflow_intervention` sessions accumulate in the corpus. Until then, Phase 3E validation is limited to within-lane analysis of `direct_prompt_native`.
