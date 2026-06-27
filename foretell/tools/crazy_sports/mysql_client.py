"""疯狂体育 MySQL 客户端（data_center 库）。"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from foretell.tools.crazy_sports.db import mysql_connection
from foretell.tools.lottery_code import (
    format_lottery_code,
    parse_lottery_entry_num,
    parse_lottery_issue_num,
)
from foretell.tools.status_codes import PlayType

_FINISHED_STATUS_IDS = {8, 9, 10, 11, 12}
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
        "status": "finished" if row.get("status_id") in _FINISHED_STATUS_IDS else "scheduled",
        "match_time_beijing": row.get("match_time_str") or date_str,
    }


def _row_basketball_match(row: dict) -> dict:
    match_time = row.get("match_time")
    date_str = ""
    if isinstance(match_time, datetime):
        date_str = match_time.strftime("%Y-%m-%d")
    elif row.get("match_time_str"):
        date_str = str(row["match_time_str"])[:10]

    return {
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
        "status": "finished" if row.get("status_id") in _FINISHED_STATUS_IDS else "scheduled",
        "match_time_beijing": row.get("match_time_str") or date_str,
    }


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
            odds[key] = value
    if odds:
        entry["odds"] = odds
    if row.get("sell_status") is not None:
        entry["sell_status"] = row.get("sell_status")
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
        if series_game is not None:
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

    def get_schedule_by_date(
        self,
        date: str,
        sport: str | None = None,
        league_preset: str | None = None,
    ) -> dict:
        rows: list[dict] = []
        if sport in (None, "football"):
            sql = f"""
            SELECT m.id, m.home_team_id, m.away_team_id, m.competition_id,
                   m.match_time, m.match_time_str, m.status_id,
                   ht.short_name_zh AS home_name, at.short_name_zh AS away_name,
                   c.short_name_zh AS league_name
            FROM football_match m
            JOIN football_team ht ON m.home_team_id = ht.id
            JOIN football_team at ON m.away_team_id = at.id
            LEFT JOIN football_competition c ON m.competition_id = c.id
            WHERE {_sql_match_on_date('m.match_time')}
        """
            params: list[Any] = [date, date]
            if league_preset:
                sql += " AND (c.name_zh LIKE %s OR c.short_name_zh LIKE %s OR c.name_en LIKE %s)"
                pattern = _like_pattern(league_preset)
                params.extend([pattern, pattern, pattern])
            sql += " ORDER BY m.match_time ASC LIMIT %s"
            params.append(_SCHEDULE_BY_DATE_LIMIT + 1)
            with mysql_connection() as cur:
                cur.execute(sql, params)
                rows.extend(_row_match(r) for r in cur.fetchall())

        if sport in (None, "basketball"):
            sql = f"""
            SELECT m.id, m.home_team_id, m.away_team_id, m.competition_id,
                   m.match_time, m.match_time_str, m.status_id,
                   ht.short_name_zh AS home_name, at.short_name_zh AS away_name,
                   c.short_name_zh AS league_name
            FROM basketball_match m
            JOIN basketball_team ht ON m.home_team_id = ht.id
            JOIN basketball_team at ON m.away_team_id = at.id
            LEFT JOIN basketball_competition c ON m.competition_id = c.id
            WHERE {_sql_match_on_date('m.match_time')}
        """
            params = [date, date]
            if league_preset:
                sql += (
                    " AND (c.name_zh LIKE %s OR c.short_name_zh LIKE %s "
                    "OR c.name_en LIKE %s OR c.short_name_en LIKE %s)"
                )
                pattern = _like_pattern(league_preset)
                params.extend([pattern, pattern, pattern, pattern])
            sql += " ORDER BY m.match_time ASC LIMIT %s"
            params.append(_SCHEDULE_BY_DATE_LIMIT + 1)
            with mysql_connection() as cur:
                cur.execute(sql, params)
                rows.extend(_row_basketball_match(r) for r in cur.fetchall())

        rows.sort(key=lambda row: row.get("match_time_beijing") or "")
        truncated = len(rows) > _SCHEDULE_BY_DATE_LIMIT
        matches = rows[:_SCHEDULE_BY_DATE_LIMIT]
        return {
            "matches": matches,
            "count": len(matches),
            "limit": _SCHEDULE_BY_DATE_LIMIT,
            "truncated": truncated,
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
            WHERE m.home_team_id = %s OR m.away_team_id = %s
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
            SELECT pt.position, pt.points, pt.won, pt.draw, pt.loss,
                   pt.total, t.short_name_zh AS team_name
            FROM football_points_table_team pt
            JOIN football_points_table p ON pt.table_id = p.id
            JOIN football_team t ON pt.team_id = t.id
            WHERE p.competition_id = %s
            ORDER BY pt.position ASC
            LIMIT 30
        """
        with mysql_connection() as cur:
            cur.execute(sql, (comp_id,))
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_team_season_stats(self, team_id: int | str) -> dict | None:
        return None

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
        return [
            {
                "match_id": r["id"],
                "date": str(r.get("match_time_str", ""))[:10],
                "home_team_id": r["home_team_id"],
                "away_team_id": r["away_team_id"],
                "home_scores": _parse_scores(r.get("home_scores")),
                "away_scores": _parse_scores(r.get("away_scores")),
            }
            for r in rows
        ]

    def get_odds_snapshot(self, match_id: int | str) -> dict | None:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return None

        with mysql_connection() as cur:
            cur.execute(
                """
                SELECT odd1, odd2, odd3, company_id
                FROM football_odds_europe
                WHERE match_id = %s AND odd1 IS NOT NULL
                ORDER BY updated_at DESC
                LIMIT 5
                """,
                (raw_id,),
            )
            europe = cur.fetchall()
            cur.execute(
                """
                SELECT odd1, odd2, odd3, company_id
                FROM football_odds_asian
                WHERE match_id = %s AND odd1 IS NOT NULL
                ORDER BY updated_at DESC
                LIMIT 5
                """,
                (raw_id,),
            )
            asian = cur.fetchall()

        if not europe and not asian:
            return None

        return {
            "match_id": raw_id,
            "european": [dict(r) for r in europe],
            "asian": [dict(r) for r in asian],
        }

    def get_odds_trend(self, match_id: int | str) -> list[dict]:
        return []

    def get_same_odds_history(self, match_id: int | str) -> list[dict]:
        return []

    def get_kelly(self, match_id: int | str) -> dict | None:
        return None

    def get_betfair(self, match_id: int | str) -> dict | None:
        return None

    def get_match_lineup(self, match_id: int | str) -> dict | None:
        return None

    def get_injury_report(self, match_id: int | str) -> dict | None:
        return None

    def get_intel_tags(self, match_id: int | str) -> list[dict]:
        return []

    def get_match_by_id(self, match_id: int | str) -> dict | None:
        raw_id = _parse_int_id(match_id)
        if raw_id is None:
            return None
        sql = """
            SELECT m.id, m.home_team_id, m.away_team_id, m.competition_id,
                   m.match_time, m.match_time_str, m.status_id,
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
        return {
            "match_id": raw_id,
            "home_scores": home_scores,
            "away_scores": away_scores,
            "full_time": f"{home_scores[0]}-{away_scores[0]}"
            if home_scores and away_scores
            else "",
            "match_time": row.get("match_time_str"),
            "status": "finished",
        }


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
