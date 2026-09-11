# DeepSeek Harness Session Logs: Native Causality, No Heuristics

## Problem

Most coding-agent runtimes expose their activity only through logs that
require temporal-proximity inference (`infer_relations()`) or serial
`last_event_id` chaining. The resulting traces are flat single-root chains:
chronologically correct, causally degenerate. DSH (DeepSeek Harness) persists
its agent loop — `turn`, `step`, `callId`, settled `tool/call` + `tool/result`
records — so ingestion can lift the *native* causal structure instead of
reconstructing it.

## Format

DSH writes one append-only zstd JSONL per session:
`~/.dsh/sessions/<workspace-slug>/<session-id>/session.jsonl.zstd`.
68 sessions (plus a 508-session `~/.dsh-backup`) on the validation machine.

Record types consumed by `hooks/dsh_parser.py`:

| Record | Becomes |
|--------|---------|
| `user/message` (source.kind=`user`) | `user_input` root of the turn |
| `assistant/message` reasoning/text blocks | `reasoning` events (Thinking/Response) |
| `tool/call` | `tool_call`, parent = step's reasoning (fan-out) |
| `tool/result` | merged into its call via `callId` (+ `duration_ms`) |
| `command/run` / `command/done` | `context_update` (paired by `commandId`) |
| `request/header` / `model/selection` | model/provider attribution |

Streaming records (`assistant/chunk`, `*-chunks`), control records
(`turn/*`, `step/*`, `compaction/*`, `llm/retry`), and non-user injections
(`plugin`, `skill-catalog`, `agent-instructions` sources) are skipped.

The parser does **not** use `causality.infer_relations()` — every edge comes
from persisted DSH identifiers.

## What the DAG looks like

Causal shape comparison across eight real sessions (metrics via
`causetrace` storage + `analysis.py`):

| Session (runtime) | events | roots | longest chain | fan-in events | max parents | max parallel calls |
|-------------------|--------|-------|---------------|---------------|-------------|--------------------|
| DSH design-oa | 2508 | 137 | 311 | 22 | 2 | 2 |
| DSH memory-plugin debug | 945 | 56 | 43 | 46 | 6 | 7 |
| DSH backup-762a | 3315 | 149 | 458 | 10 | 2 | 3 |
| DSH backup-df4c | 2638 | 60 | 210 | 1 | 2 | 3 |
| Claude Code (parser) | 7524 | 1 | 7524 | 0 | 1 | 1 |
| Codex CLI | 2007 | 1 | 2007 | 0 | 1 | 1 |
| OpenCode | 3097 | 1 | 3097 | 0 | 1 | 1 |
| Hermes | 809 | 1 | 809 | 0 | 1 | 1 |

For every non-DSH runtime the parser collapses the session into a **single
chain covering all events** (`roots=1`, `longest == events`). Only DSH data
demonstrates multi-root turns and genuine fan-in/fan-out — a direct fidelity
win from runtime-native structure (principle: causality over chronology).

Concrete fan-in example (memory-plugin debug session): one `Thinking` event
has **six** parents — six `lingshu_*` diagnostic tool calls issued in the same
step whose joint results fed that reasoning turn. The comma-separated
multi-parent `parent_event_id` (v0.1 feature) meets its first real workload
from an ingestion parser rather than a synthetic fixture.

## Native links vs timestamp inference (ROADMAP near-term measurement)

DSH is the only ingested runtime that persists ground-truth causal edges, so
the same four event streams were fed to `causality.infer_relations()` (the
heuristic used by all log-based tailers) with parents stripped, then compared
edge-set to edge-set. This is now a repeatable command:
`causetrace fidelity <session>` (`causetrace/fidelity.py`). A sanitized
session demonstrating the effect end-to-end lives at
`examples/traces/successful/dsh-20260911-parallel-investigation/` (12 native
fan-in nodes, 0 reproduced by the heuristics).

| Session | child nodes fully agreeing | missed native parent-edges | spurious parent-edges | multi-parent children: native / inferred / exactly reproduced |
|---------|---------------------------|----------------------------|-----------------------|---------------------------------------------------------------|
| design-oa | 76% | 17% | 19% | 22 / 55 / **0** |
| memory-plugin debug | 62% | 33% | 28% | 46 / 24 / **0** |
| backup-762a | 70% | 26% | 25% | 10 / 0 / **0** |
| backup-df4c | 88% | 10% | 10% | 1 / 0 / **0** |

Three findings:

1. Temporal inference disagrees with reality on **12–38% of child nodes**,
   splitting between missing and fabricated parents.
2. It reproduced **0 of 79** true multi-parent (fan-in) nodes exactly. Where it
   invented fan-in at all (design-oa: 55 claimed vs 22 real) it grouped the
   wrong joint causes; where true fan-in was denser (memory-plugin debug) it
   halved the count. Heuristics do not just miss parallelism — they emit
   structurally wrong parallelism.
3. Agreement correlates with serialness: the most sequential session
   (backup-df4c, one fan-in) scored best; the most parallel (memory-plugin
   debug) scored worst. Heuristic fidelity is inversely proportional to the
   exact structure that makes causality worth recording.

## Behavioural signatures (patterns)

- Claude Code paper-extractor: `Bash → Thinking` ×1136, `Thinking → Response` ×1027 — read-heavy interactive loop.
- DSH design-oa (interactive): 136 user turns, 7.1 tool calls/turn — heavy human steering.
- DSH backup-df4c (autonomous): 60 user turns, 22.7 tool calls/turn — batch delegation style.
- DSH backup-762a: `run_code → Thinking → run_code` ×710 — single-tool code-execution preset.
- Codex: `exec_command → exec_command` ×287 — shell-chain style.

## Wall-clock durations (first runtime with real numbers)

DSH is the first supported runtime where `duration_ms` is measured
(call record → result record). Medians: `bash` 0.1–1.4s, `edit`/`read` ~0s.
The same channel also exposes outliers: parked calls whose result arrived
after session idle — one background `run_code` measured ~1023 h wall-clock.
`duration_ms` therefore means *dispatch→resolution interval*, not pure
execution time (see schema pressure #005).

## Limitations

- Sub-agent delegation lives in separate session directories
  (`delegationDepth > 0`); no cross-session edge is invented — the parent's
  `subagent` call and the child session's root remain unlinked in the schema.
- Import-style DSH sessions (`import-*` dirs) carry no tool calls; they parse
  to prompt/reasoning-only traces.
- Tool results are truncated at 2000 chars by serialization, same as other
  runtimes.
- Re-parsing a source session mints fresh `event_id`s (uuid), so the
  append-only store cannot dedupe a second import of the same session:
  `--upsert` only protects against identical repeated saves within one
  event-id generation. One enriched causetrace session per source session.

## Reproduce

```bash
causetrace doctor                       # ✓ DeepSeek Harness
causetrace enrich-dsh-sessions          # ~/.dsh
causetrace enrich-dsh-sessions --dsh-home ~/.dsh-backup   # or a backup home
causetrace enrich-dsh <session_id> --save
causetrace tree <session_id> --quality
causetrace patterns <session_id>
```

Session logs stay on the user's machine; strip command arguments before
sharing any tree/pattern output from real sessions.
