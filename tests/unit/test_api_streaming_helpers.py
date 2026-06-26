"""Unit tests for SSE formatting helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_core.messages import AIMessageChunk

from api.streaming import format_sse, stream_agent_messages


def test_format_sse_serializes_json() -> None:
    line = format_sse("token", {"content": "hi"})
    assert line == 'event: token\ndata: {"content": "hi"}\n\n'


def test_stream_agent_messages_yields_token_events() -> None:
    agent = MagicMock()

    def fake_stream(*_args, **_kwargs):
        yield (AIMessageChunk(content="A"), {})
        yield (AIMessageChunk(content="B"), {})

    agent.stream = fake_stream

    events = list(
        stream_agent_messages(
            agent,
            {"messages": [{"role": "user", "content": "hi"}]},
            {"configurable": {"thread_id": "t1"}},
            "t1",
        )
    )

    joined = "".join(events)
    assert "event: thread" in joined
    assert '"content": "A"' in joined
    assert '"content": "B"' in joined
    assert "event: done" in joined
