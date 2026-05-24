# ToolEvent Schema

Formal field definitions for the causetrace data model. Version: v0.1.

## Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | `str` | always | Schema version string (currently `"0.1"`). Used for future migration safety. |
| `event_id` | `str` (uuid hex, 12 chars) | always | Unique event identifier |
| `tool_name` | `str` | always | Tool invoked: e.g. `"Bash"`, `"Read"`, `"Write"`, `"Edit"`, `"Grep"`, `"Glob"`, `"WebFetch"` |
| `tool_input` | `dict` or `str` | always | Serialized input arguments |
| `tool_output` | `dict` or `str` or `null` | optional | Serialized output/result |
| `timestamp` | `str` (ISO 8601) | always | When the event was recorded |
| `duration_ms` | `float` or `null` | optional | Execution duration in milliseconds |

## Causal Fields (v0.1)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `parent_event_id` | `str` or `null` | optional | Causal parent `event_id`. Comma-separated for multi-parent (fan-in) DAGs; retained when the parent is outside a partial session |
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
- Multi-parent: `parent_event_id` uses comma as separator (e.g. `"evt_a,evt_b"`). Parsed for integrity in `core.py` and for local graph analysis in `analysis.py`.

## Schema Invariants

1. Append-only: events are never mutated after storage. Each event is a single JSON line.
2. Reference integrity: full captured sessions should resolve parent IDs locally; imported or sliced sessions may retain external parents. `validate` warns for missing non-`root_` parents.
3. Event order: loaded events are sorted by `timestamp` for deterministic rendering.

## Local Analysis Boundary

`stats`, `roots`, `critical-path`, `patterns`, and `compare` analyze only
edges whose parent and child exist in the loaded session. An event whose
parents are all external is a local root. This rule prevents external IDs from
appearing as synthetic connected-component nodes and keeps partial sessions
usable without mutating stored provenance.

## Schema Policy

### event_type 准入原则

`event_type` 是 first-class 分类字段，只应包含被 >=3 个独立 runtime 验证稳定出现的类型。
新的事件分类应先在 consumer 侧以标签或 metadata 形式试验，不提升到 `event_type`。

```
层级:  event_type        ← first-class, 仅放已验证稳定的类型
       metadata["subtype"]  ← 试验性分类, 不污染 schema
```

当前已批准的 `event_type` 值: `tool_call`, `reasoning`, `context_update`, `user_input`。
