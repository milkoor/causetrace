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

---

## Pressure #002

**Date**: 2026-05-14
**Agent**: Claude Code (hooks)
**Session**: 270e9651-6b70-499e-84c8-9beb36d6fa75 (241 events → 240 validated, of which 57 post-fix)

### Problem

After fixing the hook causality bug (Pressure #001), events now form a single
56-event linear chain. Every tool call is causally linked to the previous one
because the hook bridge's PreToolUse always reads `_last_event_id` and sets it
as the parent. This produces tool-level causality ("this tool was invoked after
that tool"), not semantic causality ("this tool was invoked because the user
asked a new question").

Example: reading five files during a code review forms `Read(A) → Read(B) →
Read(C) → Read(D) → Read(E)` — but the real structure is that all five reads
are peers under a single user intent ("review the codebase"), not a sequential
chain where each read depends on the previous.

### What the schema got right

- parent_event_id is technically correct at the tool level
- tree / graph / why all produce consistent output
- fan-out (one event with multiple children) IS detected correctly when it occurs

### What the schema couldn't express

There is no way to signal "this event starts a new semantic turn." The hook
bridge has no access to user intent boundaries — it only sees individual tool
events. Without a `turn_id` or `user_message_id` in the Claude Code hook event
payload, the bridge can't distinguish "same reasoning turn" from "new user
request."

### What would help

The schema itself is sufficient. The gap is in the **hook input signal**: if
Claude Code's hook events included a turn identifier or user-message boundary,
the hook bridge could call `new_group()` at the right moments, producing
multiple independent causal trees that match semantic structure.

### Action

No schema change needed. This is a runtime signal gap. Revisit when Claude Code
exposes turn boundaries in hook events.

---

## Pressure #003

**Date**: 2026-05-14
**Agent**: Codex CLI + OpenCode (native parsers)
**Sessions**: Codex 019e2553-ade5 (465 lines → 116 events), OpenCode from DB (91 events)

### Problem

Two new runtime formats were discovered that don't fit the original action/observation model:

**Codex CLI** (real rollout format):
- `response_item/function_call` with `name`, `arguments`, `call_id`
- `response_item/function_call_output` paired by `call_id`
- `event_msg/agent_message` for reasoning
- No `mcp_tool_call_begin/end` or `exec_command_begin/end` as assumed from protocol.rs

**OpenCode** (SQLite DB):
- `part` table with `type="reasoning"` and `type="tool"` entries
- `message.parentID` provides native causal tree structure
- Timestamps are stored as milliseconds or microseconds with scale detection needed

### What the schema got right

- `tool_name`, `tool_input`, `tool_output` map cleanly to both formats
- `parent_event_id` works for both linear chains (Codex) and tree structures (OpenCode)
- `event_type` ("reasoning" / "tool_call") is sufficient for both
- `call_id` pairing maps naturally to existing sequential parent-child linking

### What the schema couldn't express

- **Codex tool looping**: The proxy+DeepSeek combo caused repeated `exec_command` calls in a loop (>100 iterations). The schema has no way to flag "suspicious repetition" vs "genuine multi-step workflow."
- **Paired call_id semantics**: `function_call` → `function_call_output` is a natural pair, but the schema collapses them into a single `tool_call` event. The pairing information (which call produced which output) is implicit in chronological ordering, not explicit.
- **call_id as cross-reference**: OpenCode and Codex both use call IDs for pairing, but this data is lost during schema translation.

### What would help

- A `pair_id` or `group_id` field to explicitly track begin/end or call/result pairing
- A `repetition_count` or `loop_detected` heuristic field for sessions with identical consecutive tool calls (Codex proxy quirk)

### Action

No schema change for v0.1.2. The current ToolEvent fields are expressive enough for
causal chain construction. The pairing gap is noted for v0.2 if cross-referencing
becomes a priority.
