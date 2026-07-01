"""代码沙箱工具:LLM 拿到离散数据后写脚本聚合统计,降低心算幻觉。

会话内单沙箱复用:按 thread_id 缓存子进程工作目录,纯标准库,无网络/无文件写。
thread_id 通过 Annotated[RunnableConfig, InjectedToolArg] 注入,不出现在 LLM schema。
"""

from __future__ import annotations

import collections
import json
import subprocess
import sys
import tempfile
import textwrap
import time
from typing import Annotated, Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

from foretell.tools.envelope import make_envelope
from foretell.tools.status_codes import StatusCode

# 按 thread_id 缓存沙箱工作目录,LRU 上限避免内存无限增长
_SANDBOXES: "collections.OrderedDict[str, str]" = collections.OrderedDict()
_MAX_SESSIONS = 8

# 执行超时(秒)
_TIMEOUT_SECONDS = 15

# 禁止的模块名(防逃逸)
_FORBIDDEN_MODULES = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "http",
    "urllib",
    "requests",
    "shutil",
    "pathlib",
    "ctypes",
    "multiprocessing",
    "threading",
    "asyncio",
    "pickle",
    "marshal",
    "importlib",
}


def _thread_id_from_config(config: RunnableConfig) -> str | None:
    """从 RunnableConfig 提取 thread_id。"""
    if not config:
        return None
    configurable = config.get("configurable", {}) if isinstance(config, dict) else {}
    tid = configurable.get("thread_id") if isinstance(configurable, dict) else None
    return tid if tid else None


def _validate_code(code: str) -> str | None:
    """静态检查危险模块引用,返回拒绝原因或 None。"""
    for mod in _FORBIDDEN_MODULES:
        if f"import {mod}" in code or f"from {mod}" in code:
            return f"forbidden module: {mod}"
    if "__import__" in code or "__builtins__" in code:
        return "forbidden dunder access"
    return None


def _build_script(code: str, data_json: str) -> str:
    """组装受限执行脚本:注入 data,捕获输出,隔离 import。"""
    return textwrap.dedent(
        f"""\
        import json
        import sys as _sys
        import statistics
        import math
        import collections
        import re

        _data = json.loads({data_json!r})

        _out = []
        def print(*args, **kwargs):
            _out.append(" ".join(str(a) for a in args))

        try:
            _result = None
{chr(10).join("            " + line for line in code.splitlines())}
            if _result is None:
                _result = chr(10).join(_out) if _out else ""
            json.dump({{"ok": True, "result": _result, "stdout": chr(10).join(_out)}}, _sys.stdout, ensure_ascii=False, default=str)
        except Exception as _e:
            json.dump({{"ok": False, "error": repr(_e), "stdout": chr(10).join(_out)}}, _sys.stdout, ensure_ascii=False, default=str)
        """
    )


@tool
def execute_code(
    code: str,
    config: Annotated[RunnableConfig, InjectedToolArg],
    data: str = "[]",
) -> str:
    """在受限沙箱内执行 Python 脚本,对离散数据做聚合统计。

    用途:工具返回离散列表(如 same_odds_history/odds_trend/h2h)时,先写脚本
    聚合统计(胜率/均值/分布/趋势),再基于统计量分析,禁止心算离散数据。
    能用 get_*/resolve_* 直接查的数据不要用本工具。

    数据传入规则(强制):
        - **禁止手抄工具返回的数值进 code**(易传输出错/幻觉);必须用 data 参数传
          envelope.data 或离散列表的 JSON,脚本内通过 _data 读取。
        - 例: 前一步调 get_same_odds_history 返回 envelope,取其 data 字段序列化为
          JSON 传给本工具 data 参数,脚本内 `_data` 即为已解析的列表。

    Args:
        code: Python 脚本(纯标准库,无网络/文件写)。可用 json/statistics/math/
            collections/re;脚本内 print() 输出会被捕获;末行表达式赋值给 _result
            可作为结构化结果。data 通过变量 _data 注入(已 json.loads)。
        data: JSON 字符串,通常是其他工具返回的 envelope.data 或离散列表,默认 "[]"。

    Returns:
        envelope:{code, dimension:"code_execution", data:{result, stdout},
        meta:{execution_ms}}
    """
    tid = _thread_id_from_config(config)
    if not tid:
        return make_envelope(
            "CONFIG_MISSING",
            "code_execution",
            {"reason": "缺少 thread_id,无法绑定沙箱会话"},
        )

    reject = _validate_code(code)
    if reject:
        return make_envelope(
            "EXECUTION_ERROR",
            "code_execution",
            {"error": f"代码被拒绝: {reject}"},
        )

    # 验证 data 是合法 JSON
    try:
        json.loads(data)
    except json.JSONDecodeError as exc:
        return make_envelope(
            "EXECUTION_ERROR",
            "code_execution",
            {"error": f"data 不是合法 JSON: {exc}"},
        )

    # 复用会话沙箱工作目录(LRU)
    workdir = _SANDBOXES.get(tid)
    if workdir is None:
        workdir = tempfile.mkdtemp(prefix=f"sandbox_{tid[:8]}_")
        _SANDBOXES[tid] = workdir
        _SANDBOXES.move_to_end(tid)
        while len(_SANDBOXES) > _MAX_SESSIONS:
            _SANDBOXES.popitem(last=False)

    script = _build_script(code, data)
    start = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
            cwd=workdir,
            env={"PYTHONPATH": "", "PATH": ""},
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        if proc.returncode != 0:
            return make_envelope(
                "EXECUTION_ERROR",
                "code_execution",
                {"stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode},
                meta={"execution_ms": elapsed_ms},
            )
        payload = json.loads(proc.stdout) if proc.stdout.strip() else {"ok": False, "error": "no output"}
        if not payload.get("ok"):
            return make_envelope(
                "EXECUTION_ERROR",
                "code_execution",
                {"stdout": payload.get("stdout", ""), "error": payload.get("error", "unknown")},
                meta={"execution_ms": elapsed_ms},
            )
        return make_envelope(
            StatusCode.OK,
            "code_execution",
            {"result": payload.get("result", ""), "stdout": payload.get("stdout", "")},
            meta={"execution_ms": elapsed_ms},
        )
    except subprocess.TimeoutExpired:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return make_envelope(
            "EXECUTION_ERROR",
            "code_execution",
            {"error": f"执行超时(>{_TIMEOUT_SECONDS}s)"},
            meta={"execution_ms": elapsed_ms},
        )
    except Exception as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return make_envelope(
            "EXECUTION_ERROR",
            "code_execution",
            {"error": f"沙箱异常: {exc!r}"},
            meta={"execution_ms": elapsed_ms},
        )
