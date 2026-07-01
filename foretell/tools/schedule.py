"""赛程查询 Tools。"""

from __future__ import annotations

from typing import Literal

from langchain.tools import tool

from foretell.tools.crazy_sports.client import get_crazy_sports_client
from foretell.tools.envelope import make_envelope
from foretell.tools.status_codes import PlayType, StatusCode

_META_SOURCE = "crazy_sports_db"


def _default_meta(client) -> dict:
    return {"source": _META_SOURCE, "freshness": client.freshness}


@tool
def get_schedule_by_date(
    date: str,
    sport: Literal["football", "basketball"] | None = None,
    league_preset: str | None = None,
    tier: Literal["top", "all"] | None = None,
) -> str:
    """按日期查询赛程列表。

    Args:
        date: 日期，格式 YYYY-MM-DD。
        sport: 运动类型过滤，football 或 basketball（可选）。
        league_preset: 联赛名称过滤，如「欧冠」「NBA」（可选）。
        tier: 赛事层级过滤，top=仅顶级赛事（世界杯/欧冠/五大联赛/NBA 等），
            all 或 None=默认策略（大赛日顶级赛事优先占位，余量按时间填低级别）。
    """
    client = get_crazy_sports_client()
    result = client.get_schedule_by_date(
        date, sport=sport, league_preset=league_preset, tier=tier
    )
    matches = result["matches"]

    meta = _default_meta(client)
    meta["limit"] = result["limit"]
    meta["truncated"] = result["truncated"]
    meta["total_count"] = result["total_count"]
    meta["tier_count"] = result["tier_count"]
    if result.get("warning"):
        meta["warning"] = result["warning"]

    if not matches:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "schedule_by_date",
            {"date": date, "sport": sport, "league_preset": league_preset, "tier": tier, "matches": []},
            meta=meta,
        )

    return make_envelope(
        StatusCode.OK,
        "schedule_by_date",
        {
            "date": date,
            "league_preset": league_preset,
            "tier": tier,
            "matches": matches,
            "count": result["count"],
        },
        meta=meta,
    )


@tool
def get_team_schedule(
    team_id: int | str,
    limit: int = 5,
    league_id: int | str | None = None,
    direction: Literal["upcoming", "recent", "all"] = "recent",
    sport: str = "football",
) -> str:
    """查询球队近期或未来赛程。

    Args:
        team_id: MySQL football_team.id 或 basketball_team.id。
        limit: 返回场次数量上限，默认 5。
        league_id: MySQL football_competition.id 或 basketball_competition.id（可选）。
        direction: upcoming=下一场/未来，recent=最近已结束，all=全部按时间倒序。
        sport: "football"(默认)或 "basketball"。篮球走 basketball_match 表(完场 status_id=10)。
    """
    client = get_crazy_sports_client()
    results = client.get_team_schedule(
        team_id,
        limit=limit,
        league_id=league_id,
        direction=direction,
        sport=sport,
    )

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "team_schedule",
            {
                "team_id": team_id,
                "league_id": league_id,
                "direction": direction,
                "sport": sport,
                "matches": [],
            },
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "team_schedule",
        {
            "team_id": team_id,
            "league_id": league_id,
            "direction": direction,
            "sport": sport,
            "matches": results,
            "count": len(results),
        },
        meta=_default_meta(client),
    )


@tool
def get_lottery_schedule(
    play_type: Literal["101", "201", "301", "401", "402", "403", "404", "405"],
    date: str | None = None,
    period: str | None = None,
) -> str:
    """查询彩票可售场次列表。

    Args:
        play_type: 玩法编码，101=竞彩足球、201=竞彩篮球、301=北单胜负、
            401=十四场胜负彩(sfc)、405=任选九场(rj,与 sfc 同期共享 14 场)、
            402=半全场、403=进球彩、404=北单让球胜平负。
        date: 销售日期 YYYY-MM-DD（可选，默认当日样本数据）。
        period: 彩票期号（可选，十四场/任九等使用）。

    业务规则:
        - entries[].odds 键为英文全称(消除拼音缩写歧义):
            win_draw_loss=胜平负(原 spf)、handicap_wdl=让球胜平负(原 rq)、
            correct_score=比分(原 bf)、total_goals=进球数(原 jq)、
            half_full_result=半全场(原 bqc)、win_loss=胜负(原 sf,篮球)、
            handicap_wl=让球胜负(原 rf)、over_under=大小分(原 dxf)、
            fourteen_wdl=十四场胜平负(原 sfc)、six_x_po=六选波(原 sxp,北单)。
        - 竞彩(101/201) odds 内层为 CSV 字符串(如 "3.52,3.66,2.00");
            北单(301/404) odds 内层为 JSON(列表[{label,odds}])。解析时按 play_type 分支。
        - lottery_zc_match(sfc/rj/bqc/jqc) 与 lottery_match(竞彩/北单) 分表存储,
            issue_num=issue*10+match_no(十四场/任九合成编号)。
        - correct_score(比分)含 31 档,其中含 3 个"其他"合计项(主其他/平其他/客其他),
            与 28 个具体比分重叠;各档赔率倒数归一后总和 >1 属正常(合计项重叠所致),
            非数据错误。归一化取 Top-N 概率比分时,需向用户说明此特性。
    """
    client = get_crazy_sports_client()
    pt = PlayType(play_type)
    results = client.get_lottery_schedule(pt, date=date, period=period)

    if not results:
        return make_envelope(
            StatusCode.DATA_MISSING,
            "lottery_schedule",
            {"play_type": play_type, "date": date, "period": period, "entries": []},
            meta=_default_meta(client),
        )

    return make_envelope(
        StatusCode.OK,
        "lottery_schedule",
        {
            "play_type": play_type,
            "date": date,
            "period": period,
            "entries": results,
            "count": len(results),
        },
        meta=_default_meta(client),
    )
