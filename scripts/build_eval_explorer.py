#!/usr/bin/env python3
"""Build static eval explorer HTML from taxonomy + eval dataset."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_common import load_taxonomy  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "data" / "eval"
JSONL_PATH = EVAL_DIR / "foretell_complex_questions.jsonl"
COVERAGE_PATH = EVAL_DIR / "coverage_report.json"
STATS_PATH = EVAL_DIR / "classification_stats.json"
P0_PATH = ROOT / "tests" / "eval" / "test_cases.yaml"
TEMPLATE_PATH = Path(__file__).resolve().parent / "eval_explorer_template.html"
OUT_PATH = EVAL_DIR / "eval-explorer.html"

SCENARIO_META: dict[str, dict[str, str]] = {
    "A": {"name": "轻查询", "description": "赛程、比分、积分榜、时间窗、实体消歧"},
    "B": {"name": "单场深度分析", "description": "竞彩模板、对阵、G7、伤病等多维度分析"},
    "C": {"name": "赛后复盘", "description": "已结束比赛的回顾与总结"},
    "D": {"name": "购彩推荐", "description": "怎么买、让球、大小球、单场方案与风险提示"},
    "E": {"name": "批量/串关", "description": "扫盘、2/3/4 串一、十四场、北单等批量场景"},
    "F": {"name": "赔率查询", "description": "赔率对比、走势、凯利等数据查询"},
    "G": {"name": "多轮追问", "description": "继续、同样逻辑、用户纠正、上下文延续"},
    "H": {"name": "语义精度", "description": "锁定排名 vs 不低于等语义约束"},
    "X": {"name": "边界/护栏", "description": "假阴性、中间态外露、盈利承诺、辱骂等边界"},
}

SCENARIO_ORDER = ["A", "B", "C", "D", "E", "F", "G", "H", "X"]


def _load_cases() -> list[dict]:
    cases: list[dict] = []
    with JSONL_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def _load_p0_ids() -> list[str]:
    with P0_PATH.open(encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return [c["id"] for c in doc.get("cases", [])]


def _session_counts(stats: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for type_id, count in stats.get("top_types", []):
        if type_id != "UNCLASSIFIED":
            counts[type_id] = count
    return counts


def build_explorer_data() -> dict:
    taxonomy = load_taxonomy()
    cases = _load_cases()
    coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    stats = json.loads(STATS_PATH.read_text(encoding="utf-8"))
    p0_ids = _load_p0_ids()
    session_counts = _session_counts(stats)

    case_by_type: dict[str, dict] = {c["type_id"]: c for c in cases}
    scenario_dist = coverage.get("scenario_distribution", {})

    scenarios = []
    for sid in SCENARIO_ORDER:
        meta = SCENARIO_META[sid]
        scenarios.append(
            {
                "id": sid,
                "name": meta["name"],
                "description": meta["description"],
                "type_count": scenario_dist.get(sid, 0),
            }
        )

    types = []
    for t in sorted(taxonomy, key=lambda x: (x.scenario, x.id)):
        case = case_by_type.get(t.id)
        types.append(
            {
                "id": t.id,
                "scenario": t.scenario,
                "name": t.name,
                "description": t.description,
                "entity_entry": t.entity_entry,
                "sport": t.sport,
                "complexity": t.complexity,
                "patterns": t.patterns,
                "keywords": t.keywords,
                "priority": t.priority,
                "tags": t.tags,
                "session_count": session_counts.get(t.id, 0),
                "case_id": case["id"] if case else None,
                "case_origin": case["source"]["origin"] if case else None,
                "case_multi_turn": case.get("multi_turn", False) if case else False,
                "case_is_p0": case["id"] in p0_ids if case else False,
                "case_has_feedback": bool(case.get("related_feedback")) if case else False,
            }
        )

    top_types = [
        {"id": tid, "count": cnt, "is_template": tid == "B01"}
        for tid, cnt in stats.get("top_types", [])
        if tid != "UNCLASSIFIED"
    ][:15]

    feedback_ids = coverage.get("feedback_regression_ids", [])

    return {
        "meta": {
            "generated_at": datetime.now(UTC).isoformat(),
            "version": "1.0",
        },
        "scenarios": scenarios,
        "types": types,
        "cases": cases,
        "stats": stats,
        "coverage": coverage,
        "p0_ids": p0_ids,
        "feedback_ids": feedback_ids,
        "top_types": top_types,
    }


def render_html(data: dict) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False)
    payload = payload.replace("</", "<\\/")
    return template.replace("__EXPLORER_DATA__", payload)


def main() -> None:
    data = build_explorer_data()
    html = render_html(data)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Built eval explorer -> {OUT_PATH} ({len(data['cases'])} cases, {len(data['types'])} types)")


if __name__ == "__main__":
    main()
