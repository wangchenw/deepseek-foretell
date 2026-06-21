"""赛程 Tool 单元测试。"""

import json

from foretell.tools.entity import resolve_league, resolve_team
from foretell.tools.schedule import get_team_schedule


def _parse(result: str) -> dict:
    return json.loads(result)


def test_get_team_schedule_upcoming_with_league() -> None:
    team = _parse(resolve_team.invoke({"name": "葡萄牙"}))
    league = _parse(resolve_league.invoke({"name": "世界杯"}))
    result = _parse(
        get_team_schedule.invoke(
            {
                "team_id": team["data"]["team_id"],
                "league_id": league["data"]["league_id"],
                "direction": "upcoming",
                "limit": 1,
            }
        )
    )
    assert result["code"] == "OK"
    assert result["data"]["count"] == 1
    assert result["data"]["matches"][0]["match_id"] == "m_portugal_wc"
    assert result["data"]["matches"][0]["league_name"] == "世界杯"


def test_get_team_schedule_recent_finished() -> None:
    result = _parse(
        get_team_schedule.invoke({"team_id": "t_spurs", "direction": "recent", "limit": 2})
    )
    assert result["code"] == "OK"
    assert result["data"]["count"] >= 1
    assert all(m["status"] == "finished" for m in result["data"]["matches"])


def test_get_team_schedule_default_recent() -> None:
    result = _parse(get_team_schedule.invoke({"team_id": "t_spurs"}))
    assert result["code"] == "OK"
    assert result["data"]["direction"] == "recent"
