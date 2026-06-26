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
        "national": 0,
    },
    "t_portugal_nt": {
        "team_id": "t_portugal_nt",
        "name": "葡萄牙",
        "name_en": "Portugal",
        "sport": "football",
        "aliases": ["葡萄牙国家队"],
        "national": 1,
    },
    "t_portugal_sporting": {
        "team_id": "t_portugal_sporting",
        "name": "葡萄牙体育",
        "name_en": "Sporting CP",
        "sport": "football",
        "aliases": ["葡萄牙体育俱乐部"],
        "national": 0,
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
    "l_world_cup": {
        "league_id": "l_world_cup",
        "name": "世界杯",
        "name_en": "FIFA World Cup",
        "sport": "football",
        "aliases": ["国际足联世界杯"],
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
        "match_time_beijing": "2026-06-18 20:00:00",
    },
    "m_portugal_wc": {
        "match_id": "m_portugal_wc",
        "home_team_id": "t_portugal_nt",
        "away_team_id": "t_bayern",
        "home_name": "葡萄牙",
        "away_name": "拜仁",
        "date": "2026-07-01",
        "league_id": "l_world_cup",
        "league_name": "世界杯",
        "sport": "football",
        "series_game": None,
        "status": "scheduled",
        "match_time_beijing": "2026-07-01 03:00:00",
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
    "t_portugal_nt": ["m_portugal_wc"],
}

# 十四场 / 任九期号样本（26061 期，4 场用于批量初筛测试）
FOURTEEN_PERIOD = "26061"
FOURTEEN_ENTRIES: list[dict] = [
    {
        "lottery_code": "第1场",
        "play_type": PlayType.FOURTEEN_MATCHES.value,
        "period": FOURTEEN_PERIOD,
        "match_id": "m_liverpool_tottenham",
        "date": "2026-06-21",
        "league_name": "英超",
        "home_name": "利物浦",
        "away_name": "热刺",
    },
    {
        "lottery_code": "第2场",
        "play_type": PlayType.FOURTEEN_MATCHES.value,
        "period": FOURTEEN_PERIOD,
        "match_id": "m_psg_bayern",
        "date": "2026-04-29",
        "league_name": "欧冠",
        "home_name": "巴黎圣曼",
        "away_name": "拜仁",
    },
    {
        "lottery_code": "第3场",
        "play_type": PlayType.FOURTEEN_MATCHES.value,
        "period": FOURTEEN_PERIOD,
        "match_id": "m_lakers_warriors",
        "date": "2026-06-21",
        "league_name": "NBA",
        "home_name": "湖人",
        "away_name": "勇士",
    },
    {
        "lottery_code": "第4场",
        "play_type": PlayType.FOURTEEN_MATCHES.value,
        "period": FOURTEEN_PERIOD,
        "match_id": "m_spurs_thunder_g6",
        "date": "2026-06-15",
        "league_name": "NBA",
        "home_name": "马刺",
        "away_name": "雷霆",
    },
]

# 彩票开售场次（键：玩法:日期 或 玩法:期号）
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
    f"{PlayType.FOURTEEN_MATCHES.value}:{FOURTEEN_PERIOD}": FOURTEEN_ENTRIES,
}

# 积分榜
STANDINGS: dict[str, list[dict]] = {
    "l_ucl": [
        {
            "rank": 1,
            "team_id": "t_psg",
            "team_name": "巴黎圣曼",
            "played": 6,
            "won": 4,
            "drawn": 1,
            "lost": 1,
            "gf": 12,
            "ga": 5,
            "points": 13,
        },
        {
            "rank": 2,
            "team_id": "t_bayern",
            "team_name": "拜仁",
            "played": 6,
            "won": 4,
            "drawn": 0,
            "lost": 2,
            "gf": 14,
            "ga": 8,
            "points": 12,
        },
    ],
    "l_premier": [
        {
            "rank": 3,
            "team_id": "t_liverpool",
            "team_name": "利物浦",
            "played": 38,
            "won": 24,
            "drawn": 10,
            "lost": 4,
            "gf": 86,
            "ga": 41,
            "points": 82,
        },
        {
            "rank": 5,
            "team_id": "t_tottenham",
            "team_name": "热刺",
            "played": 38,
            "won": 20,
            "drawn": 6,
            "lost": 12,
            "gf": 74,
            "ga": 61,
            "points": 66,
        },
    ],
    "l_nba": [
        {
            "rank": 3,
            "team_id": "t_lakers",
            "team_name": "湖人",
            "played": 82,
            "won": 50,
            "lost": 32,
            "win_pct": 0.610,
        },
        {
            "rank": 6,
            "team_id": "t_warriors",
            "team_name": "勇士",
            "played": 82,
            "won": 46,
            "lost": 36,
            "win_pct": 0.561,
        },
    ],
}

# 球队赛季统计
TEAM_SEASON_STATS: dict[str, dict] = {
    "t_psg": {
        "team_id": "t_psg",
        "league_id": "l_ucl",
        "home_w": 3,
        "home_d": 0,
        "home_l": 0,
        "away_w": 1,
        "away_d": 1,
        "away_l": 1,
        "goals_for": 12,
        "goals_against": 5,
    },
    "t_bayern": {
        "team_id": "t_bayern",
        "league_id": "l_ucl",
        "home_w": 2,
        "home_d": 0,
        "home_l": 1,
        "away_w": 2,
        "away_d": 0,
        "away_l": 1,
        "goals_for": 14,
        "goals_against": 8,
    },
    "t_liverpool": {
        "team_id": "t_liverpool",
        "league_id": "l_premier",
        "home_w": 14,
        "home_d": 4,
        "home_l": 1,
        "away_w": 10,
        "away_d": 6,
        "away_l": 3,
        "goals_for": 86,
        "goals_against": 41,
    },
    "t_lakers": {
        "team_id": "t_lakers",
        "league_id": "l_nba",
        "home_w": 28,
        "home_l": 13,
        "away_w": 22,
        "away_l": 19,
        "ppg": 113.2,
        "opp_ppg": 110.5,
    },
}

# 近期战绩 team_id -> list of results (W/D/L or W/L for basketball)
RECENT_FORM: dict[str, list[dict]] = {
    "t_psg": [
        {"result": "W", "score": "3-1", "opponent": "马赛", "venue": "home", "date": "2026-04-22"},
        {"result": "D", "score": "1-1", "opponent": "里昂", "venue": "away", "date": "2026-04-15"},
        {
            "result": "W",
            "score": "2-0",
            "opponent": "摩纳哥",
            "venue": "home",
            "date": "2026-04-08",
        },
        {"result": "W", "score": "4-1", "opponent": "南特", "venue": "away", "date": "2026-04-01"},
        {"result": "L", "score": "0-1", "opponent": "里尔", "venue": "home", "date": "2026-03-25"},
    ],
    "t_bayern": [
        {
            "result": "W",
            "score": "2-0",
            "opponent": "多特蒙德",
            "venue": "home",
            "date": "2026-04-20",
        },
        {
            "result": "W",
            "score": "3-2",
            "opponent": "勒沃库森",
            "venue": "away",
            "date": "2026-04-13",
        },
        {
            "result": "L",
            "score": "1-2",
            "opponent": "莱比锡",
            "venue": "home",
            "date": "2026-04-06",
        },
        {
            "result": "W",
            "score": "5-0",
            "opponent": "弗赖堡",
            "venue": "away",
            "date": "2026-03-30",
        },
        {
            "result": "W",
            "score": "1-0",
            "opponent": "法兰克福",
            "venue": "home",
            "date": "2026-03-23",
        },
    ],
    "t_liverpool": [
        {
            "result": "W",
            "score": "2-1",
            "opponent": "切尔西",
            "venue": "home",
            "date": "2026-06-14",
        },
        {
            "result": "D",
            "score": "1-1",
            "opponent": "阿森纳",
            "venue": "away",
            "date": "2026-06-07",
        },
        {
            "result": "W",
            "score": "3-0",
            "opponent": "埃弗顿",
            "venue": "home",
            "date": "2026-05-31",
        },
        {
            "result": "W",
            "score": "2-0",
            "opponent": "纽卡斯尔",
            "venue": "away",
            "date": "2026-05-24",
        },
        {"result": "D", "score": "0-0", "opponent": "曼城", "venue": "home", "date": "2026-05-17"},
    ],
    "t_lakers": [
        {
            "result": "W",
            "score": "112-105",
            "opponent": "掘金",
            "venue": "home",
            "date": "2026-06-18",
        },
        {
            "result": "L",
            "score": "98-110",
            "opponent": "太阳",
            "venue": "away",
            "date": "2026-06-15",
        },
        {
            "result": "W",
            "score": "120-115",
            "opponent": "快船",
            "venue": "home",
            "date": "2026-06-12",
        },
        {
            "result": "W",
            "score": "108-102",
            "opponent": "国王",
            "venue": "away",
            "date": "2026-06-09",
        },
        {
            "result": "L",
            "score": "95-101",
            "opponent": "雷霆",
            "venue": "home",
            "date": "2026-06-06",
        },
    ],
}

# 历史交锋 key: sorted team ids joined
H2H: dict[str, list[dict]] = {
    "t_bayern|t_psg": [
        {
            "date": "2025-11-26",
            "home_team_id": "t_bayern",
            "away_team_id": "t_psg",
            "score": "1-0",
            "competition": "欧冠",
        },
        {
            "date": "2025-10-01",
            "home_team_id": "t_psg",
            "away_team_id": "t_bayern",
            "score": "1-1",
            "competition": "欧冠",
        },
        {
            "date": "2024-04-16",
            "home_team_id": "t_bayern",
            "away_team_id": "t_psg",
            "score": "2-0",
            "competition": "欧冠",
        },
    ],
    "t_liverpool|t_tottenham": [
        {
            "date": "2026-01-15",
            "home_team_id": "t_liverpool",
            "away_team_id": "t_tottenham",
            "score": "3-1",
            "competition": "英超",
        },
        {
            "date": "2025-08-20",
            "home_team_id": "t_tottenham",
            "away_team_id": "t_liverpool",
            "score": "0-2",
            "competition": "英超",
        },
    ],
}

# 盘口快照
ODDS_SNAPSHOT: dict[str, dict] = {
    "m_psg_bayern": {
        "european": {
            "home": 2.10,
            "draw": 3.40,
            "away": 3.25,
            "companies": ["威廉希尔", "Bet365", "澳门"],
        },
        "asian": {
            "line": "平手/半球",
            "line_cn": "巴黎让平手/半球",
            "home_water": 0.92,
            "away_water": 0.98,
        },
        "over_under": {"line": 2.75, "over": 0.88, "under": 1.02},
    },
    "m_liverpool_tottenham": {
        "european": {"home": 1.75, "draw": 3.80, "away": 4.50},
        "asian": {
            "line": "半球/一球",
            "line_cn": "利物浦让半球/一球",
            "home_water": 0.95,
            "away_water": 0.95,
        },
        "over_under": {"line": 2.5, "over": 0.90, "under": 1.00},
    },
    "m_lakers_warriors": {
        "moneyline": {"home": 1.85, "away": 2.05},
        "spread": {"line": -2.5, "line_cn": "湖人让2.5分", "home_water": 0.91, "away_water": 0.99},
        "total": {"line": 224.5, "over": 0.93, "under": 0.97},
    },
    "m_spurs_thunder_g6": {
        "moneyline": {"home": 1.72, "away": 2.18},
        "spread": {"line": -3.5, "line_cn": "马刺让3.5分", "home_water": 0.90, "away_water": 1.00},
        "total": {"line": 218.5, "over": 0.92, "under": 0.98},
    },
}

# 赔率走势
ODDS_TREND: dict[str, list[dict]] = {
    "m_psg_bayern": [
        {
            "time": "2026-04-28 08:00",
            "european_home": 2.20,
            "asian_line_cn": "平手",
            "over_under_line": 2.5,
        },
        {
            "time": "2026-04-29 12:00",
            "european_home": 2.10,
            "asian_line_cn": "巴黎让平手/半球",
            "over_under_line": 2.75,
        },
    ],
}

# 同赔历史
SAME_ODDS_HISTORY: dict[str, list[dict]] = {
    "m_psg_bayern": [
        {
            "date": "2024-03-05",
            "match": "皇马 VS 莱比锡",
            "result": "2-1",
            "same_odds_outcome": "主胜",
        },
        {
            "date": "2023-11-08",
            "match": "曼城 VS 年轻人",
            "result": "3-0",
            "same_odds_outcome": "主胜",
        },
    ],
}

# 凯利指数
KELLY: dict[str, dict] = {
    "m_psg_bayern": {"home": 0.92, "draw": 0.88, "away": 1.05},
}

# 必发数据
BETFAIR: dict[str, dict] = {
    "m_psg_bayern": {"home_pct": 42.5, "draw_pct": 28.0, "away_pct": 29.5, "volume": 1250000},
}

# 阵容
MATCH_LINEUP: dict[str, dict] = {
    "m_psg_bayern": {
        "home_formation": "4-3-3",
        "away_formation": "4-2-3-1",
        "home_xi": [
            "多纳鲁马",
            "阿什拉夫",
            "马尔基尼奥斯",
            "卢卡斯",
            "门德斯",
            "维蒂尼亚",
            "法比安",
            "李刚仁",
            "登贝莱",
            "姆巴佩",
            "巴尔科拉",
        ],
        "away_xi": [
            "诺伊尔",
            "基米希",
            "于帕",
            "金玟哉",
            "戴维斯",
            "格雷茨卡",
            "莱默尔",
            "穆西亚拉",
            "萨内",
            "凯恩",
            "奥利塞",
        ],
        "status": "predicted",
    },
}

# 伤停
INJURY_REPORT: dict[str, dict] = {
    "m_psg_bayern": {
        "home": [{"player": "什克里尼亚尔", "status": "伤缺", "reason": "腿筋"}],
        "away": [
            {"player": "格纳布里", "status": "伤缺", "reason": "膝盖"},
            {"player": "博伊", "status": "停赛", "reason": "累积黄牌"},
        ],
    },
}

# 情报标签
INTEL_TAGS: dict[str, list[dict]] = {
    "m_psg_bayern": [
        {"tag": "主场优势", "weight": "high", "detail": "巴黎近5个欧冠主场4胜1平"},
        {"tag": "核心复出", "weight": "medium", "detail": "姆巴佩预计首发"},
        {"tag": "体能隐忧", "weight": "medium", "detail": "拜仁上轮联赛轮换有限"},
    ],
}

# 完场赛果与复盘数据
MATCH_RESULTS: dict[str, dict] = {
    "m_spurs_thunder_g6": {
        "match_id": "m_spurs_thunder_g6",
        "status": "finished",
        "final_score": {"home": 118, "away": 112},
        "score_display": "118-112",
        "winner": "home",
        "period_scores": [
            {"period": "Q1", "home": 28, "away": 30},
            {"period": "Q2", "home": 32, "away": 26},
            {"period": "Q3", "home": 31, "away": 28},
            {"period": "Q4", "home": 27, "away": 24},
        ],
        "stats": {
            "home_fg_pct": 0.48,
            "away_fg_pct": 0.44,
            "home_rebounds": 45,
            "away_rebounds": 41,
            "home_assists": 26,
            "away_assists": 22,
        },
        "key_events": [
            {
                "time": "Q3 05:32",
                "type": "三分球",
                "player": "文班亚马",
                "detail": "三分命中反超比分",
            },
            {
                "time": "Q4 02:15",
                "type": "关键防守",
                "player": "文班亚马",
                "detail": "封盖亚历山大上篮稳住领先",
            },
        ],
    },
}

DEFAULT_FRESHNESS = "mock_static"
