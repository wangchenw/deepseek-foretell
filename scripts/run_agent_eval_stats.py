"""P2: 10 实时世界杯沙箱统计场景真实 LLM 端到端验证。

基于 2026-07-01 世界杯 32 强赛开打语境,逐场景 invoke agent,记录 tool_calls +
沙箱代码 + 最终回复,输出 data/eval/e2e_stats_results.json。
评分维度:tool_path / numeric_correctness / no_mental_math / code_reasonable / bracket_path。
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
import traceback
from pathlib import Path

# 禁用 httpx/langsmith 等第三方 INFO 日志,stdout 只留脚本进度
logging.disable(logging.INFO)

from langchain_core.messages import HumanMessage

# 触发 load_dotenv
import config.settings  # noqa: F401
from foretell.agent import create_foretell_agent

OUTPUT = Path("data/eval/e2e_stats_results.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# 2026 世界杯 season_id=13776(P1 探查确认,6/25-7/15),葡萄牙 team_id=12082(1/16 vs 克罗地亚)
# 今日 32 强已踢:德国vs巴拉圭/法国vs瑞典/巴西vs日本/科特迪瓦vs挪威/南非vs加拿大/荷兰vs摩洛哥
# 未踢:葡萄牙vs克罗地亚/西班牙vs奥地利/美国vs波黑/比利时vs塞内加尔/墨西哥vs厄瓜多尔/英格兰vs刚果等
WC_SEASON = 13776

# 10 实时场景(带具体上下文,避免 LLM 澄清;数据缺失场景验证 agent 鲁棒降级)
SCENARIOS = [
    {
        "id": "RT01_BRACKET",
        "category": "bracket_path",
        "prompt": f"2026世界杯(season_id={WC_SEASON})葡萄牙夺冠概率多大?先用get_season_bracket(season_id={WC_SEASON})拿对阵树,再用execute_code沿parent_id路径累乘胜率算夺冠概率。葡萄牙在1/16决赛对阵克罗地亚。",
        "expect_tool": "execute_code",
        "expect_preceding": "get_season_bracket",
    },
    {
        "id": "RT02_POISSON",
        "category": "poisson",
        "prompt": f"2026世界杯1/16决赛葡萄牙vs克罗地亚,用泊松分布算各比分概率。先get_odds_snapshot拿这场欧赔(在european[0].current里),用execute_code从赔率隐含概率反推主客进球期望λ,再算比分矩阵(math.exp),给出概率最大的5个比分。",
        "expect_tool": "execute_code",
        "expect_preceding": "get_odds_snapshot",
    },
    {
        "id": "RT03_SAME_ODDS",
        "category": "same_odds",
        "prompt": "2026世界杯1/16决赛墨西哥vs厄瓜多尔(match_id=4459723),历史上同赔率下主队胜率多少?先get_same_odds_history(match_id=4459723)拿历史离散数据,再execute_code按胜平负groupby算胜率,禁止心算。",
        "expect_tool": "execute_code",
        "expect_preceding": "get_same_odds_history",
    },
    {
        "id": "RT04_EURO_NORMALIZE",
        "category": "implied_prob",
        "prompt": "2026世界杯1/16决赛葡萄牙vs克罗地亚,欧赔隐含概率归一化多少?先get_odds_snapshot拿这场赔率(在european[0].current的home_win/draw/away_win),再execute_code三向倒数归一化,禁止心算,给出主胜/平/客胜概率,和应≈100%。",
        "expect_tool": "execute_code",
        "expect_preceding": "get_odds_snapshot",
    },
    {
        "id": "RT05_ODDS_CHANGE",
        "category": "odds_change",
        "prompt": "2026世界杯1/16决赛葡萄牙vs克罗地亚,盘口变动分析。先get_odds_snapshot拿这场赔率(european[0]的initial和current),用execute_code算初盘到即时盘的主胜/平/客胜赔率变动百分比和方向,统计各家公司的盘口倾向。",
        "expect_tool": "execute_code",
        "expect_preceding": "get_odds_snapshot",
    },
    {
        "id": "RT06_BF_NORMALIZE",
        "category": "bf_normalize",
        "prompt": "2026世界杯1/16决赛葡萄牙vs克罗地亚,竞彩比分赔率归一化。先resolve_lottery_match或get_official_handicap_odds拿比分赔率,再execute_code对各比分赔率倒数归一化,取隐含概率最高的5个比分,并说明归一化总和情况(是否≈1,若不是请解释原因)。",
        "expect_tool": "execute_code",
        "expect_preceding": None,
    },
    {
        "id": "RT07_H2H",
        "category": "h2h",
        "prompt": "2026世界杯1/16决赛法国vs瑞典,历史交锋胜负平分布。先resolve_team拿法国和瑞典team_id,再get_h2h拿交锋历史,最后execute_code统计胜负平场次和胜率。",
        "expect_tool": "execute_code",
        "expect_preceding": "get_h2h",
    },
    {
        "id": "RT08_RECENT_FORM",
        "category": "recent_form",
        "prompt": "2026世界杯1/16决赛西班牙队最近战绩胜率和场均进球。先resolve_team拿西班牙team_id,再get_recent_form(n=10)拿最近10场,最后execute_code聚合胜率和场均进球/失球。",
        "expect_tool": "execute_code",
        "expect_preceding": "get_recent_form",
    },
    {
        "id": "RT09_OVER_UNDER",
        "category": "over_under",
        "prompt": "2026世界杯1/16决赛葡萄牙vs克罗地亚,大小球赔率隐含概率归一。先get_over_under_odds拿这场大小球赔率,再execute_code对各档(2.0/2.5/3.0等)赔率倒数归一化,给出大球/小球概率。",
        "expect_tool": "execute_code",
        "expect_preceding": "get_over_under_odds",
    },
    {
        "id": "RT10_LOCK_MATH",
        "category": "league_math",
        "prompt": "2026赛季荷甲(league_id=168)争冠形势,榜首是否已锁定冠军?先get_standings_full(league_id=168)拿领先分差lead和剩余轮次remaining_rounds,再execute_code用锁定公式lead > remaining_rounds * 3判定。",
        "expect_tool": "execute_code",
        "expect_preceding": "get_standings_full",
    },
]


def _extract_tool_calls(messages: list) -> list[dict]:
    """从 agent 返回的 messages 提取 tool_calls 序列。"""
    calls = []
    for m in messages:
        tool_calls = getattr(m, "tool_calls", None) or []
        for tc in tool_calls:
            name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
            args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", None)
            calls.append({"name": name, "args": args})
    return calls


def _extract_sandbox_code(messages: list) -> str:
    """提取 execute_code 的 code 参数(沙箱脚本)。"""
    for m in messages:
        tool_calls = getattr(m, "tool_calls", None) or []
        for tc in tool_calls:
            name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
            if name == "execute_code":
                args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", None)
                if isinstance(args, dict):
                    return args.get("code", "")
    return ""


def _extract_final_text(messages: list) -> str:
    """提取最后一条 AI 文本回复。"""
    for m in reversed(messages):
        content = getattr(m, "content", "")
        if content and getattr(m, "type", None) == "ai" and not getattr(m, "tool_calls", None):
            return content if isinstance(content, str) else str(content)
    return ""


def _score(scenario: dict, tool_calls: list[dict], final_text: str, sandbox_code: str) -> dict:
    """按 5 维度评分。"""
    names = [c["name"] for c in tool_calls]
    has_execute_code = "execute_code" in names
    has_preceding = (
        scenario["expect_preceding"] in names if scenario.get("expect_preceding") else True
    )
    has_bracket = "get_season_bracket" in names if scenario["category"] == "bracket_path" else True

    no_mental_math = has_execute_code

    # numeric_correctness:最终回复含数值结果(胜率/概率/比分/锁定,带%或小数)
    has_pct = bool(re.search(r"\d+(\.\d+)?\s*%|胜率|概率|锁定|比分|进球", final_text))
    numeric_correctness = has_pct

    # code_reasonable:沙箱代码非空且含统计结构
    code_reasonable = bool(sandbox_code) and bool(
        re.search(r"for|sum|math\.exp|1/|len\(|round\(|\[\w+|\{.*:.*\}", sandbox_code)
    )

    tool_path = has_execute_code and has_preceding and has_bracket

    return {
        "tool_path": tool_path,
        "numeric_correctness": numeric_correctness,
        "no_mental_math": no_mental_math,
        "code_reasonable": code_reasonable,
        "bracket_path": has_bracket,
        "overall": tool_path and no_mental_math and code_reasonable,
    }


def run_one(agent, scenario: dict) -> dict:
    sid = scenario["id"]
    thread_id = f"rt-{sid}"
    config = {"configurable": {"thread_id": thread_id, "user_id": "eval-rt"}}
    t0 = time.time()
    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=scenario["prompt"])]}, config=config
        )
        msgs = result.get("messages", [])
        tool_calls = _extract_tool_calls(msgs)
        final_text = _extract_final_text(msgs)
        sandbox_code = _extract_sandbox_code(msgs)
        scores = _score(scenario, tool_calls, final_text, sandbox_code)
        elapsed = round(time.time() - t0, 1)
        # 判 gap 类型
        gap = None
        if not scores["overall"]:
            if not scores["tool_path"]:
                gap = "orchestration" if not scores["no_mental_math"] else "tool_path"
            elif not scores["code_reasonable"]:
                gap = "sandbox_code"
            elif not scores["numeric_correctness"]:
                gap = "numeric_output"
        return {
            "id": sid,
            "category": scenario["category"],
            "prompt": scenario["prompt"],
            "tool_calls": tool_calls,
            "tool_call_count": len(tool_calls),
            "sandbox_code": sandbox_code[:1500],
            "final_text": final_text[:2000],
            "scores": scores,
            "gap": gap,
            "elapsed_s": elapsed,
            "status": "ok",
        }
    except Exception as e:
        return {
            "id": sid,
            "category": scenario["category"],
            "prompt": scenario["prompt"],
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc()[:2000],
            "elapsed_s": round(time.time() - t0, 1),
            "status": "error",
            "gap": "exception",
        }


def main() -> int:
    only = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    if not os.environ.get("MINIMAX_API_KEY"):
        print("ERROR: MINIMAX_API_KEY 未设置,无法跑真实 LLM 评估", file=sys.stderr)
        return 2

    print("创建 agent...")
    agent = create_foretell_agent(deploy_env="dev")

    results = []
    for sc in SCENARIOS:
        if only and sc["id"] not in only:
            continue
        print(f"\n[{sc['id']}] {sc['prompt'][:50]}...", flush=True)
        r = run_one(agent, sc)
        results.append(r)
        if r["status"] == "ok":
            s = r["scores"]
            print(
                f"  -> tools={r['tool_call_count']} elapsed={r['elapsed_s']}s "
                f"overall={s['overall']} gap={r.get('gap')}"
            )
            print(f"  tool_calls: {[c['name'] for c in r['tool_calls']]}")
        else:
            print(f"  -> ERROR: {r.get('error', '')[:120]}")

    OUTPUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n结果已写入 {OUTPUT}")

    ok = [r for r in results if r["status"] == "ok"]
    passed = [r for r in ok if r["scores"]["overall"]]
    print(f"\n汇总: {len(passed)}/{len(results)} 通过 (overall), {len(ok)}/{len(results)} 无错误")
    if results:
        gaps = [r.get("gap") for r in results if r.get("gap")]
        if gaps:
            print(f"gap 分布: {dict((g, gaps.count(g)) for g in set(gaps))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
