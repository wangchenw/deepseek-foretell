#!/usr/bin/env python3
"""Generate template atomic_decompositions for all 120 types from probe_cases + taxonomy."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_common import load_taxonomy  # noqa: E402
from llm_eval_common import ATOMIC_DIR, P0_TYPE_IDS, dump_yaml, load_probe_case, load_yaml  # noqa: E402

ENTITY_TO_ATOMIC: dict[str, list[dict[str, Any]]] = {
    "date": [{"id": "a1", "category": "fetch_schedule", "target": {"source": "date"}}],
    "team": [
        {"id": "a1", "category": "resolve_entity", "target": {"entity": "team"}},
        {"id": "a2", "category": "fetch_schedule", "target": {"team_id": "$a1"}},
    ],
    "team+time": [
        {"id": "a1", "category": "resolve_entity", "target": {"entity": "team"}},
        {"id": "a2", "category": "refine_time_window", "target": {}},
        {"id": "a3", "category": "fetch_schedule", "target": {"direction": "all"}},
        {"id": "a4", "category": "discover_via_search", "target": {"status": "skipped"}},
    ],
    "match": [
        {"id": "a1", "category": "resolve_entity", "target": {"entity": "match"}},
        {"id": "a2", "category": "synthesize_answer", "target": {}},
    ],
    "lottery_code": [
        {"id": "a1", "category": "resolve_entity", "target": {"entity": "lottery"}},
    ],
    "context": [
        {"id": "a1", "category": "maintain_context", "target": {}},
        {"id": "a2", "category": "synthesize_answer", "target": {}},
    ],
    "none": [{"id": "a1", "category": "apply_guardrails", "target": {}}],
}


def generate_for_type(type_id: str, skip_existing_p0: bool = True) -> dict[str, Any] | None:
    if skip_existing_p0 and type_id in P0_TYPE_IDS:
        path = ATOMIC_DIR / f"{type_id}.yaml"
        if path.exists():
            return None

    probe = load_probe_case(type_id) or {}
    turns_text = probe.get("probe_turns") or probe.get("full_turns") or ["[placeholder]"]
    entity = probe.get("entity_entry", "unknown")
    atomics = ENTITY_TO_ATOMIC.get(entity, ENTITY_TO_ATOMIC.get("match", []))

    if probe.get("scenario") == "B":
        atomics = atomics + [
            {"id": "b1", "category": "delegate_subagent", "target": {"agents": ["fundamentals", "odds", "intel"]}},
            {"id": "b2", "category": "synthesize_answer", "target": {"format": "six_segment"}},
        ]
    if probe.get("scenario") == "G":
        atomics = [
            {"id": "g0", "category": "maintain_context", "target": {}},
            *atomics,
        ]
    if probe.get("scenario") == "X":
        atomics = atomics + [{"id": "x1", "category": "apply_guardrails", "target": {}}]

    doc = {
        "type_id": type_id,
        "type_name": probe.get("type_name", ""),
        "scenario": probe.get("scenario", ""),
        "entity_entry": entity,
        "priority": probe.get("priority", "P2"),
        "generated": True,
        "turns": [
            {
                "turn": i + 1,
                "user": turns_text[i] if i < len(turns_text) else turns_text[-1],
                "atomics": [{**a, "id": f"T{i+1}-{a['id']}"} for a in atomics],
            }
            for i in range(min(len(turns_text), 3))
        ],
        "hard_constraints": _constraints(type_id, probe),
    }
    return doc


def _constraints(type_id: str, probe: dict) -> list[str]:
    c: list[str] = []
    if type_id in {"A08", "X05"}:
        c.append("禁止未穷尽前断言无比赛")
    if type_id.startswith("X"):
        c.append("不输出中间态")
    if probe.get("related_feedback"):
        c.extend(probe.get("related_feedback"))
    return c


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Generate for all 120 types")
    parser.add_argument("--force-p0", action="store_true", help="Overwrite P0 hand-crafted files")
    args = parser.parse_args()

    ATOMIC_DIR.mkdir(parents=True, exist_ok=True)
    taxonomy = load_taxonomy()
    written = 0
    for t in taxonomy:
        if args.all or t.id not in P0_TYPE_IDS:
            doc = generate_for_type(t.id, skip_existing_p0=not args.force_p0)
            if doc:
                dump_yaml(ATOMIC_DIR / f"{t.id}.yaml", doc)
                written += 1
    print(f"Generated {written} atomic decomposition files -> {ATOMIC_DIR}")


if __name__ == "__main__":
    main()
