# Show HN: Causal traces for debugging AI coding agent tool calls

I use coding agents for non-trivial fixes, and flat tool timelines make one
question unnecessarily hard: why did the agent make this edit or rerun this
command?

I built a small Python tool that records tool calls as causal trees and DAGs.
For native hooks it retains parent links; for log-only runtimes it marks the
inference as heuristic. A Codex CLI parser now pairs real rollout
`function_call` and `function_call_output` records via `call_id`.

The new release includes a zero-setup demo:

```bash
pip install causetrace
causetrace demo
```

It writes a local sample DAG and shows commands for the causal tree, fan-in
graph, critical path, and root-cause chain.

Repository: https://github.com/milkoor/causetrace
