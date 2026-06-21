"""Skills 加载集成测试。"""

import pytest

from deepagents.middleware.skills import _list_skills_with_errors

from foretell.backends import create_agent_backend


def test_skills_load_from_composite_backend() -> None:
    backend = create_agent_backend()
    skills, error = _list_skills_with_errors(backend, "/skills/")
    assert error is None
    names = {s["name"] for s in skills}
    assert "foretell-light-query" in names
    assert "foretell-entity-resolution" in names
    assert len(skills) >= 11


@pytest.fixture
def mock_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key-for-pytest")


def test_foretell_agent_compiles(mock_llm_env: None) -> None:
    from foretell.agent import create_foretell_agent

    agent = create_foretell_agent(deploy_env="dev")
    assert agent.get_graph().nodes
