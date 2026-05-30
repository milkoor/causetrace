# Phase 3D Tier 1 Validation v0.2.5

This document records the first descriptive pass over the Tier 1 hypotheses in Phase 3D.

It is not a prediction result. It is a corpus-backed validation note with explicit denominators and lane scope.

## Validation Context

- corpus version: v0.2.5
- corpus snapshot baseline: sessions `976`
- strict research-grade sessions: `157`
- native strict sessions: `100`
- lane scope: native lane
- validation type: descriptive, stratified, non-predictive

## Native Lane Baseline Used

- native sessions: `100`
- topology counts:
  - dominant_chain: `93`
  - mixed: `6`
  - multi_root_exploration: `1`
- runtime counts:
  - anthropic: `49`
  - claude-code: `46`
  - codex: `2`
  - claude: `1`
  - aider: `1`
  - sisyphus - ultraworker: `1`
- task counts:
  - feature_add: `37`
  - review: `19`
  - exploration: `19`
  - bug_fix: `10`
  - project_init: `9`
  - debug_test: `3`
  - migration: `1`
  - doc_gen: `1`
  - unknown: `1`

## Tier 1 Hypotheses

### H-RM-001

- **Claim:** dominant_chain is the default morphology in native coding-agent sessions.
- **Result:** supported
- **Evidence:** dominant_chain is the plurality topology in the native lane at `93/100`.
- **Notes:** The native lane still contains a small amount of mixed and multi-root structure, but dominant_chain is clearly the default morphology.

### H-RM-002

- **Claim:** runtime-level topology differences shrink after controlling for `data_origin` and `task_type`.
- **Result:** inconclusive
- **Evidence:** the current corpus shows runtime skew in the native lane, but there is not yet a controlled benchmark comparison or a sufficiently balanced runtime distribution to test shrinkage robustly.
- **Notes:** This remains a confounder-control hypothesis for later validation.

### H-RM-003

- **Claim:** multi_root_exploration remains a minority morphology in native real_work sessions.
- **Result:** supported
- **Evidence:** multi_root_exploration appears only `1/100` times in the native lane baseline.
- **Notes:** This is a strong minority signal in the current native corpus.

### H-TT-001

- **Claim:** review and exploration tasks are more likely to show multi_root_exploration than feature_add tasks.
- **Result:** not supported in the current corpus
- **Evidence:** the native lane contains `0` multi_root_exploration cases in review, exploration, and feature_add tasks; the single native multi_root case is in project_init.
- **Notes:** The current sample does not support the proposed task association.

### H-TT-002

- **Claim:** feature_add tasks are more likely to show dominant_chain or branch_collapse than exploration tasks.
- **Result:** supported with caveat
- **Evidence:** feature_add tasks are `37/37` dominant_chain in the native lane, while exploration tasks are `17/19` dominant_chain. branch_collapse is not present in the native lane baseline.
- **Notes:** The dominant_chain portion of the hypothesis is supported; the branch_collapse portion is not testable in the current native lane because branch_collapse does not appear there.

## Summary

- Supported: H-RM-001, H-RM-003, H-TT-002 (with caveat)
- Inconclusive: H-RM-002
- Not supported: H-TT-001

## Next Action

Proceed to the Tier 2 hypotheses only after the failure and human-intervention subsets are expanded enough to make those checks meaningful.
