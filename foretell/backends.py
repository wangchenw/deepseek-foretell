from __future__ import annotations

from typing import TYPE_CHECKING, Any

from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from config.settings import FORETELL_SKILLS_DIR, get_settings

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.store.base import BaseStore

_postgres_pool: ConnectionPool | None = None
_postgres_checkpointer: BaseCheckpointSaver | None = None
_postgres_store: BaseStore | None = None


def get_postgres_pool(database_url: str) -> ConnectionPool:
    global _postgres_pool
    if _postgres_pool is None:
        _postgres_pool = ConnectionPool(
            conninfo=database_url,
            min_size=1,
            max_size=10,
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
                "row_factory": dict_row,
            },
        )
    return _postgres_pool


def create_checkpointer(deploy_env: str | None = None) -> BaseCheckpointSaver:
    """按部署环境创建 Checkpointer：dev 用 MemorySaver，prod 用 PostgresSaver。"""
    global _postgres_checkpointer

    env = (deploy_env or get_settings().deploy_env).lower()
    if env == "dev":
        return MemorySaver()

    if env == "prod":
        settings = get_settings()
        if not settings.database_url:
            raise ValueError("生产环境需要设置 DATABASE_URL")

        if _postgres_checkpointer is not None:
            return _postgres_checkpointer

        try:
            from langgraph.checkpoint.postgres import PostgresSaver
        except ImportError as exc:
            raise ImportError("生产 Checkpointer 需要安装 langgraph-checkpoint-postgres") from exc

        checkpointer = PostgresSaver(get_postgres_pool(settings.database_url))
        checkpointer.setup()
        _postgres_checkpointer = checkpointer
        return checkpointer

    raise ValueError(f"未知 DEPLOY_ENV: {env!r}")


def create_store(deploy_env: str | None = None) -> BaseStore | None:
    """按部署环境创建 Store：dev 用 InMemoryStore，prod 用 PostgresStore。"""
    global _postgres_store

    env = (deploy_env or get_settings().deploy_env).lower()
    if env == "dev":
        return InMemoryStore()

    if env == "prod":
        settings = get_settings()
        if not settings.database_url:
            raise ValueError("生产环境需要设置 DATABASE_URL")

        if _postgres_store is not None:
            return _postgres_store

        try:
            from langgraph.store.postgres import PostgresStore
        except ImportError as exc:
            raise ImportError(
                "生产 Store 需要安装 langgraph-checkpoint-postgres（PostgresStore 随该包提供）"
            ) from exc

        store = PostgresStore(get_postgres_pool(settings.database_url))
        store.setup()
        _postgres_store = store
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
