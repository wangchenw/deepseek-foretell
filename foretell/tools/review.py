"""赛后复盘 Tools。"""

from __future__ import annotations

import json
from typing import Literal

from langchain.tools import tool

from foretell.tools.crazy_sports.client import get_crazy_sports_client
from foretell.tools.deep import get_match_incidents, get_match_team_stats, get_match_tlive
from foretell.tools.envelope import make_envelope
from foretell.tools.odds import get_odds_trend
from foretell.tools.status_codes import StatusCode

_META_SOURCE = "crazy_sports_db"


def _default_meta(client) -> dict:
    return {"source": _META_SOURCE, "freshness": client.freshness}


_REVIEW_SECTIONS = ("result", "incidents", "team_stats", "tlive", "odds_trend")


@tool
def get_match_result(match_id: int | str) -> str:
    """查询已完场比赛的赛果、技术统计与关键事件，用于赛后复盘。

    Args:
        match_id: MySQL football_match.id，须先通过实体定位获取；仅已完场比赛有数据。
    """
    client = get_crazy_sports_client()
    result = client.get_match_result(match_id)

    if result is None:
        match_info = client.get_match_by_id(match_id)
        if match_info and match_info.get("status") != "finished":
            return make_envelope(
                StatusCode.NOT_APPLICABLE,
                "match_result",
                {"match_id": match_id, "reason": "比赛尚未结束，无法提供完场复盘数据"},
                match_id=match_id,
                meta=_default_meta(client),
            )
        return make_envelope(
            StatusCode.DATA_MISSING,
            "match_result",
            {"match_id": match_id},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "match_result",
        result,
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def get_match_review(
    match_id: int | str,
    sport: str = "football",
    sections: list[Literal["result", "incidents", "team_stats", "tlive", "odds_trend"]] | None = None,
) -> str:
    """C 类赛后复盘一站式聚合:比分 + 事件 + 技术统计 + 文字直播 + 赔率回顾。

    一次调用拿全赛后复盘所需的多维度数据,避免多次调用 + 拼接导致遗漏。
    赛前拦截:未完场直接返回 NOT_APPLICABLE,不复盘。

    Args:
        match_id: MySQL football_match.id 或 basketball_match.id。
        sport: "football"(默认)或 "basketball"。
        sections: 要包含的维度子集,None=全取 ["result","incidents","team_stats",
            "tlive","odds_trend"]。LLM 可传 ["result","odds_trend"] 精简返回省 token。

    Returns:
        envelope dimension="match_review",data 含各 section 子结果,
        meta={sections_included}。赛前返回 NOT_APPLICABLE。
    """
    client = get_crazy_sports_client()
    wanted = list(sections) if sections else list(_REVIEW_SECTIONS)
    # 校验 sections
    invalid = set(wanted) - set(_REVIEW_SECTIONS)
    if invalid:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "match_review",
            {"match_id": match_id, "reason": f"未知 sections: {invalid}"},
            match_id=match_id,
            meta=_default_meta(client),
        )

    data: dict[str, object] = {}
    included: list[str] = []

    for sec in wanted:
        if sec == "result":
            raw = get_match_result.invoke({"match_id": match_id})
            env = json.loads(raw)
            if env["code"] != "OK":
                # 赛前拦截:result 非 OK(未完场/无数据)直接返回不复盘
                return make_envelope(
                    StatusCode.NOT_APPLICABLE if env["code"] == "NOT_APPLICABLE" else env["code"],
                    "match_review",
                    {"match_id": match_id, "reason": env["data"].get("reason", "无赛果数据")},
                    match_id=match_id,
                    meta={**_default_meta(client), "sections_included": []},
                )
            data["result"] = env["data"]
            included.append("result")
        elif sec == "incidents":
            raw = get_match_incidents.invoke({"match_id": match_id, "sport": sport})
            data["incidents"] = json.loads(raw)["data"]
            included.append("incidents")
        elif sec == "team_stats":
            raw = get_match_team_stats.invoke({"match_id": match_id, "sport": sport})
            data["team_stats"] = json.loads(raw)["data"]
            included.append("team_stats")
        elif sec == "tlive":
            raw = get_match_tlive.invoke({"match_id": match_id, "sport": sport})
            data["tlive"] = json.loads(raw)["data"]
            included.append("tlive")
        elif sec == "odds_trend":
            raw = get_odds_trend.invoke({"match_id": match_id, "sport": sport})
            data["odds_trend"] = json.loads(raw)["data"]
            included.append("odds_trend")

    return make_envelope(
        StatusCode.OK,
        "match_review",
        data,
        match_id=match_id,
        meta={**_default_meta(client), "sections_included": included},
    )
