"""`skillev init` scaffolding."""
from __future__ import annotations

from pathlib import Path

ENV_YAML = """\
# Agent that executes each case. mock = deterministic fake agent (no API key
# needed, driven by each case's mock.yaml); claude = headless Claude Code.
agent: mock
# model: claude-sonnet-4-5
max_turns: 8
timeout: 600
"""

TASK_MD = """\
Describe the task for the agent here, as you would hand it to a colleague.

Fixtures from fixtures/ are copied into a fresh workspace before the run.
"""

GRADER_YAML = """\
checks:
  - type: file_exists
    path: output.txt
  - type: contains
    file: output.txt
    any_of: ["TODO"]
  # - type: rubric
  #   model: gpt-4o-mini
  #   min_score: 3
  #   rubric: |
  #     Score 1-5: ...
"""

MOCK_YAML = """\
# Behavior of the mock agent for this case (delete when using a real agent).
transcript: |
  Working on the task...
  Done.
create_files:
  output.txt: |
    TODO
"""

SCAFFOLD_FILES = {
    "evals/env.yaml": ENV_YAML,
    "evals/cases/example/task.md": TASK_MD,
    "evals/cases/example/grader.yaml": GRADER_YAML,
    "evals/cases/example/mock.yaml": MOCK_YAML,
}


def write_scaffold(skill_dir: Path) -> list[str]:
    skill_dir = Path(skill_dir)
    if (skill_dir / "evals" / "cases").is_dir():
        return []
    created = []
    for rel, content in SCAFFOLD_FILES.items():
        p = skill_dir / rel
        if p.exists():
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        created.append(rel)
    return created
