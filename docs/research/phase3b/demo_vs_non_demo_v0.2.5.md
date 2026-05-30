# Phase 3B Demo vs Non-demo: v0.2.5

Date: 2026-05-29

This report checks whether the Phase 3A signal survives removal of `demo`
sessions.

## Corpus Snapshot

- strict research-grade sessions: `107`
- demo strict sessions: `61`
- non-demo strict sessions: `46`

## Runtime Distribution

### Demo

| runtime | sessions |
| --- | ---: |
| demo | 61 |

### Non-demo

| runtime | sessions |
| --- | ---: |
| anthropic | 42 |
| codex | 2 |
| claude | 1 |
| aider | 1 |

## Topology Distribution

| subset | dominant_chain | multi_root_exploration | mixed |
| --- | ---: | ---: | ---: |
| demo | 53 | 8 | 0 |
| non-demo | 42 | 1 | 3 |

## Descriptive Metric Means

| subset | sessions | avg branch density | avg transition entropy | avg path reuse ratio | avg frontier max width |
| --- | ---: | ---: | ---: | ---: | ---: |
| demo | 61 | 0.3989 | 0.8484 | 0.3639 | 1.1639 |
| non-demo | 46 | 0.1206 | 2.4017 | 0.3771 | 18.4130 |

## Observations

- `demo` sessions are structurally denser on branching and much more concentrated in `dominant_chain` plus `multi_root_exploration`.
- `non-demo` sessions show higher transition entropy, but the subset is much smaller and much less balanced.
- `multi_root_exploration` is still present after removing `demo`, but it becomes sparse.

## Negative Results

- No stable runtime fingerprint can be inferred from the demo/non-demo split alone.
- The non-demo subset is too small for generalization.
- The frontier width mean in the non-demo subset is dominated by a small number of outliers, so it should not be read as a stable property.
