"""赛事元数据 Tools：赛季、教练、裁判、场馆、半全场统计、进失球概率。"""

from __future__ import annotations

from typing import Literal

from langchain.tools import tool

from foretell.tools.crazy_sports.client import get_crazy_sports_client
from foretell.tools.envelope import make_envelope
from foretell.tools.status_codes import StatusCode

_META_SOURCE = "crazy_sports_db"


def _default_meta(client) -> dict:
    return {"source": _META_SOURCE, "freshness": client.freshness}


@tool
def resolve_basketball_league(name: str) -> str:
    """模糊解析篮球赛事名称，返回候选 league_id 列表。

    Args:
        name: 赛事名称（中文/英文/简称均可）。
    """
    client = get_crazy_sports_client()
    result = client.resolve_basketball_league(name)
    if not result:
        return make_envelope(
            StatusCode.ENTITY_NOT_FOUND, "basketball_league", {"query": name},
            meta=_default_meta(client),
        )
    return make_envelope(
        StatusCode.OK, "basketball_league", {"candidates": result, "count": len(result), "query": name},
        meta=_default_meta(client),
    )


@tool
def get_seasons(competition_id: int | str, sport: Literal["football", "basketball"] = "football") -> str:
    """查询赛事的赛季列表（按最新优先，标注 is_current）。

    Args:
        competition_id: MySQL football_competition.id / basketball_competition.id。
        sport: 足球或篮球，默认足球。
    """
    client = get_crazy_sports_client()
    result = client.get_seasons(competition_id, sport)
    if not result:
        return make_envelope(
            StatusCode.DATA_MISSING, "seasons",
            {"competition_id": competition_id, "sport": sport},
            meta=_default_meta(client),
        )
    return make_envelope(
        StatusCode.OK, "seasons", {"seasons": result, "count": len(result), "sport": sport},
        meta=_default_meta(client),
    )


@tool
def get_coach(coach_id: int | str, sport: Literal["football", "basketball"] = "football") -> str:
    """查询教练资料（含国籍、阵型偏好、合同）。

    Args:
        coach_id: MySQL football_coach.id / basketball_coach.id。
        sport: 足球或篮球，默认足球。
    """
    client = get_crazy_sports_client()
    result = client.get_coach(coach_id, sport)
    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING, "coach", {"coach_id": coach_id, "sport": sport},
            meta=_default_meta(client),
        )
    return make_envelope(
        StatusCode.OK, "coach", {"profile": result, "sport": sport},
        meta=_default_meta(client),
    )


@tool
def get_referee(referee_id: int | str) -> str:
    """查询裁判资料（含国籍、年龄）。

    Args:
        referee_id: MySQL football_referee.id。
    """
    client = get_crazy_sports_client()
    result = client.get_referee(referee_id)
    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING, "referee", {"referee_id": referee_id},
            meta=_default_meta(client),
        )
    return make_envelope(
        StatusCode.OK, "referee", {"profile": result},
        meta=_default_meta(client),
    )


@tool
def get_venue(venue_id: int | str, sport: Literal["football", "basketball"] = "football") -> str:
    """查询场馆资料（含容量、城市、草坪类型）。

    Args:
        venue_id: MySQL football_venue.id / basketball_venue.id。
        sport: 足球或篮球，默认足球。
    """
    client = get_crazy_sports_client()
    result = client.get_venue(venue_id, sport)
    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING, "venue", {"venue_id": venue_id, "sport": sport},
            meta=_default_meta(client),
        )
    return make_envelope(
        StatusCode.OK, "venue", {"profile": result, "sport": sport},
        meta=_default_meta(client),
    )


@tool
def get_match_half_stats(
    match_id: int | str,
    scope: Literal["ft", "p1", "p2", "o1", "o2"] = "ft",
) -> str:
    """查询比赛半全场统计（按 scope 区分全场/上下半场/加时）。

    scope 含义：ft=全场、p1=上半场、p2=下半场、o1=加时上半场、o2=加时下半场。

    Args:
        match_id: MySQL football_match.id。
        scope: 统计范围，默认 ft（全场）。
    """
    client = get_crazy_sports_client()
    result = client.get_match_half_stats(match_id, scope)
    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING, "match_half_stats",
            {"match_id": match_id, "scope": scope},
            match_id=match_id, meta=_default_meta(client),
        )
    return make_envelope(
        StatusCode.OK, "match_half_stats", {"stats": result, "scope": scope},
        match_id=match_id, meta=_default_meta(client),
    )


@tool
def get_goals_lost_rate(match_id: int | str) -> str:
    """查询比赛进失球概率（主队/客队进失球分布）。

    Args:
        match_id: MySQL football_match.id。
    """
    client = get_crazy_sports_client()
    result = client.get_goals_lost_rate(match_id)
    if not result:
        return make_envelope(
            StatusCode.DATA_MISSING, "goals_lost_rate", {"match_id": match_id},
            match_id=match_id, meta=_default_meta(client),
        )
    return make_envelope(
        StatusCode.OK, "goals_lost_rate", {"rates": result, "count": len(result)},
        match_id=match_id, meta=_default_meta(client),
    )
