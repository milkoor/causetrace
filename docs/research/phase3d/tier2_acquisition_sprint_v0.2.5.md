# Phase 3D-T2 Acquisition Sprint v0.2.5

This note turns the current Tier 2 gap into an explicit acquisition sprint.

Tier 2 remains acquisition-only until the failure / near-failure / intervention subset becomes materially larger.

## Current Corpus Baseline

- sessions: `980`
- events: `27389`
- strict research-grade sessions: `157`
- native strict sessions: `100`
- native failure: `1`
- native human_intervention=true: `5`
- native failure anchor: `aider_902f54e8`
- proxy failure candidate: `7de9a576-5306-4f0b-8950-53938c6b8dd9`
- explicit AskUserQuestion intervention examples:
  - `e68b4fe5-0034-4acf-877d-954e6287e00b`
  - `908184bd-5602-4f6b-97e1-36293069d20f`
- controlled_benchmark pilot sessions: `3`

## Sprint Goal

Move Tier 2 from acquisition-only toward exploratory-validation-ready by growing the native failure / near-failure / intervention subset.

## First-Stage Targets

- native failure: `5-10`
- native near-failure: `10`
- native human_intervention=true: `10`
- explicit correction trigger: `20`
- non-anthropic failure / near-failure: `5`
- failure / near-failure across at least `3` runtimes

## Acquisition Rules

- Do not fabricate artificial failures.
- Prefer real task failures, unresolved test failures, abandoned sessions, and genuine recovery attempts.
- Keep near-failure sessions.
- Human intervention must be explicitly evidenced.
- Record correction triggers in notes when available.
- Do not promote proxy candidates into native without evidence.

## Recommended Task Categories

- `bug_fix`
- `test_repair`
- `dependency_upgrade`
- `refactor regression`
- `long_session_repair`
- `feature_add` with failing tests
- `repo_analysis` with correction
- `multi-file repair`

## Post-Sprint Review Checklist

After the next acquisition batch, report:

- native failure count
- native near-failure count
- native human_intervention=true count
- correction trigger count
- runtime distribution
- task_type distribution
- topology distribution
- whether Tier 2 is now exploratory-validation-ready

## Scope Note

This is a native-lane acquisition sprint. It does not ingest controlled benchmark data or external trajectories, and it does not change the topology taxonomy.
