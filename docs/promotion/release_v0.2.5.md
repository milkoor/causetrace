# causetrace v0.2.5: corpus hardening for runtime topology research

`causetrace` turns AI coding agent tool calls into causal trees and DAGs for
Claude Code, Codex CLI, OpenCode, Aider, Continue.dev, and GitHub Copilot.

Version 0.2.5 turns the project from "corpus can be counted" into "corpus can
be audited":

- field-level metadata provenance, with missing-field coverage separated from
  unknown provenance
- canonical benchmark and taxonomy manifests, so ordering does not change the
  hash
- shared corpus facts for health/readiness reporting
- research-grade session gating for Phase 3 entry
- benchmark verify / compare, taxonomy, readiness, and materialization flows
- structural exemplars for fan-in, branch-collapse, and multi-root sessions

Install the release:

```bash
pip install "causetrace @ git+https://github.com/milkoor/causetrace.git@v0.2.5"
causetrace demo
```

The demo creates a local causal DAG, renders the tree, and prints follow-up
commands for graph inspection, causal chain tracing, corpus health, and
readiness checks.

For corpus work:

```bash
causetrace metadata <session_id>
causetrace corpus health
causetrace corpus readiness
causetrace corpus benchmark
causetrace corpus taxonomy
causetrace report <session_id>
```

Technical case study: Codex CLI rollout parsing is still validated against real
`function_call` / `function_call_output` data paired by `call_id`:
https://github.com/milkoor/causetrace/blob/main/docs/case-studies/codex-rollout-parser.md

Repository: https://github.com/milkoor/causetrace

## Distribution Checklist

- Confirm the GitHub release and PyPI package page for `0.2.5`.
- Update the published posts and install commands that still point at older tags.
- Keep the old release assets archived for historical reference.
