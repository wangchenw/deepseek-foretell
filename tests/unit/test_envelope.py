"""make_envelope 单元测试。"""

import json

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
        match_id="m_12345",
        meta={"source": "crazy_sports_db", "freshness": "mock"},
    )
    parsed = json.loads(raw)
    assert parsed["match_id"] == "m_12345"
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
