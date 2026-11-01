from skillev.graders import run_check


def test_file_exists(tmp_path):
    (tmp_path / "out.txt").write_text("hi", encoding="utf-8")
    assert run_check({"type": "file_exists", "path": "out.txt"}, tmp_path, "").passed
    assert not run_check({"type": "file_exists", "path": "nope.txt"}, tmp_path, "").passed


def test_contains_any_of_and_all_of(tmp_path):
    (tmp_path / "out.txt").write_text("because retrying prevents loss", encoding="utf-8")
    spec = {"type": "contains", "file": "out.txt", "any_of": ["because", "nope"]}
    assert run_check(spec, tmp_path, "").passed
    spec["all_of"] = True
    assert not run_check(spec, tmp_path, "").passed


def test_contains_transcript_target(tmp_path):
    spec = {"type": "contains", "file": "transcript", "text": "Done."}
    assert run_check(spec, tmp_path, "Working...\nDone.").passed


def test_regex(tmp_path):
    (tmp_path / "msg.txt").write_text("fix(ui): crash on load\n", encoding="utf-8")
    spec = {"type": "regex", "file": "msg.txt", "pattern": r"^(feat|fix)(\([^)]*\))?: .+"}
    assert run_check(spec, tmp_path, "").passed
    (tmp_path / "msg.txt").write_text("updated stuff", encoding="utf-8")
    assert not run_check(spec, tmp_path, "").passed


def test_command(tmp_path):
    assert run_check({"type": "command", "run": "exit 0"}, tmp_path, "").passed
    bad = run_check({"type": "command", "run": "exit 3"}, tmp_path, "")
    assert not bad.passed and "exit=3" in bad.detail


def test_unknown_type_fails():
    r = run_check({"type": "wat"}, None, "")
    assert not r.passed and "unknown check type" in r.detail
