"""深度情报 Tools（阵容、伤停、标签）。"""

from __future__ import annotations

from langchain.tools import tool

from foretell.tools.crazy_sports.client import get_crazy_sports_client
from foretell.tools.envelope import make_envelope
from foretell.tools.status_codes import StatusCode

_META_SOURCE = "crazy_sports_db"


def _default_meta(client) -> dict:
    return {"source": _META_SOURCE, "freshness": client.freshness}


@tool
def get_match_lineup(match_id: str) -> str:
    """查询比赛预计首发阵容。

    Args:
        match_id: 比赛 ID。
    """
    client = get_crazy_sports_client()
    result = client.get_match_lineup(match_id)

    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "match_lineup",
            {"match_id": match_id},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "match_lineup",
        result,
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def get_injury_report(match_id: str) -> str:
    """查询比赛伤停与停赛报告。

    Args:
        match_id: 比赛 ID。
    """
    client = get_crazy_sports_client()
    result = client.get_injury_report(match_id)

    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "injury_report",
            {"match_id": match_id},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "injury_report",
        result,
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def get_intel_tags(match_id: str) -> str:
    """查询比赛情报标签（主场优势、核心复出、体能隐忧等）。

    Args:
        match_id: 比赛 ID。
    """
    client = get_crazy_sports_client()
    results = client.get_intel_tags(match_id)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "intel_tags",
            {"match_id": match_id, "tags": []},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "intel_tags",
        {"match_id": match_id, "tags": results, "count": len(results)},
        match_id=match_id,
        meta=_default_meta(client),
    )
