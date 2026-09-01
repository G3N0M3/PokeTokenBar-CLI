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
    ("RARE", "💎 1x Evolution Stone", 4, "evo_stone", "evo_stone"),
    ("RARE", "🔮 1x Mega Stone", 4, "item", "mega_stone"),
    ("RARE", "🪈 1x Poké Flute (Summons Boss!)", 3, "item", "poke_flute"),
    ("EPIC", "🍇 1x Golden Razz Berry", 2, "item", "berry_golden"),
    ("EPIC", "🥚 1x Rare Egg Tier", 2, "egg", "rare"),
    ("LEGENDARY", "🌟 1x Master Ball (Guaranteed Shiny Hatch!)", 1, "item", "master_ball"),
]

class GachaEngine:
    @staticmethod
    def pull_one(inv: Dict[str, Any] = None) -> Tuple[str, str, str, Any]:
        """Returns (Rarity, DisplayName, Type, Value)"""
        weights = [item[2] for item in GACHA_LOOT_TABLE]
        choice = list(random.choices(GACHA_LOOT_TABLE, weights=weights, k=1)[0])
        
        if choice[3] == "evo_stone":
            stone_types = [
                "water_stone", "fire_stone", "thunder_stone", 
                "leaf_stone", "moon_stone", "sun_stone", 
                "ice_stone", "shiny_stone", "dusk_stone", "dawn_stone"
            ]
            st_key = random.choice(stone_types)
            st_name = st_key.replace("_", " ").title()
            choice[1] = f"💎 1x {st_name}"
            choice[3] = "item"
            choice[4] = st_key

        elif choice[4] == "mega_stone":
            from poketokenbar.game.models import MEGA_STONES
            available_stones = list(MEGA_STONES.keys())
            if inv:
                available_stones = [s for s in available_stones if inv.get(f"mega_stone_{s}", 0) == 0]
            if not available_stones:
                choice[1] = "💰 +5.0M Spendable Tokens (Duplicate Mega Stone converted)"
                choice[3] = "tokens"
                choice[4] = 5_000_000
            else:
                stone_id = random.choice(available_stones)
                choice[1] = f"🔮 1x {MEGA_STONES[stone_id]}"
                choice[4] = f"mega_stone_{stone_id}"
            
        return choice[0], choice[1], choice[3], choice[4]

    @staticmethod
    def pull_ten(inv: Dict[str, Any] = None) -> List[Tuple[str, str, str, Any]]:
        local_inv = dict(inv) if inv else {}
        results = []
        for _ in range(10):
            res = GachaEngine.pull_one(local_inv)
            if res[2] == "item":
                local_inv[res[3]] = local_inv.get(res[3], 0) + 1
            results.append(res)
        return results
