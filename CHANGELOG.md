# Changelog

## 0.2.0 — 2026-11-01

- `rubric` checks: `samples: N` runs N independent judgements and the median
  score wins — one outlier judge call can no longer flip a regression gate.
- New `skillev gate` command: re-gate the newest stored run against a baseline
  (`--against <run-id>`) without re-running the agent, for CI jobs that run in
  a separate step or machine.
- New `skillev show <case>`: inspect a case's check-by-check results and the
  agent transcript from any stored run.
- `skillev run --html report.html`: self-contained HTML report with grades,
  check details and transcripts.
- Composite GitHub Action: `uses: D0NO1/skill-eval@main` in any workflow.
- Fixed: same-second runs could be ordered incorrectly, breaking baseline
  selection; run timestamps are now guaranteed unique.

## 0.1.0 — 2026-11-01

Initial release.

- Case format: `evals/cases/<name>/` with `task.md`, `fixtures/`, `grader.yaml`
  (+ optional `mock.yaml` for the deterministic mock agent).
- Graders: `file_exists`, `contains`, `regex`, `command` (deterministic) and
  `rubric` (LLM-as-judge, OpenAI-compatible API).
- Adapters: `mock` (no API key) and `claude` (headless Claude Code); pluggable.
- Regression gate: run scores are compared to the previous run; a case
  dropping more than one letter grade fails with exit code 1.
- `skillev init/run/history` CLI.
