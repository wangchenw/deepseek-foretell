"""Mock 疯狂体育固定样本数据。"""

from __future__ import annotations

from foretell.tools.status_codes import PlayType

# 球队
TEAMS: dict[str, dict] = {
    "t_psg": {
        "team_id": "t_psg",
        "name": "巴黎圣曼",
        "name_en": "Paris Saint-Germain",
        "sport": "football",
        "aliases": ["巴黎", "大巴黎", "PSG"],
    },
    "t_bayern": {
        "team_id": "t_bayern",
        "name": "拜仁",
        "name_en": "Bayern Munich",
        "sport": "football",
        "aliases": ["拜仁慕尼黑"],
    },
    "t_liverpool": {
        "team_id": "t_liverpool",
        "name": "利物浦",
        "name_en": "Liverpool",
        "sport": "football",
        "aliases": [],
    },
    "t_tottenham": {
        "team_id": "t_tottenham",
        "name": "热刺",
        "name_en": "Tottenham",
        "sport": "football",
        "aliases": ["托特纳姆热刺"],
    },
    "t_lakers": {
        "team_id": "t_lakers",
        "name": "湖人",
        "name_en": "Los Angeles Lakers",
        "sport": "basketball",
        "aliases": ["洛杉矶湖人"],
    },
    "t_warriors": {
        "team_id": "t_warriors",
        "name": "勇士",
        "name_en": "Golden State Warriors",
        "sport": "basketball",
        "aliases": ["金州勇士"],
    },
    "t_spurs": {
        "team_id": "t_spurs",
        "name": "马刺",
        "name_en": "San Antonio Spurs",
        "sport": "basketball",
        "aliases": ["圣安东尼奥马刺"],
    },
    "t_thunder": {
        "team_id": "t_thunder",
        "name": "雷霆",
        "name_en": "Oklahoma City Thunder",
        "sport": "basketball",
        "aliases": ["俄克拉荷马雷霆"],
    },
}

# 联赛
LEAGUES: dict[str, dict] = {
    "l_ucl": {
        "league_id": "l_ucl",
        "name": "欧冠",
        "name_en": "UEFA Champions League",
        "sport": "football",
        "aliases": ["欧洲冠军联赛", "欧冠联赛"],
    },
    "l_nba": {
        "league_id": "l_nba",
        "name": "NBA",
        "name_en": "NBA",
        "sport": "basketball",
        "aliases": ["美国职业篮球联赛"],
    },
    "l_premier": {
        "league_id": "l_premier",
        "name": "英超",
        "name_en": "Premier League",
        "sport": "football",
        "aliases": ["英格兰超级联赛"],
    },
}

# 比赛
MATCHES: dict[str, dict] = {
    "m_psg_bayern": {
        "match_id": "m_psg_bayern",
        "home_team_id": "t_psg",
        "away_team_id": "t_bayern",
        "home_name": "巴黎圣曼",
        "away_name": "拜仁",
        "date": "2026-04-29",
        "league_id": "l_ucl",
        "league_name": "欧冠",
        "sport": "football",
        "series_game": None,
        "status": "scheduled",
    },
    "m_liverpool_tottenham": {
        "match_id": "m_liverpool_tottenham",
        "home_team_id": "t_liverpool",
        "away_team_id": "t_tottenham",
        "home_name": "利物浦",
        "away_name": "热刺",
        "date": "2026-06-21",
        "league_id": "l_premier",
        "league_name": "英超",
        "sport": "football",
        "series_game": None,
        "status": "scheduled",
    },
    "m_lakers_warriors": {
        "match_id": "m_lakers_warriors",
        "home_team_id": "t_lakers",
        "away_team_id": "t_warriors",
        "home_name": "湖人",
        "away_name": "勇士",
        "date": "2026-06-21",
        "league_id": "l_nba",
        "league_name": "NBA",
        "sport": "basketball",
        "series_game": None,
        "status": "scheduled",
    },
    "m_spurs_thunder_g6": {
        "match_id": "m_spurs_thunder_g6",
        "home_team_id": "t_spurs",
        "away_team_id": "t_thunder",
        "home_name": "马刺",
        "away_name": "雷霆",
        "date": "2026-06-15",
        "league_id": "l_nba",
        "league_name": "NBA",
        "sport": "basketball",
        "series_game": 6,
        "status": "finished",
    },
    "m_spurs_thunder_g7": {
        "match_id": "m_spurs_thunder_g7",
        "home_team_id": "t_spurs",
        "away_team_id": "t_thunder",
        "home_name": "马刺",
        "away_name": "雷霆",
        "date": "2026-06-18",
        "league_id": "l_nba",
        "league_name": "NBA",
        "sport": "basketball",
        "series_game": 7,
        "status": "scheduled",
    },
}

# 竞彩场次映射
LOTTERY_MATCHES: dict[str, dict] = {
    f"{PlayType.JINGCAI_FOOTBALL.value}:周二004": {
        "lottery_code": "周二004",
        "play_type": PlayType.JINGCAI_FOOTBALL.value,
        "match_id": "m_psg_bayern",
        "date": "2026-04-29",
        "league_name": "欧冠",
        "home_name": "巴黎圣曼",
        "away_name": "拜仁",
    },
    f"{PlayType.JINGCAI_FOOTBALL.value}:周二001": {
        "lottery_code": "周二001",
        "play_type": PlayType.JINGCAI_FOOTBALL.value,
        "match_id": "m_liverpool_tottenham",
        "date": "2026-06-21",
        "league_name": "英超",
        "home_name": "利物浦",
        "away_name": "热刺",
    },
    f"{PlayType.JINGCAI_BASKETBALL.value}:周一305": {
        "lottery_code": "周一305",
        "play_type": PlayType.JINGCAI_BASKETBALL.value,
        "match_id": "m_lakers_warriors",
        "date": "2026-06-21",
        "league_name": "NBA",
        "home_name": "湖人",
        "away_name": "勇士",
    },
}

# 按日赛程索引
SCHEDULE_BY_DATE: dict[str, list[str]] = {
    "2026-04-29": ["m_psg_bayern"],
    "2026-06-15": ["m_spurs_thunder_g6"],
    "2026-06-18": ["m_spurs_thunder_g7"],
    "2026-06-21": ["m_liverpool_tottenham", "m_lakers_warriors"],
}

# 球队赛程
TEAM_SCHEDULE: dict[str, list[str]] = {
    "t_liverpool": ["m_liverpool_tottenham"],
    "t_psg": ["m_psg_bayern"],
    "t_spurs": ["m_spurs_thunder_g6", "m_spurs_thunder_g7"],
}

# 彩票开售场次
LOTTERY_SCHEDULE: dict[str, list[dict]] = {
  f"{PlayType.JINGCAI_FOOTBALL.value}:2026-06-21": [
      LOTTERY_MATCHES[f"{PlayType.JINGCAI_FOOTBALL.value}:周二001"],
  ],
  f"{PlayType.JINGCAI_FOOTBALL.value}:2026-04-29": [
      LOTTERY_MATCHES[f"{PlayType.JINGCAI_FOOTBALL.value}:周二004"],
  ],
  f"{PlayType.JINGCAI_BASKETBALL.value}:2026-06-21": [
      LOTTERY_MATCHES[f"{PlayType.JINGCAI_BASKETBALL.value}:周一305"],
  ],
}

DEFAULT_FRESHNESS = "mock_static"
