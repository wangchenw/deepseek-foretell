#!/usr/bin/env python3
"""Summarize route_matrix gaps and skill update candidates."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import yaml

EVAL_DIR = Path(__file__).resolve().parent.parent / "data" / "eval"
MATRIX_PATH = EVAL_DIR / "route_matrix.yaml"
SUMMARY_PATH = EVAL_DIR / "route_gaps_summary.md"


def build_summary(matrix_path: Path = MATRIX_PATH, out_path: Path = SUMMARY_PATH) -> str:
    data = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])

    route_status = Counter(e.get("actual_probe", {}).get("route_status") for e in entries)
    db_status = Counter(e.get("actual_probe", {}).get("db_status") for e in entries)
    gap_type = Counter(e.get("gap_type") for e in entries)
    scenario = Counter(e.get("scenario") for e in entries)

    candidates = [e for e in entries if e.get("skill_update_candidate")]
    blocked = [e for e in entries if e.get("actual_probe", {}).get("route_status") == "blocked"]
    stub_partial = [
        e for e in entries if e.get("gap_type") == "implementation" or e.get("actual_probe", {}).get("db_status") == "stub"
    ]

    lines = [
        "# Eval Route Gaps Summary",
        "",
        f"- Total entries: {len(entries)}",
        f"- Last wave: {data.get('meta', {}).get('last_wave', '?')}",
        "",
        "## Route Status",
        "",
    ]
    for k, v in sorted(route_status.items()):
        lines.append(f"- {k}: {v}")

    lines.extend(["", "## DB Status", ""])
    for k, v in sorted(db_status.items()):
        lines.append(f"- {k}: {v}")

    lines.extend(["", "## Gap Type", ""])
    for k, v in sorted(gap_type.items()):
        lines.append(f"- {k}: {v}")

    lines.extend(["", "## By Scenario", ""])
    for k, v in sorted(scenario.items()):
        lines.append(f"- {k}: {v}")

    lines.extend(["", "## Skill Update Candidates (P0 verified)", ""])
    for e in candidates:
        lines.append(f"- {e['type_id']} ({e.get('type_name', '')})")

    lines.extend(["", "## Top Implementation Gaps (stub tools)", ""])
    seen: set[str] = set()
    for e in stub_partial[:30]:
        tid = e["type_id"]
        if tid not in seen:
            seen.add(tid)
            lines.append(f"- {tid}: {e.get('gap') or 'stub'}")

    lines.extend(["", "## Blocked Types", ""])
    for e in blocked[:20]:
        lines.append(f"- {e['type_id']}: {e.get('gap')}")

    text = "\n".join(lines) + "\n"
    out_path.write_text(text, encoding="utf-8")
    print(f"Summary -> {out_path}")
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=MATRIX_PATH)
    parser.add_argument("--out", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()
    build_summary(args.matrix, args.out)


if __name__ == "__main__":
    main()
