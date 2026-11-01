from skillev.grading import CaseResult, letter
from skillev.report import compare
from skillev.runner import SuiteResult


def suite(cases: dict) -> SuiteResult:
    return SuiteResult(
        skill="s", adapter="mock", timestamp="20260101T000000",
        git_branch=None, git_sha=None,
        cases=[CaseResult(case=n, score=0, grade=g, checks=[]) for n, g in cases.items()],
    )


def test_letter_boundaries():
    assert letter(90) == "A" and letter(89.9) == "B"
    assert letter(75) == "B" and letter(74.9) == "C"
    assert letter(60) == "C" and letter(0) == "D"


def test_drop_one_grade_is_warning():
    diffs, failed = compare(suite({"a": "B"}), suite({"a": "A"}))
    assert not failed and diffs[0].status == "warn"


def test_drop_two_grades_fails_gate():
    diffs, failed = compare(suite({"a": "C"}), suite({"a": "A"}))
    assert failed and diffs[0].status == "gate"


def test_new_and_removed_cases():
    diffs, failed = compare(suite({"a": "A", "b": "B"}), suite({"a": "A", "gone": "A"}))
    assert not failed
    statuses = {d.case: d.status for d in diffs}
    assert statuses["b"] == "new" and statuses["gone"] == "removed"
