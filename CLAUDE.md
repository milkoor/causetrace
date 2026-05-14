# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What causetrace does

causetrace is an Agent Runtime Observation primitive — it captures tool calls from coding agents (Claude Code, OpenCode, Aider, Continue.dev, Codex CLI, GitHub Copilot) and links them into causal trees and DAGs via `parent_event_id` chains. Instead of flat timelines, every event records *why* it happened, enabling replay, root-cause analysis, and behavior explanation.

## Build & test

```bash
# Install (editable)
pip install -e .

# Run all tests
python -m pytest tests/test_invariants.py -v

# Run a single test
python -m pytest tests/test_invariants.py::test_causality_chain_links -v

# Run demo
python demo/run_demo.py
```

## CLI

```bash
causetrace timeline [session_id]    # Flat chronological view
causetrace tree [session_id]        # Causal parent→child tree
causetrace graph [session_id]       # Multi-parent DAG (fan-in)
causetrace sessions                 # List recorded sessions
causetrace export <session_id>      # Export as JSON
causetrace replay [session_id]      # Replay trace with provenance
causetrace why <session_id> <eid>   # Trace causal chain from event
causetrace opencode [--save]        # Scan OpenCode logs
causetrace aider [--save] -- [args] # Run aider with tracing
causetrace continue [--save]        # Scan Continue.dev logs
causetrace codex [--save]           # Scan OpenAI Codex CLI logs
causetrace copilot [--save]         # Scan GitHub Copilot agent logs
```

## Architecture

- **`causetrace/core.py`** — Core data model (`ToolEvent`), causal linking (`TraceRecorder`), append-only JSONL storage (`JSONStore`), tree/DAG builders, renderers, `ReplayEngine`.
- **`causetrace/causality.py`** — Temporal causality inference for unstructured logs: turn detection, sequential chaining, fan-in detection. Used by log-based tailers.
- **`causetrace/cli.py`** — argparse-based CLI dispatching to 12 subcommands.
- **`causetrace/hooks/`** — Agent-specific bridges and tailers:
  - `claude_code.py` — Claude Code PreToolUse/PostToolUse hook bridge
  - `opencode_tailer.py` — OpenCode tool.registry log parser
  - `aider_bridge.py` — Aider subprocess wrapper (stdout parsing)
  - `continue_tailer.py` — Continue.dev JSON log tailer
  - `codex_tailer.py` — Codex CLI JSONL session log parser
  - `copilot_tailer.py` — GitHub Copilot VS Code extension host log parser
- **`tests/test_invariants.py`** — Tests runtime invariants (serialization roundtrip, causality acyclicity, append-only integrity, renderer stability), not business logic.

## Runtime principles

See `docs/runtime-principles.md` for the full set. Core tenets:

1. **Causality over chronology** — the causal graph is the primary runtime abstraction
2. **Fidelity over coverage** — higher-fidelity causality > supporting more runtimes
3. **Runtime-native semantics** — schema evolves from real traces, not speculative design
4. **Semantic restraint** — new event types require evidence across >=3 independent runtimes
5. **Separate core from intelligence** — AI features must live outside the core (future `causetrace-intelligence/`)

## Key design choices

- **Schema evolution** is tracked reactively in `docs/schema/` (INDEX.md for evolution log, SCHEMA.md for field definitions, pressure-log.md for trace data that strains the current model).
- **Multi-parent causality** uses comma-separated `parent_event_id` (e.g. `"root_a,root_b"` ) for fan-in DAGs. `_parse_parents()` splits on comma.
- **Storage** is append-only JSONL files at `~/.causetrace/data/<session_id>.jsonl`. No DB dependency.
- **Heuristic causality** (`infer_relations()` in `causality.py`) is an explicit fallback for log-based agents, clearly documented as lower fidelity.
- **Data model**: `ToolEvent` has event_id, parent_event_id, session_id, event_type, caused_by, model, provider, agent, tool_name, tool_input, tool_output, timestamp, duration_ms.
