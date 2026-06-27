"""实体与赛程 Tool 单元测试。"""

import json

from foretell.tools.entity import (
    resolve_league,
    resolve_lottery_match,
    resolve_match,
    resolve_team,
)
from foretell.tools.schedule import (
    get_lottery_schedule,
    get_schedule_by_date,
    get_team_schedule,
)


def _parse(result: str) -> dict:
    return json.loads(result)


def _candidates(result: dict) -> list[dict]:
    return result["data"]["candidates"]


def _first_match_id(result: dict) -> int:
    return _candidates(result)[0]["match_id"]


def _first_team_id(result: dict) -> int:
    return _candidates(result)[0]["team_id"]


def _first_league_id(result: dict) -> int:
    return _candidates(result)[0]["league_id"]


def test_resolve_match_found() -> None:
    result = _parse(resolve_match.invoke({"home": "巴黎", "away": "拜仁", "date": "2026-04-29"}))
    assert result["code"] == "OK"
    assert result["dimension"] == "match_entity"
    assert "match_id" not in result
    assert result["data"]["count"] == len(_candidates(result))
    assert isinstance(_first_match_id(result), int)
    assert isinstance(_candidates(result)[0]["home_team_id"], int)
    assert isinstance(_candidates(result)[0]["away_team_id"], int)


def test_resolve_match_not_found() -> None:
    result = _parse(resolve_match.invoke({"home": "不存在主队", "away": "不存在客队"}))
    assert result["code"] == "ENTITY_NOT_FOUND"
    assert result["dimension"] == "match_entity"


def test_resolve_match_series_game_not_found() -> None:
    result = _parse(resolve_match.invoke({"home": "巴黎", "away": "拜仁", "series_game": 99}))
    assert result["code"] == "NOT_APPLICABLE"
    assert "series_game" in result["data"]


def test_resolve_lottery_match() -> None:
    result = _parse(resolve_lottery_match.invoke({"play_type": "101", "code": "周二004"}))
    assert result["code"] == "OK"
    assert result["data"]["lottery_id"]
    assert "match_id" not in result
    if result["data"].get("match_candidates"):
        assert isinstance(result["data"]["match_candidates"][0]["match_id"], int)
    assert result["data"]["lottery_code"]


def test_resolve_lottery_match_basketball() -> None:
    result = _parse(resolve_lottery_match.invoke({"play_type": "201", "code": "周日301"}))
    assert result["code"] == "OK"
    assert result["data"]["play_type"] == "201"
    assert result["data"]["issue_num"] == 7301
    assert result["data"]["lottery_code"] == "周日301"


def test_resolve_lottery_match_fourteen_candidates() -> None:
    result = _parse(resolve_lottery_match.invoke({"play_type": "401", "code": "第1场"}))
    assert result["code"] == "OK"
    data = result["data"]
    if data.get("candidates"):
        assert data["count"] >= 1
        assert data["candidates"][0]["play_type"] == "401"
        assert data["candidates"][0]["issue_num"] == 1
    else:
        assert data["play_type"] == "401"
        assert data["issue_num"] == 1


def test_resolve_lottery_match_not_found() -> None:
    result = _parse(resolve_lottery_match.invoke({"play_type": "101", "code": "周二999"}))
    assert result["code"] == "ENTITY_NOT_FOUND"


def test_resolve_team() -> None:
    result = _parse(resolve_team.invoke({"name": "利物浦"}))
    assert result["code"] == "OK"
    assert result["data"]["name"] == "利物浦"
    assert result["data"]["count"] == len(_candidates(result))
    assert 1 <= result["data"]["count"] <= 10
    assert isinstance(_first_team_id(result), int)


def test_resolve_team_portugal_national_team() -> None:
    result = _parse(resolve_team.invoke({"name": "葡萄牙"}))
    assert result["code"] == "OK"
    candidates = _candidates(result)
    assert any(team["national"] == 1 for team in candidates)
    assert any(team["national"] == 0 for team in candidates)


def test_resolve_team_portugal_sporting_club() -> None:
    result = _parse(resolve_team.invoke({"name": "葡萄牙体育"}))
    assert result["code"] == "OK"
    assert any(team["national"] == 0 for team in _candidates(result))


def test_resolve_league() -> None:
    result = _parse(resolve_league.invoke({"name": "欧冠"}))
    assert result["code"] == "OK"
    assert result["data"]["name"] == "欧冠"
    assert result["data"]["count"] == len(_candidates(result))
    assert 1 <= result["data"]["count"] <= 10
    assert isinstance(_first_league_id(result), int)


def test_get_schedule_by_date() -> None:
    result = _parse(get_schedule_by_date.invoke({"date": "2026-04-29"}))
    assert result["code"] == "OK"
    assert result["data"]["count"] >= 1
    assert result["meta"]["limit"] == 100
    assert isinstance(result["meta"]["truncated"], bool)
    assert all(isinstance(match["match_id"], int) for match in result["data"]["matches"])


def test_get_schedule_by_date_football_filter() -> None:
    result = _parse(get_schedule_by_date.invoke({"date": "2026-04-29", "sport": "football"}))
    assert result["code"] == "OK"
    assert result["data"]["count"] >= 1
    assert all(match["sport"] == "football" for match in result["data"]["matches"])


def test_get_schedule_by_date_league_preset() -> None:
    result = _parse(
        get_schedule_by_date.invoke({"date": "2026-04-29", "league_preset": "欧冠"})
    )
    assert result["code"] == "OK"
    assert result["data"]["league_preset"] == "欧冠"
    assert result["data"]["count"] >= 1
    assert all("欧冠" in match["league_name"] for match in result["data"]["matches"])


def test_get_schedule_by_date_empty() -> None:
    result = _parse(get_schedule_by_date.invoke({"date": "2099-01-01"}))
    assert result["code"] == "DATA_MISSING"


def test_get_team_schedule() -> None:
    team = _parse(resolve_team.invoke({"name": "利物浦"}))
    result = _parse(
        get_team_schedule.invoke({"team_id": _first_team_id(team), "direction": "all"})
    )
    assert result["code"] == "OK"
    assert result["data"]["count"] >= 1


def test_get_lottery_schedule() -> None:
    result = _parse(get_lottery_schedule.invoke({"play_type": "101"}))
    assert result["code"] == "OK"
    assert result["data"]["count"] >= 1


def test_get_lottery_schedule_basketball() -> None:
    result = _parse(get_lottery_schedule.invoke({"play_type": "201", "date": "2025-07-28"}))
    assert result["code"] == "OK"
    assert result["data"]["count"] >= 1
    assert all(entry["play_type"] == "201" for entry in result["data"]["entries"])


def test_get_lottery_schedule_beidan() -> None:
    result = _parse(get_lottery_schedule.invoke({"play_type": "301", "period": "25075"}))
    assert result["code"] == "OK"
    assert result["data"]["count"] >= 1
    assert all(entry["play_type"] == "301" for entry in result["data"]["entries"])


def test_get_lottery_schedule_fourteen() -> None:
    result = _parse(get_lottery_schedule.invoke({"play_type": "401", "period": "25093"}))
    assert result["code"] == "OK"
    assert result["data"]["count"] == 14
    assert all(entry["play_type"] == "401" for entry in result["data"]["entries"])


def test_get_lottery_schedule_half_full_and_goal_lottery() -> None:
    half_full = _parse(get_lottery_schedule.invoke({"play_type": "402", "period": "26126"}))
    goal = _parse(get_lottery_schedule.invoke({"play_type": "403", "period": "26133"}))
    assert half_full["code"] == "OK"
    assert goal["code"] == "OK"
    assert half_full["data"]["count"] >= 1
    assert goal["data"]["count"] >= 1


def test_get_lottery_schedule_beidan_handicap() -> None:
    result = _parse(get_lottery_schedule.invoke({"play_type": "404", "period": "25075"}))
    assert result["code"] == "OK"
    assert result["data"]["count"] >= 1
    assert all(entry["play_type"] == "404" for entry in result["data"]["entries"])
