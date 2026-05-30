# Phase 3D Baseline v0.2.5

This document records the first descriptive baseline for Phase 3D against the current v0.2.5 corpus snapshot.

It is not a validation result and it is not a conclusion. It is the starting point for hypothesis tracking.

## Corpus Snapshot

- sessions: `976`
- events: `26033`
- ready: `True`
- strict research-grade sessions: `157`
- native strict sessions: `100`
- data_origin coverage: `100%`
- runtime breadth: `7`
- task breadth: `9`

## Baseline Observations

- `dominant_chain` remains the primary topology morphology in the corpus.
- `mixed` and `multi_root_exploration` exist, but they remain minority morphologies.
- The native lane is now large enough to support baseline hypothesis checks, but not large enough to support strong universal claims.
- Runtime distribution is still uneven, with `anthropic` and `claude-code` accounting for most explicit runtime labels.
- Task distribution is still uneven, with `debug_test`, `feature_add`, `exploration`, and `review` dominating the labeled subset.
- Failure and human-intervention coverage remain limited relative to the overall corpus, so failure morphology and intervention morphology should be treated as weaker, later-stage candidates.

## Tier 1 Hypotheses To Check First

The current corpus is best suited for the following immediate checks:

- H-RM-001: dominant_chain is the default morphology in native coding-agent sessions.
- H-RM-002: runtime-level topology differences shrink after controlling for `data_origin` and `task_type`.
- H-RM-003: multi_root_exploration remains a minority morphology in native real_work sessions.
- H-TT-001: review and exploration tasks are more likely to show multi_root_exploration than feature_add tasks.
- H-TT-002: feature_add tasks are more likely to show dominant_chain or branch_collapse than exploration tasks.

## Current Cautions

- Do not treat the baseline as a fingerprint.
- Do not promote literature-derived hypotheses into conclusions without corpus-backed validation.
- Do not mix controlled benchmark candidates into the native baseline.
- Do not infer failure morphology from the current corpus without a stronger failure subset.

## Negative-Result Log Placeholder

If a future check does not support a hypothesis, record:

- corpus snapshot
- lane scope
- metrics computed
- observed result
- reason it failed
- next action

## Next Action

Run the first pass of descriptive checks for Tier 1 hypotheses under the Phase 3D validation protocol, then record supported, weakened, inconclusive, and unsupported results separately.
