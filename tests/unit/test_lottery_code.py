from foretell.tools.lottery_code import (
    format_jczq_code,
    format_lottery_code,
    parse_jczq_issue_num,
    parse_lottery_entry_num,
    parse_lottery_issue_num,
)


def test_parse_tuesday_004():
    assert parse_jczq_issue_num("周二004") == 2004


def test_parse_saturday_071():
    assert parse_jczq_issue_num("周六071") == 6071


def test_parse_pure_issue_num():
    assert parse_jczq_issue_num("6071") == 6071


def test_parse_from_composite_text():
    assert parse_jczq_issue_num("竞彩足球周二004 巴黎VS拜仁") == 2004
    assert parse_lottery_issue_num("竞彩篮球周日301") == 7301


def test_format_jczq_code():
    assert format_jczq_code(6071) == "周六071"
    assert format_jczq_code(2004) == "周二004"
    assert format_lottery_code(7301) == "周日301"


def test_parse_lottery_entry_num():
    assert parse_lottery_entry_num("第8场") == 8
    assert parse_lottery_entry_num("本期任选14场第12场") == 12
    assert parse_lottery_entry_num("8") == 8


def test_invalid_code():
    assert parse_jczq_issue_num("周二04") is None
    assert parse_jczq_issue_num("") is None
    assert parse_lottery_entry_num("第十五场") is None
