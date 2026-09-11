# Roadmap

## Near Term

- Collect sanitized traces from Claude Code, Codex CLI, and OpenCode users.
  - First contribution: a sanitized DeepSeek Harness parallel-investigation
    trace under `examples/traces/successful/dsh-20260911-parallel-investigation/`.
- Measure how often native parent links differ from timestamp-based inference.
  - Shipped as `causetrace fidelity <session>`: re-runs the temporal
    heuristics on a native session and reports edge recall/precision and
    fan-in reproduction. On the first four DSH sessions it shows 62–88%
    child-level agreement and **0 / 79 true fan-in nodes exactly reproduced**;
    batched across 48 DSH sessions (≥150 events): ~70% mean agreement and
    **0 / 724 fan-in nodes reproduced** (fan-in density vs agreement r = −0.39).
    Caveat: the metric is only meaningful for runtimes that persist *native*
    links; on log-chained parsers (whose parents are themselves inferred) it
    measures parser-vs-heuristics agreement, not ground truth.
- Make exported fixtures easier to sanitize and submit in pull requests.

## Under Evaluation

- A lightweight HTML or SVG report generated from existing trace files.
- Interchange guidance for other agent-observability tooling.

## Non-Goals

The core library will remain local-first and dependency-light. Hosted dashboards,
LLM summarization, and automated diagnosis are not planned for the core package.
