#!/usr/bin/env python3
"""Extract user questions from ai.foretell_sessions into raw_questions.jsonl."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pymysql

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_common import (  # noqa: E402
    MAX_RUN_EXTRACT,
    ensure_eval_dir,
    get_session_connection,
    user_id_prefix,
)

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "eval" / "raw_questions.jsonl"


def _turn_extract_sql(max_runs: int) -> str:
    cols = ["session_id", "created_at", "updated_at", "JSON_LENGTH(runs) AS run_count"]
    for i in range(max_runs):
        cols.append(
            f"JSON_UNQUOTE(JSON_EXTRACT(runs, '$[{i}].input.input_content')) AS t{i}"
        )
    return f"SELECT {', '.join(cols)} FROM foretell_sessions WHERE runs IS NOT NULL AND session_id > %s ORDER BY session_id LIMIT %s"


def extract(
    *,
    batch_size: int = 400,
    max_rows: int | None = None,
    output: Path = RAW_PATH,
    resume: bool = True,
) -> int:
    ensure_eval_dir()
    checkpoint = output.with_suffix(".checkpoint.json")
    last_id = ""
    written = 0

    if resume and checkpoint.exists():
        data = json.loads(checkpoint.read_text(encoding="utf-8"))
        last_id = data.get("last_session_id", "")
        written = int(data.get("written", 0))
        print(f"Resuming from session_id > {last_id!r}, already written {written}")

    sql = _turn_extract_sql(MAX_RUN_EXTRACT)
    mode = "a" if resume and output.exists() and last_id else "w"

    def _connect():
        return get_session_connection()

    conn = _connect()

    try:
        with output.open(mode, encoding="utf-8") as out_f:
            while True:
                if max_rows is not None and written >= max_rows:
                    break

                limit = batch_size
                if max_rows is not None:
                    limit = min(limit, max_rows - written)

                for attempt in range(3):
                    try:
                        with conn.cursor() as cur:
                            cur.execute(sql, (last_id, limit))
                            rows = cur.fetchall()
                        break
                    except pymysql.err.OperationalError:
                        if attempt == 2:
                            raise
                        conn = _connect()
                        time.sleep(2)

                if not rows:
                    break

                for row in rows:
                    session_id = row[0]
                    created_at = row[1]
                    updated_at = row[2]
                    run_count = row[3] or 0
                    turns = []
                    for idx in range(MAX_RUN_EXTRACT):
                        content = row[4 + idx]
                        if content and str(content).strip():
                            turns.append(
                                {
                                    "run_index": idx,
                                    "content": str(content).strip(),
                                }
                            )

                    record = {
                        "session_id": session_id,
                        "user_id_prefix": user_id_prefix(session_id),
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "run_count": int(run_count),
                        "turns": turns,
                    }
                    out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    written += 1
                    last_id = session_id

                checkpoint.write_text(
                    json.dumps({"last_session_id": last_id, "written": written}, ensure_ascii=False),
                    encoding="utf-8",
                )
                print(f"  batch done: last_id={last_id}, total={written}", flush=True)
                time.sleep(0.05)

                if len(rows) < limit:
                    break
    finally:
        conn.close()

    print(f"Extracted {written} sessions -> {output}")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract foretell session questions")
    parser.add_argument("--batch-size", type=int, default=400)
    parser.add_argument("--max-rows", type=int, default=None, help="Limit rows (for testing)")
    parser.add_argument("--output", type=Path, default=RAW_PATH)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()
    extract(
        batch_size=args.batch_size,
        max_rows=args.max_rows,
        output=args.output,
        resume=not args.no_resume,
    )


if __name__ == "__main__":
    main()
