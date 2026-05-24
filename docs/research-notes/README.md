# Runtime Research Notes

Observations about agent runtime behavior that inform schema evolution and causality model design.

## Purpose

These notes capture what the schema and code alone cannot:

- Why a particular trace was surprising
- Why a causality pattern was unstable
- What runtime behavior couldn't be expressed in the current schema
- Why a replay failed or produced wrong semantics
- Correlations between trace patterns and agent behavior

## Format

Each note should be a single markdown file with a date prefix:

```
2026-05-14-parallel-causality-gap.md
2026-05-15-fan-in-ambiguity.md
```

## Topics worth tracking

- **Causality ambiguity** — when parent_event_id can't express the real relationship
- **Schema pressure** — traces that strain the current field set
- **Replay failures** — why a trace didn't replay faithfully
- **Pattern mismatches** — expected causal patterns vs. observed ones
- **Agent-specific behavior** — quirks of particular runtimes

Validated pattern observations belong in `docs/research/patterns/`. When an
analysis implementation changes a metric definition, annotate existing
observations rather than silently rewriting historical results.
