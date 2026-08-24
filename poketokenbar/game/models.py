import math
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

class Rarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    LEGENDARY = "legendary"

    @property
    def sort_rank(self) -> int:
        ranks = {Rarity.COMMON: 0, Rarity.UNCOMMON: 1, Rarity.RARE: 2, Rarity.LEGENDARY: 3}
        return ranks[self]

    def graduation_total_for(self, difficulty: 'DifficultyMode' = None) -> int:
        if difficulty is None:
            difficulty = DifficultyMode.EASY
        return difficulty.graduation_totals[self]

    @classmethod
    def from_capture_rate(cls, capture_rate: int, is_legendary: bool = False, is_mythical: bool = False) -> 'Rarity':
        if is_legendary or is_mythical:
            return cls.LEGENDARY
        if capture_rate <= 45:
            return cls.RARE
        if capture_rate <= 120:
            return cls.UNCOMMON
        return cls.COMMON

class DifficultyMode(str, Enum):
    SPEED = "speed"      # Super fast progression (~200x easier)
    EASY = "easy"        # Very casual scale (~50x easier)
    MEDIUM = "medium"    # Balanced CLI scale (Default - ~15x easier)
    HARD = "hard"        # Challenging CLI scale (~5x easier)
    ORIGINAL = "original"# Heavy original macOS app scale

    @property
    def graduation_totals(self) -> Dict[Rarity, int]:
        if self == DifficultyMode.SPEED:
            return {Rarity.COMMON: 2_000_000, Rarity.UNCOMMON: 5_000_000, Rarity.RARE: 10_000_000, Rarity.LEGENDARY: 20_000_000}
        elif self == DifficultyMode.EASY:
            return {Rarity.COMMON: 10_000_000, Rarity.UNCOMMON: 25_000_000, Rarity.RARE: 50_000_000, Rarity.LEGENDARY: 100_000_000}
        elif self == DifficultyMode.HARD:
            return {Rarity.COMMON: 150_000_000, Rarity.UNCOMMON: 375_000_000, Rarity.RARE: 750_000_000, Rarity.LEGENDARY: 1_500_000_000}
        elif self == DifficultyMode.ORIGINAL:
            return {Rarity.COMMON: 750_000_000, Rarity.UNCOMMON: 1_875_000_000, Rarity.RARE: 3_000_000_000, Rarity.LEGENDARY: 6_000_000_000}
        else: # MEDIUM (Default)
            return {Rarity.COMMON: 50_000_000, Rarity.UNCOMMON: 125_000_000, Rarity.RARE: 250_000_000, Rarity.LEGENDARY: 500_000_000}

    @property
    def hatch_threshold(self) -> int:
        if self == DifficultyMode.SPEED:
            return 100_000
        elif self == DifficultyMode.EASY:
            return 500_000
        elif self == DifficultyMode.HARD:
            return 3_000_000
        elif self == DifficultyMode.ORIGINAL:
            return 5_000_000
        else: # MEDIUM
            return 1_500_000

    @property
    def shop_prices(self) -> Dict[str, int]:
        if self == DifficultyMode.SPEED:
            return {"rare_candy": 1_000_000, "mint": 200_000, "shiny_charm": 10_000_000, "egg_normal": 2_000_000, "egg_uncommon": 5_000_000, "egg_rare": 10_000_000}
        elif self == DifficultyMode.EASY:
            return {"rare_candy": 5_000_000, "mint": 1_000_000, "shiny_charm": 30_000_000, "egg_normal": 10_000_000, "egg_uncommon": 25_000_000, "egg_rare": 50_000_000}
        elif self == DifficultyMode.HARD:
            return {"rare_candy": 75_000_000, "mint": 15_000_000, "shiny_charm": 500_000_000, "egg_normal": 100_000_000, "egg_uncommon": 250_000_000, "egg_rare": 500_000_000}
        elif self == DifficultyMode.ORIGINAL:
            return {"rare_candy": 500_000_000, "mint": 100_000_000, "shiny_charm": 3_000_000_000, "egg_normal": 1_000_000_000, "egg_uncommon": 2_500_000_000, "egg_rare": 4_000_000_000}
        else: # MEDIUM
            return {"rare_candy": 25_000_000, "mint": 5_000_000, "shiny_charm": 150_000_000, "egg_normal": 30_000_000, "egg_uncommon": 75_000_000, "egg_rare": 150_000_000}

class PokemonBalance:
    EGG_HATCH_THRESHOLD = 1_500_000
    EXPEDITION_VIRIDIAN = 5_000_000
    EXPEDITION_CERULEAN = 15_000_000
    EXPEDITION_SILVER = 30_000_000
    EXPEDITION_SPEAR_PILLAR = 100_000_000

    @staticmethod
    def phase_threshold(rarity: Rarity, total_forms: int, stage_index: int, difficulty: DifficultyMode = DifficultyMode.MEDIUM) -> int:
        k = max(1, total_forms)
        i = stage_index + 1  # 1-based
        total = float(rarity.graduation_total_for(difficulty))
        denom = float(k * (k + 1)) / 2.0
        return int(round(total * float(i) / denom))

class PokemonNature(str, Enum):
    HARDY = "hardy"
    LONELY = "lonely"
    BRAVE = "brave"
    ADAMANT = "adamant"
    NAUGHTY = "naughty"
    BOLD = "bold"
    DOCILE = "docile"
    RELAXED = "relaxed"
    IMPISH = "impish"
    LAX = "lax"
    TIMID = "timid"
    HASTY = "hasty"
    SERIOUS = "serious"
    JOLLY = "jolly"
    NAIVE = "naive"
    MODEST = "modest"
    MILD = "mild"
    QUIET = "quiet"
    BASHFUL = "bashful"
    RASH = "rash"
    CALM = "calm"
    GENTLE = "gentle"
    SASSY = "sassy"
    CAREFUL = "careful"
    QUIRKY = "quirky"

    @property
    def display_name(self) -> str:
        return self.value.capitalize()

class ItemKind(str, Enum):
    RARE_CANDY = "rare_candy"
    MINT = "mint"
    SHINY_CHARM = "shiny_charm"
    BERRY_ORAN = "berry_oran"
    BERRY_GOLDEN = "berry_golden"
    MEGA_STONE = "mega_stone"
    EXPEDITION_PASS = "expedition_pass"
    POKE_FLUTE = "poke_flute"
    MASTER_BALL = "master_ball"
    MAP_FRAGMENT = "map_fragment"

    def price_for(self, difficulty: DifficultyMode = DifficultyMode.EASY) -> int:
        prices = {
            ItemKind.RARE_CANDY: difficulty.shop_prices.get("rare_candy", 5_000_000),
            ItemKind.MINT: difficulty.shop_prices.get("mint", 1_000_000),
            ItemKind.SHINY_CHARM: difficulty.shop_prices.get("shiny_charm", 30_000_000),
            ItemKind.BERRY_ORAN: 1_000_000,
            ItemKind.BERRY_GOLDEN: 5_000_000,
            ItemKind.MEGA_STONE: 50_000_000,
            ItemKind.EXPEDITION_PASS: 15_000_000,
            ItemKind.POKE_FLUTE: 25_000_000,
            ItemKind.MASTER_BALL: 500_000_000,
            ItemKind.MAP_FRAGMENT: 1_000_000,
        }
        return prices.get(self, 5_000_000)

    @property
    def price(self) -> int:
        return self.price_for(DifficultyMode.EASY)

    @property
    def name_en(self) -> str:
        return {
            ItemKind.RARE_CANDY: "Rare Candy",
            ItemKind.MINT: "Mint",
            ItemKind.SHINY_CHARM: "Shiny Charm",
            ItemKind.BERRY_ORAN: "Oran Berry",
            ItemKind.BERRY_GOLDEN: "Golden Razz Berry",
            ItemKind.MEGA_STONE: "Mega Stone",
            ItemKind.EXPEDITION_PASS: "Expedition Pass",
            ItemKind.POKE_FLUTE: "Poké Flute",
            ItemKind.MASTER_BALL: "Master Ball",
            ItemKind.MAP_FRAGMENT: "Map",
        }[self]

    @property
    def emoji(self) -> str:
        return {
            ItemKind.RARE_CANDY: "🍬",
            ItemKind.MINT: "🌿",
            ItemKind.SHINY_CHARM: "✨",
            ItemKind.BERRY_ORAN: "🫐",
            ItemKind.BERRY_GOLDEN: "🍇",
            ItemKind.MEGA_STONE: "🔮",
            ItemKind.EXPEDITION_PASS: "🎫",
            ItemKind.POKE_FLUTE: "🪈",
            ItemKind.MASTER_BALL: "🌟",
            ItemKind.MAP_FRAGMENT: "📜",
        }[self]

@dataclass
class MonState:
    base_id: int
    path_ids: List[int]
    planned_path_ids: List[int]
    stage_index: int
    used_at_stage: int
    rarity: Rarity
    total_forms: int
    is_shiny: bool = False
    nature: Optional[PokemonNature] = None
    ditto_disguise: Optional[int] = None
    ditto_revealed: bool = False
    is_mega: bool = False
    mega_form: Optional[str] = None
    happiness: int = 100

    @property
    def current_id(self) -> int:
        if not self.path_ids:
            return self.base_id
        idx = min(self.stage_index, len(self.path_ids) - 1)
        return self.path_ids[idx]

@dataclass
class DexEntry:
    id: str
    base_id: int
    final_id: int
    chain_order: List[int]
    rarity: Rarity
    caught_at: str
    is_shiny: bool = False
    nature: Optional[PokemonNature] = None
    names: Dict[int, Dict[str, str]] = field(default_factory=dict)

MEGA_STONES = {
    "3": "Venusaurite",
    "6_X": "Charizardite X",
    "6_Y": "Charizardite Y",
    "9": "Blastoisinite",
    "15": "Beedrillite",
    "18": "Pidgeotite",
    "65": "Alakazite",
    "80": "Slowbronite",
    "94": "Gengarite",
    "115": "Kangaskhanite",
    "127": "Pinsirite",
    "130": "Gyaradosite",
    "142": "Aerodactylite",
    "150_X": "Mewtwonite X",
    "150_Y": "Mewtwonite Y",
    "181": "Ampharosite",
    "208": "Steelixite",
    "212": "Scizorite",
    "214": "Heracronite",
    "229": "Houndoominite",
    "248": "Tyranitarite",
    "254": "Sceptilite",
    "257": "Blazikenite",
    "260": "Swampertite",
    "282": "Gardevoirite",
    "303": "Mawilite",
    "306": "Aggronite",
    "310": "Manectite",
    "319": "Sharpedonite",
    "323": "Cameruptite",
    "334": "Altarianite",
    "354": "Banettite",
    "359": "Absolite",
    "373": "Salamencite",
    "376": "Metagrossite",
    "380": "Latiasite",
    "381": "Latiosite",
    "384": "Meteorite",
    "428": "Lopunnite",
    "445": "Garchompite",
    "448": "Lucarionite",
    "460": "Abomasite",
    "475": "Galladite",
    "531": "Audinite",
    "719": "Diancite"
}
