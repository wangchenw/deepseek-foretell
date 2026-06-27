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


def _collect_final_assistant_text(chunks: Iterator[tuple[Any, Any]]) -> str:
    """Collect tokens from the last assistant message in a LangGraph messages stream.

    Deep Agents / tool-calling graphs emit one AIMessage per model turn. Intermediate
    turns (planning, tool selection) must not be streamed to the client — same rule
    as non-streaming ``result["messages"][-1].content``.
    """
    message_order: list[str] = []
    message_parts: dict[str, list[str]] = {}

    for chunk in chunks:
        token, _metadata = chunk
        if not isinstance(token, AIMessageChunk):
            continue

        msg_id = token.id or "__anonymous__"
        if msg_id not in message_parts:
            message_order.append(msg_id)
            message_parts[msg_id] = []

        text = _extract_text_content(token.content)
        if text:
            message_parts[msg_id].append(text)

    if not message_order:
        return ""

    final_msg_id = message_order[-1]
    return "".join(message_parts.get(final_msg_id, []))


def stream_agent_messages(
    agent: Any,
    input_state: dict[str, Any],
    config: dict[str, Any],
    thread_id: str,
) -> Iterator[str]:
    """Stream the final assistant reply as SSE events."""
    yield format_sse("thread", {"thread_id": thread_id})

    raw_stream = agent.stream(input_state, config=config, stream_mode="messages")
    final_text = _collect_final_assistant_text(raw_stream)

    if final_text:
        yield format_sse("token", {"content": final_text})

    yield format_sse("done", {"thread_id": thread_id})
