"""Deterministic graders: file_exists, contains, regex, command.

Common fields for text checks:
    file: <workspace-relative path>  or  "transcript"
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .base import CheckResult


def _read_target(spec: dict, workspace: Path, transcript: str) -> str | None:
    name = str(spec.get("file", "transcript"))
    if name == "transcript":
        return transcript
    p = workspace / name
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace")
    return None


def file_exists(spec: dict, workspace: Path, transcript: str) -> CheckResult:
    path = str(spec.get("path", ""))
    ok = (workspace / path).exists()
    detail = "" if ok else f"file not found: {path}"
    return CheckResult("file_exists", ok, 1.0 if ok else 0.0, detail)


def contains(spec: dict, workspace: Path, transcript: str) -> CheckResult:
    text = _read_target(spec, workspace, transcript)
    if text is None:
        return CheckResult("contains", False, 0.0, "target not found")
    needles = spec.get("any_of") or ([spec["text"]] if spec.get("text") else [])
    needles = [str(n) for n in needles]
    if not needles:
        return CheckResult("contains", False, 0.0, "no 'text' or 'any_of' given")
    missing = [n for n in needles if n not in text]
    if spec.get("all_of"):
        ok = not missing
        detail = "" if ok else f"missing: {missing}"
    else:
        ok = len(missing) < len(needles)  # any_of semantics
        detail = "" if ok else f"none of {needles} found"
    return CheckResult("contains", ok, 1.0 if ok else 0.0, detail)


def regex(spec: dict, workspace: Path, transcript: str) -> CheckResult:
    text = _read_target(spec, workspace, transcript)
    if text is None:
        return CheckResult("regex", False, 0.0, "target not found")
    pattern = str(spec.get("pattern", ""))
    if not pattern:
        return CheckResult("regex", False, 0.0, "no 'pattern' given")
    ok = re.search(pattern, text, re.MULTILINE) is not None
    detail = "" if ok else f"pattern not matched: {pattern!r}"
    return CheckResult("regex", ok, 1.0 if ok else 0.0, detail)


def command(spec: dict, workspace: Path, transcript: str) -> CheckResult:
    cmd = str(spec.get("run", ""))
    if not cmd:
        return CheckResult("command", False, 0.0, "no 'run' given")
    proc = subprocess.run(
        cmd, shell=True, cwd=workspace, capture_output=True, text=True, timeout=300
    )
    ok = proc.returncode == 0
    detail = "" if ok else f"exit={proc.returncode} {proc.stderr.strip()[:300]}"
    return CheckResult("command", ok, 1.0 if ok else 0.0, detail)


DISPATCH = {
    "file_exists": file_exists,
    "contains": contains,
    "regex": regex,
    "command": command,
}
