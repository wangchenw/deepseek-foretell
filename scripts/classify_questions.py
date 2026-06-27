#!/usr/bin/env python3
"""Classify raw session questions against taxonomy."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_common import (  # noqa: E402
    classify_session_turns,
    classify_text,
    complexity_score,
    ensure_eval_dir,
    load_taxonomy,
    normalize_question,
)

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "eval" / "raw_questions.jsonl"
CLASSIFIED_PATH = Path(__file__).resolve().parent.parent / "data" / "eval" / "classified_by_type.json"
STATS_PATH = Path(__file__).resolve().parent.parent / "data" / "eval" / "classification_stats.json"


def classify_raw(input_path: Path = RAW_PATH, output_path: Path = CLASSIFIED_PATH) -> dict:
    taxonomy = load_taxonomy()
    by_type: dict[str, list[dict]] = defaultdict(list)
    stats = Counter()
    unclassified: list[dict] = []

    with input_path.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            turns = [t["content"] for t in rec.get("turns", [])]
            if not turns:
                continue

            norm_first, pattern_hash = normalize_question(turns[0])
            cls = classify_session_turns(turns, taxonomy)
            primary_id = cls["primary_type_id"]
            score = complexity_score(turns, primary_id, taxonomy)

            # Collect all matching type ids across turns
            all_type_ids: set[str] = set()
            if primary_id:
                all_type_ids.add(primary_id)
            for turn in turns[1:]:
                matched = classify_text(turn, taxonomy)
                if matched:
                    all_type_ids.add(matched.id)

            enriched = {
                **rec,
                "turns_text": turns,
                "normalized_first": norm_first,
                "pattern_hash": pattern_hash,
                "classification": cls,
                "all_type_ids": sorted(all_type_ids),
                "complexity_score": score,
            }

            if primary_id:
                by_type[primary_id].append(enriched)
                stats[primary_id] += 1
            else:
                assigned = False
                for turn in turns[1:]:
                    follow_match = classify_text(turn, taxonomy)
                    if follow_match:
                        by_type[follow_match.id].append(enriched)
                        stats[follow_match.id] += 1
                        assigned = True
                        break
                if not assigned:
                    unclassified.append(enriched)
                    stats["UNCLASSIFIED"] += 1

            # Index under all matched types for follow-up rich sessions
            for tid in all_type_ids:
                if tid != primary_id and enriched not in by_type[tid]:
                    by_type[tid].append(enriched)

    ensure_eval_dir()
    result = {
        "by_type": dict(by_type),
        "unclassified": unclassified,
        "stats": dict(stats),
        "total_sessions": sum(stats.values()),
    }
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    stats_summary = {
        "total_sessions": result["total_sessions"],
        "classified_types": len(by_type),
        "unclassified_count": len(unclassified),
        "top_types": stats.most_common(30),
        "multi_turn_count": sum(
            1 for items in by_type.values() for item in items if len(item.get("turns_text", [])) >= 2
        ),
    }
    STATS_PATH.write_text(json.dumps(stats_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Classified {result['total_sessions']} sessions into {len(by_type)} types")
    print(f"Unclassified: {len(unclassified)}")
    print(f"Wrote {output_path} and {STATS_PATH}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=RAW_PATH)
    parser.add_argument("--output", type=Path, default=CLASSIFIED_PATH)
    args = parser.parse_args()
    classify_raw(args.input, args.output)


if __name__ == "__main__":
    main()
