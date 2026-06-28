"""PostgreSQL conversation audit log for compliance and complaint review."""

from __future__ import annotations

import logging
from typing import Literal

from config.settings import get_settings
from foretell.backends import get_postgres_pool

logger = logging.getLogger(__name__)

ConversationStatus = Literal["ok", "error", "empty_reply"]

_TABLE_READY = False

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS foretell_conversation_turns (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    user_message TEXT NOT NULL,
    assistant_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    stream BOOLEAN NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    latency_ms INTEGER
)
"""

_CREATE_INDEXES_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_fct_user_created ON foretell_conversation_turns (user_id, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_fct_thread_id ON foretell_conversation_turns (thread_id)",
)

_INSERT_SQL = """
INSERT INTO foretell_conversation_turns (
    user_id,
    thread_id,
    user_message,
    assistant_message,
    stream,
    status,
    error_message,
    latency_ms
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""


def setup_conversation_log_table() -> None:
    """Create audit table and indexes if they do not exist."""
    global _TABLE_READY
    if _TABLE_READY:
        return

    settings = get_settings()
    if not settings.conversation_log_enabled or not settings.database_url:
        return

    pool = get_postgres_pool(settings.database_url)
    with pool.connection() as conn:
        conn.execute(_CREATE_TABLE_SQL)
        for sql in _CREATE_INDEXES_SQL:
            conn.execute(sql)

    _TABLE_READY = True


def log_conversation_turn(
    *,
    user_id: str,
    thread_id: str,
    user_message: str,
    assistant_message: str | None,
    stream: bool,
    status: ConversationStatus,
    error_message: str | None = None,
    latency_ms: int | None = None,
) -> None:
    """Best-effort append of one user-visible Q&A turn for audit purposes."""
    settings = get_settings()
    if not settings.conversation_log_enabled or not settings.database_url:
        return

    try:
        setup_conversation_log_table()
        pool = get_postgres_pool(settings.database_url)
        with pool.connection() as conn:
            conn.execute(
                _INSERT_SQL,
                (
                    user_id,
                    thread_id,
                    user_message,
                    assistant_message,
                    stream,
                    status,
                    error_message,
                    latency_ms,
                ),
            )
    except Exception:
        logger.exception(
            "Failed to log conversation turn (user_id=%r, thread_id=%r)",
            user_id,
            thread_id,
        )
