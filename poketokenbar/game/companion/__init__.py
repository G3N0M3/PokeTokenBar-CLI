"""Companion subsystem for PokeTokenBar.

Modularized into domain mixins:
- hatching: Egg acquisition and hatching logic.
- evolution: Dynamic, time-based, stone, and mega evolution.
- feeding: Happiness management and feeding commands.
- items: Item purchases, sales, and held item usage.
- expeditions: Pokédex area expeditions and rewards.
- profile: Trainer cards, daily quests, streak, and achievements.
- markets: Corporate investments, dividends, and black market.
- casino: Gacha, slot machine, poker, and blackjack minigames.
- rocket: Team Rocket operations, boss battles, and armory.
"""

import datetime

from poketokenbar.game.companion.engine import CompanionEngine
from poketokenbar.game.companion.hatching import BASE_SPECIES_STARTERS, HatchingMixin
from poketokenbar.game.companion.evolution import (
    TIME_BASED_BRANCH_OVERRIDES,
    get_current_time_of_day,
    EvolutionMixin,
)
from poketokenbar.game.companion.feeding import FeedingMixin
from poketokenbar.game.companion.items import ItemsMixin
from poketokenbar.game.companion.expeditions import ExpeditionsMixin
from poketokenbar.game.companion.profile import ProfileMixin
from poketokenbar.game.companion.markets import MarketsMixin
from poketokenbar.game.companion.casino import CasinoMixin
from poketokenbar.game.companion.rocket import (
    ROCKET_OPERATION_DIALOGUES,
    RocketMixin,
)

__all__ = [
    "CompanionEngine",
    "datetime",
    "BASE_SPECIES_STARTERS",
    "TIME_BASED_BRANCH_OVERRIDES",
    "get_current_time_of_day",
    "ROCKET_OPERATION_DIALOGUES",
    "HatchingMixin",
    "EvolutionMixin",
    "FeedingMixin",
    "ItemsMixin",
    "ExpeditionsMixin",
    "ProfileMixin",
    "MarketsMixin",
    "CasinoMixin",
    "RocketMixin",
]
