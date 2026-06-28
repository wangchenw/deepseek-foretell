#!/usr/bin/env python3
"""Auto decision tree: Phase 1 results -> Phase 2a route."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_eval_common import EVAL_DIR, P0_TYPE_IDS, PLAYBOOKS_PATH, load_yaml  # noqa: E402

DECISION_PATH = EVAL_DIR / "phase2_decision.json"


def load_phase1_results() -> dict[str, dict[str, Any]]:
    playbooks = load_yaml(PLAYBOOKS_PATH)
    by_id = {e["type_id"]: e for e in playbooks.get("entries", [])}
    path_dir = EVAL_DIR / "path_attempts"
    results: dict[str, dict[str, Any]] = {}
    for tid in P0_TYPE_IDS:
        pb = by_id.get(tid, {})
        ev = pb.get("llm_eval", {})
        path_file = path_dir / f"{tid}.yaml"
        path_data = load_yaml(path_file) if path_file.exists() else {}
        blocking = path_data.get("blocking_gap") or {}
        gaps = pb.get("gaps") or []
        first_gap = gaps[0] if gaps else None
        if isinstance(first_gap, dict):
            gap_from_pb = first_gap.get("gap_type") or first_gap.get("detail", "")
        elif isinstance(first_gap, str):
            gap_from_pb = first_gap
        else:
            gap_from_pb = ""
        gap_type = blocking.get("type")
        if not gap_type and gap_from_pb:
            for prefix in ("data_gap", "routing_gap", "implementation_gap", "pipeline_gap"):
                if prefix in gap_from_pb:
                    gap_type = prefix
                    break
        results[tid] = {
            "pass": ev.get("pass", False),
            "overall": ev.get("overall"),
            "gap_type": gap_type,
            "gap_detail": blocking.get("description") or gap_from_pb,
            "route_complete": path_data.get("route_complete"),
        }
    return results


def decide(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ax_pass = all(results[t]["pass"] for t in ("A08", "A17", "X05", "X06", "X12") if t in results)

    lottery_types = ("B01", "B09", "E05")
    lottery_fail = sum(1 for t in lottery_types if t in results and not results[t]["pass"])
    b01_lottery_gap = (
        not results.get("B01", {}).get("pass", True)
        and results.get("B01", {}).get("gap_type") == "data_gap"
        and "resolve_lottery_match" in (results.get("B01", {}).get("gap_detail") or "")
    )

    g_types = ("G01", "G07")
    g_fail = all(not results[t]["pass"] for t in g_types if t in results)
    g_checkpointer = any(
        "checkpointer" in (results[t].get("gap_detail") or "").lower()
        or results[t].get("gap_type") == "pipeline_gap"
        for t in g_types
        if t in results
    )

    # Trigger A: lottery series
    if lottery_fail >= 2 and b01_lottery_gap:
        route = "Phase_2a_lottery"
        reason = f"竞彩系列 {lottery_fail}/3 失败且 B01 resolve_lottery_match data_gap"
    elif g_fail and g_checkpointer and lottery_fail < 3:
        route = "Phase_2a_checkpointer"
        reason = "G01/G07 全失败且 checkpointer 缺口；竞彩非主因"
    elif ax_pass and lottery_fail >= 1:
        route = "Phase_2a_priority_order"
        reason = "A/X 全通；混合 gap，按优先序：竞彩→checkpointer→stub"
    elif ax_pass:
        route = "Phase_2b"
        reason = "A/X 全通且无单一阻塞 gap，跳过 2a"
    else:
        route = "Phase_2a_priority_order"
        reason = "默认混合路径：竞彩→checkpointer→stub"

    return {
        "phase1_complete": True,
        "ax_all_pass": ax_pass,
        "lottery_fail_count": lottery_fail,
        "g_all_fail": g_fail,
        "selected_route": route,
        "reason": reason,
        "next_steps": _next_steps(route),
        "p0_results": results,
    }


def _next_steps(route: str) -> list[str]:
    if route == "Phase_2a_lottery":
        return [
            "phase2a_lottery_diagnose.py",
            "rerun B01/B09/E05 path if param found",
            "Phase_2b run_llm_eval_full.py",
        ]
    if route == "Phase_2a_checkpointer":
        return ["eval_checkpointer_demo.py", "rerun G01/G07", "Phase_2b"]
    if route == "Phase_2a_priority_order":
        return ["phase2a_lottery_diagnose.py", "eval_checkpointer_demo.py", "Phase_2b"]
    return ["run_llm_eval_full.py"]


def main() -> None:
    results = load_phase1_results()
    decision = decide(results)
    DECISION_PATH.write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Decision: {decision['selected_route']}")
    print(f"Reason: {decision['reason']}")
    print(f"Saved -> {DECISION_PATH}")


if __name__ == "__main__":
    main()
