"""Unit tests for PostgreSQL conversation audit log."""

from __future__ import annotations

from unittest.mock import MagicMock

import foretell.conversation_log as conversation_log
from foretell.conversation_log import log_conversation_turn, setup_conversation_log_table


def test_log_conversation_turn_skipped_in_dev(dev_env) -> None:
    pool = MagicMock()
    conversation_log._TABLE_READY = False

    log_conversation_turn(
        user_id="user-1",
        thread_id="user-1:abc12345",
        user_message="hello",
        assistant_message="hi",
        stream=False,
        status="ok",
        latency_ms=10,
    )

    pool.connection.assert_not_called()


def test_log_conversation_turn_inserts_in_prod(prod_env, monkeypatch) -> None:
    conversation_log._TABLE_READY = False
    conn = MagicMock()
    pool = MagicMock()
    pool.connection.return_value.__enter__ = MagicMock(return_value=conn)
    pool.connection.return_value.__exit__ = MagicMock(return_value=False)
    monkeypatch.setattr(conversation_log, "get_postgres_pool", lambda _url: pool)

    log_conversation_turn(
        user_id="user-1",
        thread_id="user-1:abc12345",
        user_message="分析巴黎 VS 拜仁",
        assistant_message="最终回答",
        stream=True,
        status="ok",
        latency_ms=321,
    )

    conn.execute.assert_any_call(conversation_log._CREATE_TABLE_SQL)
    insert_call = conn.execute.call_args_list[-1]
    assert insert_call[0][1] == (
        "user-1",
        "user-1:abc12345",
        "分析巴黎 VS 拜仁",
        "最终回答",
        True,
        "ok",
        None,
        321,
    )


def test_log_conversation_turn_setup_runs_once(prod_env, monkeypatch) -> None:
    conversation_log._TABLE_READY = False
    conn = MagicMock()
    pool = MagicMock()
    pool.connection.return_value.__enter__ = MagicMock(return_value=conn)
    pool.connection.return_value.__exit__ = MagicMock(return_value=False)
    monkeypatch.setattr(conversation_log, "get_postgres_pool", lambda _url: pool)

    log_conversation_turn(
        user_id="user-1",
        thread_id="user-1:abc12345",
        user_message="q1",
        assistant_message="a1",
        stream=False,
        status="ok",
    )
    log_conversation_turn(
        user_id="user-1",
        thread_id="user-1:abc12345",
        user_message="q2",
        assistant_message="a2",
        stream=False,
        status="ok",
    )

    create_calls = [call for call in conn.execute.call_args_list if call[0][0] == conversation_log._CREATE_TABLE_SQL]
    assert len(create_calls) == 1


def test_log_conversation_turn_swallows_db_errors(prod_env, monkeypatch) -> None:
    conversation_log._TABLE_READY = True
    pool = MagicMock()
    pool.connection.side_effect = RuntimeError("db down")
    monkeypatch.setattr(conversation_log, "get_postgres_pool", lambda _url: pool)

    log_conversation_turn(
        user_id="user-1",
        thread_id="user-1:abc12345",
        user_message="hello",
        assistant_message="hi",
        stream=False,
        status="ok",
    )


def test_setup_conversation_log_table_is_noop_when_disabled(dev_env) -> None:
    conversation_log._TABLE_READY = False
    setup_conversation_log_table()
    assert conversation_log._TABLE_READY is False
