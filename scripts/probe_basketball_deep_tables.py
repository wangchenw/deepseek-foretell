"""探针:确认篮球 deep 表可用性 + football_promotions 字段名。

用于 s3e 剩余域决策:篮球 deep 表能否直接用、字段是否与足球对齐、
promotion_name 能否 JOIN 补全。
"""
from __future__ import annotations

from foretell.tools.crazy_sports.db import mysql_connection


def run(sql: str, params: tuple = ()) -> list[dict]:
    with mysql_connection() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def describe_table(table: str) -> list[dict]:
    return run(f"DESCRIBE {table}")


def count_rows(table: str) -> int:
    rows = run(f"SELECT COUNT(*) AS c FROM {table}")
    return rows[0]["c"] if rows else 0


def main() -> None:
    # ---- 1. 篮球 deep 候选表存在性 + 记录数 ----
    basketball_deep_candidates = [
        "basketball_match_lineup",
        "basketball_match_lineup_detail",
        "basketball_match_incidents",
        "basketball_match_team_stats",
        "basketball_match_stats",
        "basketball_match_player_stats",
        "basketball_match_half_team_stats",
        "basketball_team_injury",
        "basketball_match_team_injury",
        "basketball_intelligence",
        "basketball_match_intelligence",
        "basketball_match_tlive",
        "basketball_team_squad",
        "basketball_match_goals_lost_rate",
        "basketball_bracket_match_up",
        "basketball_bracket_rounds",
        "basketball_brackets",
        "basketball_competition_teams_stats",
        "basketball_competition_players_stats",
        "basketball_competition_shooters",
    ]
    print("=" * 70)
    print("1. 篮球 deep 候选表存在性 + 记录数")
    print("=" * 70)
    existing_tables: list[str] = []
    for t in basketball_deep_candidates:
        try:
            c = count_rows(t)
            existing_tables.append(t)
            print(f"  {t:45s} {c:>10} 行")
        except Exception as e:
            print(f"  {t:45s} 不存在 ({type(e).__name__})")

    # ---- 2. 篮球 deep 表字段结构(对比足球) ----
    football_deep_pairs = [
        ("football_match_lineup", "basketball_match_lineup"),
        ("football_match_lineup_detail", "basketball_match_lineup_detail"),
        ("football_match_incidents", "basketball_match_incidents"),
        ("football_match_team_stats", "basketball_match_team_stats"),
        ("football_match_player_stats", "basketball_match_player_stats"),
        ("football_team_injury", "basketball_team_injury"),
        ("football_intelligence", "basketball_intelligence"),
        ("football_match_tlive", "basketball_match_tlive"),
        ("football_team_squad", "basketball_team_squad"),
        ("football_bracket_match_up", "basketball_bracket_match_up"),
        ("football_competition_teams_stats", "basketball_competition_teams_stats"),
    ]
    print("\n" + "=" * 70)
    print("2. 篮球 deep 表字段结构对比足球")
    print("=" * 70)
    for fb, bb in football_deep_pairs:
        if bb not in existing_tables:
            continue
        try:
            fb_cols = describe_table(fb)
        except Exception:
            fb_cols = []
        bb_cols = describe_table(bb)
        fb_names = {c["Field"] for c in fb_cols}
        bb_names = {c["Field"] for c in bb_cols}
        common = fb_names & bb_names
        only_fb = fb_names - bb_names
        only_bb = bb_names - fb_names
        print(f"\n  [{fb}] vs [{bb}]")
        print(f"    足球字段数={len(fb_names)} 篮球字段数={len(bb_names)} 共同={len(common)}")
        if only_fb:
            print(f"    仅足球: {sorted(only_fb)[:10]}")
        if only_bb:
            print(f"    仅篮球: {sorted(only_bb)[:10]}")
        if common and len(common) < len(fb_names):
            print(f"    共同字段: {sorted(common)[:10]}")

    # ---- 3. 篮球 deep 表覆盖度(多少场比赛/赛季) ----
    print("\n" + "=" * 70)
    print("3. 篮球 deep 表覆盖度(关联 basketball_match 的场次/赛季)")
    print("=" * 70)
    if "basketball_match_incidents" in existing_tables:
        rows = run("""
            SELECT COUNT(DISTINCT bi.match_id) AS matches,
                   COUNT(*) AS cnt
            FROM basketball_match_incidents bi
        """)
        print(f"  basketball_match_incidents: 覆盖 {rows[0].get('matches')} 场, {rows[0].get('cnt')} 行")
    if "basketball_match_lineup" in existing_tables:
        rows = run("SELECT COUNT(DISTINCT match_id) AS matches, COUNT(*) AS cnt FROM basketball_match_lineup")
        print(f"  basketball_match_lineup: 覆盖 {rows[0].get('matches')} 场, {rows[0].get('cnt')} 行")
    if "basketball_match_team_stats" in existing_tables:
        rows = run("SELECT COUNT(DISTINCT match_id) AS matches, COUNT(*) AS cnt FROM basketball_match_team_stats")
        print(f"  basketball_match_team_stats: 覆盖 {rows[0].get('matches')} 场, {rows[0].get('cnt')} 行")
    if "basketball_team_injury" in existing_tables:
        rows = run("SELECT COUNT(DISTINCT team_id) AS teams, COUNT(*) AS cnt FROM basketball_team_injury")
        print(f"  basketball_team_injury: 覆盖 {rows[0].get('teams')} 队, {rows[0].get('cnt')} 行")
    if "basketball_competition_teams_stats" in existing_tables:
        rows = run("SELECT COUNT(DISTINCT season_id) AS seasons, COUNT(DISTINCT team_id) AS teams, COUNT(*) AS cnt FROM basketball_competition_teams_stats")
        print(f"  basketball_competition_teams_stats: {rows[0].get('seasons')} 赛季, {rows[0].get('teams')} 队, {rows[0].get('cnt')} 行")
    if "basketball_competition_players_stats" in existing_tables:
        rows = run("SELECT COUNT(DISTINCT season_id) AS seasons, COUNT(DISTINCT player_id) AS players, COUNT(*) AS cnt FROM basketball_competition_players_stats")
        print(f"  basketball_competition_players_stats: {rows[0].get('seasons')} 赛季, {rows[0].get('players')} 球员, {rows[0].get('cnt')} 行")
    if "basketball_match_intelligence" in existing_tables:
        rows = run("SELECT COUNT(DISTINCT id) AS matches, COUNT(*) AS cnt FROM basketball_match_intelligence")
        print(f"  basketball_match_intelligence: 覆盖 {rows[0].get('matches')} 场, {rows[0].get('cnt')} 行")

    # ---- 4. football_promotions 字段名(P4 暂缓项) ----
    print("\n" + "=" * 70)
    print("4. football_promotions 字段名(P4 promotion_name JOIN 暂缓项)")
    print("=" * 70)
    try:
        cols = describe_table("football_promotions")
        print(f"  football_promotions 字段({len(cols)}):")
        for c in cols:
            print(f"    {c['Field']:30s} {c['Type']}")
        # 抽样数据
        sample = run("SELECT * FROM football_promotions LIMIT 5")
        print(f"\n  抽样 5 行:")
        for r in sample:
            print(f"    {r}")
    except Exception as e:
        print(f"  football_promotions 不存在/无权限: {e}")

    # 顺便确认 promotion_id 在 football_points_table_team 的实际值分布
    print("\n  football_points_table_team.promotion_id 值分布(英超为例):")
    try:
        rows = run("""
            SELECT pt.promotion_id, COUNT(*) AS teams
            FROM football_points_table p
            JOIN football_points_table_team pt ON pt.table_id = p.id
            WHERE p.competition_id = 82
            GROUP BY pt.promotion_id
            ORDER BY teams DESC
            LIMIT 10
        """)
        for r in rows:
            print(f"    promotion_id={r['promotion_id']}: {r['teams']} 队")
    except Exception as e:
        print(f"    查询失败: {e}")


if __name__ == "__main__":
    main()
