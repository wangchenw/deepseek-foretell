from datetime import date

from api import main as api_main
from foretell.prompts import build_system_prompt
from foretell.tools import get_tools


def test_build_system_prompt_includes_current_date() -> None:
    prompt = build_system_prompt(date(2026, 6, 26))

    assert "当前日期：2026-06-26" in prompt
    assert "Asia/Shanghai" in prompt


def test_get_tools_includes_internet_search() -> None:
    tool_names = {tool.name for tool in get_tools()}

    assert "internet_search" in tool_names


def test_api_agent_cache_is_partitioned_by_date(monkeypatch) -> None:
    created_agents = []

    def fake_create_foretell_agent(deploy_env: str):
        agent = object()
        created_agents.append((deploy_env, agent))
        return agent

    monkeypatch.setattr(api_main, "create_foretell_agent", fake_create_foretell_agent)
    api_main._get_agent_for_date.cache_clear()

    same_day_first = api_main._get_agent_for_date("2026-06-26")
    same_day_second = api_main._get_agent_for_date("2026-06-26")
    next_day = api_main._get_agent_for_date("2026-06-27")

    assert same_day_first is same_day_second
    assert next_day is not same_day_first
    assert len(created_agents) == 2

    api_main._get_agent_for_date.cache_clear()
