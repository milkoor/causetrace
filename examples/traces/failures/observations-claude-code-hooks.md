# Failure #001: Claude Code hook — broken causal linking

**Trace**: source session retained locally (189 events, 81 min; not published because it includes local paths)
**Root cause**: The Claude Code hook bridge created a new `TraceRecorder` per PostToolUse
  and never passed `parent_event_id` to `record_call()`.

## Symptoms

- Every event is a root node (flat timeline, no tree structure)
- `causetrace validate` passes (no broken refs — but every parent is null)
- Chronological order is preserved, causality is completely lost

## Root cause detail

In `hooks/claude_code.py`:

1. `_load_pre()` called `_save_last_event_id(session_id, data.get("parent_event_id", ""))`
   — this saved the **parent's** event_id as "last event" instead of the current event's ID
2. PostToolUse handler created a fresh `TraceRecorder()` each time, so
   `self._last_event_id` was always `None`
3. `record_call()` was called without `parent_event_id=`, so it fell back
   to `self._last_event_id` (always `None`)

## Fix

- `_load_pre()` no longer has side effects on the event_id chain
- PostToolUse reads `parent_id = pre_data.get("parent_event_id")` and passes
  `parent_event_id=parent_id` to `record_call()`
- After recording, saves the new event's ID: `_save_last_event_id(session_id, event.event_id)`

## Impact

All 61 existing sessions (including the 189-event 81-minute session) have no
causal structure. Future sessions will have proper parent→child chains.

## Lesson

The hook bridge was never tested end-to-end. The unit tests create chains via
`TraceRecorder.record_call()` but never tested the hook JSON roundtrip.
Add an integration test for the hook stdin/stdout flow.

For a public, sanitized causal trace that exercises the current CLI, run
`causetrace demo` and inspect the generated session with `tree`, `graph`, and
`why`.
