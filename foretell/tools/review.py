"""赛后复盘 Tools。"""

from __future__ import annotations

from langchain.tools import tool

from foretell.tools.crazy_sports.client import get_crazy_sports_client
from foretell.tools.envelope import make_envelope
from foretell.tools.status_codes import StatusCode

_META_SOURCE = "crazy_sports_db"


def _default_meta(client) -> dict:
    return {"source": _META_SOURCE, "freshness": client.freshness}


@tool
def get_match_result(match_id: int | str) -> str:
    """查询已完场比赛的赛果、技术统计与关键事件，用于赛后复盘。

    Args:
        match_id: MySQL football_match.id，须先通过实体定位获取；仅已完场比赛有数据。
    """
    client = get_crazy_sports_client()
    result = client.get_match_result(match_id)

    if result is None:
        match_info = client.get_match_by_id(match_id)
        if match_info and match_info.get("status") != "finished":
            return make_envelope(
                StatusCode.NOT_APPLICABLE,
                "match_result",
                {"match_id": match_id, "reason": "比赛尚未结束，无法提供完场复盘数据"},
                match_id=match_id,
                meta=_default_meta(client),
            )
        return make_envelope(
            StatusCode.DATA_MISSING,
            "match_result",
            {"match_id": match_id},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "match_result",
        result,
        match_id=match_id,
        meta=_default_meta(client),
    )
