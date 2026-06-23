# Project Principles

## Project Boundary

`causetrace` is a runtime morphology research engine for AI coding agents.

The core project stays focused on:

- causal runtime tracing
- topology analysis
- research-grade corpus management
- empirical morphology discovery
- reproducible research reports

The core project does not expand into:

- generic observability platforms
- UI products
- SaaS services
- agent platforms
- benchmark leaderboards
- failure prediction products
- enterprise diagnostics

## Core Acceptance Rule

A new feature belongs in core only if it clearly improves at least one of:

1. runtime causality fidelity
2. topology analysis
3. corpus research validity
4. morphology vocabulary
5. reproducible runtime-behavior research

If a capability is valuable but does not improve those five areas, it should be split into a separate project or extension.

## Split-Project Examples

| Direction | Suggested form |
| --- | --- |
| Web dashboard | `causetrace-viewer` |
| Benchmark runner | `causetrace-bench` |
| External trajectory adapters | `causetrace-adapters` |
| Dataset registry | separate corpus tool |
| Failure prediction | separate modeling project |
| SaaS/API | separate product |

## Governance Rule

Core purity beats feature accumulation.

If a direction is adjacent but not essential to causal topology research, keep it outside `causetrace` core.

## Literature Integration Rule

External research papers may inform hypotheses, terminology, and research questions, but they must not directly alter core schemas, taxonomy labels, or analysis claims unless causetrace corpus evidence supports the change.

Literature-driven ideas should first enter a literature note and the hypothesis registry, not the core implementation or the primary taxonomy.

## Data-Grounded Method Rule

Do not assume a method improves performance, safety, or auditability. Record it, compare it, then decide.

All future method claims must be grounded in recorded runtime traces. A method is not considered effective unless its impact on performance, morphology, and auditability is separately recorded.

Final task success is not enough. A method may improve auditability while increasing overhead, reduce runtime events while weakening evidence, or improve task success while reducing human reviewability.

## Comparability Rule

Raw session volume is not research sample size.

Cross-session claims require a named comparable corpus or experimental subset with disclosed inclusion rules, denominators, metadata tiers, and sampling bias. Metadata work serves comparability; it is not a goal by itself.

## Critical External Research Absorption Rule

External research should be critically absorbed.

It may influence hypotheses, terminology, and research questions, but it must not directly change core schemas, topology taxonomy, readiness gates, or research conclusions without causetrace corpus evidence.

The default path is:

- literature note
- hypothesis registry
- corpus-backed analysis
- only then possible promotion into broader causetrace terminology or claims

## Commercially Valuable Adjacent Work

If a capability:

1. clearly satisfies the split-project rule, and
2. has strong commercialization or distribution potential,

then it may be proposed as a separate project or product suggestion.

That suggestion should be recorded explicitly, but it still does not belong in `causetrace` core unless it also satisfies the core acceptance rule.

The default action is:

- document the suggestion
- keep the core boundary intact
- evaluate commercialization separately from core research scope
