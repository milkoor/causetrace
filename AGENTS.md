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
