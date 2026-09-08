import math
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple

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
    EXP_SHARE = "exp_share"
    SOOTHE_BELL = "soothe_bell"
    SCOPE_LENS = "scope_lens"
    LIFE_ORB = "life_orb"
    CHOICE_BAND = "choice_band"
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
    CHOICE_SPECS = "choice_specs"
    FOCUS_SASH = "focus_sash"
    ROCKY_HELMET = "rocky_helmet"
    ASSAULT_VEST = "assault_vest"
    HEAVY_BOOTS = "heavy_boots"
    COMPASS_OF_DEEP = "compass_of_deep"
    REVITALIZING_TONIC = "revitalizing_tonic"
    SACRED_ASH = "sacred_ash"
    WARP_WHISTLE = "warp_whistle"
    EXPEDITION_ENERGY_TONIC = "expedition_energy_tonic"
    EXPEDITION_INSURANCE = "expedition_insurance"
    ROCKET_RADAR = "rocket_radar"
    METAL_COAT = "metal_coat"
    KINGS_ROCK = "kings_rock"
    DRAGON_SCALE = "dragon_scale"
    UPGRADE = "upgrade"
    DUBIOUS_DISC = "dubious_disc"
    PROTECTOR = "protector"
    ELECTIRIZER = "electirizer"
    MAGMARIZER = "magmarizer"
    REAPER_CLOTH = "reaper_cloth"
    PRISM_SCALE = "prism_scale"
    FAKE_RARE_CANDY = "fake_rare_candy"
    FAKE_MASTER_BALL = "fake_master_ball"
    FAKE_THUNDER_STONE = "fake_thunder_stone"
    FAKE_WATER_STONE = "fake_water_stone"
    FAKE_FIRE_STONE = "fake_fire_stone"
    FAKE_ANCIENT_MAP = "fake_ancient_map"
    FAKE_GOLD_NUGGET = "fake_gold_nugget"
    FAKE_EXP_SHARE = "fake_exp_share"
    FAKE_SOOTHE_BELL = "fake_soothe_bell"
    FAKE_SCOPE_LENS = "fake_scope_lens"
    FAKE_FOCUS_SASH = "fake_focus_sash"
    FAKE_MEGA_STONE = "fake_mega_stone"

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
            ItemKind.EXP_SHARE: 25_000_000,
            ItemKind.SOOTHE_BELL: 20_000_000,
            ItemKind.SCOPE_LENS: 30_000_000,
            ItemKind.LIFE_ORB: 25_000_000,
            ItemKind.CHOICE_BAND: 20_000_000,
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
            ItemKind.CHOICE_SPECS: 20_000_000,
            ItemKind.FOCUS_SASH: 22_000_000,
            ItemKind.ROCKY_HELMET: 20_000_000,
            ItemKind.ASSAULT_VEST: 22_000_000,
            ItemKind.HEAVY_BOOTS: 18_000_000,
            ItemKind.COMPASS_OF_DEEP: 25_000_000,
            ItemKind.REVITALIZING_TONIC: 8_000_000,
            ItemKind.SACRED_ASH: 30_000_000,
            ItemKind.WARP_WHISTLE: 30_000_000,
            ItemKind.EXPEDITION_ENERGY_TONIC: 18_000_000,
            ItemKind.EXPEDITION_INSURANCE: 20_000_000,
            ItemKind.ROCKET_RADAR: 25_000_000,
            ItemKind.METAL_COAT: 35_000_000,
            ItemKind.KINGS_ROCK: 35_000_000,
            ItemKind.DRAGON_SCALE: 35_000_000,
            ItemKind.UPGRADE: 30_000_000,
            ItemKind.DUBIOUS_DISC: 35_000_000,
            ItemKind.PROTECTOR: 30_000_000,
            ItemKind.ELECTIRIZER: 35_000_000,
            ItemKind.MAGMARIZER: 35_000_000,
            ItemKind.REAPER_CLOTH: 35_000_000,
            ItemKind.PRISM_SCALE: 35_000_000,
            ItemKind.FAKE_RARE_CANDY: 1,
            ItemKind.FAKE_MASTER_BALL: 1,
            ItemKind.FAKE_THUNDER_STONE: 1,
            ItemKind.FAKE_WATER_STONE: 1,
            ItemKind.FAKE_FIRE_STONE: 1,
            ItemKind.FAKE_ANCIENT_MAP: 1,
            ItemKind.FAKE_GOLD_NUGGET: 1,
            ItemKind.FAKE_EXP_SHARE: 1,
            ItemKind.FAKE_SOOTHE_BELL: 1,
            ItemKind.FAKE_SCOPE_LENS: 1,
            ItemKind.FAKE_FOCUS_SASH: 1,
            ItemKind.FAKE_MEGA_STONE: 1,
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
            ItemKind.EXP_SHARE: "Exp. Share",
            ItemKind.SOOTHE_BELL: "Soothe Bell",
            ItemKind.SCOPE_LENS: "Scope Lens",
            ItemKind.LIFE_ORB: "Life Orb",
            ItemKind.CHOICE_BAND: "Choice Band",
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
            ItemKind.CHOICE_SPECS: "Choice Specs",
            ItemKind.FOCUS_SASH: "Focus Sash",
            ItemKind.ROCKY_HELMET: "Rocky Helmet",
            ItemKind.ASSAULT_VEST: "Assault Vest",
            ItemKind.HEAVY_BOOTS: "Heavy Boots",
            ItemKind.COMPASS_OF_DEEP: "Compass of Deep",
            ItemKind.REVITALIZING_TONIC: "Revitalizing Tonic",
            ItemKind.SACRED_ASH: "Sacred Ash",
            ItemKind.WARP_WHISTLE: "Warp Whistle",
            ItemKind.EXPEDITION_ENERGY_TONIC: "Energy Tonic (All)",
            ItemKind.EXPEDITION_INSURANCE: "Exped. Insurance",
            ItemKind.ROCKET_RADAR: "Rocket Radar",
            ItemKind.METAL_COAT: "Metal Coat",
            ItemKind.KINGS_ROCK: "King's Rock",
            ItemKind.DRAGON_SCALE: "Dragon Scale",
            ItemKind.UPGRADE: "Upgrade",
            ItemKind.DUBIOUS_DISC: "Dubious Disc",
            ItemKind.PROTECTOR: "Protector",
            ItemKind.ELECTIRIZER: "Electirizer",
            ItemKind.MAGMARIZER: "Magmarizer",
            ItemKind.REAPER_CLOTH: "Reaper Cloth",
            ItemKind.PRISM_SCALE: "Prism Scale",
            ItemKind.FAKE_RARE_CANDY: '"Rare Candy"',
            ItemKind.FAKE_MASTER_BALL: '"Master Ball"',
            ItemKind.FAKE_THUNDER_STONE: '"Thunder Stone"',
            ItemKind.FAKE_WATER_STONE: '"Water Stone"',
            ItemKind.FAKE_FIRE_STONE: '"Fire Stone"',
            ItemKind.FAKE_ANCIENT_MAP: '"Ancient Map"',
            ItemKind.FAKE_GOLD_NUGGET: '"Gold Nugget"',
            ItemKind.FAKE_EXP_SHARE: '"Exp. Share"',
            ItemKind.FAKE_SOOTHE_BELL: '"Soothe Bell"',
            ItemKind.FAKE_SCOPE_LENS: '"Scope Lens"',
            ItemKind.FAKE_FOCUS_SASH: '"Focus Sash"',
            ItemKind.FAKE_MEGA_STONE: '"Charizardite"',
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
            ItemKind.EXP_SHARE: "🎒",
            ItemKind.SOOTHE_BELL: "🔔",
            ItemKind.SCOPE_LENS: "🔍",
            ItemKind.LIFE_ORB: "🔮",
            ItemKind.CHOICE_BAND: "🥊",
            ItemKind.WATER_STONE: "💎",
            ItemKind.FIRE_STONE: "💎",
            ItemKind.THUNDER_STONE: "💎",
            ItemKind.LEAF_STONE: "💎",
            ItemKind.MOON_STONE: "💎",
            ItemKind.SUN_STONE: "💎",
            ItemKind.ICE_STONE: "💎",
            ItemKind.SHINY_STONE: "💎",
            ItemKind.DUSK_STONE: "💎",
            ItemKind.DAWN_STONE: "💎",
            ItemKind.CHOICE_SPECS: "👓",
            ItemKind.FOCUS_SASH: "🎗️",
            ItemKind.ROCKY_HELMET: "⛑️",
            ItemKind.ASSAULT_VEST: "🦺",
            ItemKind.HEAVY_BOOTS: "🥾",
            ItemKind.COMPASS_OF_DEEP: "🧭",
            ItemKind.REVITALIZING_TONIC: "⚗️",
            ItemKind.SACRED_ASH: "🏺",
            ItemKind.WARP_WHISTLE: "🌬️",
            ItemKind.EXPEDITION_ENERGY_TONIC: "⚡",
            ItemKind.EXPEDITION_INSURANCE: "📜",
            ItemKind.ROCKET_RADAR: "📡",
            ItemKind.METAL_COAT: "⚙️",
            ItemKind.KINGS_ROCK: "👑",
            ItemKind.DRAGON_SCALE: "🐉",
            ItemKind.UPGRADE: "💾",
            ItemKind.DUBIOUS_DISC: "💿",
            ItemKind.PROTECTOR: "🛡️",
            ItemKind.ELECTIRIZER: "🔌",
            ItemKind.MAGMARIZER: "🌋",
            ItemKind.REAPER_CLOTH: "👻",
            ItemKind.PRISM_SCALE: "✨",
            ItemKind.FAKE_RARE_CANDY: "🍬",
            ItemKind.FAKE_MASTER_BALL: "🌟",
            ItemKind.FAKE_THUNDER_STONE: "⚡",
            ItemKind.FAKE_WATER_STONE: "💧",
            ItemKind.FAKE_FIRE_STONE: "🔥",
            ItemKind.FAKE_ANCIENT_MAP: "📜",
            ItemKind.FAKE_GOLD_NUGGET: "🪙",
            ItemKind.FAKE_EXP_SHARE: "🎒",
            ItemKind.FAKE_SOOTHE_BELL: "🔔",
            ItemKind.FAKE_SCOPE_LENS: "🔍",
            ItemKind.FAKE_FOCUS_SASH: "🎗️",
            ItemKind.FAKE_MEGA_STONE: "🔮",
        }.get(self, "📦")

@dataclass
class CorporateInfo:
    id: str
    name: str
    ticker: str
    share_price: int
    base_dividend: float
    perk_name: str
    perk_desc: str
    catalyst_desc: str

CORPORATIONS: Dict[str, CorporateInfo] = {
    "silph": CorporateInfo(
        id="silph",
        name="Silph Co.",
        ticker="SILPH",
        share_price=10_000_000,
        base_dividend=0.025,
        perk_name="Silph Tech",
        perk_desc="+15% Expedition tokens & speed",
        catalyst_desc="Expedition completions boost research & tech"
    ),
    "devon": CorporateInfo(
        id="devon",
        name="Devon Corporation",
        ticker="DEVON",
        share_price=10_000_000,
        base_dividend=0.025,
        perk_name="Devon Commerce",
        perk_desc="-10% Discount on Shop items & eggs",
        catalyst_desc="Shopping & egg purchases boost retail volume"
    ),
    "aether": CorporateInfo(
        id="aether",
        name="Aether Foundation",
        ticker="AETHR",
        share_price=5_000_000,
        base_dividend=0.020,
        perk_name="Aether Sanctuary",
        perk_desc="Halves happiness decay; +5 daily hap.",
        catalyst_desc="High happiness & shinies earn conservation grants"
    ),
    "mauville": CorporateInfo(
        id="mauville",
        name="Greater Mauville Holdings",
        ticker="MAUV",
        share_price=5_000_000,
        base_dividend=0.020,
        perk_name="Casino Royalty",
        perk_desc="+10% Payout bonus on all minigames",
        catalyst_desc="Casino house profits & player losses boost revenues"
    ),
    "macro": CorporateInfo(
        id="macro",
        name="Macro Cosmos",
        ticker="MACRO",
        share_price=20_000_000,
        base_dividend=0.030,
        perk_name="Dynamax Energy",
        perk_desc="+20% Tokens from Boss raids & Red battle",
        catalyst_desc="Defeating Gym Bosses & Red validates energy tech"
    )
}

CORPORATE_LORE_EVENTS: Dict[str, List[Tuple[str, float]]] = {
    "silph": [
        ("Silph Co. patents next-gen Poké Ball alloy in Saffron City!", +0.06),
        ("Expedition surveys return rare geological samples to Silph labs.", +0.04),
        ("Silph electronics division beats quarterly revenue forecasts.", +0.03),
        ("Team Rocket disruption reported near Silph Saffron offices.", -0.05),
        ("Global supply chain shortage delays Silph component shipments.", -0.03),
    ],
    "devon": [
        ("Devon geologists unearth rich evolutionary stone vein in Hoenn!", +0.06),
        ("Devon Corporation announces surging egg incubator sales.", +0.04),
        ("Rustboro commerce chamber awards Devon annual trade trophy.", +0.03),
        ("Oceanic shipping delay halts Devon maritime export fleet.", -0.04),
        ("Mining machinery malfunction temporarily stalls Devon quarry.", -0.03),
    ],
    "aether": [
        ("Alola Pokémon Sanctuary receives major conservation grant!", +0.05),
        ("Aether Foundation rehabilitation clinic celebrates zero attrition.", +0.04),
        ("Rare species census reveals thriving companion populations.", +0.03),
        ("Severe tropical squall causes minor structural damage at Paradise.", -0.04),
        ("Conservation foundation overhead costs rise slightly this quarter.", -0.02),
    ],
    "mauville": [
        ("Mauville Game Corner reports record tourist slot revenue!", +0.06),
        ("Greater Mauville Holdings opens sleek new entertainment arcade.", +0.04),
        ("Casino VIP poker tournament generates booming token turnover.", +0.03),
        ("High-roller cleans out Mauville Blackjack vault with winning run.", -0.05),
        ("Mauville city utility tax assessment comes in above expectations.", -0.03),
    ],
    "macro": [
        ("Macro Cosmos lands Galar national power grid expansion deal!", +0.07),
        ("Macro energy labs report breakthrough in power containment.", +0.05),
        ("Wyndon Stadium sponsorship agreement yields record corporate fees.", +0.03),
        ("Dynamax grid power surge prompts costly routine maintenance.", -0.05),
        ("Galar environmental review requests Macro energy audit.", -0.03),
    ]
}

MARKET_HEADLINES: Dict[str, List[str]] = {
    "bullish": [
        "📈 INDICES SURGE: Heavy developer coding volume sparks rally!",
        "🚀 BULL MARKET: Developer streak fuels massive investor optimism!",
        "✨ MARKET MOMENTUM: High token burn powers broad corporate gains!"
    ],
    "steady": [
        "📊 MARKET BALANCED: Indices hold steady across all sectors.",
        "⚖️ TRADING RANGE: Steady developer coding keeps market anchored.",
        "🏢 CORPORATE OUTLOOK: Mixed trading as investors weigh quarterly yields."
    ],
    "bearish": [
        "📉 MARKET DRAG: Quiet coding session softens trading volumes.",
        "⚠️ CONSOLIDATION: Sluggish token burn tempers investor appetite.",
        "🌧️ POKÉMON EXCHANGE: Cautious trading as markets await catalyst."
    ]
}

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
