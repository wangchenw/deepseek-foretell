"""MySQL 连接上下文。

D0 加固:Queue 连接池(大小 3)+ 借出 ping 检查 + 失败重试,根治 agent 多工具链触发 DB 服务端连接限流,
并避免单连接复用时的"Packet sequence number wrong"(嵌套 with mysql_connection 时多 cursor 共用连接)。
"""

from __future__ import annotations

import queue
import time
from collections.abc import Iterator
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor
from pymysql.err import OperationalError

from config.settings import get_settings

# 连接池(大小 3:支持嵌套 with mysql_connection 各借独立连接)
_POOL: queue.Queue[pymysql.Connection | None] = queue.Queue(maxsize=3)
_POOL_SIZE = 3
_RETRY_ATTEMPTS = 3
_RETRY_INTERVAL = 1.0


def _new_conn() -> pymysql.Connection:
    """新建连接(失败重试)。"""
    last_exc: Exception | None = None
    for attempt in range(_RETRY_ATTEMPTS):
        try:
            settings = get_settings()
            return pymysql.connect(
                **settings.mysql_connection_kwargs(), cursorclass=DictCursor
            )
        except OperationalError as exc:
            last_exc = exc
            if attempt < _RETRY_ATTEMPTS - 1:
                time.sleep(_RETRY_INTERVAL)
    assert last_exc is not None
    raise last_exc


def _borrow() -> pymysql.Connection:
    """从池借连接;池空则新建;借出后 ping 检查,失败则重建。"""
    try:
        conn = _POOL.get_nowait()
    except queue.Empty:
        return _new_conn()
    # ping 检查(失败则丢弃,新建)
    try:
        conn.ping()
        return conn
    except OperationalError:
        try:
            conn.close()
        except Exception:
            pass
        return _new_conn()


def _return(conn: pymysql.Connection) -> None:
    """归还连接到池;池满则关闭。"""
    try:
        _POOL.put_nowait(conn)
    except queue.Full:
        try:
            conn.close()
        except Exception:
            pass


@contextmanager
def mysql_connection() -> Iterator[DictCursor]:
    """从池借连接,上下文结束归还(commit/rollback)。"""
    conn = _borrow()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
        _return(conn)
    except Exception:
        try:
            conn.rollback()
        except OperationalError:
            pass
        # 异常连接不归还(可能脏),关闭丢弃
        try:
            conn.close()
        except Exception:
            pass
        raise
