# ToolEvent Schema

Formal field definitions for the causetrace data model. Version: v0.1.

## Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | `str` (uuid hex, 12 chars) | always | Unique event identifier |
| `tool_name` | `str` | always | Tool invoked: e.g. `"Bash"`, `"Read"`, `"Write"`, `"Edit"`, `"Grep"`, `"Glob"`, `"WebFetch"` |
| `tool_input` | `dict` or `str` | always | Serialized input arguments |
| `tool_output` | `dict` or `str` or `null` | optional | Serialized output/result |
| `timestamp` | `str` (ISO 8601) | always | When the event was recorded |
| `duration_ms` | `float` or `null` | optional | Execution duration in milliseconds |

## Causal Fields (v0.1)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `parent_event_id` | `str` or `null` | optional | Causal parent `event_id`. Comma-separated for multi-parent (fan-in) DAGs |
| `session_id` | `str` or `null` | optional | Owning session scope |
| `event_type` | `str` | optional, defaults to `"tool_call"` | `"tool_call"` \| `"reasoning"` \| `"context_update"` \| `"user_input"` |
| `caused_by` | `str` or `null` | optional | Semantic tag: `"user"` \| `"reasoning"` \| `event_id` \| freeform label |

## Attribution Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | `str` or `null` | optional | Model identifier (e.g. `"claude-sonnet-4-20250514"`) |
| `provider` | `str` or `null` | optional | Provider identifier (e.g. `"anthropic"`, `"openai"`) |
| `agent` | `str` or `null` | optional | Agent identifier (e.g. `"claude-code"`, `"opencode"`, `"aider"`, `"copilot"`) |

## Serialization Rules

- `tool_input` and `tool_output` are JSON-serialized. String values are truncated at 2000 characters during serialization (`_safe_serialize` in `core.py`).
- Fields with `null`/empty values are omitted on serialization (keep payload compact).
- Multi-parent: `parent_event_id` uses comma as separator (e.g. `"evt_a,evt_b"`). Parsed by `_parse_parents()` in `core.py`.

## Schema Invariants

1. Append-only: events are never mutated after storage. Each event is a single JSON line.
2. No orphan references: `parent_event_id(s)` should reference existing `event_id`s within the same session (enforced by test `test_causality_no_orphan_references`).
3. Event order: loaded events are sorted by `timestamp` for deterministic rendering.
