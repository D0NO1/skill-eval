# Contributing

Thanks for helping make skill testing a real practice.

## Setup

```bash
git clone https://github.com/D0NO1/skill-eval.git
cd skill-eval
pip install -e . pytest
pytest -q
```

The entire test suite runs offline with the mock agent — **please keep it that
way**. Tests must not require API keys, network access, or real agent CLIs.
LLM-judge code paths are tested with mocks (see `tests/test_gate_show_html.py`).

## Ground rules

- One PR, one purpose. Keep diffs focused.
- New features need tests and a README touch.
- Grader/adapter behavior changes should update `examples/commit-linter` if
  the example demonstrates them.
- Python ≥ 3.10, stdlib-first: avoid adding dependencies unless there's no
  reasonable alternative.

## Adding an agent adapter

1. Subclass `AgentAdapter` in `src/skillev/adapters/` — implement
   `run(task, workspace, case, env) -> AgentRun`.
2. Register it in `src/skillev/adapters/__init__.py`.
3. Add a test that runs a case with it (mocked subprocesses are fine).
4. Document it in the README's Agents table.

## Releasing (maintainers)

1. Bump `__version__` and `pyproject.toml`.
2. Add a CHANGELOG entry.
3. Tag `vX.Y.Z` and push; create the GitHub Release from the changelog.
