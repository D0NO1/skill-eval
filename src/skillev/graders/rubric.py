"""LLM-as-judge rubric grader (OpenAI-compatible chat API, stdlib only).

grader.yaml:

    - type: rubric
      model: gpt-4o-mini          # required
      min_score: 3                # pass threshold, 1-5 (default 3)
      samples: 3                  # optional: n independent judgements,
                                  # median score wins (cuts judge noise)
      temperature: 0.7            # optional; defaults to 0.7 when samples > 1
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


def _judge_once(
    prompt: str, model: str, temperature: float, api_key: str, base_url: str
) -> tuple[int, str]:
    """One judge call. Retried once on failure; raises after that."""
    import time
    import urllib.request

    body = {
        "model": model,
        "temperature": temperature,
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
    last_error: Exception | None = None
    for _ in range(2):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                content = json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"]
            data = json.loads(_extract_json(content))
            return max(1, min(5, int(data.get("score", 0)))), str(data.get("reason", ""))
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"judge call failed: {last_error}")


def _median(scores: list[int]) -> int:
    s = sorted(scores)
    return s[len(s) // 2]  # lower-middle for even n: judge conservatively


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

    samples = max(1, int(spec.get("samples", 1)))
    temperature = float(spec.get("temperature", 0.7 if samples > 1 else 0.0))
    prompt = (
        f"# Rubric\n{rubric_text}\n\n"
        f"# Agent transcript\n{transcript or '(empty)'}\n\n"
        f"# Workspace files\n{_collect_files(workspace)}\n"
    )

    scores: list[int] = []
    reasons: list[str] = []
    for _ in range(samples):
        try:
            score, reason = _judge_once(prompt, model, temperature, api_key, base_url)
        except Exception as exc:  # a dead judge call scores lowest, never crashes the run
            score, reason = 1, f"judge failed: {exc}"
        scores.append(score)
        reasons.append(f"{score}/5 {reason}")

    final = _median(scores)
    detail = f"{samples} sample(s): " + " | ".join(reasons)
    return CheckResult("rubric", final >= min_score, final / 5.0, detail[:500])
