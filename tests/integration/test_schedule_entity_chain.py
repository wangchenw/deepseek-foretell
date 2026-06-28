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


def test_today_query_must_include_world_cup() -> None:
    """模拟「今天有什么比赛」：tier=top 路径必须返回 6 场世界杯，
    含哥伦比亚 vs 葡萄牙。回归 feedback #003–#006 假阴性。"""
    result = _parse(
        get_schedule_by_date.invoke({"date": "2026-06-28", "tier": "top"})
    )
    assert result["code"] == "OK"
    matches = result["data"]["matches"]
    wc = [m for m in matches if m["league_name"] == "世界杯"]
    assert len(wc) == 6
    assert any(
        "哥伦比亚" in m["home_name"] and "葡萄牙" in m["away_name"] for m in wc
    )


def test_today_default_mode_does_not_truncate_world_cup() -> None:
    """默认模式（无 tier/league_preset）在大赛日不能把世界杯截断掉。"""
    result = _parse(get_schedule_by_date.invoke({"date": "2026-06-28"}))
    assert result["code"] == "OK"
    assert result["meta"]["truncated"] is True
    wc = [m for m in result["data"]["matches"] if m["league_name"] == "世界杯"]
    assert len(wc) == 6
