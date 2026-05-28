# r/Python post

**Title:** I built causetrace — a causal debugger for AI coding agents that turns flat logs into trees and DAGs

---

**Body:**

Been working with AI coding agents (Claude Code, Copilot, Aider, etc.) and noticed a recurring pain: when these agents run 50+ tool calls in a session, figuring out *why* a particular thing happened means scrolling through a flat chronological log and manually connecting the dots.

causetrace solves this by recording each tool event with an explicit `parent_event_id` — so instead of a flat timeline, you get a causal tree:

```
$ causetrace tree ses_10d2f16e
[03:13:37] Read(src/main.py)
    └─ Grep(pattern=FIXME)
      └─ Read(src/utils.py)
[03:13:37] Read(src/utils.py)  [caused_by: need_context]
    └─ Edit(src/utils.py)
      └─ Bash(pytest -x)
```

Try it without configuring an agent:

```bash
pip install "causetrace @ git+https://github.com/milkoor/causetrace.git@v0.2.0"
causetrace demo
```

**Supported agents:**
- Claude Code (hooks — high-fidelity tool sequence, without turn boundaries)
- OpenCode (log tail + DB enrich)
- Aider (process wrapper)
- Continue.dev, Copilot (log tailing); Codex CLI (validated rollout enrichment)

**What else it does:**
- `causetrace replay <session>` — replay the entire session with provenance
- `causetrace why <session> <event>` — trace a single event back to root cause
- `causetrace doctor` — diagnose which agents are configured correctly
- `causetrace install-claude-hook` — configure Claude Code recording with a settings backup
- Enrich commands for Claude Code / OpenCode / Codex CLI that extract reasoning blocks + tool calls

Zero external dependencies. Data stored as append-only JSONL.

Would love to hear if others have hit this debugging problem with coding agents, and what workarounds you've been using.

https://github.com/milkoor/causetrace

---

**Tags:** Python 3.10+, GitHub release `v0.2.0`
