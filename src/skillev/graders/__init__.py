from pathlib import Path

from .base import CheckResult
from .deterministic import DISPATCH
from .rubric import rubric as _rubric_check

# Note: imported with an alias so the `rubric` attribute of this package keeps
# pointing at the rubric *submodule* (mock.patch("skillev.graders.rubric._judge_once")
# resolves attributes through this package).


def run_check(spec: dict, workspace: Path, transcript: str) -> CheckResult:
    ctype = str(spec.get("type", ""))
    if ctype == "rubric":
        return _rubric_check(spec, workspace, transcript)
    fn = DISPATCH.get(ctype)
    if fn is None:
        return CheckResult(ctype or "(none)", False, 0.0, f"unknown check type: {ctype!r}")
    return fn(spec, workspace, transcript)


__all__ = ["CheckResult", "run_check"]
