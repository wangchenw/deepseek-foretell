"""实体识别与场次定位 Tools。"""

from __future__ import annotations

from typing import Literal

from langchain.tools import tool

from foretell.tools.crazy_sports.client import get_crazy_sports_client
from foretell.tools.envelope import make_envelope
from foretell.tools.status_codes import PlayType, StatusCode

_META_SOURCE = "crazy_sports_db"


def _default_meta(client) -> dict:
    return {"source": _META_SOURCE, "freshness": client.freshness}


@tool
def resolve_match(
    home: str,
    away: str,
    date: str | None = None,
    series_game: int | None = None,
) -> str:
    """按主客队名称模糊查询比赛候选。

    Args:
        home: 主队名称（支持中文简称或全称）。
        away: 客队名称。
        date: 比赛日期，格式 YYYY-MM-DD（可选）。
        series_game: 系列赛场次编号，如 G7 传 7（可选）。
            返回多个候选时，结合日期、赛事、主客队和上下文自行选择正确 match_id。
    """
    client = get_crazy_sports_client()
    candidates = client.resolve_match(home, away, date=date, series_game=series_game)

    if not candidates:
        if series_game is not None:
            return make_envelope(
                StatusCode.NOT_APPLICABLE,
                "match_entity",
                {
                    "home": home,
                    "away": away,
                    "series_game": series_game,
                    "reason": f"未找到系列赛第{series_game}场，禁止降级分析其他场次",
                },
                meta=_default_meta(client),
            )
        return make_envelope(
            StatusCode.ENTITY_NOT_FOUND,
            "match_entity",
            {"home": home, "away": away, "date": date},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "match_entity",
        {
            "home": home,
            "away": away,
            "date": date,
            "candidates": candidates,
            "count": len(candidates),
            "match_status": candidates[0].get("status") if len(candidates) == 1 else "ambiguous",
            "match_time_beijing": candidates[0].get("match_time_beijing") if len(candidates) == 1 else None,
            "neutral": candidates[0].get("neutral") if len(candidates) == 1 else None,
            "round_group": candidates[0].get("round_group") if len(candidates) == 1 else None,
            "round_num": candidates[0].get("round_num") if len(candidates) == 1 else None,
        },
        match_id=candidates[0].get("match_id") if len(candidates) == 1 else None,
        meta=_default_meta(client),
    )


@tool
def resolve_lottery_match(
    play_type: Literal["101", "201", "301", "401", "402", "403", "404"],
    code: str,
    date: str | None = None,
) -> str:
    """按彩票玩法与场次编号定位比赛。

    Args:
        play_type: 玩法编码，101=竞彩足球、201=竞彩篮球、301=北单胜负、401=十四场/任九等。
        code: 场次编号，如「周二004」「周一305」。
        date: 开奖/销售日期 YYYY-MM-DD（可选）。
    """
    client = get_crazy_sports_client()
    pt = PlayType(play_type)
    result = client.resolve_lottery_match(pt, code, date=date)

    if result is None:
        return make_envelope(
            StatusCode.ENTITY_NOT_FOUND,
            "lottery_match_entity",
            {"play_type": play_type, "code": code, "date": date},
            meta=_default_meta(client),
        )

    match_id = result.get("match_id")
    return make_envelope(
        StatusCode.OK,
        "lottery_match_entity",
        result,
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def resolve_team(name: str) -> str:
    """按名称模糊查询球队候选。

    Args:
        name: 球队名称或常用简称，如「利物浦」「湖人」。
            返回多个候选时，结合 name/name_en/national/aliases 自行选择正确 team_id。
    """
    client = get_crazy_sports_client()
    candidates = client.resolve_team(name)

    if not candidates:
        return make_envelope(
            StatusCode.ENTITY_NOT_FOUND,
            "team_entity",
            {"name": name},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "team_entity",
        {"name": name, "candidates": candidates, "count": len(candidates)},
        meta=_default_meta(client),
    )


@tool
def resolve_league(name: str) -> str:
    """按名称模糊查询联赛候选。

    Args:
        name: 联赛名称或简称，如「欧冠」「NBA」「英超」。
            返回多个候选时，结合日期、国家、赛事语境自行选择正确 league_id。
    """
    client = get_crazy_sports_client()
    candidates = client.resolve_league(name)

    if not candidates:
        return make_envelope(
            StatusCode.ENTITY_NOT_FOUND,
            "league_entity",
            {"name": name},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "league_entity",
        {"name": name, "candidates": candidates, "count": len(candidates)},
        meta=_default_meta(client),
    )
