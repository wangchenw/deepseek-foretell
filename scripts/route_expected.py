"""Expected routes and probe heuristics for eval type_ids."""

from __future__ import annotations

from typing import Any

SCENARIO_SKILL: dict[str, str] = {
    "A": "foretell-light-query",
    "B": "foretell-match-analysis",
    "C": "foretell-post-review",
    "D": "foretell-betting-single",
    "E": "foretell-batch-screening",
    "F": "foretell-odds-query",
    "G": "foretell-follow-up",
    "H": "foretell-league-outlook",
    "X": "foretell-output-discipline",
}

SCENARIO_SUBAGENTS: dict[str, list[str]] = {
    "A": ["entity-resolver"],
    "B": ["entity-resolver", "fundamentals-analyst", "odds-analyst", "intel-analyst"],
    "C": ["entity-resolver"],
    "D": ["entity-resolver", "fundamentals-analyst", "odds-analyst", "intel-analyst"],
    "E": ["screening-agent"],
    "F": ["odds-analyst"],
    "G": [],
    "H": ["entity-resolver"],
    "X": [],
}

STUB_TOOLS = frozenset({
    "get_team_season_stats",
    "get_odds_trend",
    "get_same_odds_history",
    "get_kelly",
    "get_betfair",
    "get_match_lineup",
    "get_injury_report",
    "get_intel_tags",
})

TYPE_TOOL_OVERRIDES: dict[str, list[dict[str, Any]]] = {
    "A08": [
        {"name": "resolve_team", "params": {"name": "葡萄牙"}},
        {"name": "get_team_schedule", "params": {"team_id": "$team_id", "direction": "all", "limit": 5}},
        {"name": "get_schedule_by_date", "params": {"date": "$today", "tier": "top"}},
    ],
    "A17": [
        {"name": "resolve_team", "params": {"name": "法国"}},
        {"name": "get_team_schedule", "params": {"team_id": "$team_id", "direction": "all", "limit": 10}},
    ],
    "B01": [
        {"name": "resolve_lottery_match", "params": {"play_type": "101", "code": "009", "date": "2026-06-15"}},
    ],
    "B09": [
        {"name": "resolve_match", "params": {"home": "马刺", "away": "雷霆", "series_game": 7}},
    ],
    "E05": [
        {"name": "get_lottery_schedule", "params": {"play_type": "401"}},
    ],
    "X05": [
        {"name": "resolve_team", "params": {"name": "葡萄牙"}},
        {"name": "get_team_schedule", "params": {"team_id": "$team_id", "direction": "all", "limit": 5}},
    ],
    "X06": [
        {"name": "resolve_match", "params": {"home": "法国", "away": "挪威"}},
    ],
    "X12": [
        {"name": "resolve_match", "params": {"home": "法国", "away": "挪威", "date": "2024-06-27"}},
    ],
}

ENTITY_ENTRY_TOOLS: dict[str, list[str]] = {
    "date": ["get_schedule_by_date", "get_lottery_schedule"],
    "date+league": ["get_schedule_by_date"],
    "team": ["resolve_team", "get_team_schedule"],
    "team+time": ["resolve_team", "get_team_schedule", "get_schedule_by_date"],
    "team+competition": ["resolve_team", "get_team_schedule"],
    "match": ["resolve_match", "get_match_result"],
    "match_pair": ["resolve_match"],
    "match_pair+date": ["resolve_match"],
    "match_pair+series": ["resolve_match"],
    "league": ["resolve_league", "get_standings"],
    "team_pair": ["resolve_team", "get_h2h"],
    "lottery_code": ["resolve_lottery_match", "get_lottery_schedule"],
    "lottery_batch": ["get_lottery_schedule"],
    "lottery_period": ["get_lottery_schedule"],
    "batch": ["get_lottery_schedule"],
    "context": [],
    "none": [],
    "unknown": [],
}


def expected_skill(scenario: str) -> str:
    return SCENARIO_SKILL.get(scenario, "foretell-light-query")


def expected_subagents(scenario: str, type_id: str) -> list[str]:
    if type_id in {"A08", "A17", "X05", "X06", "X12"}:
        return ["entity-resolver"]
    return list(SCENARIO_SUBAGENTS.get(scenario, []))


def expected_tools(type_id: str, scenario: str, entity_entry: str) -> list[dict[str, Any]]:
    if type_id in TYPE_TOOL_OVERRIDES:
        return [dict(t) for t in TYPE_TOOL_OVERRIDES[type_id]]

    tools = list(ENTITY_ENTRY_TOOLS.get(entity_entry, ENTITY_ENTRY_TOOLS["unknown"]))

    if scenario == "B":
        tools.extend(["get_recent_form", "get_h2h", "get_odds_snapshot", "get_match_lineup", "get_injury_report"])
    elif scenario == "C":
        tools = ["resolve_match", "get_match_result"]
    elif scenario == "F":
        tools = ["resolve_match", "get_odds_snapshot", "get_odds_trend", "get_kelly", "get_betfair"]
    elif scenario == "E":
        tools = ["get_lottery_schedule", "get_recent_form", "get_odds_snapshot"]
    elif scenario == "H":
        tools = ["resolve_league", "get_standings", "get_team_schedule"]
    elif scenario == "G":
        tools = ["resolve_lottery_match"]
    elif scenario == "X":
        tools = []

    seen: set[str] = set()
    ordered: list[dict[str, Any]] = []
    for name in tools:
        if name not in seen:
            seen.add(name)
            ordered.append({"name": name, "params": {}})
    return ordered


def infer_fallback(scenario: str, tools: list[dict[str, Any]]) -> str:
    if scenario == "X":
        return "honest_decline"
    tool_names = {t["name"] for t in tools}
    if tool_names & STUB_TOOLS:
        return "internet_search"
    if not tool_names:
        return "honest_decline"
    return "none"
