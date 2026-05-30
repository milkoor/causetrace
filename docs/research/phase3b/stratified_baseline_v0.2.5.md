# Phase 3B Stratified Baseline: v0.2.5

Date: 2026-05-29

This report carries the descriptive baseline from Phase 3A into the first
stratified pass. The focus is on subgroup size and shape, not on prediction.

## Corpus Snapshot

- causetrace version: `v0.2.5`
- strict research-grade sessions: `107`
- strict non-demo sessions: `46`
- strict demo sessions: `61`

## Split Summary

| split | sessions | dominant_chain | multi_root_exploration | mixed |
| --- | ---: | ---: | ---: | ---: |
| strict_all | 107 | 95 | 9 | 3 |
| strict_non_demo | 46 | 42 | 1 | 3 |
| strict_demo | 61 | 53 | 8 | 0 |

## Immediate Observations

- The strict corpus is still dominated by `dominant_chain`.
- `demo` sessions contribute most of the `multi_root_exploration` signal.
- Removing `demo` reduces the runtime set to four runtimes:
  - `anthropic`
  - `codex`
  - `claude`
  - `aider`
- The non-demo subset is too small to support a strong runtime law.

## Negative Results

- No stable fingerprint is justified after stratifying by `demo`.
- No stable topology-task conclusion is justified after stratifying by `demo`.
- The strict subset remains too imbalanced to support a strong `human_intervention` split.
