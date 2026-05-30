# Phase 3C Lane Baseline After Origin Annotation (v0.2.5)

This is a descriptive lane baseline after the first manual `data_origin` pass. It is still advisory and does not write back to metadata.

## Corpus Snapshot

- total sessions: `930`
- data-origin labeled sessions: `930`
- missing `data_origin`: `0`

## Data Origin Distribution

- `native`: `54`
- `unknown`: `876`

## Native Lane Baseline

The native lane is the currently actionable research lane.

### Native session mix

- sessions: `54`
- task source:
  - `real_work`: `54`
- runtime:
  - `anthropic`: `49`
  - `codex`: `2`
  - `claude`: `1`
  - `aider`: `1`
  - `sisyphus - ultraworker`: `1`
- task type:
  - `exploration`: `19`
  - `feature_add`: `10`
  - `review`: `9`
  - `bug_fix`: `6`
  - `project_init`: `5`
  - `debug_test`: `2`
  - `migration`: `1`
  - `doc_gen`: `1`
  - `unknown`: `1`
- topology:
  - `dominant_chain`: `48`
  - `mixed`: `5`
  - `multi_root_exploration`: `1`

### Native strict subset

- strict sessions: `54`
- task source:
  - `real_work`: `54`
- runtime:
  - `anthropic`: `50`
  - `codex`: `2`
  - `claude`: `1`
  - `aider`: `1`
  - `sisyphus - ultraworker`: `1`
- task type:
  - `exploration`: `19`
  - `feature_add`: `10`
  - `review`: `9`
  - `bug_fix`: `6`
  - `project_init`: `5`
  - `debug_test`: `2`
  - `migration`: `1`
  - `doc_gen`: `1`
  - `unknown`: `1`
- topology:
  - `dominant_chain`: `48`
  - `mixed`: `5`
  - `multi_root_exploration`: `1`
- failure sessions: `1`

### Native strict near-misses

The strict native subset is now complete.

- missing `success`: `0`
- strict-native near-misses: `none`

## Unknown Lane Baseline

The unknown lane still dominates the raw corpus, but it is no longer source-opaque.

### Unknown lane mix

- sessions: `876`
- task source:
  - `unknown`: `812`
  - `demo`: `62`
  - `proxy`: `2`
- runtime:
  - `unknown`: `800`
  - `demo`: `62`
  - `anthropic`: `12`
  - `aider`: `1`
  - `codex`: `1`
- task type:
  - `unknown`: `813`
  - `debug_test`: `62`
  - `exploration`: `1`
- topology:
  - `dominant_chain`: `753`
  - `mixed`: `115`
  - `multi_root_exploration`: `8`

### Unknown strict subset

- strict sessions: `62`
- task source:
  - `demo`: `61`
  - `proxy`: `1`
- runtime:
  - `demo`: `61`
  - `anthropic`: `1`
- task type:
  - `debug_test`: `62`
- topology:
  - `dominant_chain`: `54`
  - `multi_root_exploration`: `8`
- failure sessions: `1`

## Current Interpretation

- `real_work` sessions are the best current native lane.
- `demo` sessions remain separate from controlled benchmark by policy.
- `proxy` is too small to auto-classify.
- `unknown` is now a residual bucket, not a source-tier label.
- The native lane is real, and the strict native subset is `54` after provenance normalization.

## Next Manual Review Priority

1. native strict sessions
2. failure candidates
3. proxy rows
4. demo rows
5. residual unknown rows

## Next Reports to Recompute

- [Origin annotation summary](origin_annotation_summary_v0.2.5.md)
- [Origin labeling queue](origin_labeling_queue_v0.2.5.md)
- [Lane inclusion rules](lane_inclusion_rules.md)
- [Review batches](review_batches_v0.2.5.md)
