#!/usr/bin/env python3
"""Phase 1 Supplement: Multi-round diagnosis for failed P0 cases (B01, B09, E05, G01, G07).

Fills the gap between single-round path_attempts and full LLM eval.
Read-only: invokes foretell tools without modifying tool code.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_eval_common import EVAL_DIR, dump_yaml, load_probe_case, today_iso  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = EVAL_DIR / "phase1_supplement"

FAILED_CASES = ["B01", "B09", "E05", "G01", "G07"]

# Placeholders resolved from prior lottery schedule results in the same case run.
FROM_LOTTERY_MATCH_ID = "__from_lottery_match_id__"
FROM_LOTTERY_HOME_TEAM_ID = "__from_lottery_home_team_id__"
FROM_TODAY = "__today__"

FALLBACK_STRATEGIES: dict[str, list[dict[str, Any]]] = {
    "B01": [
        {
            "round": 1,
            "name": "resolve_lottery_match (weekday code)",
            "tools": [
                {
                    "name": "resolve_lottery_match",
                    "params": {"play_type": "101", "code": "周日009", "date": "2026-06-15"},
                }
            ],
        },
        {
            "round": 2,
            "name": "resolve_lottery_match (numeric code)",
            "tools": [
                {
                    "name": "resolve_lottery_match",
                    "params": {"play_type": "101", "code": "009", "date": "2026-06-15"},
                }
            ],
        },
        {
            "round": 3,
            "name": "resolve_lottery_match (date slash format)",
            "tools": [
                {
                    "name": "resolve_lottery_match",
                    "params": {"play_type": "101", "code": "周日009", "date": "2026/06/15"},
                }
            ],
        },
        {
            "round": 4,
            "name": "get_lottery_schedule (fall back)",
            "tools": [
                {
                    "name": "get_lottery_schedule",
                    "params": {"play_type": "101", "date": "2026-06-15"},
                }
            ],
        },
        {
            "round": 5,
            "name": "get_schedule_by_date (cross-verify)",
            "tools": [
                {
                    "name": "get_schedule_by_date",
                    "params": {"date": "2026-06-15", "tier": "all"},
                }
            ],
        },
    ],
    "B09": [
        {
            "round": 1,
            "name": "resolve_match (G7)",
            "tools": [
                {
                    "name": "resolve_match",
                    "params": {"home": "马刺", "away": "雷霆", "series_game": 7},
                }
            ],
        },
        {
            "round": 2,
            "name": "resolve_match (without series_game)",
            "tools": [
                {"name": "resolve_match", "params": {"home": "马刺", "away": "雷霆"}},
            ],
        },
        {
            "round": 3,
            "name": "get_schedule_by_date (NBA finals)",
            "tools": [
                {
                    "name": "get_schedule_by_date",
                    "params": {"date": "2026-06-15", "sport": "basketball", "league_preset": "NBA"},
                }
            ],
        },
        {
            "round": 4,
            "name": "resolve_match (city names fallback)",
            "tools": [
                {
                    "name": "resolve_match",
                    "params": {"home": "圣安东尼奥", "away": "俄克拉荷马"},
                }
            ],
        },
        {
            "round": 5,
            "name": "honest decline (G7 not in DB)",
            "tools": [],
            "recommendation": "honest_decline",
        },
    ],
    "E05": [
        {
            "round": 1,
            "name": "get_lottery_schedule (14 games)",
            "tools": [{"name": "get_lottery_schedule", "params": {"play_type": "401"}}],
        },
        {
            "round": 2,
            "name": "get_recent_form (screening)",
            "tools": [
                {
                    "name": "get_recent_form",
                    "params": {"team_id": FROM_LOTTERY_HOME_TEAM_ID},
                }
            ],
        },
        {
            "round": 3,
            "name": "get_odds_snapshot (risk disclosure)",
            "tools": [
                {
                    "name": "get_odds_snapshot",
                    "params": {"match_id": FROM_LOTTERY_MATCH_ID},
                }
            ],
        },
        {
            "round": 4,
            "name": "screening fallback (textual criteria only)",
            "tools": [],
            "recommendation": "textual_screening_only",
        },
    ],
    "G01": [
        {
            "round": 1,
            "name": "resolve_lottery_match (turn 1 full analysis)",
            "tools": [
                {
                    "name": "resolve_lottery_match",
                    "params": {"play_type": "101", "code": "004", "date": "2026-06-23"},
                }
            ],
        },
        {
            "round": 2,
            "name": "get_lottery_schedule fallback",
            "tools": [{"name": "get_lottery_schedule", "params": {"play_type": "101"}}],
        },
        {
            "round": 3,
            "name": "turn 2: maintain_context (checkpointer needed)",
            "tools": [],
            "recommendation": "need_checkpointer",
        },
        {
            "round": 4,
            "name": "turn 2: synthetic score prediction (no new tool)",
            "tools": [],
            "recommendation": "synthesize_from_turn1_context",
        },
    ],
    "G07": [
        {
            "round": 1,
            "name": "get_lottery_schedule (beidan 301)",
            "tools": [{"name": "get_lottery_schedule", "params": {"play_type": "301"}}],
        },
        {
            "round": 2,
            "name": "get_schedule_by_date (today's context)",
            "tools": [
                {
                    "name": "get_schedule_by_date",
                    "params": {"date": FROM_TODAY, "tier": "top"},
                }
            ],
        },
        {
            "round": 3,
            "name": "get_odds_snapshot (criteria 2/4/5)",
            "tools": [
                {
                    "name": "get_odds_snapshot",
                    "params": {"match_id": FROM_LOTTERY_MATCH_ID},
                }
            ],
        },
        {
            "round": 4,
            "name": "get_injury_report (criteria 4)",
            "tools": [
                {
                    "name": "get_injury_report",
                    "params": {"match_id": FROM_LOTTERY_MATCH_ID},
                }
            ],
        },
        {
            "round": 5,
            "name": "follow-up optimization (cross-session checkpointer)",
            "tools": [],
            "recommendation": "need_checkpointer",
        },
    ],
}

IMPLEMENTATION_GAP_CODES = frozenset({"DATA_MISSING", "SKIP_MATCH", "PARTIAL", "NOT_APPLICABLE"})


def _parse(raw: str) -> dict[str, Any]:
    return json.loads(raw)


def _tool_registry() -> dict[str, Any]:
    from foretell.tools.deep import get_injury_report
    from foretell.tools.entity import resolve_lottery_match, resolve_match
    from foretell.tools.odds import get_odds_snapshot
    from foretell.tools.schedule import get_lottery_schedule, get_schedule_by_date
    from foretell.tools.stats import get_recent_form

    return {
        "resolve_lottery_match": resolve_lottery_match,
        "resolve_match": resolve_match,
        "get_lottery_schedule": get_lottery_schedule,
        "get_schedule_by_date": get_schedule_by_date,
        "get_recent_form": get_recent_form,
        "get_odds_snapshot": get_odds_snapshot,
        "get_injury_report": get_injury_report,
    }


def _resolve_params(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for key, value in params.items():
        if value == FROM_LOTTERY_MATCH_ID:
            resolved[key] = ctx.get("sample_match_id")
        elif value == FROM_LOTTERY_HOME_TEAM_ID:
            resolved[key] = ctx.get("sample_home_team_id")
        elif value == FROM_TODAY:
            resolved[key] = today_iso()
        else:
            resolved[key] = value
    return resolved


def _lottery_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    payload = data.get("data") or {}
    return payload.get("entries") or payload.get("matches") or []


def _ensure_lottery_context(ctx: dict[str, Any]) -> None:
    """Derive match_id / team_id from lottery entry when raw fields are absent."""
    entry = ctx.get("lottery_sample_entry")
    if not entry:
        return

    if ctx.get("sample_match_id") is None and entry.get("home_name") and entry.get("away_name"):
        from foretell.tools.entity import resolve_match

        params: dict[str, Any] = {
            "home": entry["home_name"],
            "away": entry["away_name"],
        }
        if entry.get("date"):
            params["date"] = entry["date"]
        try:
            data = _parse(resolve_match.invoke(params))
        except Exception:  # noqa: BLE001
            data = {}
        if data.get("code") == "OK":
            candidates = (data.get("data") or {}).get("candidates") or []
            if candidates:
                ctx["sample_match_id"] = candidates[0].get("match_id")
                ctx["sample_home_team_id"] = candidates[0].get("home_team_id")

    if ctx.get("sample_home_team_id") is None and entry.get("home_name"):
        from foretell.tools.entity import resolve_team

        try:
            data = _parse(resolve_team.invoke({"name": entry["home_name"]}))
        except Exception:  # noqa: BLE001
            data = {}
        if data.get("code") == "OK":
            candidates = (data.get("data") or {}).get("candidates") or []
            if candidates:
                ctx["sample_home_team_id"] = candidates[0].get("team_id")

    if ctx.get("sample_match_id") is None:
        schedule_matches = ctx.get("schedule_sample_matches") or []
        if schedule_matches:
            first = schedule_matches[0]
            ctx["sample_match_id"] = first.get("match_id")
            ctx["sample_home_team_id"] = ctx.get("sample_home_team_id") or first.get("home_team_id")


def _update_context_from_result(tool_name: str, data: dict[str, Any], ctx: dict[str, Any]) -> None:
    if tool_name == "get_lottery_schedule" and data.get("code") == "OK":
        entries = _lottery_entries(data)
        if entries:
            first = entries[0]
            ctx["lottery_sample_entry"] = first
            ctx["sample_match_id"] = first.get("match_id")
            ctx["sample_home_team_id"] = first.get("home_team_id")
            ctx["lottery_count"] = len(entries)
            _ensure_lottery_context(ctx)
    elif tool_name == "get_schedule_by_date" and data.get("code") == "OK":
        matches = (data.get("data") or {}).get("matches") or []
        if matches:
            ctx["schedule_sample_matches"] = matches
            if ctx.get("sample_match_id") is None:
                ctx["sample_match_id"] = matches[0].get("match_id")
                ctx["sample_home_team_id"] = ctx.get("sample_home_team_id") or matches[0].get("home_team_id")
    elif tool_name == "resolve_lottery_match" and data.get("code") == "OK":
        ctx["sample_match_id"] = data.get("match_id") or (data.get("data") or {}).get("match_id")
    elif tool_name == "resolve_match" and data.get("code") == "OK":
        payload = data.get("data") or {}
        candidates = payload.get("candidates") or []
        if candidates:
            ctx["sample_match_id"] = candidates[0].get("match_id")
            ctx["sample_home_team_id"] = candidates[0].get("home_team_id")


def _attempt_summary(data: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {"code": data.get("code", "ERROR")}
    payload = data.get("data") or {}
    if "count" in payload:
        summary["count"] = payload["count"]
    if data.get("match_id") is not None:
        summary["match_id"] = data.get("match_id")
    candidates = payload.get("candidates") or []
    if candidates:
        summary["count"] = len(candidates)
    return summary


def invoke_tool(tool_name: str, params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    registry = _tool_registry()
    tool = registry.get(tool_name)
    if tool is None:
        return {"code": "ERROR", "message": f"Unknown tool: {tool_name}"}

    resolved = _resolve_params(params, ctx)
    if any(
        params.get(k) in {FROM_LOTTERY_MATCH_ID, FROM_LOTTERY_HOME_TEAM_ID}
        for k in params
    ):
        _ensure_lottery_context(ctx)
        resolved = _resolve_params(params, ctx)
    if None in resolved.values():
        missing = [k for k, v in resolved.items() if v is None]
        return {
            "code": "CONTEXT_MISSING",
            "message": f"Cannot resolve params {missing}; run lottery schedule first",
            "params": resolved,
        }

    try:
        raw = tool.invoke(resolved)
        data = _parse(raw)
    except Exception as exc:  # noqa: BLE001
        return {"code": "ERROR", "message": str(exc), "params": resolved}

    _update_context_from_result(tool_name, data, ctx)
    attempt = {"tool": tool_name, "params": resolved, **_attempt_summary(data)}
    if data.get("code") != "OK":
        payload = data.get("data") or {}
        if payload.get("reason"):
            attempt["reason"] = payload["reason"]
    return attempt


def _infer_root_cause(
    case_id: str,
    ok_rounds: int,
    blocked_rounds: int,
    impl_gap_rounds: int,
    no_tool_rounds: list[dict[str, Any]],
) -> tuple[str, str]:
    recommendations = [r.get("recommendation") for r in no_tool_rounds if r.get("recommendation")]
    if any(r in {"need_checkpointer", "synthesize_from_turn1_context"} for r in recommendations):
        fix = "wire_checkpointer_for_multi_turn; see phase2a_checkpointer_demo.yaml"
        if impl_gap_rounds > 0 and case_id == "G07":
            fix += "; backfill_injury_report_for_screening_criteria"
        return "context_gap", fix
    if any(r == "honest_decline" for r in recommendations) and ok_rounds == 0:
        return "data_gap", "honest_decline_series_game_not_in_db"
    if impl_gap_rounds > 0 and case_id in {"E05", "G07"}:
        return "implementation_gap", "implement_or_backfill_odds_form_injury_for_screening"
    if ok_rounds >= 2:
        return "routing_or_parameter_gap", "adjust_params_or_fallback_path"
    if impl_gap_rounds > 0:
        return "implementation_gap", "implement_or_backfill_deep_tools"
    return "data_gap", "upstream_data_quality_or_mapping"


def diagnose_case(case_id: str, strategies: list[dict[str, Any]]) -> dict[str, Any]:
    probe = load_probe_case(case_id) or {}
    logger.info("\n%s", "=" * 60)
    logger.info("Diagnosing %s: %d rounds", case_id, len(strategies))
    logger.info("%s", "=" * 60)

    ctx: dict[str, Any] = {}
    results: dict[str, Any] = {
        "type_id": case_id,
        "case_id": probe.get("case_id"),
        "diagnosed_at": today_iso(),
        "rounds": [],
    }

    ok_rounds = 0
    blocked_rounds = 0
    impl_gap_rounds = 0
    no_tool_rounds: list[dict[str, Any]] = []

    for strategy in strategies:
        round_num = strategy["round"]
        round_name = strategy["name"]
        tools = strategy.get("tools") or []

        logger.info("\nRound %d: %s", round_num, round_name)

        round_result: dict[str, Any] = {
            "round": round_num,
            "name": round_name,
            "tools_attempted": len(tools),
            "attempts": [],
        }
        if strategy.get("recommendation"):
            round_result["recommendation"] = strategy["recommendation"]

        if not tools:
            round_result["result"] = "no_tool_available"
            logger.info("  -> No tool; recommendation=%s", strategy.get("recommendation", "n/a"))
            results["rounds"].append(round_result)
            no_tool_rounds.append(round_result)
            blocked_rounds += 1
            continue

        round_ok = False
        round_impl_gap = False
        for tool in tools:
            tool_name = tool["name"]
            tool_params = tool["params"]
            logger.info("  Tool: %s | Params: %s", tool_name, tool_params)

            attempt = invoke_tool(tool_name, tool_params, ctx)
            round_result["attempts"].append(attempt)

            code = attempt.get("code", "ERROR")
            if code == "OK":
                logger.info("    OK (count=%s)", attempt.get("count", 1))
                round_ok = True
            elif code in IMPLEMENTATION_GAP_CODES:
                logger.info("    %s (implementation/data partial)", code)
                round_impl_gap = True
            else:
                logger.info("    %s", code)

        if round_ok:
            round_result["result"] = "OK"
            ok_rounds += 1
        elif round_impl_gap:
            round_result["result"] = "IMPLEMENTATION_GAP"
            impl_gap_rounds += 1
            blocked_rounds += 1
        else:
            round_result["result"] = round_result["attempts"][-1].get("code", "ERROR") if round_result["attempts"] else "ERROR"
            blocked_rounds += 1

        results["rounds"].append(round_result)

    root_cause, recommended_fix = _infer_root_cause(
        case_id, ok_rounds, blocked_rounds, impl_gap_rounds, no_tool_rounds
    )
    results["summary"] = {
        "ok_rounds": ok_rounds,
        "blocked_rounds": blocked_rounds,
        "implementation_gap_rounds": impl_gap_rounds,
        "no_tool_rounds": len(no_tool_rounds),
        "total_rounds": len(strategies),
    }
    results["root_cause"] = root_cause
    results["recommended_fix"] = recommended_fix
    if ctx.get("sample_match_id"):
        results["sample_ids"] = {
            "match_id": ctx.get("sample_match_id"),
            "home_team_id": ctx.get("sample_home_team_id"),
        }

    logger.info("\n[Diagnosis] %s", case_id)
    logger.info("  OK: %d | Blocked: %d | Impl gap: %d", ok_rounds, blocked_rounds, impl_gap_rounds)
    logger.info("  Root cause: %s", root_cause)
    logger.info("  Recommended fix: %s", recommended_fix)

    return results


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results: dict[str, Any] = {
        "meta": {
            "phase": "phase1_supplement",
            "diagnosed_cases": FAILED_CASES,
            "supplement_date": today_iso(),
            "purpose": "multi-round diagnosis for failed P0 cases",
            "constraint": "read-only foretell tool invocation; no path_attempts overwrite",
        },
        "cases": [],
    }

    for case_id in FAILED_CASES:
        strategies = FALLBACK_STRATEGIES.get(case_id, [])
        result = diagnose_case(case_id, strategies)
        all_results["cases"].append(result)

        case_file = OUTPUT_DIR / f"{case_id}_supplement.yaml"
        dump_yaml(case_file, result)
        logger.info("  -> Saved to %s", case_file)

    summary_file = OUTPUT_DIR / "supplement_summary.yaml"
    dump_yaml(summary_file, all_results)

    logger.info("\n%s", "=" * 60)
    logger.info("Supplement complete -> %s", summary_file)
    logger.info("%s", "=" * 60)

    print("\n[Phase 1 Supplement Summary]")
    print("+---------+-------------------------+------------------------------------------+")
    print("| Type_ID | Root Cause              | Recommended Fix                          |")
    print("+---------+-------------------------+------------------------------------------+")
    for case in all_results["cases"]:
        tid = case["type_id"]
        root = (case.get("root_cause") or "unknown")[:23]
        rec = (case.get("recommended_fix") or "unknown")[:40]
        print(f"| {tid:7s} | {root:23s} | {rec:40s} |")
    print("+---------+-------------------------+------------------------------------------+")


if __name__ == "__main__":
    main()
