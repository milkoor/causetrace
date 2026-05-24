# Coding agents produce causal DAGs, not logs

---

I've been building tracing hooks for coding agents — Claude Code, Codex CLI, Copilot, and others. The goal was simple: record what these agents do, so I could debug them when things went wrong.

What I found surprised me. **The standard observability abstraction — a flat, chronological log of events — is the wrong primitive for coding agents.** These agents don't produce meaningful timelines. They produce causal DAGs.

This post explains why, shows the difference with real traces, and argues that runtime observability for AI coding agents needs a fundamentally different data model.

---

## 1. A debugging story

A Claude Code session ran 87 tool calls over 12 minutes. The agent was asked to fix a bug. It read files, grepped for patterns, edited code, ran tests, failed, read more files, edited again, and eventually succeeded.

At the end, I wanted to understand one thing: **why did it delete a particular line?**

The flat timeline looked like this (simplified):

```
[10:02:13] Read(file_path=src/parser.py)
[10:02:15] Read(file_path=src/utils.py)
[10:02:18] Grep(pattern="parse_token")
[10:02:20] Edit(file_path=src/parser.py)
[10:02:22] Bash(command=pytest tests/ -x)
[10:02:25] Read(file_path=src/parser.py)
[10:02:28] Edit(file_path=src/parser.py)
[10:02:30] Bash(command=pytest tests/)
[10:02:33] Read(file_path=docs/api.md)
[10:02:35] Edit(file_path=docs/api.md)
```

Chronological order, zero insight. Two `Read(parser.py)` calls — which one was before the critical edit? Why the `Read(docs/api.md)` after the tests passed? The flat timeline records *when* but tells you nothing about *why*.

This isn't a visualization problem. It's an **abstraction problem**.

---

## 2. Why flat timelines fail for coding agents

Conventional logging (syslog, OpenTelemetry spans, application logs) assumes events are **independent observations** of a system. You log them in sequence, and the sequence itself carries meaning: request A happened, then request B happened.

Coding agent tool calls are different. They form a **dependency graph**. Every tool call is a direct response to the output of a prior call:

- The agent reads a file **because** it found a relevant symbol in a grep result
- It edits code **because** it understood the context from a read
- It runs tests **because** it made an edit and needs to verify
- It reads documentation **because** the test failure revealed a misunderstanding

These are not independent events. They are **edges in a directed graph** where each node is a tool call and each edge is a causal dependency.

A flat timeline encodes zero dependency information. It's a list of nodes without edges — a graph with no structure.

---

## 3. The causal DAG model

Instead of a flat list, record each tool call with an explicit `parent_event_id` — a reference to the event that caused it.

Here's the same 9-event session rendered as a causal tree:

```
[03:13:37] Read(file_path=src/main.py)
    └─ [03:13:37] Grep(pattern=FIXME)
      └─ [03:13:37] Read(file_path=src/utils.py)
[03:13:37] Read(file_path=src/utils.py)  [caused by: need_context]
    └─ [03:13:38] Edit(file_path=src/utils.py)
      └─ [03:13:38] Bash(command=python -m pytest tests/ -x)
[03:13:38] Grep(pattern=counter)
    └─ [03:13:38] Edit(file_path=docs/api.md)
      └─ [03:13:38] Bash(command=python -m pytest tests/)
```

Three independent causal trees, each with a clear "why":

1. **Tree 1:** The agent read `main.py`, found a FIXME in the grep output, read `utils.py` for context
2. **Tree 2 (user-requested context):** The user asked for context on `utils.py`, agent edited it, ran tests to verify
3. **Tree 3:** The agent searched for "counter" in docs, found an out-of-date reference, edited `api.md`, ran all tests

This is not a nicer visualization of the same data. **It's a different data model.**

With `parent_event_id`, you can:

**Trace root cause:** Given any event, walk the parent chain to find the original trigger:

```
causetrace why ses_10d2f16e <event_id>

  [03:13:38] Grep(pattern=counter) ──→
  [03:13:38] Edit(file_path=docs/api.md) ──→
  [03:13:38] Bash(command=python -m pytest tests/) ◀── TARGET
```

**Handle fan-in:** A tool call can consume outputs from multiple prior calls. Multi-parent causality via comma-separated `parent_event_id`:

```
  [02:42:40] Bash(pytest)  ← Edit(docs/api.md)
  [02:42:41] Grep(FIXME)   ← Read(main.py)
  [02:42:41] Read(utils.py) ← Grep(FIXME)
  [02:42:41] Edit(utils.py) ← Read(utils.py)
  [02:42:41] Bash(pytest -x) ← Edit(utils.py)
```

**Replay with provenance:** Walk the DAG in causal order (not chronological), replaying each event with its context. This reveals the agent's decision path, not just its action sequence.

---

## 4. Fidelity varies by agent

Not every coding agent exposes clean causal primitives:

| Agent | Method | Causal Fidelity |
|-------|--------|----------------|
| Claude Code | PreToolUse / PostToolUse hooks | High for tool sequence; turn boundaries are unavailable |
| OpenCode | SQLite DB extraction | High (native parent-child in DB schema) |
| Codex CLI | Rollout JSONL parser | Medium (call_id pairing + heuristic) |
| Aider | Process wrapper (stdout parsing) | Medium (best-effort from output) |
| Continue.dev | Log tailing + temporal inference | Low (~80% heuristic) |
| GitHub Copilot | Extension host log parsing | Low (~80% heuristic) |

For log-based agents without native causality, temporal proximity heuristics recover most of the structure: if event B happened within 2 seconds of event A's completion, B is likely a child of A. It's not perfect, but it recovers the ~80% case.

The important architectural point: **causality is not binary.** The data model
supports native structural edges when available and degrades to bounded,
documented heuristics for unstructured logs.

---

## 5. What this means for agent observability

Current runtime observability for coding agents has the wrong abstraction.

Tools like OpenTelemetry are designed for distributed systems where spans form trees based on request propagation. Agent tool calls are different — they form trees based on **information flow**, not request context propagation. An agent reads a file because of what it found in a prior read — that's not a parent span in the OpenTelemetry sense, but it's the essential causal link for understanding agent behavior.

Building the right abstraction means:

1. **Capture edges, not just nodes.** A log is a list of nodes. A causal trace records the edges between them.
2. **Design for dependency, not chronology.** Chronological order is easy to reconstruct from timestamps. Dependency order is not.
3. **Accept graceful degradation.** Native causal hooks → perfect traces. Log tailing → heuristic traces. The data model should accommodate both without breaking.

---

## 6. An open-source implementation

I've packaged this into an open-source runtime tracer called **causetrace**. It records tool calls with explicit `parent_event_id` chains, renders trees and DAGs, and supports root-cause tracing and replay.

The storage model is intentionally minimal: append-only JSONL per session, zero external dependencies. Each session is a file in `~/.causetrace/data/<session_id>.jsonl`.

**Quick start:**

```bash
pip install causetrace
causetrace demo                 # saved trace, tree, and follow-up commands
causetrace doctor               # check agent configuration
```

The project supports 6 coding agent runtimes and is MIT-licensed.

But the point of this post isn't the tool. It's the abstraction: **coding agents produce causal DAGs, not logs.** If you're building observability for AI coding agents, start from that premise.

---

*Try the runnable demo: `pip install causetrace && causetrace demo`.*
*GitHub: [https://github.com/milkoor/causetrace](https://github.com/milkoor/causetrace)*
