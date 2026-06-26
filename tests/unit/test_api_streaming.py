"""Phase 4: SSE streaming endpoint tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessageChunk

from api.main import app, get_agent


@pytest.fixture(autouse=True)
def _clear_agent_cache() -> None:
    get_agent.cache_clear()
    yield
    get_agent.cache_clear()


@pytest.fixture
def client():
    return TestClient(app)


def _mock_stream_agent(chunks: list[str]) -> MagicMock:
    agent = MagicMock()

    def fake_stream(*_args, **_kwargs):
        for text in chunks:
            yield (AIMessageChunk(content=text), {"langgraph_node": "agent"})

    agent.stream = fake_stream
    return agent


def test_stream_requires_user_id(client, dev_env) -> None:
    response = client.post("/v1/chat", json={"message": "hello", "stream": True})
    assert response.status_code == 401


def test_stream_rejects_foreign_thread_id(client, dev_env) -> None:
    response = client.post(
        "/v1/chat",
        headers={"X-User-Id": "user-a"},
        json={"message": "hello", "thread_id": "user-b:abc123", "stream": True},
    )
    assert response.status_code == 403


def test_stream_returns_sse_events(client, dev_env, monkeypatch) -> None:
    monkeypatch.setattr("api.main.get_agent", lambda: _mock_stream_agent(["你好", "世界"]))

    with client.stream(
        "POST",
        "/v1/chat",
        headers={"X-User-Id": "user-1"},
        json={"message": "hello", "stream": True},
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

        body = response.read().decode()

    assert "event: thread" in body
    assert '"thread_id"' in body
    assert "event: token" in body
    assert "你好" in body
    assert "世界" in body
    assert "event: done" in body


def test_stream_uses_provided_thread_id(client, dev_env, monkeypatch) -> None:
    monkeypatch.setattr("api.main.get_agent", lambda: _mock_stream_agent(["ok"]))

    thread_id = "user-1:session-abc"
    with client.stream(
        "POST",
        "/v1/chat",
        headers={"X-User-Id": "user-1"},
        json={"message": "hello", "stream": True, "thread_id": thread_id},
    ) as response:
        assert response.status_code == 200
        body = response.read().decode()

    assert thread_id in body
