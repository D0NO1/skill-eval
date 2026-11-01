"""Check results shared by all graders."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CheckResult:
    type: str
    passed: bool
    score: float  # normalized 0.0 - 1.0
    detail: str = ""
