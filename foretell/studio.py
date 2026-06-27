"""LangGraph Studio / langgraph dev 入口（仅供本地测试调试）。

与 api/main.py 的 FastAPI 启动路径完全独立、互不影响：本模块只被
langgraph.json 引用，给官方 `langgraph dev` 服务器 + LangGraph Studio 使用。

关键区别：这里**不**传 checkpointer / store。
`langgraph dev` 服务器会自带并接管对话记忆（线程持久化），若再传入
自定义 checkpointer 会与之冲突。因此测试入口把持久化交给官方服务器。

工具、系统提示词、子 Agent、Backend 等全部复用 create_foretell_agent
的同一批组件，保持单一事实来源——只有 create_deep_agent 的装配在此重写。
"""

from deepagents import create_deep_agent

from config.llm import get_chat_model
from foretell.backends import create_agent_backend
from foretell.middleware import reasoning_split_middleware
from foretell.prompts import build_system_prompt
from foretell.subagents import get_subagents
from foretell.tools import get_tools


def make_graph():
    """构建用于 LangGraph Studio 的 Foretell agent（不挂自带持久化）。"""
    return create_deep_agent(
        name="foretell",
        model=get_chat_model(),
        tools=get_tools(),
        system_prompt=build_system_prompt(),
        backend=create_agent_backend(),
        skills=["/skills/"],
        subagents=get_subagents(),
        middleware=[reasoning_split_middleware],
    )
