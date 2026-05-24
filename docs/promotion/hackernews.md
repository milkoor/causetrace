# Show HN: causetrace – A technical post, not a product launch

**Goal:** Frame as a technical discovery about runtime observability abstractions, not a tool announcement.

**Target audience:** Engineers who have used coding agents and felt the pain of debugging from flat logs.

---

## Title

> Coding agents produce causal DAGs, not timelines

---

## Body

I've been building tracing hooks for Claude Code and parsing Codex CLI rollout files to understand what coding agents actually do during a session.

What I found surprised me: these agents don't produce meaningful flat timelines. They produce causal DAGs.

**The flat timeline problem:**

A typical 50-call Claude Code session rendered chronologically:

```
[03:13:37] Read(file_path=src/main.py)
[03:13:37] Grep(pattern=FIXME)
[03:13:37] Read(file_path=src/utils.py)
[03:13:37] Read(file_path=src/utils.py)
[03:13:38] Edit(file_path=src/utils.py)
[03:13:38] Bash(command=python -m pytest tests/ -x)
[03:13:38] Grep(pattern=counter)
[03:13:38] Edit(file_path=docs/api.md)
[03:13:38] Bash(command=python -m pytest tests/)
```

Two `Read(src/utils.py)` calls in a row — was the second one a repeat? A different context? Why the `Grep(pattern=counter)` after the test run? Flat timelines give you questions, not answers.

**What's really happening:**

Each tool call is a directed response to a prior result. The agent reads a file → finds a FIXME → looks up supporting code → edits → verifies. That's a causal chain, not a log line.

When you reconstruct the parent-child relationships, the same session becomes:

```
[03:13:37] Read(file_path=src/main.py)
    └─ [03:13:37] Grep(pattern=FIXME)
      └─ [03:13:37] Read(file_path=src/utils.py)
[03:13:37] Read(file_path=src/utils.py)  ← root (user requested context)
    └─ [03:13:38] Edit(file_path=src/utils.py)
      └─ [03:13:38] Bash(command=python -m pytest tests/ -x)
[03:13:38] Grep(pattern=counter)
    └─ [03:13:38] Edit(file_path=docs/api.md)
      └─ [03:13:38] Bash(command=python -m pytest tests/)
```

Three independent causal trees, each with a clear "why."

**How it works:**

- Claude Code exposes PreToolUse/PostToolUse hooks — a recorder can persist tool-level parent links
- Those links recover tool sequence, but hook data does not expose user-turn boundaries
- For agents without native hooks (Copilot, Continue.dev), temporal proximity heuristics recover ~80% of the causal structure
- Storage is append-only JSONL per session — one file, no database, zero dependencies

**The Codex CLI case was a rabbit hole:**

Codex CLI's documented format (`protocol.rs`) suggests `exec_command_begin`/`exec_command_end` events. The real rollout JSONL uses `response_item/function_call` and `response_item/function_call_output` paired by `call_id`, with `event_msg/agent_message` for reasoning. The documented format and the actual format don't match — I only found this after proxying through a DeepSeek adapter and dumping raw traces.

This matters because: if you're building runtime tooling for coding agents, the source of truth is the real trace format, not the source code comments.

**What I built (causetrace):**

An open-source runtime tracer that:
- Records tool calls with explicit `parent_event_id` chains
- Renders causal trees, multi-parent DAGs, and root-cause traces
- Supports Claude Code (hooks), OpenCode (log + DB), Aider (wrapper), Continue.dev / Copilot (log tail), and Codex CLI (rollout parser)
- `causetrace why <event>` — trace any event back to root cause
- `causetrace replay` — replay a session with causal provenance

**The bigger question:**

I think current runtime observability for coding agents has the wrong abstraction. Flat logs assume independence between events. But agent tool calls are structurally dependent — every Read is because of a prior Edit's output, every Bash is because of a prior Read's findings.

A causal DAG is a better primitive than a log stream for this domain.

Would love feedback from anyone who's tried to debug agent behavior from raw logs — especially if you've hit traces where flat representation actively hid the bug.

https://github.com/milkoor/causetrace

---

## Notes for posting

- Post as text, not a link (HN allows text posts for Show HN)
- Be ready to answer: "How is this different from just adding more logging?"
- Key defense: the difference is structural — parent_event_id makes the relationship between events explicit, which enables root-cause tracing and replay in a way that flat logs can't
- If someone asks about web UI: the answer is "CLI-only for now, because the most valuable feedback at this stage is from people who can read terminal output"
