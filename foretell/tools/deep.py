"""深度数据 Tools：阵容、伤停、情报、射手榜、大名单、系列赛、篮球积分榜、直播、事件、技术统计。"""

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
def get_match_lineup(match_id: int | str) -> str:
    """查询比赛预计首发阵容。

    Args:
        match_id: MySQL football_match.id。
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
def get_injury_report(match_id: int | str) -> str:
    """查询比赛伤停与停赛报告。

    Args:
        match_id: MySQL football_match.id。
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
def get_intel_tags(match_id: int | str) -> str:
    """查询比赛情报标签（主场优势、核心复出、体能隐忧等）。

    Args:
        match_id: MySQL football_match.id。
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


@tool
def get_top_scorers(competition_id: int | str, limit: int = 20) -> str:
    """查询赛事当前赛季射手榜（进球数倒序）。

    Args:
        competition_id: MySQL football_competition.id，须先通过 resolve_league 获取。
        limit: 返回人数，默认 20。
    """
    client = get_crazy_sports_client()
    results = client.get_top_scorers(competition_id, limit=limit)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "top_scorers",
            {"competition_id": competition_id, "scorers": []},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "top_scorers",
        {"competition_id": competition_id, "scorers": results, "count": len(results)},
        meta=_default_meta(client),
    )


@tool
def get_team_squad(team_id: int | str) -> str:
    """查询球队大名单（含位置、球衣号、队长标识）。

    Args:
        team_id: MySQL football_team.id，须先通过 resolve_team 获取。
    """
    client = get_crazy_sports_client()
    results = client.get_team_squad(team_id)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "team_squad",
            {"team_id": team_id, "squad": []},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "team_squad",
        {"team_id": team_id, "squad": results, "count": len(results)},
        meta=_default_meta(client),
    )


@tool
def get_series_matchup(
    sport: Literal["football", "basketball"],
    team_id: int | str | None = None,
    limit: int = 20,
) -> str:
    """查询系列赛对阵（含 NBA 季后赛 G7、欧冠淘汰赛等多回合对阵）。

    Args:
        sport: football 或 basketball。
        team_id: 球队 id（可选），传入则只返回该队参与的系列赛。
        limit: 返回对阵数，默认 20。
    """
    client = get_crazy_sports_client()
    results = client.get_series_matchup(sport, team_id=team_id, limit=limit)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "series_matchup",
            {"sport": sport, "team_id": team_id, "matchups": []},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "series_matchup",
        {"sport": sport, "team_id": team_id, "matchups": results, "count": len(results)},
        meta=_default_meta(client),
    )


@tool
def get_basketball_standings(league_id: int | str) -> str:
    """查询篮球联赛当前赛季积分榜（胜负/胜率/胜场差/场均得失分/主客战绩）。

    Args:
        league_id: MySQL basketball_competition.id，须先通过 resolve_league 获取。
    """
    client = get_crazy_sports_client()
    results = client.get_basketball_standings(league_id)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "basketball_standings",
            {"league_id": league_id, "rows": []},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "basketball_standings",
        {"league_id": league_id, "rows": results, "count": len(results)},
        meta=_default_meta(client),
    )


@tool
def get_match_tlive(match_id: int | str, limit: int = 100) -> str:
    """查询比赛实时文字直播事件流（按时间排序）。

    Args:
        match_id: MySQL football_match.id，须先通过实体定位获取。
        limit: 返回事件数，默认 100。
    """
    client = get_crazy_sports_client()
    results = client.get_match_tlive(match_id, limit=limit)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "match_tlive",
            {"match_id": match_id, "events": []},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "match_tlive",
        {"match_id": match_id, "events": results, "count": len(results)},
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def get_match_incidents(match_id: int | str) -> str:
    """查询比赛关键事件（进球/红黄牌/换人/VAR，按时间排序）。

    Args:
        match_id: MySQL football_match.id，须先通过实体定位获取。
    """
    client = get_crazy_sports_client()
    results = client.get_match_incidents(match_id)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "match_incidents",
            {"match_id": match_id, "incidents": []},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "match_incidents",
        {"match_id": match_id, "incidents": results, "count": len(results)},
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def get_match_team_stats(match_id: int | str) -> str:
    """查询比赛球队技术统计（射门/传球/控球率/角球等，主客两队）。

    Args:
        match_id: MySQL football_match.id，须先通过实体定位获取。
    """
    client = get_crazy_sports_client()
    results = client.get_match_team_stats(match_id)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "match_team_stats",
            {"match_id": match_id, "stats": []},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "match_team_stats",
        {"match_id": match_id, "stats": results, "count": len(results)},
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def get_match_player_stats(match_id: int | str, limit: int = 30) -> str:
    """查询比赛球员技术统计（含评分，按评分倒序）。

    Args:
        match_id: MySQL football_match.id，须先通过实体定位获取。
        limit: 返回球员数，默认 30。
    """
    client = get_crazy_sports_client()
    results = client.get_match_player_stats(match_id, limit=limit)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "match_player_stats",
            {"match_id": match_id, "players": []},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "match_player_stats",
        {"match_id": match_id, "players": results, "count": len(results)},
        match_id=match_id,
        meta=_default_meta(client),
    )
