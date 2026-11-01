from pathlib import Path

from .base import CheckResult
from .deterministic import DISPATCH
from .rubric import rubric


def run_check(spec: dict, workspace: Path, transcript: str) -> CheckResult:
    ctype = str(spec.get("type", ""))
    if ctype == "rubric":
        return rubric(spec, workspace, transcript)
    fn = DISPATCH.get(ctype)
    if fn is None:
        return CheckResult(ctype or "(none)", False, 0.0, f"unknown check type: {ctype!r}")
    return fn(spec, workspace, transcript)


__all__ = ["CheckResult", "run_check"]
