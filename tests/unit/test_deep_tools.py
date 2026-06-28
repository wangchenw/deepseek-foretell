"""深度情报 Tool 单元测试。"""

import json

from foretell.tools.deep import get_injury_report, get_intel_tags, get_match_lineup


def _parse(result: str) -> dict:
    return json.loads(result)


def test_get_match_lineup() -> None:
    result = _parse(get_match_lineup.invoke({"match_id": 4531806}))
    assert result["code"] == "OK"
    assert result["dimension"] == "match_lineup"
    assert result["match_id"] == 4531806


def test_get_match_lineup_missing() -> None:
    result = _parse(get_match_lineup.invoke({"match_id": 0}))
    assert result["code"] == "DATA_MISSING"


def test_get_injury_report() -> None:
    result = _parse(get_injury_report.invoke({"match_id": 4531806}))
    assert result["code"] == "OK"
    assert result["match_id"] == 4531806


def test_get_intel_tags() -> None:
    result = _parse(get_intel_tags.invoke({"match_id": 4531806}))
    assert result["code"] == "OK"
    assert result["data"]["count"] >= 1


def test_get_intel_tags_missing() -> None:
    result = _parse(get_intel_tags.invoke({"match_id": 0}))
    assert result["code"] == "DATA_MISSING"
