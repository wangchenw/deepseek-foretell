"""球员实体 Tools：资料、身价、转会、荣誉。"""

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
def get_player_profile(player_id: int | str, sport: Literal["football", "basketball"] = "football") -> str:
    """查询球员资料（含国籍、身高、体重、位置、身价）。

    Args:
        player_id: MySQL football_player.id / basketball_player.id。
        sport: 足球或篮球，默认足球。
    """
    client = get_crazy_sports_client()
    result = client.get_player_profile(player_id, sport)
    if result is None:
        return make_envelope(
            StatusCode.DATA_MISSING, "player_profile",
            {"player_id": player_id, "sport": sport},
            meta=_default_meta(client),
        )
    return make_envelope(
        StatusCode.OK, "player_profile", {"profile": result, "sport": sport},
        meta=_default_meta(client),
    )


@tool
def get_player_market_value(player_id: int | str) -> str:
    """查询球员身价历史（含时间、币种、年龄）。

    Args:
        player_id: MySQL football_player.id。
    """
    client = get_crazy_sports_client()
    result = client.get_player_market_value(player_id)
    if not result:
        return make_envelope(
            StatusCode.DATA_MISSING, "player_market_value", {"player_id": player_id},
            meta=_default_meta(client),
        )
    return make_envelope(
        StatusCode.OK, "player_market_value", {"history": result, "count": len(result)},
        meta=_default_meta(client),
    )


@tool
def get_player_transfers(player_id: int | str, sport: Literal["football", "basketball"] = "football") -> str:
    """查询球员转会历史（含来源队、目标队、转会费）。

    Args:
        player_id: MySQL football_player.id / basketball_player.id。
        sport: 足球或篮球，默认足球。
    """
    client = get_crazy_sports_client()
    result = client.get_player_transfers(player_id, sport)
    if not result:
        return make_envelope(
            StatusCode.DATA_MISSING, "player_transfers",
            {"player_id": player_id, "sport": sport},
            meta=_default_meta(client),
        )
    return make_envelope(
        StatusCode.OK, "player_transfers", {"history": result, "count": len(result), "sport": sport},
        meta=_default_meta(client),
    )


@tool
def get_player_honors(player_id: int | str, sport: Literal["football", "basketball"] = "football") -> str:
    """查询球员荣誉（含赛事、赛季、球队）。

    Args:
        player_id: MySQL football_player.id / basketball_player.id。
        sport: 足球或篮球，默认足球。
    """
    client = get_crazy_sports_client()
    result = client.get_player_honors(player_id, sport)
    if not result:
        return make_envelope(
            StatusCode.DATA_MISSING, "player_honors",
            {"player_id": player_id, "sport": sport},
            meta=_default_meta(client),
        )
    return make_envelope(
        StatusCode.OK, "player_honors", {"honors": result, "count": len(result), "sport": sport},
        meta=_default_meta(client),
    )


@tool
def get_team_honors(team_id: int | str, sport: Literal["football", "basketball"] = "football") -> str:
    """查询球队荣誉（含赛事、赛季）。

    Args:
        team_id: MySQL football_team.id / basketball_team.id。
        sport: 足球或篮球，默认足球。
    """
    client = get_crazy_sports_client()
    result = client.get_team_honors(team_id, sport)
    if not result:
        return make_envelope(
            StatusCode.DATA_MISSING, "team_honors", {"team_id": team_id, "sport": sport},
            meta=_default_meta(client),
        )
    return make_envelope(
        StatusCode.OK, "team_honors", {"honors": result, "count": len(result), "sport": sport},
        meta=_default_meta(client),
    )


@tool
def resolve_basketball_team(name: str) -> str:
    """模糊解析篮球球队名称，返回候选 team_id 列表。

    Args:
        name: 球队名称（中文/英文/简称均可）。
    """
    client = get_crazy_sports_client()
    result = client.resolve_basketball_team(name)
    if not result:
        return make_envelope(
            StatusCode.ENTITY_NOT_FOUND, "basketball_team", {"query": name},
            meta=_default_meta(client),
        )
    return make_envelope(
        StatusCode.OK, "basketball_team", {"candidates": result, "count": len(result), "query": name},
        meta=_default_meta(client),
    )
