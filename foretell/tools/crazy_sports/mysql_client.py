"""疯狂体育 MySQL 客户端（data_center 库）。"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Literal

from foretell.tools.crazy_sports.db import mysql_connection
from foretell.tools.lottery_code import (
    format_lottery_code,
    parse_lottery_entry_num,
    parse_lottery_issue_num,
)
from foretell.tools.status_codes import PlayType

# 仅 status_id=8(完场)才算真正踢完、有赛果可统计；
# 9推迟/10中断/11腰斩/12取消 属异常，不应进入战绩/赛果统计。
_FINISHED_STATUS_IDS = {8}

# status_id → 语义化状态字符串（来源：football_match.status_id 列注释）
# 0异常/1未开赛/2上半场/3中场/4下半场/5加时/6弃用/7点球决战/
# 8完场/9推迟/10中断/11腰斩/12取消/13待定
_STATUS_MAP: dict[int, str] = {
    0: "abnormal",
    1: "not_started",
    2: "in_play",
    3: "in_play",
    4: "in_play",
    5: "overtime",
    7: "penalty_shootout",
    8: "finished",
    9: "postponed",
    10: "interrupted",
    11: "abandoned",
    12: "cancelled",
    13: "tbd",
}

# basketball_match.status_id 列注释
# 0异常/1未开赛/2第一节/3第一节完/4第二节/5第二节完/6第三节/7第三节完/
# 8第四节/9加时赛/10完场/11中断/12取消/13延期/14腰斩/15待定
_BASKETBALL_STATUS_MAP: dict[int, str] = {
    0: "abnormal",
    1: "not_started",
    2: "in_play",
    3: "in_play",
    4: "in_play",
    5: "in_play",
    6: "in_play",
    7: "in_play",
    8: "in_play",
    9: "overtime",
    10: "finished",
    11: "interrupted",
    12: "cancelled",
    13: "postponed",
    14: "abandoned",
    15: "tbd",
}

# lottery_*_odds.sell_status 列注释：0未开售/1仅过关/2单关和过关/3停售
_SELL_STATUS_MAP: dict[int, str] = {
    0: "not_on_sale",
    1: "parlay_only",
    2: "singles_and_parlay",
    3: "suspended",
}

# bracket_match_up.type_id 列注释：1单场决胜/8三局两胜/9五局三胜/10七局四胜
_SERIES_TYPE_MAP: dict[int, str] = {
    1: "single_match",
    8: "best_of_3",
    9: "best_of_5",
    10: "best_of_7",
}

# bracket_match_up.state_id 列注释：1未开赛/2等待对手/6进行中/7主场胜/8客场胜/9取消/10轮空/11等待抽签
_SERIES_STATE_MAP: dict[int, str] = {
    1: "not_started",
    2: "awaiting_opponent",
    6: "in_play",
    7: "home_won",
    8: "away_won",
    9: "cancelled",
    10: "bye",
    11: "awaiting_draw",
}

# football_team_injury.type 列注释：0未知/1受伤/2停赛/3出战成疑
_INJURY_TYPE_MAP: dict[int, str] = {
    0: "unknown",
    1: "injured",
    2: "suspended",
    3: "doubtful",
}

# football_match_incidents.type —— 纳米足球状态码文档「技术统计」
# 1进球/2角球/3黄牌/4红牌/5越位/6任意球/7球门球/8点球/9换人/10比赛开始/
# 11中场/12结束/13半场比分/15两黄变红/16点球未进/17乌龙球/18助攻/19伤停补时/
# 21射正/22射偏/23进攻/24危险进攻/25控球率/26加时赛结束/27点球大战结束/
# 28 VAR/29点球(点球大战)/30点球未进(点球大战)/37射门被阻挡/38补水
_INCIDENT_TYPE_MAP: dict[int, str] = {
    1: "goal", 2: "corner", 3: "yellow_card", 4: "red_card", 5: "offside",
    6: "free_kick", 7: "goal_kick", 8: "penalty", 9: "substitution",
    10: "match_start", 11: "half_time", 12: "match_end", 13: "half_time_score",
    15: "second_yellow_to_red", 16: "penalty_missed", 17: "own_goal",
    18: "assist", 19: "stoppage_time", 21: "shot_on_target", 22: "shot_off_target",
    23: "attack", 24: "dangerous_attack", 25: "possession",
    26: "overtime_end", 27: "penalty_shootout_end", 28: "var",
    29: "penalty_shootout", 30: "penalty_shootout_missed",
    37: "shot_blocked", 38: "water_break",
}

# football_match_incidents.reason_type —— 纳米足球状态码文档「事件原因」
# 0未知/1犯规/2个人犯规/3侵犯对手或受伤换人/4战术犯规或战术换人/5进攻犯规/
# 6无球犯规/7持续犯规/8持续侵犯/9暴力行为/10危险动作/11手球犯规/12严重犯规/
# 13故意犯规/14阻挡进球机会/15拖延时间/16视频回看裁定/17判罚取消/18争论/
# 19对判罚表达异议/20犯规和攻击言语/21过度庆祝/22没回退到要求距离/23打架/
# 24辅助判罚/25替补席/26赛后行为/27其他原因/28未被允许进入场地/29进入比赛场地/
# 30离开比赛赛场/31非体育道德行为/32非主观意愿恶意犯规/33假摔/34干预var复审/
# 35进入裁判评审区/36吐口水/37病毒
_INCIDENT_REASON_MAP: dict[int, str] = {
    0: "unknown", 1: "foul", 2: "personal_foul",
    3: "opponent_violation_or_injury_sub", 4: "tactical_foul_or_tactical_sub",
    5: "offensive_foul", 6: "off_ball_foul", 7: "persistent_foul",
    8: "persistent_violation", 9: "violent_conduct", 10: "dangerous_play",
    11: "handball", 12: "serious_foul", 13: "intentional_foul",
    14: "denying_goal_scoring_opportunity", 15: "time_wasting",
    16: "var_review", 17: "decision_overturned", 18: "dissent",
    19: "protest_to_decision", 20: "foul_and_abusive_language",
    21: "excessive_celebration", 22: "failure_to_retreat_distance",
    23: "fighting", 24: "assistant_decision", 25: "substitute_bench",
    26: "post_match_behavior", 27: "other", 28: "not_allowed_to_enter",
    29: "entering_field", 30: "leaving_field", 31: "unsporting_behavior",
    32: "unintentional_malicious_foul", 33: "diving", 34: "interfering_var",
    35: "entering_review_area", 36: "spitting", 37: "virus",
}

# football_player_transfer.transfer_type —— 纳米 openapi 字段说明
# 1租借/2租借结束/3转会/4退役/5选秀/6已解约/7已签约/8未知
_TRANSFER_TYPE_MAP: dict[int, str] = {
    1: "loan", 2: "loan_end", 3: "transfer", 4: "retirement",
    5: "draft", 6: "released", 7: "signed", 8: "unknown",
}

# football_player.preferred_foot —— 纳米 openapi 字段说明
# 0未知/1左脚/2右脚/3左右脚
_PREFERRED_FOOT_MAP: dict[int, str] = {
    0: "unknown", 1: "left", 2: "right", 3: "both",
}

# basketball_player.position —— DB 列注释（C/SF/PF/SG/PG/F/G）
_BASKETBALL_POSITION_MAP: dict[str, str] = {
    "C": "center", "SF": "small_forward", "PF": "power_forward",
    "SG": "shooting_guard", "PG": "point_guard",
    "F": "forward", "G": "guard",
}

# basketball_player.preferred_hand —— DB 列注释：1左手/2右手/3左右手
_PREFERRED_HAND_MAP: dict[int, str] = {
    1: "left", 2: "right", 3: "both",
}


def _status_from_id(status_id: Any, sport: str = "football") -> str:
    if status_id is None:
        return "unknown"
    map_ = _BASKETBALL_STATUS_MAP if sport == "basketball" else _STATUS_MAP
    try:
        return map_.get(int(status_id), "unknown")
    except (TypeError, ValueError):
        return "unknown"


def _sell_status_from_id(sell_status: Any) -> str:
    if sell_status is None:
        return "unknown"
    try:
        return _SELL_STATUS_MAP.get(int(sell_status), "unknown")
    except (TypeError, ValueError):
        return "unknown"


def _series_type_from_id(type_id: Any) -> str:
    if type_id is None:
        return "unknown"
    try:
        return _SERIES_TYPE_MAP.get(int(type_id), "unknown")
    except (TypeError, ValueError):
        return "unknown"


def _series_state_from_id(state_id: Any) -> str:
    if state_id is None:
        return "unknown"
    try:
        return _SERIES_STATE_MAP.get(int(state_id), "unknown")
    except (TypeError, ValueError):
        return "unknown"


def _injury_type_from_id(type_id: Any) -> str:
    if type_id is None:
        return "unknown"
    try:
        return _INJURY_TYPE_MAP.get(int(type_id), "unknown")
    except (TypeError, ValueError):
        return "unknown"
_SCHEDULE_BY_DATE_LIMIT = 100
_LOTTERY_SCHEDULE_LIMIT = 50
_LOTTERY_PLAY_TABLES = {
    PlayType.JINGCAI_FOOTBALL: ("lottery_jczq_odds", None),
    PlayType.JINGCAI_BASKETBALL: ("lottery_jclq_odds", None),
    PlayType.BEIDAN_WIN_LOSS: ("lottery_bd_odds", None),
    PlayType.FOURTEEN_MATCHES: ("lottery_zc_match", "sfc"),
    PlayType.HALF_FULL: ("lottery_zc_match", "bqc"),
    PlayType.GOAL_LOTTERY: ("lottery_zc_match", "jqc"),
    PlayType.BEIDAN_HANDICAP: ("lottery_bdsf_odds", None),
}
_LOTTERY_ODDS_COLUMNS = {
    PlayType.JINGCAI_FOOTBALL: ("spf", "rq", "bf", "jq", "bqc"),
    PlayType.JINGCAI_BASKETBALL: ("sf", "rf", "dxf", "sfc"),
    PlayType.BEIDAN_WIN_LOSS: ("spf", "jq", "bqc", "sxp", "bf"),
    PlayType.BEIDAN_HANDICAP: ("sf",),
}

# 顶级赛事 competition_id 白名单（ID 硬编码，依赖 data_center competition_id 稳定性；
# DB 重导或 ID 变更需同步。来源：2026-06-28 probe football_competition/basketball_competition）。
_TOP_TIER_FOOTBALL_COMPETITION_IDS: frozenset[int] = frozenset({
    1,    # 世界杯
    45,   # 欧洲杯
    46,   # 欧冠
    47,   # 欧联
    82,   # 英超
    108,  # 意甲
    120,  # 西甲
    129,  # 德甲
    142,  # 法甲
    457,  # 美职联 (MLS)
    491,  # 亚冠
    542,  # 中超
    567,  # 日职联 (J1)
    581,  # 韩K联
})
_TOP_TIER_BASKETBALL_COMPETITION_IDS: frozenset[int] = frozenset({
    1,    # NBA
    3,    # CBA
    202,  # 欧洲杯 (国际篮联)
    475,  # 欧洲杯
})
_TOP_TIER_BUDGET = 50  # 默认模式下为顶级赛事预留的最大槽位


def _top_tier_ids(sport: str) -> frozenset[int] | None:
    if sport == "football":
        return _TOP_TIER_FOOTBALL_COMPETITION_IDS
    if sport == "basketball":
        return _TOP_TIER_BASKETBALL_COMPETITION_IDS
    return None


def _sql_match_on_date(column: str) -> str:
    return (
        f"{column} >= UNIX_TIMESTAMP(%s) "
        f"AND {column} < UNIX_TIMESTAMP(DATE_ADD(%s, INTERVAL 1 DAY))"
    )


def _sql_match_upcoming(column: str) -> str:
    return f"{column} > UNIX_TIMESTAMP(NOW())"


def _parse_int_id(raw_id: int | str | None) -> int | None:
    if raw_id is None:
        return None
    try:
        return int(raw_id)
    except (TypeError, ValueError):
        return None


def _like_pattern(name: str) -> str:
    return f"%{name.strip()}%"


def _row_match(row: dict) -> dict:
    match_time = row.get("match_time")
    date_str = ""
    if isinstance(match_time, datetime):
        date_str = match_time.strftime("%Y-%m-%d")
    elif row.get("match_time_str"):
        date_str = str(row["match_time_str"])[:10]

    env_keys = (
        "environment_temperature",
        "environment_humidity",
        "environment_wind",
        "environment_pressure",
    )
    env = None
    if any(row.get(k) not in (None, "") for k in env_keys):
        env = {k.replace("environment_", ""): row.get(k) for k in env_keys}

    neutral_raw = row.get("neutral")
    neutral = None
    if neutral_raw is not None:
        try:
            neutral = bool(int(neutral_raw))
        except (TypeError, ValueError):
            neutral = None

    return {
        "match_id": row["id"],
        "home_team_id": row["home_team_id"],
        "away_team_id": row["away_team_id"],
        "home_name": row.get("home_name") or row.get("short_home") or "",
        "away_name": row.get("away_name") or row.get("short_away") or "",
        "date": date_str,
        "league_id": row.get("competition_id"),
        "league_name": row.get("league_name") or row.get("short_comp") or "",
        "sport": "football",
        "series_game": None,
        "status": _status_from_id(row.get("status_id")),
        "match_time_beijing": row.get("match_time_str") or date_str,
        "neutral": neutral,
        "round_group": row.get("round_group_num"),
        "round_num": row.get("round_num"),
        "home_position": row.get("home_position") or None,
        "away_position": row.get("away_position") or None,
        "environment": env,
    }


def _row_basketball_match(row: dict) -> dict:
    match_time = row.get("match_time")
    date_str = ""
    if isinstance(match_time, datetime):
        date_str = match_time.strftime("%Y-%m-%d")
    elif row.get("match_time_str"):
        date_str = str(row["match_time_str"])[:10]

    result = {
        "match_id": row["id"],
        "home_team_id": row["home_team_id"],
        "away_team_id": row["away_team_id"],
        "home_name": row.get("home_name") or row.get("short_home") or "",
        "away_name": row.get("away_name") or row.get("short_away") or "",
        "date": date_str,
        "league_id": row.get("competition_id"),
        "league_name": row.get("league_name") or row.get("short_comp") or "",
        "sport": "basketball",
        "series_game": None,
        "status": _status_from_id(row.get("status_id"), sport="basketball"),
        "match_time_beijing": row.get("match_time_str") or date_str,
    }
    home_scores = _parse_scores(row.get("home_scores"))
    away_scores = _parse_scores(row.get("away_scores"))
    if home_scores or away_scores:
        result["score_breakdown"] = _decode_basketball_scores(home_scores, away_scores)
    return result


def _row_team(row: dict) -> dict:
    return {
        "team_id": row["id"],
        "name": row.get("short_name_zh") or row.get("name_zh") or "",
        "name_en": row.get("name_en") or "",
        "sport": "football",
        "national": int(row.get("national") or 0),
        "aliases": [a for a in [row.get("name_zh"), row.get("name_en")] if a],
    }


def _row_league(row: dict) -> dict:
    return {
        "league_id": row["id"],
        "name": row.get("short_name_zh") or row.get("name_zh") or "",
        "name_en": row.get("name_en") or "",
        "sport": "football",
        "aliases": [a for a in [row.get("name_zh"), row.get("name_en")] if a],
    }


def _zc_issue_num(row: dict) -> int:
    issue = str(row.get("issue") or "")
    match_id = str(row.get("match_id") or "")
    if issue and match_id.startswith(issue):
        suffix = match_id[len(issue) :]
        if suffix.isdigit():
            return int(suffix)
    return int(row.get("id") or 0)


def _format_zc_code(row: dict) -> str:
    return f"第{_zc_issue_num(row)}场"


def _row_lottery_entry(row: dict, play_type: PlayType) -> dict:
    if play_type in {
        PlayType.FOURTEEN_MATCHES,
        PlayType.HALF_FULL,
        PlayType.GOAL_LOTTERY,
    }:
        entry = {
            "lottery_id": row["id"],
            "play_type": play_type.value,
            "issue": str(row["issue"]),
            "issue_num": _zc_issue_num(row),
            "lottery_code": _format_zc_code(row),
            "home_name": row.get("home") or "",
            "away_name": row.get("away") or "",
            "league_name": row.get("comp") or "",
            "date": str(row["match_time_str"])[:10] if row.get("match_time_str") else "",
            "match_id": row.get("match_id"),
        }
        if row.get("result") not in (None, ""):
            entry["result"] = row.get("result")
        return entry

    entry = {
        "lottery_id": row["id"],
        "play_type": play_type.value,
        "issue": str(row["issue"]),
        "issue_num": row["issue_num"],
        "lottery_code": format_lottery_code(row["issue_num"])
        if play_type in {PlayType.JINGCAI_FOOTBALL, PlayType.JINGCAI_BASKETBALL}
        else str(row["issue_num"]),
        "home_name": row.get("short_home") or row.get("home") or "",
        "away_name": row.get("short_away") or row.get("away") or "",
        "league_name": row.get("short_comp") or row.get("comp") or "",
        "date": str(row["match_time_str"])[:10] if row.get("match_time_str") else "",
        "match_id": None,
    }
    odds: dict[str, Any] = {}
    for key in ("spf", "rq", "bf", "jq", "bqc", "sf", "rf", "dxf", "sfc", "sxp"):
        value = row.get(key)
        if value not in (None, ""):
            odds[key] = _parse_lottery_play(key, value)
    if odds:
        entry["odds"] = odds
    sell_raw = row.get("sell_status")
    if sell_raw is not None:
        entry["sell_status_raw"] = str(sell_raw)
        play_keys = _LOTTERY_ODDS_COLUMNS.get(play_type)
        if play_keys:
            is_beidan = play_type in {PlayType.BEIDAN_WIN_LOSS, PlayType.BEIDAN_HANDICAP}
            entry["sell_status"] = _parse_sell_status(str(sell_raw), play_keys, is_beidan)
    return entry


class MySQLCrazySportsClient:
    """从 data_center MySQL 读取结构化体育数据。"""

    @property
    def freshness(self) -> str:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    def resolve_team(self, name: str) -> list[dict]:
        sql = """
            SELECT id, name_zh, name_en, short_name_zh, national
            FROM football_team
            WHERE name_zh LIKE %s OR short_name_zh LIKE %s OR name_en LIKE %s
            LIMIT 10
        """
        pattern = _like_pattern(name)
        with mysql_connection() as cur:
            cur.execute(sql, (pattern, pattern, pattern))
            rows = cur.fetchall()
        return [_row_team(row) for row in rows]

    def resolve_league(self, name: str) -> list[dict]:
        sql = """
            SELECT id, name_zh, name_en, short_name_zh
            FROM football_competition
            WHERE name_zh LIKE %s OR short_name_zh LIKE %s OR name_en LIKE %s
            LIMIT 10
        """
        pattern = _like_pattern(name)
        with mysql_connection() as cur:
            cur.execute(sql, (pattern, pattern, pattern))
            rows = cur.fetchall()
        return [_row_league(row) for row in rows]

    def resolve_match(
        self,
        home: str,
        away: str,
        date: str | None = None,
        series_game: int | None = None,
    ) -> list[dict]:
        sql = """
            SELECT m.id, m.home_team_id, m.away_team_id, m.competition_id,
                   m.match_time, m.match_time_str, m.status_id,
                   m.neutral, m.round_group_num, m.round_num,
                   m.home_position, m.away_position,
                   m.environment_temperature, m.environment_humidity,
                   m.environment_wind, m.environment_pressure,
                   ht.short_name_zh AS home_name, at.short_name_zh AS away_name,
                   c.short_name_zh AS league_name
            FROM football_match m
            JOIN football_team ht ON m.home_team_id = ht.id
            JOIN football_team at ON m.away_team_id = at.id
            LEFT JOIN football_competition c ON m.competition_id = c.id
            WHERE (ht.name_zh LIKE %s OR ht.short_name_zh LIKE %s)
              AND (at.name_zh LIKE %s OR at.short_name_zh LIKE %s)
        """
        params: list[Any] = [
            _like_pattern(home),
            _like_pattern(home),
            _like_pattern(away),
            _like_pattern(away),
        ]
        if date:
            sql += f" AND {_sql_match_on_date('m.match_time')}"
            params.extend([date, date])
        sql += " ORDER BY m.match_time DESC LIMIT 10"

        with mysql_connection() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [_row_match(row) for row in rows]

    def resolve_lottery_match(
        self,
        play_type: PlayType,
        code: str,
        date: str | None = None,
    ) -> dict | None:
        table, zc_type = _LOTTERY_PLAY_TABLES[play_type]
        if zc_type is not None:
            entry_num = parse_lottery_entry_num(code)
            if entry_num is None:
                return None
            sql = """
                SELECT id, issue, match_id, comp, home, away,
                       match_time, match_time_str, result
                FROM lottery_zc_match
                WHERE type = %s
            """
            params: list[Any] = [zc_type]
            if date:
                sql += f" AND {_sql_match_on_date('match_time')}"
                params.extend([date, date])
            sql += " HAVING issue_num = %s ORDER BY issue DESC LIMIT 10"
            sql = sql.replace(
                "SELECT id, issue, match_id",
                "SELECT id, issue, match_id, "
                "CAST(SUBSTRING(CAST(match_id AS CHAR), CHAR_LENGTH(CAST(issue AS CHAR)) + 1) AS UNSIGNED) AS issue_num",
            )
            params.append(entry_num)
            with mysql_connection() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
            if not rows:
                return None
            candidates = [_row_lottery_entry(row, play_type) for row in rows]
            if len(candidates) == 1:
                return candidates[0]
            return {
                "play_type": play_type.value,
                "code": code,
                "candidates": candidates,
                "count": len(candidates),
            }

        issue_num = parse_lottery_issue_num(code)
        if issue_num is None:
            return None

        if play_type in {PlayType.BEIDAN_WIN_LOSS, PlayType.BEIDAN_HANDICAP}:
            select_names = "comp, home, away"
        else:
            select_names = "short_home, short_away, short_comp, home, away, comp"
        odds_columns = _LOTTERY_ODDS_COLUMNS[play_type]
        odds_select = ", ".join(odds_columns)
        sql = f"""
            SELECT id, issue, issue_num, {select_names},
                   match_time, match_time_str, sell_status, {odds_select}
            FROM {table}
            WHERE issue_num = %s
        """
        params = [issue_num]
        if date:
            sql += f" AND {_sql_match_on_date('match_time')}"
            params.extend([date, date])
        sql += " ORDER BY match_time DESC LIMIT 1"

        with mysql_connection() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        if not row:
            return None

        entry = _row_lottery_entry(row, play_type)
        entry["code"] = entry["lottery_code"]

        if play_type == PlayType.JINGCAI_FOOTBALL:
            match_candidates = self.resolve_match(
                entry["home_name"],
                entry["away_name"],
                date=entry["date"] or date,
            )
            if match_candidates:
                entry["match_candidates"] = match_candidates
        return entry

    def _count_sport_on_date(
        self,
        sport: str,
        date: str,
        only_competition_ids: frozenset[int] | None = None,
    ) -> int:
        table = "football_match" if sport == "football" else "basketball_match"
        sql = f"SELECT COUNT(*) AS cnt FROM {table} m WHERE {_sql_match_on_date('m.match_time')}"
        params: list[Any] = [date, date]
        if only_competition_ids:
            sql += f" AND m.competition_id IN ({','.join(['%s'] * len(only_competition_ids))})"
            params.extend(only_competition_ids)
        with mysql_connection() as cur:
            cur.execute(sql, params)
            return int(cur.fetchone()["cnt"])

    def _query_sport_on_date(
        self,
        sport: str,
        date: str,
        league_preset: str | None = None,
        only_competition_ids: frozenset[int] | None = None,
        exclude_competition_ids: frozenset[int] | None = None,
        limit: int = _SCHEDULE_BY_DATE_LIMIT + 1,
    ) -> list[dict]:
        if sport == "football":
            table, team_tbl, comp_tbl, row_fn = (
                "football_match", "football_team", "football_competition", _row_match,
            )
        else:
            table, team_tbl, comp_tbl, row_fn = (
                "basketball_match", "basketball_team", "basketball_competition", _row_basketball_match,
            )
        sql = f"""
            SELECT m.id, m.home_team_id, m.away_team_id, m.competition_id,
                   m.match_time, m.match_time_str, m.status_id,
                   ht.short_name_zh AS home_name, at.short_name_zh AS away_name,
                   c.short_name_zh AS league_name
            FROM {table} m
            JOIN {team_tbl} ht ON m.home_team_id = ht.id
            JOIN {team_tbl} at ON m.away_team_id = at.id
            LEFT JOIN {comp_tbl} c ON m.competition_id = c.id
            WHERE {_sql_match_on_date('m.match_time')}
        """
        params: list[Any] = [date, date]
        if only_competition_ids:
            sql += f" AND m.competition_id IN ({','.join(['%s'] * len(only_competition_ids))})"
            params.extend(only_competition_ids)
        elif exclude_competition_ids:
            sql += f" AND m.competition_id NOT IN ({','.join(['%s'] * len(exclude_competition_ids))})"
            params.extend(exclude_competition_ids)
        if league_preset:
            if sport == "football":
                sql += " AND (c.name_zh LIKE %s OR c.short_name_zh LIKE %s OR c.name_en LIKE %s)"
                pattern = _like_pattern(league_preset)
                params.extend([pattern, pattern, pattern])
            else:
                sql += (
                    " AND (c.name_zh LIKE %s OR c.short_name_zh LIKE %s "
                    "OR c.name_en LIKE %s OR c.short_name_en LIKE %s)"
                )
                pattern = _like_pattern(league_preset)
                params.extend([pattern, pattern, pattern, pattern])
        sql += " ORDER BY m.match_time ASC LIMIT %s"
        params.append(limit)
        with mysql_connection() as cur:
            cur.execute(sql, params)
            return [row_fn(r) for r in cur.fetchall()]

    def get_schedule_by_date(
        self,
        date: str,
        sport: str | None = None,
        league_preset: str | None = None,
        tier: Literal["top", "all"] | None = None,
    ) -> dict:
        sports: list[str] = []
        if sport in (None, "football"):
            sports.append("football")
        if sport in (None, "basketball"):
            sports.append("basketball")

        total_count = 0
        tier_count = 0
        for sp in sports:
            top_ids = _top_tier_ids(sp)
            total_count += self._count_sport_on_date(sp, date)
            if top_ids:
                tier_count += self._count_sport_on_date(sp, date, only_competition_ids=top_ids)

        rows: list[dict] = []
        prioritized = False
        if league_preset:
            for sp in sports:
                rows.extend(self._query_sport_on_date(sp, date, league_preset=league_preset))
        elif tier == "top":
            for sp in sports:
                top_ids = _top_tier_ids(sp)
                if top_ids:
                    rows.extend(
                        self._query_sport_on_date(sp, date, only_competition_ids=top_ids)
                    )
        elif total_count > _SCHEDULE_BY_DATE_LIMIT:
            # 默认模式 + 大赛日：顶级赛事优先占位，余量按时间填低级别
            prioritized = True
            top_rows: list[dict] = []
            for sp in sports:
                top_ids = _top_tier_ids(sp)
                if top_ids:
                    top_rows.extend(
                        self._query_sport_on_date(sp, date, only_competition_ids=top_ids)
                    )
            top_rows.sort(key=lambda r: r.get("match_time_beijing") or "")
            top_rows = top_rows[:_TOP_TIER_BUDGET]
            rest_budget = _SCHEDULE_BY_DATE_LIMIT - len(top_rows) + 1
            rest_rows: list[dict] = []
            for sp in sports:
                top_ids = _top_tier_ids(sp)
                rest_rows.extend(
                    self._query_sport_on_date(
                        sp, date,
                        exclude_competition_ids=top_ids,
                        limit=rest_budget,
                    )
                    if top_ids
                    else self._query_sport_on_date(sp, date, limit=rest_budget)
                )
            rest_rows.sort(key=lambda r: r.get("match_time_beijing") or "")
            rows = top_rows + rest_rows
        else:
            for sp in sports:
                rows.extend(self._query_sport_on_date(sp, date))

        if not prioritized:
            rows.sort(key=lambda r: r.get("match_time_beijing") or "")
        truncated = len(rows) > _SCHEDULE_BY_DATE_LIMIT
        matches = rows[:_SCHEDULE_BY_DATE_LIMIT]

        warning: str | None = None
        if truncated and not league_preset and tier != "top":
            warning = (
                f"仅展示前{_SCHEDULE_BY_DATE_LIMIT}场，今日共{total_count}场，"
                f"其中{tier_count}场顶级赛事已优先包含；"
                f"如需完整列表请传 league_preset 或 tier=top"
            )

        return {
            "matches": matches,
            "count": len(matches),
            "limit": _SCHEDULE_BY_DATE_LIMIT,
            "truncated": truncated,
            "total_count": total_count,
            "tier_count": tier_count,
            "warning": warning,
        }

    def get_team_schedule(
        self,
        team_id: int | str,
        limit: int = 5,
        league_id: int | str | None = None,
        direction: str = "recent",
    ) -> list[dict]:
        raw_id = _parse_int_id(team_id)
        if raw_id is None:
            return []
        sql = """
            SELECT m.id, m.home_team_id, m.away_team_id, m.competition_id,
                   m.match_time, m.match_time_str, m.status_id,
                   ht.short_name_zh AS home_name, at.short_name_zh AS away_name,
                   c.short_name_zh AS league_name
            FROM football_match m
            JOIN football_team ht ON m.home_team_id = ht.id
            JOIN football_team at ON m.away_team_id = at.id
            LEFT JOIN football_competition c ON m.competition_id = c.id
            WHERE (m.home_team_id = %s OR m.away_team_id = %s)
        """
        params: list[Any] = [raw_id, raw_id]
        if league_id is not None:
            comp_id = _parse_int_id(league_id)
            if comp_id is None:
                return []
            sql += " AND m.competition_id = %s"
            params.append(comp_id)

        if direction == "upcoming":
            sql += f" AND {_sql_match_upcoming('m.match_time')}"
            sql += " AND m.status_id NOT IN %s"
            params.append(tuple(_FINISHED_STATUS_IDS))
            sql += " ORDER BY m.match_time ASC"
        elif direction == "recent":
            sql += " AND m.status_id IN %s"
            params.append(tuple(_FINISHED_STATUS_IDS))
            sql += " ORDER BY m.match_time DESC"
        else:
            sql += " ORDER BY m.match_time DESC"

        sql += " LIMIT %s"
        params.append(limit)

        with mysql_connection() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [_row_match(r) for r in rows]

    def get_lottery_schedule(
        self,
        play_type: PlayType,
        date: str | None = None,
        period: str | None = None,
    ) -> list[dict]:
        table, zc_type = _LOTTERY_PLAY_TABLES[play_type]
        if zc_type is not None:
            sql = """
                SELECT id, issue, match_id, comp, home, away,
                       match_time, match_time_str, result
                FROM lottery_zc_match
                WHERE type = %s
            """
            params: list[Any] = [zc_type]
            if period:
                sql += " AND issue = %s"
                params.append(period)
            elif date:
                sql += f" AND {_sql_match_on_date('match_time')}"
                params.extend([date, date])
            else:
                sql += " AND issue = (SELECT MAX(issue) FROM lottery_zc_match WHERE type = %s)"
                params.append(zc_type)
            sql += " ORDER BY match_id ASC LIMIT %s"
            params.append(_LOTTERY_SCHEDULE_LIMIT)
            with mysql_connection() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
            return [_row_lottery_entry(r, play_type) for r in rows]

        if play_type in {PlayType.BEIDAN_WIN_LOSS, PlayType.BEIDAN_HANDICAP}:
            select_names = "comp, home, away"
        else:
            select_names = "short_home, short_away, short_comp, home, away, comp"
        odds_columns = _LOTTERY_ODDS_COLUMNS[play_type]
        odds_select = ", ".join(odds_columns)
        sql = f"""
            SELECT id, issue, issue_num, {select_names},
                   match_time, match_time_str, sell_status, {odds_select}
            FROM {table}
            WHERE 1=1
        """
        params: list[Any] = []
        if period:
            sql += " AND issue = %s"
            params.append(period)
        elif date:
            sql += f" AND {_sql_match_on_date('match_time')}"
            params.extend([date, date])
        else:
            sql += f" AND {_sql_match_upcoming('match_time')}"
        sql += " ORDER BY issue_num ASC LIMIT %s"
        params.append(_LOTTERY_SCHEDULE_LIMIT)

        with mysql_connection() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        return [_row_lottery_entry(r, play_type) for r in rows]

    def get_standings(self, league_id: int | str) -> list[dict]:
        comp_id = _parse_int_id(league_id)
        if comp_id is None:
            return []
        sql = """
            SELECT pt.team_id, t.short_name_zh AS team_name,
                   pt.position, pt.points, pt.deduct_points, pt.total,
                   pt.won, pt.draw, pt.loss, pt.goals, pt.goals_against, pt.goal_diff,
                   pt.home_points, pt.home_total, pt.home_won, pt.home_draw, pt.home_loss,
                   pt.home_goals, pt.home_goals_against, pt.home_goal_diff,
                   pt.away_points, pt.away_total, pt.away_won, pt.away_draw, pt.away_loss,
                   pt.away_goals, pt.away_goals_against, pt.away_goal_diff
            FROM football_points_table p
            JOIN football_points_table_team pt ON pt.table_id = p.id
            JOIN football_team t ON pt.team_id = t.id
            WHERE p.competition_id = %s
              AND p.season_id = (
                  SELECT MAX(season_id) FROM football_points_table
                  WHERE competition_id = %s
              )
            ORDER BY pt.position ASC
            LIMIT 30
        """
        with mysql_connection() as cur:
            cur.execute(sql, (comp_id, comp_id))
            rows = cur.fetchall()
        return [_format_standings_row(r) for r in rows]

    def get_team_season_stats(self, team_id: int | str) -> dict | None:
        raw_id = _parse_int_id(team_id)
        if raw_id is None:
            return None
        sql = """
            SELECT s.season_id, s.team_id, s.matches, s.goals, s.penalty, s.assists,
                   s.red_cards, s.yellow_cards, s.shots, s.shots_on_target,
                   s.dribble, s.dribble_succ, s.clearances, s.blocked_shots,
                   s.tackles, s.passes, s.passes_accuracy, s.key_passes,
                   s.crosses, s.crosses_accuracy, s.long_balls, s.long_balls_accuracy,
                   s.duels, s.duels_won, s.aerial_won, s.aerial_lost,
                   s.ground_won, s.ground_lost, s.fouls, s.was_fouled,
                   s.goals_against, s.interceptions, s.offsides,
                   s.yellow2red_cards, s.corner_kicks, s.ball_possession,
                   s.freekicks, s.freekick_goals, s.hit_woodwork,
                   t.short_name_zh AS team_name,
                   se.competition_id, c.short_name_zh AS competition_name
            FROM football_competition_teams_stats s
            LEFT JOIN football_team t ON s.team_id = t.id
            LEFT JOIN football_season se ON s.season_id = se.id
            LEFT JOIN football_competition c ON se.competition_id = c.id
            WHERE s.team_id = %s
            ORDER BY s.season_id DESC
            LIMIT 1
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            row = cur.fetchone()
        if not row:
            return None
        return _format_team_season_stats(row)

    def get_recent_form(
        self,
        team_id: int | str,
        venue: str | None = None,
        n: int = 5,
    ) -> list[dict]:
        raw_id = _parse_int_id(team_id)
        if raw_id is None:
            return []
        sql = """
            SELECT m.id, m.home_team_id, m.away_team_id, m.home_scores, m.away_scores,
                   m.match_time_str, m.status_id
            FROM football_match m
            WHERE (m.home_team_id = %s OR m.away_team_id = %s)
              AND m.status_id IN %s
        """
        params: list[Any] = [raw_id, raw_id, tuple(_FINISHED_STATUS_IDS)]
        if venue == "home":
            sql += " AND m.home_team_id = %s"
            params.append(raw_id)
        elif venue == "away":
            sql += " AND m.away_team_id = %s"
            params.append(raw_id)
        sql += " ORDER BY m.match_time DESC LIMIT %s"
        params.append(n)

        with mysql_connection() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        results = []
        for r in rows:
            home_scores = _parse_scores(r.get("home_scores"))
            away_scores = _parse_scores(r.get("away_scores"))
            if not home_scores or not away_scores:
                continue
            hg, ag = home_scores[0], away_scores[0]
            is_home = str(r["home_team_id"]) == str(raw_id)
            gf, ga = (hg, ag) if is_home else (ag, hg)
            if gf > ga:
                outcome = "W"
            elif gf < ga:
                outcome = "L"
            else:
                outcome = "D"
            results.append(
                {
                    "date": str(r.get("match_time_str", ""))[:10],
                    "outcome": outcome,
                    "goals_for": gf,
                    "goals_against": ga,
                    "venue": "home" if is_home else "away",
                }
            )
        return results

    def get_h2h(self, team_a: int | str, team_b: int | str, n: int = 5) -> list[dict]:
        id_a = _parse_int_id(team_a)
        id_b = _parse_int_id(team_b)
        if id_a is None or id_b is None:
            return []
        sql = """
            SELECT m.id, m.home_team_id, m.away_team_id, m.home_scores, m.away_scores,
                   m.match_time_str
            FROM football_match m
            WHERE ((m.home_team_id = %s AND m.away_team_id = %s)
                OR (m.home_team_id = %s AND m.away_team_id = %s))
              AND m.status_id IN %s
            ORDER BY m.match_time DESC
            LIMIT %s
        """
        with mysql_connection() as cur:
            cur.execute(
                sql,
                (id_a, id_b, id_b, id_a, tuple(_FINISHED_STATUS_IDS), n),
            )
            rows = cur.fetchall()
        results = []
        for r in rows:
            home_scores = _parse_scores(r.get("home_scores"))
            away_scores = _parse_scores(r.get("away_scores"))
            results.append({
                "match_id": r["id"],
                "date": str(r.get("match_time_str", ""))[:10],
                "home_team_id": r["home_team_id"],
                "away_team_id": r["away_team_id"],
                "score_breakdown": _decode_scores(home_scores, away_scores),
            })
        return results

    def get_odds_snapshot(self, match_id: int | str) -> dict | None:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return None

        odds_cols = (
            "{alias}.odd1, {alias}.odd2, {alias}.odd3, "
            "{alias}.first_odd1, {alias}.first_odd2, {alias}.first_odd3, "
            "{alias}.real_odd1, {alias}.real_odd2, {alias}.real_odd3, "
            "{alias}.is_zoudi, {alias}.is_entertained, "
            "{alias}.company_id, c.company_name"
        )
        with mysql_connection() as cur:
            cur.execute(
                f"""
                SELECT {odds_cols.format(alias="e")}
                FROM football_odds_europe e
                LEFT JOIN match_odds_companys c
                  ON e.company_id = c.company_id AND c.match_type = 1
                WHERE e.match_id = %s AND e.odd1 IS NOT NULL
                ORDER BY e.updated_at DESC
                LIMIT 5
                """,
                (raw_id,),
            )
            europe = cur.fetchall()
            cur.execute(
                f"""
                SELECT {odds_cols.format(alias="a")}
                FROM football_odds_asian a
                LEFT JOIN match_odds_companys c
                  ON a.company_id = c.company_id AND c.match_type = 1
                WHERE a.match_id = %s AND a.odd1 IS NOT NULL
                ORDER BY a.updated_at DESC
                LIMIT 5
                """,
                (raw_id,),
            )
            asian = cur.fetchall()

        if not europe and not asian:
            return None

        return {
            "match_id": raw_id,
            "european": [_format_european_odds(r) for r in europe],
            "asian": [_format_asian_odds(r) for r in asian],
        }

    def get_odds_trend(self, match_id: int | str) -> list[dict]:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return []
        select_cols = (
            "e.company_id, c.company_name, e.odd1, e.odd2, e.odd3, "
            "e.is_zoudi, e.is_entertained, e.updated_at"
        )
        join_clause = (
            "LEFT JOIN match_odds_companys c "
            "ON e.company_id = c.company_id AND c.match_type = 1"
        )
        # 先取比赛 match_time，路由到月分区表 football_odds_europe_change_YYYYMM
        with mysql_connection() as cur:
            cur.execute(
                "SELECT match_time FROM football_match WHERE id = %s LIMIT 1",
                (raw_id,),
            )
            match_row = cur.fetchone()
            rows: list[dict] = []
            if match_row and match_row.get("match_time"):
                from datetime import datetime as _dt
                try:
                    ts = int(match_row["match_time"])
                    dt = _dt.fromtimestamp(ts)
                    # 分区表隔月建（奇数月：01/03/05/07/09/11），每个覆盖2个月
                    odd_month = (dt.month - 1) // 2 * 2 + 1
                    ym = f"{dt.year}{odd_month:02d}"
                    partition_table = f"football_odds_europe_change_{ym}"
                    cur.execute(
                        f"SELECT {select_cols} FROM {partition_table} e {join_clause} "
                        f"WHERE e.match_id = %s ORDER BY e.updated_at ASC LIMIT 50",
                        (raw_id,),
                    )
                    rows = list(cur.fetchall())
                except Exception:
                    rows = []  # 分区表不存在则 fallback 基表
            # fallback：基表
            if not rows:
                cur.execute(
                    f"SELECT {select_cols} FROM football_odds_europe_change e {join_clause} "
                    f"WHERE e.match_id = %s ORDER BY e.updated_at ASC LIMIT 50",
                    (raw_id,),
                )
                rows = list(cur.fetchall())
        return [_format_odds_trend_row(r) for r in rows]

    def get_same_odds_history(self, match_id: int | str) -> list[dict]:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return []
        sql = """
            SELECT e.play_id, e.league_id, e.host_id, e.guest_id,
                   e.host_score, e.guest_score,
                   e.win, e.same, e.lost, e.real_win, e.real_same, e.real_lost
            FROM football_europe_match_index e
            WHERE e.league_id = (
                SELECT m.competition_id FROM football_match m WHERE m.id = %s
            )
              AND e.play_id != %s
            ORDER BY e.match_time DESC
            LIMIT 10
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id, raw_id))
            rows = cur.fetchall()
        return [_format_same_odds_row(r) for r in rows]

    def get_kelly(self, match_id: int | str) -> dict | None:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return None
        sql = """
            SELECT odd1, odd2, odd3, company_id
            FROM football_odds_europe
            WHERE match_id = %s AND odd1 IS NOT NULL AND odd2 IS NOT NULL AND odd3 IS NOT NULL
            ORDER BY updated_at DESC
            LIMIT 5
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            rows = cur.fetchall()
        if not rows:
            return None
        entries = []
        for r in rows:
            o1, o2, o3 = float(r["odd1"]), float(r["odd2"]), float(r["odd3"])
            inv_sum = 1 / o1 + 1 / o2 + 1 / o3
            p1 = (1 / o1) / inv_sum
            p2 = (1 / o2) / inv_sum
            p3 = (1 / o3) / inv_sum
            k1 = (o1 * p1 - 1) / (o1 - 1) if o1 != 1 else None
            k2 = (o2 * p2 - 1) / (o2 - 1) if o2 != 1 else None
            k3 = (o3 * p3 - 1) / (o3 - 1) if o3 != 1 else None
            entries.append({
                "company_id": r["company_id"],
                "odds": {"home_win": o1, "draw": o2, "away_win": o3},
                "implied_prob": {
                    "home_win": round(p1, 4), "draw": round(p2, 4), "away_win": round(p3, 4),
                },
                "kelly": {
                    "home_win": round(k1, 4) if k1 is not None else None,
                    "draw": round(k2, 4) if k2 is not None else None,
                    "away_win": round(k3, 4) if k3 is not None else None,
                },
            })
        return {"match_id": raw_id, "entries": entries}

    def get_betfair(self, match_id: int | str) -> dict | None:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return None
        sql = """
            SELECT `index`, per, amount, odds, payout, hot, stock, kelly, euroavg
            FROM football_bf
            WHERE id = %s
            LIMIT 1
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            row = cur.fetchone()
        if not row:
            return None
        return {
            "match_id": raw_id,
            "trade_index": row.get("index"),
            "trade_ratio": row.get("per"),
            "trade_amount": row.get("amount"),
            "live_price": row.get("odds"),
            "profit_index": row.get("payout"),
            "hot_cold_index": row.get("hot"),
            "listing_ratio": row.get("stock"),
            "kelly_variance": row.get("kelly"),
            "avg_european_odds": row.get("euroavg"),
        }

    def get_match_lineup(self, match_id: int | str) -> dict | None:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return None
        with mysql_connection() as cur:
            cur.execute(
                """
                SELECT l.id, l.confirmed, l.home_formation, l.away_formation,
                       l.home_coach_id, l.away_coach_id
                FROM football_match_lineup l
                WHERE l.match_id = %s AND l.confirmed = 1
                LIMIT 1
                """,
                (raw_id,),
            )
            lineup = cur.fetchone()
            if not lineup:
                return None
            cur.execute(
                """
                SELECT ld.team_id, ld.first, ld.captain, ld.player_id, ld.name, ld.shirt_number,
                       ld.position, ld.x, ld.y, ld.rating
                FROM football_match_lineup_detail ld
                WHERE ld.lineup_id = %s
                ORDER BY ld.team_id, ld.first DESC, ld.shirt_number
                LIMIT 30
                """,
                (lineup["id"],),
            )
            players = cur.fetchall()
        return _format_lineup(lineup, players)

    def get_injury_report(self, match_id: int | str) -> dict | None:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return None
        with mysql_connection() as cur:
            cur.execute(
                "SELECT home_team_id, away_team_id FROM football_match WHERE id = %s",
                (raw_id,),
            )
            match = cur.fetchone()
            if not match:
                return None
            home_id, away_id = match["home_team_id"], match["away_team_id"]
            cur.execute(
                """
                SELECT i.team_id, i.player_id, i.type, i.reason, i.missed_matches,
                       p.short_name_zh AS player_name, p.name_zh AS player_full_name
                FROM football_team_injury i
                LEFT JOIN football_player p ON i.player_id = p.id
                WHERE i.team_id IN (%s, %s) AND i.del_flag = 1
                LIMIT 30
                """,
                (home_id, away_id),
            )
            rows = cur.fetchall()
        home = [_format_injury_row(r) for r in rows if r["team_id"] == home_id]
        away = [_format_injury_row(r) for r in rows if r["team_id"] == away_id]
        return {"match_id": raw_id, "home": home, "away": away}

    def get_intel_tags(self, match_id: int | str) -> list[dict]:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return []
        sql = """
            SELECT good_home, good_away, bad_home, bad_away, neutral
            FROM football_intelligence
            WHERE id = %s
            LIMIT 1
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            row = cur.fetchone()
        if not row:
            return []
        tags: list[dict] = []
        for side, field, sentiment in [
            ("home", "good_home", "positive"),
            ("home", "bad_home", "negative"),
            ("away", "good_away", "positive"),
            ("away", "bad_away", "negative"),
            ("neutral", "neutral", "neutral"),
        ]:
            content = row.get(field)
            if content and str(content).strip():
                tags.append({"side": side, "sentiment": sentiment, "content": content})
        return tags

    def get_match_by_id(self, match_id: int | str) -> dict | None:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return None
        sql = """
            SELECT m.id, m.home_team_id, m.away_team_id, m.competition_id,
                   m.match_time, m.match_time_str, m.status_id,
                   m.neutral, m.round_group_num, m.round_num,
                   m.home_position, m.away_position,
                   m.environment_temperature, m.environment_humidity,
                   m.environment_wind, m.environment_pressure,
                   ht.short_name_zh AS home_name, at.short_name_zh AS away_name,
                   c.short_name_zh AS league_name
            FROM football_match m
            JOIN football_team ht ON m.home_team_id = ht.id
            JOIN football_team at ON m.away_team_id = at.id
            LEFT JOIN football_competition c ON m.competition_id = c.id
            WHERE m.id = %s
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            row = cur.fetchone()
        return _row_match(row) if row else None

    def get_match_result(self, match_id: int | str) -> dict | None:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return None
        sql = """
            SELECT id, home_scores, away_scores, match_time_str, status_id
            FROM football_match
            WHERE id = %s AND status_id IN %s
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id, tuple(_FINISHED_STATUS_IDS)))
            row = cur.fetchone()
        if not row:
            return None
        home_scores = _parse_scores(row.get("home_scores"))
        away_scores = _parse_scores(row.get("away_scores"))
        full_time = (
            f"{home_scores[0]}-{away_scores[0]}"
            if home_scores and away_scores
            else ""
        )
        return {
            "match_id": raw_id,
            "full_time": full_time,
            "score_breakdown": _decode_scores(home_scores, away_scores),
            "match_time": row.get("match_time_str"),
            "status": "finished",
        }

    def get_top_scorers(self, competition_id: int | str, limit: int = 20) -> list[dict]:
        comp_id = _parse_int_id(competition_id)
        if comp_id is None:
            return []
        sql = """
            SELECT s.position, s.team_id, s.player_id, s.goals, s.penalty,
                   s.assists, s.minutes_played,
                   t.short_name_zh AS team_name,
                   p.short_name_zh AS player_name, p.name_zh AS player_full_name
            FROM football_competition_shooters s
            JOIN football_team t ON s.team_id = t.id
            LEFT JOIN football_player p ON s.player_id = p.id
            WHERE s.season_id = (
                SELECT MAX(id) FROM football_season WHERE competition_id = %s
            )
            ORDER BY s.goals DESC, s.position ASC
            LIMIT %s
        """
        with mysql_connection() as cur:
            cur.execute(sql, (comp_id, limit))
            rows = cur.fetchall()
        return [_format_scorer_row(r) for r in rows]

    def get_team_squad(self, team_id: int | str) -> list[dict]:
        raw_id = _parse_int_id(team_id)
        if raw_id is None:
            return []
        sql = """
            SELECT s.player_id, s.position, s.shirt_number, s.is_captain,
                   p.short_name_zh AS player_name, p.name_zh AS player_full_name
            FROM football_team_squad s
            LEFT JOIN football_player p ON s.player_id = p.id
            WHERE s.team_id = %s
            ORDER BY s.position, s.shirt_number
            LIMIT 50
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            rows = cur.fetchall()
        return [_format_squad_row(r) for r in rows]

    def get_series_matchup(
        self,
        sport: str,
        team_id: int | str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        if sport == "basketball":
            table, team_tbl = "basketball_bracket_match_up", "basketball_team"
        else:
            table, team_tbl = "football_bracket_match_up", "football_team"
        sql = f"""
            SELECT bu.id, bu.type_id, bu.state_id, bu.home_team_id, bu.away_team_id,
                   bu.winner_team_id, bu.home_score, bu.away_score, bu.match_ids, bu.note,
                   ht.short_name_zh AS home_name, at.short_name_zh AS away_name
            FROM {table} bu
            JOIN {team_tbl} ht ON bu.home_team_id = ht.id
            JOIN {team_tbl} at ON bu.away_team_id = at.id
        """
        params: list[Any] = []
        if team_id is not None:
            raw_id = _parse_int_id(team_id)
            if raw_id is None:
                return []
            sql += " WHERE bu.home_team_id = %s OR bu.away_team_id = %s"
            params = [raw_id, raw_id]
        sql += " ORDER BY bu.updated_at DESC LIMIT %s"
        params.append(limit)
        with mysql_connection() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [_format_series_matchup_row(r) for r in rows]

    def get_basketball_standings(self, league_id: int | str) -> list[dict]:
        comp_id = _parse_int_id(league_id)
        if comp_id is None:
            return []
        sql = """
            SELECT pt.team_id, t.short_name_zh AS team_name,
                   pt.position, pt.won, pt.lost, pt.won_rate, pt.game_back,
                   pt.points_avg, pt.points_against_avg, pt.diff_avg, pt.streaks,
                   pt.home, pt.away, pt.last_10, pt.conference, pt.division,
                   pt.points, pt.points_for, pt.points_agt, pt.group
            FROM basketball_points_table p
            JOIN basketball_points_table_team pt ON pt.point_table_id = p.id
            JOIN basketball_team t ON pt.team_id = t.id
            WHERE p.competition_id = %s
              AND p.season_id = (
                  SELECT MAX(season_id) FROM basketball_points_table
                  WHERE competition_id = %s
              )
            ORDER BY pt.position ASC
            LIMIT 30
        """
        with mysql_connection() as cur:
            cur.execute(sql, (comp_id, comp_id))
            rows = cur.fetchall()
        return [_format_basketball_standings_row(r) for r in rows]

    def get_match_tlive(self, match_id: int | str, limit: int = 100) -> list[dict]:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return []
        sql = """
            SELECT main, type, position, time, data, sort
            FROM football_match_tlive
            WHERE match_id = %s
            ORDER BY sort ASC, time ASC
            LIMIT %s
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id, limit))
            rows = cur.fetchall()
        return [_format_tlive_row(r) for r in rows]

    def get_match_incidents(self, match_id: int | str) -> list[dict]:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return []
        sql = """
            SELECT type, position, time, second, player_id, player_name,
                   assist1_id, assist1_name, assist2_id, assist2_name,
                   in_player_id, in_player_name, out_player_id, out_player_name,
                   home_score, away_score, var_reason, var_result, reason_type, sort
            FROM football_match_incidents
            WHERE match_id = %s
            ORDER BY sort ASC, time ASC
            LIMIT 100
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            rows = cur.fetchall()
        return [_format_incident_row(r) for r in rows]

    def get_match_team_stats(self, match_id: int | str) -> list[dict]:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return []
        sql = """
            SELECT s.team_id, t.short_name_zh AS team_name,
                   s.goals, s.penalty, s.assists, s.red_cards, s.yellow_cards,
                   s.shots, s.shots_on_target, s.dribble, s.dribble_succ,
                   s.clearances, s.blocked_shots, s.interceptions, s.tackles,
                   s.passes, s.passes_accuracy, s.key_passes, s.crosses,
                   s.crosses_accuracy, s.long_balls, s.long_balls_accuracy,
                   s.duels, s.duels_won, s.fouls, s.was_fouled, s.goals_against,
                   s.offsides, s.yellow2red_cards, s.corner_kicks, s.ball_possession,
                   s.freekicks, s.freekick_goals, s.hit_woodwork, s.fastbreaks,
                   s.fastbreak_shots, s.fastbreak_goals, s.poss_losts
            FROM football_match_team_stats s
            LEFT JOIN football_team t ON s.team_id = t.id
            WHERE s.match_id = %s
            LIMIT 2
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_match_player_stats(self, match_id: int | str, limit: int = 30) -> list[dict]:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return []
        sql = """
            SELECT s.team_id, s.player_id, t.short_name_zh AS team_name,
                   p.short_name_zh AS player_name, p.name_zh AS player_full_name,
                   s.first, s.minutes_played,
                   s.goals, s.penalty, s.assists, s.red_cards, s.yellow_cards,
                   s.shots, s.shots_on_target, s.passes, s.passes_accuracy,
                   s.key_passes, s.crosses, s.dribble, s.dribble_succ,
                   s.tackles, s.interceptions, s.clearances, s.fouls,
                   s.was_fouled, s.offsides, s.rating
            FROM football_match_player_stats s
            LEFT JOIN football_team t ON s.team_id = t.id
            LEFT JOIN football_player p ON s.player_id = p.id
            WHERE s.match_id = %s
            ORDER BY s.rating DESC
            LIMIT %s
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id, limit))
            rows = cur.fetchall()
        return [_format_player_stats_row(r) for r in rows]

    def resolve_basketball_team(self, name: str) -> list[dict]:
        sql = """
            SELECT id, name_zh, name_en, short_name_zh, national, competition_id, venue_id
            FROM basketball_team
            WHERE name_zh LIKE %s OR short_name_zh LIKE %s OR name_en LIKE %s
            LIMIT 10
        """
        pattern = _like_pattern(name)
        with mysql_connection() as cur:
            cur.execute(sql, (pattern, pattern, pattern))
            rows = cur.fetchall()
        return [{"team_id": r["id"], "name": r.get("short_name_zh") or r.get("name_zh") or "",
                 "name_en": r.get("name_en") or "", "sport": "basketball",
                 "national": int(r.get("national") or 0),
                 "competition_id": r.get("competition_id"),
                 "aliases": [a for a in [r.get("name_zh"), r.get("name_en")] if a]}
                for r in rows]

    def resolve_basketball_league(self, name: str) -> list[dict]:
        sql = """
            SELECT id, name_zh, name_en, short_name_zh, type
            FROM basketball_competition
            WHERE name_zh LIKE %s OR short_name_zh LIKE %s OR name_en LIKE %s
            LIMIT 10
        """
        pattern = _like_pattern(name)
        with mysql_connection() as cur:
            cur.execute(sql, (pattern, pattern, pattern))
            rows = cur.fetchall()
        return [{"league_id": r["id"], "name": r.get("short_name_zh") or r.get("name_zh") or "",
                 "name_en": r.get("name_en") or "", "sport": "basketball",
                 "type": {0: "unknown", 1: "league", 2: "cup"}.get(int(r.get("type") or 0), "unknown"),
                 "aliases": [a for a in [r.get("name_zh"), r.get("name_en")] if a]}
                for r in rows]

    def get_seasons(self, competition_id: int | str, sport: str = "football") -> list[dict]:
        comp_id = _parse_int_id(competition_id)
        if comp_id is None:
            return []
        table = "basketball_season" if sport == "basketball" else "football_season"
        sql = f"""
            SELECT id, competition_id, year, is_current, has_player_stats, has_team_stats, has_table
            FROM {table}
            WHERE competition_id = %s
            ORDER BY is_current DESC, id DESC
            LIMIT 10
        """
        with mysql_connection() as cur:
            cur.execute(sql, (comp_id,))
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_player_profile(self, player_id: int | str, sport: str = "football") -> dict | None:
        raw_id = _parse_int_id(player_id)
        if raw_id is None:
            return None
        table = "basketball_player" if sport == "basketball" else "football_player"
        sql = f"""
            SELECT id, name_zh, name_en, short_name_zh, show_name_zh, nationality, country_id,
                   birthday, age, height, weight, position, market_value, market_value_currency,
                   contract_until, preferred_foot
            FROM {table}
            WHERE id = %s
            LIMIT 1
        """
        # basketball_player 没有 nationality/market_value/preferred_foot，用容错 SELECT
        if sport == "basketball":
            sql = """
                SELECT id, name_zh, name_en, short_name_zh, show_name_zh, country_id,
                       birthday, age, height, weight, position, salary, shirt_number,
                       school, contract_until, preferred_hand
                FROM basketball_player
                WHERE id = %s
                LIMIT 1
            """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            row = cur.fetchone()
        if row is None:
            return None
        profile = dict(row)
        # 足球：preferred_foot 映射
        if sport != "basketball" and profile.get("preferred_foot") is not None:
            profile["preferred_foot_code"] = profile.get("preferred_foot")
            profile["preferred_foot"] = _PREFERRED_FOOT_MAP.get(
                int(profile.get("preferred_foot") or 0), "unknown"
            )
        # 篮球：position + preferred_hand 映射
        if sport == "basketball":
            pos = profile.get("position")
            if pos:
                profile["position_code"] = pos
                profile["position"] = _BASKETBALL_POSITION_MAP.get(pos, pos)
            if profile.get("preferred_hand") is not None:
                profile["preferred_hand_code"] = profile.get("preferred_hand")
                profile["preferred_hand"] = _PREFERRED_HAND_MAP.get(
                    int(profile.get("preferred_hand") or 0), "unknown"
                )
        return profile

    def get_player_market_value(self, player_id: int | str) -> list[dict]:
        raw_id = _parse_int_id(player_id)
        if raw_id is None:
            return []
        sql = """
            SELECT player_id, market_time, market_value, market_value_currency, team_id, age
            FROM football_player_market
            WHERE player_id = %s
            ORDER BY market_time DESC
            LIMIT 10
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_player_transfers(self, player_id: int | str, sport: str = "football") -> list[dict]:
        raw_id = _parse_int_id(player_id)
        if raw_id is None:
            return []
        if sport == "basketball":
            sql = """
                SELECT player_id, from_team_id, to_team_id, transfer_type, transfer_time, transfer_fee, transfer_desc
                FROM basketball_player_transfer
                WHERE player_id = %s
                ORDER BY transfer_time DESC
                LIMIT 10
            """
        else:
            sql = """
                SELECT player_id, from_team_id, from_team_name, to_team_id, to_team_name,
                       transfer_type, transfer_time, transfer_fee, transfer_desc
                FROM football_player_transfer
                WHERE player_id = %s
                ORDER BY transfer_time DESC
                LIMIT 10
            """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            rows = cur.fetchall()
        return [_format_transfer_row(r) for r in rows]

    def get_player_honors(self, player_id: int | str, sport: str = "football") -> list[dict]:
        raw_id = _parse_int_id(player_id)
        if raw_id is None:
            return []
        table = "basketball_player_honor" if sport == "basketball" else "football_player_honor"
        sql = f"""
            SELECT player_id, honor_id, team_id, competition_id, season_id, season
            FROM {table}
            WHERE player_id = %s
            ORDER BY season_id DESC
            LIMIT 20
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_team_honors(self, team_id: int | str, sport: str = "football") -> list[dict]:
        raw_id = _parse_int_id(team_id)
        if raw_id is None:
            return []
        table = "basketball_team_honor" if sport == "basketball" else "football_team_honor"
        sql = f"""
            SELECT team_id, honor_id, competition_id, season_id, season
            FROM {table}
            WHERE team_id = %s
            ORDER BY season_id DESC
            LIMIT 20
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_coach(self, coach_id: int | str, sport: str = "football") -> dict | None:
        raw_id = _parse_int_id(coach_id)
        if raw_id is None:
            return None
        if sport == "basketball":
            sql = """
                SELECT id, name_zh, name_en, short_name_zh, type, birthday, age, team_id, country_id
                FROM basketball_coach
                WHERE id = %s
                LIMIT 1
            """
        else:
            sql = """
                SELECT id, name_zh, name_en, short_name_zh, type, birthday, age,
                       preferred_formation, country_id, nationality, team_id, joined, contract_until
                FROM football_coach
                WHERE id = %s
                LIMIT 1
            """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            row = cur.fetchone()
        return dict(row) if row else None

    def get_referee(self, referee_id: int | str) -> dict | None:
        raw_id = _parse_int_id(referee_id)
        if raw_id is None:
            return None
        sql = """
            SELECT id, name_zh, name_en, short_name_zh, birthday, age, country_id
            FROM football_referee
            WHERE id = %s
            LIMIT 1
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            row = cur.fetchone()
        return dict(row) if row else None

    def get_venue(self, venue_id: int | str, sport: str = "football") -> dict | None:
        raw_id = _parse_int_id(venue_id)
        if raw_id is None:
            return None
        if sport == "basketball":
            sql = """
                SELECT id, name_zh, name_en, capacity, country_id, city, city_zh, city_en
                FROM basketball_venue
                WHERE id = %s
                LIMIT 1
            """
        else:
            sql = """
                SELECT id, name_zh, name_en, capacity, country_id, city_zh, city_en, surface, undersoil_heating
                FROM football_venue
                WHERE id = %s
                LIMIT 1
            """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            row = cur.fetchone()
        return dict(row) if row else None

    def get_match_half_stats(self, match_id: int | str, scope: str = "ft") -> dict | None:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return None
        sql = """
            SELECT scope, home_goals, away_goals, home_corner_kicks, away_corner_kicks,
                   home_yellow_cards, away_yellow_cards, home_red_cards, away_red_cards,
                   home_shots, away_shots, home_shot_on_target, away_shot_on_target,
                   home_ball_possession, away_ball_possession, home_passes, away_passes,
                   home_passes_accuracy, away_passes_accuracy, home_fouls, away_fouls,
                   home_offsides, away_offsides, home_attack, away_attack,
                   home_attack_dangerous, away_attack_dangerous
            FROM football_match_half_team_stats
            WHERE match_id = %s AND scope = %s
            LIMIT 1
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id, scope))
            row = cur.fetchone()
        return dict(row) if row else None

    def get_goals_lost_rate(self, match_id: int | str) -> list[dict]:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return []
        sql = """
            SELECT match_id, host_jin, host_shi, guest_jin, guest_shi, type, name
            FROM football_match_goals_lost_rate
            WHERE match_id = %s
            LIMIT 10
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_over_under_odds(self, match_id: int | str) -> dict | None:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return None
        rows = _query_odds_table("football_odds_over_down", raw_id)
        if not rows:
            return None
        return {"match_id": raw_id, "over_under": [_format_generic_odds(r, _OVER_UNDER_LABELS) for r in rows]}

    def get_half_odds(self, match_id: int | str) -> dict | None:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return None
        europe = _query_odds_table("football_odds_half_europe", raw_id)
        asian = _query_odds_table("football_odds_half_asian", raw_id)
        over_down = _query_odds_table("football_odds_half_over_down", raw_id)
        if not europe and not asian and not over_down:
            return None
        return {
            "match_id": raw_id,
            "european": [_format_generic_odds(r, _EUROPEAN_LABELS) for r in europe],
            "asian": [_format_generic_odds(r, _ASIAN_LABELS) for r in asian],
            "over_under": [_format_generic_odds(r, _OVER_UNDER_LABELS) for r in over_down],
        }

    def get_corner_odds(self, match_id: int | str) -> dict | None:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return None
        full = _query_odds_table("football_odds_corner", raw_id)
        half = _query_odds_table("football_odds_half_corner", raw_id)
        if not full and not half:
            return None
        return {
            "match_id": raw_id,
            "full_time": [_format_generic_odds(r, _OVER_UNDER_LABELS) for r in full],
            "half_time": [_format_generic_odds(r, _OVER_UNDER_LABELS) for r in half],
        }

    def get_hundred_europe_odds(self, match_id: int | str) -> list[dict]:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return []
        sql = """
            SELECT h.company_id, c.company_name,
                   h.first_odd1, h.first_odd2, h.first_odd3,
                   h.real_odd1, h.real_odd2, h.real_odd3, h.is_entertained
            FROM football_odds_hundred_europe h
            LEFT JOIN match_odds_companys c ON h.company_id = c.company_id AND c.match_type = 1
            WHERE h.match_id = %s
            ORDER BY h.updated_at DESC
            LIMIT 5
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            rows = cur.fetchall()
        return [{
            "company_id": r.get("company_id"), "company_name": r.get("company_name"),
            "initial": _odds_triplet(r, "first_odd", _EUROPEAN_LABELS),
            "latest": _odds_triplet(r, "real_odd", _EUROPEAN_LABELS),
            "suspended": _bool_flag(r.get("is_entertained")),
        } for r in rows]

    def get_official_handicap_odds(self, match_id: int | str) -> list[dict]:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return []
        sql = """
            SELECT o.company_id, c.company_name,
                   o.first_handicap, o.first_odd1, o.first_odd2, o.first_odd3,
                   o.real_handicap, o.real_odd1, o.real_odd2, o.real_odd3, o.is_entertained
            FROM football_odds_official_handicap o
            LEFT JOIN match_odds_companys c ON o.company_id = c.company_id AND c.match_type = 1
            WHERE o.match_id = %s
            ORDER BY o.updated_at DESC
            LIMIT 5
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            rows = cur.fetchall()
        return [{
            "company_id": r.get("company_id"), "company_name": r.get("company_name"),
            "initial": {"handicap": r.get("first_handicap"),
                        **_odds_triplet(r, "first_odd", _EUROPEAN_LABELS)},
            "latest": {"handicap": r.get("real_handicap"),
                       **_odds_triplet(r, "real_odd", _EUROPEAN_LABELS)},
            "suspended": _bool_flag(r.get("is_entertained")),
        } for r in rows]

    def get_promotions(self, sport: str = "football") -> list[dict]:
        if sport == "basketball":
            sql = "SELECT id, name_zh, name_en, season_id, competition_id FROM basketball_promotions LIMIT 30"
        else:
            sql = "SELECT id, name_zh, name_en FROM football_promotions LIMIT 30"
        with mysql_connection() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_first_second(self, limit: int = 20) -> list[dict]:
        sql = """
            SELECT id, name, season, sport_id, type, issue_num, sell_status, bonus_odds,
                   team_name_first, team_id_first, team_name_second, team_id_second,
                   champion_flag, top2_qualification
            FROM football_first_second_info
            ORDER BY end_time DESC
            LIMIT %s
        """
        with mysql_connection() as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_fifa_ranking(self, gender: int = 1, limit: int = 30) -> list[dict]:
        sql = """
            SELECT ranking, team_id, region_id, points, previous_points, position_changed, pub_time
            FROM football_fifa_ranking
            WHERE gender = %s
            ORDER BY pub_time DESC, ranking ASC
            LIMIT %s
        """
        with mysql_connection() as cur:
            cur.execute(sql, (gender, limit))
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_club_ranking(self, limit: int = 30) -> list[dict]:
        sql = """
            SELECT ranking, team_id, points, previous_points, position_changed
            FROM football_club_ranking
            ORDER BY ranking ASC
            LIMIT %s
        """
        with mysql_connection() as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_season_best(self, competition_id: int | str, season_id: int | str | None = None) -> dict | None:
        comp_id = _parse_int_id(competition_id)
        if comp_id is None:
            return None
        season_filter = "AND season_id = %s" if season_id is not None else "AND season_id = (SELECT MAX(season_id) FROM football_season_best_player WHERE competition_id = %s)"
        params: list[Any] = [comp_id] if season_id is None else [comp_id, _parse_int_id(season_id)]
        with mysql_connection() as cur:
            cur.execute(
                f"""
                SELECT type_sort, type_name, team_id, player_id, matches, value, penalty
                FROM football_season_best_player
                WHERE competition_id = %s {season_filter}
                ORDER BY type_sort, sort
                LIMIT 30
                """,
                params,
            )
            players = cur.fetchall()
            cur.execute(
                f"""
                SELECT type_sort, type_name, team_id, matches, value
                FROM football_season_best_team
                WHERE competition_id = %s {season_filter}
                ORDER BY type_sort, sort
                LIMIT 10
                """,
                params,
            )
            teams = cur.fetchall()
        return {"competition_id": comp_id, "best_players": [dict(r) for r in players],
                "best_teams": [dict(r) for r in teams]}

    def get_recommendations(self, match_id: int | str) -> dict | None:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return None
        sql = """
            SELECT id, confidence_factor, predict_msg, source_match_id
            FROM data_macao_recommend
            WHERE source_match_id = %s
            ORDER BY create_time DESC
            LIMIT 3
        """
        with mysql_connection() as cur:
            cur.execute(sql, (raw_id,))
            rows = cur.fetchall()
        if not rows:
            return None
        return {"match_id": raw_id, "recommendations": [dict(r) for r in rows]}


def _parse_scores(raw: Any) -> list[int]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [int(x) for x in raw]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [int(x) for x in parsed]
        except json.JSONDecodeError:
            pass
    return []


def _decode_scores(home: list[int], away: list[int]) -> dict:
    """解读 7 元素比分数组 [常规, 半场, 红牌, 黄牌, 角球, 加时, 点球]。

    点球/加时未踢则对应字段为 None，避免模型脑补点球比分。
    角球 -1 表示无角球数据，统一映射为 None。
    """
    def pick(arr: list[int], i: int) -> int | None:
        return arr[i] if len(arr) > i else None

    h_full, a_full = pick(home, 0), pick(away, 0)
    h_half, a_half = pick(home, 1), pick(away, 1)
    h_corner, a_corner = pick(home, 4), pick(away, 4)
    h_ot, a_ot = pick(home, 5), pick(away, 5)
    h_pen, a_pen = pick(home, 6), pick(away, 6)
    has_ot = bool(h_ot or a_ot)
    has_pen = bool(h_pen or a_pen)
    return {
        "full_time": f"{h_full}-{a_full}" if h_full is not None and a_full is not None else None,
        "half_time": f"{h_half}-{a_half}" if h_half is not None and a_half is not None else None,
        "red_card": {"home": pick(home, 2), "away": pick(away, 2)},
        "yellow_card": {"home": pick(home, 3), "away": pick(away, 3)},
        "corner": {
            "home": None if h_corner == -1 else h_corner,
            "away": None if a_corner == -1 else a_corner,
        },
        "overtime": f"{h_ot}-{a_ot}" if has_ot else None,
        "penalty": f"{h_pen}-{a_pen}" if has_pen else None,
    }


def _decode_basketball_scores(home: list[int], away: list[int]) -> dict:
    """解读篮球比分数组 [节1, 节2, 节3, 节4, 加时...]。

    加时节数不固定（0~N 个），全部累加为 overtime；full_time 为四节+加时总和。
    """
    def pick(arr: list[int], i: int) -> int | None:
        return arr[i] if len(arr) > i else None

    def sum_extra(arr: list[int], start: int) -> int:
        return sum(x for x in arr[start:] if x is not None)

    h_q = [pick(home, i) for i in range(4)]
    a_q = [pick(away, i) for i in range(4)]
    h_ot = sum_extra(home, 4)
    a_ot = sum_extra(away, 4)
    h_full = sum(x for x in h_q if x is not None) + h_ot
    a_full = sum(x for x in a_q if x is not None) + a_ot
    return {
        "full_time": f"{h_full}-{a_full}",
        "by_quarter": [
            {"home": h_q[i], "away": a_q[i]} for i in range(4)
        ],
        "overtime": f"{h_ot}-{a_ot}" if h_ot or a_ot else None,
    }


def _odds_triplet(row: dict, prefix: str, labels: tuple[str, str, str]) -> dict:
    """从 row 抽取 odd 三元组并按 labels 命名。prefix 为 'odd'/'first_odd'/'real_odd'。"""
    return {
        labels[0]: row.get(f"{prefix}1"),
        labels[1]: row.get(f"{prefix}2"),
        labels[2]: row.get(f"{prefix}3"),
    }


def _bool_flag(val: Any) -> bool | None:
    """0/1 标志位转 bool，None 透传。"""
    if val is None:
        return None
    try:
        return int(val) == 1
    except (TypeError, ValueError):
        return None


# 欧赔 odd1/2/3 = 主胜/和/客胜；亚盘 odd1/2/3 = 主队水位/盘口/客队水位
_EUROPEAN_LABELS = ("home_win", "draw", "away_win")
_ASIAN_LABELS = ("home_line", "handicap", "away_line")


def _format_european_odds(row: dict) -> dict:
    return {
        "company_id": row.get("company_id"),
        "company_name": row.get("company_name"),
        "initial": _odds_triplet(row, "first_odd", _EUROPEAN_LABELS),
        "current": _odds_triplet(row, "odd", _EUROPEAN_LABELS),
        "latest": _odds_triplet(row, "real_odd", _EUROPEAN_LABELS),
        "in_play": _bool_flag(row.get("is_zoudi")),
        "suspended": _bool_flag(row.get("is_entertained")),
    }


def _format_asian_odds(row: dict) -> dict:
    return {
        "company_id": row.get("company_id"),
        "company_name": row.get("company_name"),
        "initial": _odds_triplet(row, "first_odd", _ASIAN_LABELS),
        "current": _odds_triplet(row, "odd", _ASIAN_LABELS),
        "latest": _odds_triplet(row, "real_odd", _ASIAN_LABELS),
        "in_play": _bool_flag(row.get("is_zoudi")),
        "suspended": _bool_flag(row.get("is_entertained")),
    }


_OVER_UNDER_LABELS = ("over", "total", "under")


def _format_generic_odds(row: dict, labels: tuple[str, str, str]) -> dict:
    return {
        "company_id": row.get("company_id"),
        "company_name": row.get("company_name"),
        "initial": _odds_triplet(row, "first_odd", labels),
        "current": _odds_triplet(row, "odd", labels),
        "latest": _odds_triplet(row, "real_odd", labels),
        "in_play": _bool_flag(row.get("is_zoudi")),
        "suspended": _bool_flag(row.get("is_entertained")),
    }


def _query_odds_table(table: str, match_id: int) -> list[dict]:
    sql = f"""
        SELECT t.company_id, c.company_name,
               t.first_odd1, t.first_odd2, t.first_odd3,
               t.odd1, t.odd2, t.odd3,
               t.real_odd1, t.real_odd2, t.real_odd3,
               t.is_zoudi, t.is_entertained
        FROM {table} t
        LEFT JOIN match_odds_companys c ON t.company_id = c.company_id AND c.match_type = 1
        WHERE t.match_id = %s AND t.odd1 IS NOT NULL
        ORDER BY t.updated_at DESC
        LIMIT 5
    """
    with mysql_connection() as cur:
        cur.execute(sql, (match_id,))
        return list(cur.fetchall())


def _format_standings_row(row: dict) -> dict:
    """积分榜行结构化：分离主客战绩，还原字段语义。"""
    def _venue(prefix: str) -> dict:
        return {
            "points": row.get(f"{prefix}_points"),
            "played": row.get(f"{prefix}_total"),
            "won": row.get(f"{prefix}_won"),
            "draw": row.get(f"{prefix}_draw"),
            "loss": row.get(f"{prefix}_loss"),
            "goals": row.get(f"{prefix}_goals"),
            "goals_against": row.get(f"{prefix}_goals_against"),
            "goal_diff": row.get(f"{prefix}_goal_diff"),
        }
    return {
        "team_id": row.get("team_id"),
        "team_name": row.get("team_name"),
        "position": row.get("position"),
        "points": row.get("points"),
        "deduct_points": row.get("deduct_points"),
        "played": row.get("total"),
        "won": row.get("won"),
        "draw": row.get("draw"),
        "loss": row.get("loss"),
        "goals": row.get("goals"),
        "goals_against": row.get("goals_against"),
        "goal_diff": row.get("goal_diff"),
        "home": _venue("home"),
        "away": _venue("away"),
    }


# 北单 sell_status 状态码：0未开售/1销售中/2未知/3已停售/4已开奖(与竞彩不同)
_BD_SELL_STATUS_MAP: dict[int, str] = {
    0: "not_on_sale",
    1: "on_sale",
    2: "unknown",
    3: "suspended",
    4: "drawn",
}

# 竞彩多选项玩法的固定标签顺序(来源：lottery_jczq_odds/jclq_odds 列注释)
_BF_LABELS = (
    "1:0", "2:0", "2:1", "3:0", "3:1", "3:2", "4:0", "4:1", "4:2",
    "5:0", "5:1", "5:2", "胜其他", "0:0", "1:1", "2:2", "3:3", "平其他",
    "0:1", "0:2", "1:2", "0:3", "1:3", "2:3", "0:4", "1:4", "2:4",
    "0:5", "1:5", "2:5", "负其他",
)
_JQ_LABELS = ("0", "1", "2", "3", "4", "5", "6", "7+")
_BQC_LABELS = ("胜胜", "胜平", "胜负", "平胜", "平平", "平负", "负胜", "负平", "负负")
_SFC_LABELS = (
    "主胜1-5", "客胜1-5", "主胜6-10", "客胜6-10", "主胜11-15", "客胜11-15",
    "主胜16-20", "客胜16-20", "主胜21-25", "客胜21-25", "主胜26+", "客胜26+",
)


def _split_csv_values(raw: str) -> list[Any]:
    """逗号分隔串拆分，尽量转 float，转不了的保留 str。"""
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    result: list[Any] = []
    for p in parts:
        try:
            result.append(float(p))
        except ValueError:
            result.append(p)
    return result


def _parse_lottery_play(play_key: str, raw: str) -> dict | list | str:
    """把竞彩玩法赔率串解析成结构化对象；未知玩法保留原值。"""
    vals = _split_csv_values(raw)
    if play_key == "spf":
        return {"win": vals[0] if vals else None, "draw": vals[1] if len(vals) > 1 else None,
                "loss": vals[2] if len(vals) > 2 else None}
    if play_key == "rq":
        return {"handicap": vals[0] if vals else None, "win": vals[1] if len(vals) > 1 else None,
                "draw": vals[2] if len(vals) > 2 else None, "loss": vals[3] if len(vals) > 3 else None}
    if play_key == "sf":
        return {"home_win": vals[0] if vals else None, "away_win": vals[1] if len(vals) > 1 else None}
    if play_key == "rf":
        return {"handicap": vals[0] if vals else None, "home_win": vals[1] if len(vals) > 1 else None,
                "away_win": vals[2] if len(vals) > 2 else None}
    if play_key == "dxf":
        return {"total": vals[0] if vals else None, "over": vals[1] if len(vals) > 1 else None,
                "under": vals[2] if len(vals) > 2 else None}
    if play_key == "bf":
        return [{"label": _BF_LABELS[i], "odds": vals[i]}
                for i in range(min(len(_BF_LABELS), len(vals)))]
    if play_key == "jq":
        return [{"label": _JQ_LABELS[i], "odds": vals[i]}
                for i in range(min(len(_JQ_LABELS), len(vals)))]
    if play_key == "bqc":
        return [{"label": _BQC_LABELS[i], "odds": vals[i]}
                for i in range(min(len(_BQC_LABELS), len(vals)))]
    if play_key == "sfc":
        return [{"label": _SFC_LABELS[i], "odds": vals[i]}
                for i in range(min(len(_SFC_LABELS), len(vals)))]
    return raw  # sxp 等未知格式


def _parse_sell_status(raw: str, play_keys: tuple[str, ...], is_beidan: bool) -> dict:
    """sell_status 逗号串按 play_keys 顺序拆分成各玩法的销售状态语义。"""
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    result: dict[str, str] = {}
    for i, key in enumerate(play_keys):
        if i < len(parts):
            try:
                code = int(parts[i])
            except ValueError:
                result[key] = "unknown"
                continue
            if is_beidan:
                result[key] = _BD_SELL_STATUS_MAP.get(code, "unknown")
            else:
                result[key] = _SELL_STATUS_MAP.get(code, "unknown")
    return result


# 文字直播/事件 position：0中立/1主队/2客队
_MATCH_POSITION_MAP: dict[int, str] = {0: "neutral", 1: "home", 2: "away"}


def _position_from_id(pos: Any) -> str:
    if pos is None:
        return "unknown"
    try:
        return _MATCH_POSITION_MAP.get(int(pos), "unknown")
    except (TypeError, ValueError):
        return "unknown"


def _format_scorer_row(row: dict) -> dict:
    return {
        "position": row.get("position"),
        "player_id": row.get("player_id"),
        "player_name": row.get("player_name") or row.get("player_full_name"),
        "team_id": row.get("team_id"),
        "team_name": row.get("team_name"),
        "goals": row.get("goals"),
        "penalty_goals": row.get("penalty"),
        "assists": row.get("assists"),
        "minutes_played": row.get("minutes_played"),
    }


def _format_squad_row(row: dict) -> dict:
    return {
        "player_id": row.get("player_id"),
        "player_name": row.get("player_name") or row.get("player_full_name"),
        "position": row.get("position"),
        "shirt_number": row.get("shirt_number"),
        "is_captain": _bool_flag(row.get("is_captain")),
    }


def _format_series_matchup_row(row: dict) -> dict:
    match_ids_raw = row.get("match_ids")
    match_ids = []
    if match_ids_raw:
        match_ids = [int(x) for x in str(match_ids_raw).split(",") if x.strip().isdigit()]
    return {
        "matchup_id": row.get("id"),
        "series_type": _series_type_from_id(row.get("type_id")),
        "state": _series_state_from_id(row.get("state_id")),
        "home_team_id": row.get("home_team_id"),
        "home_name": row.get("home_name"),
        "away_team_id": row.get("away_team_id"),
        "away_name": row.get("away_name"),
        "winner_team_id": row.get("winner_team_id"),
        "home_wins": row.get("home_score"),
        "away_wins": row.get("away_score"),
        "match_ids": match_ids,
        "note": row.get("note"),
    }


def _format_basketball_standings_row(row: dict) -> dict:
    return {
        "team_id": row.get("team_id"),
        "team_name": row.get("team_name"),
        "position": row.get("position"),
        "won": row.get("won"),
        "lost": row.get("lost"),
        "win_rate": row.get("won_rate"),
        "games_back": row.get("game_back"),
        "points_per_game": row.get("points_avg"),
        "points_against_per_game": row.get("points_against_avg"),
        "diff_per_game": row.get("diff_avg"),
        "streak": row.get("streaks"),
        "home_record": row.get("home"),
        "away_record": row.get("away"),
        "last_10": row.get("last_10"),
        "conference_record": row.get("conference"),
        "division_record": row.get("division"),
        "points": row.get("points"),
        "points_for": row.get("points_for"),
        "points_against": row.get("points_agt"),
        "group": row.get("group"),
    }


def _format_tlive_row(row: dict) -> dict:
    return {
        "is_key_event": _bool_flag(row.get("main")),
        "type": row.get("type"),
        "side": _position_from_id(row.get("position")),
        "minute": row.get("time"),
        "content": row.get("data"),
    }


def _format_incident_row(row: dict) -> dict:
    raw_type = row.get("type")
    raw_type_int = int(raw_type) if raw_type is not None else None
    result: dict[str, Any] = {
        "type_code": raw_type_int,
        "type": _INCIDENT_TYPE_MAP.get(raw_type_int, "unknown"),
        "side": _position_from_id(row.get("position")),
        "minute": row.get("time"),
        "second": row.get("second"),
        "player_id": row.get("player_id"),
        "player_name": row.get("player_name"),
        "home_score": row.get("home_score"),
        "away_score": row.get("away_score"),
    }
    if row.get("assist1_name"):
        result["assist1"] = {"player_id": row.get("assist1_id"), "name": row.get("assist1_name")}
    if row.get("assist2_name"):
        result["assist2"] = {"player_id": row.get("assist2_id"), "name": row.get("assist2_name")}
    if row.get("in_player_name") or row.get("out_player_name"):
        result["substitution"] = {
            "in": {"player_id": row.get("in_player_id"), "name": row.get("in_player_name")},
            "out": {"player_id": row.get("out_player_id"), "name": row.get("out_player_name")},
        }
    if row.get("var_reason") is not None:
        result["var_reason"] = row.get("var_reason")
        result["var_result"] = row.get("var_result")
    if row.get("reason_type") is not None:
        raw_reason = int(row.get("reason_type"))
        result["reason_code"] = raw_reason
        result["reason"] = _INCIDENT_REASON_MAP.get(raw_reason, "unknown")
    return result


def _format_transfer_row(row: dict) -> dict:
    result = dict(row)
    raw_type = result.get("transfer_type")
    if raw_type is not None:
        result["transfer_type_code"] = raw_type
        result["transfer_type"] = _TRANSFER_TYPE_MAP.get(int(raw_type), "unknown")
    return result


def _format_player_stats_row(row: dict) -> dict:
    rating = row.get("rating")
    rating_value: float | None = None
    if rating is not None:
        try:
            rating_value = round(int(rating) / 100, 2)
        except (TypeError, ValueError):
            rating_value = None
    return {
        "player_id": row.get("player_id"),
        "player_name": row.get("player_name") or row.get("player_full_name"),
        "team_id": row.get("team_id"),
        "team_name": row.get("team_name"),
        "is_starter": _bool_flag(row.get("first")),
        "minutes_played": row.get("minutes_played"),
        "rating": rating_value,
        "goals": row.get("goals"),
        "penalty_goals": row.get("penalty"),
        "assists": row.get("assists"),
        "red_cards": row.get("red_cards"),
        "yellow_cards": row.get("yellow_cards"),
        "shots": row.get("shots"),
        "shots_on_target": row.get("shots_on_target"),
        "passes": row.get("passes"),
        "passes_accuracy": row.get("passes_accuracy"),
        "key_passes": row.get("key_passes"),
        "crosses": row.get("crosses"),
        "dribble": row.get("dribble"),
        "dribble_succ": row.get("dribble_succ"),
        "tackles": row.get("tackles"),
        "interceptions": row.get("interceptions"),
        "clearances": row.get("clearances"),
        "fouls": row.get("fouls"),
        "was_fouled": row.get("was_fouled"),
        "offsides": row.get("offsides"),
    }


def _format_team_season_stats(row: dict) -> dict:
    return {
        "team_id": row.get("team_id"),
        "team_name": row.get("team_name"),
        "season_id": row.get("season_id"),
        "competition_id": row.get("competition_id"),
        "competition_name": row.get("competition_name"),
        "matches": row.get("matches"),
        "goals": row.get("goals"),
        "penalty_goals": row.get("penalty"),
        "assists": row.get("assists"),
        "red_cards": row.get("red_cards"),
        "yellow_cards": row.get("yellow_cards"),
        "shots": row.get("shots"),
        "shots_on_target": row.get("shots_on_target"),
        "dribble": row.get("dribble"),
        "dribble_succ": row.get("dribble_succ"),
        "clearances": row.get("clearances"),
        "blocked_shots": row.get("blocked_shots"),
        "tackles": row.get("tackles"),
        "passes": row.get("passes"),
        "passes_accuracy": row.get("passes_accuracy"),
        "key_passes": row.get("key_passes"),
        "crosses": row.get("crosses"),
        "crosses_accuracy": row.get("crosses_accuracy"),
        "long_balls": row.get("long_balls"),
        "long_balls_accuracy": row.get("long_balls_accuracy"),
        "duels": row.get("duels"),
        "duels_won": row.get("duels_won"),
        "aerial_won": row.get("aerial_won"),
        "aerial_lost": row.get("aerial_lost"),
        "ground_won": row.get("ground_won"),
        "ground_lost": row.get("ground_lost"),
        "fouls": row.get("fouls"),
        "was_fouled": row.get("was_fouled"),
        "goals_against": row.get("goals_against"),
        "interceptions": row.get("interceptions"),
        "offsides": row.get("offsides"),
        "yellow2red_cards": row.get("yellow2red_cards"),
        "corner_kicks": row.get("corner_kicks"),
        "ball_possession": row.get("ball_possession"),
        "freekicks": row.get("freekicks"),
        "freekick_goals": row.get("freekick_goals"),
        "hit_woodwork": row.get("hit_woodwork"),
    }


def _format_lineup(lineup: dict, players: list[dict]) -> dict:
    home_players = [_format_lineup_player(p) for p in players if p.get("team_id") == lineup.get("home_team_id")]
    away_players = [_format_lineup_player(p) for p in players if p.get("team_id") == lineup.get("away_team_id")]
    # lineup 可能不含 home_team_id/away_team_id，回退按出现顺序二分
    if not home_players and not away_players and players:
        mid = len(players) // 2
        home_players = [_format_lineup_player(p) for p in players[:mid]]
        away_players = [_format_lineup_player(p) for p in players[mid:]]
    return {
        "confirmed": _bool_flag(lineup.get("confirmed")),
        "home_formation": lineup.get("home_formation"),
        "away_formation": lineup.get("away_formation"),
        "home_coach_id": lineup.get("home_coach_id"),
        "away_coach_id": lineup.get("away_coach_id"),
        "home": home_players,
        "away": away_players,
    }


def _format_lineup_player(p: dict) -> dict:
    rating = p.get("rating")
    rating_value: float | None = None
    if rating is not None:
        try:
            rating_value = round(int(rating) / 100, 2)
        except (TypeError, ValueError):
            rating_value = None
    return {
        "player_id": p.get("player_id"),
        "player_name": p.get("name"),
        "shirt_number": p.get("shirt_number"),
        "position": p.get("position"),
        "is_starter": _bool_flag(p.get("first")),
        "is_captain": _bool_flag(p.get("captain")),
        "x": p.get("x"),
        "y": p.get("y"),
        "rating": rating_value,
    }


def _format_injury_row(row: dict) -> dict:
    return {
        "player_id": row.get("player_id"),
        "player_name": row.get("player_name") or row.get("player_full_name"),
        "type": _injury_type_from_id(row.get("type")),
        "reason": row.get("reason"),
        "missed_matches": row.get("missed_matches"),
    }


def _format_odds_trend_row(row: dict) -> dict:
    return {
        "company_id": row.get("company_id"),
        "company_name": row.get("company_name"),
        "odds": {"home_win": row.get("odd1"), "draw": row.get("odd2"), "away_win": row.get("odd3")},
        "in_play": _bool_flag(row.get("is_zoudi")),
        "suspended": _bool_flag(row.get("is_entertained")),
        "changed_at": row.get("updated_at"),
    }


def _format_same_odds_row(row: dict) -> dict:
    return {
        "match_id": row.get("play_id"),
        "league_id": row.get("league_id"),
        "home_team_id": row.get("host_id"),
        "away_team_id": row.get("guest_id"),
        "home_score": row.get("host_score"),
        "away_score": row.get("guest_score"),
        "initial_odds": {"home_win": row.get("win"), "draw": row.get("same"), "away_win": row.get("lost")},
        "current_odds": {"home_win": row.get("real_win"), "draw": row.get("real_same"), "away_win": row.get("real_lost")},
    }
