# Changelog

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
