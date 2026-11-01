import json
import shutil
from pathlib import Path

import pytest

from skillev import cli
from skillev.spec import load_suite

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPO_ROOT / "examples" / "commit-linter"


@pytest.fixture
def skill(tmp_path):
    dest = tmp_path / "commit-linter"
    shutil.copytree(EXAMPLE, dest)
    return dest


def test_run_suite_mock_all_pass():
    suite = load_suite(EXAMPLE)
    from skillev.runner import run_suite

    result = run_suite(suite)
    assert all(c.score == 100.0 and c.grade == "A" for c in result.cases)
    assert result.avg_score == 100.0


def test_cli_run_then_regression(skill, capsys):
    assert cli.main(["run", str(skill)]) == 0
    # second run with no changes -> no regressions, gate PASS
    assert cli.main(["run", str(skill)]) == 0
    out = capsys.readouterr().out
    assert "regression gate: PASS" in out


def test_cli_run_detects_regression(skill, capsys):
    cli.main(["run", str(skill), "--no-baseline"])
    capsys.readouterr()
    # "upgrade" the skill: mock now writes a non-conventional subject
    case = skill / "evals" / "cases" / "conventional-subject" / "mock.yaml"
    case.write_text(
        "transcript: |\n  done\ncreate_files:\n  commit-msg.txt: |\n    updated stuff\n",
        encoding="utf-8",
    )
    rc = cli.main(["run", str(skill)])
    out = capsys.readouterr().out
    assert rc == 1 and "regression gate: FAIL" in out


def test_cli_init_and_history(tmp_path, capsys):
    assert cli.main(["init", str(tmp_path)]) == 0
    assert (tmp_path / "evals" / "cases" / "example" / "grader.yaml").exists()
    # the scaffolded example case passes out of the box
    assert cli.main(["run", str(tmp_path)]) == 0
    capsys.readouterr()
    assert cli.main(["history", str(tmp_path)]) == 0
    assert "avg=" in capsys.readouterr().out


def test_cli_json_output(skill, capsys):
    assert cli.main(["run", str(skill), "--no-baseline", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["skill"] == "commit-linter" and len(data["cases"]) == 2
