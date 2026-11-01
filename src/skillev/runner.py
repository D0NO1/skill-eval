"""Run an eval suite: for each case, set up a throwaway workspace, run the
agent, grade the artifacts."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .adapters import get_adapter
from .grading import CaseResult, grade_case
from .spec import EvalSuite

TRANSCRIPT_SAVED_CHARS = 8000


@dataclass
class SuiteResult:
    skill: str
    adapter: str
    timestamp: str
    git_branch: str | None
    git_sha: str | None
    cases: list[CaseResult] = field(default_factory=list)

    @property
    def run_id(self) -> str:
        ts = self.timestamp.replace(":", "").replace("-", "")
        return f"{ts}-{self.git_sha or 'nogit'}"

    @property
    def avg_score(self) -> float:
        return round(sum(c.score for c in self.cases) / len(self.cases), 1) if self.cases else 0.0

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "adapter": self.adapter,
            "timestamp": self.timestamp,
            "run_id": self.run_id,
            "git_branch": self.git_branch,
            "git_sha": self.git_sha,
            "avg_score": self.avg_score,
            "cases": [c.to_dict() for c in self.cases],
        }


def _git_info(skill_dir: Path) -> tuple[str | None, str | None]:
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=skill_dir, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=skill_dir, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        return (branch or None), (sha or None)
    except Exception:
        return None, None


def run_suite(suite: EvalSuite, adapter_name: str | None = None) -> SuiteResult:
    adapter = get_adapter(adapter_name or suite.env.agent)
    case_results: list[CaseResult] = []
    for case in suite.cases:
        with tempfile.TemporaryDirectory(prefix="skillev-") as td:
            workspace = Path(td)
            fixtures = case.path / "fixtures"
            if fixtures.is_dir():
                shutil.copytree(fixtures, workspace, dirs_exist_ok=True)
            agent_run = adapter.run(task=case.task, workspace=workspace, case=case, env=suite.env)
            result = grade_case(case, workspace, agent_run.transcript)
            result.transcript = agent_run.transcript[:TRANSCRIPT_SAVED_CHARS]
            case_results.append(result)
    branch, sha = _git_info(suite.skill_dir)
    return SuiteResult(
        skill=suite.skill_name,
        adapter=adapter.name,
        timestamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S"),
        git_branch=branch,
        git_sha=sha,
        cases=case_results,
    )
