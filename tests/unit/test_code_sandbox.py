"""T3a: execute_code 沙箱 L1 单元测试(5 金标准 fixture)。

验证沙箱能正确执行各类统计计算,与手算期望值一致。
"""

import json
import math

from langchain_core.runnables import RunnableConfig

from foretell.tools.code_sandbox import execute_code

CFG = RunnableConfig(configurable={"thread_id": "test-l1-sandbox"})


def _run(code: str, data: str) -> dict:
    result = json.loads(execute_code.invoke({"code": code, "data": data}, config=CFG))
    assert result["code"] == "OK", f"沙箱执行失败: {result}"
    return result["data"]["result"]


def test_same_odds_win_rate() -> None:
    """同赔历史胜率聚合:10 场离散数据 → 主胜/平/客胜率,总和=1。"""
    data = json.dumps([
        {"result": "home", "odds": 1.74}, {"result": "draw", "odds": 3.2},
        {"result": "home", "odds": 1.8}, {"result": "away", "odds": 4.5},
        {"result": "home", "odds": 1.7}, {"result": "draw", "odds": 3.3},
        {"result": "home", "odds": 1.9}, {"result": "away", "odds": 5.0},
        {"result": "home", "odds": 1.6}, {"result": "home", "odds": 1.85},
    ])
    code = """
h = sum(1 for r in _data if r["result"] == "home")
d = sum(1 for r in _data if r["result"] == "draw")
a = sum(1 for r in _data if r["result"] == "away")
n = len(_data)
_result = {"home_win_rate": round(h/n, 3), "draw_rate": round(d/n, 3),
           "away_win_rate": round(a/n, 3), "total": n}
"""
    r = _run(code, data)
    assert r["total"] == 10
    assert r["home_win_rate"] == 0.6
    assert abs(r["home_win_rate"] + r["draw_rate"] + r["away_win_rate"] - 1.0) < 1e-6


def test_odds_trend_stats() -> None:
    """赔率走势统计:50 点 → 初盘/收盘/最大变动/均值。"""
    odds = [2.0 + i * 0.02 for i in range(50)]  # 2.0 → 2.98
    data = json.dumps([{"idx": i, "odds": o} for i, o in enumerate(odds)])
    code = """
xs = [r["odds"] for r in _data]
_result = {"initial": xs[0], "final": xs[-1], "max_change": round(xs[-1]-xs[0], 3),
           "mean": round(sum(xs)/len(xs), 4), "count": len(xs)}
"""
    r = _run(code, data)
    assert r["count"] == 50
    assert r["initial"] == 2.0
    assert r["final"] == 2.98
    assert r["max_change"] == 0.98


def test_correct_score_normalization() -> None:
    """竞彩比分赔率归一:31 项赔率倒数归一,Top-5,总和≈1。"""
    # 模拟 31 项比分赔率(简化为 10 项)
    items = [
        {"label": "1:0", "odds": 8.0}, {"label": "2:1", "odds": 9.5},
        {"label": "1:1", "odds": 6.5}, {"label": "0:0", "odds": 7.0},
        {"label": "2:0", "odds": 11.0}, {"label": "0:1", "odds": 12.0},
        {"label": "1:2", "odds": 13.0}, {"label": "3:0", "odds": 18.0},
        {"label": "0:2", "odds": 19.0}, {"label": "胜其他", "odds": 25.0},
    ]
    data = json.dumps(items)
    code = """
probs = [{"label": r["label"], "p": 1/r["odds"]} for r in _data]
s = sum(x["p"] for x in probs)
norm = [{"label": x["label"], "prob": round(x["p"]/s, 4)} for x in probs]
norm.sort(key=lambda x: -x["prob"])
_result = {"top5": norm[:5], "sum_probs": round(sum(x["prob"] for x in norm), 4)}
"""
    r = _run(code, data)
    assert abs(r["sum_probs"] - 1.0) < 1e-4
    assert r["top5"][0]["label"] == "1:1"  # 赔率最低 → 概率最高


def test_poisson_score_matrix() -> None:
    """Poisson 比分概率:λ_home=2.1, λ_away=1.3 → 比分矩阵,概率最大比分。"""
    data = json.dumps({"lambda_home": 2.1, "lambda_away": 1.3})
    code = """
lam_h, lam_a = _data["lambda_home"], _data["lambda_away"]
def pk(lam, k): return math.exp(-lam)*lam**k/math.factorial(k)
scores = {}
for i in range(6):
    for j in range(6):
        scores[f"{i}:{j}"] = round(pk(lam_h, i)*pk(lam_a, j), 5)
best = max(scores.items(), key=lambda x: x[1])
over_2_5 = sum(v for k, v in scores.items() if int(k.split(":")[0])+int(k.split(":")[1]) > 2.5)
_result = {"best_score": best[0], "best_prob": best[1], "over_2_5": round(over_2_5, 4)}
"""
    r = _run(code, data)
    assert r["best_score"] == "2:1"  # λ=2.1,1.3 最可能比分
    assert 0.07 < r["best_prob"] < 0.12


def test_h04_lock_formula() -> None:
    """H04 争冠锁定判定:lead=10, remaining=3 → locked=True(10 > 3*3)。"""
    data = json.dumps({"lead": 10, "remaining_rounds": 3, "points_per_win": 3})
    code = """
_result = {"locked": _data["lead"] > _data["remaining_rounds"] * _data["points_per_win"],
           "lead": _data["lead"], "remaining": _data["remaining_rounds"]}
"""
    r = _run(code, data)
    assert r["locked"] is True
    assert r["lead"] == 10

    # 未锁定场景
    data2 = json.dumps({"lead": 8, "remaining_rounds": 3, "points_per_win": 3})
    r2 = _run(code, data2)
    assert r2["locked"] is False  # 8 < 9


def test_forbidden_module_rejected() -> None:
    """危险模块被拒:import os → EXECUTION_ERROR。"""
    result = json.loads(
        execute_code.invoke({"code": "import os\n_result = os.listdir('.')", "data": "[]"}, config=CFG)
    )
    assert result["code"] == "EXECUTION_ERROR"
    assert "forbidden" in result["data"]["error"]
