"""赛后复盘 Tool 单元测试。"""

import json

from foretell.tools.review import get_match_result


def _parse(result: str) -> dict:
    return json.loads(result)


def test_get_match_result_finished() -> None:
    result = _parse(get_match_result.invoke({"match_id": 4531806}))
    assert result["code"] == "OK"
    assert result["dimension"] == "match_result"
    assert result["data"]["full_time"]
    assert result["data"]["status"] == "finished"


def test_get_match_result_not_finished() -> None:
    result = _parse(get_match_result.invoke({"match_id": 4460934}))
    assert result["code"] == "NOT_APPLICABLE"
    assert "尚未结束" in result["data"]["reason"]


def test_get_match_result_missing() -> None:
    result = _parse(get_match_result.invoke({"match_id": 0}))
    assert result["code"] == "DATA_MISSING"
