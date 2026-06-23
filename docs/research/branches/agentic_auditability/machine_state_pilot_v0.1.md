# Machine-State Reasoning Pilot v0.1

## Status

Single-run pilot complete.

This note belongs to the future `agentic_auditability_branch`. It is not a Phase 4 evidence-grade update, does not open Phase 4-3, and does not open Phase 5.

## Question

Does `machine_state + human_audit_summary` improve runtime efficiency or audit structure compared with an ordinary natural-language prompt on the same small read-only inspection task?

## Compared Sessions

| Group | Prompt variant | Session |
| --- | --- | --- |
| A | ordinary natural-language prompt | `019ec9b8-f1ca-7ca0-ab17-25963df3a238` |
| C | `machine_state + human_audit_summary` | `019ec9b9-b85b-7b53-a1c9-2093695892d3` |

Task: inspect `docs/research/roadmap/agentic_auditability_roadmap_v0.2.5.md` and answer whether it clearly distinguishes prompt-level compressed text, structured machine-state reasoning, and true latent/vector communication.

## Observed Metrics

| Metric | A: natural-language prompt | C: `machine_state + human_audit_summary` | Result |
| --- | ---: | ---: | --- |
| events | 8 | 9 | C higher |
| `exec_command` calls | 2 | 3 | C higher |
| topology | `dominant_chain` | `dominant_chain` | no topology change |
| max depth | 7 | 8 | C higher |
| time span | 18s | 26s | C higher |
| output tokens | 605 | 1107 | C higher |
| reasoning tokens | 132 | 240 | C higher |
| final answer words | 119 | 148 | C higher |
| validation | pass | pass | both valid |

## Pilot Result

On this small read-only inspection task, `machine_state + human_audit_summary` improved audit structure but did not improve runtime efficiency compared with a natural-language prompt.

It increased event count, tool-call count, elapsed span, output tokens, and reasoning tokens. Both runs produced correct answers. The main observed benefit was clearer audit structure, not performance improvement.

## Interpretation Boundary

This pilot does not support the claim:

```text
machine_state -> fewer tokens / faster execution / shorter runtime chain
```

It does support the narrower observation:

```text
machine_state + human_audit_summary -> clearer audit output structure
```

The result should be interpreted as:

```text
Auditability instrumentation may improve reviewability while increasing runtime overhead.
```

## Limitations

- Single-run only.
- Small read-only inspection task.
- No accuracy difference: both variants answered correctly.
- Not generalizable to long-horizon, multi-file, handoff-heavy, safety-boundary, or constraint-heavy tasks.
- The task was too simple to test whether structured state reduces context drift or handoff loss.
- The result must not be used to promote a mainline theory candidate or modify Phase 4 evidence grades.

## Revised Hypotheses

H-MS-001: Auditability benefit

```text
machine_state + human_audit_summary may improve audit structure and decision trace coverage.
```

H-MS-002: Overhead cost

```text
machine_state + human_audit_summary may increase runtime overhead, especially on small or simple tasks.
```

H-MS-003: Task-dependent value

```text
machine_state may be more useful for long-horizon, multi-step, handoff, safety-boundary, or constraint-heavy tasks than for small read-only inspection tasks.
```

## Mainline Impact

- Phase 4 remains frozen.
- Phase 4-3 remains trigger-gated.
- Phase 5 remains closed.
- No schema fields are added.
- No topology taxonomy changes are made.
- No unknown sessions are classified.
- No performance improvement is claimed.
