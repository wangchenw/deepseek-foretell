"""实体链赛程集成测试。"""

import json

from foretell.tools.entity import resolve_league, resolve_team
from foretell.tools.schedule import get_schedule_by_date, get_team_schedule


def _parse(result: str) -> dict:
    return json.loads(result)


def test_portugal_world_cup_upcoming_tool_chain() -> None:
    team = _parse(resolve_team.invoke({"name": "葡萄牙"}))
    assert team["code"] == "OK"
    assert team["data"]["team_id"] == "t_portugal_nt"

    league = _parse(resolve_league.invoke({"name": "世界杯"}))
    assert league["code"] == "OK"
    assert league["data"]["league_id"] == "l_world_cup"

    schedule = _parse(
        get_team_schedule.invoke(
            {
                "team_id": team["data"]["team_id"],
                "league_id": league["data"]["league_id"],
                "direction": "upcoming",
                "limit": 1,
            }
        )
    )
    assert schedule["code"] == "OK"
    match = schedule["data"]["matches"][0]
    assert match["match_id"] == "m_portugal_wc"
    assert match["league_name"] == "世界杯"


def test_liverpool_schedule_direct_tool_chain() -> None:
    """简单单队赛程：主路径两步 Tool，无需 subagent。"""
    team = _parse(resolve_team.invoke({"name": "利物浦"}))
    assert team["data"]["team_id"] == "t_liverpool"

    schedule = _parse(
        get_team_schedule.invoke(
            {"team_id": team["data"]["team_id"], "direction": "upcoming", "limit": 1}
        )
    )
    assert schedule["code"] == "OK"
    assert schedule["data"]["count"] == 1


def test_nba_schedule_by_date_direct() -> None:
    result = _parse(get_schedule_by_date.invoke({"date": "2026-06-21", "sport": "basketball"}))
    assert result["code"] == "OK"
    assert result["data"]["count"] >= 1
    assert all(m["sport"] == "basketball" for m in result["data"]["matches"])
