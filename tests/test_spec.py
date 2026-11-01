from pathlib import Path

from skillev.spec import load_suite

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_load_example_suite():
    suite = load_suite(REPO_ROOT / "examples" / "commit-linter")
    assert suite.skill_name == "commit-linter"
    assert suite.env.agent == "mock"
    assert [c.name for c in suite.cases] == ["body-explains-why", "conventional-subject"]
    conv = next(c for c in suite.cases if c.name == "conventional-subject")
    assert "commit-msg.txt" in conv.task
    assert conv.grader["checks"][0]["type"] == "file_exists"
    assert conv.mock is not None


def test_missing_cases_exits(tmp_path):
    import pytest

    (tmp_path / "evals").mkdir()
    with pytest.raises(SystemExit):
        load_suite(tmp_path)
