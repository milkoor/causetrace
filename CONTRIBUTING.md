# Contributing

## Principles

Before contributing, read [docs/runtime-principles.md](docs/runtime-principles.md).
The project prioritizes causal fidelity over feature breadth. A PR that compromises
runtime semantics will be rejected regardless of functionality.
Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report
vulnerabilities privately as described in [SECURITY.md](SECURITY.md).

## What we need

### Real traces

The single most valuable contribution is real-world trace data. If you use
causetrace with any agent, share your experience in a GitHub Issue:
- What did you learn?
- What was hard to express?
- What did the schema struggle to represent?

This feeds [docs/schema/pressure-log.md](docs/schema/pressure-log.md) and
drives schema evolution.

### Agent bridges

New agent hooks/tailers are welcome, but:

1. The agent must be open-source or have a documented log format
2. The bridge must produce causally-linked events (not flat logs)
3. Test with a real trace before submitting

### Bug fixes

Open an issue first. Include the causetrace output and agent type.

## What we don't accept

- AI features (summarization, anomaly detection, auto-RCA) in the core
- Database dependencies
- Dashboard or visualization integrations
- Anything that couples causetrace to a specific agent framework

These belong in separate projects.

## Getting started

```bash
git clone https://github.com/milkoor/causetrace.git
cd causetrace
pip install -e ".[test]"
python -m pytest tests/ -v
causetrace demo
```

Changes to causal topology or analysis must add focused coverage in
`tests/test_dag_fixtures.py`; storage, serialization, validation, and CLI
contracts belong in `tests/test_invariants.py`. First-run and configuration
flows belong in `tests/test_onboarding.py`.

## Publishing to PyPI

Maintainer only. To publish a new version:

1. Update `version` in `pyproject.toml`, `__version__` in `causetrace/__init__.py`, and `CHANGELOG.md`
2. Tag the release: `git tag v<version> && git push origin --tags`
3. The [publish workflow](.github/workflows/publish.yml) will build and upload automatically

The workflow uses PyPI Trusted Publishing through GitHub Actions OIDC
(`id-token: write`). Configure the `milkoor/causetrace` project as a trusted
publisher on PyPI; no repository API token is used by the workflow. The PyPI
GitHub publisher fields must match:

```text
Owner:       milkoor
Repository:  causetrace
Workflow:    publish.yml
Environment: (blank)
```

If publishing fails with `invalid-publisher`, register or correct these fields
under the PyPI project's Publishing settings, then rerun the failed GitHub
Actions job.

To publish manually:
```bash
pip install build twine
python -m build
python -m twine upload dist/*
```
