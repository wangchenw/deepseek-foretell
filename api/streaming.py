"""SSE helpers for /v1/chat streaming responses."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from langchain_core.messages import AIMessageChunk


def format_sse(event: str, data: dict[str, Any] | str) -> str:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def _extract_text_content(content: str | list[Any]) -> str:
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    return "".join(parts)


def stream_agent_messages(
    agent: Any,
    input_state: dict[str, Any],
    config: dict[str, Any],
    thread_id: str,
) -> Iterator[str]:
    """Stream final assistant tokens as SSE events."""
    yield format_sse("thread", {"thread_id": thread_id})

    for chunk in agent.stream(input_state, config=config, stream_mode="messages"):
        token, _metadata = chunk
        if not isinstance(token, AIMessageChunk) or not token.content:
            continue
        text = _extract_text_content(token.content)
        if text:
            yield format_sse("token", {"content": text})

    yield format_sse("done", {"thread_id": thread_id})
