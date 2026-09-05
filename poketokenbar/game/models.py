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
    MEGA = "mega"

    @property
    def sort_rank(self) -> int:
        ranks = {Rarity.COMMON: 0, Rarity.UNCOMMON: 1, Rarity.RARE: 2, Rarity.LEGENDARY: 3, Rarity.MEGA: 4}
        return ranks[self]

    def graduation_total_for(self, difficulty: 'DifficultyMode' = None) -> int:
        if difficulty is None:
            difficulty = DifficultyMode.MEDIUM
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
            return {Rarity.COMMON: 2_000_000, Rarity.UNCOMMON: 5_000_000, Rarity.RARE: 10_000_000, Rarity.LEGENDARY: 20_000_000, Rarity.MEGA: 40_000_000}
        elif self == DifficultyMode.EASY:
            return {Rarity.COMMON: 10_000_000, Rarity.UNCOMMON: 25_000_000, Rarity.RARE: 50_000_000, Rarity.LEGENDARY: 100_000_000, Rarity.MEGA: 200_000_000}
        elif self == DifficultyMode.HARD:
            return {Rarity.COMMON: 150_000_000, Rarity.UNCOMMON: 375_000_000, Rarity.RARE: 750_000_000, Rarity.LEGENDARY: 1_500_000_000, Rarity.MEGA: 3_000_000_000}
        elif self == DifficultyMode.ORIGINAL:
            return {Rarity.COMMON: 750_000_000, Rarity.UNCOMMON: 1_875_000_000, Rarity.RARE: 3_000_000_000, Rarity.LEGENDARY: 6_000_000_000, Rarity.MEGA: 12_000_000_000}
        else: # MEDIUM (Default)
            return {Rarity.COMMON: 50_000_000, Rarity.UNCOMMON: 125_000_000, Rarity.RARE: 250_000_000, Rarity.LEGENDARY: 500_000_000, Rarity.MEGA: 1_000_000_000}

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
            return {"rare_candy": 1_000_000, "mint": 200_000, "egg_normal": 2_000_000, "egg_uncommon": 5_000_000, "egg_rare": 10_000_000}
        elif self == DifficultyMode.EASY:
            return {"rare_candy": 5_000_000, "mint": 1_000_000, "egg_normal": 10_000_000, "egg_uncommon": 25_000_000, "egg_rare": 50_000_000}
        elif self == DifficultyMode.HARD:
            return {"rare_candy": 75_000_000, "mint": 15_000_000, "egg_normal": 100_000_000, "egg_uncommon": 250_000_000, "egg_rare": 500_000_000}
        elif self == DifficultyMode.ORIGINAL:
            return {"rare_candy": 500_000_000, "mint": 100_000_000, "egg_normal": 1_000_000_000, "egg_uncommon": 2_500_000_000, "egg_rare": 4_000_000_000}
        else: # MEDIUM
            return {"rare_candy": 25_000_000, "mint": 5_000_000, "egg_normal": 30_000_000, "egg_uncommon": 75_000_000, "egg_rare": 150_000_000}

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
    BERRY_ORAN = "berry_oran"
    BERRY_GOLDEN = "berry_golden"
    MEGA_STONE = "mega_stone"
    EXPEDITION_PASS = "expedition_pass"
    POKE_FLUTE = "poke_flute"
    MASTER_BALL = "master_ball"
    MAP_FRAGMENT = "map_fragment"
    EXPEDITION_LICENSE = "expedition_license"
    EVERSTONE = "everstone"
    LUCKY_EGG = "lucky_egg"
    AMULET_COIN = "amulet_coin"
    LEFTOVERS = "leftovers"
    CHOICE_SCARF = "choice_scarf"
    WATER_STONE = "water_stone"
    FIRE_STONE = "fire_stone"
    THUNDER_STONE = "thunder_stone"
    LEAF_STONE = "leaf_stone"
    MOON_STONE = "moon_stone"
    SUN_STONE = "sun_stone"
    ICE_STONE = "ice_stone"
    SHINY_STONE = "shiny_stone"
    DUSK_STONE = "dusk_stone"
    DAWN_STONE = "dawn_stone"

    def price_for(self, difficulty: DifficultyMode = DifficultyMode.EASY) -> int:
        prices = {
            ItemKind.RARE_CANDY: difficulty.shop_prices.get("rare_candy", 5_000_000),
            ItemKind.MINT: difficulty.shop_prices.get("mint", 1_000_000),
            ItemKind.BERRY_ORAN: 1_000_000,
            ItemKind.BERRY_GOLDEN: 5_000_000,
            ItemKind.MEGA_STONE: 50_000_000,
            ItemKind.EXPEDITION_PASS: 15_000_000,
            ItemKind.POKE_FLUTE: 50_000_000,
            ItemKind.MASTER_BALL: 500_000_000,
            ItemKind.MAP_FRAGMENT: 10_000_000,
            ItemKind.EXPEDITION_LICENSE: 200_000_000,
            ItemKind.EVERSTONE: 500_000,
            ItemKind.LUCKY_EGG: 5_000_000,
            ItemKind.AMULET_COIN: 2_000_000,
            ItemKind.LEFTOVERS: 2_000_000,
            ItemKind.CHOICE_SCARF: 2_000_000,
            ItemKind.WATER_STONE: 50_000_000,
            ItemKind.FIRE_STONE: 50_000_000,
            ItemKind.THUNDER_STONE: 50_000_000,
            ItemKind.LEAF_STONE: 50_000_000,
            ItemKind.MOON_STONE: 50_000_000,
            ItemKind.SUN_STONE: 50_000_000,
            ItemKind.ICE_STONE: 50_000_000,
            ItemKind.SHINY_STONE: 50_000_000,
            ItemKind.DUSK_STONE: 50_000_000,
            ItemKind.DAWN_STONE: 50_000_000,
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
            ItemKind.BERRY_ORAN: "Oran Berry",
            ItemKind.BERRY_GOLDEN: "Golden Razz Berry",
            ItemKind.MEGA_STONE: "Mega Stone",
            ItemKind.EXPEDITION_PASS: "Expedition Pass",
            ItemKind.POKE_FLUTE: "Poké Flute",
            ItemKind.MASTER_BALL: "Master Ball",
            ItemKind.MAP_FRAGMENT: "Map",
            ItemKind.EXPEDITION_LICENSE: "Expedition License",
            ItemKind.EVERSTONE: "Everstone",
            ItemKind.LUCKY_EGG: "Lucky Egg",
            ItemKind.AMULET_COIN: "Amulet Coin",
            ItemKind.LEFTOVERS: "Leftovers",
            ItemKind.CHOICE_SCARF: "Choice Scarf",
            ItemKind.WATER_STONE: "Water Stone",
            ItemKind.FIRE_STONE: "Fire Stone",
            ItemKind.THUNDER_STONE: "Thunder Stone",
            ItemKind.LEAF_STONE: "Leaf Stone",
            ItemKind.MOON_STONE: "Moon Stone",
            ItemKind.SUN_STONE: "Sun Stone",
            ItemKind.ICE_STONE: "Ice Stone",
            ItemKind.SHINY_STONE: "Shiny Stone",
            ItemKind.DUSK_STONE: "Dusk Stone",
            ItemKind.DAWN_STONE: "Dawn Stone",
        }[self]

    @property
    def emoji(self) -> str:
        return {
            ItemKind.RARE_CANDY: "🍬",
            ItemKind.MINT: "🌿",
            ItemKind.BERRY_ORAN: "🫐",
            ItemKind.BERRY_GOLDEN: "🍇",
            ItemKind.MEGA_STONE: "🔮",
            ItemKind.EXPEDITION_PASS: "🎫",
            ItemKind.POKE_FLUTE: "🪈",
            ItemKind.MASTER_BALL: "🌟",
            ItemKind.MAP_FRAGMENT: "📜",
            ItemKind.EXPEDITION_LICENSE: "📜",
            ItemKind.EVERSTONE: "🪨",
            ItemKind.LUCKY_EGG: "🍀",
            ItemKind.AMULET_COIN: "🪙",
            ItemKind.LEFTOVERS: "🍎",
            ItemKind.CHOICE_SCARF: "🥊",
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
    held_item: Optional[str] = None

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
    "154": "Meganiumite",
    "160": "Feraligatrite",
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
    "302": "Sablenite",
    "303": "Mawilite",
    "306": "Aggronite",
    "308": "Medichamite",
    "310": "Manectite",
    "319": "Sharpedonite",
    "323": "Cameruptite",
    "334": "Altarianite",
    "354": "Banettite",
    "359": "Absolite",
    "362": "Glalitite",
    "373": "Salamencite",
    "376": "Metagrossite",
    "380": "Latiasite",
    "381": "Latiosite",
    "382": "Blue Orb",
    "383": "Red Orb",
    "384": "Meteorite",
    "428": "Lopunnite",
    "445": "Garchompite",
    "448": "Lucarionite",
    "460": "Abomasite",
    "475": "Galladite",
    "531": "Audinite",
    "719": "Diancite"
}
