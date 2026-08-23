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
    ("UNCOMMON", "🎫 1x Expedition Pass (Insta-Complete!)", 5, "item", "expedition_pass"),
    ("UNCOMMON", "💰 +3.0M Spendable Tokens", 10, "tokens", 3_000_000),
    ("RARE", "🥚 1x Standard Egg Tier", 5, "egg", "normal"),
    ("RARE", "🥚 1x Uncommon Egg Tier", 4, "egg", "uncommon"),
    ("RARE", "🔮 1x Mega Stone", 4, "item", "mega_stone"),
    ("RARE", "🪈 1x Poké Flute (Summons Boss!)", 3, "item", "poke_flute"),
    ("EPIC", "✨ 1x Shiny Charm", 2, "item", "shiny_charm"),
    ("EPIC", "🥚 1x Rare Egg Tier", 2, "egg", "rare"),
    ("LEGENDARY", "🌟 1x Master Ball (Guaranteed Shiny Hatch!)", 1, "item", "master_ball"),
]

class GachaEngine:
    @staticmethod
    def pull_one() -> Tuple[str, str, str, Any]:
        """Returns (Rarity, DisplayName, Type, Value)"""
        weights = [item[2] for item in GACHA_LOOT_TABLE]
        choice = list(random.choices(GACHA_LOOT_TABLE, weights=weights, k=1)[0])
        
        if choice[4] == "mega_stone":
            from poketokenbar.game.models import MEGA_STONES
            stone_id = random.choice(list(MEGA_STONES.keys()))
            choice[1] = f"🔮 1x {MEGA_STONES[stone_id]}"
            choice[4] = f"mega_stone_{stone_id}"
            
        return choice[0], choice[1], choice[3], choice[4]

    @staticmethod
    def pull_ten() -> List[Tuple[str, str, str, Any]]:
        return [GachaEngine.pull_one() for _ in range(10)]
