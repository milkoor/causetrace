# Phase 3D Tier 2 Acquisition Plan v0.2.5

Tier 2 is not yet validation-ready. This plan defines the acquisition targets needed to make failure / near-failure / human-intervention hypotheses testable.

## Current Baseline

- native strict sessions: `100`
- native failure sessions: `1/100`
- native human_intervention=true sessions: `5/100`
- only native failure exemplar: `aider_902f54e8`

## Current Progress

- human_intervention acquisition target is partially met with 5 explicit native examples.
- failure coverage remains the primary gap.
- explicit correction-trigger sessions still need more review.

## First-Stage Acquisition Targets

- native failure sessions: `10`
- native near-failure sessions: `10`
- native human_intervention=true sessions: `5`
- explicit correction-trigger sessions: `20`
- failure / near-failure coverage across at least `3` runtimes

## Acquisition Priorities

1. Native failure sessions.
2. Native near-failure sessions.
3. Native human-intervention sessions.
4. Sessions with explicit correction triggers.
5. Non-anthropic failure / near-failure sessions.
6. Multi-runtime failure coverage.

## Recommended Task Types

- `bug_fix`
- `test_repair`
- `dependency_upgrade`
- `refactor gone wrong`
- `long_session_repair`
- `repo_analysis with correction`
- `feature_add with failing tests`

## Acquisition Rules

- Do not fabricate artificial failures.
- Prefer real task failures, abandoned sessions, unresolved test failures, and genuine recovery attempts.
- Near-failure sessions are valid acquisition targets.
- Human intervention must be explicitly noted in metadata notes when present.
- Correction triggers should be recorded in notes when available.
- Do not add new schema fields for this phase.

## Validation Gate

Tier 2 remains acquisition-only until the targets above are materially met.

## Practical Notes

- The current corpus can register Tier 2 hypotheses.
- The current corpus cannot yet validate Tier 2 claims robustly.
- Acquisition should focus on real-world runtime behavior, not constructed failure conditions.
