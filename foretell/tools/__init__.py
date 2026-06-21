from foretell.tools.entity import (
    resolve_league,
    resolve_lottery_match,
    resolve_match,
    resolve_team,
)
from foretell.tools.schedule import (
    get_lottery_schedule,
    get_schedule_by_date,
    get_team_schedule,
)
from foretell.tools.search import internet_search

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

FORETELL_TOOLS = ENTITY_TOOLS + SCHEDULE_TOOLS + [internet_search]


def get_tools():
    return FORETELL_TOOLS
