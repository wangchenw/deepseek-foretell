"""球队名称消歧与候选排序（Mock / MySQL 共用）。"""

from __future__ import annotations

import re

_YOUTH_PATTERN = re.compile(r"U\d{1,2}|女足|B队", re.IGNORECASE)


def _normalize_name(name: str) -> str:
    return name.strip().lower().replace(" ", "")


def _team_labels(team: dict) -> list[str]:
    labels: list[str] = []
    for key in ("name", "short_name_zh", "name_zh", "name_en"):
        val = team.get(key)
        if val:
            labels.append(str(val))
    for alias in team.get("aliases", []):
        if alias:
            labels.append(str(alias))
    return labels


def _is_youth_or_secondary(label: str, query: str) -> bool:
    if not _YOUTH_PATTERN.search(label):
        return False
    q = query.upper()
    for marker in ("U16", "U17", "U19", "U21", "女足", "B队"):
        if marker.upper() in q or marker in query:
            return False
    return True


def _match_score(query: str, team: dict) -> tuple[int, int, int]:
    """返回 (总分, 精确匹配分, 国家队加分) 用于排序。"""
    q = _normalize_name(query)
    if not q:
        return (0, 0, 0)

    exact = 0
    fuzzy = 0
    for label in _team_labels(team):
        if _is_youth_or_secondary(label, query):
            continue
        norm = _normalize_name(label)
        if not norm:
            continue
        if norm == q:
            exact = 100
            break
        if q in norm or norm in q:
            fuzzy = max(fuzzy, 50)

    if exact == 0 and fuzzy == 0:
        return (0, 0, 0)

    national_bonus = 10 if team.get("national") == 1 else 0
    total = exact or fuzzy
    if exact == 0 and national_bonus:
        total += national_bonus
    return (total, exact, national_bonus)


def pick_best_team(query: str, candidates: list[dict]) -> dict | None:
    """从候选球队中按消歧规则选出最佳匹配。"""
    scored: list[tuple[tuple[int, int, int], dict]] = []
    for team in candidates:
        score = _match_score(query, team)
        if score[0] > 0:
            scored.append((score, team))

    if not scored:
        return None

    scored.sort(key=lambda item: (-item[0][0], -item[0][1], -item[0][2]))
    best_score, best_team = scored[0]

    result = dict(best_team)
    if len(scored) > 1:
        second_score = scored[1][0]
        if second_score[0] >= best_score[0] - 5:
            alt_names = [
                _team_labels(scored[1][1])[0]
                if _team_labels(scored[1][1])
                else scored[1][1].get("name", "")
            ]
            if alt_names[0]:
                result["_disambiguation_note"] = f"另有相近候选：{alt_names[0]}"

    return result


def team_matches_query(query: str, team: dict) -> bool:
    """判断球队是否匹配查询（用于 Mock 初筛）。"""
    return _match_score(query, team)[0] > 0
