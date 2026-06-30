#!/usr/bin/env python3
"""v3 探针辅助:从 JSON 文件读参数调用 foretell 工具,绕过 PowerShell 引号地狱。

用法:
  uv run python scripts/_v3_probe.py <tool_name> <args_json_file>
  uv run python scripts/_v3_probe.py --sql <sql_file>
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: _v3_probe.py <tool> <args_file> | --sql <sql_file>", file=sys.stderr)
        return 2
    if sys.argv[1] == "--sql":
        sql = Path(sys.argv[2]).read_text(encoding="utf-8")
        cmd = ["uv", "run", "python", "scripts/foretell_eval_helper.py", "sql", sql]
    else:
        tool = sys.argv[1]
        args = Path(sys.argv[2]).read_text(encoding="utf-8")
        # 校验 JSON
        json.loads(args)
        cmd = ["uv", "run", "python", "scripts/foretell_eval_helper.py", "tool", tool, args]
    result = subprocess.run(cmd, capture_output=True)
    try:
        out = result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        out = result.stdout.decode("gbk", errors="replace")
    try:
        err = result.stderr.decode("utf-8")
    except UnicodeDecodeError:
        err = result.stderr.decode("gbk", errors="replace")
    sys.stdout.write(out)
    if err:
        sys.stderr.write(err)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
