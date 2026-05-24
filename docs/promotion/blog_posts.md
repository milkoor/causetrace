# Blog posts — content strategy

**Priority order:** 1 → 3 → 2

---

## 1. Why coding agents need causal tracing instead of logs

**Status:** MOST IMPORTANT. Write this first.

**Angle:** Foundational narrative. Establishes the problem.

**Target audience:** Engineers who use Claude Code / Codex CLI / Copilot daily and have hit debugging pain.

**Outline:**

```
Title: Coding agents produce causal DAGs, not logs

1. A real debugging story
   - A Claude Code session ran 87 tool calls
   - Something went wrong
   - Flat timeline gave no answers

2. Why flat timelines fail for coding agents
   - Tool calls are structurally dependent (each Read depends on a prior Edit's output)
   - Independence assumption (logs) vs. dependence reality (agent behavior)
   - "when" != "why"

3. The causal DAG model
   - Every tool call records parent_event_id
   - Tree view (single parent) vs. DAG view (fan-in)
   - Root cause tracing: follow parent chain backward
   - Replay with provenance

4. Real trace comparison
   - Same session rendered as timeline vs. tree vs. DAG
   - What each view reveals/hides

5. Where it works and where it doesn't
   - Hooks (Claude Code) → high-fidelity tool sequencing, without turn boundaries
   - Log tailing (Copilot, Continue.dev) → heuristic ~80%
   - The heuristic gap is a research problem, not just an implementation detail

6. Implications
   - Runtime observability for agents needs different primitives than distributed tracing
   - Causal graphs > log streams for agent behavior
```

**Publication:** Personal blog + dev.to + link on HN

---

## 2. Reverse engineering Codex CLI rollout traces

**Angle:** Technical deep-dive. Shows rigor.

**Target:** Runtime/tooling engineers, LLM infra people.

**Outline:**

```
Title: What I learned reverse engineering Codex CLI's trace format

1. Starting point: protocol.rs said X
   - Expected: exec_command_begin, exec_command_end, mcp_tool_call_begin, etc.

2. Reality: rollout JSONL said Y
   - Actual: response_item/function_call + response_item/function_call_output paired by call_id
   - event_msg/agent_message for reasoning blocks
   - response_item/response.output_item.done events

3. The proxy detour
   - Had to build a DeepSeek proxy to generate real traces
   - Responses API → Chat Completions translation
   - Tool format differences (name vs function.name wrapping)

4. What this means
   - For Codex: the runtime trace format != the source code surface
   - For tool builders: don't trust docs, trust wire data
```

---

## 3. Claude Code hooks and the missing parent_event_id

**Angle:** Small bug, big implication. Concrete and relatable.

**Target:** Claude Code heavy users, hook developers.

**Outline:**

```
Title: How a missing parent_event_id broke causal tracing on Claude Code

1. The hook setup
   - PreToolUse/PostToolUse in settings.json
   - Expected: clean event chain

2. The bug
   - parent_event_id was sometimes None
   - flat traces despite causal hook architecture
   - Root cause: the field name in pre_data

3. The fix (one line)
   - parent_id = pre_data.get("parent_event_id") or None

4. Why this matters beyond the bug
   - Claude Code hooks expose enough state to preserve tool-level parent links
   - But they do not expose user-turn boundaries
   - Treat hook traces as structural evidence, not complete semantic intent
```
