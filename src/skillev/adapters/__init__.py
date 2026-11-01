from .base import AgentAdapter, AgentRun
from .claude_code import ClaudeCodeAdapter
from .mock import MockAdapter

_REGISTRY = {
    MockAdapter.name: MockAdapter,
    ClaudeCodeAdapter.name: ClaudeCodeAdapter,
}


def get_adapter(name: str) -> AgentAdapter:
    cls = _REGISTRY.get(name)
    if cls is None:
        raise SystemExit(
            f"Unknown agent adapter '{name}'. Available: {', '.join(sorted(_REGISTRY))}"
        )
    return cls()


__all__ = ["AgentAdapter", "AgentRun", "get_adapter"]
