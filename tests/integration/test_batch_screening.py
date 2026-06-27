"""批量初筛子智能体集成测试（无 LLM）。"""

from foretell.subagents import get_subagents


def test_screening_agent_config() -> None:
    subs = get_subagents()
    screening = next(s for s in subs if s["name"] == "screening-agent")
    tool_names = {t.name for t in screening["tools"]}
    assert tool_names == {"get_recent_form", "get_odds_snapshot"}
    assert "初筛" in screening["description"]
    assert screening["skills"]
