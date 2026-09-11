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

---

## Pressure #004

**Date**: 2026-05-24
**Context**: Partial sessions and windowed analysis

### Problem

A trace fragment may begin with an event whose `parent_event_id` belongs to an
earlier fragment or external root. Treating that ID as a local graph node made
`stats`, `critical-path`, and connected components misleading.

### Action

No schema change. Stored references retain provenance, while analysis now
builds edges only from IDs present in the loaded session. Boundary children
are local roots; missing non-`root_` references remain validation warnings.

---

## Pressure #005

**Date**: 2026-09-11
**Agent**: DeepSeek Harness (session log parser)
**Sessions**: 4 real sessions, 945–3315 events (see `docs/case-studies/dsh-native-causality.md`)

### Problem

DSH is the first runtime that persists real timing and real fan-out/fan-in,
and it strains three schema edges:

1. **`duration_ms` = dispatch→resolution, not execution.** Derived from the
   `tool/call` → `tool/result` record gap. Background/parked calls resolve
   after session idle: medians land at 0.1–1.4 s, but one `run_code` call
   measures ~1023 h wall-clock. Downstream duration stats silently mix busy
   time with process downtime.
2. **Cross-session delegation is inexpressible.** DSH spawns sub-agents as
   separate session files (`delegationDepth` in the header). A parent's
   `subagent` tool call and the child session's root event cannot be linked:
   `parent_event_id` is scoped per session and there is no event-id namespace
   or `external_ref` field.
3. **Tool errors have no home.** `tool/result` carries `isError`; today it is
   smuggled into `tool_output` as a text marker. A first-class boolean/enum
   (or `metadata["is_error"]`) would let `stats`/`patterns` separate retry
   loops from genuine iteration (connects to Pressure #003's repetition note).

### What the schema got right

- Comma-separated multi-parent `parent_event_id` handled 6-parent fan-in
  natively — first real (non-fixture) fan-in workload, no mutation needed.
- `event_type` (`user_input`, `context_update`) and `caused_by` mapped DSH's
  turn roots and slash commands without new types.
- Append-only JSONL survived sessions whose zstd stream was mid-write
  (partial tail skipped as malformed line by the parser).

### Action

No schema change yet. Options parked: split `duration_ms` into
`run_ms`/`wait_ms` (or define semantics), an `external_ref`-style field for
cross-session edges, and an error flag. Revisit when a second runtime with
measured timing (or a delegation-aware consumer) shows up — per semantic
restraint, one runtime is not enough evidence to promote new fields.

**Follow-up (same day, Pressure #006 scan)**: the cross-session half of this
was worse than it looked in our favor — DSH *does* persist delegation
grounds: all 402 delegated session headers carry `parentSession`, every one
resolving to a real session directory. `causetrace dsh-tree` (read-only
`session_forest()`) now renders the forest without touching the schema;
what remains genuinely inexpressible is the *event-level* edge (parent's
`subagent` call → child's first reasoning step), since `parent_event_id`
stays session-scoped by design.

## Pressure #006

**Date**: 2026-09-11
**Agent**: DeepSeek Harness (full-corpus scan: 577 sessions, ~1.6 M records)
**Context**: follow-up census after Pressure #005; two channels were found in
the logs and are now extracted or explicitly discarded.

### Problem

1. **Mid-turn steering is not a turn, but the schema calls it one.** DSH
   splices user messages with `target:"next-step"` (861 splices corpus-wide;
   32–37% of "roots" in interactive sessions like design-oa's 137). These
   re-land as `user/message` records indistinguishable from genuine turn
   starts. The parser now correlates `agent/inbox/spliced` by message
   id/rpcId and marks `tool_input["mid_turn"] = true`, but `user_input`
   itself has no intervention vs turn-root distinction, so `stats` turn
   metrics (tools/turn, roots) still mix the two semantics.
2. **Nested dispatch depth was invisible until now.** `run_code` logs every
   inner tool call as `tool/code-dispatch-start` / `tool/code-dispatch` with
   hierarchical `subCallId` (`<parent>:code:N`) — 56 048 pairs corpus-wide.
   Extracting them (parser v2) grows code-preset sessions by 53–66%
   (762a: 3315 → 5071 events) and exposes a genuine second DAG level. The
   pressure: fidelity measurement drops where structure got deeper
   (df4c: 88% → 50% child agreement) — shallower graphs only *looked* more
   predictable. Metrics that compare across parser versions must pin the
   extraction depth.
3. **Model-failure channel has no home.** 1068 `llm/retry` records carry
   `{turn, step, provider, failure.code ∈ TIMEOUT/RATE_LIMIT/TRANSPORT/SERVER,
   retry/maxRetries, delayMs}` — a per-step reliability signal with exact
   causal attribution. Today it is discarded (no event_type fits;
   `context_update` would drown it among slash commands).

### What held up

- The `tool/call → tool/result` merge pattern ported 1:1 to the nested
  dispatch pairs — same convention, real durations (median 187 ms).
- Orphan dispatch records (parent call never observed) are skipped, not
  fabricated — fidelity-over-coverage held even when it lost events.

### Action

Parser v2 ships the nested layer + `mid_turn` marker (data stays inside
approved fields; no schema change). Keep #1 (turn-semantics split) and #3
(retry/failure event or metadata convention) open for the next runtime with
structured retries or in-flight steering.
