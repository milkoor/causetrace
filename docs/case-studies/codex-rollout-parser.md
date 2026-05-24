# Codex CLI Rollout Parsing: A Validated Case

## Problem

An early Codex ingestion path expected generic action/observation JSONL entries.
Real Codex CLI rollout data instead exposed `response_item/function_call` and
`response_item/function_call_output` records paired by `call_id`. The old
assumption produced no usable tool trace.

## Evidence

On 2026-05-14, `causetrace/hooks/codex_parser.py` was validated against a
465-line Codex CLI rollout captured through a DeepSeek-compatible adapter. It
extracted 116 events: 114 tool calls plus 2 reasoning events. The parser:

- pairs calls and outputs using `call_id`;
- imports `event_msg/agent_message` as reasoning context;
- ignores token and control records that are not causal tool events.

## Reproduce Locally

```bash
pip install "causetrace @ git+https://github.com/milkoor/causetrace.git@v0.1.3"
causetrace enrich-codex-sessions
causetrace enrich-codex <session_id> --save
causetrace stats <session_id>
causetrace critical-path <session_id>
```

Codex rollout files remain on the user's machine; public reports should remove
prompts, paths, credentials, and tool output before sharing.

## Outcome

This case is why the validated Codex route is `enrich-codex`; the older
`causetrace codex` scan path remains only for compatibility. It also motivates
the project's rule that runtime bytes, not assumed event shapes, determine
parser behavior.
