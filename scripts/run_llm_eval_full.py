#!/usr/bin/env python3
"""Phase 2b: LLM eval for all 120 types (probe_results + route_matrix -> playbooks)."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_common import load_taxonomy  # noqa: E402
from llm_eval_common import (  # noqa: E402
    ATOMIC_DIR,
    EVAL_DIR,
    PATH_DIR,
    PLAYBOOKS_PATH,
    P0_TYPE_IDS,
    ROUTE_MATRIX_PATH,
    dump_yaml,
    load_probe_case,
    load_probe_result,
    load_yaml,
    today_iso,
)
from llm_eval_review import build_playbook_entry  # noqa: E402

FULL_PLAYBOOKS_PATH = EVAL_DIR / "answer_playbooks_full_120.yaml"
ROUTE_MATRIX_FINAL_PATH = EVAL_DIR / "route_matrix_final.yaml"
FULL_SUMMARY_PATH = EVAL_DIR / "llm_eval_full_summary.md"
ACTION_ITEMS_PATH = EVAL_DIR / "phase2_action_items.md"

SCENARIO_BATCHES: list[tuple[str, list[str]]] = [
    ("Batch 1: A+X", ["A", "X"]),
    ("Batch 2: B+C", ["B", "C"]),
    ("Batch 3: D+E", ["D", "E"]),
    ("Batch 4: F+G", ["F", "G"]),
    ("Batch 5: H", ["H"]),
]

GAP_TYPE_MAP: dict[str, str] = {
    "field_unknown": "data_gap",
    "data": "data_gap",
    "routing": "routing_gap",
    "implementation": "implementation_gap",
    "pipeline": "pipeline_gap",
}


def _normalize_gap_type(raw: str | None, route_status: str) -> str:
    if not raw:
        if route_status == "prompt_only":
            return "pipeline_gap"
        if route_status == "blocked":
            return "routing_gap"
        return "routing_gap"
    return GAP_TYPE_MAP.get(raw, raw if raw.endswith("_gap") else f"{raw}_gap")


def probe_to_path_attempt(type_id: str, route_entry: dict[str, Any]) -> dict[str, Any]:
    """Convert script probe result + route_matrix gap into path_attempts shape."""
    path_file = PATH_DIR / f"{type_id}.yaml"
    if path_file.exists():
        try:
            return load_yaml(path_file)
        except Exception:
            # v1 path_attempts 含预存 yaml 格式 bug(嵌套引号/全角括号),
            # 不阻塞 v3 打分:丢弃损坏的 v1 记录,用新 probe_results 重建。
            pass

    probe = load_probe_case(type_id) or {}
    probe_result = load_probe_result(type_id)
    actual = route_entry.get("actual_probe") or {}
    route_status = actual.get("route_status", "blocked")
    gap_text = route_entry.get("gap") or ""
    gap_type = _normalize_gap_type(route_entry.get("gap_type"), route_status)

    attempts: list[dict[str, Any]] = []
    if probe_result and probe_result.get("steps"):
        for i, step in enumerate(probe_result["steps"], start=1):
            attempts.append(
                {
                    "round": i,
                    "atomic_id": f"{type_id}-probe-{i}",
                    **step,
                }
            )
    elif route_status == "prompt_only":
        attempts.append(
            {
                "round": 1,
                "atomic_id": f"{type_id}-prompt",
                "status": "prompt_only",
                "note": gap_text or "无工具链，仅 prompt 路由",
            }
        )

    blocking: dict[str, Any] | None = None
    if route_status in {"blocked", "prompt_only"} or gap_text:
        last_fail = next(
            (a for a in reversed(attempts) if a.get("code") not in {None, "OK"}),
            None,
        )
        blocking = {
            "type": gap_type,
            "description": gap_text or f"route_status={route_status}",
            "failed_atomic": (last_fail or {}).get("atomic_id"),
        }
    elif attempts and not all(a.get("code") == "OK" for a in attempts if a.get("code")):
        blocking = {
            "type": gap_type,
            "description": gap_text or "工具链未全部 OK",
            "failed_atomic": attempts[-1].get("atomic_id"),
        }

    route_complete = route_status == "verified" and blocking is None
    if route_status == "verified" and not attempts:
        route_complete = True

    return {
        "type_id": type_id,
        "case_id": probe.get("case_id") or probe_result.get("case_id") if probe_result else None,
        "explored_at": today_iso(),
        "source": "probe_results" if probe_result else "route_matrix",
        "attempts": attempts,
        "satisfied": [],
        "blocking_gap": blocking,
        "route_complete": route_complete,
    }


def run_batch(
    scenarios: list[str],
    matrix_by_id: dict[str, dict[str, Any]],
    *,
    write_paths: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    playbooks: list[dict[str, Any]] = []
    stats = {"pass": 0, "fail": 0, "partial": 0, "by_scenario": {}}

    for t in load_taxonomy():
        if t.scenario not in scenarios:
            continue
        route_entry = matrix_by_id.get(t.id, {})
        path_result = probe_to_path_attempt(t.id, route_entry)
        if write_paths and t.id not in P0_TYPE_IDS:
            dump_yaml(PATH_DIR / f"{t.id}.yaml", path_result)

        pb = build_playbook_entry(t.id, path_result, route_entry)
        playbooks.append(pb)

        ev = pb["llm_eval"]
        sc = t.scenario
        stats["by_scenario"].setdefault(sc, {"pass": 0, "fail": 0})
        if ev["pass"]:
            stats["pass"] += 1
            stats["by_scenario"][sc]["pass"] += 1
        else:
            stats["fail"] += 1
            stats["by_scenario"][sc]["fail"] += 1
        if pb.get("existing_tools_sufficient") == "partial":
            stats["partial"] += 1

    return playbooks, stats


def merge_route_matrix_final(playbooks: list[dict[str, Any]]) -> dict[str, Any]:
    matrix = load_yaml(ROUTE_MATRIX_PATH)
    pb_by_id = {p["type_id"]: p for p in playbooks}
    entries: list[dict[str, Any]] = []

    for entry in matrix.get("entries", []):
        type_id = entry.get("type_id")
        pb = pb_by_id.get(type_id)
        if not pb:
            continue
        ev = pb["llm_eval"]
        merged = dict(entry)
        merged["llm_eval_status"] = "pass" if ev["pass"] else "fail"
        merged["llm_eval_score"] = ev["overall"]
        merged["llm_eval_scores"] = ev["scores"]
        merged["atomic_tools_needed"] = pb["atomic_tools_needed"]
        merged["playbook_id"] = pb["playbook_id"]
        merged["playbook_ref"] = f"answer_playbooks_full_120.yaml#{pb['playbook_id']}"
        merged["path_attempt_ref"] = ev["path_ref"]
        merged["atomic_decomposition_ref"] = ev["atomic_ref"]
        merged["existing_tools_sufficient"] = pb["existing_tools_sufficient"]
        merged["llm_eval_gaps"] = pb.get("gaps", [])
        entries.append(merged)

    pass_n = sum(1 for e in entries if e["llm_eval_status"] == "pass")
    return {
        "version": "2.0",
        "meta": {
            "source": "route_matrix.yaml + llm_eval_full",
            "total_types": len(entries),
            "evaluated_at": today_iso(),
            "pass_count": pass_n,
            "fail_count": len(entries) - pass_n,
            "p0_types": list(P0_TYPE_IDS),
        },
        "entries": entries,
    }


def _gap_counter(playbooks: list[dict[str, Any]]) -> Counter[str]:
    c: Counter[str] = Counter()
    for pb in playbooks:
        for g in pb.get("gaps") or []:
            gt = g.get("gap_type", "unknown")
            c[gt] += 1
    return c


def write_full_summary(playbooks: list[dict[str, Any]], matrix_final: dict[str, Any]) -> None:
    meta = matrix_final["meta"]
    gap_counts = _gap_counter(playbooks)
    top_gaps = gap_counts.most_common(10)

    lines = [
        "# Foretell LLM Eval Full Summary (120 types)",
        "",
        f"- **Evaluated at**: {meta['evaluated_at']}",
        f"- **Total types**: {meta['total_types']}/120",
        f"- **Pass**: {meta['pass_count']} | **Fail**: {meta['fail_count']}",
        f"- **Partial tools sufficient**: {sum(1 for p in playbooks if p.get('existing_tools_sufficient') == 'partial')}",
        "",
        "## Distribution by Scenario",
        "",
        "| Scenario | Pass | Fail | Pass rate |",
        "|----------|------|------|-----------|",
    ]

    by_sc: dict[str, list[dict]] = {}
    for pb in playbooks:
        tid = pb["type_id"]
        sc = tid[0] if tid else "?"
        by_sc.setdefault(sc, []).append(pb)

    for sc in sorted(by_sc.keys()):
        items = by_sc[sc]
        p = sum(1 for x in items if x["llm_eval"]["pass"])
        f = len(items) - p
        rate = f"{100 * p / len(items):.0f}%" if items else "—"
        lines.append(f"| {sc} | {p} | {f} | {rate} |")

    lines.extend(
        [
            "",
            "## Top 10 Gap Types",
            "",
        ]
    )
    for gt, cnt in top_gaps:
        lines.append(f"- **{gt}**: {cnt}")

    lines.extend(
        [
            "",
            "## P0 Regression (Phase 1)",
            "",
        ]
    )
    for tid in P0_TYPE_IDS:
        pb = next((p for p in playbooks if p["type_id"] == tid), None)
        if pb:
            ev = pb["llm_eval"]
            status = "PASS" if ev["pass"] else "FAIL"
            lines.append(f"- {tid}: {status} (score {ev['overall']})")

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "```",
            "data/eval/answer_playbooks_full_120.yaml",
            "data/eval/route_matrix_final.yaml",
            "data/eval/path_attempts/{120}.yaml",
            "data/eval/atomic_decompositions/{120}.yaml",
            "```",
        ]
    )
    FULL_SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_action_items(playbooks: list[dict[str, Any]], gap_counts: Counter[str]) -> None:
    lines = [
        "# Phase 2 Action Items → Phase 3",
        "",
        f"Generated: {today_iso()}",
        "",
        "## P1 — Development (2–3 weeks)",
        "",
        "- **resolve_lottery_match**: 历史竞彩编号/date 映射；B01/G01 系列 data_gap",
        "- **checkpointer / multi-turn**: G 场景 pipeline_gap；eval_checkpointer_demo 已证 turn2 逻辑",
        "",
        "## P1.5 — Data Governance (1–2 weeks)",
        "",
        "- 竞彩 lottery 表覆盖与 nami_field_map 编号枚举",
        "- NBA series_game / 季后赛维度 (B09)",
        "",
        "## P2 — Tool Stubs (1–2 weeks)",
        "",
        "- get_odds_snapshot, get_recent_form, get_injury_report (E/F/G 高频 implementation_gap)",
        "",
        "## P3 — Optional",
        "",
        "- discover_via_search (Tavily) 对照组 wave",
        "- CI 接入 llm_eval_full + P0 regression",
        "",
        "## Gap Frequency",
        "",
    ]
    for gt, cnt in gap_counts.most_common(15):
        lines.append(f"- {gt}: {cnt}")

    fail_types = [p["type_id"] for p in playbooks if not p["llm_eval"]["pass"]]
    lines.extend(
        [
            "",
            f"## Fail Types ({len(fail_types)})",
            "",
            ", ".join(sorted(fail_types[:60])),
            ("..." if len(fail_types) > 60 else ""),
        ]
    )
    ACTION_ITEMS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM eval for all 120 types")
    parser.add_argument(
        "--scenarios",
        default="A,B,C,D,E,F,G,H,X",
        help="Comma-separated scenario letters",
    )
    parser.add_argument("--summary-only", action="store_true", help="Skip path writes, rebuild summaries")
    parser.add_argument("--merge", action="store_true", help="Only merge from existing playbooks file")
    args = parser.parse_args()

    matrix = load_yaml(ROUTE_MATRIX_PATH)
    matrix_by_id = {e["type_id"]: e for e in matrix.get("entries", [])}

    if args.merge and FULL_PLAYBOOKS_PATH.exists():
        playbooks = load_yaml(FULL_PLAYBOOKS_PATH).get("entries", [])
    else:
        scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]
        all_playbooks: list[dict[str, Any]] = []
        done = 0
        total = len(matrix_by_id)

        for batch_name, batch_scenarios in SCENARIO_BATCHES:
            if not any(s in scenarios for s in batch_scenarios):
                continue
            batch_playbooks, batch_stats = run_batch(
                batch_scenarios,
                matrix_by_id,
                write_paths=not args.summary_only,
            )
            all_playbooks.extend(batch_playbooks)
            done += len(batch_playbooks)
            print(
                f"[Progress] {batch_name} | {done}/{total} types | "
                f"pass={batch_stats['pass']} fail={batch_stats['fail']}"
            )

        playbooks = all_playbooks
        dump_yaml(
            FULL_PLAYBOOKS_PATH,
            {
                "version": "2.0",
                "meta": {"evaluated_at": today_iso(), "count": len(playbooks)},
                "entries": playbooks,
            },
        )
        print(f"Playbooks -> {FULL_PLAYBOOKS_PATH}")

    matrix_final = merge_route_matrix_final(playbooks)
    dump_yaml(ROUTE_MATRIX_FINAL_PATH, matrix_final)
    print(
        f"Route matrix final: pass={matrix_final['meta']['pass_count']} "
        f"fail={matrix_final['meta']['fail_count']} -> {ROUTE_MATRIX_FINAL_PATH}"
    )

    gap_counts = _gap_counter(playbooks)
    write_full_summary(playbooks, matrix_final)
    write_action_items(playbooks, gap_counts)
    print(f"Summary -> {FULL_SUMMARY_PATH}")
    print(f"Action items -> {ACTION_ITEMS_PATH}")


if __name__ == "__main__":
    main()
