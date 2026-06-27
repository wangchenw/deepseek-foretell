"""统计 Tool 单元测试。"""

import json

from foretell.tools.stats import get_h2h, get_recent_form, get_standings, get_team_season_stats


def _parse(result: str) -> dict:
    return json.loads(result)


def test_get_standings() -> None:
    result = _parse(get_standings.invoke({"league_id": 46}))
    assert result["code"] == "OK"
    assert result["dimension"] == "standings"
    assert result["data"]["count"] >= 2


def test_get_standings_missing() -> None:
    result = _parse(get_standings.invoke({"league_id": 0}))
    assert result["code"] == "DATA_MISSING"


def test_get_team_season_stats() -> None:
    result = _parse(get_team_season_stats.invoke({"team_id": 10249}))
    assert result["code"] == "DATA_MISSING"
    assert result["dimension"] == "team_season_stats"
    assert result["data"]["team_id"] == 10249


def test_get_team_season_stats_missing() -> None:
    result = _parse(get_team_season_stats.invoke({"team_id": 0}))
    assert result["code"] == "DATA_MISSING"


def test_get_recent_form() -> None:
    result = _parse(get_recent_form.invoke({"team_id": 10249, "n": 3}))
    assert result["code"] == "OK"
    assert result["data"]["count"] == 3


def test_get_recent_form_home_filter() -> None:
    result = _parse(get_recent_form.invoke({"team_id": 10249, "venue": "home", "n": 5}))
    assert result["code"] == "OK"
    assert all(m["venue"] == "home" for m in result["data"]["matches"])


def test_get_recent_form_missing() -> None:
    result = _parse(get_recent_form.invoke({"team_id": 0}))
    assert result["code"] == "DATA_MISSING"


def test_get_h2h() -> None:
    result = _parse(get_h2h.invoke({"team_a": 10368, "team_b": 10016}))
    assert result["code"] == "OK"
    assert result["dimension"] == "h2h"
    assert result["data"]["count"] >= 1


def test_get_h2h_missing() -> None:
    result = _parse(get_h2h.invoke({"team_a": 10368, "team_b": 0}))
    assert result["code"] == "DATA_MISSING"
