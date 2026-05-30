# Controlled Benchmark Protocol (v0.2.5)

This protocol defines how controlled benchmark data may be used in causetrace without contaminating the native lane.

## Purpose

Controlled benchmarks are for same-task, multi-runtime comparisons.

They are not native evidence. They are not a substitute for real_work corpus capture.

## Candidate Sources

- SWE-Gym
- SWE-EVO

These sources are candidates only until manually reviewed and lane-assigned.

## Required Conditions Before Ingestion

Before any controlled benchmark session is counted in the corpus, all of the following must be true:

1. manual origin annotation has been performed
2. `data_origin` is explicitly set to `controlled_benchmark`
3. the lane baseline has been recomputed
4. the lane inclusion rules have been checked
5. the session is not being used as native evidence

## Inclusion Rules

- Keep controlled benchmark sessions in their own lane.
- Use them for same-task, multi-runtime contrasts.
- Prefer tasks that can be repeated across at least two runtimes.
- Record the benchmark family and task identity in metadata or provenance notes.

## Exclusion Rules

- Do not promote benchmark traces into native claims.
- Do not use benchmark traces to backfill native gaps.
- Do not infer benchmark status from task shape alone.
- Do not treat benchmark outcomes as direct runtime morphology truth without corpus comparison.

## Recommended Benchmark Shapes

- narrow bug fix with a known failing test
- small feature task with a bounded acceptance check
- repo review task with a stable rubric
- short migration or configuration task

## Baseline Questions

For each controlled benchmark run, ask:

- Does topology remain stable across runtime families?
- Does retry density change after controlling for task identity?
- Does branch collapse appear under the same task for multiple runtimes?
- Does human intervention affect the same-task comparison?

## Output Expectations

Every controlled benchmark record should preserve:

- runtime
- task_type
- task_source
- success
- human_intervention
- `data_origin = controlled_benchmark`
- provenance for each field

## Relation to Phase 3C

This protocol is still subordinate to Phase 3C.

Phase 3C remains the current phase until:

- native lane is expanded
- manual origin annotation is stable
- controlled benchmark candidates are intentionally introduced

## Relation to Core

Controlled benchmark logic belongs in research governance and future tooling, not in the core runtime morphology model.
