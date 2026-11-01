"""Headless Claude Code adapter (`claude -p`)."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .base import AgentAdapter, AgentRun


class ClaudeCodeAdapter(AgentAdapter):
    name = "claude"

    def run(self, task, workspace: Path, case=None, env=None) -> AgentRun:
        if shutil.which("claude") is None:
            return AgentRun(
                transcript="",
                exit_code=-1,
            )
        cmd = [
            "claude",
            "-p",
            task,
            "--output-format",
            "text",
            "--max-turns",
            str(env.max_turns if env else 8),
        ]
        if env and env.model:
            cmd += ["--model", env.model]
        try:
            proc = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=env.timeout if env else 600,
            )
            transcript = proc.stdout or ""
            if proc.stderr:
                transcript += "\n" + proc.stderr
            return AgentRun(transcript=transcript, exit_code=proc.returncode)
        except subprocess.TimeoutExpired:
            return AgentRun(transcript="[skillev] agent run timed out", exit_code=-1)
