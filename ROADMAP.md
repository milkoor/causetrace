# Roadmap

## Near Term

- Collect sanitized traces from Claude Code, Codex CLI, and OpenCode users.
- Measure how often native parent links differ from timestamp-based inference.
- Make exported fixtures easier to sanitize and submit in pull requests.

## Under Evaluation

- A lightweight HTML or SVG report generated from existing trace files.
- Interchange guidance for other agent-observability tooling.

## Non-Goals

The core library will remain local-first and dependency-light. Hosted dashboards,
LLM summarization, and automated diagnosis are not planned for the core package.
