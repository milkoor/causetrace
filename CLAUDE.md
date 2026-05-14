# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What causetrace does

causetrace is an Agent Runtime Trace SDK — it captures tool calls from AI agents (Claude Code via hooks, OpenCode via log tailing) with **causal traceability**. Instead of flat timelines, events are linked into trees and DAGs via `parent_event_id` chains, enabling replay, causal chain analysis, and anomaly detection.

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
causetrace opencode --save          # Scan OpenCode logs
```

## Architecture

- **`causetrace/core.py`** — Core data model (`ToolEvent`), causal linking (`TraceRecorder`), JSON-per-session storage (`JSONStore`), tree/DAG builders (`build_tree`, `trace_causal_chain`), renderers (`TimelineRenderer` with flat/tree/graph views), and `ReplayEngine`.
- **`causetrace/causality.py`** — Temporal causality inference for OpenCode logs (no structured input/output available): turn detection, sequential chaining, fan-in detection (multiple reads → one write), agent subtask hierarchy. Used by the OpenCode hook.
- **`causetrace/hooks/claude_code.py`** — Claude Code hook bridge reads PreToolUse/PostToolUse events from stdin, tracks start times and causal parent IDs via files in `~/.causetrace/active/`. Designed to be used as a Claude Code hook script.
- **`causetrace/hooks/opencode_tailer.py`** — Parses OpenCode log files for `tool.registry` log entries, infers causality with `infer_relations()`, and optionally enriches with model/provider info from OpenCode's SQLite DB.
- **`causetrace/cli.py`** — argparse-based CLI dispatching to the 8 subcommands.
- **`tests/test_invariants.py`** — Tests runtime invariants (serialization roundtrip, causality acyclicity, append-only integrity, renderer stability), not business logic.

## Key design choices

- **Schema evolution** is tracked in `docs/schema-evolution/INDEX.md` — fields are added reactively to Runtime observations, not designed upfront.
- **Multi-parent causality** uses comma-separated `parent_event_id` (e.g. `"root_a,root_b"` ) for fan-in DAGs. `_parse_parents()` splits on comma.
- **Storage** is append-only JSONL files at `~/.causetrace/data/<session_id>.jsonl`. No DB dependency.
- **Data model**: `ToolEvent` has event_id, parent_event_id, session_id, event_type, caused_by, model, provider, agent, tool_name, tool_input, tool_output, timestamp, duration_ms.
