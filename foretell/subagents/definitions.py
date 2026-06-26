"""Foretell 子智能体配置。"""

from __future__ import annotations

from deepagents.middleware.subagents import SubAgent

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
from foretell.tools.schedule import get_team_schedule
from foretell.tools.stats import get_h2h, get_recent_form, get_standings, get_team_season_stats

_STATUS_SKILL = "/skills/foretell-status-dictionary/"
_ENTITY_SKILL = "/skills/foretell-entity-resolution/"

ENTITY_RESOLVER_TOOLS = [
    resolve_match,
    resolve_lottery_match,
    resolve_team,
    resolve_league,
    get_team_schedule,
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

SCREENING_TOOLS = [
    get_recent_form,
    get_odds_snapshot,
]

_SCREENING_JSON_OUTPUT = """
返回 JSON 对象（不要 markdown 代码块），结构：
{
  "dimension": "screening",
  "match_id": "<比赛ID>",
  "stats": {
    "preliminary_direction": "<初筛方向，如主胜/客不败/大球>",
    "confidence": "<高|中|低>",
    "form_summary": "<近况一句话>",
    "odds_summary": "<盘口一句话>"
  },
  "status_map": {"recent_form": "<OK|DATA_MISSING|...>", "odds_snapshot": "<OK|SKIP_MATCH|...>"},
  "insights": ["简短初筛洞察（非最终推荐）"]
}
注意：初筛产出仅供候选筛选，不能直接作为对用户最终推荐词。
"""

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


def get_subagents() -> list[SubAgent]:
    """返回 create_deep_agent(subagents=...) 所需的子智能体配置列表。"""
    return [
        {
            "name": "entity-resolver",
            "description": (
                "定位比赛、球队、联赛实体，返回 match_id 与定位证据。"
                "当用户提及具体对阵、竞彩编号、球队+赛事+下一场赛程，或需消歧（如葡萄牙国家队）时使用。"
            ),
            "system_prompt": (
                "你是 Foretell 实体定位专家。按 foretell-entity-resolution Skill 执行："
                "先定位再查询；保留 G7 等系列赛约束；未找到时如实报告。"
                "处理「某队+某赛事+下一场」时：resolve_team → resolve_league（若提及赛事）"
                "→ get_team_schedule(direction=upcoming)。"
                "完成后返回 JSON：dimension=entity, match_id（若有）, stats（含定位证据与赛程摘要）, "
                "status_map, insights。"
            ),
            "tools": ENTITY_RESOLVER_TOOLS,
            "skills": [_ENTITY_SKILL, _STATUS_SKILL],
        },
        {
            "name": "fundamentals-analyst",
            "description": (
                "分析积分排名、赛季统计、近期近况、历史交锋等基本面维度。深度分析路径中并行调用。"
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
                "分析欧赔、亚盘、大小球、走势、同赔、凯利、必发等盘口维度。深度分析路径中并行调用。"
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
                "分析预计阵容、伤停停赛、情报标签等深度情报维度。深度分析路径中并行调用。"
            ),
            "system_prompt": (
                "你是 Foretell 情报分析师。根据 match_id 调用阵容、伤停、情报工具。"
                f"{_SUBAGENT_JSON_OUTPUT.replace('fundamentals|odds|intel|entity', 'intel')}"
            ),
            "tools": INTEL_TOOLS,
            "skills": [_STATUS_SKILL],
        },
        {
            "name": "screening-agent",
            "description": (
                "批量初筛专用：基于近况与盘口快照快速打分，产出初筛方向与置信度。"
                "用于扫盘、串关、十四场/任九等场景 E，不作为最终推荐。"
            ),
            "system_prompt": (
                "你是 Foretell 批量初筛分析师。根据指令中的 match_id 与主客队 team_id，"
                "调用近况与盘口快照工具，快速评估并返回初筛 JSON。"
                "欧赔+亚盘均缺失时在 status_map 标注 SKIP_MATCH。"
                f"{_SCREENING_JSON_OUTPUT}"
            ),
            "tools": SCREENING_TOOLS,
            "skills": [_STATUS_SKILL],
        },
    ]
