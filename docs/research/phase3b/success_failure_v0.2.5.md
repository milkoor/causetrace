# Phase 3B Success vs Failure: v0.2.5

Date: 2026-05-29

This report checks the strict subset by outcome label. The failure side is very
small, so the purpose here is observational only.

## Corpus Snapshot

- strict research-grade sessions: `107`
- success: `105`
- failure: `2`

## Topology Distribution

| outcome | dominant_chain | multi_root_exploration | mixed |
| --- | ---: | ---: | ---: |
| success | 94 | 9 | 2 |
| failure | 1 | 0 | 1 |

## Descriptive Metric Means

| outcome | sessions | avg branch density | avg transition entropy | avg path reuse ratio | avg frontier max width |
| --- | ---: | ---: | ---: | ---: | ---: |
| success | 105 | 0.2779 | 1.4912 | 0.3595 | 2.2571 |
| failure | 2 | 0.1116 | 0.2345 | 0.8913 | 676.0000 |

## Observations

- The failure subset is too small to support a stable comparison.
- Both failure sessions are structurally atypical compared with the success bulk.
- The very large frontier width in the failure row is an outlier signal, not a conclusion.

## Negative Results

- No failure topology law can be inferred from two sessions.
- No prediction rule should be derived from this split.
