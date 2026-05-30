# Phase 3D Tier 2 Readiness v0.2.5

This document records whether the current native lane is ready for the Tier 2 hypothesis group.

Tier 2 covers failure / near-failure morphology and human intervention morphology. These hypotheses are structurally important, but they require a denser subset than the current native lane provides.

## Corpus Context

- corpus version: v0.2.5
- corpus snapshot baseline: sessions `980`
- strict research-grade sessions: `157`
- native strict sessions: `100`
- lane scope: native lane
- data_origin labeled sessions: `980`
- missing data_origin sessions: `0`

## Tier 2 Hypothesis Group

Tier 2 includes:

- H-FM-001
- H-FM-002
- H-IM-001
- H-IM-002
- H-EV-004
- H-EV-005

## Current Native-Lane Evidence

- native failure sessions: `1/100`
- native human_intervention=true sessions: `5/100`
- native success=false session ids:
  - `aider_902f54e8`
- native human_intervention=true session ids:
  - `0a2ab964-b056-425b-b7d3-4a04b6e5a4af`
  - `1a00157a-1359-4981-a11d-21f8164b2130`
  - `66808ae5-0da5-4790-b6ac-0158b9f26fae`
  - `e7fc44f1-0bfa-45d5-96b5-2f71dd015cd7`
  - `f4b12241-c80c-4fa3-9201-2d218db6030c`

## Proxy-Mediated Failure Candidate

- `7de9a576-5306-4f0b-8950-53938c6b8dd9`
  - runtime: `anthropic`
  - task_type: `debug_test`
  - task_source: `proxy`
  - data_origin: `unknown`
  - success: `false`
  - human_intervention: `false`

## Additional AskUserQuestion Human-Intervention Examples

These sessions are outside the native lane but now explicitly marked as `human_intervention=true` because the raw traces contain `AskUserQuestion` events.

- `e68b4fe5-0034-4acf-877d-954e6287e00b`
  - runtime: `anthropic`
  - data_origin: `unknown`
  - human_intervention: `true`

- `908184bd-5602-4f6b-97e1-36293069d20f`
  - runtime: `unknown`
  - data_origin: `unknown`
  - human_intervention: `true`

## Readiness Assessment

Tier 2 is not yet ready for full validation.

### Why it is not ready

- Failure and near-failure coverage is too sparse for stable morphology comparisons.
- Human-intervention coverage now has positive examples in the native lane, but it is still too sparse for stable morphology comparisons.
- The single native failure example is insufficient to separate failure morphology from idiosyncratic session behavior.
- The current corpus can register Tier 2 hypotheses, but it cannot yet support strong or even moderately stable descriptive checks for the whole group.
- Three controlled-benchmark pilot sessions exist, but they do not alter the native Tier 2 readiness gate.

## What Can Be Said Now

- Tier 2 hypotheses remain valid registry entries.
- Tier 2 hypotheses should remain open.
- The current corpus is better suited to identify acquisition targets than to validate Tier 2 claims.

## Immediate Acquisition Targets

1. Native failure and near-failure sessions.
2. Native human-intervention sessions.
3. Native sessions with explicit correction triggers.
4. Native sessions where failure is followed by measurable topology transition.

## Recommendation

Keep Tier 2 in the registry, but defer validation until the native lane has a materially larger failure/intervention subset.
