"""Foretell 子智能体配置。"""

from __future__ import annotations

from config.settings import FORETELL_SKILLS_DIR
from foretell.tools.deep import get_injury_report, get_intel_tags, get_match_lineup
from foretell.tools.entity import (
    resolve_league,
    resolve_lottery_match,
    resolve_match,
    resolve_team,
)
from foretell.tools.odds import (
    get_betfair,
    get_kelly,
    get_odds_snapshot,
    get_odds_trend,
    get_same_odds_history,
)
from foretell.tools.stats import get_h2h, get_recent_form, get_standings, get_team_season_stats

_STATUS_SKILL = str(FORETELL_SKILLS_DIR / "foretell-status-dictionary")
_ENTITY_SKILL = str(FORETELL_SKILLS_DIR / "foretell-entity-resolution")

ENTITY_RESOLVER_TOOLS = [
    resolve_match,
    resolve_lottery_match,
    resolve_team,
    resolve_league,
]

FUNDAMENTALS_TOOLS = [
    get_standings,
    get_team_season_stats,
    get_recent_form,
    get_h2h,
]

ODDS_TOOLS = [
    get_odds_snapshot,
    get_odds_trend,
    get_same_odds_history,
    get_kelly,
    get_betfair,
]

INTEL_TOOLS = [
    get_match_lineup,
    get_injury_report,
    get_intel_tags,
]

_SUBAGENT_JSON_OUTPUT = """
返回 JSON 对象（不要 markdown 代码块），结构：
{
  "dimension": "<fundamentals|odds|intel|entity>",
  "match_id": "<比赛ID>",
  "stats": {},
  "status_map": {"<子维度>": "<OK|DATA_MISSING|...>"},
  "insights": ["简短洞察"]
}
"""


def get_subagents() -> list[dict]:
    """返回 create_deep_agent(subagents=...) 所需的子智能体配置列表。"""
    return [
        {
            "name": "entity-resolver",
            "description": (
                "定位比赛、球队、联赛实体，返回 match_id 与定位证据。"
                "当用户提及具体对阵、竞彩编号或需先确认对象时使用。"
            ),
            "system_prompt": (
                "你是 Foretell 实体定位专家。按 foretell-entity-resolution Skill 执行："
                "先定位再查询；保留 G7 等系列赛约束；未找到时如实报告。"
                "完成后返回 JSON：dimension=entity, match_id, stats（含定位证据）, "
                "status_map, insights。"
            ),
            "tools": ENTITY_RESOLVER_TOOLS,
            "skills": [_ENTITY_SKILL, _STATUS_SKILL],
        },
        {
            "name": "fundamentals-analyst",
            "description": (
                "分析积分排名、赛季统计、近期近况、历史交锋等基本面维度。"
                "深度分析路径中并行调用。"
            ),
            "system_prompt": (
                "你是 Foretell 基本面分析师。根据指令中的 match_id 与球队 ID "
                "调用统计工具，汇总积分、近况、交锋数据。"
                f"{_SUBAGENT_JSON_OUTPUT}"
            ),
            "tools": FUNDAMENTALS_TOOLS,
            "skills": [_STATUS_SKILL],
        },
        {
            "name": "odds-analyst",
            "description": (
                "分析欧赔、亚盘、大小球、走势、同赔、凯利、必发等盘口维度。"
                "深度分析路径中并行调用。"
            ),
            "system_prompt": (
                "你是 Foretell 盘口分析师。根据 match_id 调用盘口工具。"
                "让球方向使用数据库中文表述，禁止自行换算。"
                "欧赔+亚盘均缺失时在 status_map 标注 SKIP_MATCH。"
                f"{_SUBAGENT_JSON_OUTPUT.replace('fundamentals|odds|intel|entity', 'odds')}"
            ),
            "tools": ODDS_TOOLS,
            "skills": [_STATUS_SKILL],
        },
        {
            "name": "intel-analyst",
            "description": (
                "分析预计阵容、伤停停赛、情报标签等深度情报维度。"
                "深度分析路径中并行调用。"
            ),
            "system_prompt": (
                "你是 Foretell 情报分析师。根据 match_id 调用阵容、伤停、情报工具。"
                f"{_SUBAGENT_JSON_OUTPUT.replace('fundamentals|odds|intel|entity', 'intel')}"
            ),
            "tools": INTEL_TOOLS,
            "skills": [_STATUS_SKILL],
        },
    ]
