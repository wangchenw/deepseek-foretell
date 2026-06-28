"""Registry of executable probe sequences for P0 and generic entity_entry probes."""

from __future__ import annotations

from datetime import date
from typing import Any, Callable

ProbeFn = Callable[[], list[dict[str, Any]]]


def _parse_json(result: str) -> dict:
    import json

    return json.loads(result)


def _national_team_id(data: dict) -> int | None:
    candidates = data.get("data", {}).get("candidates") or []
    for c in candidates:
        if c.get("national") == 1:
            return c["team_id"]
    return candidates[0]["team_id"] if candidates else None


def _probe_resolve_team_schedule(
    team_name: str,
    *,
    direction: str = "all",
    limit: int = 5,
    prefer_national: bool = False,
) -> list[dict[str, Any]]:
    from foretell.tools.entity import resolve_team
    from foretell.tools.schedule import get_team_schedule

    steps: list[dict[str, Any]] = []
    team_raw = resolve_team.invoke({"name": team_name})
    team = _parse_json(team_raw)
    steps.append({"tool": "resolve_team", "params": {"name": team_name}, "code": team.get("code"), "stub": False})

    if team.get("code") != "OK":
        return steps

    if prefer_national:
        team_id = _national_team_id(team)
    else:
        team_id = team["data"]["candidates"][0]["team_id"]

    sched_raw = get_team_schedule.invoke({"team_id": team_id, "direction": direction, "limit": limit})
    sched = _parse_json(sched_raw)
    steps.append(
        {
            "tool": "get_team_schedule",
            "params": {"team_id": team_id, "direction": direction, "limit": limit},
            "code": sched.get("code"),
            "count": sched.get("data", {}).get("count"),
            "stub": False,
        }
    )
    return steps


def _probe_schedule_today() -> list[dict[str, Any]]:
    from foretell.tools.schedule import get_schedule_by_date

    today = date.today().isoformat()
    raw = get_schedule_by_date.invoke({"date": today, "tier": "top"})
    data = _parse_json(raw)
    return [
        {
            "tool": "get_schedule_by_date",
            "params": {"date": today, "tier": "top"},
            "code": data.get("code"),
            "count": data.get("data", {}).get("count"),
            "stub": False,
        }
    ]


def _probe_lottery(play_type: str = "101") -> list[dict[str, Any]]:
    from foretell.tools.schedule import get_lottery_schedule

    raw = get_lottery_schedule.invoke({"play_type": play_type})
    data = _parse_json(raw)
    return [
        {
            "tool": "get_lottery_schedule",
            "params": {"play_type": play_type},
            "code": data.get("code"),
            "count": data.get("data", {}).get("count"),
            "stub": False,
        }
    ]


def _probe_resolve_match(home: str, away: str, **kwargs: Any) -> list[dict[str, Any]]:
    from foretell.tools.entity import resolve_match

    params = {"home": home, "away": away, **kwargs}
    raw = resolve_match.invoke(params)
    data = _parse_json(raw)
    return [
        {
            "tool": "resolve_match",
            "params": params,
            "code": data.get("code"),
            "count": data.get("data", {}).get("count"),
            "stub": False,
        }
    ]


def _probe_lottery_match(code: str, match_date: str | None = None, play_type: str = "101") -> list[dict[str, Any]]:
    from foretell.tools.entity import resolve_lottery_match

    params: dict[str, Any] = {"play_type": play_type, "code": code}
    if match_date:
        params["date"] = match_date
    raw = resolve_lottery_match.invoke(params)
    data = _parse_json(raw)
    return [
        {
            "tool": "resolve_lottery_match",
            "params": params,
            "code": data.get("code"),
            "stub": False,
        }
    ]


def _probe_standings(league: str = "英超") -> list[dict[str, Any]]:
    from foretell.tools.entity import resolve_league
    from foretell.tools.stats import get_standings

    steps: list[dict[str, Any]] = []
    league_raw = resolve_league.invoke({"name": league})
    league_data = _parse_json(league_raw)
    steps.append({"tool": "resolve_league", "params": {"name": league}, "code": league_data.get("code"), "stub": False})
    if league_data.get("code") != "OK":
        return steps
    league_id = league_data["data"]["candidates"][0]["league_id"]
    stand_raw = get_standings.invoke({"league_id": league_id})
    stand = _parse_json(stand_raw)
    steps.append(
        {
            "tool": "get_standings",
            "params": {"league_id": league_id},
            "code": stand.get("code"),
            "count": stand.get("data", {}).get("count"),
            "stub": False,
        }
    )
    return steps


def _probe_odds_snapshot() -> list[dict[str, Any]]:
    from foretell.tools.odds import get_odds_snapshot, get_odds_trend, get_kelly

    steps = _probe_resolve_match("利物浦", "切尔西")
    if steps[0].get("code") != "OK":
        return steps
    # use dummy match_id=1 if ambiguous — skip if no match
    return steps + [
        {"tool": "get_odds_snapshot", "params": {"match_id": 1}, "code": "STUB_CHECK", "stub": True},
        {"tool": "get_odds_trend", "params": {"match_id": 1}, "code": "STUB", "stub": True},
        {"tool": "get_kelly", "params": {"match_id": 1}, "code": "STUB", "stub": True},
    ]


TYPE_PROBES: dict[str, ProbeFn] = {
    "A08": lambda: _probe_resolve_team_schedule("葡萄牙", direction="all", limit=5, prefer_national=True)
    + _probe_schedule_today(),
    "A17": lambda: _probe_resolve_team_schedule("法国", direction="all", limit=10, prefer_national=True),
    "B01": lambda: _probe_lottery_match("009", "2026-06-15", play_type="101"),
    "B09": lambda: _probe_resolve_match("马刺", "雷霆", series_game=7),
    "E05": lambda: _probe_lottery("401"),
    "X05": lambda: _probe_resolve_team_schedule("葡萄牙", direction="all", limit=5, prefer_national=True),
    "X06": lambda: _probe_resolve_match("法国", "挪威"),
    "G01": lambda: _probe_lottery_match("004", play_type="101"),
    "G02": lambda: _probe_lottery_match("004", play_type="101"),
    "G07": lambda: _probe_lottery("301") + _probe_schedule_today(),
    "X12": lambda: _probe_resolve_match("法国", "挪威", date="2024-06-27")
    + _probe_resolve_match("法国", "挪威")
    + _probe_resolve_match("法国", "挪威", date="2026-06-27")
    + _probe_resolve_match("挪威", "法国", date="2026-06-27"),
}

ENTITY_ENTRY_PROBES: dict[str, ProbeFn] = {
    "date": _probe_schedule_today,
    "date+league": lambda: _probe_schedule_today(),
    "team": lambda: _probe_resolve_team_schedule("利物浦", direction="upcoming", limit=3),
    "team+time": lambda: _probe_resolve_team_schedule("葡萄牙", direction="all", limit=5, prefer_national=True),
    "team+competition": lambda: _probe_resolve_team_schedule("法国", direction="all", limit=5, prefer_national=True),
    "match": lambda: _probe_resolve_match("皇马", "巴萨"),
    "match_pair": lambda: _probe_resolve_match("利物浦", "热刺"),
    "match_pair+date": lambda: _probe_resolve_match("法国", "挪威", date="2026-06-27"),
    "match_pair+series": lambda: _probe_resolve_match("马刺", "雷霆", series_game=7),
    "league": _probe_standings,
    "team_pair": lambda: _probe_resolve_team_schedule("利物浦", direction="recent", limit=5),
    "lottery_code": lambda: _probe_lottery_match("004", play_type="101"),
    "lottery_batch": lambda: _probe_lottery("101"),
    "lottery_period": lambda: _probe_lottery("401"),
    "batch": lambda: _probe_lottery("101"),
}


def get_probe_fn(type_id: str, entity_entry: str) -> ProbeFn | None:
    if type_id in TYPE_PROBES:
        return TYPE_PROBES[type_id]
    return ENTITY_ENTRY_PROBES.get(entity_entry)
