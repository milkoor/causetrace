# Codex CLI tailer format mismatch: `codex_tailer.py` is based on wrong assumptions

## Problem

`causetrace/hooks/codex_tailer.py` was written assuming Codex CLI session data
uses the same structure as generic OpenAI Chat Completions API traces:

```python
# Assumed format (DOES NOT EXIST):
{"type": "action", "action": {"name": "Bash", "input": {...}}}
{"type": "observation", "observation": {"name": "Bash", "output": {...}}}
```

The actual Codex CLI session format is fundamentally different.

## Actual format

Codex CLI stores sessions as rollout JSONL files at:
```
~/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<uuid>.jsonl
```

Each line follows this structure (from `codex-rs/protocol/src/protocol.rs`):

```rust
struct RolloutLine {
    pub timestamp: String,
    #[serde(flatten)]
    pub item: RolloutItem,
}

enum RolloutItem {
    SessionMeta(SessionMetaLine),     // type = "session_meta"
    ResponseItem(ResponseItem),        // type = "response_item"
    EventMsg(EventMsg),                // type = "event_msg"
    TurnContext(TurnContextItem),      // type = "turn_context"
    Compacted(CompactedItem),          // type = "compacted"
}
```

Serialized JSON:
```json
{"timestamp":"...","type":"session_meta","payload":{...}}
{"timestamp":"...","type":"response_item","payload":{"type":"message","role":"developer","content":[...]}}
{"timestamp":"...","type":"event_msg","payload":{"type":"agent_reasoning","text":"..."}}
{"timestamp":"...","type":"event_msg","payload":{"type":"mcp_tool_call_begin","call_id":"...","invocation":{...}}}
{"timestamp":"...","type":"event_msg","payload":{"type":"exec_command_begin","call_id":"...","command":[...]}}
{"timestamp":"...","type":"turn_context","payload":{"model":"gpt-5.5",...}}
```

## Key differences

| Aspect | `codex_tailer.py` assumption | Actual format |
|---|---|---|
| Top-level types | `action`, `observation` | 5 types: `session_meta`, `response_item`, `event_msg`, `turn_context`, `compacted` |
| Tool calls | `action` entries | Paired `mcp_tool_call_begin/end` + `exec_command_begin/end` in event_msg |
| Reasoning | Not handled | `event_msg/agent_reasoning` |
| Output | `observation` entries | `mcp_tool_call_end.result.content` or `exec_command_end.stdout/stderr` |
| Role/content | Chat format: role+content | Responses API format with development_instructions |

## What's available in the new codex_parser.py

The new `causetrace/hooks/codex_parser.py` handles:

- **`event_msg/agent_reasoning`** → `event_type="reasoning"`, `tool_name="Thinking"`
- **`event_msg/mcp_tool_call_begin/end`** → Paired tool calls with duration
- **`event_msg/exec_command_begin/end`** → `tool_name="Bash"` with command + output
- **`response_item`** → `tool_name="Response"` for assistant text outputs
- **`session_meta`** → model/provider extraction

It also tracks in-flight call_ids to pair begin/end events and handles
orphan end events gracefully.

## Status

- `codex_tailer.py` — **KNOWN BROKEN**. Its format assumptions do not match
  any known version of Codex CLI rollout data. It will produce empty results
  or miss all events.
- `codex_parser.py` — **VALIDATED** 2026-05-14 against real session
  `019e2553-ade5` (Codex v0.130.0 via DeepSeek proxy). Extracted 116 events
  (114 tool_call + 2 reasoning) from 465-line rollout JSONL. Actual format uses
  `response_item/function_call` + `response_item/function_call_output` paired by
  `call_id`, plus `event_msg/agent_message` for reasoning.
- **Key format from real data** (not protocol.rs):
  - `response_item` with `payload.type = "function_call"` → tool call events
  - `response_item` with `payload.type = "function_call_output"` → paired output
  - `event_msg` with `payload.type = "agent_message"` → reasoning
  - `event_msg` with `payload.type = "token_count"` → token usage (skipped)

## Status

`causetrace enrich-codex` is now functional. `codex_tailer.py` remains broken
but is a separate code path (used by `causetrace codex`).

See: https://github.com/openai/codex
