# Phase 3C: Targeted Corpus Expansion

Phase 3B established a descriptive baseline and Phase 3C completed the controlled data-expansion work needed to validate whether the runtime signals seen in Phase 3A/3B survive after source and task stratification.

Phase 3C was not a prediction phase. It was a controlled data-expansion phase, and the native-lane target has now been met.

Phase 3C focused on targeted corpus expansion and manual origin annotation. External literature did not change Phase 3C execution. It informed future hypotheses, but collection preserved tool observations, test failures, self-correction text, and human intervention context when available, because those details may support future Phase 3D hypotheses.

## Source tiers

| Tier | Purpose | Typical source | Corpus rule |
| --- | --- | --- | --- |
| Native corpus | Primary research evidence | Sessions captured directly by causetrace from real agent runs | Preferred for conclusions |
| Controlled benchmark corpus | Same-task, multi-runtime comparison | SWE-bench Verified, curated issue sets, reproducible local runs | Use for controlled contrasts only |
| External trajectory corpus | Morphology expansion and failure-shape coverage | SWE-bench experiments, SWE-Gym trajectories, OpenHands trajectories | Keep separate from native strict corpus |

## Source-origin field

Use `data_origin` to label the tier:

- `native`
- `controlled_benchmark`
- `external_trajectory`
- `unknown`

Do not use `task_source` as a substitute for `data_origin`. `task_source` describes the task context; `data_origin` describes where the session came from.

## Collection priorities

1. Native non-demo sessions with explicit metadata.
2. Native failure and human-intervention sessions.
3. Controlled benchmark runs with the same task across multiple runtimes.
4. External trajectories only after provenance is explicit and the corpus lane is isolated.

## Controlled benchmark candidates

The following sources are candidate only and must remain outside strict native claims until manually reviewed and lane-assigned:

- SWE-Gym
- SWE-EVO

Rules:

- candidate only
- no ingestion before manual origin annotation
- controlled_benchmark lane only
- no native conclusion

## Inclusion rules

- Keep native, controlled benchmark, and external trajectories in separate corpus lanes.
- Do not mix external trajectories into strict native claims.
- Do not treat benchmark trajectories as ground truth for runtime cognition.

## Exclusion rules

- Do not add synthetic traces that were not produced by an actual agent run.
- Do not infer `data_origin` silently from task labels.
- Do not collapse `demo` and `controlled_benchmark` into the same tier.

## Recommended next reports

- `causetrace corpus origins`
- `causetrace corpus health`
- `causetrace corpus readiness`

## Literature and Hypothesis Links

- [Literature note: Strategic Information Allocation under Uncertainty](../literature/strategic_information_allocation_2603_15500.md)
- [Phase 3D: Runtime Morphology Hypothesis Registry](../phase3d/README.md)

## Controlled Benchmark Planning

- [Controlled benchmark protocol](controlled_benchmark_protocol_v0.2.5.md)
- [Controlled benchmark candidates](controlled_benchmark_candidates_v0.2.5.md)

## Phase 3C Status

- [Phase 3C completion tracker](status.md)

## Human Review Queue

- [Origin annotation summary](origin_annotation_summary_v0.2.5.md)
- [Origin labeling queue](origin_labeling_queue_v0.2.5.md)
- [Lane baseline](lane_baseline_v0.2.5.md)
- [Native lane research candidates](native_lane_research_candidates_v0.2.5.md)
- [Native lane expansion targets](native_lane_expansion_targets_v0.2.5.md)
- [Native lane runbook](native_lane_runbook_v0.2.5.md)
- [Lane inclusion rules](lane_inclusion_rules.md)
- [Review batches](review_batches_v0.2.5.md)
