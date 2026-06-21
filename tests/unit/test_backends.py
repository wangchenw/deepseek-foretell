"""Phase 0: backend factory tests."""

from __future__ import annotations

from deepagents.backends import StateBackend
from langgraph.checkpoint.memory import MemorySaver

from foretell.backends import create_agent_backend, create_checkpointer


def test_create_checkpointer_dev_returns_memory_saver() -> None:
    checkpointer = create_checkpointer("dev")
    assert isinstance(checkpointer, MemorySaver)


def test_create_agent_backend_returns_state_backend() -> None:
    backend = create_agent_backend(runtime=None)
    assert isinstance(backend, StateBackend)
