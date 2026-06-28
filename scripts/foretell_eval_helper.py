#!/usr/bin/env python3
"""Foretell Phase 1 v2 评估辅助器 — 子智能体统一调用入口。

子命令:
  list-tools                 列出所有 foretell 工具的签名与 docstring
  tool <name> '<json_args>'  调用一个 foretell 工具，输出 envelope JSON
  sql '<query>'              执行只读 SELECT 查询，输出 JSON 行集
  schema '<keyword>'         查 information_schema.columns 模糊匹配表名

所有输出均为 JSON（stdout），诊断信息走 stderr。子智能体应解析 stdout。

调用示例（必须 uv run）:
  uv run python scripts/foretell_eval_helper.py list-tools
  uv run python scripts/foretell_eval_helper.py tool resolve_team '{"name":"葡萄牙"}'
  uv run python scripts/foretell_eval_helper.py sql "SELECT id,name_zh,national FROM football_team WHERE name_zh LIKE '%葡萄牙%' LIMIT 10"
  uv run python scripts/foretell_eval_helper.py schema match

安全约束:
  - sql 子命令仅允许 SELECT；出现 INSERT/UPDATE/DELETE/ALTER/DROP/CREATE/REPLACE/
    TRUNCATE/RENAME/GRANT/REVOKE/LOCK/UNLOCK 关键字直接拒绝
  - 查询强制 LIMIT，若用户未写 LIMIT 自动追加 LIMIT 200
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# 让 foretell 包可被导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|ALTER|DROP|CREATE|REPLACE|TRUNCATE|"
    r"RENAME|GRANT|REVOKE|LOAD|CALL|HANDLER|LOCK|UNLOCK|SET|START\s+TRANSACTION|"
    r"COMMIT|ROLLBACK|BEGIN)\b",
    re.IGNORECASE,
)


def cmd_list_tools() -> int:
    from foretell.tools import FORETELL_TOOLS

    out: list[dict] = []
    for t in FORETELL_TOOLS:
        out.append(
            {
                "name": t.name,
                "description": (t.description or "").strip(),
                "args": t.args,
            }
        )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_tool(name: str, args_json: str) -> int:
    from foretell.tools import FORETELL_TOOLS

    tool_map = {t.name: t for t in FORETELL_TOOLS}
    if name not in tool_map:
        print(
            json.dumps(
                {"error": f"unknown tool: {name}", "available": list(tool_map)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    try:
        args = json.loads(args_json) if args_json.strip() else {}
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"invalid args json: {e}"}, ensure_ascii=False), file=sys.stderr)
        return 2

    t = tool_map[name]
    try:
        raw = t.invoke(args)
        # @tool 返回 str（envelope JSON 字符串）；尝试解析后重新格式化输出
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            print(raw)
    except Exception as e:
        print(
            json.dumps(
                {"error": f"tool invoke failed: {type(e).__name__}: {e}"},
                ensure_ascii=False,
            ),
        )
        return 1
    return 0


def _enforce_readonly(query: str) -> None:
    if _FORBIDDEN.search(query):
        raise ValueError("query contains forbidden non-SELECT keyword")


def _ensure_limit(query: str) -> str:
    # 简化判断：若整句（去注释后）没有 LIMIT，自动追加
    stripped = re.sub(r"--.*$", "", query, flags=re.MULTILINE)
    stripped = re.sub(r"/\*.*?\*/", "", stripped, flags=re.DOTALL)
    if not re.search(r"\bLIMIT\s+\d+", stripped, re.IGNORECASE):
        query = query.rstrip().rstrip(";") + " LIMIT 200"
    return query


def cmd_sql(query: str) -> int:
    from foretell.tools.crazy_sports.db import mysql_connection

    try:
        _enforce_readonly(query)
    except ValueError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        return 2
    query = _ensure_limit(query)

    try:
        with mysql_connection() as cur:
            cur.execute(query)
            rows = cur.fetchall()
        # row 是 dict 行（DictCursor）；datetime/Decimal 需序列化
        print(json.dumps(_safe_rows(rows), ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print(
            json.dumps(
                {"error": f"sql failed: {type(e).__name__}: {e}", "query": query},
                ensure_ascii=False,
            ),
        )
        return 1
    return 0


def cmd_schema(keyword: str) -> int:
    from foretell.tools.crazy_sports.db import mysql_connection

    if not keyword or not keyword.replace("%", "").isalnum():
        print(json.dumps({"error": "keyword must be alphanumeric"}, ensure_ascii=False))
        return 2
    pattern = f"%{keyword}%"
    sql = (
        "SELECT table_name, column_name, column_type, column_comment "
        "FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name LIKE %s "
        "ORDER BY table_name, ordinal_position LIMIT 300"
    )
    try:
        with mysql_connection() as cur:
            cur.execute(sql, (pattern,))
            rows = cur.fetchall()
        print(json.dumps(_safe_rows(rows), ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print(json.dumps({"error": f"schema failed: {type(e).__name__}: {e}"}, ensure_ascii=False))
        return 1
    return 0


def _safe_rows(rows: list) -> list:
    """把 DictCursor 行转成可 JSON 序列化的 dict（保留原始键）。"""
    out = []
    for r in rows:
        out.append(dict(r) if hasattr(r, "keys") else r)
    return out


def _usage() -> int:
    print(__doc__, file=sys.stderr)
    return 2


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        return _usage()
    cmd = argv[1]
    if cmd == "list-tools":
        return cmd_list_tools()
    if cmd == "tool":
        if len(argv) < 4:
            return _usage()
        return cmd_tool(argv[2], argv[3])
    if cmd == "sql":
        if len(argv) < 3:
            return _usage()
        return cmd_sql(argv[2])
    if cmd == "schema":
        if len(argv) < 3:
            return _usage()
        return cmd_schema(argv[2])
    return _usage()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
