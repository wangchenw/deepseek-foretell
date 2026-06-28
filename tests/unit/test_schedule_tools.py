"""赛程 Tool 单元测试。"""

import json

from foretell.tools.entity import resolve_team
from foretell.tools.schedule import get_schedule_by_date, get_team_schedule


def _parse(result: str) -> dict:
    return json.loads(result)


def _first_team_id(result: dict) -> int:
    return result["data"]["candidates"][0]["team_id"]


def test_get_team_schedule_all() -> None:
    team = _parse(resolve_team.invoke({"name": "利物浦"}))
    result = _parse(
        get_team_schedule.invoke(
            {
                "team_id": _first_team_id(team),
                "direction": "all",
                "limit": 1,
            }
        )
    )
    assert result["code"] == "OK"
    assert result["data"]["count"] == 1
    assert isinstance(result["data"]["matches"][0]["match_id"], int)


def test_get_team_schedule_recent_finished() -> None:
    result = _parse(
        get_team_schedule.invoke({"team_id": 10249, "direction": "recent", "limit": 2})
    )
    assert result["code"] == "OK"
    assert result["data"]["direction"] == "recent"
    assert result["data"]["count"] >= 1
    assert all(isinstance(m["match_id"], int) for m in result["data"]["matches"])


def test_get_team_schedule_default_recent() -> None:
    result = _parse(get_team_schedule.invoke({"team_id": 10249}))
    assert result["code"] == "OK"
    assert result["data"]["direction"] == "recent"


def test_get_schedule_by_date_league_preset() -> None:
    result = _parse(
        get_schedule_by_date.invoke({"date": "2026-04-29", "league_preset": "欧冠"})
    )
    assert result["code"] == "OK"
    assert result["data"]["league_preset"] == "欧冠"
    assert result["meta"]["limit"] == 100
    assert result["meta"]["truncated"] is False
    assert all("欧冠" in match["league_name"] for match in result["data"]["matches"])


def test_get_schedule_by_date_basketball() -> None:
    result = _parse(
        get_schedule_by_date.invoke(
            {"date": "2025-07-28", "sport": "basketball", "league_preset": "NBA"}
        )
    )
    assert result["code"] == "OK"
    assert result["data"]["count"] >= 1
    assert all(match["sport"] == "basketball" for match in result["data"]["matches"])
    assert all(match["league_name"] for match in result["data"]["matches"])


def test_get_schedule_by_date_merges_football_and_basketball() -> None:
    result = _parse(get_schedule_by_date.invoke({"date": "2025-07-28"}))
    assert result["code"] == "OK"
    sports = {match["sport"] for match in result["data"]["matches"]}
    assert "football" in sports
    assert "basketball" in sports


def test_get_schedule_by_date_tier_top_returns_world_cup() -> None:
    """6/28 tier=top 必须含 6 场世界杯（competition_id=1），且 meta.tier_count>=6。"""
    result = _parse(
        get_schedule_by_date.invoke({"date": "2026-06-28", "tier": "top"})
    )
    assert result["code"] == "OK"
    matches = result["data"]["matches"]
    wc = [m for m in matches if m["league_name"] == "世界杯"]
    assert len(wc) == 6
    assert result["meta"]["tier_count"] >= 6
    assert result["meta"]["truncated"] is False
    # 哥伦比亚 vs 葡萄牙 必须在结果中
    assert any(
        "哥伦比亚" in m["home_name"] and "葡萄牙" in m["away_name"] for m in wc
    )


def test_get_schedule_by_date_default_prioritizes_top_tier() -> None:
    """6/28 默认模式（无 tier/league_preset）必须含 6 场世界杯，且 truncated=true。"""
    result = _parse(get_schedule_by_date.invoke({"date": "2026-06-28"}))
    assert result["code"] == "OK"
    assert result["meta"]["truncated"] is True
    assert result["meta"]["total_count"] == 574
    assert result["meta"]["tier_count"] >= 6
    wc = [m for m in result["data"]["matches"] if m["league_name"] == "世界杯"]
    assert len(wc) == 6
    assert result["meta"]["warning"] is not None
    assert "顶级赛事" in result["meta"]["warning"]


def test_get_schedule_by_date_league_preset_no_warning() -> None:
    """league_preset 过滤时 meta.warning 应为 None（即便 truncated）。"""
    result = _parse(
        get_schedule_by_date.invoke({"date": "2026-06-28", "league_preset": "世界杯"})
    )
    assert result["code"] == "OK"
    assert result["meta"].get("warning") is None
