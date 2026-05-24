# causetrace

> [中文](README.zh-CN.md) • [CI](https://github.com/milkoor/causetrace/actions) • [PyPI](https://pypi.org/project/causetrace/) • [Changelog](CHANGELOG.md) • [Roadmap](ROADMAP.md) • [Discussions](https://github.com/milkoor/causetrace/discussions) • [Contributing](CONTRIBUTING.md) • [Security](SECURITY.md)

[![CI](https://github.com/milkoor/causetrace/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/milkoor/causetrace/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/causetrace.svg)](https://pypi.org/project/causetrace/)
[![Python](https://img.shields.io/pypi/pyversions/causetrace.svg)](https://pypi.org/project/causetrace/)
[![License](https://img.shields.io/github/license/milkoor/causetrace.svg)](LICENSE)


**causetrace** is a Python tracing and observability tool for AI coding agents
such as Claude Code, Codex CLI, OpenCode, Aider, Continue.dev, and GitHub
Copilot. It captures tool calls and links them into causal trees and DAGs,
enabling agent debugging, replay, root-cause analysis, and behavior
explanation instead of relying on flat timelines.

> **Data sources**: Claude Code (hooks), OpenCode / Continue.dev / GitHub Copilot (log tailing), Codex CLI (rollout parser), Aider (process wrapper)
> **Storage**: `~/.causetrace/data/<session_id>.jsonl` — append-only JSONL, zero external dependencies

---

## Use Cases

- Trace why an AI coding agent made a specific edit or shell call.
- Debug Claude Code hooks and Codex CLI rollout sessions from causal context.
- Compare agent sessions by topology, transitions, and critical paths.
- Collect sanitized runtime traces for agent observability research.

![From flat tool logs to causal explanation](docs/assets/demo-flow.svg)

---

## Showcase

The same session viewed four ways — flat vs. causal.

### Timeline (flat)

```
$ causetrace timeline ses_10d2f16e
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

Chronological order, but no insight into *why* each event happened.

### Causal Tree

```
$ causetrace tree ses_10d2f16e
[03:13:37] Read(file_path=src/main.py)
    └─ [03:13:37] Grep(pattern=FIXME)
      └─ [03:13:37] Read(file_path=src/utils.py)
[03:13:37] Read(file_path=src/utils.py)  [caused by: need_context]
    └─ [03:13:38] Edit(file_path=src/utils.py)
      └─ [03:13:38] Bash(command=python -m pytest tests/ -x)
[03:13:38] Grep(pattern=counter)
    └─ [03:13:38] Edit(file_path=docs/api.md)
      └─ [03:13:38] Bash(command=python -m pytest tests/)
```

Parent→child chains reveal the causal structure: each tool call is a direct response to its parent.

### Why (causal chain trace)

```
$ causetrace why ses_10d2f16e <event_id>
[03:13:38] Grep(pattern=counter) ──→
[03:13:38] Edit(file_path=docs/api.md) ──→
[03:13:38] Bash(command=python -m pytest tests/) ◀── TARGET
```

Trace *why a specific event happened* — follow the causal chain backward from any event to its root.

### Multi-parent DAG

```
$ causetrace graph ses_3e23bcc8
[02:42:40] Bash(command=python -m pytest tests/)  ← Edit(file_path=docs/api.md)
[02:42:41] Read(file_path=src/main.py)
[02:42:41] Grep(pattern=FIXME)  ← Read(file_path=src/main.py)
[02:42:41] Read(file_path=src/utils.py)  ← Grep(pattern=FIXME)
[02:42:41] Read(file_path=src/utils.py)
[02:42:41] Edit(file_path=src/utils.py)  ← Read(file_path=src/utils.py)
[02:42:41] Bash(command=python -m pytest tests/ -x)  ← Edit(file_path=src/utils.py)
[02:42:42] Grep(pattern=counter)
[02:42:42] Edit(file_path=docs/api.md)  ← Grep(pattern=counter)
```

Fan-in DAGs visualize convergent causation — one tool consuming multiple prior results. Support for multi-parent causal links via comma-separated `parent_event_id`.

---

## Supported Agents

| Agent | Method | How it works |
|-------|--------|-------------|
| **Claude Code** | Hook bridge | PreToolUse / PostToolUse hooks via `~/.claude/settings.json` |
| **OpenCode** | Log tailing | Parses `~/.local/share/opencode/log/*.log` for tool.registry entries |
| **Aider** | Process wrapper | Runs `aider` as subprocess, parses stdout for tool calls |
| **Continue.dev** | Log tailing | Parses `~/.continue/logs/core.log` for JSON tool call entries |
| **Codex CLI** | Rollout parser | Parses `~/.codex/sessions/.../rollout-*.jsonl` — `function_call`/`function_call_output` paired by `call_id` |
| **GitHub Copilot** | Log tailing | Parses `~/.config/Code/logs/` extension host logs for Copilot tool calls |

```bash
# Claude Code — automatic via hooks
causetrace tree <session_id>

# Claude Code — enrich project sessions with reasoning blocks
causetrace enrich-sessions
causetrace enrich <session_id> --save

# OpenCode — enrich DB sessions with reasoning blocks
causetrace enrich-opencode-sessions
causetrace enrich-opencode <session_id> --save

# Codex CLI — enrich rollout sessions with causal chains
causetrace enrich-codex-sessions
causetrace enrich-codex <session_id> --save

# Log-based agents — scan and save (heuristic causality)
causetrace opencode --save
causetrace continue --save
causetrace copilot --save

# Aider — run with tracing
causetrace aider -- --model gpt-4 --yes "fix the bug"
```
Usage notes:

- **Claude Code** — most precise, captures full causality via Pre/Post hooks
- **Aider** — `causetrace aider --save -- [aider args]` wraps the CLI; best-effort parsing from output
- **Codex CLI (enrich)** — parses real rollout format: `function_call`/`function_call_output` paired by `call_id`, `agent_message` for reasoning
- **OpenCode (enrich)** — extracts reasoning + tool calls from SQLite DB with causal parent-child links
- **Continue.dev**, **Copilot** — post-hoc log scanning; causality inferred from temporal proximity via `infer_relations()`
- **Codex CLI (`codex`)** — legacy scanner retained for compatibility; use `enrich-codex` for validated rollout ingestion
- All log-based agents infer causality heuristically — timestamps between events determine parent→child chains

---

## Quick Start

```bash
pip install causetrace

# Create a saved sample trace and immediately see the causal tree
causetrace demo
```

`demo` prints the generated session ID plus ready-to-run `graph`, `why`, and
`stats` commands. No agent configuration or fixture download is required.

### Hook up Claude Code

Install recording hooks while preserving existing Claude Code settings:

```bash
causetrace install-claude-hook
causetrace doctor
```

The installer writes `~/.claude/settings.json` and creates a
`settings.json.causetrace.bak` backup before its first change. Remove only
causetrace hooks with `causetrace uninstall-claude-hook`.

### Scan OpenCode logs

```bash
causetrace opencode --save
```

Parses OpenCode log files, infers causal relations from temporal proximity, and saves as a causetrace session.

### Analyze and validate sessions

```bash
causetrace validate <session_id>                 # Integrity and malformed JSONL checks
causetrace stats <session_id>                    # Topology summary
causetrace roots <session_id>                    # Local roots and downstream depth
causetrace critical-path <session_id>            # Longest local causal chain
causetrace patterns <session_id> --json          # Structured path/transition/fan-in output
causetrace patterns <session_id> --csv           # Transitions CSV
causetrace annotate <session_id> --task-type bug_fix --success
causetrace compare <session_a> <session_b>
```

Structural analysis is session-local: a parent ID not present in the loaded
session marks a local boundary, so its child is analyzed as a local root.
`validate` still reports missing non-`root_` parent references as warnings.

### Validated Cases

- [Codex CLI rollout parsing case study](docs/case-studies/codex-rollout-parser.md)
- [Claude Code hook causality failure observation](examples/traces/failures/observations-claude-code-hooks.md)
- [Runtime research notes](docs/research-notes/README.md)

---

## Data Model

Every event is a `ToolEvent`. The four causal fields (`parent_event_id`, `session_id`, `event_type`, `caused_by`) distinguish causetrace from flat logging systems.

| Field | Description |
|-------|-------------|
| `event_id` | UUID |
| `parent_event_id` | Causal parent (comma-separated for fan-in; may reference an external boundary) |
| `session_id` | Owning session |
| `tool_name` | e.g. `Bash`, `Read`, `Write` |
| `tool_input` | Serialized input arguments |
| `tool_output` | Serialized output |
| `timestamp` | ISO 8601 |
| `duration_ms` | Execution time |
| `event_type` | `tool_call` / `reasoning` / `context_update` / `user_input` |
| `caused_by` | `user` / `reasoning` / event_id / semantic tag |

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `causetrace timeline <id>` | Flat chronological view |
| `causetrace tree <id>` | Causal parent→child tree |
| `causetrace graph <id>` | Multi-parent DAG (fan-in) |
| `causetrace sessions` | List recorded sessions |
| `causetrace export <id>` | Export as JSON |
| `causetrace replay <id>` | Replay with provenance |
| `causetrace why <id> <eid>` | Trace causal chain from event |
| `causetrace enrich-sessions` | List Claude Code project sessions |
| `causetrace enrich <id> [--save]` | Enrich from Claude Code project session |
| `causetrace enrich-opencode-sessions` | List OpenCode DB sessions |
| `causetrace enrich-opencode <id> [--save]` | Enrich from OpenCode DB session |
| `causetrace enrich-codex-sessions` | List Codex CLI rollout sessions |
| `causetrace enrich-codex <id> [--save]` | Enrich from Codex CLI rollout session |
| `causetrace opencode [--save]` | Scan OpenCode logs |
| `causetrace aider [--save] -- [args]` | Run aider with tracing |
| `causetrace continue [--save]` | Scan Continue.dev logs |
| `causetrace codex [--save]` | Legacy Codex scan path; prefer `enrich-codex` |
| `causetrace copilot [--save]` | Scan GitHub Copilot agent logs |
| `causetrace validate [<id>]` | Validate JSONL integrity, references, and cycles |
| `causetrace stats [<id>]` | Show structural topology statistics |
| `causetrace roots [<id>]` | Show local roots and downstream metrics |
| `causetrace critical-path [<id>]` | Show longest local root-to-leaf chain |
| `causetrace patterns [<id>] [--json\|--csv]` | Show causal paths and transitions; CSV exports transitions |
| `causetrace annotate <id> [...]` | Store sidecar task/source/result metadata |
| `causetrace compare <a> <b>` | Compare topology and transitions across sessions |
| `causetrace doctor` | Diagnose agent configuration and data sources |
| `causetrace demo` | Create and inspect a self-contained sample trace |
| `causetrace install-claude-hook` | Configure Claude Code capture hooks safely |
| `causetrace uninstall-claude-hook` | Remove only causetrace-managed hooks |

---

## Architecture

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Claude Code  │  │   OpenCode   │  │    Aider     │  │ Continue.dev │  │  Codex CLI   │  │   Copilot    │
│  (hooks)     │  │ (log tail)   │  │ (subprocess) │  │ (log tail)   │  │ (log tail)   │  │ (log tail)   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │                 │                 │
       ▼                 ▼                 ▼                 ▼                 ▼                 ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    TraceRecorder                                                    │
│                             (causal linking, storage)                                               │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           JSONStore                                                │
│                                (append-only JSONL, no DB)                                          │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              Tree / DAG Builders                                                    │
│                              Renderers / ReplayEngine                                               │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

| Module | Responsibility |
|--------|---------------|
| `causetrace/core.py` | Data model, `TraceRecorder`, `JSONStore`, tree/DAG builders, renderers, `ReplayEngine` |
| `causetrace/analysis.py` | Session-local topology, critical paths, windows, and causal patterns |
| `causetrace/annotation.py` | Sidecar metadata for task labels and comparison workflows |
| `causetrace/causality.py` | Temporal causal inference for unstructured logs |
| `causetrace/cli.py` | argparse CLI dispatching capture, analysis, annotation, and diagnostic commands |
| `causetrace/hooks/` | Agent-specific bridges and tailers |
| `causetrace/hooks/claude_code.py` | Claude Code hook bridge |
| `causetrace/hooks/claude_project_parser.py` | Claude Code project session parser |
| `causetrace/hooks/opencode_parser.py` | OpenCode SQLite DB session parser |
| `causetrace/hooks/codex_parser.py` | Codex CLI rollout JSONL parser |
| `causetrace/hooks/opencode_tailer.py` | OpenCode log tailer |
| `causetrace/hooks/aider_bridge.py` | Aider subprocess wrapper |
| `causetrace/hooks/continue_tailer.py` | Continue.dev log tailer |
| `causetrace/hooks/codex_tailer.py` | Codex CLI log tailer (legacy, use enrich) |
| `causetrace/hooks/copilot_tailer.py` | GitHub Copilot log tailer |

---

## Development

```bash
git clone https://github.com/milkoor/causetrace.git
cd causetrace
pip install -e ".[test]"
python -m pytest tests/ -v
```

---

## License

MIT
