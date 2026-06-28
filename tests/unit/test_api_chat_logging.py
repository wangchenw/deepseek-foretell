"""API-layer tests for conversation audit logging hooks."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from api.main import app, get_agent


@pytest.fixture(autouse=True)
def _clear_agent_cache() -> None:
    get_agent.cache_clear()
    yield
    get_agent.cache_clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_sync_chat_logs_success(prod_env, client, monkeypatch) -> None:
    logged: list[dict] = []

    def capture_log(**kwargs):
        logged.append(kwargs)

    agent = MagicMock()
    agent.invoke.return_value = {"messages": [AIMessage(content="分析结果")]}
    monkeypatch.setattr("api.main.get_agent", lambda: agent)
    monkeypatch.setattr("api.main.log_conversation_turn", capture_log)

    response = client.post(
        "/v1/chat",
        headers={"X-User-Id": "user-1"},
        json={"message": "分析周二004", "stream": False},
    )

    assert response.status_code == 200
    assert len(logged) == 1
    assert logged[0]["stream"] is False
    assert logged[0]["status"] == "ok"
    assert logged[0]["user_message"] == "分析周二004"
    assert logged[0]["assistant_message"] == "分析结果"


def test_sync_chat_logs_agent_error(prod_env, monkeypatch) -> None:
    logged: list[dict] = []
    client = TestClient(app, raise_server_exceptions=False)

    agent = MagicMock()
    agent.invoke.side_effect = RuntimeError("model timeout")
    monkeypatch.setattr("api.main.get_agent", lambda: agent)
    monkeypatch.setattr("api.main.log_conversation_turn", lambda **kwargs: logged.append(kwargs))

    response = client.post(
        "/v1/chat",
        headers={"X-User-Id": "user-1"},
        json={"message": "hello", "stream": False},
    )

    assert response.status_code == 500
    assert len(logged) == 1
    assert logged[0]["status"] == "error"
    assert logged[0]["error_message"] == "model timeout"


def test_stream_chat_logs_success(prod_env, client, monkeypatch) -> None:
    from langchain_core.messages import AIMessageChunk

    logged: list[dict] = []

    agent = MagicMock()

    def fake_stream(*_args, **_kwargs):
        yield (AIMessageChunk(content="流式", id="turn-1"), {})

    agent.stream = fake_stream
    monkeypatch.setattr("api.main.get_agent", lambda: agent)
    monkeypatch.setattr("api.streaming.log_conversation_turn", lambda **kwargs: logged.append(kwargs))

    with client.stream(
        "POST",
        "/v1/chat",
        headers={"X-User-Id": "user-1"},
        json={"message": "hello", "stream": True},
    ) as response:
        assert response.status_code == 200
        response.read()

    assert len(logged) == 1
    assert logged[0]["stream"] is True
    assert logged[0]["status"] == "ok"
    assert logged[0]["assistant_message"] == "流式"


def test_chat_does_not_log_in_dev(dev_env, client, monkeypatch) -> None:
    pool = MagicMock()

    agent = MagicMock()
    agent.invoke.return_value = {"messages": [AIMessage(content="ok")]}
    monkeypatch.setattr("api.main.get_agent", lambda: agent)
    monkeypatch.setattr("foretell.conversation_log.get_postgres_pool", lambda _url: pool)

    response = client.post(
        "/v1/chat",
        headers={"X-User-Id": "user-1"},
        json={"message": "hello", "stream": False},
    )

    assert response.status_code == 200
    pool.connection.assert_not_called()
