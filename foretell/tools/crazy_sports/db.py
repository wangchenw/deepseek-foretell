"""MySQL 连接上下文。"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor

from config.settings import get_settings


@contextmanager
def mysql_connection() -> Iterator[DictCursor]:
    settings = get_settings()
    conn = pymysql.connect(**settings.mysql_connection_kwargs(), cursorclass=DictCursor)
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    finally:
        conn.close()
