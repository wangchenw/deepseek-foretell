from foretell.tools.deep import get_injury_report, get_intel_tags, get_match_lineup
from foretell.tools.review import get_match_result
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
from foretell.tools.schedule import (
    get_lottery_schedule,
    get_schedule_by_date,
    get_team_schedule,
)
from foretell.tools.search import internet_search
from foretell.tools.stats import get_h2h, get_recent_form, get_standings, get_team_season_stats

ENTITY_TOOLS = [
    resolve_match,
    resolve_lottery_match,
    resolve_team,
    resolve_league,
]

SCHEDULE_TOOLS = [
    get_schedule_by_date,
    get_team_schedule,
    get_lottery_schedule,
]

STATS_TOOLS = [
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

DEEP_TOOLS = [
    get_match_lineup,
    get_injury_report,
    get_intel_tags,
]

REVIEW_TOOLS = [
    get_match_result,
]

FORETELL_TOOLS = (
    ENTITY_TOOLS + SCHEDULE_TOOLS + STATS_TOOLS + ODDS_TOOLS + DEEP_TOOLS + REVIEW_TOOLS + [internet_search]
)


def get_tools():
    return FORETELL_TOOLS
