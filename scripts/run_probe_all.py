#!/usr/bin/env python3
"""批量跑全量 120 type_id 浅层探针,刷新 data/eval/probe_results/{id}.json。

阶段A 回归筛子:调改动后 foretell tools,验证工具链通断。
注意:浅层探针用 entity_entry 模板参数(如"葡萄牙"/"利物浦"),不命中具体场景数据 bug,
仅用于快速发现改动引入的工具链断裂(回归 ❌)。具体场景数据正确性由阶段B 三智能体真探索兜底。

用法:
    uv run python scripts/run_probe_all.py                    # 全量 120
    uv run python scripts/run_probe_all.py --scenario A,X     # 仅 A+X 批
    uv run python scripts/run_probe_all.py --dry-run          # 不实跑,仅列清单
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_common import load_taxonomy  # noqa: E402
from probe_route import run_probe  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run tool-chain probe for all 120 type_ids")
    parser.add_argument(
        "--scenario",
        default=None,
        help="逗号分隔场景字母过滤,如 A,X;默认全量",
    )
    parser.add_argument("--dry-run", action="store_true", help="不实跑,仅统计将探的 type_id")
    args = parser.parse_args()

    scenarios: set[str] | None = None
    if args.scenario:
        scenarios = {s.strip().upper() for s in args.scenario.split(",") if s.strip()}

    types = load_taxonomy()
    if scenarios:
        types = [t for t in types if t.scenario in scenarios]

    total = len(types)
    print(f"[run_probe_all] 待探 type_id: {total} 个"
          + (f" (scenario={sorted(scenarios)})" if scenarios else ""))

    ok = 0
    skipped = 0
    failed: list[tuple[str, str]] = []

    for i, t in enumerate(types, start=1):
        type_id = t.id
        try:
            result = run_probe(type_id, dry_run=args.dry_run)
            steps = len(result.get("steps", []))
            if result.get("skipped"):
                skipped += 1
                status = "SKIP"
            elif result.get("error"):
                failed.append((type_id, result["error"]))
                status = "ERR"
            else:
                ok += 1
                status = "OK"
            print(f"  [{i}/{total}] {type_id} {status} steps={steps}")
        except Exception as exc:  # noqa: BLE001 — 批量探针需容错继续
            failed.append((type_id, str(exc)))
            print(f"  [{i}/{total}] {type_id} EXC {exc}")

    print("\n[run_probe_all] 汇总:")
    print(f"  总数: {total}")
    print(f"  OK:   {ok}")
    print(f"  SKIP: {skipped}")
    print(f"  FAIL: {len(failed)}")
    if failed:
        print("  失败明细:")
        for tid, err in failed:
            print(f"    {tid}: {err[:120]}")


if __name__ == "__main__":
    main()
