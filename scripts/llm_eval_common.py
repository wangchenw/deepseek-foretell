"""Shared schemas, loaders, and paths for Foretell LLM Eval Phase 1."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = PROJECT_ROOT / "data" / "eval"

P0_TYPE_IDS: tuple[str, ...] = (
    "A08",
    "A17",
    "X05",
    "X06",
    "X12",
    "B01",
    "B09",
    "E05",
    "G01",
    "G07",
)

ATOMIC_CATEGORIES: tuple[str, ...] = (
    "resolve_entity",
    "fetch_schedule",
    "fetch_stats",
    "fetch_odds_snapshot",
    "fetch_odds_deep",
    "fetch_intel",
    "fetch_result",
    "discover_via_search",
    "delegate_subagent",
    "refine_time_window",
    "maintain_context",
    "synthesize_answer",
    "apply_guardrails",
    "cross_validation",
)

LLM_EVAL_DIMENSIONS: tuple[str, ...] = (
    "correctness",
    "completeness",
    "no_false_negative",
    "path_efficiency",
    "output_discipline",
    "context_handling",
    "scenario_compliance",
)

LLM_EVAL_WEIGHTS: dict[str, float] = {
    "correctness": 0.30,
    "completeness": 0.20,
    "no_false_negative": 0.20,
    "path_efficiency": 0.10,
    "output_discipline": 0.10,
    "context_handling": 0.05,
    "scenario_compliance": 0.05,
}

DIMENSION_THRESHOLD = 3.0
OVERALL_THRESHOLD = 3.5

ATOMIC_DIR = EVAL_DIR / "atomic_decompositions"
PATH_DIR = EVAL_DIR / "path_attempts"
PLAYBOOKS_PATH = EVAL_DIR / "answer_playbooks.yaml"
ROUTE_MATRIX_PATH = EVAL_DIR / "route_matrix.yaml"
ROUTE_MATRIX_MERGED_PATH = EVAL_DIR / "route_matrix_merged.yaml"
PROBE_CASES_PATH = EVAL_DIR / "probe_cases.yaml"
TEST_CASES_PATH = PROJECT_ROOT / "tests" / "eval" / "test_cases.yaml"
SUMMARY_PATH = EVAL_DIR / "llm_eval_summary.md"


def ensure_dirs() -> None:
    ATOMIC_DIR.mkdir(parents=True, exist_ok=True)
    PATH_DIR.mkdir(parents=True, exist_ok=True)


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def load_probe_case(type_id: str) -> dict[str, Any] | None:
    data = load_yaml(PROBE_CASES_PATH)
    for case in data.get("cases", []):
        if case.get("type_id") == type_id:
            return case
    return None


def load_test_case(type_id: str) -> dict[str, Any] | None:
    if not TEST_CASES_PATH.exists():
        return None
    data = load_yaml(TEST_CASES_PATH)
    for case in data.get("cases", []):
        if case.get("type_id") == type_id:
            return case
    return None


def load_route_matrix_entry(type_id: str) -> dict[str, Any] | None:
    matrix = load_yaml(ROUTE_MATRIX_PATH)
    for entry in matrix.get("entries", []):
        if entry.get("type_id") == type_id:
            return entry
    return None


def load_probe_result(type_id: str) -> dict[str, Any] | None:
    path = EVAL_DIR / "probe_results" / f"{type_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_atomic_decomposition(type_id: str) -> dict[str, Any]:
    path = ATOMIC_DIR / f"{type_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Missing atomic decomposition: {path}")
    return load_yaml(path)


def weighted_overall(scores: dict[str, float]) -> float:
    total = 0.0
    for dim, weight in LLM_EVAL_WEIGHTS.items():
        total += scores.get(dim, 0.0) * weight
    return round(total, 2)


def p0_pass(scores: dict[str, float]) -> bool:
    overall = weighted_overall(scores)
    if overall < OVERALL_THRESHOLD:
        return False
    return all(scores.get(dim, 0.0) >= DIMENSION_THRESHOLD for dim in LLM_EVAL_DIMENSIONS)


def p0_case_bundle(type_id: str) -> dict[str, Any]:
    probe = load_probe_case(type_id) or {}
    test = load_test_case(type_id) or {}
    route = load_route_matrix_entry(type_id) or {}
    return {
        "type_id": type_id,
        "probe_case": probe,
        "test_case": test,
        "route_matrix": route,
        "turns": test.get("turns") or probe.get("full_turns") or probe.get("probe_turns") or [],
        "expected_behaviors": test.get("expected_behaviors") or [],
    }


def today_iso() -> str:
    return date.today().isoformat()
