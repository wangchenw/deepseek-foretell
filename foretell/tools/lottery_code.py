"""彩票场次编号解析。

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
_LOTTERY_ENTRY_PATTERN = re.compile(r"第\s*(\d{1,2})\s*场")


def parse_lottery_issue_num(code: str) -> int | None:
    """将「周二004」「周六071」或纯数字 6071 转为 issue_num。"""
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


def parse_lottery_entry_num(code: str) -> int | None:
    """解析足彩「第8场」或纯数字 8。"""
    text = code.strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    match = _LOTTERY_ENTRY_PATTERN.search(text)
    if match:
        return int(match.group(1))
    return None


def format_lottery_code(issue_num: int) -> str:
    """将 issue_num 格式化为「周六071」风格可读编号。"""
    s = str(issue_num)
    if len(s) < 4:
        s = s.zfill(4)
    weekday_digit = int(s[0])
    sequence = s[1:]
    weekday_cn = _DIGIT_TO_WEEKDAY.get(weekday_digit, "?")
    return f"周{weekday_cn}{sequence}"


def parse_jczq_issue_num(code: str) -> int | None:
    """兼容旧函数名：解析竞彩足球/竞彩篮球周几编号。"""
    return parse_lottery_issue_num(code)


def format_jczq_code(issue_num: int) -> str:
    """兼容旧函数名：格式化竞彩足球/竞彩篮球周几编号。"""
    return format_lottery_code(issue_num)
