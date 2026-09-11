# Observations — dsh-20260911-parallel-investigation

**Runtime**: DeepSeek Harness (agent `dsh`, model qwen3.8-flash)
**Shape**: 41 events · 1 root · 12 fan-in children · max fan-out 2 · 3-minute
read-only code-investigation session produced almost entirely by *parallel*
tool steps.

## How this trace was produced

Parsed from a real DSH session log via `causetrace enrich-dsh <source_session> --save`,
sanitized in place (one-off pass; see checklist below), then written out in the
store's native JSONL form (one event object per line, `ToolEvent.to_dict()`),
so the file loads directly with `JSONStore` and validates with
`causetrace validate`:

- prompt, reasoning text, commands, and tool outputs replaced with
  placeholders;
- tool names bucketed to activity classes (`List`, `Search`, `ReadSegment`,
  `ReadFile`, `Edit`);
- **causal structure, timestamps, and measured `duration_ms` are untouched** —
  they are the payload of this example;
- leak-scanned for repo paths and project identifiers before export.

## What it demonstrates

1. **Native fan-out/fan-in in every step.** Each reasoning node dispatches two
   tool calls sharing one parent, and the *next* reasoning node lists both
   call IDs as joint parents (`"id_a,id_b"`). This is the comma-multi-parent
   field doing real work — visible in `graph.txt`, not in `tree.txt` (the tree
   renderer follows first-parent edges; the DAG view is the ground truth).
2. **Real durations.** All tool events carry call→result wall time
   (21–567 ms here) — DSH ingestion is the first source with measured
   durations instead of log gaps.
3. **Heuristic inference fails exactly here.** `causetrace fidelity
   dsh-20260911-parallel-investigation`:
   - 40% of children have an exactly-correct parent set after re-inference,
   - 46% of native parent edges are missed,
   - of the 12 true fan-in nodes the heuristics reproduced **0** and even
     *claimed* 0 (its fan-in detector only fires on write/edit children, and
     here every joint-cause node is a reasoning step).
   This session is the ROADMAP's "native vs timestamp-based inference"
   measurement in miniature.

## Reproduce

```bash
causetrace enrich-dsh <dsh-session-id> --save   # from real logs
causetrace graph dsh-20260911-parallel-investigation
causetrace fidelity dsh-20260911-parallel-investigation
```

(Fidelity numbers on imported sessions are only meaningful for runtimes that
persist *native* links; for heuristic-chained imports the "ground truth" is
itself an inference artifact.)
