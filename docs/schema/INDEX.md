# Causetrace Schema Evolution Log

> See [SCHEMA.md](SCHEMA.md) for formal field definitions.
> [pressure-log.md](pressure-log.md) captures real trace data that strains the current schema.
>
> Schema is not designed upfront — it emerges from real Runtime data.
> This log records every field addition, change, or removal, along with the
> Runtime behavior observation that triggered it.

## Current Schema (v0.1)

```
ToolEvent:
  schema_version     str         # "0.1"
  event_id          str         # uuid
  tool_name         str         # "Bash", "Read", "Write", "Edit", etc.
  tool_input        dict|str    # serialized input arguments
  tool_output       dict|str    # serialized output/result
  timestamp         str         # ISO 8601
  duration_ms       float|null  # execution duration in ms
  -- causal fields (v0.1) --
  parent_event_id   str|null    # causal parent event_id
  session_id        str|null    # owning session
  event_type        str         # "tool_call" | "reasoning" | "context_update" | "user_input"
  caused_by         str|null    # "user" | "reasoning" | event_id | semantic tag
  model             str|null    # model attribution
  provider          str|null    # runtime provider
  agent             str|null    # agent attribution
```

## Evolution Entries

### 2026-05-13: v0.0 → v0.1 — Added Causality

**Trigger**: Architecture review identified that ToolEvent without `parent_event_id`
captures only "what happened", not "why it happened". Timeline is linear, but
Agent Runtime behavior is a DAG.

**Changes**:
- Added `parent_event_id: Optional[str]` — links to causing event
- Added `session_id: Optional[str]` — enables cross-event session scope
- Added `event_type: str` — distinguishes tool_call from reasoning/context events
- Added `caused_by: Optional[str]` — semantic tag (user/reasoning/task_execution/verification)

**Rationale**: These 4 fields enable:
- Causal tree visualization (`causetrace tree`)
- Replay with provenance (`causetrace replay` shows `← parent`)
- Future behavior graph analysis
- Future anomaly detection (e.g., tool call without parent = potential issue)

**Not added (deferred)**:
- `context_before` / `context_after` — need real data to understand shape
- `group_id` — need multi-turn session data first
- `concurrency_id` — Claude Code runtime is serial for now

---

### 2026-05-14: Deferred — `caused_by` Concern

**Trigger**: Architecture review identified that `caused_by: Optional[str]` mixes
three distinct concepts: semantic labels (`"reasoning"`, `"user"`), structural
references (`event_id`), and heuristic annotations. This will become a
maintainability issue as causal queries grow more sophisticated.

**Status**: Deferred to v0.3+. Not actionable now because:
- `parent_event_id` already handles structural causality; `caused_by` is supplementary
- No real multi-agent trace data exists yet to validate the right abstraction
- Preemptive `causal_type` enums would likely be wrong without data

**Future direction** (candidate split):
- `parent_event_ids: List[str]` — formalize multi-parent as a list
- `causal_type: "structural" | "semantic" | "user" | "heuristic"`
- `semantic_intent: Optional[str]` — the human/semantic label

---

### 2026-05-24: Clarified Partial-Session Parent Semantics (no schema change)

**Trigger**: Session slices and imported traces may retain `parent_event_id`
values whose parent event is outside the loaded JSONL.

**Decision**:
- Raw `parent_event_id` values remain unchanged.
- Analysis commands construct topology only from parent IDs found in the
  loaded session; boundary children are local roots.
- `validate` reports missing non-`root_` references as warnings while malformed
  JSON or cycles remain invalid.

**Rationale**: Partial traces remain analyzable without pretending external
events are part of the local graph or discarding provenance.

---

*Next entry to be written when a Runtime behavior observation forces a schema change.*
