"""Deterministic fake agent driven by the case's mock.yaml.

Lets skill authors run their whole eval suite (and CI) without any LLM API
key. mock.yaml fields:

    transcript: |          # text returned as the agent transcript
      ...
    create_files:          # files the "agent" writes into the workspace
      out.txt: |
        content
    command: python gen.py # optional shell command run in the workspace
    fail: true             # optional: simulate a failing agent run
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from .base import AgentAdapter, AgentRun


class MockAdapter(AgentAdapter):
    name = "mock"

    def run(self, task, workspace: Path, case=None, env=None) -> AgentRun:
        spec = (case.mock if case else None) or {}
        command = spec.get("command")
        if command:
            subprocess.run(
                command, shell=True, cwd=workspace, capture_output=True, text=True, timeout=120
            )
        for name, content in (spec.get("create_files") or {}).items():
            p = workspace / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(str(content), encoding="utf-8")
        return AgentRun(
            transcript=str(spec.get("transcript", "")),
            exit_code=1 if spec.get("fail") else 0,
        )
