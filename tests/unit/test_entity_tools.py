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


def test_resolve_match_found() -> None:
    result = _parse(resolve_match.invoke({"home": "巴黎圣曼", "away": "拜仁", "date": "2026-04-29"}))
    assert result["code"] == "OK"
    assert result["dimension"] == "match_entity"
    assert result["match_id"] == "m_psg_bayern"
    assert result["data"]["home_name"] == "巴黎圣曼"


def test_resolve_match_not_found() -> None:
    result = _parse(resolve_match.invoke({"home": "不存在主队", "away": "不存在客队"}))
    assert result["code"] == "ENTITY_NOT_FOUND"
    assert result["dimension"] == "match_entity"


def test_resolve_match_series_game_g7() -> None:
    result = _parse(
        resolve_match.invoke({"home": "马刺", "away": "雷霆", "series_game": 7})
    )
    assert result["code"] == "OK"
    assert result["match_id"] == "m_spurs_thunder_g7"
    assert result["data"]["series_game"] == 7


def test_resolve_match_series_game_not_found() -> None:
    result = _parse(
        resolve_match.invoke({"home": "马刺", "away": "雷霆", "series_game": 99})
    )
    assert result["code"] == "NOT_APPLICABLE"
    assert "series_game" in result["data"]


def test_resolve_lottery_match() -> None:
    result = _parse(
        resolve_lottery_match.invoke({"play_type": "101", "code": "周二004"})
    )
    assert result["code"] == "OK"
    assert result["match_id"] == "m_psg_bayern"
    assert result["data"]["lottery_code"] == "周二004"


def test_resolve_lottery_match_not_found() -> None:
    result = _parse(
        resolve_lottery_match.invoke({"play_type": "101", "code": "周二999"})
    )
    assert result["code"] == "ENTITY_NOT_FOUND"


def test_resolve_team() -> None:
    result = _parse(resolve_team.invoke({"name": "利物浦"}))
    assert result["code"] == "OK"
    assert result["data"]["team_id"] == "t_liverpool"


def test_resolve_team_portugal_national_team() -> None:
    result = _parse(resolve_team.invoke({"name": "葡萄牙"}))
    assert result["code"] == "OK"
    assert result["data"]["team_id"] == "t_portugal_nt"
    assert result["data"]["national"] == 1
    assert result["meta"]["is_national"] is True


def test_resolve_team_portugal_sporting_club() -> None:
    result = _parse(resolve_team.invoke({"name": "葡萄牙体育"}))
    assert result["code"] == "OK"
    assert result["data"]["team_id"] == "t_portugal_sporting"
    assert result["data"]["national"] == 0


def test_resolve_league() -> None:
    result = _parse(resolve_league.invoke({"name": "欧冠"}))
    assert result["code"] == "OK"
    assert result["data"]["league_id"] == "l_ucl"


def test_get_schedule_by_date() -> None:
    result = _parse(get_schedule_by_date.invoke({"date": "2026-06-21"}))
    assert result["code"] == "OK"
    assert result["data"]["count"] == 2


def test_get_schedule_by_date_football_filter() -> None:
    result = _parse(
        get_schedule_by_date.invoke({"date": "2026-06-21", "sport": "football"})
    )
    assert result["code"] == "OK"
    assert result["data"]["count"] == 1


def test_get_schedule_by_date_empty() -> None:
    result = _parse(get_schedule_by_date.invoke({"date": "2099-01-01"}))
    assert result["code"] == "DATA_MISSING"


def test_get_team_schedule() -> None:
    result = _parse(
        get_team_schedule.invoke({"team_id": "t_liverpool", "direction": "all"})
    )
    assert result["code"] == "OK"
    assert result["data"]["count"] == 1


def test_get_lottery_schedule() -> None:
    result = _parse(get_lottery_schedule.invoke({"play_type": "101", "date": "2026-06-21"}))
    assert result["code"] == "OK"
    assert result["data"]["count"] == 1


def test_get_lottery_schedule_fourteen_by_period() -> None:
    result = _parse(get_lottery_schedule.invoke({"play_type": "401", "period": "26061"}))
    assert result["code"] == "OK"
    assert result["data"]["count"] == 4
