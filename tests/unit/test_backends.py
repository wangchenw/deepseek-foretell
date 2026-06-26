"""Phase 0: backend factory tests."""

from __future__ import annotations

from deepagents.backends import CompositeBackend, FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

from foretell.backends import create_agent_backend, create_checkpointer


def test_create_checkpointer_dev_returns_memory_saver() -> None:
    checkpointer = create_checkpointer("dev")
    assert isinstance(checkpointer, MemorySaver)


def test_create_agent_backend_returns_composite_with_skills_route() -> None:
    backend = create_agent_backend()
    assert isinstance(backend, CompositeBackend)
    skills_backend = backend.routes["/skills/"]
    assert isinstance(skills_backend, FilesystemBackend)
