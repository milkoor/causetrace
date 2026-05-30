# Phase 3A Baseline Report: v0.2.5

Date: 2026-05-29

This report is the first descriptive baseline for Phase 3A. It is intentionally
limited to the strict research-grade subset and records observation only.

## Corpus Snapshot

- causetrace version: `v0.2.5`
- total sessions in local corpus: `894`
- strict research-grade sessions: `107`
- readiness gate: `true`
- strict subset definition:
  - `runtime`, `task_type`, `task_source`, and `success` are present
  - provenance for those fields is `explicit_sidecar` or `annotation`

## Runtime Distribution

| runtime | sessions |
| --- | ---: |
| demo | 61 |
| anthropic | 42 |
| codex | 2 |
| claude | 1 |
| aider | 1 |

## Task Distribution

| task_type | sessions |
| --- | ---: |
| debug_test | 63 |
| exploration | 14 |
| feature_add | 10 |
| review | 7 |
| bug_fix | 6 |
| project_init | 5 |
| migration | 1 |
| doc_gen | 1 |

## Topology Distribution

| topology | sessions |
| --- | ---: |
| dominant_chain | 95 |
| multi_root_exploration | 9 |
| mixed | 3 |

## Runtime x Topology

| runtime | dominant_chain | multi_root_exploration | mixed |
| --- | ---: | ---: | ---: |
| aider | 0 | 0 | 1 |
| anthropic | 39 | 1 | 2 |
| claude | 1 | 0 | 0 |
| codex | 2 | 0 | 0 |
| demo | 53 | 8 | 0 |

## Task x Topology

| task_type | dominant_chain | multi_root_exploration | mixed |
| --- | ---: | ---: | ---: |
| bug_fix | 6 | 0 | 0 |
| debug_test | 54 | 8 | 1 |
| doc_gen | 1 | 0 | 0 |
| exploration | 13 | 0 | 1 |
| feature_add | 10 | 0 | 0 |
| migration | 1 | 0 | 0 |
| project_init | 4 | 1 | 0 |
| review | 6 | 0 | 1 |

## Observations

- The strict subset is dominated by `demo` and `anthropic` runtimes.
- `dominant_chain` is the overwhelming corpus shape in the strict subset.
- `multi_root_exploration` is present, but only as a minority shape.
- `debug_test` is the largest task class and is the only task with substantial
  `multi_root_exploration` presence in this baseline.
- `review`, `exploration`, and `project_init` each have at least one non-linear
  example, but the sample size is too small for a stable claim.

## Negative Results

- No stable runtime fingerprint can be claimed from this baseline alone.
- No stable topology-to-task conclusion can be claimed from this baseline alone.
- `branch_collapse`, `fan_in`, and `retry_heavy` are not distinguishable at the
  strict-subset level in this first baseline table.

## Next Actions

1. Extend the baseline with distribution metrics that are already available in
   the corpus primitives:
   - branch density
   - frontier width
   - transition entropy
   - path reuse ratio
2. Split the baseline by `success` and `human_intervention`.
3. Add a second baseline that excludes synthetic `demo` sessions to check how
   much of the runtime signal is corpus construction bias.
