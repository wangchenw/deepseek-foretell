"""统计维度 Tools。"""

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
def get_standings(league_id: str) -> str:
    """查询联赛积分榜。

    Args:
        league_id: 联赛 ID，须先通过 resolve_league 获取。
    """
    client = get_crazy_sports_client()
    results = client.get_standings(league_id)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "standings",
            {"league_id": league_id, "rows": []},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "standings",
        {"league_id": league_id, "rows": results, "count": len(results)},
        meta=_default_meta(client),
    )


@tool
def get_team_season_stats(team_id: str) -> str:
    """查询球队赛季统计（主客场拆分、进失球等）。

    Args:
        team_id: 球队 ID，须先通过 resolve_team 获取。
    """
    client = get_crazy_sports_client()
    result = client.get_team_season_stats(team_id)

    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "team_season_stats",
            {"team_id": team_id},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "team_season_stats",
        result,
        meta=_default_meta(client),
    )


@tool
def get_recent_form(
    team_id: str,
    venue: Literal["home", "away"] | None = None,
    n: int = 5,
) -> str:
    """查询球队近期战绩。

    Args:
        team_id: 球队 ID，须先通过 resolve_team 获取。
        venue: 主客场过滤，home 或 away（可选）。
        n: 返回场次数量，默认 5。
    """
    client = get_crazy_sports_client()
    results = client.get_recent_form(team_id, venue=venue, n=n)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "recent_form",
            {"team_id": team_id, "venue": venue, "matches": []},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "recent_form",
        {"team_id": team_id, "venue": venue, "matches": results, "count": len(results)},
        meta=_default_meta(client),
    )


@tool
def get_h2h(team_a: str, team_b: str, n: int = 5) -> str:
    """查询两队历史交锋记录。

    Args:
        team_a: 球队 A 的 team_id。
        team_b: 球队 B 的 team_id。
        n: 返回场次数量，默认 5。
    """
    client = get_crazy_sports_client()
    results = client.get_h2h(team_a, team_b, n=n)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "h2h",
            {"team_a": team_a, "team_b": team_b, "matches": []},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "h2h",
        {"team_a": team_a, "team_b": team_b, "matches": results, "count": len(results)},
        meta=_default_meta(client),
    )
