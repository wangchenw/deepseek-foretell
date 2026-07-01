"""淘汰赛对阵树 Tools:导出 bracket 用于夺冠路径概率计算。"""

from __future__ import annotations

from typing import Literal

from langchain.tools import tool

from foretell.tools.crazy_sports.client import get_crazy_sports_client
from foretell.tools.envelope import make_envelope
from foretell.tools.status_codes import StatusCode

_META_SOURCE = "crazy_sports_db"


def _default_meta(client) -> dict:
    return {"source": _META_SOURCE, "freshness": client.freshness}


@tool
def get_season_bracket(
    season_id: int | str,
    sport: Literal["football", "basketball"] = "football",
) -> str:
    """导出淘汰赛对阵树(用于夺冠路径概率计算)。

    返回完整对阵树:brackets(对阵图) + rounds(阶段:1/8决赛/1/4决赛/半决赛/决赛) +
    match_ups(对阵节点)。每个 match_up 含 parent_id(下一对阵=晋级方向)、
    children_ids(上一对阵来源)、home/away_team_id、winner_team_id、match_ids。

    用于"XX队夺冠概率"类问题:拿对阵树 + 各场胜率(odds隐含概率),
    在 execute_code 沙箱里沿 parent_id 链累乘路径概率。

    Args:
        season_id: MySQL football_brackets.season_id(赛季 ID,须先通过 get_seasons 获取)。
        sport: "football"(默认)或 "basketball"。

    Returns:
        envelope dimension="season_bracket",data={season_id, brackets, rounds,
        match_ups, count}。无对阵数据返回 DATA_MISSING。
    """
    client = get_crazy_sports_client()
    result = client.get_season_bracket(season_id, sport=sport)

    if not result or not result.get("match_ups"):
        return make_envelope(
            StatusCode.DATA_MISSING,
            "season_bracket",
            {"season_id": season_id, "sport": sport, "reason": "该赛季无淘汰赛对阵数据(可能尚未进入淘汰赛阶段)"},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "season_bracket",
        result,
        meta=_default_meta(client),
    )
