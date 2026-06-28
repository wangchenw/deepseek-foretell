"""扩展 Tools：大小球/半场/角球/百欧/官方让球赔率、排名、冠亚军、赛季最佳、心水推荐、升降级。"""

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
def get_over_under_odds(match_id: int | str) -> str:
    """查询大小球赔率（含初盘/即时/收盘，over/total/under）。

    Args:
        match_id: MySQL football_match.id。
    """
    client = get_crazy_sports_client()
    result = client.get_over_under_odds(match_id)
    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING, "over_under_odds", {"match_id": match_id},
            source=_META_SOURCE, match_id=match_id,
        )
    return make_envelope(
        StatusCode.OK, "over_under_odds", result,
        source=_META_SOURCE, match_id=match_id, meta=_default_meta(client),
    )


@tool
def get_half_odds(match_id: int | str) -> str:
    """查询半场赔率（半场欧赔/亚盘/大小球）。

    Args:
        match_id: MySQL football_match.id。
    """
    client = get_crazy_sports_client()
    result = client.get_half_odds(match_id)
    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING, "half_odds", {"match_id": match_id},
            source=_META_SOURCE, match_id=match_id,
        )
    return make_envelope(
        StatusCode.OK, "half_odds", result,
        source=_META_SOURCE, match_id=match_id, meta=_default_meta(client),
    )


@tool
def get_corner_odds(match_id: int | str) -> str:
    """查询角球赔率（全场角球 + 半场角球）。

    Args:
        match_id: MySQL football_match.id。
    """
    client = get_crazy_sports_client()
    result = client.get_corner_odds(match_id)
    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING, "corner_odds", {"match_id": match_id},
            source=_META_SOURCE, match_id=match_id,
        )
    return make_envelope(
        StatusCode.OK, "corner_odds", result,
        source=_META_SOURCE, match_id=match_id, meta=_default_meta(client),
    )


@tool
def get_hundred_europe_odds(match_id: int | str) -> str:
    """查询百欧赔率（初盘/收盘欧赔，无即时盘）。

    Args:
        match_id: MySQL football_match.id。
    """
    client = get_crazy_sports_client()
    result = client.get_hundred_europe_odds(match_id)
    if not result:
        return make_envelope(
            StatusCode.DATA_MISSING, "hundred_europe_odds", {"match_id": match_id},
            source=_META_SOURCE, match_id=match_id,
        )
    return make_envelope(
        StatusCode.OK, "hundred_europe_odds", {"odds": result, "count": len(result)},
        source=_META_SOURCE, match_id=match_id, meta=_default_meta(client),
    )


@tool
def get_official_handicap_odds(match_id: int | str) -> str:
    """查询官方让球盘（含让球数 + 胜平负初盘/收盘）。

    Args:
        match_id: MySQL football_match.id。
    """
    client = get_crazy_sports_client()
    result = client.get_official_handicap_odds(match_id)
    if not result:
        return make_envelope(
            StatusCode.DATA_MISSING, "official_handicap_odds", {"match_id": match_id},
            source=_META_SOURCE, match_id=match_id,
        )
    return make_envelope(
        StatusCode.OK, "official_handicap_odds", {"odds": result, "count": len(result)},
        source=_META_SOURCE, match_id=match_id, meta=_default_meta(client),
    )


@tool
def get_promotions(sport: Literal["football", "basketball"] = "football") -> str:
    """查询升降级信息。

    Args:
        sport: 足球或篮球，默认足球。
    """
    client = get_crazy_sports_client()
    result = client.get_promotions(sport)
    if not result:
        return make_envelope(
            StatusCode.DATA_MISSING, "promotions", {"sport": sport},
            source=_META_SOURCE, sport=sport,
        )
    return make_envelope(
        StatusCode.OK, "promotions", {"promotions": result, "count": len(result)},
        source=_META_SOURCE, sport=sport, meta=_default_meta(client),
    )


@tool
def get_first_second(limit: int = 20) -> str:
    """查询冠亚军信息（含冠军/亚军球队、奖金、销量状态）。

    Args:
        limit: 返回条数上限，默认 20。
    """
    client = get_crazy_sports_client()
    result = client.get_first_second(limit)
    if not result:
        return make_envelope(
            StatusCode.DATA_MISSING, "first_second", {"limit": limit},
            source=_META_SOURCE,
        )
    return make_envelope(
        StatusCode.OK, "first_second", {"items": result, "count": len(result)},
        source=_META_SOURCE, meta=_default_meta(client),
    )


@tool
def get_fifa_ranking(gender: int = 1, limit: int = 30) -> str:
    """查询 FIFA 国家队排名（含积分、排名变化）。

    Args:
        gender: 1=男足、2=女足，默认男足。
        limit: 返回条数上限，默认 30。
    """
    client = get_crazy_sports_client()
    result = client.get_fifa_ranking(gender, limit)
    if not result:
        return make_envelope(
            StatusCode.DATA_MISSING, "fifa_ranking", {"gender": gender, "limit": limit},
            source=_META_SOURCE,
        )
    return make_envelope(
        StatusCode.OK, "fifa_ranking", {"rankings": result, "count": len(result)},
        source=_META_SOURCE, gender=gender, meta=_default_meta(client),
    )


@tool
def get_club_ranking(limit: int = 30) -> str:
    """查询俱乐部排名（含积分、排名变化）。

    Args:
        limit: 返回条数上限，默认 30。
    """
    client = get_crazy_sports_client()
    result = client.get_club_ranking(limit)
    if not result:
        return make_envelope(
            StatusCode.DATA_MISSING, "club_ranking", {"limit": limit},
            source=_META_SOURCE,
        )
    return make_envelope(
        StatusCode.OK, "club_ranking", {"rankings": result, "count": len(result)},
        source=_META_SOURCE, meta=_default_meta(client),
    )


@tool
def get_season_best(
    competition_id: int | str,
    season_id: int | str | None = None,
) -> str:
    """查询赛季最佳球员/球队（默认取最新赛季）。

    Args:
        competition_id: MySQL football_competition.id。
        season_id: 可选，指定赛季；不传取最新赛季。
    """
    client = get_crazy_sports_client()
    result = client.get_season_best(competition_id, season_id)
    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING, "season_best",
            {"competition_id": competition_id, "season_id": season_id},
            source=_META_SOURCE, competition_id=competition_id,
        )
    return make_envelope(
        StatusCode.OK, "season_best", result,
        source=_META_SOURCE, competition_id=competition_id, meta=_default_meta(client),
    )


@tool
def get_recommendations(match_id: int | str) -> str:
    """查询心水推荐（含置信度、推荐理由）。

    Args:
        match_id: MySQL football_match.id。
    """
    client = get_crazy_sports_client()
    result = client.get_recommendations(match_id)
    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING, "recommendations", {"match_id": match_id},
            source=_META_SOURCE, match_id=match_id,
        )
    return make_envelope(
        StatusCode.OK, "recommendations", result,
        source=_META_SOURCE, match_id=match_id, meta=_default_meta(client),
    )
