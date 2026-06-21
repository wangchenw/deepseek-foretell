"""竞彩足球场次编号解析。

数据库 `issue_num` 编码规则：周几 1 位 + 场次 3 位（零填充）。
例如：6071 = 周六071，2004 = 周二004。
"""

from __future__ import annotations

import re

_WEEKDAY_TO_DIGIT: dict[str, int] = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "日": 7,
}

_DIGIT_TO_WEEKDAY: dict[int, str] = {v: k for k, v in _WEEKDAY_TO_DIGIT.items()}

_JCZQ_CODE_PATTERN = re.compile(r"周([一二三四五六日])(\d{3})")


def parse_jczq_issue_num(code: str) -> int | None:
    """将「周二004」「周六071」或纯数字 6071 转为 lottery_jczq_odds.issue_num。"""
    text = code.strip()
    if not text:
        return None

    if text.isdigit():
        return int(text)

    match = _JCZQ_CODE_PATTERN.search(text)
    if match:
        weekday = _WEEKDAY_TO_DIGIT[match.group(1)]
        sequence = match.group(2)
        return int(f"{weekday}{sequence}")

    return None


def format_jczq_code(issue_num: int) -> str:
    """将 issue_num 格式化为「周六071」风格可读编号。"""
    s = str(issue_num)
    if len(s) < 4:
        s = s.zfill(4)
    weekday_digit = int(s[0])
    sequence = s[1:]
    weekday_cn = _DIGIT_TO_WEEKDAY.get(weekday_digit, "?")
    return f"周{weekday_cn}{sequence}"
