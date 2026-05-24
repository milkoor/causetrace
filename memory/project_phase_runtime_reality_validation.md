---
name: Project Phase - Runtime Reality Validation
description: Strategic shift after v0.1 — from feature stacking to runtime analysis ontology via analysis.py
type: project
---

causetrace has entered Runtime Reality Validation phase (post-v0.1). The core question is no longer "does the code run" but "do the runtime abstractions match real agent behavior."

## Strategic priorities (ordered):

1. **Collect real traces** — 30min+ sessions, failure traces (retry loops, oscillation, abandoned branches), parallel execution traces. This is the single most important task.
2. **Build trace corpus** at `/examples/traces/` — organized by type (successful, failures, loops, retries, refactors, debugging), each with raw jsonl + tree/why output + observation notes.
3. **Runtime Pattern Discovery** — using `analysis.py` primitives (Layer 1 structural + Layer 2 pattern) to find repeated tool paths, transitions, and convergence patterns. Document findings in `/docs/research/patterns/`.
4. **Runtime Integrity** — tests (serialization roundtrip, DAG integrity, parent linking, replay consistency, malformed trace recovery), corruption handling, `causetrace validate` command.
5. **Observe users, not features** — no web UI, dashboards, AI features, embeddings, cloud sync. Watch what commands users actually run (tree vs timeline, why utility, graph complexity, stats output).
6. **Semantic stability** — schema_version field frozen, field names frozen, event_type frozen, parent semantics frozen. Schema migration cost will spike once real corpus exists.
7. **Runtime Research Notes** at `/docs/research-notes/` — capture strange traces, unstable causality patterns, inexpressible runtime behaviors, replay failures. These feed schema evolution and may become a paper/standard draft.

## Key architectural addition: analysis.py

Created `causetrace/analysis.py` as the Session Analysis Layer, sitting between core and CLI:

```text
Trace Capture (core.py)
    ↓
Causal DAG (core.py: build_tree, trace_causal_chain)
    ↓
Session Analysis Primitives (analysis.py)  ← NEW
    ↓
CLI / Compression / Intelligence
```

**Layer 1 — Structural (pure topology):**
- `compute_stats()` — event counts, depths, fan-out, link ratio, time span
- `find_roots()` — root events with downstream count and subtree depth
- `longest_path()` — longest root-to-leaf chain (critical path, topological)
- `fan_out_distribution()` — histogram of children per node
- `connected_components()` — weakly connected component sizes

**Layer 2 — Pattern (structural only, no semantic naming):**
- `detect_repeated_paths()` — tool_name subsequences that repeat
- `detect_common_transitions()` — (tool_i → tool_j) transition counts
- `detect_fan_in_patterns()` — multi-parent convergence points
- `detect_branch_collapse()` — convergence of multiple root paths

**CLI commands (thin renderers only):**
- `causetrace stats <session>` — structural session profile
- `causetrace roots <session>` — root events with downstream metrics
- `causetrace critical-path <session>` — deepest causal chain
- `causetrace patterns <session>` — repeated patterns + transitions

**Design rule:** no semantic interpretation in analysis.py. Retry loops, verification chains, planning phases must NOT be named here — let them emerge from pattern observation across multiple traces and runtimes.

**Boundary rule:** analysis is session-local. A `parent_event_id` absent from
the loaded event set is retained as provenance but does not become a graph
node; the child is treated as a local root.

## Core principle

causetrace's value is NOT ingestion volume. It's runtime semantics — explaining **why** an agent acted, not just logging what it did. This is the differentiator from all observability tools.

**Why:** The user provided a deep strategic analysis — the project must validate its causality model against real agent behavior before adding features.

**How to apply:** Every decision should be filtered through: "Does this help us understand agent behavior better, or just log more?" If the latter, defer.
