# skill-eval

[![CI](https://github.com/D0NO1/skill-eval/actions/workflows/ci.yml/badge.svg)](https://github.com/D0NO1/skill-eval/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

**Regression test harness for agent skills.**

You wrote a `SKILL.md`. Then you tweaked it. Did you just break it?

skill-eval runs a suite of tasks against your skill in throwaway workspaces,
grades the outputs with deterministic checks and LLM-as-judge rubrics, and
fails the build when a case regresses — so skill upgrades ship like code:
with tests.

```text
skill: commit-linter   adapter: mock   run: 20261101T052751-nogit
case                               score grade   vs baseline 20261101T052750-nogit
body-explains-why                  100.0     A   =
conventional-subject               100.0     A   =
avg score: 100.0
regression gate: PASS
```

中文一句话：给 agent skill 跑回归测试 —— 一组任务 + 期望输出，验证 skill 升级没有退化。

## Why

Agent skills (SKILL.md bundles) are becoming a real distribution format, but
nobody tests them. Editing a skill is editing a prompt: a wording change that
fixes one task can silently regress three others. skill-eval gives skills a
`tests/` directory and a CI gate.

- **Cases are just files** — `task.md` + `fixtures/` + `grader.yaml`, versioned next to the skill.
- **Deterministic first** — most checks are plain file/regex/command assertions; rubric judging is opt-in per check.
- **Zero-key CI** — the built-in `mock` agent replays scripted behavior, so the harness tests itself (and your graders) without any LLM credentials.
- **Regression gate** — scores are compared against your previous run; a case that drops more than one letter grade fails the build.

## Quickstart

```bash
pip install git+https://github.com/D0NO1/skill-eval.git
# or: pipx install git+https://github.com/D0NO1/skill-eval.git
```

```bash
cd my-skill
skillev init     # scaffold evals/ with a working example case
skillev run      # runs with the mock agent — no API key needed
```

Then wire your real agent into `evals/env.yaml`:

```yaml
agent: claude        # headless Claude Code; adapters are pluggable
model: claude-sonnet-4-5
max_turns: 8
timeout: 600
```

See [`examples/commit-linter/`](examples/commit-linter) for a complete, runnable skill suite.

## The case format

```text
my-skill/
├── SKILL.md
└── evals/
    ├── env.yaml                      # which agent runs the cases
    └── cases/
        └── conventional-subject/
            ├── task.md               # the prompt handed to the agent
            ├── fixtures/changes.diff # copied into a fresh workspace
            ├── grader.yaml           # what "correct" means
            └── mock.yaml             # scripted mock-agent behavior (optional)
```

Every case runs in a **throwaway workspace** seeded with `fixtures/`, so cases
can't pollute each other.

### grader.yaml

```yaml
checks:
  - type: file_exists
    path: commit-msg.txt
  - type: regex
    file: commit-msg.txt
    pattern: '^(feat|fix|docs|refactor|test|chore)(\([^)]*\))?: .+'
  - type: rubric
    model: gpt-4o-mini          # any OpenAI-compatible chat model
    min_score: 3
    rubric: |
      Score 1-5: does the message body explain WHY the change is needed,
      not just WHAT changed?
```

### Graders

| type | passes when… | params |
|---|---|---|
| `file_exists` | the file exists in the workspace | `path` |
| `contains` | text appears in a file or the transcript | `file` (`transcript` for the log), `any_of` / `all_of` / `text` |
| `regex` | the pattern matches (multiline) | `file`, `pattern` |
| `command` | a shell command exits 0 | `run` |
| `rubric` | an LLM judge scores the run ≥ `min_score` (1–5) | `model`, `rubric`, `min_score` |

A case's score is the mean of its check scores (deterministic checks are 0/1,
a rubric scores `n/5`), mapped to letter grades **A ≥ 90, B ≥ 75, C ≥ 60, else D**.

Rubric checks need `SKILL_EVAL_API_KEY` (and optionally `SKILL_EVAL_BASE_URL`,
default `https://api.openai.com/v1`).

## Regression gate

Each run is stored under `.skillev/runs/`. The next `skillev run` diffs
against the newest stored run:

- drop **≤ 1 grade** → warning
- drop **> 1 grade** → `regression gate: FAIL`, exit code 1

New cases are informational; removed cases are reported. Wire it into CI:

```yaml
- run: skillev run .
```

Typical workflow: change your skill, run the suite, iterate until the gate is
green, commit.

## Agents

| adapter | behavior |
|---|---|
| `mock` (default) | Deterministic; driven by the case's `mock.yaml` (`transcript`, `create_files`, `command`, `fail`). Ideal for CI and grader development. |
| `claude` | Runs headless Claude Code (`claude -p`) in the case workspace. |

Custom adapters are one class: subclass `AgentAdapter`, implement
`run(task, workspace, case, env) -> AgentRun`, register it in
`skillev/adapters/__init__.py`. PRs for other agent runtimes welcome.

## CLI

```text
skillev init [dir]       scaffold evals/ in a skill repo
skillev run  [dir]       run the suite (options: --agent, --no-baseline, --json)
skillev history [dir]    list past runs
```

## Roadmap

- [ ] judge ensembling (n-sample self-consistency to cut judge noise)
- [ ] `skillev gate --against <branch>` for explicit CI baselines
- [ ] transcript snapshots for debugging failed cases
- [ ] HTML report
- [ ] skill-marketplace integrations

## Contributing

The harness tests itself: `pip install -e . pytest && pytest`. The whole suite
runs offline with the mock agent — please keep it that way.

## License

[MIT](LICENSE)
