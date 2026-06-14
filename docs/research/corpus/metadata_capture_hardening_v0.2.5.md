# Metadata Capture Hardening v0.2.5

Improve future metadata capture quality so sessions enter the corpus with explicit `data_origin`, `task_source`, and `intervention_lane` — reducing reliance on retroactive classification.

## Current Baseline (2026-06-14)

| Metric | Value |
|--------|-------|
| Total metadata sessions | 992 |
| Sessions with explicit `intervention_lane` | 108 (10.9%) |
| `direct_prompt_native` | 101 (`classified_from_explicit_metadata`) |
| `superpowers_workflow_intervention` | 7 |
| Sessions classified via `task_source` only | 5 (SP: ts field, no il) |
| `data_origin` distribution | native=102, unknown=877, unset=10, controlled_benchmark=3 |
| `task_source` distribution | real_work=102, unset=815, demo=62, SP=8, controlled=3 |
| Phase 4-3 triggers | 0/8 |

### How we got here

1. Phase 3E-3 established explicit tag formats and enrichment auto-detection
2. A: `corpus classify-unlabeled --dry-run` identified 101 high-confidence native sessions
3. A2: `--apply-confirmed` wrote `intervention_lane=direct_prompt_native` with provenance `classified_from_explicit_metadata`
4. 879 sessions remain unlabeled — all have `data_origin=unknown`

**Key finding:** The "safe auto-classification surface" is exhausted. Remaining unknown sessions cannot be automatically classified without heuristic inference that would risk mislabeling.

## Upstream Capture Requirements

For every session entering the corpus from this point, capture or annotate:

### Required fields (priority order)

| Priority | Field | Rationale |
|----------|-------|-----------|
| P0 | `data_origin` | Determines lane eligibility. Must be explicit. |
| P1 | `task_source` | Disambiguates real_work from demo/benchmark/external. |
| P2 | `intervention_lane` | Explicit lane assignment when known. |
| P3 | `causetrace_tags` | Machine-readable intervention evidence. |
| P4 | `task_type` | Structural classification (bug_fix, feature_add, etc.). |
| P5 | `success` | Session outcome. |

### Validation rule

A session MUST NOT be classified into a lane based on `runtime`, `model`, tool usage patterns, prompt length, or prompt style alone. Classification requires:

- Explicit `data_origin` (native, controlled_benchmark, external_trajectory)  
  OR
- Explicit `intervention_lane` set by the capture source  
  OR
- Explicit `causetrace_tags` with recognized intervention markers

## Source-Specific Defaults

These defaults apply only when the capture source can confirm them. They are NOT inferred from session content.

### Manual real project run

```json
{
  "data_origin": "native",
  "task_source": "real_work"
}
```

No `intervention_lane` needed — these sessions are the baseline. They will be classified as `direct_prompt_native` when both fields are confirmed.

### Prompt morphology pilot

```json
{
  "data_origin": "controlled_benchmark",
  "task_source": "prompt_morphology_pilot",
  "intervention_lane": "controlled_prompt_morphology"
}
```

### Prompt-routing-skill routed task

```json
{
  "intervention_lane": "routed_prompt_intervention",
  "causetrace_tags": ["prompt-routing", "routed-prompt", "causetrace-prompt-posture"]
}
```

### Superpowers workflow

```json
{
  "intervention_lane": "superpowers_workflow_intervention",
  "causetrace_tags": ["superpowers-workflow", "workflow-intervention"]
}
```

The `causetrace_tags` block must be emitted in the first response or plan output when superpowers workflow structure is applied. This is the auditable evidence for parser detection (Phase 3E-3 enrichment recognition plan, Phase 2).

### External trajectory

```json
{
  "data_origin": "external_trajectory"
}
```

`task_source` should document the external source (e.g., `external_log_import`, `third_party_trace`).

## Capture Points

Where metadata should be written, in priority order:

1. **At enrichment time** (`causetrace enrich* --save`): When a session is enriched from an agent project, the enrichment handler writes `data_origin=native` and `task_source=real_work` if the source is a real project session (not a demo).

2. **At hook time** (Claude Code hooks, OpenCode hooks): The hook bridge can emit `causetrace_tags` when workflow markers are detected.

3. **At manual annotation time** (`causetrace annotate`): Used for post-hoc high-confidence annotation of individual sessions.

4. **At metadata-set time** (`causetrace metadata-set`): Used for bulk or targeted field updates with provenance recording.

## Non-Goals

- Do NOT infer `data_origin` from runtime, model, or tool patterns.
- Do NOT classify `data_origin=unknown` sessions automatically.
- Do NOT derive `task_type` or `success` heuristically.
- Do NOT use `Skill` tool usage alone as intervention evidence.
- Do NOT expand topology taxonomy.
- Do NOT modify theory candidate grades.
- Do NOT enter Phase 4-3 unless a trigger is actually met.

## Future Trigger Note

Trigger 8 (metadata density: >=40% labeled, >=80% lane coverage) should improve primarily through:

1. Future sessions entering the corpus with explicit metadata from capture points
2. Manual annotation of high-value sessions
3. Upstream agent runtime improvements that emit metadata natively

It should NOT improve through aggressive retroactive inference on the existing 879 `data_origin=unknown` sessions.

The current gap (108/992 labeled → need ~397 for 40%) is approximately 289 sessions. With correct capture defaults at enrichment time, new real-work sessions will enter with `data_origin=native` and `task_source=real_work`, accumulating toward the threshold naturally.

## Operating Rule

**Mislabeling is more dangerous than low coverage.** A session labeled `direct_prompt_native` that was actually an intervention session pollutes the baseline and can invalidate lane comparisons. A session left unlabeled is honest about its evidence gap.
