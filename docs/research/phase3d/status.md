# Phase 3D Status (v0.2.5)

Phase 3D is active.

It is the hypothesis registry layer for runtime morphology research. It follows the descriptive work in Phase 3A, 3B, and 3C.
The next mainline stage is `Phase 3D-T2B: Intervention-aware Acquisition`, which continues Tier 2 acquisition while keeping workflow-intervention lanes separate from the native direct-prompt baseline.

## Current Position

- Phase 2.5: complete
- Phase 3A: complete
- Phase 3B: complete
- Phase 3C: complete
- Phase 3D: active
- Phase 3E: reserved

## Current Corpus Baseline

- sessions: `1351`
- events: `128534`
- metadata sessions: `981`
- annotated sessions: `53`
- explicit runtime sessions: `179`
- ready: `True`
- strict research-grade sessions: `157`
- native strict sessions: `100`
- data_origin labeled sessions: `981`
- missing data_origin: `0`
- data_origin coverage: `100%`
- agent field coverage: `100%` (inline on events)
- provider field coverage: `99.8%` (inline on events)
- runtime distribution: opencode `1131`, claude-code `179`, codex `29`, aider `2`
- model distribution (top): doubao-seed-2.0-code `264`, deepseek-v4-pro `55`, gpt-5.4-mini `13`, gpt-5.5 `13`

## Phase 3D Documents

- [Baseline](baseline_v0.2.5.md)
- [Hypothesis registry](hypothesis_registry_v0.2.5.md)
- [Validation protocol](validation_protocol.md)
- [Hypothesis prioritization](hypothesis_prioritization_v0.2.5.md)
- [Tier 1 validation](tier1_validation_v0.2.5.md)
- [Tier 2 readiness](tier2_readiness_v0.2.5.md)
- [Tier 2 acquisition plan](tier2_acquisition_plan_v0.2.5.md)

## Tier 1 Summary

- H-RM-001: supported
- H-RM-002: inconclusive
- H-RM-003: supported
- H-TT-001: not supported in the current corpus
- H-TT-002: supported with caveat

## Tier 2 Summary

- Tier 2 is not yet validation-ready.
- Native failure coverage is `1/100`.
- Native human_intervention=true coverage is `5/100`.
- Additional AskUserQuestion-backed human-intervention examples exist outside the native lane: `e68b4fe5-0034-4acf-877d-954e6287e00b` and `908184bd-5602-4f6b-97e1-36293069d20f`.
- A single proxy-mediated failure candidate exists outside the native lane: `7de9a576-5306-4f0b-8950-53938c6b8dd9`.
- Strong native near-failure candidates have been identified, but they remain success cases and do not increase failure coverage.
- Three controlled-benchmark pilot sessions have been labeled with `data_origin=controlled_benchmark` and remain separate from the native lane.
- Tier 2 remains acquisition-only until the failure / intervention subset grows.
- Human-intervention acquisition target has been met for the current native lane.
- Intervention lanes must stay separate from the native direct-prompt baseline.

## Operating Rule

- Do not turn hypotheses into conclusions without corpus-backed validation.
- Do not move into prediction, anomaly modeling, or automatic diagnosis.
- Keep controlled benchmark and external trajectories in separate lanes.
- Keep routed-prompt and superpowers workflow traces separate from direct-prompt native traces.
- Do not move into Phase 4 yet.

## Metadata Density Warning

Current corpus scale is sufficient for validation-oriented work, but metadata density remains too low for stable theory finalization or default automation policy.

Current gap summary (explicit sidecar metadata):

- runtime missing: `1172`
- task_type missing: `1186`
- task_source missing: `1186`
- success missing: `1189`
- duration missing: `1351`
- human_intervention missing: `1255`
- model missing: `1331`
- repo_language missing: `1331`
- repo_size missing: `1331`

Note: agent and provider fields are now populated inline on all events (100% / 99.8% coverage), distinct from sidecar metadata tracked here.

## Next Action

Continue Tier 2 acquisition:

- native failure
- native near-failure
- explicit correction-trigger sessions
- native human_intervention=true is now met for the current native lane; keep it as a maintained baseline
- non-native AskUserQuestion sessions have been marked as human_intervention=true, but they do not alter the native strict gate
- proxy failure candidates may be reviewed separately, but they do not change the native strict readiness gate
- follow the acquisition sprint note for the next batch of native samples
- treat `direct_prompt_native`, `routed_prompt_intervention`, `superpowers_workflow_intervention`, and `controlled_prompt_morphology` as separate lanes in analysis
