# Phase 3A Non-demo Bias Check: v0.2.5

Date: 2026-05-29

This report checks how much of the strict-subset signal remains after removing
`demo` runtime sessions.

## Corpus Snapshot

- strict research-grade sessions: `107`
- non-demo strict sessions: `46`
- non-demo runtimes:
  - `anthropic`
  - `codex`
  - `claude`
  - `aider`

## Non-demo Distributions

### Runtime

| runtime | sessions |
| --- | ---: |
| anthropic | 42 |
| codex | 2 |
| claude | 1 |
| aider | 1 |

### Task Type

| task_type | sessions |
| --- | ---: |
| exploration | 14 |
| feature_add | 10 |
| review | 7 |
| bug_fix | 6 |
| project_init | 5 |
| debug_test | 2 |
| migration | 1 |
| doc_gen | 1 |

### Topology

| topology | sessions |
| --- | ---: |
| dominant_chain | 42 |
| mixed | 3 |
| multi_root_exploration | 1 |

## Non-demo Metric Means

| group | sessions | avg branch density | avg transition entropy | avg path reuse ratio |
| --- | ---: | ---: | ---: | ---: |
| runtime: aider | 1 | 0.0059 | 0.0000 | 1.0000 |
| runtime: anthropic | 42 | 0.1193 | 2.3111 | 0.3434 |
| runtime: claude | 1 | 0.0038 | 3.5199 | 0.6105 |
| runtime: codex | 2 | 0.0285 | 2.3557 | 0.6482 |

| task_type | sessions | avg branch density | avg transition entropy | avg path reuse ratio |
| --- | ---: | ---: | ---: | ---: |
| bug_fix | 6 | 0.0551 | 2.5881 | 0.3373 |
| debug_test | 2 | 0.1103 | 2.4458 | 0.6368 |
| doc_gen | 1 | 0.1111 | 1.1401 | 0.4359 |
| exploration | 14 | 0.1627 | 2.1811 | 0.3079 |
| feature_add | 10 | 0.0964 | 2.5408 | 0.3396 |
| migration | 1 | 0.0016 | 2.9644 | 0.6524 |
| project_init | 5 | 0.2076 | 1.4521 | 0.2407 |
| review | 7 | 0.0190 | 2.5096 | 0.5761 |

| topology | sessions | avg branch density | avg transition entropy | avg path reuse ratio |
| --- | ---: | ---: | ---: | ---: |
| dominant_chain | 42 | 0.1206 | 2.4017 | 0.3771 |
| mixed | 3 | 0.0030 | 1.4742 | 0.4970 |
| multi_root_exploration | 1 | 0.0000 | 0.0000 | 0.0000 |

## Observations

- The runtime signal does not vanish after removing `demo`, but the sample set becomes much smaller.
- `anthropic` remains the dominant non-demo runtime.
- The highest non-demo branch density is associated with `project_init`, followed by `exploration` and `feature_add`.

## Negative Results

- No stable cross-runtime claim should be made from the non-demo subset alone.
- The non-demo subset is too small for a runtime fingerprint claim.
- `multi_root_exploration` is too sparse in the non-demo subset for a meaningful topology claim.
