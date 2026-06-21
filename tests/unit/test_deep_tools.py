"""深度情报 Tool 单元测试。"""

import json

from foretell.tools.deep import get_injury_report, get_intel_tags, get_match_lineup


def _parse(result: str) -> dict:
    return json.loads(result)


def test_get_match_lineup() -> None:
    result = _parse(get_match_lineup.invoke({"match_id": "m_psg_bayern"}))
    assert result["code"] == "OK"
    assert result["dimension"] == "match_lineup"
    assert result["match_id"] == "m_psg_bayern"
    assert "home_xi" in result["data"]


def test_get_match_lineup_missing() -> None:
    result = _parse(get_match_lineup.invoke({"match_id": "m_unknown"}))
    assert result["code"] == "DATA_MISSING"


def test_get_injury_report() -> None:
    result = _parse(get_injury_report.invoke({"match_id": "m_psg_bayern"}))
    assert result["code"] == "OK"
    assert "home" in result["data"]
    assert "away" in result["data"]


def test_get_intel_tags() -> None:
    result = _parse(get_intel_tags.invoke({"match_id": "m_psg_bayern"}))
    assert result["code"] == "OK"
    assert result["data"]["count"] >= 1
    assert "tag" in result["data"]["tags"][0]


def test_get_intel_tags_missing() -> None:
    result = _parse(get_intel_tags.invoke({"match_id": "m_unknown"}))
    assert result["code"] == "DATA_MISSING"
