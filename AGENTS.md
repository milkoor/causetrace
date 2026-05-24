# Repository Guidelines

## Project Structure & Module Organization

`causetrace/` is the Python package. `core.py` owns events, storage, validation, and replay; `analysis.py` implements local topology and pattern metrics; `annotation.py` stores sidecar labels; `cli.py` exposes commands. Runtime-specific ingestion belongs in `causetrace/hooks/`. Tests are in `tests/`, DAG fixtures are in `tests/fixtures/dags/`, and the runnable example is `demo/run_demo.py`. Consult `docs/runtime-principles.md` and `docs/schema/` before changing event semantics.

## Build, Test, and Development Commands

```bash
pip install -e ".[test]"          # Editable install plus pytest
python -m pytest tests/ -v        # Run the full test suite
python -m pytest tests/test_invariants.py -v  # Check runtime invariants
python -m pytest tests/test_dag_fixtures.py -v # Check DAG analysis behavior
causetrace demo                   # Exercise the installed first-run path
causetrace doctor                 # Diagnose local runtime data sources
```

CI runs `python -m pytest tests/ -v` on Python 3.10, 3.11, and 3.12. Release builds are maintainer work; follow `CONTRIBUTING.md` before changing versions or publishing.

## Coding Style & Naming Conventions

Target Python 3.10+ and use four-space indentation. Follow existing conventions: `snake_case` for functions, variables, modules, and test names; `PascalCase` for classes such as `ToolEvent`. Prefer explicit type hints on new public helpers and short docstrings where behavior is not obvious. No formatter or linter is configured in `pyproject.toml`; keep edits consistent with nearby code and avoid unrelated formatting churn.

## Testing Guidelines

Tests use `pytest` and follow the `tests/test_*.py` pattern. Add parser or hook coverage in the matching module; first-run configuration belongs in `tests/test_onboarding.py`. Topology changes require DAG-fixture regression tests, including external-parent boundaries where relevant. Analysis is session-local: parents absent from the loaded session do not create graph nodes.

## Runtime Semantics and Trace Data

Read `docs/runtime-principles.md` before schema or hook work. Favor causal fidelity over broad but unreliable integrations. Real traces may contain prompts, paths, or outputs; sanitize fixtures and issue attachments before committing them.

## Commit & Pull Request Guidelines

Recent history uses concise imperative subjects such as `Add ...`, `Fix ...`, `Update ...`, and `Bump version ...`. Keep commits scoped. Pull requests should explain behavioral or schema impact, list tests run, link relevant issues, and include a sanitized real-trace example for new or changed runtime bridges.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **causetrace** (1796 symbols, 3056 relationships, 116 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/causetrace/context` | Codebase overview, check index freshness |
| `gitnexus://repo/causetrace/clusters` | All functional areas |
| `gitnexus://repo/causetrace/processes` | All execution flows |
| `gitnexus://repo/causetrace/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
