"""StatusCode 与 PlayType 枚举单元测试。"""

from foretell.tools.status_codes import PlayType, StatusCode


def test_status_code_values() -> None:
    assert StatusCode.OK.value == "OK"
    assert StatusCode.DATA_MISSING.value == "DATA_MISSING"
    assert StatusCode.NOT_APPLICABLE.value == "NOT_APPLICABLE"
    assert StatusCode.SKIP_MATCH.value == "SKIP_MATCH"
    assert StatusCode.ENTITY_NOT_FOUND.value == "ENTITY_NOT_FOUND"
    assert StatusCode.PARTIAL.value == "PARTIAL"


def test_status_code_is_str_enum() -> None:
    assert isinstance(StatusCode.OK, str)
    assert StatusCode.OK == "OK"


def test_play_type_codes() -> None:
    assert PlayType.JINGCAI_FOOTBALL.value == "101"
    assert PlayType.JINGCAI_BASKETBALL.value == "201"
    assert PlayType.BEIDAN_WIN_LOSS.value == "301"
    assert PlayType.FOURTEEN_MATCHES.value == "401"
    assert PlayType.HALF_FULL.value == "402"
    assert PlayType.GOAL_LOTTERY.value == "403"
    assert PlayType.BEIDAN_HANDICAP.value == "404"


def test_play_type_from_string() -> None:
    assert PlayType("101") == PlayType.JINGCAI_FOOTBALL
    assert PlayType("201") == PlayType.JINGCAI_BASKETBALL
