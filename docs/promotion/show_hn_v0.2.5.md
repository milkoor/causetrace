# causetrace v0.2.5: runtime topology research infra

`causetrace` turns AI coding agent tool calls into causal trees and DAGs for
Claude Code, Codex CLI, OpenCode, Aider, Continue.dev, and GitHub Copilot.

Version 0.2.5 pushes the project further into corpus-first research:

- metadata provenance is now auditable field by field
- missing metadata is tracked separately from unknown provenance
- benchmark and taxonomy manifests are canonicalized for stable hashes
- health and readiness share a single corpus-facts layer
- research-grade sessions are gated explicitly before Phase 3

```bash
pip install "causetrace @ git+https://github.com/milkoor/causetrace.git@v0.2.5"
causetrace demo
```

The demo produces a local causal DAG, renders the tree, and prints commands to
inspect fan-in, root-cause paths, corpus health, and readiness.

Repository: https://github.com/milkoor/causetrace

## If asked for more detail

- The corpus is now auditable, not just countable.
- The Phase 3 gate is explicit and reproducible.
- The current research focus is runtime topology, not generic observability.
