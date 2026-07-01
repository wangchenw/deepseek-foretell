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
        national: bool | None = None,
        exclude_youth: bool = True,
        sport: str = "football",
    ) -> list[dict]:
        """按主客队模糊查询比赛，返回候选列表。"""

    def resolve_lottery_match(
        self,
        play_type: PlayType,
        code: str,
        date: str | None = None,
    ) -> dict | None:
        """按玩法与场次编号定位竞彩比赛。"""

    def resolve_team(
        self,
        name: str,
        national: bool | None = None,
        exclude_youth: bool = True,
    ) -> list[dict]:
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
        sport: str = "football",
    ) -> list[dict]:
        """返回球队近期/未来赛程（支持 football/basketball 路由）。"""

    def get_lottery_schedule(
        self,
        play_type: PlayType,
        date: str | None = None,
        period: str | None = None,
    ) -> list[dict]:
        """返回彩票可售场次列表。"""

    def get_standings(
        self,
        league_id: int | str,
        season_id: int | str | None = None,
    ) -> dict:
        """返回联赛/杯赛积分榜（含 competition_type + promotion_id + group）。"""

    def _compute_remaining_rounds(
        self,
        competition_id: int,
        season_id: int | None,
        sport: str = "football",
    ) -> dict:
        """返回 {total_rounds, played, remaining_rounds, source}。"""

    def get_team_season_stats(self, team_id: int | str, sport: str = "football") -> dict | None:
        """返回球队赛季统计。"""

    def get_recent_form(
        self,
        team_id: int | str,
        venue: str | None = None,
        n: int = 5,
        sport: str = "football",
    ) -> list[dict]:
        """返回球队近期战绩。"""

    def get_h2h(self, team_a: int | str, team_b: int | str, n: int = 5, sport: str = "football") -> list[dict]:
        """返回两队历史交锋。"""

    def get_odds_snapshot(self, match_id: int | str, sport: str = "football") -> dict | None:
        """返回盘口快照(足球:欧赔+亚盘;篮球:胜胜负+让分+大小分)。"""

    def get_odds_trend(self, match_id: int | str, sport: str = "football") -> list[dict]:
        """返回赔率走势（支持 football/basketball 路由）。"""

    def get_same_odds_history(self, match_id: int | str) -> list[dict]:
        """返回同赔历史。"""

    def get_kelly(self, match_id: int | str) -> dict | None:
        """返回凯利指数。"""

    def get_betfair(self, match_id: int | str) -> dict | None:
        """返回必发成交数据。"""

    def get_match_lineup(self, match_id: int | str, sport: str = "football") -> dict | None:
        """返回预计阵容。"""

    def get_injury_report(self, match_id: int | str, sport: str = "football") -> dict | None:
        """返回伤停报告。"""

    def get_intel_tags(self, match_id: int | str, sport: str = "football") -> list[dict]:
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

    def get_season_bracket(
        self,
        season_id: int | str,
        sport: str = "football",
    ) -> dict | None:
        """返回淘汰赛对阵树(brackets + rounds + match_ups 含 parent_id/children_ids 拓扑)。"""

    def get_match_tlive(self, match_id: int | str, limit: int = 100, sport: str = "football") -> list[dict]:
        """返回比赛实时文字直播事件流。"""

    def get_match_incidents(self, match_id: int | str, sport: str = "football") -> list[dict]:
        """返回比赛关键事件（进球/红黄牌/换人/VAR）。"""

    def get_match_team_stats(self, match_id: int | str, sport: str = "football") -> list[dict]:
        """返回比赛球队技术统计。"""

    def get_match_player_stats(self, match_id: int | str, limit: int = 30, sport: str = "football") -> list[dict]:
        """返回比赛球员技术统计（含评分）。"""

    def resolve_basketball_team(self, name: str) -> list[dict]:
        """模糊解析篮球球队。"""

    def resolve_basketball_league(self, name: str) -> list[dict]:
        """模糊解析篮球赛事。"""

    def get_seasons(self, competition_id: int | str, sport: str = "football") -> list[dict]:
        """返回赛事赛季列表（按最新优先）。"""

    def get_player_profile(self, player_id: int | str, sport: str = "football") -> dict | None:
        """返回球员资料。"""

    def get_player_market_value(self, player_id: int | str, sport: str = "football") -> list[dict]:
        """返回球员身价历史（篮球暂未采集）。"""

    def get_player_transfers(self, player_id: int | str, sport: str = "football") -> list[dict]:
        """返回球员转会历史。"""

    def get_player_honors(self, player_id: int | str, sport: str = "football") -> list[dict]:
        """返回球员荣誉。"""

    def get_team_honors(self, team_id: int | str, sport: str = "football") -> list[dict]:
        """返回球队荣誉。"""

    def get_coach(self, coach_id: int | str, sport: str = "football") -> dict | None:
        """返回教练资料。"""

    def get_referee(self, referee_id: int | str) -> dict | None:
        """返回裁判资料。"""

    def get_venue(self, venue_id: int | str, sport: str = "football") -> dict | None:
        """返回场馆资料。"""

    def get_match_half_stats(self, match_id: int | str, scope: str = "ft", sport: str = "football") -> dict | None:
        """返回半全场统计（scope: ft/p1/p2/o1/o2）。"""

    def get_goals_lost_rate(self, match_id: int | str, sport: str = "football") -> list[dict]:
        """返回进失球概率。"""

    def get_over_under_odds(self, match_id: int | str) -> dict | None:
        """返回大小球赔率。"""

    def get_half_odds(self, match_id: int | str) -> dict | None:
        """返回半场赔率（欧赔/亚盘/大小球）。"""

    def get_corner_odds(self, match_id: int | str) -> dict | None:
        """返回角球赔率（全场/半场）。"""

    def get_hundred_europe_odds(self, match_id: int | str) -> list[dict]:
        """返回百欧赔率。"""

    def get_official_handicap_odds(self, match_id: int | str) -> list[dict]:
        """返回官方让球盘。"""

    def get_promotions(self, sport: str = "football") -> list[dict]:
        """返回升降级信息。"""

    def get_first_second(self, limit: int = 20) -> list[dict]:
        """返回冠亚军信息。"""

    def get_fifa_ranking(self, gender: int = 1, limit: int = 30) -> list[dict]:
        """返回 FIFA 排名。"""

    def get_club_ranking(self, limit: int = 30) -> list[dict]:
        """返回俱乐部排名。"""

    def get_season_best(self, competition_id: int | str, season_id: int | str | None = None) -> dict | None:
        """返回赛季最佳球员/球队。"""

    def get_recommendations(self, match_id: int | str) -> dict | None:
        """返回心水推荐。"""

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
