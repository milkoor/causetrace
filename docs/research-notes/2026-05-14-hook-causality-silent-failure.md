# Hook causality silently failed for 61 sessions

## Problem

The Claude Code hook bridge had a bug where `parent_event_id` was never passed
to `record_call()`, resulting in every event being a root node. The system gave
no indication of failure — `validate` passes clean on a flat trace.

## Why it was hard to catch

- No integration test for the hook stdin/stdout flow
- Unit tests create chains via direct `TraceRecorder.record_call()` and never
  exercise the actual hook bridge code path
- The schema considers null parent_event_id as valid (a root node), so there's
  no structural error

## Implication

Runtime Integrity tools (validate, tests) are necessary but not sufficient. They
verify *structural* correctness but not *semantic* correctness. A trace can be
structurally valid (all invariants pass) but semantically broken (no causality).

## What this suggests

We need a way to distinguish "intentionally flat" from "broken causality."
Heuristic: a session with many events and zero parent links is suspicious.
But this heuristic could also be wrong for genuinely parallel agents.
