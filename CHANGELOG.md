# Changelog

## 0.3.1 - 2026-09-11

- Add the DeepSeek Harness session-log bridge (`enrich-dsh`): native `turn`/`step`/`callId` causality — parallel fan-out, multi-parent fan-in, measured `duration_ms`, zstd JSONL — including nested `run_code` inner tool dispatches and mid-turn steering (`mid_turn`) markers.
- Add the Hermes Agent `state.db` session parser bridge (`enrich-hermes`).
- Add `causetrace fidelity`: measures timestamp-based inference against native ground-truth parent links (across the DSH corpus the heuristics reproduce 0 of 724 true fan-in nodes).
- Add `causetrace dsh-tree`: renders the session-level delegation forest from DSH's ground-truth `parentSession` headers (402/402 edges resolvable).
- Fix quadratic slowdown in `validate_session` cycle detection.
- Add the first sanitized DSH parallel-investigation example trace, the DSH native-causality case study, and schema pressures #005–#006.

## 0.3.0 - 2026-06-23

- Add the AI Behavior Science OS v0.3 stack: descriptor-only BDE, read-only CRDD subset compilation, and external-only CERC experiment planning.
- Add feedback integration for external execution results with gap updates and experiment reprioritization.
- Add stable dedup/upsert import entry points and metadata extensions for behavior-distribution tracking.
- Update research documentation and regression coverage for the corpus design workflow.

## 0.2.5 - 2026-05-29

- Harden corpus reporting with field-level metadata provenance and missing-field audits.
- Canonicalize benchmark and taxonomy manifests so reproducibility does not depend on input ordering.
- Unify health/readiness statistics through shared corpus facts and research-grade session gates.
- Add benchmark verify/compare, taxonomy, readiness, and materialization flows for Phase 2.5 research normalization.
- Expand corpus coverage with labeled review/demo sessions and structural fan-in / branch-collapse / multi-root exemplars.

## 0.2.0 - 2026-05-28

- Add standardized session runtime metadata sidecars and CLI commands.
- Add corpus snapshot, export, and labeled grouping helpers.
- Add markdown research report templates for structural session analysis.
- Add branch persistence, frontier width, and retry density topology primitives.
- Expand `compare` with topology distance, transition divergence, branch distribution, and root spawning comparison.

## 0.1.3 - 2026-05-24

- Add `causetrace demo` for an immediately inspectable saved causal DAG.
- Add `install-claude-hook` and `uninstall-claude-hook` with safe settings backup.
- Add onboarding tests and improve install/documentation discovery paths.
- Include the DAG fixture files required by CI and update Actions to Node 24-compatible releases.
- Correct local topology analysis and structured `patterns` output contracts.

## 0.1.2 - 2026-05-14

- Add validated Codex CLI rollout ingestion and multi-runtime enrichment paths.
- Document schema pressure found in runtime trace validation.

## 0.1.0 - 2026-05-14

- Initial causal tracing, tree rendering, replay, and runtime integrations.
