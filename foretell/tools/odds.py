"""盘口维度 Tools。"""

from __future__ import annotations

from langchain.tools import tool

from foretell.tools.crazy_sports.client import get_crazy_sports_client
from foretell.tools.envelope import make_envelope
from foretell.tools.status_codes import StatusCode

_META_SOURCE = "crazy_sports_db"


def _default_meta(client) -> dict:
    return {"source": _META_SOURCE, "freshness": client.freshness}


def _odds_missing(snapshot: dict | None) -> bool:
    if snapshot is None:
        return True
    has_european = "european" in snapshot or "moneyline" in snapshot
    has_asian = "asian" in snapshot or "spread" in snapshot
    return not has_european and not has_asian


@tool
def get_odds_snapshot(match_id: int | str, sport: str = "football") -> str:
    """查询比赛盘口快照（欧赔、亚盘/让分、大小球/大小分）。

    Args:
        match_id: MySQL football_match.id 或 basketball_match.id，须先通过实体定位获取。
        sport: "football"(默认)或 "basketball"。篮球额外返回 over_under 大小分维度
            (查 basketball_odds_over_down,修复 B08:原仅返胜平负+让分,缺大小分)。

    返回结构(data):
        - european[]: 各公司欧赔,每家含 initial(初盘)/current(即时)/latest(最新)三档,
          每档 {home_win, draw, away_win}。归一化隐含概率用 current:
          probs=[1/x for x in (home_win,draw,away_win)], s=sum(probs), norm=[p/s for p in probs]
        - asian_handicap[]: 亚盘/让分,含 handicap(让球数)+ home/away 水位
        - over_under[]: 大小球,含 total(盘口线)+ over/under 水位
    """
    client = get_crazy_sports_client()
    result = client.get_odds_snapshot(match_id, sport=sport)

    if _odds_missing(result):
        return make_envelope(
            StatusCode.SKIP_MATCH,
            "odds_snapshot",
            {"match_id": match_id, "sport": sport, "reason": "欧赔与亚盘均缺失"},
            match_id=match_id,
            meta=_default_meta(client),
        )

    code = StatusCode.OK
    if result is not None:
        has_european = "european" in result or "moneyline" in result
        has_asian = "asian" in result or "spread" in result
        has_over_under = "over_under" in result
        # 篮球期望三维度,足球期望两维度;缺则 PARTIAL
        expected_dims = 3 if sport == "basketball" else 2
        present_dims = sum([has_european, has_asian, has_over_under][:expected_dims])
        if present_dims < expected_dims:
            code = StatusCode.PARTIAL

    return make_envelope(
        code,
        "odds_snapshot",
        result,
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def get_odds_trend(match_id: int | str, sport: str = "football") -> str:
    """查询赔率走势（初盘到即时盘变动，支持足球/篮球）。

    Args:
        match_id: MySQL football_match.id 或 basketball_match.id。
        sport: "football"(默认)或 "basketball"。
            篮球路由 basketball_odds_europe_change 年分区表(修复 F03:原硬编码足球表对篮球 DATA_MISSING)。
    """
    client = get_crazy_sports_client()
    results = client.get_odds_trend(match_id, sport=sport)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "odds_trend",
            {"match_id": match_id, "points": []},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "odds_trend",
        {"match_id": match_id, "points": results, "count": len(results)},
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def get_same_odds_history(match_id: int | str) -> str:
    """查询同赔历史赛果。

    Args:
        match_id: MySQL football_match.id。

    返回结构(data): 离散场次列表,每条含:
        - host_score / guest_score: 赛果比分,推导胜负: host>guest 主胜 / =平 / <负
        - win / same / lost: 该场欧赔(主胜/平/客胜)
        - real_win / real_same / real_lost: 实际结算赔率
    统计胜率须用 execute_code 按 host_score vs guest_score groupby 胜/平/负,禁止逐行心算。
    """
    client = get_crazy_sports_client()
    results = client.get_same_odds_history(match_id)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "same_odds_history",
            {"match_id": match_id, "entries": []},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "same_odds_history",
        {"match_id": match_id, "entries": results, "count": len(results)},
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def get_kelly(match_id: int | str) -> str:
    """查询凯利指数。

    Args:
        match_id: MySQL football_match.id。
    """
    client = get_crazy_sports_client()
    result = client.get_kelly(match_id)

    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "kelly",
            {"match_id": match_id},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "kelly",
        result,
        match_id=match_id,
        meta=_default_meta(client),
    )


@tool
def get_betfair(match_id: int | str) -> str:
    """查询必发成交数据。

    Args:
        match_id: MySQL football_match.id。
    """
    client = get_crazy_sports_client()
    result = client.get_betfair(match_id)

    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "betfair",
            {"match_id": match_id},
            match_id=match_id,
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "betfair",
        result,
        match_id=match_id,
        meta=_default_meta(client),
    )
