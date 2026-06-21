"""子智能体定义单元测试。"""

from foretell.subagents import get_subagents


def test_subagent_names() -> None:
    subs = get_subagents()
    names = {s["name"] for s in subs}
    assert names == {
        "entity-resolver",
        "fundamentals-analyst",
        "odds-analyst",
        "intel-analyst",
        "screening-agent",
    }


def test_subagents_have_tools_and_skills() -> None:
    for sub in get_subagents():
        assert sub["tools"], f"{sub['name']} missing tools"
        assert sub["skills"], f"{sub['name']} missing skills"
        assert sub["system_prompt"]
        assert sub["description"]
