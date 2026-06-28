"""疯狂体育 API 客户端抽象与 MySQL 工厂。"""

from __future__ import annotations

from typing import Literal, Protocol

from config.settings import get_settings
from foretell.tools.status_codes import PlayType


class CrazySportsClient(Protocol):
    """疯狂体育只读数据访问协议。"""

    def resolve_match(
        self,
        home: str,
        away: str,
        date: str | None = None,
        series_game: int | None = None,
    ) -> list[dict]:
        """按主客队模糊查询比赛，返回候选列表。"""

    def resolve_lottery_match(
        self,
        play_type: PlayType,
        code: str,
        date: str | None = None,
    ) -> dict | None:
        """按玩法与场次编号定位竞彩比赛。"""

    def resolve_team(self, name: str) -> list[dict]:
        """按名称模糊查询球队，返回候选列表。"""

    def resolve_league(self, name: str) -> list[dict]:
        """按名称模糊查询联赛，返回候选列表。"""

    def get_schedule_by_date(
        self,
        date: str,
        sport: str | None = None,
        league_preset: str | None = None,
        tier: Literal["top", "all"] | None = None,
    ) -> dict:
        """按日期返回赛程列表与截断元信息。"""

    def get_team_schedule(
        self,
        team_id: int | str,
        limit: int = 5,
        league_id: int | str | None = None,
        direction: Literal["upcoming", "recent", "all"] = "recent",
    ) -> list[dict]:
        """返回球队近期/未来赛程。"""

    def get_lottery_schedule(
        self,
        play_type: PlayType,
        date: str | None = None,
        period: str | None = None,
    ) -> list[dict]:
        """返回彩票可售场次列表。"""

    def get_standings(self, league_id: int | str) -> list[dict]:
        """返回联赛积分榜。"""

    def get_team_season_stats(self, team_id: int | str) -> dict | None:
        """返回球队赛季统计。"""

    def get_recent_form(
        self,
        team_id: int | str,
        venue: str | None = None,
        n: int = 5,
    ) -> list[dict]:
        """返回球队近期战绩。"""

    def get_h2h(self, team_a: int | str, team_b: int | str, n: int = 5) -> list[dict]:
        """返回两队历史交锋。"""

    def get_odds_snapshot(self, match_id: int | str) -> dict | None:
        """返回盘口快照。"""

    def get_odds_trend(self, match_id: int | str) -> list[dict]:
        """返回赔率走势。"""

    def get_same_odds_history(self, match_id: int | str) -> list[dict]:
        """返回同赔历史。"""

    def get_kelly(self, match_id: int | str) -> dict | None:
        """返回凯利指数。"""

    def get_betfair(self, match_id: int | str) -> dict | None:
        """返回必发成交数据。"""

    def get_match_lineup(self, match_id: int | str) -> dict | None:
        """返回预计阵容。"""

    def get_injury_report(self, match_id: int | str) -> dict | None:
        """返回伤停报告。"""

    def get_intel_tags(self, match_id: int | str) -> list[dict]:
        """返回情报标签。"""

    def get_match_by_id(self, match_id: int | str) -> dict | None:
        """按 ID 返回比赛基础信息。"""

    def get_match_result(self, match_id: int | str) -> dict | None:
        """返回已完场比赛的赛果与复盘数据。"""

    def get_top_scorers(self, competition_id: int | str, limit: int = 20) -> list[dict]:
        """返回赛事当前赛季射手榜。"""

    def get_team_squad(self, team_id: int | str) -> list[dict]:
        """返回球队大名单。"""

    def get_series_matchup(
        self,
        sport: str,
        team_id: int | str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """返回系列赛对阵（含 NBA 季后赛 G7 等多回合对阵）。"""

    def get_basketball_standings(self, league_id: int | str) -> list[dict]:
        """返回篮球联赛积分榜。"""

    def get_match_tlive(self, match_id: int | str, limit: int = 100) -> list[dict]:
        """返回比赛实时文字直播事件流。"""

    def get_match_incidents(self, match_id: int | str) -> list[dict]:
        """返回比赛关键事件（进球/红黄牌/换人/VAR）。"""

    def get_match_team_stats(self, match_id: int | str) -> list[dict]:
        """返回比赛球队技术统计。"""

    def get_match_player_stats(self, match_id: int | str, limit: int = 30) -> list[dict]:
        """返回比赛球员技术统计（含评分）。"""

    @property
    def freshness(self) -> str:
        """数据新鲜度标识。"""


def get_crazy_sports_client() -> CrazySportsClient:
    """返回疯狂体育 MySQL 客户端实例。"""
    settings = get_settings()
    if not settings.mysql_configured:
        raise ValueError("需配置 MYSQL_HOST/USER/PASSWORD/DATABASE")
    from foretell.tools.crazy_sports.mysql_client import MySQLCrazySportsClient

    return MySQLCrazySportsClient()
