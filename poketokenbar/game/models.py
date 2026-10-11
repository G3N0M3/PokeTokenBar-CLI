import math
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple, Any

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

    def graduation_total_for(self, difficulty=None) -> int:
        ranks = {
            Rarity.COMMON: 50_000_000,
            Rarity.UNCOMMON: 125_000_000,
            Rarity.RARE: 250_000_000,
            Rarity.LEGENDARY: 500_000_000,
            Rarity.MEGA: 1_000_000_000
        }
        return ranks[self]

    @classmethod
    def from_capture_rate(cls, capture_rate: int, is_legendary: bool = False, is_mythical: bool = False) -> 'Rarity':
        if is_legendary or is_mythical:
            return cls.LEGENDARY
        if capture_rate <= 45:
            return cls.RARE
        if capture_rate <= 120:
            return cls.UNCOMMON
        return cls.COMMON

class PokemonBalance:
    EGG_HATCH_THRESHOLD = 1_500_000
    EXPEDITION_VIRIDIAN = 5_000_000
    EXPEDITION_CERULEAN = 15_000_000
    EXPEDITION_SILVER = 30_000_000
    EXPEDITION_SPEAR_PILLAR = 100_000_000

    @staticmethod
    def phase_threshold(rarity: Rarity, total_forms: int, stage_index: int, difficulty=None) -> int:
        k = max(1, total_forms)
        i = stage_index + 1  # 1-based
        total = float(rarity.graduation_total_for())
        denom = float(k * (k + 1)) / 2.0
        return int(round(total * float(i) / denom))

class ItemKind(str, Enum):
    RARE_CANDY = "rare_candy"
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

    def price_for(self, difficulty=None) -> int:
        prices = {
            ItemKind.RARE_CANDY: 5_000_000,
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
        return self.price_for()

    @property
    def name_en(self) -> str:
        return {
            ItemKind.RARE_CANDY: "Rare Candy",
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

@dataclass
class ShareholderTier:
    rank: int
    name: str
    min_shares: int
    max_shares: Optional[int]
    range_label: str

SHAREHOLDER_TIERS: List[ShareholderTier] = [
    ShareholderTier(0, "None", 0, 0, "0 sh"),
    ShareholderTier(1, "Retail", 1, 10, "1-10 sh"),
    ShareholderTier(2, "Preferred", 11, 30, "11-30 sh"),
    ShareholderTier(3, "Strategic", 31, 60, "31-60 sh"),
    ShareholderTier(4, "Corporate", 61, 100, "61-100 sh"),
    ShareholderTier(5, "Venture", 101, 150, "101-150 sh"),
    ShareholderTier(6, "Principal", 151, 210, "151-210 sh"),
    ShareholderTier(7, "Majority", 211, 280, "211-280 sh"),
    ShareholderTier(8, "Director", 281, 360, "281-360 sh"),
    ShareholderTier(9, "Executive", 361, 450, "361-450 sh"),
    ShareholderTier(10, "Chairman", 451, None, "451+ sh"),
]

def get_shareholder_rank(shares: int) -> Tuple[int, str]:
    """Returns (rank_id, rank_name) for a given number of shares.
    Rank 0: None (0 sh)
    Rank 1: Retail (1-10 sh)
    Rank 2: Preferred (11-30 sh)
    Rank 3: Strategic (31-60 sh)
    Rank 4: Corporate (61-100 sh)
    Rank 5: Venture (101-150 sh)
    Rank 6: Principal (151-210 sh)
    Rank 7: Majority (211-280 sh)
    Rank 8: Director (281-360 sh)
    Rank 9: Executive (361-450 sh)
    Rank 10: Chairman (451+ sh)
    """
    if shares <= 0:
        return 0, "None"
    for tier in reversed(SHAREHOLDER_TIERS):
        if tier.rank == 0:
            continue
        if shares >= tier.min_shares:
            return tier.rank, tier.name
    return 0, "None"

CORPORATE_TIER_PERKS: Dict[str, Dict[int, str]] = {
    "silph": {
        0: "No expedition bonuses active",
        1: "+10% Expedition tokens & speed",
        2: "+15% Expedition tokens & speed",
        3: "+20% Expedition tokens & speed",
        4: "+25% Expedition tokens & speed",
        5: "+30% Expedition tokens & speed",
        6: "+35% Expedition tokens & speed",
        7: "+40% Expedition tokens & speed",
        8: "+45% Expedition tokens & speed",
        9: "+50% Expedition tokens & speed",
        10: "+60% Expedition tokens & speed",
    },
    "devon": {
        0: "No shop or egg discounts active",
        1: "-5% Discount on Shop & eggs",
        2: "-10% Discount on Shop & eggs",
        3: "-15% Discount on Shop & eggs",
        4: "-20% Discount on Shop & eggs",
        5: "-24% Discount on Shop & eggs",
        6: "-28% Discount on Shop & eggs",
        7: "-32% Discount on Shop & eggs",
        8: "-36% Discount on Shop & eggs",
        9: "-40% Discount on Shop & eggs",
        10: "-45% Discount on Shop & eggs",
    },
    "aether": {
        0: "No happiness protection or daily bonus",
        1: "1.5x decay shield; +3 daily hap.",
        2: "2.0x decay shield; +5 daily hap.",
        3: "2.5x decay shield; +8 daily hap.",
        4: "3.0x decay shield; +12 daily hap.",
        5: "3.5x decay shield; +16 daily hap.",
        6: "4.0x decay shield; +20 daily hap.",
        7: "4.5x decay shield; +25 daily hap.",
        8: "5.0x decay shield; +30 daily hap.",
        9: "5.5x decay shield; +36 daily hap.",
        10: "6.0x decay shield; +45 daily hap.",
    },
    "mauville": {
        0: "No casino payout bonus active",
        1: "+5% Casino minigame payout bonus",
        2: "+10% Casino minigame payout bonus",
        3: "+15% Casino minigame payout bonus",
        4: "+20% Casino minigame payout bonus",
        5: "+25% Casino minigame payout bonus",
        6: "+30% Casino minigame payout bonus",
        7: "+35% Casino minigame payout bonus",
        8: "+40% Casino minigame payout bonus",
        9: "+45% Casino minigame payout bonus",
        10: "+50% Casino minigame payout bonus",
    },
    "macro": {
        0: "No raid or auto-battle bonus active",
        1: "+10% Boss raid & battle tokens",
        2: "+20% Boss raid & battle tokens",
        3: "+30% Boss raid & battle tokens",
        4: "+40% Boss raid & battle tokens",
        5: "+50% Boss raid & battle tokens",
        6: "+60% Boss raid & battle tokens",
        7: "+70% Boss raid & battle tokens",
        8: "+80% Boss raid & battle tokens",
        9: "+90% Boss raid & battle tokens",
        10: "+100% Boss raid & battle tokens",
    },
    "viridian": {
        0: "No dividend bonus or clearance active",
        1: "+0.5% Div yield bonus",
        2: "+1.0% Div yield & covert ties",
        3: "+1.5% Div yield & covert ties",
        4: "+2.0% Div yield & Syndicate ties",
        5: "+2.5% Div yield & Syndicate ties",
        6: "+3.0% Div yield & Syndicate ties",
        7: "+3.5% Div yield & Syndicate ties",
        8: "+4.0% Div yield & Syndicate ties",
        9: "+4.5% Div yield & Syndicate ties",
        10: "+5.0% Div yield & Syndicate ties",
    },
}

CORPORATIONS: Dict[str, CorporateInfo] = {
    "silph": CorporateInfo(
        id="silph",
        name="Silph Co.",
        ticker="SILPH",
        share_price=10_000_000,
        base_dividend=0.025,
        perk_name="Silph Tech",
        perk_desc="+10% to +60% Expedition tokens & spd",
        catalyst_desc="Expedition completions boost research & tech"
    ),
    "devon": CorporateInfo(
        id="devon",
        name="Devon Corporation",
        ticker="DEVON",
        share_price=10_000_000,
        base_dividend=0.025,
        perk_name="Devon Commerce",
        perk_desc="-5% to -45% Shop & egg discount",
        catalyst_desc="Shopping & egg purchases boost retail volume"
    ),
    "aether": CorporateInfo(
        id="aether",
        name="Aether Foundation",
        ticker="AETHR",
        share_price=5_000_000,
        base_dividend=0.020,
        perk_name="Aether Sanctuary",
        perk_desc="1.5x-6.0x decay shield; +3-45 hap.",
        catalyst_desc="High happiness & shinies earn conservation grants"
    ),
    "mauville": CorporateInfo(
        id="mauville",
        name="Greater Mauville Holdings",
        ticker="MAUV",
        share_price=5_000_000,
        base_dividend=0.020,
        perk_name="Casino Royalty",
        perk_desc="+5% to +50% Casino minigame bonus",
        catalyst_desc="Casino house profits & player losses boost revenues"
    ),
    "macro": CorporateInfo(
        id="macro",
        name="Macro Cosmos",
        ticker="MACRO",
        share_price=20_000_000,
        base_dividend=0.030,
        perk_name="Dynamax Energy",
        perk_desc="+10% to +100% Tokens from Boss raids",
        catalyst_desc="Defeating Gym Bosses validates energy tech"
    ),
    "viridian": CorporateInfo(
        id="viridian",
        name="Viridian Global Logistics",
        ticker="VRDN",
        share_price=25_000_000,
        base_dividend=0.025,
        perk_name="Covert Logistics",
        perk_desc="+0.5% to +5.0% Div yield & covert ties",
        catalyst_desc="Nocturnal shipments & high market volume fuel growth"
    )
}

PATTERN_BULL_RALLY = "bull_rally"

BASE_PRICES: Dict[str, int] = {
    "silph": 10_000_000,
    "devon": 10_000_000,
    "aether": 5_000_000,
    "mauville": 5_000_000,
    "macro": 20_000_000,
    "viridian": 25_000_000,
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
    ],
    "viridian": [
        ("Viridian Logistics expands nocturnal freight runs between Saffron and Celadon.", +0.06),
        ("Warehouse security upgrade: All guards equipped with black berets and comms.", +0.04),
        ("Unscheduled bulk cargo arrived at Celadon basement depot after midnight.", +0.03),
        ("Rumors of subterranean tunnels beneath Viridian Gym dismissed as routine.", -0.04),
        ("Viridian Logistics CEO conducts annual shareholder meeting behind tinted glass.", -0.03),
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

class RocketRank(str, Enum):
    INFORMANT = "Informant"
    OPERATIVE = "Operative"
    SPECIAL_AGENT = "Special Agent"
    EXECUTIVE = "Executive"
    COMMANDER = "Commander"

SPECIAL_SPECIES: Dict[int, Dict[str, Any]] = {
    2001: {"name": "Armored Mewtwo", "rarity": Rarity.LEGENDARY, "base_id": 150},
    2002: {"name": "Porygon-Zero", "rarity": Rarity.RARE, "base_id": 137},
    2003: {"name": "Augmented Venusaur", "rarity": Rarity.RARE, "base_id": 3},
    2004: {"name": "Augmented Charizard", "rarity": Rarity.RARE, "base_id": 6},
    2005: {"name": "Augmented Blastoise", "rarity": Rarity.RARE, "base_id": 9},
    2006: {"name": "Augmented Tauros", "rarity": Rarity.UNCOMMON, "base_id": 128},
    2007: {"name": "Augmented Dragonite", "rarity": Rarity.RARE, "base_id": 149},
    2008: {"name": "Augmented Alakazam", "rarity": Rarity.RARE, "base_id": 65},
    2010: {"name": "MissingNo.", "rarity": Rarity.RARE, "base_id": 137},
    2011: {"name": "Venustoise", "rarity": Rarity.RARE, "base_id": 3},
    2012: {"name": "Prototype Chimera-001", "rarity": Rarity.LEGENDARY, "base_id": 150},
    2013: {"name": "Cyber-Zapdos", "rarity": Rarity.LEGENDARY, "base_id": 145},
    2014: {"name": "Apex Vanguard Mon-Omega", "rarity": Rarity.LEGENDARY, "base_id": 150},
}

@dataclass
class RocketOperation:
    id: str
    code_name: str
    title: str
    briefing: str
    target_description: str
    target_tokens: int
    reward_tokens: int
    reward_rank: RocketRank
    intel_unlocked: str
    is_boss: bool = False
    boss_name: Optional[str] = None
    boss_hp: int = 0

@dataclass
class SyndicateIntelEntry:
    id: str
    title: str
    date: str
    content: str

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
    ditto_disguise: Optional[int] = None
    ditto_revealed: bool = False
    is_mega: bool = False
    mega_form: Optional[str] = None
    happiness: int = 100
    held_item: Optional[str] = None
    is_graduated: bool = False

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

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Executive Resort Area Luxury Suite
# ---------------------------------------------------------------------------
LUXURY_WEALTH_THRESHOLD = 100_000_000_000  # 100.0 Billion tokens (bank + holding)
LUXURY_VIP_FEE = 500_000_000  # 500.0 Million tokens VIP broker fee
LUXURY_DEED_COST = 1_000_000_000_000  # 1.0 Trillion tokens

# Backward-compatible aliases
PENTHOUSE_WEALTH_THRESHOLD = LUXURY_WEALTH_THRESHOLD
PENTHOUSE_VIP_FEE = LUXURY_VIP_FEE
PENTHOUSE_DEED_COST = LUXURY_DEED_COST
VILLA_DEED_COST = LUXURY_DEED_COST

LUXURY_FACILITIES = {
    "nursery": {
        "name": "Automated Cryo-Nursery",
        "icon": "🥚",
        "levels": {
            1: {"name": "Auto-Incubator", "cost": 500_000_000_000, "desc": "Auto-incubates 1 queued nursery egg in background"},
            2: {"name": "Tri-Incubator", "cost": 1_500_000_000_000, "desc": "Incubates 3 queued eggs in parallel"},
            3: {"name": "Quantum Matrix", "cost": 4_000_000_000_000, "desc": "Incubates ALL queued eggs in parallel (2x spd)"},
        }
    },
    "springs": {
        "name": "Hot Springs & Berry Grove",
        "icon": "💧",
        "levels": {
            1: {"name": "Automated Feeding", "cost": 300_000_000_000, "desc": "Auto-feeds companion daily from berry bag"},
            2: {"name": "Eternal Warmth", "cost": 1_000_000_000_000, "desc": "Companion happiness decay rate halved"},
            3: {"name": "Sacred Springs", "cost": 3_000_000_000_000, "desc": "Immune to decay; +50% coding EXP boost"},
        }
    },
    "trading_desk": {
        "name": "Quantum Trading Terminal",
        "icon": "📊",
        "levels": {
            1: {"name": "Satellite Telemetry", "cost": 500_000_000_000, "desc": "Displays live stock directional bias & duration"},
            2: {"name": "Auto-Compounder", "cost": 2_000_000_000_000, "desc": "Auto-sweeps daily stock dividends into checking"},
            3: {"name": "Whale Catalyst", "cost": 5_000_000_000_000, "desc": "Unlock 'catalyst <corp>' to trigger Bull Rally"},
        }
    },
    "chromatic_lab": {
        "name": "Chromatic Resonator",
        "icon": "✨",
        "levels": {
            1: {"name": "Shiny Transmuter", "cost": 10_000_000_000_000, "desc": "Use 'transmute <idx>' to convert companion to Shiny"},
        }
    }
}
PENTHOUSE_FACILITIES = LUXURY_FACILITIES
VILLA_FACILITIES = LUXURY_FACILITIES
LUXURY_WINGS = LUXURY_FACILITIES
PENTHOUSE_WINGS = LUXURY_FACILITIES
VILLA_WINGS = LUXURY_FACILITIES

LUXURY_DECOR = {
    "piano": {
        "name": "Grand Concert Piano",
        "cost": 300_000_000_000,
        "icon": "🎹",
        "perk": "Harmonic Melodies (+10 Hap)",
        "desc": "Polished ebony grand piano. Play melodies to cheer companion."
    },
    "chandelier": {
        "name": "Diamond Chandelier",
        "cost": 500_000_000_000,
        "icon": "💎",
        "perk": "Prismatic Aura (+5% Exped)",
        "desc": "Kalosian crystal chandelier boosting expedition token yields."
    },
    "statue": {
        "name": "Golden Arceus Statue",
        "cost": 1_000_000_000_000,
        "icon": "🗽",
        "perk": "Divine Aura (+10% Raids)",
        "desc": "Solid gold effigy honoring the Alpha Pokémon's creation myth."
    },
    "hologram": {
        "name": "Master Core Hologram",
        "cost": 1_500_000_000_000,
        "icon": "🔮",
        "perk": "Quantum Matrix (+5% Casino)",
        "desc": "3D wireframe hologram of Mon-Omega boosting casino payouts."
    },
    "fountain": {
        "name": "Prism Spring Fountain",
        "cost": 2_000_000_000_000,
        "icon": "⛲",
        "perk": "Mineral Waters (100% Hap)",
        "desc": "Rainbow marble fountain. Pure spring restores happiness to max."
    },
    "throne": {
        "name": "Sovereign Tycoon Throne",
        "cost": 3_000_000_000_000,
        "icon": "👑",
        "perk": "Corporate Rule (+10% Divs)",
        "desc": "Velvet & platinum throne conferring supreme corporate authority."
    },
    "watch": {
        "name": "Baron's 24K Sovereign Watch",
        "cost": 0,
        "icon": "⌚",
        "perk": "The Velvet Sting Trophy (+15% VIP)",
        "desc": "Solid gold pocket watch seized from the bankrupted Baron Salvatore Croix."
    },
}
PENTHOUSE_DECOR = LUXURY_DECOR
VILLA_DECOR = LUXURY_DECOR

POKER_VIP_TRIGGER_BET = 100_000_000_000_000  # 100.0T tokens
POKER_VIP_MIN_BET = 10_000_000_000_000       # 10.0T tokens
POKER_VIP_MULTIPLIERS = {
    "Royal Flush": 100,
    "Straight Flush": 25,
    "Four of a Kind": 12,
    "Full House": 6,
    "Flush": 5,
    "Straight": 4,
    "Three of a Kind": 3,
    "Two Pair": 2,
    "One Pair": 2,
    "High Card": 2,
}

VELVET_PATRONS: List[str] = [
    "Duchess Eleanor",
    "Gentleman Walter",
    "Madame Vivienne",
]

VELVET_MARKS: List[str] = [
    "Financier Vance",
    "Viktor Rostov",
    "Countess Beverly",
    "Lord Sterling",
    "Oligarch Thorne",
    "Corinne Vane",
]

VELVET_STING_CHAPTERS: Dict[str, Dict[str, Any]] = {
    "1": {
        "title": "Operation Clean Slate: The Syndicate Recruitment",
        "location": "The Velvet Salon // Private Ante-Chamber",
        "speaker": "Madame Vivienne",
        "opponent": "VIP Patrons [Trial]",
        "dialogue": [
            "\"Welcome to The Velvet Salon, Trainer. That hundred-trillion wager on the main floor certainly turned heads.",
            "",
            "Allow me to introduce our circle: Duchess Eleanor, Gentleman Walter, and myself. To the outside world, we are mere high-society dilettantes enjoying private card games.",
            "",
            "In truth, we are an undercover syndicate. Our target is Baron Salvatore Croix—a ruthless oligarch who has spent decades strip-mining sacred Pokémon habitats, foreclosing on non-profit daycares, and laundering his ill-gotten quadrillions through private poker tables.",
            "",
            "We intend to ruin him legally at the green felt. You've proven your incredible talent by winning 10 hands and securing 500.0T tokens at our felt. You are now officially inducted into our inner circle! Type 'sting' to proceed with our master plan!\""
        ],
        "tactical_orders": [
            "• Win a total of 10 hands at The Velvet Salon table ('table vip').",
            "• Accumulate at least 500.0T tokens in total VIP table winnings."
        ],
        "req_wins": 10,
        "req_winnings": 500_000_000_000_000,
    },
    "2": {
        "title": "Operation Paper Trail: Tracing the Shadow Ledgers",
        "location": "Silph-Devon Clearing Suite // Clandestine Wire",
        "speaker": "Duchess Eleanor",
        "opponent": "Financier Vance [Money Runner]",
        "dialogue": [
            "\"Splendid performance at the tables, darling. Your nerves are as steady as diamond.",
            "",
            "Our wiretaps have confirmed that Croix routes his laundering through high-roller pots, disguising illegal payouts as casino earnings.",
            "",
            "Croix's offshore wire runner, Financier Vance, has just taken a seat at the table. To crack his encrypted transaction telemetry, we need a massive token surge on the felt. Take down a single pot worth at least 25.0T tokens from him.",
            "",
            "Once that transaction clears our private terminal, Vivienne's analysts can pinpoint Croix's primary liquidity reserve. Do not disappoint us!\""
        ],
        "tactical_orders": [
            "• Win a single poker pot of at least 25.0T tokens against Financier Vance at the VIP table.",
            "• Intercept Croix's offshore transaction telemetry."
        ],
        "req_pot": 25_000_000_000_000,
    },
    "3": {
        "title": "[MINI-BOSS 1] Breaking the Bouncer: Viktor Rostov",
        "location": "VIP High-Limit Antechamber // The Heavy Velvet Curtain",
        "speaker": "Gentleman Walter",
        "opponent": "Viktor Rostov [Enforcer]",
        "is_boss": True,
        "boss_max_stack": 50_000_000_000_000,
        "dialogue": [
            "\"Keep your voice down, kid. We have trouble.",
            "",
            "Croix's chief of private security—Viktor 'The Bull' Rostov—noticed our telemetry spike. The brute just barged into the salon.",
            "",
            "He claims he's here to 'inspect the action', but he brought a 50.0T war chest to bully everyone off the felt and shut our sting down before it starts.",
            "",
            "We can't brawl here without blowing our cover. Sit across from him at the table ('table vip') and strip him of every single token in his stack!\""
        ],
        "tactical_orders": [
            "• Face Viktor Rostov at The Velvet Salon felt ('table vip').",
            "• Deplete Viktor's 50.0T security war chest to 0 tokens."
        ],
    },
    "4": {
        "title": "Operation Liquid Freeze: The Offshore Intercept",
        "location": "Vermilion Deep Anchorage // Luxury Cruiser M.S. Croesus",
        "speaker": "Madame Vivienne",
        "opponent": "Countess Beverly [Bondholder]",
        "dialogue": [
            "\"Viktor slunk out with his tail between his legs. Exquisite card play, Trainer!",
            "",
            "While you had him occupied, our hackers traced his communications directly to the M.S. Croesus docked in Vermilion Harbor. That is where Croix parks his bearer bonds.",
            "",
            "We are filing an emergency judicial freeze with the International Police, but the court demands 50.0T tokens in escrow collateral to seal the injunction.",
            "",
            "Countess Beverly, one of Croix's key luxury syndicate bondholders, is holding court at the felt. Accumulate at least 50.0T tokens in total VIP winnings from her to fund our legal strike. Move quickly before Croix catches wind!\""
        ],
        "tactical_orders": [
            "• Accumulate 50.0T tokens in total VIP table winnings against Countess Beverly.",
            "• Collateralize the legal freeze on Croix's luxury yacht accounts."
        ],
        "req_winnings": 50_000_000_000_000,
    },
    "5": {
        "title": "Operation Counter-Bluff: Poisoning the Well",
        "location": "The Grand Velvet Salon Felt // Private Alcove",
        "speaker": "Gentleman Walter",
        "opponent": "Lord Sterling [Syndicator]",
        "dialogue": [
            "\"Croix's financial analysts are panicking, kid. They realize their yacht accounts are locked.",
            "",
            "Their only option now is to liquidate secondary assets and pour liquidity directly into Celadon's high-roller tables to recover their capital. Croix's principal syndicator, Lord Sterling, has taken the seat across from you.",
            "",
            "We need to establish total psychological dominance at this felt. Walter wants to see true mastery of the cards: win 3 hands with Two Pair or better against Lord Sterling.",
            "",
            "Show them that our salon table is an iron fortress where loose gamblers come to die!\""
        ],
        "tactical_orders": [
            "• Win 3 hands at the VIP table showing Two Pair or higher against Lord Sterling.",
            "• Solidify syndicate dominance before the main event."
        ],
        "req_ranked_wins": 3,
    },
    "6": {
        "title": "Operation Golden Lure: The Whale's Invitation",
        "location": "Celadon Penthouse Skylounge // Neon Horizon",
        "speaker": "Duchess Eleanor",
        "opponent": "Oligarch Thorne [Consortium Partner]",
        "dialogue": [
            "\"The trap is set, darling. Croix's pride is his greatest fatal flaw.",
            "",
            "He considers himself the undisputed emperor of high-stakes gambling. If he sees an upstart holding astronomical wealth at this table, he won't be able to resist sitting down to take it.",
            "",
            "Croix's most notorious consortium partner, Oligarch Thorne, is at the table. Flash the ultimate whale lure: take down a massive pot of at least 100.0T tokens against him, or hold at least 250.0T in your liquid vault.",
            "",
            "Once Croix sees that magnitude of capital on our felt, he will demand a private heads-up match in person!\""
        ],
        "tactical_orders": [
            "• Win a single pot >= 100.0T tokens against Oligarch Thorne OR hold >= 250.0T spendable tokens.",
            "• Bait Baron Salvatore Croix into entering the Velvet Salon."
        ],
        "req_whale_pot": 100_000_000_000_000,
        "req_whale_balance": 250_000_000_000_000,
    },
    "7": {
        "title": "[MINI-BOSS 2] The Auditor's Gambit: Corinne Vane",
        "location": "Executive Salon Suite // Private Baccarat Vault",
        "speaker": "Madame Vivienne",
        "opponent": "Corinne Vane [Chief Auditor]",
        "is_boss": True,
        "boss_max_stack": 100_000_000_000_000,
        "dialogue": [
            "\"Croix took the bait! But the cautious old vulture isn't stepping in blind.",
            "",
            "He has dispatched his chief financial officer and actuarial savant: Corinne 'The Ledger' Vane. She has calculated the odds on every card dealt in this casino since 1998.",
            "",
            "She sits down with a 100.0T corporate treasury stack, determined to dismantle your bankroll with cold mathematical precision.",
            "",
            "Take the table ('table vip'). Break her math and strip her 100.0T stack to zero!\""
        ],
        "tactical_orders": [
            "• Challenge Corinne Vane at The Velvet Salon felt ('table vip').",
            "• Drain Corinne's 100.0T corporate treasury stack to 0 tokens."
        ],
    },
    "8": {
        "title": "[BOSS] First Blood: The Baron Takes the Felt",
        "location": "The Inner Velvet Sanctum // Gilded Chandeliers",
        "speaker": "Gentleman Walter",
        "opponent": "Baron Salvatore Croix [Tycoon]",
        "is_boss": True,
        "boss_max_stack": 150_000_000_000_000,
        "dialogue": [
            "\"Look who finally decided to show his face. Smelling of cigars and arrogance.",
            "",
            "Baron Salvatore Croix has stepped through the velvet curtain. He sweeps his mink coat aside, slips on his gold signet ring, and glares across the felt at you.",
            "",
            "'So you're the little upstart whose lucky streak has embarrassed my staff? Let us see how your amateur nerve holds against true capital.'",
            "",
            "He tosses 150.0T in platinum plaques onto the table. This is it, kid. Deal in ('table vip') and take first blood!\""
        ],
        "tactical_orders": [
            "• Face Baron Salvatore Croix at The Velvet Salon felt ('table vip').",
            "• Deplete his 150.0T personal buy-in to 0 tokens."
        ],
    },
    "9": {
        "title": "[BOSS] Cornered Vulture: The Desperate Liquidation",
        "location": "The Velvet Salon // Midnight Shadows",
        "speaker": "Duchess Eleanor",
        "opponent": "Baron Salvatore Croix [Tycoon]",
        "is_boss": True,
        "boss_max_stack": 250_000_000_000_000,
        "dialogue": [
            "\"The Baron's composure has completely shattered! He is sweating through his tailored silk vest.",
            "",
            "Rather than admitting defeat, his wounded pride has driven him to utter madness. He just authorized an emergency wire from his private Swiss bank accounts.",
            "",
            "He reloads the felt with an astronomical 250.0T tokens, snarling that he will double down on every street until he crushes you.",
            "",
            "Stay composed, darling. Let his fury work against him. Step back to the felt ('table vip') and strip his emergency reserves!\""
        ],
        "tactical_orders": [
            "• Re-engage Baron Croix at The Velvet Salon felt ('table vip').",
            "• Strip his 250.0T emergency liquidity reserves down to 0 tokens."
        ],
    },
    "10": {
        "title": "[CAMPAIGN CLIMAX] Velvet Guillotine: Total Insolvency",
        "location": "Sealed High-Roller Vault // The Final Felt",
        "speaker": "Madame Vivienne & The Syndicate",
        "opponent": "Baron Salvatore Croix [Tycoon]",
        "is_boss": True,
        "boss_max_stack": 350_000_000_000_000,
        "dialogue": [
            "\"The moment of ultimate reckoning has arrived. All exits to the casino are locked.",
            "",
            "Baron Salvatore Croix is trembling, his hands clutching a gold-embossed leather folio. Inside are the master property deeds and corporate charter to Croix Consolidated Resources—worth 350.0T tokens.",
            "",
            "'All of it,' he wheezes, his eyes bloodshot. 'I wager my entire empire against yours. One final heads-up battle to the death.'",
            "",
            "The dealer shuffles the high-roller deck. The syndicate stands behind your chair. Deliver the final blow, Trainer! Bankrupt him completely!\""
        ],
        "tactical_orders": [
            "• Enter the Climax Showdown at The Velvet Salon felt ('table vip').",
            "• Drain Baron Croix's final 350.0T master empire stack to exactly 0 tokens!"
        ],
    },
    "epilogue": {
        "title": "Campaign Epilogue: The Dawn of the Card Shark",
        "location": "The Velvet Salon // Sunrise Over Celadon",
        "speaker": "Madame Vivienne, Walter, Eleanor & Agent Looker",
        "dialogue": [
            "The final card hits the felt. Baron Salvatore Croix stares blankly at the board as his empire dissolves into nothingness.",
            "",
            "The heavy mahogany doors swing open. Detective Looker of the International Police steps forward with a team of officers, flashing a federal warrant.",
            "",
            "\"Salvatore Croix,\" Looker announces. \"Without your offshore liquidity and bribery fund, your shell network has collapsed. You are under arrest for systemic financial fraud, illegal land seizures, and racketeering.\"",
            "",
            "As Croix is escorted away in cuffs, Madame Vivienne uncorks a vintage Roseli champagne. Glasses clink across the table. Walter grins warmly, and Duchess Eleanor presents you with the Baron's solid gold pocket watch.",
            "",
            "\"You didn't just win a poker game, Trainer,\" Vivienne says with a radiant smile. \"You liberated an entire region from a tyrant's grip. The Velvet Salon will forever honor you as our Sovereign Card Shark.\""
        ],
        "tactical_orders": [
            "• Baron Salvatore Croix completely bankrupted and incarcerated.",
            "• Seized treasury bounty (+100.0T tokens) credited to your vault.",
            "• Title '♠️ Master of the Velvet Sting' & 'Baron's 24K Sovereign Watch' awarded."
        ],
    },
}

