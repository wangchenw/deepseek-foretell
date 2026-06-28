#!/usr/bin/env python3
"""Run tool-chain probe for a single eval type_id."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from route_probe_registry import get_probe_fn  # noqa: E402

PROBE_RESULTS = Path(__file__).resolve().parent.parent / "data" / "eval" / "probe_results"
PROBE_CASES = Path(__file__).resolve().parent.parent / "data" / "eval" / "probe_cases.yaml"


def _load_case(type_id: str) -> dict | None:
    import yaml

    data = yaml.safe_load(PROBE_CASES.read_text(encoding="utf-8"))
    for case in data.get("cases", []):
        if case["type_id"] == type_id:
            return case
    return None


def run_probe(type_id: str, *, dry_run: bool = False) -> dict:
    case = _load_case(type_id)
    if not case:
        raise SystemExit(f"Unknown type_id: {type_id}")

    probe_fn = get_probe_fn(type_id, case.get("entity_entry", ""))
    result = {
        "type_id": type_id,
        "case_id": case.get("case_id"),
        "probe_status": case.get("probe_status"),
        "dry_run": dry_run,
        "steps": [],
        "error": None,
    }

    if dry_run or probe_fn is None:
        result["skipped"] = True
        result["reason"] = "dry_run" if dry_run else "no_probe_registered"
        return result

    try:
        result["steps"] = probe_fn()
    except Exception as exc:  # noqa: BLE001 — probe script surfaces errors
        result["error"] = str(exc)

    PROBE_RESULTS.mkdir(parents=True, exist_ok=True)
    out = PROBE_RESULTS / f"{type_id}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Probe {type_id}: {len(result['steps'])} steps -> {out}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True, help="type_id e.g. A08")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = run_probe(args.type.upper(), dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
