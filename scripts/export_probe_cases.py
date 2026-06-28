#!/usr/bin/env python3
"""Export probe_cases.yaml and scenario_manifest.yaml from eval JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_common import (  # noqa: E402
    LOTTERY_TEMPLATE_RE,
    TAXONOMY_PATH,
    load_taxonomy,
    normalize_question,
)

JSONL = Path(__file__).resolve().parent.parent / "data" / "eval" / "foretell_complex_questions.jsonl"
P0_YAML = Path(__file__).resolve().parent.parent / "tests" / "eval" / "test_cases.yaml"
PROBE_OUT = Path(__file__).resolve().parent.parent / "data" / "eval" / "probe_cases.yaml"
MANIFEST_OUT = Path(__file__).resolve().parent.parent / "data" / "eval" / "scenario_manifest.yaml"

SCENARIO_SKILLS = {
    "A": "foretell/skills/foretell-light-query/SKILL.md",
    "B": "foretell/skills/foretell-match-analysis/SKILL.md",
    "C": "foretell/skills/foretell-post-review/SKILL.md",
    "D": "foretell/skills/foretell-betting-single/SKILL.md",
    "E": "foretell/skills/foretell-batch-screening/SKILL.md",
    "F": "foretell/skills/foretell-odds-query/SKILL.md",
    "G": "foretell/skills/foretell-follow-up/SKILL.md",
    "H": "foretell/skills/foretell-league-outlook/SKILL.md",
    "X": "foretell/skills/foretell-output-discipline/SKILL.md",
}

P0_TYPE_IDS = {"A08", "A17", "B01", "B09", "E05", "G01", "G02", "X05", "X06", "X12"}


def _load_p0_ids() -> set[str]:
    if not P0_YAML.exists():
        return set(P0_TYPE_IDS)
    data = yaml.safe_load(P0_YAML.read_text(encoding="utf-8"))
    return {c["type_id"] for c in data.get("cases", [])}


def _pick_probe_turns(case: dict) -> tuple[list[str], str, str | None]:
    """Return (probe_turns, probe_status, canonical_first)."""
    turns = case.get("turns") or []
    origin = case.get("source", {}).get("origin", "production")
    case_id = case.get("id", "")

    if case.get("related_feedback"):
        return list(turns), "ready", None

    if origin == "synthetic" and not case_id.endswith("-SYN"):
        return list(turns), "ready", None

    if case_id.endswith("-SYN") or (
        turns and turns[0].startswith("[") and turns[0].endswith("]")
    ):
        return list(turns) if turns else [], "needs_manual", None

    if not turns:
        return [], "needs_manual", None

    first = turns[0].strip()
    canonical = None
    if len(first) > 120 or LOTTERY_TEMPLATE_RE.search(first):
        canonical, _ = normalize_question(first)
        if canonical == first and len(first) > 120:
            canonical = first[:120].rstrip() + "…"

    if len(first) <= 120 and not LOTTERY_TEMPLATE_RE.search(first):
        probe = [first]
    elif canonical:
        probe = [canonical]
    else:
        norm, _ = normalize_question(first)
        probe = [norm]

    return probe, "ready", canonical


def _priority(case: dict, p0_ids: set[str]) -> str:
    if case.get("related_feedback") or case["type_id"] in p0_ids:
        return "P0"
    if case.get("source", {}).get("origin") == "synthetic":
        return "P1"
    return "P2"


def export_probe_cases(jsonl_path: Path = JSONL, out_path: Path = PROBE_OUT) -> list[dict]:
    p0_ids = _load_p0_ids()
    taxonomy = {t.id: t for t in load_taxonomy()}
    cases: list[dict] = []

    with jsonl_path.open(encoding="utf-8") as f:
        for line in f:
            case = json.loads(line)
            type_id = case["type_id"]
            t = taxonomy.get(type_id)
            probe_turns, probe_status, canonical = _pick_probe_turns(case)
            entry = {
                "type_id": type_id,
                "type_name": case.get("type_name") or (t.name if t else ""),
                "scenario": case.get("scenario") or (t.scenario if t else ""),
                "case_id": case.get("id"),
                "probe_turns": probe_turns,
                "full_turns": case.get("turns", []),
                "entity_entry": case.get("entity_entry") or (t.entity_entry if t else ""),
                "origin": case.get("source", {}).get("origin", "production"),
                "priority": _priority(case, p0_ids),
                "probe_status": probe_status,
                "multi_turn": case.get("multi_turn", False),
                "related_feedback": case.get("related_feedback", []),
            }
            if canonical:
                entry["canonical_first"] = canonical
            cases.append(entry)

    cases.sort(key=lambda c: c["type_id"])
    doc = {
        "description": "Probe cases for route exploration (short turns for DB/tool probing)",
        "total": len(cases),
        "cases": cases,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        yaml.dump(doc, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print(f"Exported {len(cases)} probe cases -> {out_path}")
    return cases


def export_scenario_manifest(out_path: Path = MANIFEST_OUT) -> None:
    taxonomy = load_taxonomy()
    by_scenario: dict[str, list[str]] = {}
    for t in taxonomy:
        by_scenario.setdefault(t.scenario, []).append(t.id)

    scenarios = []
    for letter in "ABCDEFGHX":
        type_ids = sorted(by_scenario.get(letter, []))
        scenarios.append(
            {
                "scenario": letter,
                "type_count": len(type_ids),
                "type_ids": type_ids,
                "primary_skill": SCENARIO_SKILLS.get(letter, ""),
            }
        )

    doc = {
        "description": "Scenario to skill mapping for route exploration",
        "taxonomy_path": str(TAXONOMY_PATH.relative_to(MANIFEST_OUT.parent.parent.parent)),
        "scenarios": scenarios,
    }
    with out_path.open("w", encoding="utf-8") as f:
        yaml.dump(doc, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print(f"Exported scenario manifest -> {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", type=Path, default=JSONL)
    parser.add_argument("--probe-out", type=Path, default=PROBE_OUT)
    parser.add_argument("--manifest-out", type=Path, default=MANIFEST_OUT)
    args = parser.parse_args()
    export_probe_cases(args.jsonl, args.probe_out)
    export_scenario_manifest(args.manifest_out)


if __name__ == "__main__":
    main()
