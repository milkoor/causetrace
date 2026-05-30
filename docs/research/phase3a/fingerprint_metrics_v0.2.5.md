# Phase 3A Fingerprint Metrics: v0.2.5

Date: 2026-05-29

Strict research-grade subset only. Metrics are descriptive, not predictive.

## Corpus Snapshot

- causetrace version: `v0.2.5`
- strict research-grade sessions: `107`
- strict subset definition:
  - `runtime`, `task_type`, `task_source`, and `success` are present
  - provenance for those fields is `explicit_sidecar` or `annotation`

## Aggregate Metrics

The following values are means across sessions in each group.

| group | sessions | avg branch density | avg transition entropy | avg path reuse ratio | avg frontier max width |
| --- | ---: | ---: | ---: | ---: | ---: |
| runtime: aider | 1 | 0.0059 | 0.0000 | 1.0000 | 2.0000 |
| runtime: anthropic | 42 | 0.1193 | 2.3111 | 0.3434 | 1.7857 |
| runtime: claude | 1 | 0.0038 | 3.5199 | 0.6105 | 1.0000 |
| runtime: codex | 2 | 0.0285 | 2.3557 | 0.6482 | 1.0000 |
| runtime: demo | 61 | 0.3989 | 0.8484 | 0.3639 | 0.8689 |

| task_type | sessions | avg branch density | avg transition entropy | avg path reuse ratio | avg frontier max width |
| --- | ---: | ---: | ---: | ---: | ---: |
| bug_fix | 6 | 0.0551 | 2.5881 | 0.3373 | 2.0000 |
| debug_test | 63 | 0.3897 | 0.8991 | 0.3726 | 0.9206 |
| doc_gen | 1 | 0.1111 | 1.1401 | 0.4359 | 1.0000 |
| exploration | 14 | 0.1627 | 2.1811 | 0.3079 | 1.9286 |
| feature_add | 10 | 0.0964 | 2.5408 | 0.3396 | 1.5000 |
| migration | 1 | 0.0016 | 2.9644 | 0.6524 | 3.0000 |
| project_init | 5 | 0.2076 | 1.4521 | 0.2407 | 1.2000 |
| review | 7 | 0.0190 | 2.5096 | 0.5761 | 1.5714 |

| topology | sessions | avg branch density | avg transition entropy | avg path reuse ratio | avg frontier max width |
| --- | ---: | ---: | ---: | ---: | ---: |
| dominant_chain | 95 | 0.3095 | 1.6066 | 0.4004 | 1.3474 |
| mixed | 3 | 0.0030 | 1.4742 | 0.4970 | 1.6667 |
| multi_root_exploration | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Observations

- `demo` sessions show materially higher branch density than the non-demo runtimes.
- `debug_test` is the largest task class and has the highest branch density among the task groups.
- `exploration` has higher frontier width than `feature_add` and `review`, but the sample size is still limited.
- `multi_root_exploration` is present but concentrated in a small portion of the corpus.

## Negative Results

- No stable runtime fingerprint can be asserted from these metrics alone.
- No stable runtime ranking should be inferred from these descriptive means.
- `multi_root_exploration` here is too small to support a generalization.
