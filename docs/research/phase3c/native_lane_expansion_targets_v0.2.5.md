# Native Lane Expansion Targets (v0.2.5)

This document turned the current native-lane baseline into a concrete collection plan. The Phase 3C native target has now been met; this file remains as a record of the expansion plan and the constraints that shaped it.

## Current Phase 3C Status

- strict research-grade sessions: `157`
- native strict sessions: `100`
- data_origin coverage: `100%`
- strict native coverage: complete
- current bottleneck: native lane target reached; remaining work moves to Phase 3D / 3E validation and future refreshes

## Current Native Strict Baseline

- strict native sessions: `100`
- runtime concentration:
  - `anthropic`: `49`
  - `claude-code`: `46`
  - `codex`: `2`
  - `claude`: `1`
  - `aider`: `1`
  - `sisyphus - ultraworker`: `1`
- task concentration:
  - `feature_add`: `39`
  - `review`: `18`
  - `project_init`: `13`
  - `bug_fix`: `8`
  - `debug_test`: `6`
  - `exploration`: `3`
  - `migration`: `1`
  - `doc_gen`: `1`
  - `unknown`: `1`
- topology:
  - `dominant_chain`: `92`
  - `mixed`: `7`
  - `multi_root_exploration`: `1`

## Current Interpretation

- The native lane is valid and strict.
- The native lane target has been met.
- The current strict set is useful for descriptive baseline work and now large enough to support the next phase of hypothesis validation.

## Expansion Priorities

### Priority 1: Add non-anthropic native sessions

Goal: reduce runtime concentration and make runtime comparisons less dominated by one family. This is now a future refresh goal rather than a Phase 3C blocker.

Targets:
- `codex`: more than `2` strict native sessions
- `claude`: more than `1` strict native session
- `aider`: more than `1` strict native session
- add at least one more native session from a non-Anthropic runtime with clear provenance

### Priority 2: Add native sessions with underrepresented task types

Goal: widen the task mix inside the native lane. This is now a future refresh goal rather than a Phase 3C blocker.

Targets:
- `debug_test`
- `migration`
- `doc_gen`
- `project_init`
- `bug_fix` and `review` outside the current dominant pattern

### Priority 3: Add native sessions that are not pure dominant_chain

Goal: observe whether native lane can surface more branching or convergence structure. This is now a future refresh goal rather than a Phase 3C blocker.

Targets:
- `mixed`
- `multi_root_exploration`
- future native fan-in / branch-collapse exemplars if real_work sessions produce them

## Suggested Next 20 Native Sessions

Recommended balance for the next batch during the original expansion phase:

- 8 sessions: non-Anthropic runtime comparison
- 6 sessions: underrepresented task types
- 4 sessions: branchy or multi-root candidates
- 2 sessions: failure or near-failure real_work sessions

## Post-Expansion Checklist

After each new native batch, recompute and record:

- native strict count
- runtime distribution
- task-type distribution
- topology distribution
- failure / near-failure count
- human_intervention count
- dominant_chain ratio
- demo vs non-demo separation
- non-Anthropic share

## Inclusion Rule for New Native Sessions

To enter the strict native lane, a session should have:

- `data_origin = native`
- `task_source = real_work`
- `runtime` explicitly labeled
- `task_type` explicitly labeled
- `success` explicitly labeled
- provenance marked as `annotation` or `explicit_sidecar`

## What Not to Do

- Do not promote demo sessions into native.
- Do not use proxy-mediated sessions as native without explicit review.
- Do not count controlled benchmark data as native lane evidence.
- Do not treat dominant_chain abundance as a sufficient reason to stop collecting native sessions during the expansion phase.

## Next Recompute

After the next collection batch, recompute:

- native strict count
- runtime distribution
- task-type distribution
- topology distribution
- non-dominant topology count
- near-miss count

## Expansion Goal

The native expansion target has been reached. Future native refreshes should preserve provenance discipline and continue to increase the share of non-Anthropic runtime, low-frequency task types, and non-dominant topology shapes as new real_work sessions appear.
