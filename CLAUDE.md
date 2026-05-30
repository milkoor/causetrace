# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What causetrace does

causetrace is an Agent Runtime Observation primitive — it captures tool calls from coding agents (Claude Code, OpenCode, Aider, Continue.dev, Codex CLI, GitHub Copilot) and links them into causal trees and DAGs via `parent_event_id` chains. Instead of flat timelines, every event records *why* it happened, enabling replay, root-cause analysis, and behavior explanation.

## Before making changes

Read `docs/dependency-map.md` first — it shows which modules depend on what.
Use it to assess change impact before modifying any file.

## Build & test

```bash
# Install (editable)
pip install -e .

# Run all tests
python -m pytest tests/ -v

# Run a single test
python -m pytest tests/test_invariants.py::test_causality_chain_links -v

# Run the installed first-run path
causetrace demo
```

## CLI

```bash
causetrace timeline [session_id]    # Flat chronological view
causetrace tree [session_id]            # Causal parent→child tree
causetrace tree [session_id] --quality  # Tree with causal quality report
causetrace tree [session_id] --compress # Compress consecutive same-tool runs ([×N])
causetrace graph [session_id]       # Multi-parent DAG (fan-in)
causetrace sessions                 # List recorded sessions
causetrace export <session_id>      # Export as JSON
causetrace replay [session_id]      # Replay trace with provenance
causetrace why <session_id> <eid>   # Trace causal chain from event
causetrace enrich-sessions                # List Claude Code project sessions
causetrace enrich <session_id> [--save]   # Enrich from Claude Code project session
causetrace enrich-opencode-sessions       # List OpenCode DB sessions
causetrace enrich-opencode <id> [--save]  # Enrich from OpenCode DB session
causetrace enrich-codex-sessions          # List Codex CLI rollout sessions
causetrace enrich-codex <id> [--save]     # Enrich from Codex CLI rollout session
causetrace opencode [--save]              # Scan OpenCode logs
causetrace aider [--save] -- [args]       # Run aider with tracing
causetrace continue [--save]              # Scan Continue.dev logs
causetrace codex [--save]                 # Legacy scan path; prefer enrich-codex
causetrace copilot [--save]               # Scan GitHub Copilot agent logs
causetrace doctor                         # Diagnose agent configuration and data sources
causetrace stats [session]                # Structural session statistics
causetrace roots [session]                # Root events with downstream metrics
causetrace critical-path [session]        # Longest root-to-leaf causal chain
causetrace patterns [session]             # Repeated tool patterns & transitions
causetrace patterns [session] --csv       # Causal transitions as CSV
causetrace validate [session]             # Check JSONL/references/cycles
causetrace validate --all                 # Validate all stored sessions
causetrace annotate <session> [...]       # Store sidecar metadata
causetrace compare <a> <b>                # Compare session topology
causetrace demo                            # Create an inspectable sample trace
causetrace install-claude-hook             # Configure recording hooks safely
causetrace uninstall-claude-hook           # Remove only managed hooks
```

## Architecture

- **`causetrace/core.py`** — Core data model (`ToolEvent`), causal linking (`TraceRecorder`), append-only JSONL storage (`JSONStore`), tree/DAG builders, renderers, `ReplayEngine`.
- **`causetrace/invariants.py`** — Composable DAG correctness checkers (acyclicity, unique IDs, root definition, local references). Used by DAG fixture tests.
- **`causetrace/analysis.py`** — Session analysis primitives (structural + pattern). Layer 1: graph/path/topology metrics (compute_stats, find_roots, longest_path). Layer 1.2: entropy & density (transition_entropy, branch_density, root_spawning_rate, path_reuse_ratio). Layer 2: structural patterns without semantic naming (detect_repeated_paths, detect_common_transitions, detect_fan_in_patterns, detect_branch_collapse).
- **`causetrace/causality.py`** — Temporal causality inference for unstructured logs: turn detection, sequential chaining, fan-in detection. Used by log-based tailers.
- **`causetrace/cli.py`** — argparse-based CLI dispatching capture, analysis, annotation, and diagnostic commands.
- **`causetrace/onboarding.py`** — Self-contained demo session generation and safe Claude Code hook settings updates.
- **`causetrace/hooks/`** — Agent-specific bridges and tailers:
  - `claude_code.py` — Claude Code PreToolUse/PostToolUse hook bridge
  - `claude_project_parser.py` — Claude Code project session parser (enrich)
  - `opencode_parser.py` — OpenCode SQLite DB session parser (enrich)
  - `codex_parser.py` — Codex CLI rollout JSONL parser (enrich)
  - `opencode_tailer.py` — OpenCode tool.registry log parser (legacy)
  - `aider_bridge.py` — Aider subprocess wrapper (stdout parsing)
  - `continue_tailer.py` — Continue.dev JSON log tailer
  - `codex_tailer.py` — Codex CLI JSONL session log parser (legacy, use enrich)
  - `copilot_tailer.py` — GitHub Copilot VS Code extension host log parser
- **`tests/test_invariants.py`** — Tests runtime invariants (serialization roundtrip, causality acyclicity, append-only integrity, renderer stability), not business logic.
- **`tests/test_enrich.py`** — Tests for Claude Code project session parser.
- **`tests/test_opencode_enrich.py`** — Tests for OpenCode DB session parser.
- **`tests/test_dag_fixtures.py`** — Topology fixtures and session-local analysis regression tests.
- **`tests/test_onboarding.py`** — First-run demo and Claude Code configuration regression tests.

## Runtime principles

See `docs/runtime-principles.md` for the full set. Core tenets:

1. **Causality over chronology** — the causal graph is the primary runtime abstraction
2. **Fidelity over coverage** — higher-fidelity causality > supporting more runtimes
3. **Runtime-native semantics** — schema evolves from real traces, not speculative design
4. **Semantic restraint** — new event types require evidence across >=3 independent runtimes
5. **Separate core from intelligence** — AI features must live outside the core (future `causetrace-intelligence/`)

## /promote — promotion skill

When asked to promote (major update, new release, technical discovery), execute this workflow:

### 0. Pre-flight check
- Run all tests: `python -m pytest tests/ -v`
- Run demo: `causetrace demo`
- Run `python3 tools/promote.py checklist <version> "description"` to generate full checklist

### 1. Write the story (always start here)
- Identify the **technical discovery** or **real debugging story** — never lead with the tool
- Draft blog post in `docs/promotion/blog_<topic>.md`
- HN post must be pure technical insight: **no project name, no GitHub link, no install commands**
- Blog post can mention the project but put it in the last section

### 2. Blog → dev.to
```bash
python3 tools/promote.py devto-post docs/promotion/blog_<topic>.md
```

### 3. HN post (if new content)
- Wait 24h+ since last HN post to avoid flagging
- Title must be a technical claim, not a product announcement
- Text: pure insight with real trace example, zero marketing language
- Keep project name and GitHub link out of the body (can profile/post if asked)

### 4. Twitter/X (if screenshots available)
- 1 tweet per insight, 24h spacing between tweets
- Strip ANSI codes from terminal output
- Use `python3 tools/promote.py tweet "text"` to check length
- Attach real terminal screenshots

### 5. Follow-up
- Monitor HN/dev.to comments, reply within 24h
- Add blog links to `docs/promotion/index.md`
- Collect trace feedback → `docs/schema/pressure-log.md`

**Real KPI:** complex real traces collected, schema pressure identified, not stars/signups.

## Key design choices

- **Schema evolution** is tracked reactively in `docs/schema/` (INDEX.md for evolution log, SCHEMA.md for field definitions, pressure-log.md for trace data that strains the current model).
- **Multi-parent causality** uses comma-separated `parent_event_id` (e.g. `"root_a,root_b"` ) for fan-in DAGs. `_parse_parents()` splits on comma.
- **Session-local analysis** retains only parent edges whose IDs are in the loaded session; a child of an external parent is a local root for `stats`, `roots`, and `critical-path`.
- **Storage** is append-only JSONL files at `~/.causetrace/data/<session_id>.jsonl`. No DB dependency.
- **Dependency map** at `docs/dependency-map.md` — check before modifying any module to assess change impact.
- **Heuristic causality** (`infer_relations()` in `causality.py`) is an explicit fallback for log-based agents, clearly documented as lower fidelity.
- **Data model**: `ToolEvent` has event_id, parent_event_id, session_id, event_type, caused_by, model, provider, agent, tool_name, tool_input, tool_output, timestamp, duration_ms.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **causetrace** (2160 symbols, 3824 relationships, 164 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/causetrace/context` | Codebase overview, check index freshness |
| `gitnexus://repo/causetrace/clusters` | All functional areas |
| `gitnexus://repo/causetrace/processes` | All execution flows |
| `gitnexus://repo/causetrace/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
