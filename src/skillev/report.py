"""Baseline comparison and regression gate.

Gate rule: a case that drops MORE than one letter grade vs the baseline
fails the gate. A drop of exactly one grade is a warning.
"""
from __future__ import annotations

from dataclasses import dataclass

from .grading import grade_index
from .runner import SuiteResult


@dataclass
class CaseDiff:
    case: str
    base_grade: str | None
    cur_grade: str
    status: str  # "ok" | "warn" | "gate" | "new" | "removed"
    detail: str = ""


def compare(current: SuiteResult, baseline: SuiteResult) -> tuple[list[CaseDiff], bool]:
    base_by_name = {c.case: c for c in baseline.cases}
    cur_names = {c.case for c in current.cases}
    diffs: list[CaseDiff] = []
    gate_failed = False

    for cur in current.cases:
        base = base_by_name.get(cur.case)
        if base is None:
            diffs.append(CaseDiff(cur.case, None, cur.grade, "new", "no baseline for this case"))
            continue
        drop = grade_index(cur.grade) - grade_index(base.grade)
        if drop > 1:
            diffs.append(
                CaseDiff(cur.case, base.grade, cur.grade, "gate", f"dropped {drop} grades")
            )
            gate_failed = True
        elif drop == 1:
            diffs.append(CaseDiff(cur.case, base.grade, cur.grade, "warn", "dropped 1 grade"))
        else:
            diffs.append(CaseDiff(cur.case, base.grade, cur.grade, "ok"))

    for name in sorted(set(base_by_name) - cur_names):
        diffs.append(CaseDiff(name, base_by_name[name].grade, None, "removed", "case missing in current run"))
    return diffs, gate_failed


def render(result: SuiteResult, diffs: list[CaseDiff] | None, baseline_id: str | None) -> str:
    lines = [
        f"skill: {result.skill}   adapter: {result.adapter}   run: {result.run_id}",
        f"{'case':<32} {'score':>7} {'grade':>5}"
        + ("   " + f"vs baseline {baseline_id}" if baseline_id else ""),
    ]
    for c in result.cases:
        line = f"{c.case:<32} {c.score:>7.1f} {c.grade:>5}"
        if diffs is not None:
            d = next((d for d in diffs if d.case == c.case), None)
            if d and d.status != "new":
                mark = {"ok": "=", "warn": "-1 (warn)", "gate": f"{d.detail} FAIL"}[d.status]
                line += f"   {mark}"
            elif d:
                line += "   +new"
        lines.append(line)
    lines.append(f"avg score: {result.avg_score}")
    if diffs is not None:
        for d in diffs:
            if d.status == "removed":
                lines.append(f"removed case: {d.case} (was {d.base_grade})")
        gate = "FAIL" if any(d.status == "gate" for d in diffs) else "PASS"
        lines.append(f"regression gate: {gate}")
    return "\n".join(lines)
