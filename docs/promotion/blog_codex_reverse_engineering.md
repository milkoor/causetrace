# Reverse engineering Codex CLI rollout traces

---

I spent a weekend building a DeepSeek proxy for Codex CLI so I could generate real tracing data. The proxying was straightforward. What I found when I looked at the actual trace files was not.

**The documented format and the real format don't match.**

This is the story of that mismatch: what I expected, what I found, and why it matters if you're building runtime tooling for coding agents.

---

## The setup: why a proxy?

Codex CLI uses OpenAI's Responses API (via their SDK). DeepSeek only supports Chat Completions. To use DeepSeek as the backend, I needed a translation proxy — intercept Responses API calls and translate them to Chat Completions.

The proxy (`tools/codex_deepseek_proxy.py`) was straightforward:

1. Accept POST requests at `/responses` (or `/v1/responses`)
2. Translate the `input` field (Responses API format) to Chat Completions `messages`
3. Translate tool definitions from `{"name": "bash", "parameters": {...}}` to `{"type": "function", "function": {"name": "bash", "parameters": {...}}}`
4. Send to DeepSeek, receive a Chat Completions response, translate it back to Responses API event format
5. Return the response as a JSON body (not SSE stream — DeepSeek's streaming output is incompatible)

The translation is mechanical, but there was one critical detail: **Codex expects `function_call` items with status `"in_progress"`, not `"completed"`.** The status tells Codex the tool has been invoked but hasn't completed yet — it's waiting for `function_call_output` to arrive. Set it to `"completed"` and Codex thinks the tool already ran and has no output.

After getting the proxy working, Codex CLI ran happily against DeepSeek. Now I had real trace data.

---

## What I expected to see

Codex CLI stores session data as rollout JSONL files in `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`. Each line is a JSON object with a `type` field and a `payload`.

Based on reading Codex CLI's source code (specifically `protocol.rs`), I expected event types like:

- `exec_command_begin` / `exec_command_end` — command execution boundaries
- `mcp_tool_call_begin` / `mcp_tool_call_end` — MCP tool call boundaries
- `agent_reasoning` — the model's internal reasoning

I modelled my first parser around these. It produced exactly **1 event per session**. Something was very wrong.

---

## What the real format looks like

I dumped a raw rollout file. Here's the actual format (validated against Codex v0.130.0):

```
{"timestamp":"...","type":"session_meta","payload":{"model_provider":"deepseek","cli_version":"0.130.0"}}
{"timestamp":"...","type":"event_msg","payload":{"type":"task_started",...}}
{"timestamp":"...","type":"response_item","payload":{"type":"message","role":"developer","content":[...]}}
{"timestamp":"...","type":"turn_context","payload":{"model":"deepseek-chat",...}}
{"timestamp":"...","type":"event_msg","payload":{"type":"token_count",...}}
{"timestamp":"...","type":"response_item","payload":{"type":"function_call","name":"exec_command","arguments":"{}","call_id":"call_xxx"}}
{"timestamp":"...","type":"response_item","payload":{"type":"function_call_output","call_id":"call_xxx","output":"..."}}
{"timestamp":"...","type":"response_item","payload":{"type":"message","role":"assistant","content":[{"type":"output_text","text":"..."}]}}
{"timestamp":"...","type":"event_msg","payload":{"type":"agent_message","message":"..."}}
{"timestamp":"...","type":"event_msg","payload":{"type":"task_complete",...}}
```

The core pattern is:

- **`response_item/function_call`** — the model requested a tool invocation. Contains `name`, `arguments` (JSON string), and `call_id`.
- **`response_item/function_call_output`** — the result of that invocation. Contains `call_id` (paired with the corresponding `function_call`) and `output` (string).
- **`event_msg/agent_message`** — the model's reasoning text. This is where thinking/reasoning blocks live.
- **`response_item/message` (role=assistant)** — the model's text response to the user.
- **`event_msg/token_count`** — token usage tracking, interspersed everywhere.

There are no `exec_command_begin`, `exec_command_end`, `mcp_tool_call_begin`, or `mcp_tool_call_end` events. At least not in the v0.130.0 rollout format.

---

## The three things that surprised me

### 1. call_id pairing, not nesting

Tool invocations and their results are **flat, linked by `call_id`** — not nested events. The `function_call` line appears, then later (potentially many lines later) the matching `function_call_output` appears with the same `call_id`. Between them can be token_count events, reasoning messages, or other function calls.

This means the parser must buffer pending calls and match them by `call_id`, rather than assuming a begin/end nesting structure.

### 2. Token counts are everywhere

`event_msg/token_count` events appear between almost every meaningful event. They don't seem to follow a predictable cadence — sometimes before a function call, sometimes after, sometimes between reasoning blocks. They're noise for causal tracing but you need to handle them without breaking the event chain.

### 3. No explicit causality

The rollout format has no `parent_event_id` or equivalent causal field. Causality must be inferred from ordering: the model receives `function_call_output`, then decides what to do next — so the next `function_call` or `agent_message` after an output is causally dependent on it. This is the same temporal heuristic that log-based tailers for Copilot and Continue.dev use.

---

## The translation chain

Here's what actually happens when Codex CLI runs through the DeepSeek proxy:

```
Codex CLI (Responses API)
  → POST /responses { input: [...], tools: [...] }
    → Proxy translates input → messages, tools → function definitions
    → DeepSeek Chat Completions API
      → Proxy translates response → Responses API events
        → Codex receives function_call with call_id
        → Codex executes the tool
          → Codex sends function_call_output back
            → Proxy translates to next request
              → Loop until task_complete
```

Each loop iteration in the proxy is a single Chat Completions call. The response contains either:
- Tool calls (function_call items) → translate to Responses API output items
- A text response (message content) → translate as assistant message
- Both (the model can return text + tool calls in the same response)

---

## Implications for runtime tooling

If you're building observability or tracing for coding agents, the Codex CLI format teaches a few lessons:

1. **Don't trust source code comments, trust wire data.** `protocol.rs` suggested one format; the actual rollout files used another. The source code showed the internal data structures, not the serialization format.

2. **call_id pairing is a recurring pattern.** Both Codex CLI and OpenAI's Responses API use `call_id` to link function calls to their outputs. It's not nesting — it's a flat key-value relationship. Parser design should match: buffer by `call_id`, match on arrival.

3. **Log-based causality is the fallback, not the primary model.** Codex CLI rollout data has no causal links. They must be inferred. This is fine for the ~80% case, but it means you can't always tell which `function_call_output` triggered which subsequent `function_call`.

4. **The event stream is heterogeneous.** Token counts, metadata, and control events are mixed with function calls. A robust parser must distinguish signal from noise without assuming a fixed event sequence.

---

## The open-source implementation

The parser I ended up building (`causetrace/hooks/codex_parser.py`) handles:

- `response_item/function_call` → creates a pending call tracked by `call_id`
- `response_item/function_call_output` → matches by `call_id`, updates the corresponding event with `tool_output`
- `event_msg/agent_message` → creates a reasoning event with causal parent linking
- `response_item/message (assistant)` → creates a response text event

It turns a 465-line rollout file into 116 causally-linked events — a parser accuracy improvement from effectively 0% (the protocol.rs-based attempt) to 100% of discoverable events in the real format.

The full source is available at:
https://github.com/milkoor/causetrace/blob/main/causetrace/hooks/codex_parser.py

And the DeepSeek proxy that made the real traces possible:
https://github.com/milkoor/causetrace/blob/main/tools/codex_deepseek_proxy.py

---

*This is the second in a series about coding agent runtime observability. First post: [Coding agents produce causal DAGs, not logs](https://dev.to/milkoor/coding-agents-produce-causal-dags-not-logs-ne6).*
