#!/usr/bin/env python3
"""Phase 2a: diagnose resolve_lottery_match parameter combinations (read-only, no tool code changes)."""

from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_eval_common import EVAL_DIR, dump_yaml, today_iso  # noqa: E402

REPORT_PATH = EVAL_DIR / "phase2a_lottery_diagnosis.yaml"


def _parse(raw: str) -> dict[str, Any]:
    return json.loads(raw)


def sweep_lottery_codes() -> list[dict[str, Any]]:
    from foretell.tools.entity import resolve_lottery_match

    # B01 template: 周日009 德国 VS 库拉索 2026-06-15
    codes = ["009", "周日009", "周009", "009", "德国", "Sunday009"]
    dates = ["2026-06-15", None, today_iso()]
    play_types = ["101"]

    results: list[dict[str, Any]] = []
    for pt, code, dt in product(play_types, codes, dates):
        params: dict[str, Any] = {"play_type": pt, "code": code}
        if dt:
            params["date"] = dt
        try:
            raw = resolve_lottery_match.invoke(params)
            data = _parse(raw)
            results.append(
                {
                    "params": params,
                    "code": data.get("code"),
                    "match_id": data.get("match_id"),
                }
            )
        except Exception as exc:  # noqa: BLE001
            results.append({"params": params, "code": "ERROR", "error": str(exc)})

    return results


def sweep_active_lottery() -> dict[str, Any]:
    from foretell.tools.schedule import get_lottery_schedule

    out: dict[str, Any] = {}
    for pt in ("101", "201", "401", "301"):
        raw = get_lottery_schedule.invoke({"play_type": pt})
        data = _parse(raw)
        matches = (data.get("data") or {}).get("matches") or []
        out[pt] = {
            "code": data.get("code"),
            "count": len(matches),
            "sample_codes": [m.get("lottery_code") or m.get("code") for m in matches[:5]],
        }
    return out


def main() -> None:
    sweep = sweep_lottery_codes()
    active = sweep_active_lottery()
    ok = [r for r in sweep if r.get("code") == "OK"]

    report = {
        "diagnosed_at": today_iso(),
        "constraint": "未修改 foretell/tools；仅参数探测",
        "b01_target": {"play_type": "101", "code": "009", "date": "2026-06-15", "event": "德国 VS 库拉索"},
        "parameter_sweep": sweep,
        "ok_combinations": ok,
        "active_lottery_snapshot": active,
        "conclusion": (
            "历史场次 2026-06-15 周日009 未命中"
            if not ok
            else f"发现 {len(ok)} 组可用参数"
        ),
        "gap_type": "data_gap" if not ok else "routing_gap",
        "recommendation": (
            "上游纳米/竞彩表缺历史或编号映射；Phase2b 继续标记 B01 blocked"
            if not ok
            else "在 eval explore_b01 中采用 ok_combinations[0] 重跑"
        ),
    }
    dump_yaml(REPORT_PATH, report)
    print(f"Lottery diagnosis: {len(ok)} OK / {len(sweep)} tried -> {REPORT_PATH}")
    print(report["conclusion"])


if __name__ == "__main__":
    main()
