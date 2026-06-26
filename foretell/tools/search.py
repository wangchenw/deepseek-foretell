"""互联网搜索工具（Tavily）。默认未注册到主智能体；仅在结构化 DB 无法覆盖时作 fallback 手动接入。"""

import json
import os
from typing import Literal

from langchain.tools import tool
from tavily import TavilyClient


def _get_tavily_client() -> TavilyClient:
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("未设置 TAVILY_API_KEY。请在环境变量中配置，用于互联网搜索。")
    return TavilyClient(api_key=api_key)


@tool
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> str:
    """在互联网上搜索与查询相关的最新信息。

    Args:
        query: 搜索关键词或问题。
        max_results: 返回结果数量上限。
        topic: 搜索主题类别（general / news / finance）。
        include_raw_content: 是否包含网页原文。
    """
    client = _get_tavily_client()
    results = client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
    return json.dumps(results, ensure_ascii=False, indent=2)
