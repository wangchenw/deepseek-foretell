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

    业务规则:
        - 每行 row 含 promotion_id(资格分组 ID,JOIN football_promotions 得 promotion_name):
            正值表示该名次对应升级/欧战/保级等资格分组。
        - played=已赛场次(=DB total);won/draw/loss=胜平负场;goals/goals_against=进失球;
            goal_diff=净胜球;points=积分(已扣 deduct_points)。
        - 争冠悬念判断:lead=榜首 points - 第二名 points;remaining_rounds=总轮数 - 榜首 played。
            足球锁定公式:lead > remaining_rounds × 3(剩余全胜也追不上)。
        - competition_type: 1=league(单表积分榜)/2=cup(多组+淘汰赛)/3=friendly。
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


@tool
def get_standings_full(
    league_id: int | str,
    season_id: int | str | None = None,
    sport: str = "football",
) -> str:
    """H 类争冠/降级/保级悬念一站式聚合:积分榜 + 资格规则 + 剩余轮次 + 榜首领先分差。

    一次调用拿到判断悬念所需的全部输入:standings(含 promotion_id 资格分组)、
    promotions(资格规则字典)、remaining_rounds(剩余轮次)、lead(榜首领先分差)。
    避免多次调用 get_standings + get_promotions + 心算剩余轮次导致幻觉。

    Args:
        league_id: MySQL football_competition.id 或 basketball_competition.id。
        season_id: 赛季 ID(可选,不传自动取有数据的最大赛季)。
        sport: "football"(默认)或 "basketball"。

    Returns:
        envelope dimension="standings_full",data={standings, promotions, season_id,
        competition_type},meta={lead, played, remaining_rounds, total_rounds, source}。

    争冠锁定判定(足球): lead > remaining_rounds * 3 → 数学锁定(剩余全胜也追不上榜首)。
    复杂并列/净胜球相互战绩判定走 execute_code 沙箱算。
    """
    client = get_crazy_sports_client()
    standings_result = client.get_standings(league_id, season_id=season_id)
    rows = standings_result.get("rows", [])
    if not rows:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "standings_full",
            {"league_id": league_id, "sport": sport, "standings": [], "promotions": []},
            meta=_default_meta(client),
        )

    promotions = client.get_promotions(sport)

    # 推断 season_id(用于算 remaining_rounds):取榜首行的 season 不可得,用 standings_result 无 season;
    # 若用户未传 season_id,从 standings 智能选择的 season 推断需额外查询,这里用榜首 played 反推。
    # remaining_rounds 需 season_id;若未传则尝试用榜首 played + stage round_count。
    rr = client._compute_remaining_rounds(
        int(league_id),
        int(season_id) if season_id is not None else None,
        sport=sport,
    )
    played = rr.get("played") or rows[0].get("played") or 0
    lead = None
    if len(rows) >= 2:
        lead = (rows[0].get("points") or 0) - (rows[1].get("points") or 0)

    return make_envelope(
        StatusCode.OK,
        "standings_full",
        {
            "league_id": league_id,
            "sport": sport,
            "standings": rows,
            "promotions": promotions,
            "competition_type": standings_result.get("competition_type"),
            "competition_type_name": standings_result.get("competition_type_name"),
        },
        meta={
            **_default_meta(client),
            "lead": lead,
            "played": played,
            "remaining_rounds": rr.get("remaining_rounds"),
            "total_rounds": rr.get("total_rounds"),
            "remaining_source": rr.get("source"),
        },
    )
