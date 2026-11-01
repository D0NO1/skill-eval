"""LLM-as-judge rubric grader (OpenAI-compatible chat API, stdlib only).

grader.yaml:

    - type: rubric
      model: gpt-4o-mini          # required
      min_score: 3                # pass threshold, 1-5 (default 3)
      rubric: |
        Score 1-5: ...

Environment:
    SKILL_EVAL_API_KEY    required
    SKILL_EVAL_BASE_URL   optional, default https://api.openai.com/v1
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .base import CheckResult

SYSTEM_PROMPT = (
    "You are a strict but fair grader for AI agent runs. "
    "Score the run against the rubric. Reply with JSON only: "
    '{"score": <integer 1-5>, "reason": "<one sentence>"}'
)

MAX_FILES_BYTES = 32_000


def _collect_files(workspace: Path) -> str:
    chunks: list[str] = []
    total = 0
    for p in sorted(workspace.rglob("*")):
        if not p.is_file() or p.stat().st_size > 200_000:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = p.relative_to(workspace).as_posix()
        chunk = f"--- {rel} ---\n{text}\n"
        if total + len(chunk) > MAX_FILES_BYTES:
            chunks.append("[truncated]")
            break
        chunks.append(chunk)
        total += len(chunk)
    return "\n".join(chunks) or "(no files)"


def _extract_json(text: str) -> str:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON in judge response: {text[:200]}")
    return text[start : end + 1]


def rubric(spec: dict, workspace: Path, transcript: str) -> CheckResult:
    model = spec.get("model")
    rubric_text = str(spec.get("rubric", "")).strip()
    min_score = float(spec.get("min_score", 3))
    if not model or not rubric_text:
        return CheckResult("rubric", False, 0.0, "rubric check requires 'model' and 'rubric'")
    api_key = os.environ.get("SKILL_EVAL_API_KEY")
    if not api_key:
        return CheckResult("rubric", False, 0.0, "SKILL_EVAL_API_KEY not set")
    base_url = os.environ.get("SKILL_EVAL_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    import urllib.request

    prompt = (
        f"# Rubric\n{rubric_text}\n\n"
        f"# Agent transcript\n{transcript or '(empty)'}\n\n"
        f"# Workspace files\n{_collect_files(workspace)}\n"
    )
    body = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    req = urllib.request.Request(
        base_url + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            content = json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"]
        data = json.loads(_extract_json(content))
        score = max(1, min(5, int(data.get("score", 0))))
        return CheckResult("rubric", score >= min_score, score / 5.0, str(data.get("reason", ""))[:500])
    except Exception as exc:  # network, auth, parse errors -> fail the check
        return CheckResult("rubric", False, 0.0, f"rubric judge failed: {exc}")
