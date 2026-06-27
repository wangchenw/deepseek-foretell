#!/usr/bin/env python3
"""Generate spot-check report for eval dataset quality review."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

JSONL = Path(__file__).resolve().parent.parent / "data" / "eval" / "foretell_complex_questions.jsonl"
REPORT = Path(__file__).resolve().parent.parent / "data" / "eval" / "spot_check_report.json"


def main() -> None:
    cases = []
    with JSONL.open(encoding="utf-8") as f:
        for line in f:
            cases.append(json.loads(line))

    # Stratified sample: all feedback regression + random from each scenario
    by_scenario: dict[str, list] = {}
    for c in cases:
        by_scenario.setdefault(c["scenario"], []).append(c)

    sample: list[dict] = []
    for c in cases:
        if c.get("related_feedback"):
            sample.append(c)

    rng = random.Random(42)
    for scenario, items in sorted(by_scenario.items()):
        pool = [c for c in items if c not in sample]
        need = max(2, 30 // len(by_scenario) - sum(1 for s in sample if s["scenario"] == scenario))
        sample.extend(rng.sample(pool, min(need, len(pool))))

    sample = sample[:30]
    seen = set()
    unique_sample = []
    for c in sample:
        if c["id"] not in seen:
            seen.add(c["id"])
            unique_sample.append(
                {
                    "id": c["id"],
                    "type_id": c["type_id"],
                    "scenario": c["scenario"],
                    "multi_turn": c["multi_turn"],
                    "turn_count": len(c["turns"]),
                    "turns_preview": [t[:80] for t in c["turns"][:4]],
                    "origin": c.get("source", {}).get("origin"),
                    "related_feedback": c.get("related_feedback", []),
                    "review_status": "pending",
                }
            )

    report = {
        "total_cases_in_dataset": len(cases),
        "spot_check_count": len(unique_sample),
        "feedback_regression_included": [
            c["id"] for c in unique_sample if c.get("related_feedback")
        ],
        "sample": unique_sample,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Spot-check report: {len(unique_sample)} cases -> {REPORT}")


if __name__ == "__main__":
    main()
