#!/usr/bin/env python3
"""Export P0 tool-chain verifiable test cases from eval JSONL."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

JSONL = Path(__file__).resolve().parent.parent / "data" / "eval" / "foretell_complex_questions.jsonl"
OUT = Path(__file__).resolve().parent.parent / "tests" / "eval" / "test_cases.yaml"

# Cases verifiable via entity/tool chain (no LLM)
P0_TYPE_IDS = {
    "A17",  # France + World Cup schedule
    "A08",  # Portugal time window
    "B01",  # Lottery template
    "G01", "G02",  # Follow-up chain
    "E05",  # 14场
    "B09",  # G7 series
}


def main() -> None:
    cases = []
    with JSONL.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec["type_id"] in P0_TYPE_IDS or rec.get("related_feedback"):
                cases.append(
                    {
                        "id": rec["id"],
                        "type_id": rec["type_id"],
                        "turns": rec["turns"],
                        "expected_behaviors": rec.get("expected_behaviors", []),
                        "related_feedback": rec.get("related_feedback", []),
                        "verify": "tool_chain",
                    }
                )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = {"description": "P0 regression cases for tool-chain verification", "cases": cases}
    with OUT.open("w", encoding="utf-8") as f:
        yaml.dump(doc, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print(f"Exported {len(cases)} P0 cases -> {OUT}")


if __name__ == "__main__":
    main()
