"""批量初筛赛程与子智能体集成测试（无 LLM）。"""

import json

from foretell.subagents import get_subagents
from foretell.tools.odds import get_odds_snapshot
from foretell.tools.schedule import get_lottery_schedule
from foretell.tools.stats import get_recent_form


def _parse(result: str) -> dict:
    return json.loads(result)


def test_fourteen_matches_lottery_schedule_by_period() -> None:
    result = _parse(get_lottery_schedule.invoke({"play_type": "401", "period": "26061"}))
    assert result["code"] == "OK"
    assert result["data"]["count"] == 4
    match_ids = {e["match_id"] for e in result["data"]["entries"]}
    assert "m_liverpool_tottenham" in match_ids
    assert "m_psg_bayern" in match_ids


def test_screening_agent_config() -> None:
    subs = get_subagents()
    screening = next(s for s in subs if s["name"] == "screening-agent")
    tool_names = {t.name for t in screening["tools"]}
    assert tool_names == {"get_recent_form", "get_odds_snapshot"}
    assert "初筛" in screening["description"]
    assert screening["skills"]


def test_batch_screening_tools_chain() -> None:
    """拉取十四场列表后，每场可完成近况+盘口快查（screening-agent 工具链）。"""
    schedule = _parse(get_lottery_schedule.invoke({"play_type": "401", "period": "26061"}))
    entries = schedule["data"]["entries"]

    from foretell.tools.crazy_sports.mock_data import MATCHES

    for entry in entries:
        match_id = entry["match_id"]
        match_info = MATCHES[match_id]
        home_id = match_info["home_team_id"]

        form = _parse(get_recent_form.invoke({"team_id": home_id, "n": 3}))
        odds = _parse(get_odds_snapshot.invoke({"match_id": match_id}))

        assert form["code"] in {"OK", "DATA_MISSING"}
        assert odds["code"] in {"OK", "DATA_MISSING", "SKIP_MATCH"}
