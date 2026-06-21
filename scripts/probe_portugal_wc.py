from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
from foretell.tools.crazy_sports.db import mysql_connection

PT_ID = 13152

with mysql_connection() as cur:
    cur.execute(
        """
        SELECT m.id, m.match_time_str, m.status_id, ht.short_name_zh, at.short_name_zh, c.short_name_zh
        FROM football_match m
        JOIN football_team ht ON m.home_team_id = ht.id
        JOIN football_team at ON m.away_team_id = at.id
        LEFT JOIN football_competition c ON m.competition_id = c.id
        WHERE (m.home_team_id = %s OR m.away_team_id = %s)
          AND m.match_time > NOW()
        ORDER BY m.match_time ASC
        LIMIT 10
        """,
        (PT_ID, PT_ID),
    )
    print("Portugal NT future matches:")
    for r in cur.fetchall():
        print(r)

    cur.execute(
        """
        SELECT m.id, m.match_time_str, c.short_name_zh
        FROM football_match m
        LEFT JOIN football_competition c ON m.competition_id = c.id
        WHERE (m.home_team_id = %s OR m.away_team_id = %s)
          AND c.id = 1
        ORDER BY m.match_time DESC
        LIMIT 5
        """,
        (PT_ID, PT_ID),
    )
    print("Portugal WC history/recent:")
    for r in cur.fetchall():
        print(r)
