# Project A Pilot Plan

This is the first pilot application repo for the cross-project prompt morphology study.

## Why This Repo

`Project A` is well-suited to long-chain calibration and correction-style tasks. It naturally produces cases where prompt structure may influence:

- fallback behavior
- safety gating
- review loops
- correction triggers
- near-failure recovery

## Suggested Task Types

- signature calibration
- table-vs-title-block ambiguity
- rule conflict resolution
- review and correction
- failing test repair
- workflow regression repair

## Suggested Pilot Scope

- 5 real tasks
- 2 to 3 prompt variants per task
- 1 fixed runtime where possible
- same commit baseline across variants

## What to Measure

- whether expanded prompts reduce ambiguous retries
- whether expanded prompts reduce human intervention
- whether expanded prompts improve final outcome quality
- whether expanded prompts over-constrain the task and hide useful exploration

## Project Output

Produce a project-level decision page answering:

- should automatic prompt expansion be recommended here
- which task types benefit
- which task types are harmed
- which prompt templates are reusable
- what execution checklist should be adopted
