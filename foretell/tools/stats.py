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


def _basketball_unavailable(client, dimension: str, entity_id, table_name: str, id_field: str = "team_id") -> str:
    """篮球该维度暂未采集时返回明确的 DATA_MISSING(非含糊空结果)。"""
    return make_envelope(
        StatusCode.DATA_MISSING,
        dimension,
        {
            id_field: entity_id,
            "sport": "basketball",
            "reason": f"该维度篮球暂未采集({table_name} 表不存在)",
        },
        meta=_default_meta(client),
    )


@tool
def get_standings(league_id: int | str, season_id: int | str | None = None) -> str:
    """查询联赛/杯赛积分榜（赛制感知 + season 智能选择 + 欧战/升降级资格）。

    Args:
        league_id: MySQL football_competition.id，须先通过 resolve_league 获取。
        season_id: 赛季 ID（可选）。不传时自动取有数据的最大赛季（修复休赛期空榜）。
            查历史赛季时传指定 season_id。
    """
    client = get_crazy_sports_client()
    result = client.get_standings(league_id, season_id=season_id)

    rows = result.get("rows", [])
    if not rows:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "standings",
            {"league_id": league_id, "rows": [], "competition_type": result.get("competition_type")},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "standings",
        {
            "league_id": league_id,
            "rows": rows,
            "count": len(rows),
            "competition_type": result.get("competition_type"),
            "competition_type_name": result.get("competition_type_name"),
        },
        meta=_default_meta(client),
    )


@tool
def get_team_season_stats(team_id: int | str, sport: str = "football") -> str:
    """查询球队赛季统计（足球主客场拆分进失球等 / 篮球得分篮板助攻效率等）。

    Args:
        team_id: MySQL football_team.id 或 basketball_team.id。
        sport: "football"(默认)查 football_competition_teams_stats;
            "basketball" 查 basketball_competition_team_stats(得分/投篮准度/篮板/助攻抢断盖帽/效率)。
    """
    client = get_crazy_sports_client()
    result = client.get_team_season_stats(team_id, sport=sport)

    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "team_season_stats",
            {"team_id": team_id, "sport": sport},
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
    team_id: int | str,
    venue: Literal["home", "away"] | None = None,
    n: int = 5,
    sport: str = "football",
) -> str:
    """查询球队近期战绩。

    Args:
        team_id: MySQL football_team.id 或 basketball_team.id。
        venue: 主客场过滤，home 或 away（可选）。
        n: 返回场次数量，默认 5。
        sport: "football"(默认)或 "basketball"。篮球走 basketball_match 表。
    """
    client = get_crazy_sports_client()
    results = client.get_recent_form(team_id, venue=venue, n=n, sport=sport)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "recent_form",
            {"team_id": team_id, "venue": venue, "sport": sport, "matches": []},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "recent_form",
        {"team_id": team_id, "venue": venue, "sport": sport, "matches": results, "count": len(results)},
        meta=_default_meta(client),
    )


@tool
def get_h2h(team_a: int | str, team_b: int | str, n: int = 5, sport: str = "football") -> str:
    """查询两队历史交锋记录。

    Args:
        team_a: 球队 A 的 MySQL football_team.id 或 basketball_team.id。
        team_b: 球队 B 的 MySQL football_team.id 或 basketball_team.id。
        n: 返回场次数量，默认 5。
        sport: "football"(默认)或 "basketball"。篮球走 basketball_match 表。
    """
    client = get_crazy_sports_client()
    results = client.get_h2h(team_a, team_b, n=n, sport=sport)

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
