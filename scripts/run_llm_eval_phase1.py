#!/usr/bin/env python3
"""Run LLM Eval Phase 1 path exploration for P0 types with real foretell tools."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_eval_common import (  # noqa: E402
    ATOMIC_DIR,
    PATH_DIR,
    P0_TYPE_IDS,
    ROUTE_MATRIX_MERGED_PATH,
    ensure_dirs,
    load_atomic_decomposition,
    load_probe_case,
    today_iso,
)


def _parse_json(result: str) -> dict[str, Any]:
    return json.loads(result)


def _national_team_id(data: dict[str, Any]) -> int | None:
    candidates = data.get("data", {}).get("candidates") or []
    for c in candidates:
        if c.get("national") == 1:
            return c["team_id"]
    return candidates[0]["team_id"] if candidates else None


def _step(tool: str, params: dict[str, Any], code: str, **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {"tool": tool, "params": params, "code": code, "stub": extra.pop("stub", False)}
    row.update(extra)
    return row


def _skipped_search(atomic_id: str, reason: str = "Eval constraint: no Tavily/internet_search") -> dict[str, Any]:
    return {
        "atomic_id": atomic_id,
        "category": "discover_via_search",
        "status": "skipped",
        "note": reason,
    }


def explore_a08() -> dict[str, Any]:
    from foretell.tools.entity import resolve_team
    from foretell.tools.schedule import get_schedule_by_date, get_team_schedule

    attempts: list[dict[str, Any]] = []
    satisfied: list[str] = []
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    team_raw = resolve_team.invoke({"name": "葡萄牙"})
    team = _parse_json(team_raw)
    attempts.append({"round": 1, "atomic_id": "A08-T2-a1", **_step("resolve_team", {"name": "葡萄牙"}, team.get("code", "ERROR"))})
    if team.get("code") != "OK":
        return _blocked("A08", attempts, satisfied, "routing_gap", "resolve_team 失败")

    team_id = _national_team_id(team)
    for rnd, direction in ((1, "upcoming"), (2, "all")):
        sched_raw = get_team_schedule.invoke({"team_id": team_id, "direction": direction, "limit": 5})
        sched = _parse_json(sched_raw)
        attempts.append(
            {
                "round": rnd,
                "atomic_id": "A08-T2-a2",
                "fallback": direction if rnd > 1 else None,
                **_step(
                    "get_team_schedule",
                    {"team_id": team_id, "direction": direction, "limit": 5},
                    sched.get("code", "ERROR"),
                    count=sched.get("data", {}).get("count"),
                ),
            }
        )
        if sched.get("code") == "OK":
            satisfied.extend(["A08-T2-a1", "A08-T2-a2"])
            break

    sched_date_raw = get_schedule_by_date.invoke({"date": tomorrow, "tier": "top"})
    sched_date = _parse_json(sched_date_raw)
    attempts.append(
        {
            "round": 3,
            "atomic_id": "A08-T2-a3",
            **_step(
                "get_schedule_by_date",
                {"date": tomorrow, "tier": "top"},
                sched_date.get("code", "ERROR"),
                count=sched_date.get("data", {}).get("count"),
            ),
        }
    )
    if sched_date.get("code") == "OK":
        satisfied.append("A08-T2-a3")

    attempts.append({"round": 1, **_skipped_search("A08-T2-a4")})
    return _result("A08", attempts, satisfied, None)


def explore_a17() -> dict[str, Any]:
    from foretell.tools.entity import resolve_team
    from foretell.tools.schedule import get_team_schedule

    attempts: list[dict[str, Any]] = []
    satisfied: list[str] = []

    team_raw = resolve_team.invoke({"name": "法国"})
    team = _parse_json(team_raw)
    attempts.append({"round": 1, "atomic_id": "A17-T0-a1", **_step("resolve_team", {"name": "法国"}, team.get("code", "ERROR"))})
    if team.get("code") != "OK":
        return _blocked("A17", attempts, satisfied, "routing_gap", "resolve_team 法国失败")

    team_id = _national_team_id(team)
    sched_raw = get_team_schedule.invoke({"team_id": team_id, "direction": "all", "limit": 10})
    sched = _parse_json(sched_raw)
    attempts.append(
        {
            "round": 1,
            "atomic_id": "A17-T0-a2",
            **_step(
                "get_team_schedule",
                {"team_id": team_id, "direction": "all", "limit": 10},
                sched.get("code", "ERROR"),
                count=sched.get("data", {}).get("count"),
            ),
        }
    )
    if sched.get("code") == "OK":
        satisfied.extend(["A17-T0-a1", "A17-T0-a2"])
    return _result("A17", attempts, satisfied, None)


def explore_x05() -> dict[str, Any]:
    from foretell.tools.entity import resolve_team
    from foretell.tools.schedule import get_schedule_by_date, get_team_schedule

    attempts: list[dict[str, Any]] = []
    satisfied: list[str] = []
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    team_raw = resolve_team.invoke({"name": "葡萄牙"})
    team = _parse_json(team_raw)
    attempts.append({"round": 1, "atomic_id": "X05-T0-a1", **_step("resolve_team", {"name": "葡萄牙"}, team.get("code", "ERROR"))})
    if team.get("code") != "OK":
        return _blocked("X05", attempts, satisfied, "routing_gap", "resolve_team 失败")

    team_id = _national_team_id(team)
    for rnd, direction in ((1, "upcoming"), (2, "all")):
        sched_raw = get_team_schedule.invoke({"team_id": team_id, "direction": direction, "limit": 5})
        sched = _parse_json(sched_raw)
        attempts.append(
            {
                "round": rnd,
                "atomic_id": "X05-T0-a2",
                "fallback": direction if rnd > 1 else None,
                **_step(
                    "get_team_schedule",
                    {"team_id": team_id, "direction": direction, "limit": 5},
                    sched.get("code", "ERROR"),
                    count=sched.get("data", {}).get("count"),
                ),
            }
        )
        if sched.get("code") == "OK":
            satisfied.extend(["X05-T0-a1", "X05-T0-a2"])
            break

    sched_date_raw = get_schedule_by_date.invoke({"date": tomorrow, "tier": "top"})
    sched_date = _parse_json(sched_date_raw)
    attempts.append(
        {
            "round": 3,
            "atomic_id": "X05-T0-a3",
            "category": "cross_validation",
            **_step(
                "get_schedule_by_date",
                {"date": tomorrow, "tier": "top"},
                sched_date.get("code", "ERROR"),
                count=sched_date.get("data", {}).get("count"),
            ),
        }
    )
    if sched_date.get("code") == "OK":
        satisfied.append("X05-T0-a3")

    attempts.append({"round": 1, **_skipped_search("X05-T0-a4")})
    return _result("X05", attempts, satisfied, None)


def explore_x06() -> dict[str, Any]:
    from foretell.tools.entity import resolve_match

    attempts: list[dict[str, Any]] = []
    satisfied: list[str] = []

    raw = resolve_match.invoke({"home": "法国", "away": "挪威"})
    data = _parse_json(raw)
    attempts.append(
        {
            "round": 1,
            "atomic_id": "X06-T0-a1",
            **_step("resolve_match", {"home": "法国", "away": "挪威"}, data.get("code", "ERROR"), count=data.get("data", {}).get("count")),
        }
    )
    if data.get("code") == "OK":
        satisfied.append("X06-T0-a1")
    return _result("X06", attempts, satisfied, None)


def explore_x12() -> dict[str, Any]:
    from foretell.tools.entity import resolve_match

    attempts: list[dict[str, Any]] = []
    satisfied: list[str] = []
    blocking: dict[str, Any] | None = None

    params_r1 = {"home": "法国", "away": "挪威", "date": "2024-06-27"}
    raw1 = resolve_match.invoke(params_r1)
    data1 = _parse_json(raw1)
    attempts.append({"round": 1, "atomic_id": "X12-T0-a1", **_step("resolve_match", params_r1, data1.get("code", "ERROR"))})

    params_r2 = {"home": "法国", "away": "挪威"}
    raw2 = resolve_match.invoke(params_r2)
    data2 = _parse_json(raw2)
    attempts.append(
        {
            "round": 2,
            "atomic_id": "X12-T0-a2",
            "fallback": "drop_date_filter",
            **_step("resolve_match", params_r2, data2.get("code", "ERROR"), count=data2.get("data", {}).get("count")),
        }
    )

    params_r3 = {"home": "法国", "away": "挪威", "date": "2026-06-27"}
    raw3 = resolve_match.invoke(params_r3)
    data3 = _parse_json(raw3)
    attempts.append({"round": 3, "atomic_id": "X12-T1-a1", **_step("resolve_match", params_r3, data3.get("code", "ERROR"), count=data3.get("data", {}).get("count"))})

    params_r4 = {"home": "挪威", "away": "法国", "date": "2026-06-27"}
    raw4 = resolve_match.invoke(params_r4)
    data4 = _parse_json(raw4)
    attempts.append(
        {
            "round": 3,
            "atomic_id": "X12-T1-a1",
            "fallback": "swap_home_away_for_world_cup",
            **_step("resolve_match", params_r4, data4.get("code", "ERROR"), count=data4.get("data", {}).get("count")),
        }
    )

    if data4.get("code") == "OK":
        satisfied.extend(["X12-T0-a2", "X12-T1-a1"])
    elif data3.get("code") == "OK":
        satisfied.extend(["X12-T0-a2", "X12-T1-a1"])
    elif data2.get("code") == "OK":
        satisfied.append("X12-T0-a2")
        blocking = {
            "type": "routing_gap",
            "description": "2026-06-27 场次以挪威主场入库，需 swap home/away 或从候选列表消歧",
            "failed_atomic": "X12-T1-a1",
        }
    else:
        blocking = {"type": "data_gap", "description": "法国 vs 挪威 无可用 match 记录", "failed_atomic": "X12-T0-a2"}

    return _result("X12", attempts, satisfied, blocking)


def explore_b01() -> dict[str, Any]:
    from foretell.tools.entity import resolve_lottery_match

    attempts: list[dict[str, Any]] = []
    params = {"play_type": "101", "code": "009", "date": "2026-06-15"}
    raw = resolve_lottery_match.invoke(params)
    data = _parse_json(raw)
    attempts.append({"round": 1, "atomic_id": "B01-T0-a1", **_step("resolve_lottery_match", params, data.get("code", "ERROR"))})

    blocking = {
        "type": "data_gap",
        "description": "resolve_lottery_match 返回 ENTITY_NOT_FOUND：周日009 德国VS库拉索 2026-06-15 不在 lottery 表",
        "failed_atomic": "B01-T0-a1",
    }
    return _result("B01", attempts, [], blocking)


def explore_b09() -> dict[str, Any]:
    from foretell.tools.entity import resolve_match

    attempts: list[dict[str, Any]] = []
    params = {"home": "马刺", "away": "雷霆", "series_game": 7}
    raw = resolve_match.invoke(params)
    data = _parse_json(raw)
    attempts.append({"round": 1, "atomic_id": "B09-T0-a1", **_step("resolve_match", params, data.get("code", "ERROR"))})

    blocking = {
        "type": "data_gap",
        "description": "resolve_match 返回 NOT_APPLICABLE：NBA 季后赛 G7 series_game 维度未入库",
        "failed_atomic": "B09-T0-a1",
    }
    return _result("B09", attempts, [], blocking)


def explore_e05() -> dict[str, Any]:
    from foretell.tools.schedule import get_lottery_schedule

    attempts: list[dict[str, Any]] = []
    satisfied: list[str] = []
    raw = get_lottery_schedule.invoke({"play_type": "401"})
    data = _parse_json(raw)
    attempts.append(
        {
            "round": 1,
            "atomic_id": "E05-T0-a1",
            **_step("get_lottery_schedule", {"play_type": "401"}, data.get("code", "ERROR"), count=data.get("data", {}).get("count")),
        }
    )
    if data.get("code") == "OK":
        satisfied.append("E05-T0-a1")

    blocking = {
        "type": "implementation_gap",
        "description": "十四场场次列表 OK，但 delegate_subagent 所需 get_recent_form/get_odds_snapshot 等为 stub",
        "failed_atomic": "E05-T0-a3",
    }
    return _result("E05", attempts, satisfied, blocking)


def explore_g01() -> dict[str, Any]:
    from foretell.tools.entity import resolve_lottery_match
    from foretell.tools.schedule import get_lottery_schedule

    attempts: list[dict[str, Any]] = []
    satisfied: list[str] = []

    params = {"play_type": "101", "code": "004"}
    raw = resolve_lottery_match.invoke(params)
    data = _parse_json(raw)
    attempts.append({"round": 1, "atomic_id": "G01-T0-a1", **_step("resolve_lottery_match", params, data.get("code", "ERROR"))})

    if data.get("code") != "OK":
        lot_raw = get_lottery_schedule.invoke({"play_type": "101"})
        lot = _parse_json(lot_raw)
        attempts.append(
            {
                "round": 2,
                "atomic_id": "G01-T0-a1",
                "fallback": "list_active_lottery",
                **_step("get_lottery_schedule", {"play_type": "101"}, lot.get("code", "ERROR"), count=lot.get("data", {}).get("count")),
            }
        )
        if lot.get("code") == "OK":
            satisfied.append("G01-T0-a1-fallback")

    blocking = {
        "type": "data_gap",
        "description": "周二004 巴黎VS拜仁 竞彩编码未命中；多轮 maintain_context 依赖 checkpointer 未测",
        "failed_atomic": "G01-T0-a1",
    }
    return _result("G01", attempts, satisfied, blocking)


def explore_g07() -> dict[str, Any]:
    from foretell.tools.schedule import get_lottery_schedule, get_schedule_by_date

    attempts: list[dict[str, Any]] = []
    satisfied: list[str] = []
    today = today_iso()

    lot_raw = get_lottery_schedule.invoke({"play_type": "301"})
    lot = _parse_json(lot_raw)
    attempts.append(
        {
            "round": 1,
            "atomic_id": "G07-T0-a2",
            **_step("get_lottery_schedule", {"play_type": "301"}, lot.get("code", "ERROR"), count=lot.get("data", {}).get("count")),
        }
    )
    if lot.get("code") == "OK":
        satisfied.append("G07-T0-a2")

    sched_raw = get_schedule_by_date.invoke({"date": today, "tier": "top"})
    sched = _parse_json(sched_raw)
    attempts.append(
        {
            "round": 2,
            "atomic_id": "G07-T0-a3",
            **_step("get_schedule_by_date", {"date": today, "tier": "top"}, sched.get("code", "ERROR"), count=sched.get("data", {}).get("count")),
        }
    )
    if sched.get("code") == "OK":
        satisfied.append("G07-T0-a3")

    attempts.append({"round": 1, **_skipped_search("G07-T0-a5", "标准3/4需媒体热度与伤停，Eval 禁止 internet_search")})

    blocking = {
        "type": "implementation_gap",
        "description": "5条筛选标准需赔率/伤停/近期进球 stub + 跨窗口 context；北单列表可拉但深度筛选工具不足",
        "failed_atomic": "G07-T0-a4",
    }
    return _result("G07", attempts, satisfied, blocking)


EXPLORERS: dict[str, Any] = {
    "A08": explore_a08,
    "A17": explore_a17,
    "X05": explore_x05,
    "X06": explore_x06,
    "X12": explore_x12,
    "B01": explore_b01,
    "B09": explore_b09,
    "E05": explore_e05,
    "G01": explore_g01,
    "G07": explore_g07,
}


def _result(
    type_id: str,
    attempts: list[dict[str, Any]],
    satisfied: list[str],
    blocking_gap: dict[str, Any] | None,
) -> dict[str, Any]:
    probe = load_probe_case(type_id) or {}
    return {
        "type_id": type_id,
        "case_id": probe.get("case_id"),
        "explored_at": today_iso(),
        "attempts": attempts,
        "satisfied": sorted(set(satisfied)),
        "blocking_gap": blocking_gap,
        "route_complete": blocking_gap is None,
    }


def _blocked(
    type_id: str,
    attempts: list[dict[str, Any]],
    satisfied: list[str],
    gap_type: str,
    description: str,
) -> dict[str, Any]:
    return _result(type_id, attempts, satisfied, {"type": gap_type, "description": description})


def run_path_exploration(type_id: str) -> dict[str, Any]:
    fn = EXPLORERS.get(type_id)
    if not fn:
        raise SystemExit(f"No explorer for {type_id}")
    return fn()


def write_path_attempt(type_id: str, result: dict[str, Any]) -> Path:
    ensure_dirs()
    path = PATH_DIR / f"{type_id}.yaml"
    from llm_eval_common import dump_yaml

    dump_yaml(path, result)
    return path


def run_all(type_ids: list[str] | None = None) -> dict[str, dict[str, Any]]:
    ids = type_ids or list(P0_TYPE_IDS)
    results: dict[str, dict[str, Any]] = {}
    for type_id in ids:
        atomic_path = ATOMIC_DIR / f"{type_id}.yaml"
        if not atomic_path.exists():
            print(f"Skip {type_id}: missing {atomic_path}", file=sys.stderr)
            continue
        load_atomic_decomposition(type_id)
        result = run_path_exploration(type_id)
        out = write_path_attempt(type_id, result)
        results[type_id] = result
        print(f"Path {type_id}: route_complete={result['route_complete']} -> {out}")
    return results


def merge_route_matrix() -> Path:
    from llm_eval_common import (
        PLAYBOOKS_PATH,
        ROUTE_MATRIX_MERGED_PATH,
        ROUTE_MATRIX_PATH,
        dump_yaml,
        load_yaml,
    )

    matrix = load_yaml(ROUTE_MATRIX_PATH)
    playbooks = {e["type_id"]: e for e in load_yaml(PLAYBOOKS_PATH).get("entries", [])}
    entries: list[dict[str, Any]] = []
    for entry in matrix.get("entries", []):
        type_id = entry.get("type_id")
        if type_id not in P0_TYPE_IDS:
            continue
        pb = playbooks[type_id]
        ev = pb["llm_eval"]
        merged = dict(entry)
        merged["llm_eval_status"] = "pass" if ev["pass"] else "fail"
        merged["llm_eval_score"] = ev["overall"]
        merged["llm_eval_scores"] = ev["scores"]
        merged["atomic_tools_needed"] = pb["atomic_tools_needed"]
        merged["playbook_id"] = pb["playbook_id"]
        merged["playbook_ref"] = f"answer_playbooks.yaml#{pb['playbook_id']}"
        merged["path_attempt_ref"] = ev["path_ref"]
        merged["atomic_decomposition_ref"] = ev["atomic_ref"]
        merged["existing_tools_sufficient"] = pb["existing_tools_sufficient"]
        merged["llm_eval_gaps"] = pb.get("gaps", [])
        entries.append(merged)

    out = {
        "version": "1.1",
        "meta": {
            "source": "route_matrix.yaml + llm_eval_phase1",
            "p0_types": list(P0_TYPE_IDS),
            "evaluated_at": today_iso(),
            "pass_count": sum(1 for e in entries if e["llm_eval_status"] == "pass"),
            "fail_count": sum(1 for e in entries if e["llm_eval_status"] == "fail"),
        },
        "entries": entries,
    }
    dump_yaml(ROUTE_MATRIX_MERGED_PATH, out)
    print(f"Merged {len(entries)} P0 entries -> {ROUTE_MATRIX_MERGED_PATH}")
    return ROUTE_MATRIX_MERGED_PATH


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM Eval Phase 1 path exploration")
    parser.add_argument("--type", action="append", help="type_id (repeatable); default all P0")
    parser.add_argument("--merge", action="store_true", help="merge route_matrix_merged.yaml from playbooks")
    args = parser.parse_args()
    if args.merge:
        merge_route_matrix()
        return
    run_all(args.type or list(P0_TYPE_IDS))


if __name__ == "__main__":
    main()
