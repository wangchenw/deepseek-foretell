"""Agent 中间件：把 MiniMax 的行内 <think>…</think> 思考转成标准推理块。

MiniMax 走 OpenAI 兼容接口时，会把思考用 ``<think>…</think>`` 直接写进 content
（其官方文档说明：OpenAI ChatCompletion 原生格式不支持单独返回 thinking）。
结果就是思考和正文混在一起，在任何前端都不优雅。

这里用 langchain 的 ``wrap_model_call`` 中间件，在模型返回后把 ``<think>`` 段切出来，
重挂成 LangChain 标准 reasoning 内容块，正文只保留真正的回答。这样 LangGraph Studio
以及任意 AI 前端都会把思考渲染成独立（可折叠）的推理区，而不是正文里的一坨标签——
既**保留**思考，又优雅。

工具调用（tool_calls）不受影响：它们与 content 分开存储，这里只改写 content。
"""

from __future__ import annotations

import re
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage

_THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL)


def split_think(text: str) -> tuple[str, str]:
    """把文本拆成 (reasoning, answer)。无 think 段时 reasoning 为空字符串。"""
    reasonings = [m.group(1).strip() for m in _THINK_RE.finditer(text)]
    answer = _THINK_RE.sub("", text)
    # 容错：未闭合的 <think>（极少见，如被截断），把开标签之后的内容算作思考
    if "<think>" in answer:
        head, _, tail = answer.partition("<think>")
        if tail.strip():
            reasonings.append(tail.strip())
        answer = head
    reasoning = "\n\n".join(r for r in reasonings if r)
    return reasoning, answer.strip()


def rewrite_message(msg: AIMessage) -> AIMessage:
    """把含 <think> 的字符串 content 改写为 [推理块, 正文块]；否则原样返回。"""
    if not isinstance(msg.content, str) or "<think>" not in msg.content:
        return msg
    reasoning, answer = split_think(msg.content)
    if not reasoning:
        return msg
    blocks: list[dict[str, Any]] = [{"type": "reasoning", "reasoning": reasoning}]
    if answer:
        blocks.append({"type": "text", "text": answer})
    return msg.model_copy(update={"content": blocks})


def _apply(response: Any) -> Any:
    """把模型响应里所有 AIMessage 的 <think> 切成推理块（同步/异步共用）。"""
    result = getattr(response, "result", None)
    if result is None:
        # 某些路径下 handler 可能直接返回 AIMessage
        return rewrite_message(response) if isinstance(response, AIMessage) else response
    response.result = [
        rewrite_message(m) if isinstance(m, AIMessage) else m for m in result
    ]
    return response


class ReasoningSplitMiddleware(AgentMiddleware):
    """在每次模型调用返回后，将 <think> 思考切成标准推理块。

    同时实现同步与异步版本：LangGraph dev / Studio 走异步（ainvoke/astream），
    本地脚本与测试常走同步（invoke），两条路径行为一致。
    """

    def wrap_model_call(self, request, handler):
        return _apply(handler(request))

    async def awrap_model_call(self, request, handler):
        return _apply(await handler(request))


# 供 create_deep_agent(middleware=[...]) 使用的实例
reasoning_split_middleware = ReasoningSplitMiddleware()
