"""实体链赛程集成测试。"""

import json

from foretell.tools.entity import resolve_team
from foretell.tools.schedule import get_schedule_by_date, get_team_schedule


def _parse(result: str) -> dict:
    return json.loads(result)


def _first_team_id(result: dict) -> int:
    return result["data"]["candidates"][0]["team_id"]


def _national_team_id(result: dict) -> int:
    return next(team["team_id"] for team in result["data"]["candidates"] if team["national"] == 1)


def test_portugal_schedule_direct_tool_chain() -> None:
    team = _parse(resolve_team.invoke({"name": "葡萄牙"}))
    assert team["code"] == "OK"
    team_id = _national_team_id(team)
    assert isinstance(team_id, int)

    schedule = _parse(
        get_team_schedule.invoke(
            {"team_id": team_id, "direction": "all", "limit": 1}
        )
    )
    assert schedule["code"] == "OK"
    assert schedule["data"]["count"] == 1
    assert isinstance(schedule["data"]["matches"][0]["match_id"], int)


def test_liverpool_schedule_direct_tool_chain() -> None:
    """简单单队赛程：主路径两步 Tool，无需 subagent。"""
    team = _parse(resolve_team.invoke({"name": "利物浦"}))
    team_id = _first_team_id(team)
    assert isinstance(team_id, int)

    schedule = _parse(
        get_team_schedule.invoke(
            {"team_id": team_id, "direction": "upcoming", "limit": 1}
        )
    )
    assert schedule["code"] == "OK"
    assert schedule["data"]["count"] == 1


def test_football_schedule_by_date_direct() -> None:
    result = _parse(get_schedule_by_date.invoke({"date": "2026-04-29", "sport": "football"}))
    assert result["code"] == "OK"
    assert result["data"]["count"] >= 1
    assert all(m["sport"] == "football" for m in result["data"]["matches"])
