#!/usr/bin/env python3
"""Build final eval JSONL dataset from classified sessions + synthetic seeds."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_common import ensure_eval_dir, load_taxonomy  # noqa: E402

CLASSIFIED_PATH = Path(__file__).resolve().parent.parent / "data" / "eval" / "classified_by_type.json"
JSONL_PATH = Path(__file__).resolve().parent.parent / "data" / "eval" / "foretell_complex_questions.jsonl"
REPORT_PATH = Path(__file__).resolve().parent.parent / "data" / "eval" / "coverage_report.json"
TAXONOMY_PATH = Path(__file__).resolve().parent.parent / "data" / "eval" / "taxonomy.yaml"


def _synthetic_seeds() -> list[dict]:
    """Synthetic cases for types missing from production data, including feedback #001-#003."""
    return [
        {
            "id": "TC-A17-REG-001",
            "type_id": "A17",
            "type_name": "实体消歧_国家队",
            "scenario": "A",
            "complexity": "high",
            "entity_entry": "team+competition",
            "sport": "football",
            "lottery_play": None,
            "multi_turn": False,
            "turns": ["最近世界杯赛程法国队的比赛安排？"],
            "source": {"session_id": "synthetic", "run_indices": [0], "origin": "synthetic"},
            "tags": ["disambiguation", "schedule", "regression"],
            "expected_behaviors": ["含日期对手状态", "含北京时间", "含主客场", "默认法国男足2026世界杯"],
            "related_feedback": ["#001"],
        },
        {
            "id": "TC-X12-REG-002",
            "type_id": "X12",
            "type_name": "主客颠倒",
            "scenario": "X",
            "complexity": "high",
            "entity_entry": "match_pair+date",
            "sport": "football",
            "lottery_play": None,
            "multi_turn": True,
            "turns": ["法国 vs 挪威 2024-06-27", "应该是2026世界杯那场"],
            "source": {"session_id": "synthetic", "run_indices": [0, 1], "origin": "synthetic"},
            "tags": ["regression", "context", "match_resolution"],
            "expected_behaviors": ["最终定位2026-06-27", "挪威主场", "不输出中间态", "不暴露match_id"],
            "related_feedback": ["#002"],
        },
        {
            "id": "TC-A08-REG-003",
            "type_id": "A08",
            "type_name": "时间窗_明早",
            "scenario": "A",
            "complexity": "high",
            "entity_entry": "team+time",
            "sport": "football",
            "lottery_play": None,
            "multi_turn": True,
            "turns": [
                "今晚的葡萄牙比赛什么时候开始",
                "明天早上的",
                "葡萄牙明天早上世界杯比赛啊",
            ],
            "source": {"session_id": "synthetic", "run_indices": [0, 1, 2], "origin": "synthetic"},
            "tags": ["time_window", "context_loss", "regression"],
            "expected_behaviors": ["不得假阴性", "6/28 07:30 哥伦比亚vs葡萄牙", "含主客场", "不暴露内部编号"],
            "related_feedback": ["#003"],
        },
        {
            "id": "TC-G01-REG-004",
            "type_id": "G01",
            "type_name": "比分预测追问",
            "scenario": "G",
            "complexity": "high",
            "entity_entry": "context",
            "sport": "football",
            "lottery_play": "101",
            "multi_turn": True,
            "turns": [
                "分析竞彩足球周二004 巴黎 VS 拜仁胜平负、比分",
                "比分预测",
            ],
            "source": {"session_id": "synthetic", "run_indices": [0, 1], "origin": "synthetic"},
            "tags": ["follow_up", "regression"],
            "expected_behaviors": ["保持同场定位", "给出比分区间", "不重复完整六段"],
            "related_feedback": [],
        },
        {
            "id": "TC-G02-REG-005",
            "type_id": "G02",
            "type_name": "率先进球追问",
            "scenario": "G",
            "complexity": "high",
            "entity_entry": "context",
            "sport": "football",
            "lottery_play": "101",
            "multi_turn": True,
            "turns": [
                "分析竞彩足球周二004 巴黎 VS 拜仁胜平负、比分",
                "比分预测",
                "哪一队率先进球",
            ],
            "source": {"session_id": "synthetic", "run_indices": [0, 1, 2], "origin": "synthetic"},
            "tags": ["follow_up"],
            "expected_behaviors": ["保持同场定位", "先进球概率判断"],
            "related_feedback": [],
        },
        {
            "id": "TC-B09-REG-006",
            "type_id": "B09",
            "type_name": "系列赛G7",
            "scenario": "B",
            "complexity": "high",
            "entity_entry": "match_pair+series",
            "sport": "basketball",
            "lottery_play": None,
            "multi_turn": False,
            "turns": ["马刺对雷霆 G7 分析"],
            "source": {"session_id": "synthetic", "run_indices": [0], "origin": "synthetic"},
            "tags": ["series"],
            "expected_behaviors": ["保留G7约束", "找不到时不得降级G6"],
            "related_feedback": [],
        },
        {
            "id": "TC-E05-REG-007",
            "type_id": "E05",
            "type_name": "十四场",
            "scenario": "E",
            "complexity": "high",
            "entity_entry": "lottery_period",
            "sport": "football",
            "lottery_play": "401",
            "multi_turn": False,
            "turns": ["本期十四场给个方案"],
            "source": {"session_id": "synthetic", "run_indices": [0], "origin": "synthetic"},
            "tags": ["batch"],
            "expected_behaviors": ["两阶段初筛", "含风险提示"],
            "related_feedback": [],
        },
        {
            "id": "TC-X05-REG-008",
            "type_id": "X05",
            "type_name": "假阴性风险",
            "scenario": "X",
            "complexity": "high",
            "entity_entry": "team+competition",
            "sport": "football",
            "lottery_play": None,
            "multi_turn": False,
            "turns": ["葡萄牙明天早上世界杯有比赛吗"],
            "source": {"session_id": "synthetic", "run_indices": [0], "origin": "synthetic"},
            "tags": ["regression", "guardrail"],
            "expected_behaviors": ["禁止未穷尽前断言无比赛", "交叉验证赛程"],
            "related_feedback": ["#003"],
        },
        {
            "id": "TC-X06-REG-009",
            "type_id": "X06",
            "type_name": "中间态外露",
            "scenario": "X",
            "complexity": "high",
            "entity_entry": "none",
            "sport": "any",
            "lottery_play": None,
            "multi_turn": False,
            "turns": ["法国 vs 挪威具体哪场"],
            "source": {"session_id": "synthetic", "run_indices": [0], "origin": "synthetic"},
            "tags": ["output_discipline"],
            "expected_behaviors": ["不输出正在查询", "不输出未找到过程", "仅最终结论"],
            "related_feedback": ["#002"],
        },
        {
            "id": "TC-H03-REG-010",
            "type_id": "H03",
            "type_name": "季后赛锁定",
            "scenario": "H",
            "complexity": "high",
            "entity_entry": "league",
            "sport": "basketball",
            "lottery_play": None,
            "multi_turn": False,
            "turns": ["哪些球队锁定了季后赛"],
            "source": {"session_id": "synthetic", "run_indices": [0], "origin": "synthetic"},
            "tags": ["semantic"],
            "expected_behaviors": ["仅报告精确锁定名次球队", "区分锁定不低于"],
            "related_feedback": [],
        },
    ]


def _type_lookup() -> dict[str, dict]:
    taxonomy = load_taxonomy()
    return {t.id: t for t in taxonomy}


def _pick_best(items: list[dict]) -> dict:
    return max(items, key=lambda x: (x.get("complexity_score", 0), len(x.get("turns_text", []))))


def build_dataset(
    classified_path: Path = CLASSIFIED_PATH,
    output_path: Path = JSONL_PATH,
    report_path: Path = REPORT_PATH,
) -> None:
    ensure_eval_dir()
    type_map = _type_lookup()
    all_type_ids = sorted(type_map.keys())

    if classified_path.exists():
        classified = json.loads(classified_path.read_text(encoding="utf-8"))
        by_type: dict[str, list] = classified.get("by_type", {})
    else:
        by_type = {}

    seeds = _synthetic_seeds()
    seed_by_type = {s["type_id"]: s for s in seeds}
    selected: dict[str, list[dict]] = defaultdict(list)
    used_pattern: set[str] = set()
    multi_turn_cases: list[dict] = []

    for type_id in all_type_ids:
        items = by_type.get(type_id, [])
        if not items:
            continue
        # Prefer multi-turn and high complexity
        items_sorted = sorted(
            items,
            key=lambda x: (x.get("complexity_score", 0), len(x.get("turns_text", []))),
            reverse=True,
        )
        for item in items_sorted[:3]:
            ph = item.get("pattern_hash", "")
            if ph and ph in used_pattern and len(item.get("turns_text", [])) <= 1:
                continue
            if ph:
                used_pattern.add(ph)
            t = type_map[type_id]
            turns = item.get("turns_text", [])
            case = {
                "id": f"TC-{type_id}-{len(selected[type_id]) + 1:03d}",
                "type_id": type_id,
                "type_name": t.name,
                "scenario": t.scenario,
                "complexity": t.complexity if len(turns) < 2 else "high",
                "entity_entry": t.entity_entry,
                "sport": t.sport,
                "lottery_play": _infer_lottery(turns),
                "multi_turn": len(turns) >= 2,
                "turns": turns,
                "source": {
                    "session_id": item.get("session_id"),
                    "run_indices": list(range(len(turns))),
                    "origin": "production",
                },
                "tags": t.tags,
                "expected_behaviors": _expected_behaviors(t.scenario, type_id),
                "related_feedback": [],
            }
            selected[type_id].append(case)
            if len(turns) >= 2:
                multi_turn_cases.append(case)
            if len(selected[type_id]) >= 1:
                break

    # Build one case per type_id
    final_by_type: dict[str, dict] = {}

    for type_id in all_type_ids:
        if selected.get(type_id):
            final_by_type[type_id] = selected[type_id][0]
        elif type_id in seed_by_type:
            final_by_type[type_id] = seed_by_type[type_id]

    # Apply all synthetic seeds (regression overrides)
    for seed in seeds:
        final_by_type[seed["type_id"]] = seed

    # Fill any remaining gaps
    for type_id in all_type_ids:
        if type_id not in final_by_type:
            t = type_map[type_id]
            final_by_type[type_id] = {
                "id": f"TC-{type_id}-SYN",
                "type_id": type_id,
                "type_name": t.name,
                "scenario": t.scenario,
                "complexity": t.complexity,
                "entity_entry": t.entity_entry,
                "sport": t.sport,
                "lottery_play": None,
                "multi_turn": False,
                "turns": [_default_question(t)],
                "source": {"session_id": "synthetic", "run_indices": [0], "origin": "synthetic"},
                "tags": t.tags,
                "expected_behaviors": _expected_behaviors(t.scenario, type_id),
                "related_feedback": [],
            }

    final_list = sorted(final_by_type.values(), key=lambda c: c["type_id"])

    with output_path.open("w", encoding="utf-8") as f:
        for case in final_list:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    scenario_dist: dict[str, int] = defaultdict(int)
    origin_dist: dict[str, int] = defaultdict(int)
    multi_count = 0
    for case in final_list:
        scenario_dist[case["scenario"]] += 1
        origin_dist[case.get("source", {}).get("origin", "unknown")] += 1
        if case.get("multi_turn"):
            multi_count += 1

    missing = [tid for tid in all_type_ids if tid not in final_by_type]
    g_types = [c for c in final_list if c["scenario"] == "G"]

    report = {
        "total_types_defined": len(all_type_ids),
        "total_cases": len(final_list),
        "missing_types": missing,
        "multi_turn_cases": multi_count,
        "scenario_distribution": dict(scenario_dist),
        "origin_distribution": dict(origin_dist),
        "g_scenario_count": len(g_types),
        "production_backed_types": sum(
            1 for c in final_list if c.get("source", {}).get("origin") == "production"
        ),
        "synthetic_types": sum(
            1 for c in final_list if c.get("source", {}).get("origin") == "synthetic"
        ),
        "feedback_regression_ids": [c["id"] for c in final_list if c.get("related_feedback")],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Built {len(final_list)} cases -> {output_path}")
    print(f"Multi-turn: {multi_count}, G scenario types: {len(g_types)}")
    print(f"Missing types: {len(missing)}")
    print(f"Report -> {report_path}")


def _infer_lottery(turns: list[str]) -> str | None:
    text = " ".join(turns)
    if "竞彩篮球" in text:
        return "201"
    if "竞彩足球" in text or "周" in text:
        return "101"
    if "十四场" in text or "胜负彩" in text:
        return "401"
    if "任九" in text:
        return "401"
    if "北单" in text:
        return "301"
    return None


def _expected_behaviors(scenario: str, type_id: str) -> list[str]:
    base = {
        "A": ["意图对齐", "归纳优先于罗列", "数据不足时诚实说明"],
        "B": ["多维度深度分析", "数据诚实规则", "不暴露工具名"],
        "C": ["定位已完场比赛", "不复盘购彩除非追问"],
        "D": ["单一主推方向", "结尾含风险提示"],
        "E": ["两阶段初筛深核", "初筛不能直接作最终推荐"],
        "F": ["区分快照与走势", "不混淆查询路径"],
        "G": ["保持比赛定位稳定", "不重复完整六段"],
        "H": ["语义精确匹配锁定排名"],
        "X": ["遵守输出纪律与安全护栏"],
    }.get(scenario, ["符合产品规范"])
    if type_id.startswith("A") and "08" in type_id:
        base.append("不得假阴性")
    if type_id.startswith("X"):
        base.append("不输出中间态")
    return base


def _default_question(t) -> str:
    defaults = {
        "A01": "今晚五大联赛有什么比赛",
        "B01": "分析【2026-06-15 01:00:00 竞彩足球周日009 世界杯 德国 VS 库拉索】的赛事的胜平负、比分结果",
        "C01": "昨天皇马那场怎么回事",
        "D01": "这场怎么买",
        "E01": "帮我扫盘",
        "F01": "这场赔率对比一下",
        "G01": "比分预测",
        "H01": "英超争冠还有悬念吗",
        "X01": "今天国际政治局势如何",
    }
    return defaults.get(t.id, f"[{t.name}示例问法]")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--classified", type=Path, default=CLASSIFIED_PATH)
    parser.add_argument("--output", type=Path, default=JSONL_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args()
    build_dataset(args.classified, args.output, args.report)


if __name__ == "__main__":
    main()
