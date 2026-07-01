"""T3b: L2 agent 轨迹测试(不耗真实 LLM)。

验证:
1. create_foretell_agent 编译成功,execute_code + get_season_bracket 在主 agent 工具列表
2. 5 个强统计场景的"前置工具 → execute_code"数据流就绪(前置工具返回 OK,沙箱能处理其数据)
"""

from __future__ import annotations

import json

import pytest
from langchain_core.runnables import RunnableConfig

from foretell.tools import get_tools
from foretell.tools.code_sandbox import execute_code
from foretell.tools.bracket import get_season_bracket

CFG = RunnableConfig(configurable={"thread_id": "test-l2-trace"})


@pytest.fixture
def mock_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key-for-pytest")


def test_execute_code_registered_in_main_agent() -> None:
    """execute_code 在主 agent 工具列表(不加入 subagent)。"""
    tools = get_tools()
    names = {t.name for t in tools}
    assert "execute_code" in names
    assert "get_season_bracket" in names
    assert "get_standings_full" in names
    assert "get_match_review" in names


def test_agent_compiles_with_sandbox_and_bracket(mock_llm_env: None) -> None:
    """create_foretell_agent 编译成功(含 execute_code + bracket 工具)。"""
    from foretell.agent import create_foretell_agent

    agent = create_foretell_agent(deploy_env="dev")
    assert agent is not None


def test_same_odds_history_to_sandbox_dataflow() -> None:
    """F05 同赔场景:get_same_odds_history 返回离散列表 → execute_code 能聚合胜率。"""
    from foretell.tools.odds import get_same_odds_history
    from pymysql.err import OperationalError

    # 先定位一场有同赔历史的比赛(用已知的世界杯 match_id)
    try:
        odds_env = json.loads(get_same_odds_history.invoke({"match_id": 4459720}))
    except OperationalError:
        pytest.skip("DB 连接不可用")
    if odds_env["code"] != "OK" or not odds_env["data"].get("entries"):
        pytest.skip("无同赔历史数据(该场未开赛或无历史)")
    entries = odds_env["data"]["entries"]
    # 沙箱聚合:按 result 字段算胜率
    code = """
h = sum(1 for r in _data if r.get("result") == "home" or r.get("real_win") == 1)
n = len(_data)
_result = {"total": n, "home_count": h, "rate": round(h/n, 3) if n else 0}
"""
    result = json.loads(execute_code.invoke({"code": code, "data": json.dumps(entries)}, config=CFG))
    assert result["code"] == "OK"
    assert result["data"]["result"]["total"] == len(entries)


def test_odds_trend_to_sandbox_dataflow() -> None:
    """F02 走势场景:get_odds_trend 返回离散序列 → execute_code 算趋势统计。"""
    from foretell.tools.odds import get_odds_trend
    from pymysql.err import OperationalError

    try:
        trend_env = json.loads(get_odds_trend.invoke({"match_id": 4459720}))
    except OperationalError:
        pytest.skip("DB 连接不可用")
    if trend_env["code"] != "OK" or not trend_env["data"].get("trend"):
        pytest.skip("无赔率走势数据")
    trend = trend_env["data"]["trend"]
    code = """
xs = [r.get("home") or r.get("odds_home") or 0 for r in _data if isinstance(r, dict)]
_result = {"count": len(xs), "initial": xs[0] if xs else None, "final": xs[-1] if xs else None}
"""
    result = json.loads(execute_code.invoke({"code": code, "data": json.dumps(trend)}, config=CFG))
    assert result["code"] == "OK"


def test_standings_full_to_sandbox_lock_dataflow() -> None:
    """H04 锁定场景:get_standings_full 返回 lead/remaining → execute_code 判定锁定。"""
    from foretell.tools.stats import get_standings_full
    from pymysql.err import OperationalError

    try:
        env = json.loads(get_standings_full.invoke({"league_id": 168}))  # 荷甲
    except OperationalError:
        pytest.skip("DB 连接不可用")
    if env["code"] != "OK":
        pytest.skip("无积分榜数据")
    meta = env.get("meta", {})
    lead = meta.get("lead")
    remaining = meta.get("remaining_rounds")
    if lead is None or remaining is None:
        pytest.skip("无 lead/remaining 数据")
    code = """
_result = {"locked": _data["lead"] > _data["remaining"] * 3,
           "lead": _data["lead"], "remaining": _data["remaining"]}
"""
    result = json.loads(
        execute_code.invoke({"code": code, "data": json.dumps({"lead": lead, "remaining": remaining})}, config=CFG)
    )
    assert result["code"] == "OK"
    assert isinstance(result["data"]["result"]["locked"], bool)


def test_bracket_to_sandbox_path_dataflow() -> None:
    """夺冠路径场景:get_season_bracket 返回对阵树 → execute_code 能遍历 parent_id 链。"""
    from foretell.tools.crazy_sports.mysql_client import mysql_connection
    from pymysql.err import OperationalError

    # 取有对阵树的赛季(世界杯 competition_id=1)
    try:
        with mysql_connection() as cur:
            cur.execute(
                "SELECT b.season_id FROM football_brackets b WHERE b.competition_id=1 ORDER BY b.end_time DESC LIMIT 1"
            )
            row = cur.fetchone()
    except OperationalError:
        pytest.skip("DB 连接不可用")
    if not row:
        pytest.skip("无世界杯 bracket 数据")
    sid = row["season_id"]
    env = json.loads(get_season_bracket.invoke({"season_id": sid, "sport": "football"}))
    if env["code"] != "OK":
        pytest.skip("该赛季无对阵树")
    match_ups = env["data"]["match_ups"]
    # 沙箱:验证对阵树拓扑(parent_id 链可遍历)
    code = """
nodes = {m["matchup_id"]: m for m in _data}
has_parent = sum(1 for m in _data if m.get("parent_id"))
has_children = sum(1 for m in _data if m.get("children_ids"))
finals = [m for m in _data if not m.get("parent_id")]
_result = {"total": len(_data), "has_parent": has_parent, "has_children": has_children, "finals": len(finals)}
"""
    result = json.loads(execute_code.invoke({"code": code, "data": json.dumps(match_ups)}, config=CFG))
    assert result["code"] == "OK"
    r = result["data"]["result"]
    assert r["total"] == len(match_ups)
    assert r["finals"] >= 1  # 至少一个决赛节点(无 parent)
