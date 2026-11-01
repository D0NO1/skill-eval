"""Persist and load run results under <skill>/.skillev/runs/."""
from __future__ import annotations

import json
from pathlib import Path

from .runner import SuiteResult


def runs_dir(skill_dir: Path) -> Path:
    return Path(skill_dir) / ".skillev" / "runs"


def save(skill_dir: Path, result: SuiteResult) -> Path:
    d = runs_dir(skill_dir)
    d.mkdir(parents=True, exist_ok=True)
    # Keep timestamps unique: bump the second until the run id is free, so
    # filenames stay clean IDs and sort order == save order == time order.
    out = d / f"{result.run_id}.json"
    if out.exists():
        from datetime import datetime, timedelta

        dt = datetime.strptime(result.timestamp, "%Y%m%dT%H%M%S")
        while out.exists():
            dt += timedelta(seconds=1)
            result.timestamp = dt.strftime("%Y%m%dT%H%M%S")
            out = d / f"{result.run_id}.json"
    out.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def list_runs(skill_dir: Path) -> list[Path]:
    """All runs, oldest first. Sorted by the timestamp stored *inside* each
    file — filenames may carry -2/-3 suffixes from same-second runs, so the
    filename itself is only an ID, not an ordering key."""
    d = runs_dir(skill_dir)
    if not d.is_dir():
        return []

    def key(p: Path) -> tuple:
        try:
            ts = json.loads(p.read_text(encoding="utf-8")).get("timestamp", "")
        except Exception:
            ts = ""
        return (ts, p.name)

    return sorted(d.glob("*.json"), key=key)


def _from_dict(data: dict) -> SuiteResult:
    from .grading import CaseResult, CheckResultDTO

    return SuiteResult(
        skill=data.get("skill", ""),
        adapter=data.get("adapter", ""),
        timestamp=data.get("timestamp", ""),
        git_branch=data.get("git_branch"),
        git_sha=data.get("git_sha"),
        cases=[
            CaseResult(
                case=c.get("case", ""),
                score=c.get("score", 0.0),
                grade=c.get("grade", "D"),
                checks=[CheckResultDTO(**ck) for ck in c.get("checks", [])],
                transcript=c.get("transcript", ""),
            )
            for c in data.get("cases", [])
        ],
    )


def load(skill_dir: Path, run_id: str) -> SuiteResult | None:
    p = runs_dir(skill_dir) / f"{run_id}.json"
    if not p.exists():
        p = runs_dir(skill_dir) / f"{run_id}"
    if not p.exists():
        return None
    return _from_dict(json.loads(p.read_text(encoding="utf-8")))


def latest(skill_dir: Path) -> SuiteResult | None:
    """Most recent run on disk (the current run is not saved yet when called)."""
    runs = list_runs(skill_dir)
    if not runs:
        return None
    return _from_dict(json.loads(runs[-1].read_text(encoding="utf-8")))
