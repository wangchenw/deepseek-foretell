#!/usr/bin/env python3
"""Explore routes for eval types by scenario; write scenario_*.yaml entries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from route_expected import (  # noqa: E402
    STUB_TOOLS,
    expected_skill,
    expected_subagents,
    expected_tools,
    infer_fallback,
)
from route_probe_registry import TYPE_PROBES, get_probe_fn  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent.parent / "data" / "eval"
PROBE_CASES = EVAL_DIR / "probe_cases.yaml"
ROUTES_DIR = EVAL_DIR / "routes"
PROBE_RESULTS = EVAL_DIR / "probe_results"


def _load_probe_cases(scenario: str | None = None) -> list[dict]:
    data = yaml.safe_load(PROBE_CASES.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    if scenario:
        cases = [c for c in cases if c.get("scenario") == scenario.upper()]
    return cases


def _analyze_steps(steps: list[dict[str, Any]]) -> tuple[str, str, str | None]:
    """Return route_status, db_status, gap."""
    if not steps:
        return "blocked", "missing_table", "无探针步骤或未注册 probe"

    codes = [s.get("code") for s in steps]
    stubs = [s for s in steps if s.get("stub")]

    if all(c in ("OK", None) or c == "STUB_CHECK" for c in codes if c not in ("STUB",)):
        if stubs:
            return "partial", "stub", "部分工具为 stub 实现"
        if all(c == "OK" for c in codes):
            return "verified", "ok", None
        return "partial", "partial", "部分步骤非 OK"

    if any(c == "OK" for c in codes):
        return "partial", "partial", "工具链部分成功"

    return "blocked", "partial", "工具链未返回 OK"


def _gap_type(scenario: str, db_status: str, tools: list[dict[str, Any]], gap: str | None) -> str:
    if scenario == "X":
        return "routing"
    if db_status == "stub":
        return "implementation"
    tool_names = {t["name"] for t in tools}
    if tool_names & STUB_TOOLS:
        return "implementation"
    if gap and "无" in gap:
        return "data_missing"
    if db_status == "missing_table":
        return "data_missing"
    return "routing"


def _build_entry(case: dict, steps: list[dict[str, Any]], probe_error: str | None) -> dict[str, Any]:
    type_id = case["type_id"]
    scenario = case["scenario"]
    tools = expected_tools(type_id, scenario, case.get("entity_entry", ""))
    skill = expected_skill(scenario)

    if scenario == "X" and type_id not in TYPE_PROBES:
        route_status = "prompt_only"
        db_status = "ok"
        gap = "护栏/输出纪律，主要依赖 prompt 与 output-discipline skill"
        gap_type = "routing"
    elif case.get("probe_status") == "needs_manual":
        route_status = "blocked"
        db_status = "unverified_semantics"
        gap = "探针问法为占位，需人工补 probe_turns"
        gap_type = "field_unknown"
        steps = []
    elif probe_error:
        route_status = "blocked"
        db_status = "partial"
        gap = probe_error
        gap_type = "routing"
    else:
        route_status, db_status, gap = _analyze_steps(steps)
        gap_type = _gap_type(scenario, db_status, tools, gap)

    if scenario == "G" and route_status == "verified":
        route_status = "partial"
        gap = (gap or "") + "；多轮追问需 checkpointer，未跑完整 agent"

    entry: dict[str, Any] = {
        "type_id": type_id,
        "type_name": case.get("type_name", ""),
        "scenario": scenario,
        "probe_case_id": case.get("case_id"),
        "priority": case.get("priority", "P2"),
        "expected_route": {
            "skill": skill,
            "tools": tools,
            "subagents": expected_subagents(scenario, type_id),
        },
        "actual_probe": {
            "result_file": f"probe_results/{type_id}.json",
            "route_status": route_status,
            "db_status": db_status,
            "step_count": len(steps),
        },
        "gap": gap,
        "gap_type": gap_type,
        "nami_refs": [],
        "fallback": infer_fallback(scenario, tools),
        "skill_update_candidate": route_status in ("verified", "partial")
        and case.get("priority") == "P0",
        "reviewed": False,
    }
    if type_id in {"A08", "A17", "X05"}:
        entry["nami_refs"] = ["football_match.match_time", "football_team.national"]
    return entry


def explore_scenario(scenario: str, *, skip_probe: bool = False) -> list[dict]:
    cases = _load_probe_cases(scenario.upper())
    entries: list[dict] = []

    for case in cases:
        type_id = case["type_id"]
        steps: list[dict] = []
        probe_error: str | None = None

        if not skip_probe and case.get("probe_status") != "needs_manual":
            if case.get("scenario") == "X" and type_id not in TYPE_PROBES:
                pass
            else:
                probe_fn = get_probe_fn(type_id, case.get("entity_entry", ""))
                if probe_fn:
                    try:
                        steps = probe_fn()
                        PROBE_RESULTS.mkdir(parents=True, exist_ok=True)
                        probe_doc = {
                            "type_id": type_id,
                            "case_id": case.get("case_id"),
                            "steps": steps,
                        }
                        (PROBE_RESULTS / f"{type_id}.json").write_text(
                            json.dumps(probe_doc, ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                    except Exception as exc:  # noqa: BLE001
                        probe_error = str(exc)

        entries.append(_build_entry(case, steps, probe_error))

    ROUTES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ROUTES_DIR / f"scenario_{scenario.upper()}.yaml"
    doc = {
        "scenario": scenario.upper(),
        "explored": len(entries),
        "entries": entries,
    }
    with out_path.open("w", encoding="utf-8") as f:
        yaml.dump(doc, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print(f"Scenario {scenario.upper()}: {len(entries)} entries -> {out_path}")
    return entries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", help="Single scenario letter A-X")
    parser.add_argument("--all", action="store_true", help="Explore all scenarios")
    parser.add_argument("--skip-probe", action="store_true", help="Skip live DB probes")
    args = parser.parse_args()

    if args.all:
        for letter in "ABCDEFGHX":
            explore_scenario(letter, skip_probe=args.skip_probe)
    elif args.scenario:
        explore_scenario(args.scenario, skip_probe=args.skip_probe)
    else:
        parser.error("Provide --scenario X or --all")


if __name__ == "__main__":
    main()
