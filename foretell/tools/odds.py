"""盘口维度 Tools。"""

from __future__ import annotations

from langchain.tools import tool

from foretell.tools.crazy_sports.client import get_crazy_sports_client
from foretell.tools.envelope import make_envelope
from foretell.tools.status_codes import StatusCode

_META_SOURCE = "crazy_sports_db"


def _default_meta(client) -> dict:
    return {"source": _META_SOURCE, "freshness": client.freshness}


def _odds_missing(snapshot: dict | None) -> bool:
    if snapshot is None:
        return True
    has_european = "european" in snapshot or "moneyline" in snapshot
    has_asian = "asian" in snapshot or "spread" in snapshot
    return not has_european and not has_asian


@tool
def get_odds_snapshot(match_id: str) -> str:
    """查询比赛盘口快照（欧赔、亚盘/让分、大小球/大小分）。

    Args:
        match_id: 比赛 ID，须先通过实体定位获取。
    """
    client = get_crazy_sports_client()
    result = client.get_odds_snapshot(match_id)

    if _odds_missing(result):
        return make_envelope(
            StatusCode.SKIP_MATCH,
            "odds_snapshot",
            {"match_id": match_id, "reason": "欧赔与亚盘均缺失"},
            match_id=match_id,
            meta=_default_meta(client),
        )

    code = StatusCode.OK
    if result is not None:
        has_european = "european" in result or "moneyline" in result
        has_asian = "asian" in result or "spread" in result
        if not (has_european and has_asian):
            code = StatusCode.PARTIAL

    return make_envelope(
        code,
        "odds_snapshot",
        result,
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def get_odds_trend(match_id: str) -> str:
    """查询赔率走势（初盘到即时盘变动）。

    Args:
        match_id: 比赛 ID。
    """
    client = get_crazy_sports_client()
    results = client.get_odds_trend(match_id)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "odds_trend",
            {"match_id": match_id, "points": []},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "odds_trend",
        {"match_id": match_id, "points": results, "count": len(results)},
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def get_same_odds_history(match_id: str) -> str:
    """查询同赔历史赛果。

    Args:
        match_id: 比赛 ID。
    """
    client = get_crazy_sports_client()
    results = client.get_same_odds_history(match_id)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "same_odds_history",
            {"match_id": match_id, "entries": []},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "same_odds_history",
        {"match_id": match_id, "entries": results, "count": len(results)},
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def get_kelly(match_id: str) -> str:
    """查询凯利指数。

    Args:
        match_id: 比赛 ID。
    """
    client = get_crazy_sports_client()
    result = client.get_kelly(match_id)

    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "kelly",
            {"match_id": match_id},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "kelly",
        result,
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def get_betfair(match_id: str) -> str:
    """查询必发成交数据。

    Args:
        match_id: 比赛 ID。
    """
    client = get_crazy_sports_client()
    result = client.get_betfair(match_id)

    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "betfair",
            {"match_id": match_id},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "betfair",
        result,
        match_id=match_id,
        meta=_default_meta(client),
    )
