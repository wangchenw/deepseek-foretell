"""赛后复盘 Tool 单元测试。"""

import json

from foretell.tools.review import get_match_result


def _parse(result: str) -> dict:
    return json.loads(result)


def test_get_match_result_finished() -> None:
    result = _parse(get_match_result.invoke({"match_id": "m_spurs_thunder_g6"}))
    assert result["code"] == "OK"
    assert result["dimension"] == "match_result"
    assert result["data"]["score_display"] == "118-112"
    assert result["data"]["key_events"]


def test_get_match_result_not_finished() -> None:
    result = _parse(get_match_result.invoke({"match_id": "m_psg_bayern"}))
    assert result["code"] == "NOT_APPLICABLE"
    assert "尚未结束" in result["data"]["reason"]


def test_get_match_result_missing() -> None:
    result = _parse(get_match_result.invoke({"match_id": "m_unknown"}))
    assert result["code"] == "DATA_MISSING"
