# Schema Pressure Log

> Records every instance where real trace data exposed a gap, awkwardness,
> or ambiguity in the current ToolEvent schema.
>
> This is the evidence base for future schema evolution — not design, but
> runtime reality pressure.

## How to use

When you encounter a trace that is difficult to express with the current schema:

1. Describe the trace pattern (what happened)
2. Note which field(s) felt overloaded or insufficient
3. Note what you *wanted* to express but couldn't cleanly
4. Date and context (agent type, session length, etc.)

Entries are raw observations. No judgment. No action required.

---

## Entries

*(No entries yet. This file exists to capture the first pressure point.)*

---

## Pressure #001

**Date**: 2026-05-14
**Agent**: Claude Code (hooks)
**Session**: 270e9651-6b70-499e-84c8-9beb36d6fa75 (189 events, 81 min)

### Problem

The Claude Code hook bridge produced a flat trace where every event is a root.
Causal linking was silently broken — no parent_event_id was ever set. The schema
accepted the data without error (`validate` passes clean), but the trace is
causally meaningless.

### Root cause

The hook bridge created a new `TraceRecorder` per event and never passed
`parent_event_id` to `record_call()`. The event_id chain was written and read
but the actual link was dropped between reading from the `.pre` file and calling
`record_call()`.

### What the schema got right

- The data is valid per all schema invariants
- Chronological ordering is preserved
- roundtrip serialization is consistent

### What the schema couldn't express

There is no signal in the schema that says "this session should have had causal
structure but something went wrong." A flat trace is indistinguishable from a
session where every event genuinely has no causal parent.

### What would help

A `causality_complete` flag or heuristic: if a session has >N events and zero
parent_event_id chains, it's likely broken rather than genuinely flat.
Alternatively, the hooks could emit a session-level metadata event that
declares the expected linking strategy.
