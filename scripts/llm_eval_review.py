"""Heuristic review scoring from path exploration results (LLM-eval surrogate)."""

from __future__ import annotations

from typing import Any

from llm_eval_common import (
    DIMENSION_THRESHOLD,
    LLM_EVAL_DIMENSIONS,
    OVERALL_THRESHOLD,
    load_probe_case,
    load_test_case,
    p0_pass,
    weighted_overall,
)


def score_from_path_result(
    type_id: str,
    path_result: dict[str, Any],
    *,
    scenario: str | None = None,
) -> dict[str, Any]:
    """Derive rubric scores from path_attempts structure without calling LLM."""
    probe = load_probe_case(type_id) or {}
    test = load_test_case(type_id) or {}
    scenario = scenario or probe.get("scenario", "A")
    blocking = path_result.get("blocking_gap")
    route_complete = path_result.get("route_complete", False)
    attempts = path_result.get("attempts") or []

    codes = [a.get("code") for a in attempts if isinstance(a, dict) and a.get("code")]
    ok_count = sum(1 for c in codes if c == "OK")
    has_skipped_search = any(a.get("status") == "skipped" for a in attempts if isinstance(a, dict))

    scores: dict[str, float] = {
        "correctness": 3.5,
        "completeness": 3.5,
        "no_false_negative": 3.5,
        "path_efficiency": 3.5,
        "output_discipline": 3.5,
        "context_handling": 3.0,
        "scenario_compliance": 3.5,
    }

    if route_complete and not blocking:
        scores["correctness"] = 4.5
        scores["completeness"] = 4.0 if scenario in {"A", "H"} else 3.8
        scores["no_false_negative"] = 4.5 if type_id in {"A08", "X05"} or scenario == "X" else 4.0
        scores["path_efficiency"] = 4.0 if len(attempts) <= 5 else 3.5
        scores["output_discipline"] = 4.5 if scenario == "X" else 4.0
        scores["context_handling"] = 3.5 if scenario == "G" else 4.0
        scores["scenario_compliance"] = 4.0
    elif blocking:
        gap_type = blocking.get("type", "routing_gap")
        scores["correctness"] = 2.5 if gap_type == "data_gap" else 3.0
        scores["completeness"] = 2.5
        scores["no_false_negative"] = 2.0 if type_id in {"X05", "A08"} else 3.0
        scores["path_efficiency"] = 3.0 if ok_count > 0 else 2.0
        scores["output_discipline"] = 4.0 if scenario == "X" else 3.0
        scores["context_handling"] = 2.0 if scenario == "G" else 3.0
        scores["scenario_compliance"] = 2.5 if gap_type == "implementation_gap" else 3.0
        if ok_count > 0:
            scores["correctness"] += 0.3
            scores["path_efficiency"] += 0.3

    if probe.get("probe_status") == "needs_manual":
        scores["completeness"] = 2.0
        scores["correctness"] = 2.0

    if scenario == "G":
        scores["context_handling"] = 2.5 if blocking else 3.5
        if "checkpointer" in (blocking or {}).get("description", "").lower():
            scores["context_handling"] = 2.0

    if has_skipped_search and type_id in {"X05", "A08", "A01"}:
        scores["no_false_negative"] = min(scores["no_false_negative"], 4.0)

    overall = weighted_overall(scores)
    passed = p0_pass(scores) if type_id in {
        "A08", "A17", "X05", "X06", "X12", "B01", "B09", "E05", "G01", "G07"
    } else overall >= OVERALL_THRESHOLD and all(
        scores[d] >= DIMENSION_THRESHOLD for d in LLM_EVAL_DIMENSIONS
    )

    return {
        "scores": scores,
        "overall": overall,
        "pass": passed,
        "notes": _notes(type_id, path_result, test),
    }


def build_playbook_entry(
    type_id: str,
    path_result: dict[str, Any],
    route_entry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    probe = load_probe_case(type_id) or {}
    route = route_entry or {}
    ev = score_from_path_result(type_id, path_result, scenario=probe.get("scenario"))
    blocking = path_result.get("blocking_gap")
    expected = route.get("expected_route") or {}
    tools = expected.get("tools") or []

    atomic_tools = [t.get("name") for t in tools if t.get("name")]
    gaps: list[dict[str, Any]] = []
    if blocking:
        gaps.append(
            {
                "gap_type": blocking.get("type", "routing_gap"),
                "detail": blocking.get("description", ""),
            }
        )

    sufficient = "true"
    if blocking:
        gt = blocking.get("type", "")
        if gt == "data_gap":
            sufficient = "false"
        elif gt == "implementation_gap":
            sufficient = "partial"
        else:
            sufficient = "partial"

    return {
        "type_id": type_id,
        "case_id": probe.get("case_id") or path_result.get("case_id"),
        "playbook_id": f"PB-{type_id}",
        "summary": _summary(type_id, probe, path_result, route),
        "atomic_tools_needed": atomic_tools,
        "pipeline_stages": _pipeline_stages(probe.get("scenario", "A"), blocking),
        "existing_tools_sufficient": sufficient,
        "gaps": gaps,
        "llm_eval": {
            **ev,
            "path_ref": f"path_attempts/{type_id}.yaml",
            "atomic_ref": f"atomic_decompositions/{type_id}.yaml",
        },
        "answer_playbook": {
            "steps": [t.get("name", "") for t in tools[:8]],
            "forbidden": _forbidden(type_id, probe.get("scenario", "A")),
        },
    }


def _pipeline_stages(scenario: str, blocking: dict | None) -> list[str]:
    base = {
        "A": ["entity_resolution", "schedule_fetch", "answer_synthesis"],
        "B": ["entity_resolution", "parallel_analysis", "answer_synthesis"],
        "C": ["entity_resolution", "result_fetch", "post_review"],
        "D": ["entity_resolution", "analysis", "betting_recommendation"],
        "E": ["lottery_list", "screening", "deep_review"],
        "F": ["entity_resolution", "odds_query"],
        "G": ["entity_resolution", "analysis", "checkpointer", "follow_up"],
        "H": ["entity_resolution", "standings", "outlook_narrative"],
        "X": ["entity_resolution", "guardrails", "answer_synthesis"],
    }.get(scenario, ["entity_resolution", "answer_synthesis"])
    if blocking and "checkpointer" in blocking.get("description", "").lower():
        if "checkpointer" not in base:
            base.append("checkpointer")
    if scenario in {"A", "X"}:
        base = list(dict.fromkeys(["entity_resolution", "cross_validation", *base]))
    return base


def _forbidden(type_id: str, scenario: str) -> list[str]:
    items = ["暴露 match_id", "暴露工具名"]
    if scenario == "X" or type_id in {"X06", "X12"}:
        items.append("输出中间态查询过程")
    if type_id in {"A08", "X05"}:
        items.extend(["direction=recent 查未来场", "未穷尽前断言无比赛"])
    return items


def _summary(
    type_id: str,
    probe: dict,
    path_result: dict,
    route: dict,
) -> str:
    name = probe.get("type_name") or type_id
    if path_result.get("route_complete"):
        return f"{name}：路径探索 complete，预期 skill={route.get('expected_route', {}).get('skill', '?')}"
    gap = (path_result.get("blocking_gap") or {}).get("description", "未知 gap")
    return f"{name}：blocked — {gap[:120]}"


def _notes(type_id: str, path_result: dict, test: dict) -> str:
    parts = []
    if test.get("expected_behaviors"):
        parts.append(f"expected: {', '.join(test['expected_behaviors'][:3])}")
    if path_result.get("blocking_gap"):
        parts.append(path_result["blocking_gap"].get("description", "")[:100])
    return "; ".join(parts) or f"path route_complete={path_result.get('route_complete')}"
