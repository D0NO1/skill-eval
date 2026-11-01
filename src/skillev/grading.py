"""Score computation: checks -> case score -> letter grade."""
from __future__ import annotations

from dataclasses import dataclass, field

from .graders import run_check
from .spec import Case

GRADES = "ABCD"


def letter(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    return "D"


def grade_index(grade: str) -> int:
    return GRADES.index(grade)


@dataclass
class CheckResultDTO:
    type: str
    passed: bool
    score: float
    detail: str = ""

    @classmethod
    def from_result(cls, r) -> "CheckResultDTO":
        return cls(r.type, r.passed, r.score, r.detail)


@dataclass
class CaseResult:
    case: str
    score: float
    grade: str
    checks: list[CheckResultDTO] = field(default_factory=list)
    transcript: str = ""

    def to_dict(self) -> dict:
        return {
            "case": self.case,
            "score": self.score,
            "grade": self.grade,
            "checks": [vars(c) for c in self.checks],
            "transcript": self.transcript,
        }


def grade_case(case: Case, workspace, transcript: str) -> CaseResult:
    specs = (case.grader or {}).get("checks") or []
    results = [CheckResultDTO.from_result(run_check(s, workspace, transcript)) for s in specs]
    if not results:
        return CaseResult(case.name, 0.0, "D", results)
    score = sum(r.score for r in results) / len(results) * 100.0
    return CaseResult(case.name, round(score, 1), letter(score), results)
