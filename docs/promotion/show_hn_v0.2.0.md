# causetrace v0.2.0: runtime topology corpus tooling

`causetrace` turns AI coding agent tool calls into causal trees and DAGs for
Claude Code, Codex CLI, OpenCode, Aider, Continue.dev, and GitHub Copilot.

Version 0.2.0 pushes the project into corpus-first research:

- standardized runtime metadata sidecars
- corpus snapshot/export helpers
- markdown research report templates
- branch persistence, frontier width, and retry density primitives
- compare output that includes topology distance and branch distribution

```bash
pip install "causetrace @ git+https://github.com/milkoor/causetrace.git@v0.2.0"
causetrace demo
```

The demo produces a local causal DAG, renders the tree, and prints follow-up
commands for graph inspection, causal chain tracing, and topology analysis.

Repository: https://github.com/milkoor/causetrace
