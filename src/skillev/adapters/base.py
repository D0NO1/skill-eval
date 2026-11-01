"""Agent adapter interface: how the harness executes a task."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..spec import Case, EnvSpec


@dataclass
class AgentRun:
    transcript: str
    exit_code: int


class AgentAdapter:
    """Runs one task in a workspace and returns the transcript.

    Adapters must be side-effect isolated: the workspace is a throwaway
    directory pre-populated with the case's fixtures/.
    """

    name = "base"

    def run(self, task: str, workspace: Path, case: Case | None = None, env: EnvSpec | None = None) -> AgentRun:
        raise NotImplementedError
