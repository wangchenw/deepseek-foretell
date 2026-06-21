"""疯狂体育 API 客户端抽象与 Mock 实现。"""

from __future__ import annotations

from typing import Protocol

from config.settings import get_settings
from foretell.tools.crazy_sports.mock_data import (
    BETFAIR,
    DEFAULT_FRESHNESS,
    H2H,
    INJURY_REPORT,
    INTEL_TAGS,
    KELLY,
    LEAGUES,
    LOTTERY_MATCHES,
    LOTTERY_SCHEDULE,
    MATCHES,
    MATCH_LINEUP,
    ODDS_SNAPSHOT,
    ODDS_TREND,
    RECENT_FORM,
    SAME_ODDS_HISTORY,
    SCHEDULE_BY_DATE,
    STANDINGS,
    TEAM_SCHEDULE,
    TEAM_SEASON_STATS,
    TEAMS,
)
from foretell.tools.status_codes import PlayType


def _normalize_name(name: str) -> str:
    return name.strip().lower().replace(" ", "")


def _match_team_name(query: str, team: dict) -> bool:
    q = _normalize_name(query)
    candidates = [team["name"], team.get("name_en", "")]
    candidates.extend(team.get("aliases", []))
    return any(_normalize_name(c) == q or q in _normalize_name(c) for c in candidates if c)


def _match_league_name(query: str, league: dict) -> bool:
    q = _normalize_name(query)
    candidates = [league["name"], league.get("name_en", "")]
    candidates.extend(league.get("aliases", []))
    return any(_normalize_name(c) == q or q in _normalize_name(c) for c in candidates if c)


class CrazySportsClient(Protocol):
    """疯狂体育只读数据访问协议。"""

    def resolve_match(
        self,
        home: str,
        away: str,
        date: str | None = None,
        series_game: int | None = None,
    ) -> dict | None:
        """按主客队定位比赛，未找到返回 None。"""

    def resolve_lottery_match(
        self,
        play_type: PlayType,
        code: str,
        date: str | None = None,
    ) -> dict | None:
        """按玩法与场次编号定位竞彩比赛。"""

    def resolve_team(self, name: str) -> dict | None:
        """按名称定位球队。"""

    def resolve_league(self, name: str) -> dict | None:
        """按名称定位联赛。"""

    def get_schedule_by_date(
        self,
        date: str,
        sport: str | None = None,
        league_preset: str | None = None,
    ) -> list[dict]:
        """按日期返回赛程列表。"""

    def get_team_schedule(self, team_id: str, limit: int = 5) -> list[dict]:
        """返回球队近期/未来赛程。"""

    def get_lottery_schedule(
        self,
        play_type: PlayType,
        date: str | None = None,
        period: str | None = None,
    ) -> list[dict]:
        """返回彩票可售场次列表。"""

    def get_standings(self, league_id: str) -> list[dict]:
        """返回联赛积分榜。"""

    def get_team_season_stats(self, team_id: str) -> dict | None:
        """返回球队赛季统计。"""

    def get_recent_form(
        self,
        team_id: str,
        venue: str | None = None,
        n: int = 5,
    ) -> list[dict]:
        """返回球队近期战绩。"""

    def get_h2h(self, team_a: str, team_b: str, n: int = 5) -> list[dict]:
        """返回两队历史交锋。"""

    def get_odds_snapshot(self, match_id: str) -> dict | None:
        """返回盘口快照。"""

    def get_odds_trend(self, match_id: str) -> list[dict]:
        """返回赔率走势。"""

    def get_same_odds_history(self, match_id: str) -> list[dict]:
        """返回同赔历史。"""

    def get_kelly(self, match_id: str) -> dict | None:
        """返回凯利指数。"""

    def get_betfair(self, match_id: str) -> dict | None:
        """返回必发成交数据。"""

    def get_match_lineup(self, match_id: str) -> dict | None:
        """返回预计阵容。"""

    def get_injury_report(self, match_id: str) -> dict | None:
        """返回伤停报告。"""

    def get_intel_tags(self, match_id: str) -> list[dict]:
        """返回情报标签。"""

    @property
    def freshness(self) -> str:
        """数据新鲜度标识。"""


class MockCrazySportsClient:
    """基于固定样本数据的 Mock 客户端，用于开发与测试。"""

    @property
    def freshness(self) -> str:
        return DEFAULT_FRESHNESS

    def resolve_match(
        self,
        home: str,
        away: str,
        date: str | None = None,
        series_game: int | None = None,
    ) -> dict | None:
        candidates = []
        for match in MATCHES.values():
            home_ok = _match_team_name(home, TEAMS[match["home_team_id"]])
            away_ok = _match_team_name(away, TEAMS[match["away_team_id"]])
            if not (home_ok and away_ok):
                continue
            if date is not None and match["date"] != date:
                continue
            if series_game is not None:
                if match.get("series_game") != series_game:
                    continue
            elif match.get("series_game") is not None:
                # 未指定系列赛场次时，跳过系列赛场次
                continue
            candidates.append(match)

        if not candidates:
            return None
        if len(candidates) == 1:
            return dict(candidates[0])
        # 多场匹配时返回最近一场
        return dict(sorted(candidates, key=lambda m: m["date"], reverse=True)[0])

    def resolve_lottery_match(
        self,
        play_type: PlayType,
        code: str,
        date: str | None = None,
    ) -> dict | None:
        key = f"{play_type.value}:{code}"
        entry = LOTTERY_MATCHES.get(key)
        if entry is None:
            return None
        if date is not None and entry.get("date") != date:
            return None
        result = dict(entry)
        match = MATCHES.get(entry["match_id"])
        if match:
            result["match"] = dict(match)
        return result

    def resolve_team(self, name: str) -> dict | None:
        for team in TEAMS.values():
            if _match_team_name(name, team):
                return dict(team)
        return None

    def resolve_league(self, name: str) -> dict | None:
        for league in LEAGUES.values():
            if _match_league_name(name, league):
                return dict(league)
        return None

    def get_schedule_by_date(
        self,
        date: str,
        sport: str | None = None,
        league_preset: str | None = None,
    ) -> list[dict]:
        match_ids = SCHEDULE_BY_DATE.get(date, [])
        results = []
        for mid in match_ids:
            match = MATCHES[mid]
            if sport is not None and match["sport"] != sport:
                continue
            if league_preset is not None:
                league = LEAGUES.get(match["league_id"])
                if league is None or not _match_league_name(league_preset, league):
                    continue
            results.append(dict(match))
        return results

    def get_team_schedule(self, team_id: str, limit: int = 5) -> list[dict]:
        match_ids = TEAM_SCHEDULE.get(team_id, [])[:limit]
        return [dict(MATCHES[mid]) for mid in match_ids]

    def get_lottery_schedule(
        self,
        play_type: PlayType,
        date: str | None = None,
        period: str | None = None,
    ) -> list[dict]:
        if date is None:
            date = "2026-06-21"
        key = f"{play_type.value}:{date}"
        entries = LOTTERY_SCHEDULE.get(key, [])
        return [dict(e) for e in entries]

    def get_standings(self, league_id: str) -> list[dict]:
        return [dict(row) for row in STANDINGS.get(league_id, [])]

    def get_team_season_stats(self, team_id: str) -> dict | None:
        stats = TEAM_SEASON_STATS.get(team_id)
        return dict(stats) if stats else None

    def get_recent_form(
        self,
        team_id: str,
        venue: str | None = None,
        n: int = 5,
    ) -> list[dict]:
        form = RECENT_FORM.get(team_id, [])
        if venue is not None:
            form = [r for r in form if r.get("venue") == venue]
        return [dict(r) for r in form[:n]]

    def get_h2h(self, team_a: str, team_b: str, n: int = 5) -> list[dict]:
        key = "|".join(sorted([team_a, team_b]))
        return [dict(r) for r in H2H.get(key, [])[:n]]

    def get_odds_snapshot(self, match_id: str) -> dict | None:
        odds = ODDS_SNAPSHOT.get(match_id)
        return dict(odds) if odds else None

    def get_odds_trend(self, match_id: str) -> list[dict]:
        return [dict(r) for r in ODDS_TREND.get(match_id, [])]

    def get_same_odds_history(self, match_id: str) -> list[dict]:
        return [dict(r) for r in SAME_ODDS_HISTORY.get(match_id, [])]

    def get_kelly(self, match_id: str) -> dict | None:
        kelly = KELLY.get(match_id)
        return dict(kelly) if kelly else None

    def get_betfair(self, match_id: str) -> dict | None:
        betfair = BETFAIR.get(match_id)
        return dict(betfair) if betfair else None

    def get_match_lineup(self, match_id: str) -> dict | None:
        lineup = MATCH_LINEUP.get(match_id)
        return dict(lineup) if lineup else None

    def get_injury_report(self, match_id: str) -> dict | None:
        report = INJURY_REPORT.get(match_id)
        return dict(report) if report else None

    def get_intel_tags(self, match_id: str) -> list[dict]:
        return [dict(t) for t in INTEL_TAGS.get(match_id, [])]


def get_crazy_sports_client() -> CrazySportsClient:
    """根据配置返回疯狂体育客户端实例。

    当前仅实现 Mock；真实 API 客户端在 Phase 4 接入。
    """
    settings = get_settings()
    if settings.crazy_sports_api_base and settings.crazy_sports_api_key:
        # Phase 4: 返回真实客户端
        pass
    return MockCrazySportsClient()
