# Phase 3B Runtime Signal After Controls: v0.2.5

Date: 2026-05-29

This report asks the only Phase 3B question that matters:

> After removing the main confounders, does a runtime-level descriptive signal
> still remain?

## Control Sets

- strict_all: `107`
- strict_non_demo: `46`
- strict_success_only: `105`
- strict_failure_only: `2`

## Runtime Means After Demo Removal

| runtime | sessions | avg branch density | avg transition entropy | avg path reuse ratio |
| --- | ---: | ---: | ---: | ---: |
| aider | 1 | 0.0059 | 0.0000 | 1.0000 |
| anthropic | 42 | 0.1193 | 2.3111 | 0.3434 |
| claude | 1 | 0.0038 | 3.5199 | 0.6105 |
| codex | 2 | 0.0285 | 2.3557 | 0.6482 |

## Observations

- A runtime-level signal still exists after removing `demo`, but the sample is
  heavily concentrated in `anthropic`.
- `claude` and `aider` are single-session points and are not suitable for a
  stable claim.
- `codex` is too small to support a robust comparison.

## What Survives the Controls

- The corpus still shows structural differences across runtimes.
- The signal is descriptive, not predictive.
- The signal is not strong enough to call a fingerprint.

## Negative Results

- No stable runtime fingerprint can be claimed after the controls.
- No stable runtime ranking should be inferred from these counts.
- Phase 3B does not yet justify moving to prediction or anomaly modeling.
