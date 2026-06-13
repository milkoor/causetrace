# Phase 3E Lane Baseline v0.2.5

This document records the first intervention-aware lane baseline for Phase 3E. It is not a validation result. It is the starting point for lane-separated hypothesis tracking.

## Corpus Snapshot

- metadata sessions: `992`
- events: `131,952`
- data sessions: `1,517`
- runtime breadth: `7`
- task breadth: `9`

## Lane Distribution

| Lane | Sessions | Events | % of corpus |
|------|----------|--------|-------------|
| `direct_prompt_native` | 101 | 32,141 | 24.4% |
| `controlled_prompt_morphology` | 3 | 135 | 0.1% |
| `superpowers_workflow_intervention` | 8 | 42,465 | 32.2% |
| `routed_prompt_intervention` | 0 | 0 | 0% |
| unlabeled | 880 | 16,160 | 12.2% |

Note: superpowers_workflow_intervention event count inflated by 3 large sessions (10K-19K events each) from Phase 3E-2 manual annotation. These sessions have no causetrace_tags in event content; classification is via metadata sidecar.

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

8 sessions labeled with `task_source=superpowers_workflow_intervention`. 5 carry explicit causetrace_tags in metadata sidecars (Phase 3E-3 headless runs); 3 were manually annotated during Phase 3E-2.

| Metric | Value |
|--------|-------|
| Sessions | 8 |
| Events | 42,465 |
| Tagged (causetrace_tags in metadata) | 5 |
| Untagged (manual annotation only) | 3 |
| Evidence level: strong | 5 (tagged) |
| Evidence level: moderate | 3 (manual) |
| Agent | claude-code (8) |
| Runtime | claude-code (8) |

Note: event count inflated by 3 large sessions (10K-19K events each) from Phase 3E-2 annotation. The 5 tagged headless sessions are small (10-26 events each, except 7e8574ec at 1,180 events).

Parser detection gate is OPEN for this lane. Phase 2 auto-detection in enrichment pipeline is operational.

## Unlabeled Sessions

880 sessions lack explicit lane labels. These sessions have `data_origin` set but do not match any of the four Phase 3E lane criteria.

## Lane Comparison Summary

| Metric | direct_prompt_native | controlled_prompt_morphology | routed_prompt_intervention | superpowers_workflow_intervention |
|--------|---------------------|------------------------------|---------------------------|----------------------------------|
| Sessions | 101 | 3 | 0 | 8 |
| Events | 32,141 | 135 | 0 | 42,465 |
| Tagged | N/A (native) | 0 | 0 | 5 |
| Evidence: strong | N/A | 0 | 0 | 5 |
| Evidence: moderate | N/A | 0 | 0 | 3 |
| Agent breadth | 5 | 1 | 0 | 1 |

## Current Cautions

- `direct_prompt_native` is the only lane with sufficient sample size for statistical hypothesis checks.
- `superpowers_workflow_intervention` (8 sessions) is dominated by 3 large manually-annotated sessions; descriptive observation only.
- `controlled_prompt_morphology` (3 sessions) is too small for validation — it exists only as a lane marker.
- `routed_prompt_intervention` carries zero labeled sessions — it is a placeholder lane.
- Do not merge intervention lanes into the native baseline.
- Do not draw cross-lane conclusions when only one lane has statistical mass.
- The 880 unlabeled sessions are not a lane — they are a labeling gap.

## Next Action

Phase 3E infrastructure is complete. Parser detection gate is OPEN for superpowers_workflow_intervention. Background acquisition continues for all lanes. Tier 2 validation deferred until native failure >= 10, near-failure >= 10. See [closure report](closure_report_v0.2.5.md).
