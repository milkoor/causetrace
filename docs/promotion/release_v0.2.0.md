# causetrace v0.2.0: runtime topology corpus tooling

`causetrace` turns AI coding agent tool calls into causal trees and DAGs for
Claude Code, Codex CLI, OpenCode, Aider, Continue.dev, and GitHub Copilot.
Version 0.2.0 adds the first corpus-focused research layer:

```bash
pip install "causetrace @ git+https://github.com/milkoor/causetrace.git@v0.2.0"
causetrace demo
```

The release adds standardized runtime metadata sidecars, corpus snapshot/export
helpers, a Markdown research report template, and new topology primitives for
branch persistence, frontier width, and retry density. The `compare` command
now includes topology distance, transition divergence, branch distribution,
and root-spawning comparison.

For corpus work, use:

```bash
causetrace metadata <session_id>
causetrace corpus snapshot
causetrace corpus export
causetrace report <session_id>
```

Technical case study: Codex CLI rollout parsing is still validated against real
`function_call` / `function_call_output` data paired by `call_id`:
https://github.com/milkoor/causetrace/blob/main/docs/case-studies/codex-rollout-parser.md

Repository: https://github.com/milkoor/causetrace

Release note: GitHub Actions published `v0.2.0` to PyPI successfully.

## Distribution Checklist

- Confirm the GitHub release and PyPI package page for `0.2.0`.
- Update the published posts and install commands that still point at `0.1.3`.
- Keep the old `0.1.3` assets archived for historical reference.
