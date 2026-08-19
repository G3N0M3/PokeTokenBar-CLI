import random
from typing import List, Dict, Tuple, Any

GACHA_COST_SINGLE = 5_000_000       # 5.0M tokens per pull
GACHA_COST_MULTI = 45_000_000       # 45.0M tokens for 10-pull (1 free!)

GACHA_LOOT_TABLE = [
    # (Category, Item_Name, Weight, Reward_Type, Value)
    ("COMMON", "🫐 1x Oran Berry", 25, "item", "berry_oran"),
    ("COMMON", "🌿 1x Mint", 20, "item", "mint"),
    ("COMMON", "💰 +1.0M Spendable Tokens", 20, "tokens", 1_000_000),
    ("UNCOMMON", "🍬 1x Rare Candy", 15, "item", "rare_candy"),
    ("UNCOMMON", "🍇 1x Golden Razz Berry", 10, "item", "berry_golden"),
    ("UNCOMMON", "💰 +3.0M Spendable Tokens", 10, "tokens", 3_000_000),
    ("RARE", "🥚 1x Standard Egg Tier", 5, "egg", "normal"),
    ("RARE", "🥚 1x Uncommon Egg Tier", 4, "egg", "uncommon"),
    ("RARE", "🔮 1x Mega Stone", 4, "item", "mega_stone"),
    ("EPIC", "✨ 1x Shiny Charm", 2, "item", "shiny_charm"),
    ("EPIC", "🥚 1x Rare Egg Tier", 2, "egg", "rare"),
    ("LEGENDARY", "🌟 1x Guaranteed Shiny Companion (or +50M Tokens!)", 1, "legendary", 50_000_000),
]

class GachaEngine:
    @staticmethod
    def pull_one() -> Tuple[str, str, str, Any]:
        """Returns (Rarity, DisplayName, Type, Value)"""
        weights = [item[2] for item in GACHA_LOOT_TABLE]
        choice = random.choices(GACHA_LOOT_TABLE, weights=weights, k=1)[0]
        return choice[0], choice[1], choice[3], choice[4]

    @staticmethod
    def pull_ten() -> List[Tuple[str, str, str, Any]]:
        return [GachaEngine.pull_one() for _ in range(10)]
