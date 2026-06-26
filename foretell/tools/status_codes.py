"""Foretell Tool 层状态码与玩法枚举。"""

from enum import StrEnum


class StatusCode(StrEnum):
    """Tool envelope 状态码，由 Tool 层判定，不由 LLM 猜测。"""

    OK = "OK"
    DATA_MISSING = "DATA_MISSING"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SKIP_MATCH = "SKIP_MATCH"
    ENTITY_NOT_FOUND = "ENTITY_NOT_FOUND"
    PARTIAL = "PARTIAL"


class PlayType(StrEnum):
    """中国体育彩票玩法内部编码，与 Foretell 产品文档一致。"""

    JINGCAI_FOOTBALL = "101"  # 竞彩足球
    JINGCAI_BASKETBALL = "201"  # 竞彩篮球
    BEIDAN_WIN_LOSS = "301"  # 北单胜负过关
    FOURTEEN_MATCHES = "401"  # 十四场胜负彩 / 任九
    HALF_FULL = "402"  # 半全场
    GOAL_LOTTERY = "403"  # 进球彩
    BEIDAN_HANDICAP = "404"  # 北单让球胜平负
