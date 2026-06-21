"""疯狂体育 MySQL 客户端（data_center 库）。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from foretell.tools.crazy_sports.db import mysql_connection
from foretell.tools.lottery_code import format_jczq_code, parse_jczq_issue_num
from foretell.tools.status_codes import PlayType
from foretell.tools.crazy_sports.team_resolve import pick_best_team

_FINISHED_STATUS_IDS = {8, 9, 10, 11, 12}


def _sql_match_on_date(column: str) -> str:
    return (
        f"{column} >= UNIX_TIMESTAMP(%s) "
        f"AND {column} < UNIX_TIMESTAMP(DATE_ADD(%s, INTERVAL 1 DAY))"
    )


def _sql_match_upcoming(column: str) -> str:
    return f"{column} > UNIX_TIMESTAMP(NOW())"


def _match_id(raw_id: int | str) -> str:
    return f"fm_{raw_id}"


def _parse_match_id(match_id: str) -> int | None:
    if match_id.startswith("fm_"):
        try:
            return int(match_id[3:])
        except ValueError:
            return None
    if match_id.startswith("jczq_"):
        return None
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
        "match_id": _match_id(row["id"]),
        "home_team_id": f"ft_{row['home_team_id']}",
        "away_team_id": f"ft_{row['away_team_id']}",
        "home_name": row.get("home_name") or row.get("short_home") or "",
        "away_name": row.get("away_name") or row.get("short_away") or "",
        "date": date_str,
        "league_id": f"fc_{row['competition_id']}" if row.get("competition_id") else None,
        "league_name": row.get("league_name") or row.get("short_comp") or "",
        "sport": "football",
        "series_game": None,
        "status": "finished" if row.get("status_id") in _FINISHED_STATUS_IDS else "scheduled",
        "match_time_beijing": row.get("match_time_str") or date_str,
    }


def _row_team(row: dict) -> dict:
    return {
        "team_id": f"ft_{row['id']}",
        "name": row.get("short_name_zh") or row.get("name_zh") or "",
        "name_en": row.get("name_en") or "",
        "sport": "football",
        "national": int(row.get("national") or 0),
        "aliases": [a for a in [row.get("name_zh"), row.get("name_en")] if a],
    }


def _row_league(row: dict) -> dict:
    return {
        "league_id": f"fc_{row['id']}",
        "name": row.get("short_name_zh") or row.get("name_zh") or "",
        "name_en": row.get("name_en") or "",
        "sport": "football",
        "aliases": [a for a in [row.get("name_zh"), row.get("name_en")] if a],
    }



class MySQLCrazySportsClient:
    """从 data_center MySQL 读取结构化体育数据。"""

    @property
    def freshness(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def resolve_team(self, name: str) -> dict | None:
        sql = """
            SELECT id, name_zh, name_en, short_name_zh, national
            FROM football_team
            WHERE name_zh LIKE %s OR short_name_zh LIKE %s OR name_en LIKE %s
            LIMIT 50
        """
        pattern = _like_pattern(name)
        with mysql_connection() as cur:
            cur.execute(sql, (pattern, pattern, pattern))
            rows = cur.fetchall()
        if not rows:
            return None
        candidates = [_row_team(row) for row in rows]
        return pick_best_team(name, candidates)

    def resolve_league(self, name: str) -> dict | None:
        sql = """
            SELECT id, name_zh, name_en, short_name_zh
            FROM football_competition
            WHERE name_zh LIKE %s OR short_name_zh LIKE %s OR name_en LIKE %s
            LIMIT 1
        """
        pattern = _like_pattern(name)
        with mysql_connection() as cur:
            cur.execute(sql, (pattern, pattern, pattern))
            row = cur.fetchone()
        return _row_league(row) if row else None

    def resolve_match(
        self,
        home: str,
        away: str,
        date: str | None = None,
        series_game: int | None = None,
    ) -> dict | None:
        if series_game is not None:
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
        sql += " ORDER BY m.match_time DESC LIMIT 1"

        with mysql_connection() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        return _row_match(row) if row else None

    def resolve_lottery_match(
        self,
        play_type: PlayType,
        code: str,
        date: str | None = None,
    ) -> dict | None:
        if play_type != PlayType.JINGCAI_FOOTBALL:
            return None

        issue_num = parse_jczq_issue_num(code)
        if issue_num is None:
            return None

        sql = """
            SELECT id, issue, issue_num, short_home, short_away, short_comp,
                   match_time, match_time_str, home, away, comp
            FROM lottery_jczq_odds
            WHERE issue_num = %s
        """
        params: list[Any] = [issue_num]
        if date:
            sql += f" AND {_sql_match_on_date('match_time')}"
            params.extend([date, date])
        sql += " ORDER BY match_time DESC LIMIT 1"

        with mysql_connection() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        if not row:
            return None

        lottery_id = f"jczq_{row['issue']}_{row['issue_num']}"
        entry = {
            "lottery_id": lottery_id,
            "play_type": play_type.value,
            "code": format_jczq_code(row["issue_num"]),
            "lottery_code": format_jczq_code(row["issue_num"]),
            "issue": str(row["issue"]),
            "issue_num": row["issue_num"],
            "home_name": row["short_home"] or row["home"],
            "away_name": row["short_away"] or row["away"],
            "league_name": row["short_comp"] or row["comp"],
            "date": str(row["match_time_str"])[:10] if row.get("match_time_str") else "",
            "match_id": lottery_id,
        }

        linked = self.resolve_match(
            entry["home_name"],
            entry["away_name"],
            date=entry["date"] or date,
        )
        if linked:
            entry["match_id"] = linked["match_id"]
            entry["match"] = linked
        return entry

    def get_schedule_by_date(
        self,
        date: str,
        sport: str | None = None,
        league_preset: str | None = None,
    ) -> list[dict]:
        if sport == "basketball":
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
            WHERE {_sql_match_on_date('m.match_time')}
            ORDER BY m.match_time ASC
            LIMIT 100
        """
        with mysql_connection() as cur:
            cur.execute(sql, (date, date))
            rows = cur.fetchall()
        return [_row_match(r) for r in rows]

    def get_team_schedule(
        self,
        team_id: str,
        limit: int = 5,
        league_id: str | None = None,
        direction: str = "recent",
    ) -> list[dict]:
        raw_id = team_id.replace("ft_", "")
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
        if league_id:
            comp_id = league_id.replace("fc_", "")
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
        if play_type != PlayType.JINGCAI_FOOTBALL:
            return []

        sql = """
            SELECT issue, issue_num, short_home, short_away, short_comp,
                   match_time, match_time_str
            FROM lottery_jczq_odds
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
        sql += " ORDER BY issue_num ASC LIMIT 50"

        with mysql_connection() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        return [
            {
                "lottery_id": f"jczq_{r['issue']}_{r['issue_num']}",
                "play_type": play_type.value,
                "issue": str(r["issue"]),
                "issue_num": r["issue_num"],
                "lottery_code": format_jczq_code(r["issue_num"]),
                "home_name": r["short_home"],
                "away_name": r["short_away"],
                "league_name": r["short_comp"],
                "date": str(r["match_time_str"])[:10] if r.get("match_time_str") else "",
            }
            for r in rows
        ]

    def get_standings(self, league_id: str) -> list[dict]:
        comp_id = league_id.replace("fc_", "")
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

    def get_team_season_stats(self, team_id: str) -> dict | None:
        return None

    def get_recent_form(
        self, team_id: str, venue: str | None = None, n: int = 5
    ) -> list[dict]:
        raw_id = team_id.replace("ft_", "")
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

    def get_h2h(self, team_a: str, team_b: str, n: int = 5) -> list[dict]:
        id_a = team_a.replace("ft_", "")
        id_b = team_b.replace("ft_", "")
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
                "match_id": _match_id(r["id"]),
                "date": str(r.get("match_time_str", ""))[:10],
                "home_team_id": f"ft_{r['home_team_id']}",
                "away_team_id": f"ft_{r['away_team_id']}",
                "home_scores": _parse_scores(r.get("home_scores")),
                "away_scores": _parse_scores(r.get("away_scores")),
            }
            for r in rows
        ]

    def get_odds_snapshot(self, match_id: str) -> dict | None:
        raw_id = _parse_match_id(match_id)
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
            "match_id": match_id,
            "european": [dict(r) for r in europe],
            "asian": [dict(r) for r in asian],
        }

    def get_odds_trend(self, match_id: str) -> list[dict]:
        return []

    def get_same_odds_history(self, match_id: str) -> list[dict]:
        return []

    def get_kelly(self, match_id: str) -> dict | None:
        return None

    def get_betfair(self, match_id: str) -> dict | None:
        return None

    def get_match_lineup(self, match_id: str) -> dict | None:
        return None

    def get_injury_report(self, match_id: str) -> dict | None:
        return None

    def get_intel_tags(self, match_id: str) -> list[dict]:
        return []

    def get_match_by_id(self, match_id: str) -> dict | None:
        raw_id = _parse_match_id(match_id)
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

    def get_match_result(self, match_id: str) -> dict | None:
        raw_id = _parse_match_id(match_id)
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
            "match_id": match_id,
            "home_scores": home_scores,
            "away_scores": away_scores,
            "full_time": f"{home_scores[0]}-{away_scores[0]}" if home_scores and away_scores else "",
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
