from foretell.tools.code_sandbox import execute_code
from foretell.tools.deep import (
    get_basketball_standings,
    get_injury_report,
    get_intel_tags,
    get_match_incidents,
    get_match_lineup,
    get_match_player_stats,
    get_match_team_stats,
    get_match_tlive,
    get_series_matchup,
    get_team_squad,
    get_top_scorers,
)
from foretell.tools.entity import (
    resolve_league,
    resolve_lottery_match,
    resolve_match,
    resolve_team,
)
from foretell.tools.extra import (
    get_club_ranking,
    get_corner_odds,
    get_fifa_ranking,
    get_first_second,
    get_half_odds,
    get_hundred_europe_odds,
    get_official_handicap_odds,
    get_over_under_odds,
    get_promotions,
    get_recommendations,
    get_season_best,
)
from foretell.tools.odds import (
    get_betfair,
    get_kelly,
    get_odds_snapshot,
    get_odds_trend,
    get_same_odds_history,
)
from foretell.tools.player import (
    get_player_honors,
    get_player_market_value,
    get_player_profile,
    get_player_transfers,
    get_team_honors,
    resolve_basketball_team,
)
from foretell.tools.review import get_match_result, get_match_review
from foretell.tools.schedule import (
    get_lottery_schedule,
    get_schedule_by_date,
    get_team_schedule,
)
from foretell.tools.search import internet_search
from foretell.tools.stats import get_h2h, get_recent_form, get_standings, get_standings_full, get_team_season_stats
from foretell.tools.tournament import (
    get_coach,
    get_goals_lost_rate,
    get_match_half_stats,
    get_referee,
    get_seasons,
    get_venue,
    resolve_basketball_league,
)

ENTITY_TOOLS = [
    resolve_match,
    resolve_lottery_match,
    resolve_team,
    resolve_league,
    resolve_basketball_team,
    resolve_basketball_league,
]

SCHEDULE_TOOLS = [
    get_schedule_by_date,
    get_team_schedule,
    get_lottery_schedule,
]

STATS_TOOLS = [
    get_standings,
    get_standings_full,
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
    get_top_scorers,
    get_team_squad,
    get_series_matchup,
    get_basketball_standings,
    get_match_tlive,
    get_match_incidents,
    get_match_team_stats,
    get_match_player_stats,
]

PLAYER_TOOLS = [
    get_player_profile,
    get_player_market_value,
    get_player_transfers,
    get_player_honors,
    get_team_honors,
]

TOURNAMENT_TOOLS = [
    get_seasons,
    get_coach,
    get_referee,
    get_venue,
    get_match_half_stats,
    get_goals_lost_rate,
]

EXTRA_TOOLS = [
    get_over_under_odds,
    get_half_odds,
    get_corner_odds,
    get_hundred_europe_odds,
    get_official_handicap_odds,
    get_promotions,
    get_first_second,
    get_fifa_ranking,
    get_club_ranking,
    get_season_best,
    get_recommendations,
]

REVIEW_TOOLS = [
    get_match_result,
    get_match_review,
]

SEARCH_TOOLS = [
    internet_search,
]

CODE_TOOLS = [
    execute_code,
]

FORETELL_TOOLS = (
    ENTITY_TOOLS
    + SCHEDULE_TOOLS
    + STATS_TOOLS
    + ODDS_TOOLS
    + DEEP_TOOLS
    + PLAYER_TOOLS
    + TOURNAMENT_TOOLS
    + EXTRA_TOOLS
    + REVIEW_TOOLS
    + SEARCH_TOOLS
    + CODE_TOOLS
)


def get_tools():
    return FORETELL_TOOLS
