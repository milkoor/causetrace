# The Hook Ceiling: why tool-level observation can't capture agent reasoning

## The problem

causetrace's hook/log layer sits at the tool boundary — it sees tool calls
and their results, but not the internal reasoning that produced them. This
is a fundamental limitation, not a gap that can be engineered away at the
current layer.

## The stack

```
LLM (reasoning + decisions)       ← invisible to causetrace
  │
Agent Runtime (orchestration)     ← partially visible (some state)
  │
Tool boundary (hook/log layer)    ← causetrace lives here
  │
OS / filesystem / shell
```

At the tool layer, we see *what* the agent did, never *why* it decided to do
it. The `caused_by` field exists to capture this, but it depends on the
runtime choosing to expose the reason.

## Three approaches to deeper signals

### 1. API intercept (highest fidelity, most invasive)

Intercept the HTTP requests/responses between the agent and the LLM provider.
This reveals the full conversation: system prompt, user messages, assistant
reasoning, tool calls, tool results, and the model's internal thought process.

**Feasibility for causetrace:**
- Works for self-hosted agents using OpenAI/Anthropic APIs directly
- NOT feasible for Claude Code (uses proprietary endpoint)
- NOT feasible for Copilot (uses Microsoft endpoint)
- Requires a local proxy or MitM setup
- Adds latency and complexity

### 2. Agent internal state export (fragile, agent-specific)

Some agents expose internal state:
- Claude Code checkpoints at `~/.claude/checkpoints/`
- Debug/verbose modes that dump plan structure or context
- Structured log formats with reasoning traces

**Feasibility for causetrace:**
- Format is unstable and varies between agent versions
- No standardization across runtimes
- High maintenance burden for low reliability
- Violates runtime-neutrality principle

### 3. Reverse inference from tool_io (current path)

Infer intent from tool input/output patterns. For example:
- `Read(file=X)` + `Edit(file=X, pattern=Y)` → agent is fixing a bug in X
- `Grep(pattern=Y)` + multiple `Read` results → agent is investigating Y
- Repeated failing `Edit` + `Bash(test)` → agent is in a retry loop

**Feasibility for causetrace:**
- Already works at a basic level (sequential chaining, fan-in detection)
- Always approximate — sees "what" not "why"
- Quality depends entirely on the richness of tool_input/tool_output
- This is the causetrace-native approach

## Implication for causetrace

The `caused_by` field in ToolEvent is the right place for reasoning signals,
but it can only be populated if the runtime provides the information at
hook time. causetrace should NOT attempt to:

- Parse LLM responses retroactively (too fragile)
- Maintain agent-specific state extractors (too coupled)
- Guess intent from tool patterns (too speculative)

## What causetrace SHOULD do

1. Keep `caused_by` as a first-class field, ready for when runtimes provide
   the signal
2. Track this limitation in pressure-log when it causes ambiguity
3. Document in schema docs that `caused_by` is a runtime-provided field,
   not inferred

## Related

This connects to Pressure #002 (linear causality from missing turn
boundary) — both are runtime signal gaps, not schema gaps.
