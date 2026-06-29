"""盘口 Tool 单元测试。"""

import json

from foretell.tools.odds import (
    get_betfair,
    get_kelly,
    get_odds_snapshot,
    get_odds_trend,
    get_same_odds_history,
)


def _parse(result: str) -> dict:
    return json.loads(result)


def test_get_odds_snapshot_football() -> None:
    result = _parse(get_odds_snapshot.invoke({"match_id": 4531806}))
    assert result["code"] == "OK"
    assert result["dimension"] == "odds_snapshot"
    assert result["match_id"] == 4531806
    assert "european" in result["data"]
    assert "asian" in result["data"]


def test_get_odds_snapshot_skip_match() -> None:
    result = _parse(get_odds_snapshot.invoke({"match_id": 0}))
    assert result["code"] == "SKIP_MATCH"
    assert result["dimension"] == "odds_snapshot"


def test_get_odds_trend() -> None:
    result = _parse(get_odds_trend.invoke({"match_id": 4531806}))
    assert result["code"] in {"OK", "DATA_MISSING"}
    if result["code"] == "OK":
        assert "points" in result["data"]
        assert result["data"]["count"] >= 0


def test_get_odds_trend_missing() -> None:
    result = _parse(get_odds_trend.invoke({"match_id": 0}))
    assert result["code"] == "DATA_MISSING"


def test_get_same_odds_history() -> None:
    result = _parse(get_same_odds_history.invoke({"match_id": 4531806}))
    assert result["code"] == "OK"
    assert result["data"]["count"] >= 1


def test_get_kelly() -> None:
    result = _parse(get_kelly.invoke({"match_id": 4531806}))
    assert result["code"] == "OK"
    assert result["data"]["entries"]


def test_get_betfair() -> None:
    result = _parse(get_betfair.invoke({"match_id": 4531806}))
    assert result["code"] == "OK"
