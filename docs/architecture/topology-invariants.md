# Topology Invariants

## Guarantees

These invariants hold for every valid causetrace session:

| Invariant | Description | Enforced by |
|-----------|-------------|-------------|
| Unique event IDs | No two events share the same `event_id` within a session | `check_unique_ids` |
| Acyclic parent chains | Parent-event references form a DAG — no cycles | `check_acyclicity` |
| Resolvable parent refs | Every `parent_event_id` resolves to an event in the session, or begins with `root_` (external convention) | `check_local_references` |
| Root = indegree 0 | An event is a root iff no other event in the session references it as parent | `check_root_definition` |

## Non-guarantees

These are NOT guaranteed by the invariant layer:

- **Causal correctness** — a cycle-free DAG does not prove the recorded parent-child relationships match the agent's actual causal structure
- **Timestamp consistency** — timestamps may drift or be missing; no invariant checks temporal ordering
- **Completeness** — an event may have missing children (e.g. a tool call whose result was not captured)
- **Cross-runtime semantic equivalence** — `"Read"` means different things across Claude Code, Codex CLI, and OpenCode
- **Deterministic replay** — replay is observational, not reproductive

## Usage

```python
from causetrace.invariants import check_invariants

result = check_invariants(events)
if not result["valid"]:
    for name, check in result["checks"].items():
        if check["violations"]:
            print(f"{name}: {check['violations']}")
```

## Architecture

The invariant module (`causetrace/invariants.py`) is designed for:

- **Composability** — each checker is a pure function: `(events) -> List[str]`
- **No dependencies** — only relies on Python stdlib
- **Testability** — 10 DAG fixtures in `tests/fixtures/dags/` cover valid and corrupt topologies; the parametrized `test_invariant_battery` runs every invariant against every fixture

## Related

- `causetrace/core.py:validate_session()` — higher-level validation (also checks JSONL parsing, orphans, and broken refs)
- `tests/test_dag_fixtures.py` — 45+ tests covering topology metrics and invariants
- `docs/schema/` — schema evolution discipline for new fields