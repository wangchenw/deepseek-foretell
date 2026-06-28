"""Unit tests for SSE formatting helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessageChunk

from api.streaming import (
    _collect_final_assistant_text,
    format_sse,
    stream_agent_messages,
)


@pytest.fixture(autouse=True)
def _force_dev_env(dev_env) -> None:
    """Avoid audit-log writes when local .env is prod."""


def test_format_sse_serializes_json() -> None:
    line = format_sse("token", {"content": "hi"})
    assert line == 'event: token\ndata: {"content": "hi"}\n\n'


def test_collect_final_assistant_text_uses_last_message_only() -> None:
    def fake_stream():
        yield (
            AIMessageChunk(
                content="第一轮思考",
                id="turn-1",
                tool_call_chunks=[
                    {"name": "get_schedule_by_date", "args": "{}", "id": "1", "index": 0},
                ],
            ),
            {},
        )
        yield (AIMessageChunk(content="最终回答", id="turn-2"), {})

    assert _collect_final_assistant_text(fake_stream()) == "最终回答"


def test_stream_agent_messages_yields_only_final_message() -> None:
    agent = MagicMock()

    def fake_stream(*_args, **_kwargs):
        yield (AIMessageChunk(content="中间轮次", id="turn-1"), {})
        yield (AIMessageChunk(content="最终", id="turn-2"), {})

    agent.stream = fake_stream

    events = list(
        stream_agent_messages(
            agent,
            {"messages": [{"role": "user", "content": "hi"}]},
            {"configurable": {"thread_id": "t1"}},
            "t1",
            "user-1",
            "hi",
        )
    )

    joined = "".join(events)
    assert "event: thread" in joined
    assert '"content": "中间轮次"' not in joined
    assert '"content": "最终"' in joined
    assert "event: done" in joined


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
            "user-1",
            "hi",
        )
    )

    joined = "".join(events)
    assert "event: thread" in joined
    assert '"content": "AB"' in joined or '"content": "B"' in joined
    assert "event: done" in joined
