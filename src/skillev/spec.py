"""Load and validate eval specs (env.yaml, cases, grader.yaml)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class EnvSpec:
    """Suite-level environment: which agent runs the cases and how."""

    agent: str = "mock"
    model: str | None = None
    max_turns: int = 8
    timeout: int = 600


@dataclass
class Case:
    name: str
    path: Path  # case directory
    task: str  # content of task.md
    grader: dict = field(default_factory=dict)  # parsed grader.yaml
    mock: dict | None = None  # parsed mock.yaml (optional, for the mock adapter)


@dataclass
class EvalSuite:
    skill_dir: Path
    skill_name: str
    env: EnvSpec
    cases: list[Case]


def load_suite(skill_dir: Path) -> EvalSuite:
    skill_dir = Path(skill_dir).resolve()
    if not skill_dir.is_dir():
        raise SystemExit(f"Skill directory not found: {skill_dir}")
    evals = skill_dir / "evals"
    env = EnvSpec()
    env_file = evals / "env.yaml"
    if env_file.exists():
        data = yaml.safe_load(env_file.read_text(encoding="utf-8")) or {}
        env = EnvSpec(
            agent=str(data.get("agent", "mock")),
            model=data.get("model"),
            max_turns=int(data.get("max_turns", 8)),
            timeout=int(data.get("timeout", 600)),
        )

    cases_dir = evals / "cases"
    cases: list[Case] = []
    if cases_dir.is_dir():
        for d in sorted(p for p in cases_dir.iterdir() if p.is_dir()):
            task_file = d / "task.md"
            grader_file = d / "grader.yaml"
            if not task_file.exists() or not grader_file.exists():
                continue  # not a case directory
            grader = yaml.safe_load(grader_file.read_text(encoding="utf-8")) or {}
            mock_file = d / "mock.yaml"
            mock = None
            if mock_file.exists():
                mock = yaml.safe_load(mock_file.read_text(encoding="utf-8"))
            cases.append(
                Case(
                    name=d.name,
                    path=d,
                    task=task_file.read_text(encoding="utf-8"),
                    grader=grader,
                    mock=mock,
                )
            )
    if not cases:
        raise SystemExit(
            f"No eval cases found under {cases_dir}.\n"
            "Each case needs a directory with task.md + grader.yaml. "
            "Run `skillev init` to scaffold one."
        )
    return EvalSuite(skill_dir=skill_dir, skill_name=skill_dir.name, env=env, cases=cases)
