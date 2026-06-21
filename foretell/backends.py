from __future__ import annotations

from typing import TYPE_CHECKING, Any

from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from config.settings import FORETELL_SKILLS_DIR, get_settings

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.store.base import BaseStore


def create_checkpointer(deploy_env: str | None = None) -> BaseCheckpointSaver:
    """按部署环境创建 Checkpointer：dev 用 MemorySaver，prod 用 PostgresSaver。"""
    env = (deploy_env or get_settings().deploy_env).lower()
    if env == "dev":
        return MemorySaver()

    if env == "prod":
        settings = get_settings()
        if not settings.database_url:
            raise ValueError("生产环境需要设置 DATABASE_URL")

        try:
            from langgraph.checkpoint.postgres import PostgresSaver
        except ImportError as exc:
            raise ImportError(
                "生产 Checkpointer 需要安装 langgraph-checkpoint-postgres"
            ) from exc

        checkpointer = PostgresSaver.from_conn_string(settings.database_url)
        if hasattr(checkpointer, "setup"):
            checkpointer.setup()
        return checkpointer

    raise ValueError(f"未知 DEPLOY_ENV: {env!r}")


def create_store(deploy_env: str | None = None) -> BaseStore | None:
    """按部署环境创建 Store：dev 用 InMemoryStore，prod 用 PostgresStore。"""
    env = (deploy_env or get_settings().deploy_env).lower()
    if env == "dev":
        return InMemoryStore()

    if env == "prod":
        settings = get_settings()
        if not settings.database_url:
            raise ValueError("生产环境需要设置 DATABASE_URL")

        try:
            from langgraph.store.postgres import PostgresStore
        except ImportError as exc:
            raise ImportError(
                "生产 Store 需要安装 langgraph-store-postgres"
            ) from exc

        store = PostgresStore.from_conn_string(settings.database_url)
        if hasattr(store, "setup"):
            store.setup()
        return store

    raise ValueError(f"未知 DEPLOY_ENV: {env!r}")


def create_agent_backend(runtime: Any = None):
    """创建 Agent Harness Backend：State 默认层 + 只读 Skills 路由。"""
    return CompositeBackend(
        default=StateBackend(),
        routes={
            "/skills/": FilesystemBackend(
                root_dir=str(FORETELL_SKILLS_DIR),
                virtual_mode=True,
            ),
        },
    )
