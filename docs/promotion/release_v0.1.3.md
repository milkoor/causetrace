# causetrace v0.1.3: a runnable first look at AI coding agent causal traces

`causetrace` turns AI coding agent tool calls into causal trees and DAGs for
Claude Code, Codex CLI, OpenCode, and other Python workflows.

Version 0.1.3 removes the first-run barrier:

```bash
pip install "causetrace @ git+https://github.com/milkoor/causetrace.git@v0.1.3"
causetrace demo
```

The command saves a local sample DAG, renders its causal tree, and prints
ready-to-run commands for multi-parent graph inspection, root-cause tracing,
and topology statistics.

For Claude Code users, onboarding is now one command:

```bash
causetrace install-claude-hook
```

It preserves existing settings and creates a backup before first modification.

Technical case study: Codex CLI rollout parsing is validated against real
`function_call` / `function_call_output` data paired by `call_id`:
https://github.com/milkoor/causetrace/blob/main/docs/case-studies/codex-rollout-parser.md

Repository: https://github.com/milkoor/causetrace

Release note: the GitHub tag is live; the PyPI upload is pending registration
of this repository's Trusted Publisher. Switch the install line to
`pip install causetrace` once PyPI exposes version `0.1.3`.

## Distribution Checklist

- Publish the GitHub Release and confirm the PyPI `0.1.3` package page.
- Update the two existing dev.to articles with the runnable demo and remove the dead HN link.
- Use `docs/assets/demo-flow.svg` in X/Reddit announcements.
- Submit a fresh Hacker News post only after the install command is publicly available.
