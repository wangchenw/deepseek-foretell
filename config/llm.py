import os

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from config.settings import DEFAULT_BASE_URL, DEFAULT_MODEL, MINIMAX_THINKING_ENABLED


def get_chat_model(
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> ChatOpenAI:
    """创建 MiniMax ChatOpenAI 实例，配置优先使用传入参数，否则读取环境变量。"""
    resolved_api_key = api_key or os.environ.get("MINIMAX_API_KEY")
    if not resolved_api_key:
        raise ValueError(
            "未设置 MiniMax API Key。请在环境变量中配置 MINIMAX_API_KEY，"
            "或在调用 get_chat_model(api_key=...) 时传入。"
        )

    thinking_type = "adaptive" if MINIMAX_THINKING_ENABLED else "disabled"

    return ChatOpenAI(
        model=model or DEFAULT_MODEL,
        api_key=SecretStr(resolved_api_key),
        base_url=base_url or DEFAULT_BASE_URL,
        extra_body={"thinking": {"type": thinking_type}},
    )
