# Twitter/X strategy

**Not a thread. Individual high-signal posts with real trace screenshots.**

---

## Post 1 — The core insight (with screenshot)

> Claude Code spent 81 minutes fixing a bug.
>
> Timeline view looked meaningless.
>
> But the causal DAG immediately showed:
> - root search
> - verification loops
> - failed edit branches
> - retry paths
>
> Coding agents don't generate logs.
> They generate causal graphs.

Attach: screenshot of `causetrace tree` output

---

## Post 2 — A specific debugging moment (with screenshot)

> "why did the agent delete that line?"
>
> Flat log: `Edit(file_path=x.py)` at 14:23
>
> Causal trace:
> ```
> causetrace why ses_abc <event_id>
> Read(api_docs.md) ──→
> Edit(x.py) ◀── TARGET
> ```
>
> It read documentation first, then applied the change.
> The flat log told me *when*. The causal trace told me *why*.

Attach: screenshot of `causetrace why` output

---

## Post 3 — The Codex CLI reverse engineering story

> I spent a week reverse engineering Codex CLI's rollout JSONL format.
>
> The source code says: `exec_command_begin` / `exec_command_end`
>
> The real format: `response_item/function_call` paired by `call_id`
>
> If you're building tooling for AI coding agents: the real trace format is the source of truth, not the code comments.

---

## Post 4 — The question (engagement)

> If you use Claude Code / Copilot / Codex CLI daily:
>
> Have you ever needed to trace *why* an agent made a specific edit, and couldn't figure it out from the chat log?
>
> Curious how common this debugging pain actually is.

---

## Posting cadence

- Post 1 → wait 24h → Post 2 or 3 → wait 24h → Post 4
- Don't post all at once
- Don't link directly in early posts (let people ask)
- Engage with every comment
