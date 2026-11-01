import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from skillev import cli
from skillev.graders.rubric import rubric as run_rubric

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPO_ROOT / "examples" / "commit-linter"


@pytest.fixture
def skill(tmp_path):
    dest = tmp_path / "commit-linter"
    shutil.copytree(EXAMPLE, dest)
    return dest


def test_rubric_median_of_samples(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILL_EVAL_API_KEY", "test")
    seq = iter([(5, "r1"), (1, "r2"), (3, "r3")])
    with patch("skillev.graders.rubric._judge_once", side_effect=lambda *a, **k: next(seq)):
        r = run_rubric(
            {"model": "m", "samples": 3, "rubric": "x", "min_score": 4}, tmp_path, ""
        )
    assert r.score == 3 / 5 and not r.passed  # median of [5,1,3] is 3
    assert "3 sample(s)" in r.detail and "r2" in r.detail


def test_rubric_single_sample_default_temperature(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILL_EVAL_API_KEY", "test")
    seen = {}
    with patch(
        "skillev.graders.rubric._judge_once",
        side_effect=lambda *a, **k: seen.setdefault("t", a[2]) or (5, "ok"),
    ):
        r = run_rubric({"model": "m", "rubric": "x"}, tmp_path, "")
    assert r.passed and seen["t"] == 0.0  # deterministic by default


def test_cli_gate_pass_and_fail(skill, capsys):
    cli.main(["run", str(skill), "--no-baseline"])
    cli.main(["run", str(skill), "--no-baseline"])
    capsys.readouterr()
    assert cli.main(["gate", str(skill)]) == 0
    assert "regression gate: PASS" in capsys.readouterr().out
    # break the skill, run again -> gate fails (no re-run needed for gate)
    case = skill / "evals" / "cases" / "conventional-subject" / "mock.yaml"
    case.write_text(
        "transcript: |\n  done\ncreate_files:\n  commit-msg.txt: |\n    updated stuff\n",
        encoding="utf-8",
    )
    assert cli.main(["run", str(skill), "--no-baseline"]) == 0
    assert cli.main(["gate", str(skill)]) == 1
    assert "regression gate: FAIL" in capsys.readouterr().out
    # explicit --against also works
    assert cli.main(["gate", str(skill), "--against", "nosuchrun"]) == 2


def test_cli_show(skill, capsys):
    cli.main(["run", str(skill), "--no-baseline"])
    capsys.readouterr()
    assert cli.main(["show", "conventional-subject", str(skill)]) == 0
    out = capsys.readouterr().out
    assert "[PASS] file_exists" in out and "--- transcript ---" in out
    assert "Reading changes.diff" in out  # transcript round-trips through storage
    assert cli.main(["show", "no-such-case", str(skill)]) == 2
    out = capsys.readouterr().out
    assert "available:" in out


def test_cli_html_report(skill, tmp_path, capsys):
    out_html = tmp_path / "report.html"
    cli.main(["run", str(skill), "--no-baseline", "--html", str(out_html)])
    capsys.readouterr()
    cli.main(["run", str(skill), "--html", str(out_html)])
    text = out_html.read_text(encoding="utf-8")
    assert "commit-linter" in text and "eval report" in text
    assert "regression gate: PASS" in text  # second run has a baseline
    assert "conventional-subject" in text
