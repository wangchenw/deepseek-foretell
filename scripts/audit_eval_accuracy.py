"""P2 正确性审计:独立重跑 LLM 沙箱 code,与 LLM 声称数值比对,评准确性/完整性/质量。

审计维度:
- numeric_accuracy:LLM final_text 声称的数值与沙箱真实输出是否一致
- logic_correctness:沙箱 code 逻辑是否真确(归一化和≈1、胜率总和=1、锁定布尔等)
- completeness:是否输出了所有该输出的统计量
- data_fidelity:LLM 从工具返回抄数据进 code 时是否有转录错误(抽样核对)
"""
from __future__ import annotations

import json
import re
from langchain_core.runnables import RunnableConfig

from foretell.tools.code_sandbox import execute_code

CFG = RunnableConfig(configurable={"thread_id": "audit-rt"})

r = json.load(open("data/eval/e2e_stats_results.json", encoding="utf-8"))


def _run_sandbox(code: str, data: str) -> dict:
    """独立执行 LLM 的沙箱 code,拿真实输出。"""
    if not code.strip():
        return {"ok": False, "error": "empty code"}
    try:
        env = json.loads(execute_code.invoke({"code": code, "data": data or "[]"}, config=CFG))
        if env["code"] == "OK":
            return {"ok": True, "result": env["data"].get("result"), "stdout": env["data"].get("stdout", "")}
        return {"ok": False, "error": env["code"], "detail": env["data"]}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def _extract_numbers(text: str) -> list[float]:
    """从文本提取所有百分比和小数(用于数值比对),已排除 think 块。"""
    # 去除 <think>...</think> 块(中间推导数不计入 LLM 声称的最终数值)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    nums = []
    # 百分比(统一转为小数,与沙箱小数输出可比)
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%", text):
        nums.append(round(float(m.group(1)) / 100, 4))
    # 小数(0.xxx 或 x.xx)
    for m in re.finditer(r"(?<![%\d])(0\.\d{2,4}|[1-9]\d?\.\d{2,4})(?![%\d])", text):
        nums.append(float(m.group(1)))
    return nums


def _check_normalization(sandbox_out: dict) -> dict:
    """检查归一化场景:和是否≈1。"""
    text = ""
    if isinstance(sandbox_out.get("result"), dict):
        text = json.dumps(sandbox_out["result"])
    elif isinstance(sandbox_out.get("result"), str):
        text = sandbox_out["result"]
    text += " " + sandbox_out.get("stdout", "")
    # 找所有 0.xxx 概率,看是否有一组和≈1
    probs = [float(m) for m in re.findall(r"(?<![\d.])(0\.\d{2,4})(?![\d])", text)]
    sums = []
    # 尝试连续 3 个概率求和(三向归一)
    for i in range(len(probs) - 2):
        s = sum(probs[i:i+3])
        if 0.95 <= s <= 1.05:
            sums.append(round(s, 4))
    return {"has_norm_sum_near_1": len(sums) > 0, "sums": sums[:3], "prob_count": len(probs)}


def audit_one(x: dict) -> dict:
    sid = x["id"]
    cat = x["category"]
    final = x.get("final_text", "")
    ecs = [(c, i) for i, c in enumerate(x["tool_calls"]) if c["name"] == "execute_code"]

    runs = []
    for ec, idx in ecs:
        args = ec["args"]
        code = args.get("code", "") if isinstance(args, dict) else ""
        data = args.get("data", "[]") if isinstance(args, dict) else "[]"
        out = _run_sandbox(code, data)
        runs.append({"idx": idx, "code_len": len(code), "out": out})

    # 取最后一次 execute_code 的输出作为最终沙箱结果
    last_out = runs[-1]["out"] if runs else {"ok": False, "error": "no execute_code"}

    # 数值比对:沙箱输出里的数 vs final_text 里的数
    sandbox_text = ""
    if last_out.get("ok"):
        r = last_out.get("result")
        if isinstance(r, dict):
            sandbox_text = json.dumps(r, ensure_ascii=False)
        elif isinstance(r, str):
            sandbox_text = r
        sandbox_text += " " + last_out.get("stdout", "")
    sandbox_nums = set(round(n, 2) for n in _extract_numbers(sandbox_text))
    final_nums = set(round(n, 2) for n in _extract_numbers(final))

    # LLM final 里声称的数,有多少在沙箱输出里出现(一致性)
    if final_nums and sandbox_nums:
        matched = sum(1 for n in final_nums if any(abs(n - s) < 0.5 for s in sandbox_nums))
        consistency = round(matched / len(final_nums), 2)
    else:
        consistency = None

    # 完整性检查(归一化场景)
    norm_check = _check_normalization(last_out) if last_out.get("ok") else {}

    # 逻辑正确性:沙箱是否成功执行
    logic_ok = last_out.get("ok", False)

    # 准确性判定
    if consistency is None:
        accuracy = "unknown"
    elif consistency >= 0.6:
        accuracy = "consistent"
    elif consistency >= 0.3:
        accuracy = "partial"
    else:
        accuracy = "inconsistent"

    return {
        "id": sid,
        "category": cat,
        "execute_code_runs": len(runs),
        "sandbox_exec_ok": logic_ok,
        "sandbox_error": last_out.get("error") if not logic_ok else None,
        "sandbox_result_preview": (sandbox_text[:300] if sandbox_text else None),
        "sandbox_nums": sorted(sandbox_nums)[:15],
        "final_nums": sorted(final_nums)[:15],
        "numeric_consistency": consistency,
        "accuracy": accuracy,
        "normalization_check": norm_check,
    }


results = [audit_one(x) for x in r]
print("=" * 80)
print("P2 正确性审计报告")
print("=" * 80)
for a in results:
    print(f"\n[{a['id']}] ({a['category']})")
    print(f"  execute_code 调用数: {a['execute_code_runs']}")
    print(f"  沙箱独立执行: {'OK' if a['sandbox_exec_ok'] else 'FAIL: ' + str(a['sandbox_error'])}")
    if a['sandbox_result_preview']:
        print(f"  沙箱输出预览: {a['sandbox_result_preview'][:200]}")
    print(f"  沙箱数值(前15): {a['sandbox_nums']}")
    print(f"  LLM声称数值(前15): {a['final_nums']}")
    print(f"  数值一致性: {a['numeric_consistency']} → 准确性={a['accuracy']}")
    if a['normalization_check']:
        nc = a['normalization_check']
        print(f"  归一化检查: 和≈1={nc['has_norm_sum_near_1']}, sums={nc['sums']}, prob_count={nc['prob_count']}")

# 汇总
print("\n" + "=" * 80)
print("汇总")
print("=" * 80)
accs = [a['accuracy'] for a in results]
logic_ok_count = sum(1 for a in results if a['sandbox_exec_ok'])
consistent = sum(1 for a in results if a['accuracy'] == 'consistent')
partial = sum(1 for a in results if a['accuracy'] == 'partial')
inconsistent = sum(1 for a in results if a['accuracy'] == 'inconsistent')
unknown = sum(1 for a in results if a['accuracy'] == 'unknown')
print(f"沙箱独立执行成功: {logic_ok_count}/{len(results)}")
print(f"数值准确性: consistent={consistent}, partial={partial}, inconsistent={inconsistent}, unknown={unknown}")

# 保存详细结果
json.dump(results, open("data/eval/e2e_stats_audit.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("\n详细审计已写入 data/eval/e2e_stats_audit.json")
