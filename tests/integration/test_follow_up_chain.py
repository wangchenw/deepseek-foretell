"""场景 G 多轮追问链集成测试。"""

from __future__ import annotations

import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from foretell.tools.deep import get_injury_report, get_intel_tags, get_match_lineup
from foretell.tools.entity import resolve_match, resolve_team
from foretell.tools.odds import get_odds_snapshot
from foretell.tools.stats import get_h2h, get_recent_form

THREAD_ID = "test-user:follow-up-chain"
USER_ID = "test-user"


@pytest.fixture
def mock_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """提供假 API Key 以便 create_foretell_agent 编译图（不实际调用 LLM）。"""
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key-for-pytest")


@pytest.fixture
def follow_up_config() -> dict:
    return {"configurable": {"thread_id": THREAD_ID, "user_id": USER_ID}}


def _parse(result: str) -> dict:
    return json.loads(result)


def _first_team_id(result: dict) -> int:
    return result["data"]["candidates"][0]["team_id"]


def _first_match_id(result: dict) -> int:
    return result["data"]["candidates"][0]["match_id"]


def test_follow_up_chain_tool_data() -> None:
    """Paris vs Bayern 具备追问链所需的基础数据。"""
    entity = _parse(resolve_match.invoke({"home": "巴黎", "away": "拜仁", "date": "2026-04-29"}))
    assert entity["code"] == "OK"
    match_id = _first_match_id(entity)
    assert isinstance(match_id, int)

    odds = _parse(get_odds_snapshot.invoke({"match_id": match_id}))
    assert odds["code"] == "OK"

    home = _parse(resolve_team.invoke({"name": "巴黎"}))
    away = _parse(resolve_team.invoke({"name": "拜仁"}))
    home_team_id = _first_team_id(home)
    away_team_id = _first_team_id(away)
    home_form = _parse(get_recent_form.invoke({"team_id": home_team_id, "n": 5}))
    away_form = _parse(get_recent_form.invoke({"team_id": away_team_id, "n": 5}))
    assert home_form["code"] == "OK"
    assert away_form["code"] == "OK"

    h2h = _parse(get_h2h.invoke({"team_a": home_team_id, "team_b": away_team_id}))
    assert h2h["code"] == "OK"

    lineup = _parse(get_match_lineup.invoke({"match_id": match_id}))
    injury = _parse(get_injury_report.invoke({"match_id": match_id}))
    intel = _parse(get_intel_tags.invoke({"match_id": match_id}))
    assert lineup["code"] == "DATA_MISSING"
    assert injury["code"] == "DATA_MISSING"
    assert intel["code"] == "DATA_MISSING"


def test_thread_checkpoint_persists_follow_up_messages(mock_llm_env: None) -> None:
    """固定 thread_id 下 Checkpointer 保留分析 → 比分预测 → 先进球 多轮消息。"""
    from foretell.agent import create_foretell_agent

    agent = create_foretell_agent(deploy_env="dev")
    config = {"configurable": {"thread_id": THREAD_ID, "user_id": USER_ID}}

    analysis_reply = (
        "【六段分析】巴黎 VS 拜仁：胜平负倾向主胜，让球巴黎让平手/半球，"
        "大小球 2.75 偏大，比分区间 2-1/1-1。"
    )

    agent.update_state(
        config,
        {
            "messages": [
                HumanMessage(content="分析竞彩足球周二004 巴黎 VS 拜仁胜平负、比分"),
                AIMessage(content=analysis_reply),
            ]
        },
    )

    state = agent.get_state(config)
    assert len(state.values["messages"]) == 2

    agent.update_state(
        config,
        {
            "messages": [
                HumanMessage(content="比分预测"),
                AIMessage(content="最可能比分 2-1（约 18%），其次 1-1（约 15%）。"),
            ]
        },
    )
    state2 = agent.get_state(config)
    assert len(state2.values["messages"]) == 4
    assert state2.values["messages"][-2].content == "比分预测"

    agent.update_state(
        config,
        {"messages": [HumanMessage(content="哪一队率先进球")]},
    )
    state3 = agent.get_state(config)
    assert len(state3.values["messages"]) == 5
    assert state3.values["messages"][-1].content == "哪一队率先进球"
    assert "巴黎 VS 拜仁" in state3.values["messages"][1].content


def test_agent_has_subagents(mock_llm_env: None) -> None:
    """create_foretell_agent 应成功编译并挂载子智能体。"""
    from foretell.agent import create_foretell_agent

    agent = create_foretell_agent(deploy_env="dev")
    assert agent is not None
