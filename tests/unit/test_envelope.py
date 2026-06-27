"""make_envelope 单元测试。"""

import json
from decimal import Decimal

from foretell.tools.envelope import make_envelope
from foretell.tools.status_codes import StatusCode


def test_envelope_ok_minimal() -> None:
    raw = make_envelope(StatusCode.OK, "match_entity", {"foo": "bar"})
    parsed = json.loads(raw)
    assert parsed["code"] == "OK"
    assert parsed["dimension"] == "match_entity"
    assert parsed["data"] == {"foo": "bar"}
    assert "match_id" not in parsed
    assert "meta" not in parsed


def test_envelope_with_match_id_and_meta() -> None:
    raw = make_envelope(
        StatusCode.OK,
        "schedule_by_date",
        {"matches": []},
        match_id=12345,
        meta={"source": "crazy_sports_db", "freshness": "2026-06-27T00:00:00Z"},
    )
    parsed = json.loads(raw)
    assert parsed["match_id"] == 12345
    assert parsed["meta"]["source"] == "crazy_sports_db"


def test_envelope_all_status_codes() -> None:
    for code in StatusCode:
        raw = make_envelope(code, "test_dimension")
        parsed = json.loads(raw)
        assert parsed["code"] == code.value
        assert parsed["dimension"] == "test_dimension"
        assert parsed["data"] == {}


def test_envelope_string_code() -> None:
    raw = make_envelope("CUSTOM", "test", data=None)
    parsed = json.loads(raw)
    assert parsed["code"] == "CUSTOM"
    assert parsed["data"] == {}


def test_envelope_serializes_mysql_decimal_odds() -> None:
    raw = make_envelope(
        StatusCode.OK,
        "odds_snapshot",
        {
            "european": [
                {"odd1": Decimal("1.85"), "odd2": Decimal("3.40"), "odd3": Decimal("4.20")}
            ]
        },
        match_id=123,
    )
    parsed = json.loads(raw)
    assert parsed["data"]["european"][0]["odd1"] == 1.85
