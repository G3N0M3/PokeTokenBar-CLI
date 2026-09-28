"""Combat and battle engines for PokeTokenBar."""

from poketokenbar.game.combat.red_battle import (
    RedBattleHandler,
    RED_TEAM,
    generate_player_moves as generate_red_player_moves,
)
from poketokenbar.game.combat.rocket_battle import (
    RocketBattleHandler,
    ROCKET_BOSS_TEAMS,
    get_effectiveness,
    generate_player_moves as generate_rocket_player_moves,
)

__all__ = [
    "RedBattleHandler",
    "RED_TEAM",
    "generate_red_player_moves",
    "RocketBattleHandler",
    "ROCKET_BOSS_TEAMS",
    "get_effectiveness",
    "generate_rocket_player_moves",
]
