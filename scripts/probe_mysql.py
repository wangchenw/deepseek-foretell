"""MySQL 连接探针（需 .env 中 MYSQL_* 配置）。"""

from foretell.tools.crazy_sports.db import mysql_connection


def main() -> None:
    with mysql_connection() as cur:
        cur.execute("SELECT DATABASE() AS db, COUNT(*) AS cnt FROM football_match")
        row = cur.fetchone()
        print(f"connected db={row['db']} football_match rows={row['cnt']}")


if __name__ == "__main__":
    main()
