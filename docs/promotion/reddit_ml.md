# r/MachineLearning post

**Title:** [P] causetrace — agent runtime observation: causal DAGs from coding agent tool calls

---

**Body:**

When AI coding agents (Claude Code, Copilot, etc.) execute complex multi-step tasks, they produce long sequences of tool calls — Bash, Read, Edit, Grep. Current observability approaches treat these as flat timelines, losing the causal structure.

causetrace is an **agent runtime observation primitive** that captures tool calls with explicit `parent_event_id` links, producing causal trees and DAGs instead of flat logs.

**Why this matters:**

Agent behavior debugging is fundamentally different from traditional debugging. When an agent hallucinates or makes a wrong edit, you need to trace backward: "what context did it Read before this Edit? Which earlier output caused this decision?" Flat logs don't answer this — causal graphs do.

**Current limitations I'm aware of:**

- Fidelity varies by agent. Claude Code hooks provide reliable tool-level sequencing but not user-turn boundaries. Log-based agents (Copilot, Continue.dev) rely on heuristic temporal inference.
- The causal model is currently a DAG. True cyclic dependencies (agent re-reading its own output) aren't modeled yet.
- No visualization beyond terminal rendering (ASCII trees/DAGs). A web UI would be the obvious next step.

**Technical details:**
- Append-only JSONL storage per session (~/.causetrace/data/)
- Multi-parent fan-in via comma-separated `parent_event_id`
- Heuristic `infer_relations()` as fallback for unstructured logs
- Schema evolution tracked reactively from real traces

**6 supported runtimes:** Claude Code, OpenCode, Aider, Continue.dev, Codex CLI, GitHub Copilot

Would appreciate feedback from anyone working on agent observability or tool-use monitoring.

GitHub: https://github.com/milkoor/causetrace
PyPI: `pip install causetrace`
