#!/usr/bin/env python3
"""Merge scenario_*.yaml into route_matrix.yaml."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

EVAL_DIR = Path(__file__).resolve().parent.parent / "data" / "eval"
ROUTES_DIR = EVAL_DIR / "routes"
MATRIX_PATH = EVAL_DIR / "route_matrix.yaml"


def merge(last_wave: str | None = None) -> dict:
    entries: list[dict] = []
    waves: list[str] = []

    for path in sorted(ROUTES_DIR.glob("scenario_*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        wave = data.get("scenario", path.stem.replace("scenario_", ""))
        waves.append(wave)
        entries.extend(data.get("entries", []))

    entries.sort(key=lambda e: e.get("type_id", ""))
    last = last_wave or (waves[-1] if waves else "")

    status_counts: dict[str, int] = {}
    for e in entries:
        rs = e.get("actual_probe", {}).get("route_status", "unknown")
        status_counts[rs] = status_counts.get(rs, 0) + 1

    matrix = {
        "version": "1.0",
        "meta": {
            "explored": len(entries),
            "total": 120,
            "last_wave": last,
            "waves_merged": sorted(set(waves)),
            "route_status_distribution": status_counts,
        },
        "entries": entries,
    }
    MATRIX_PATH.write_text(yaml.dump(matrix, allow_unicode=True, sort_keys=False, default_flow_style=False), encoding="utf-8")
    print(f"Merged {len(entries)} entries -> {MATRIX_PATH}")
    return matrix


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--last-wave", default=None)
    args = parser.parse_args()
    merge(args.last_wave)


if __name__ == "__main__":
    main()
