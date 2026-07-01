"""S4: 验证 lottery odds 键名已改为英文全称(消除拼音缩写歧义)。"""

import json

from foretell.tools.schedule import get_lottery_schedule


def _parse(result: str) -> dict:
    return json.loads(result)


# 各 play_type 期望出现的英文全称键子集
_EXPECTED_LABELS = {
    "101": {"win_draw_loss", "handicap_wdl", "correct_score", "total_goals", "half_full_result"},
    "201": {"win_loss", "handicap_wl", "over_under", "fourteen_wdl"},
    "301": {"win_draw_loss", "total_goals", "half_full_result", "six_x_po", "correct_score"},
    "404": {"win_loss"},
}

# 旧拼音缩写键,改名后不应再出现
_LEGACY_KEYS = {"spf", "rq", "bf", "jq", "bqc", "sf", "rf", "dxf", "sfc", "sxp"}


def _collect_odds_keys(result: dict) -> set[str]:
    keys: set[str] = set()
    for entry in result["data"]["entries"]:
        odds = entry.get("odds")
        if isinstance(odds, dict):
            keys.update(odds.keys())
    return keys


def test_lottery_odds_keys_jingcai_football() -> None:
    result = _parse(get_lottery_schedule.invoke({"play_type": "101"}))
    assert result["code"] == "OK"
    keys = _collect_odds_keys(result)
    if keys:
        assert keys <= _EXPECTED_LABELS["101"], f"出现非预期键: {keys - _EXPECTED_LABELS['101']}"
        assert not (keys & _LEGACY_KEYS), f"残留旧缩写键: {keys & _LEGACY_KEYS}"


def test_lottery_odds_keys_jingcai_basketball() -> None:
    result = _parse(get_lottery_schedule.invoke({"play_type": "201", "date": "2025-07-28"}))
    assert result["code"] == "OK"
    keys = _collect_odds_keys(result)
    if keys:
        assert keys <= _EXPECTED_LABELS["201"], f"出现非预期键: {keys - _EXPECTED_LABELS['201']}"
        assert not (keys & _LEGACY_KEYS), f"残留旧缩写键: {keys & _LEGACY_KEYS}"


def test_lottery_odds_keys_beidan_win_loss() -> None:
    result = _parse(get_lottery_schedule.invoke({"play_type": "301", "period": "25075"}))
    assert result["code"] == "OK"
    keys = _collect_odds_keys(result)
    if keys:
        assert keys <= _EXPECTED_LABELS["301"], f"出现非预期键: {keys - _EXPECTED_LABELS['301']}"
        assert not (keys & _LEGACY_KEYS), f"残留旧缩写键: {keys & _LEGACY_KEYS}"


def test_lottery_odds_keys_beidan_handicap() -> None:
    result = _parse(get_lottery_schedule.invoke({"play_type": "404", "period": "25075"}))
    assert result["code"] == "OK"
    keys = _collect_odds_keys(result)
    if keys:
        assert keys <= _EXPECTED_LABELS["404"], f"出现非预期键: {keys - _EXPECTED_LABELS['404']}"
        assert not (keys & _LEGACY_KEYS), f"残留旧缩写键: {keys & _LEGACY_KEYS}"


def test_lottery_odds_no_legacy_keys_any_play() -> None:
    """所有玩法都不应残留旧拼音缩写键。"""
    for play_type in ("101", "201", "301", "404"):
        params = {"play_type": play_type}
        if play_type in ("301", "404"):
            params["period"] = "25075"
        if play_type == "201":
            params["date"] = "2025-07-28"
        result = _parse(get_lottery_schedule.invoke(params))
        if result["code"] == "OK":
            keys = _collect_odds_keys(result)
            assert not (keys & _LEGACY_KEYS), f"play_type={play_type} 残留旧缩写键: {keys & _LEGACY_KEYS}"
