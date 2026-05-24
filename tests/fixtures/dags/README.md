# DAG Fixtures — Topology Invariants

Each fixture is a JSONL file of causetrace ToolEvents with known topological properties.
Tests in `test_dag_fixtures.py` load each fixture and assert the invariants documented below.

| Fixture | Events | Roots | Leaves | Max Depth | Avg Depth | Components | Cycles | Longest Path | Notes |
|---------|--------|-------|--------|-----------|-----------|------------|--------|-------------|-------|
| `chain` | 4 | 1 | 1 | 3 | 1.5 | 1 | 0 | 4 | Simple linear chain |
| `fan-in` | 3 | 2 | 1 | 1 | 0.33 | 1 | 0 | 2 | Two roots → one child |
| `deep-merge` | 4 | 1 | 1 | 2 | 1.0 | 1 | 0 | 3 | Same root, two branches merge |
| `diamond` | 6 | 1 | 1 | 3 | 1.5 | 1 | 0 | 4 | Multi-layer merge |
| `cycle` | 3 | 0 | 0 | 0 | 0.0 | 1 | ≥1 | 0 | a→b→c→a cycle |
| `multi-parent-cycle` | 3 | 1 | 0 | 0 | 0.0 | 1 | ≥1 | 1 | Invalid cyclic branch is omitted from bounded path metrics |
| `forest` | 5 | 2 | 2 | 2 | 0.8 | 2 | 0 | 3 | Two disconnected trees |
| `deep-chain` | 10 | 1 | 1 | 9 | 4.5 | 1 | 0 | 10 | Deep linear chain |
| `fork` | 3 | 1 | 2 | 1 | 0.67 | 1 | 0 | 2 | One root, two leaves |
| `timed-fan-in` | 4 | 2 | 1 | 2 | 0.75 | 1 | 0 | 3 | Ordered fan-in with chain |

## Legend

- **Roots**: events with no parent present in the loaded session
- **Leaves**: events with no children
- **Max Depth**: longest distance from root to leaf (0-based)
- **Avg Depth**: sum of depths / total nodes
- **Components**: weakly connected components
- **Cycles**: expected cycle count (0 = acyclic)
- **Longest Path**: longest root-to-leaf chain (node count)

The tests also cover partial-session semantics: a node whose recorded parent is
outside the loaded event set becomes a local root for analysis.
