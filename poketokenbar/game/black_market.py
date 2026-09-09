import random
from typing import Dict, List, Tuple, Optional, Any

# Exactly 100 contraband items across 9 illicit categories
BLACK_MARKET_POOL_100: List[Dict[str, Any]] = [
    # === 1. Bulk Goods & Consumables (12 items) ===
    {"name": "🍬 Bulk Rare Candies (5x)", "type": "item", "item_key": "rare_candy", "qty": 5, "price": 10_000_000, "stock": 2, "max_stock": 2, "badge": "33% OFF"},
    {"name": "🍬 Bulk Rare Candies (10x)", "type": "item", "item_key": "rare_candy", "qty": 10, "price": 18_000_000, "stock": 1, "max_stock": 1, "badge": "40% OFF"},
    {"name": "🍬 Bulk Rare Candies (25x)", "type": "item", "item_key": "rare_candy", "qty": 25, "price": 40_000_000, "stock": 1, "max_stock": 1, "badge": "BULK DEAL"},
    {"name": "🌿 Bulk Mints (5x)", "type": "item", "item_key": "mint", "qty": 5, "price": 3_500_000, "stock": 2, "max_stock": 2, "badge": "30% OFF"},
    {"name": "🌿 Bulk Mints (10x)", "type": "item", "item_key": "mint", "qty": 10, "price": 6_000_000, "stock": 1, "max_stock": 1, "badge": "40% OFF"},
    {"name": "🫐 Bulk Oran Berries (10x)", "type": "item", "item_key": "berry_oran", "qty": 10, "price": 6_000_000, "stock": 3, "max_stock": 3, "badge": "40% OFF"},
    {"name": "🫐 Bulk Oran Berries (25x)", "type": "item", "item_key": "berry_oran", "qty": 25, "price": 12_500_000, "stock": 2, "max_stock": 2, "badge": "HALF OFF"},
    {"name": "🍇 Bulk Golden Razz (3x)", "type": "item", "item_key": "berry_golden", "qty": 3, "price": 10_000_000, "stock": 2, "max_stock": 2, "badge": "33% OFF"},
    {"name": "🍇 Bulk Golden Razz (5x)", "type": "item", "item_key": "berry_golden", "qty": 5, "price": 15_000_000, "stock": 1, "max_stock": 1, "badge": "40% OFF"},
    {"name": "⚗️ Revitalizing Tonic", "type": "item", "item_key": "revitalizing_tonic", "qty": 1, "price": 8_000_000, "stock": 2, "max_stock": 2, "badge": "RESTORE"},
    {"name": "⚗️ Revitalizing Tonic (3x)", "type": "item", "item_key": "revitalizing_tonic", "qty": 3, "price": 20_000_000, "stock": 1, "max_stock": 1, "badge": "RESTORE"},
    {"name": "🏺 Sacred Ash", "type": "item", "item_key": "sacred_ash", "qty": 1, "price": 30_000_000, "stock": 1, "max_stock": 1, "badge": "REVIVE"},

    # === 2. Elemental Evolution Troves (10 items) ===
    {"name": "💎 Evolution Stone Trove (3x)", "type": "trove_stone", "qty": 3, "price": 30_000_000, "stock": 2, "max_stock": 2, "badge": "SEALED"},
    {"name": "💎 Evolution Stone Cache (5x)", "type": "trove_stone", "qty": 5, "price": 45_000_000, "stock": 1, "max_stock": 1, "badge": "SEALED"},
    {"name": "🔥 Ignited Fire Trove (3x)", "type": "trove_stone_fire", "qty": 3, "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "SEALED"},
    {"name": "💧 Oceanic Water Trove (3x)", "type": "trove_stone_water", "qty": 3, "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "SEALED"},
    {"name": "⚡ Voltage Thunder Trove (3x)", "type": "trove_stone_thunder", "qty": 3, "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "SEALED"},
    {"name": "🍃 Verdant Leaf Trove (3x)", "type": "trove_stone_leaf", "qty": 3, "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "SEALED"},
    {"name": "🌙 Celestial Stone Trove (2x)", "type": "trove_stone_celestial", "qty": 2, "price": 28_000_000, "stock": 1, "max_stock": 1, "badge": "SEALED"},
    {"name": "☀️ Solar Stone Cache (3x)", "type": "trove_stone_sun", "qty": 3, "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "SEALED"},
    {"name": "🌑 Twilight Stone Trove (2x)", "type": "trove_stone_twilight", "qty": 2, "price": 28_000_000, "stock": 1, "max_stock": 1, "badge": "SEALED"},
    {"name": "🪨 Everstone Bundle (3x)", "type": "item", "item_key": "everstone", "qty": 3, "price": 1_200_000, "stock": 2, "max_stock": 2, "badge": "CONTRABAND"},

    # === 3. Smuggled Combat Held Items (14 items) ===
    {"name": "🔮 Life Orb (Held Item)", "type": "item", "item_key": "life_orb", "qty": 1, "price": 25_000_000, "stock": 1, "max_stock": 1, "badge": "COMBAT"},
    {"name": "🥊 Choice Band (Held Item)", "type": "item", "item_key": "choice_band", "qty": 1, "price": 20_000_000, "stock": 1, "max_stock": 1, "badge": "COMBAT"},
    {"name": "👓 Choice Specs (Held Item)", "type": "item", "item_key": "choice_specs", "qty": 1, "price": 20_000_000, "stock": 1, "max_stock": 1, "badge": "COMBAT"},
    {"name": "🥊 Choice Scarf (Held Item)", "type": "item", "item_key": "choice_scarf", "qty": 1, "price": 18_000_000, "stock": 1, "max_stock": 1, "badge": "COMBAT"},
    {"name": "🎗️ Focus Sash (Held Item)", "type": "item", "item_key": "focus_sash", "qty": 1, "price": 22_000_000, "stock": 1, "max_stock": 1, "badge": "COMBAT"},
    {"name": "🍎 Leftovers (Held Item)", "type": "item", "item_key": "leftovers", "qty": 1, "price": 15_000_000, "stock": 1, "max_stock": 1, "badge": "COMBAT"},
    {"name": "⛑️ Rocky Helmet (Held Item)", "type": "item", "item_key": "rocky_helmet", "qty": 1, "price": 20_000_000, "stock": 1, "max_stock": 1, "badge": "COMBAT"},
    {"name": "🦺 Assault Vest (Held Item)", "type": "item", "item_key": "assault_vest", "qty": 1, "price": 22_000_000, "stock": 1, "max_stock": 1, "badge": "COMBAT"},
    {"name": "🥾 Heavy Boots (Held Item)", "type": "item", "item_key": "heavy_boots", "qty": 1, "price": 18_000_000, "stock": 1, "max_stock": 1, "badge": "COMBAT"},
    {"name": "🔍 Scope Lens (Held Item)", "type": "item", "item_key": "scope_lens", "qty": 1, "price": 30_000_000, "stock": 1, "max_stock": 1, "badge": "COMBAT"},
    {"name": "🔔 Soothe Bell (Held Item)", "type": "item", "item_key": "soothe_bell", "qty": 1, "price": 20_000_000, "stock": 1, "max_stock": 1, "badge": "COMBAT"},
    {"name": "🎒 Exp. Share (Held Item)", "type": "item", "item_key": "exp_share", "qty": 1, "price": 25_000_000, "stock": 1, "max_stock": 1, "badge": "COMBAT"},
    {"name": "🪙 Amulet Coin (Held Item)", "type": "item", "item_key": "amulet_coin", "qty": 1, "price": 18_000_000, "stock": 1, "max_stock": 1, "badge": "COMBAT"},
    {"name": "🍀 Lucky Egg (Held Item)", "type": "item", "item_key": "lucky_egg", "qty": 1, "price": 25_000_000, "stock": 1, "max_stock": 1, "badge": "COMBAT"},

    # === 4. Syndicate Evolution Artifacts (10 items) ===
    {"name": "⚙️ Metal Coat", "type": "item", "item_key": "metal_coat", "qty": 1, "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "EVOLUTION"},
    {"name": "👑 King's Rock", "type": "item", "item_key": "kings_rock", "qty": 1, "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "EVOLUTION"},
    {"name": "🐉 Dragon Scale", "type": "item", "item_key": "dragon_scale", "qty": 1, "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "EVOLUTION"},
    {"name": "💾 Upgrade", "type": "item", "item_key": "upgrade", "qty": 1, "price": 30_000_000, "stock": 1, "max_stock": 1, "badge": "EVOLUTION"},
    {"name": "💿 Dubious Disc", "type": "item", "item_key": "dubious_disc", "qty": 1, "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "EVOLUTION"},
    {"name": "🛡️ Protector", "type": "item", "item_key": "protector", "qty": 1, "price": 30_000_000, "stock": 1, "max_stock": 1, "badge": "EVOLUTION"},
    {"name": "🔌 Electirizer", "type": "item", "item_key": "electirizer", "qty": 1, "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "EVOLUTION"},
    {"name": "🌋 Magmarizer", "type": "item", "item_key": "magmarizer", "qty": 1, "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "EVOLUTION"},
    {"name": "👻 Reaper Cloth", "type": "item", "item_key": "reaper_cloth", "qty": 1, "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "EVOLUTION"},
    {"name": "✨ Prism Scale", "type": "item", "item_key": "prism_scale", "qty": 1, "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "EVOLUTION"},

    # === 5. Specialized Illicit Eggs (8 items) ===
    {"name": "🥚 Rare Egg Voucher", "type": "egg", "egg_tier": "rare", "price": 12_000_000, "stock": 1, "max_stock": 1, "badge": "SPECIAL"},
    {"name": "🌟 Legendary Egg Voucher", "type": "egg", "egg_tier": "legendary", "price": 40_000_000, "stock": 1, "max_stock": 1, "badge": "LEGENDARY"},
    {"name": "🦖 Ancient Fossil Egg", "type": "egg", "egg_tier": "fossil", "price": 28_000_000, "stock": 1, "max_stock": 1, "badge": "SPECIAL"},
    {"name": "🐉 Dragon Den Egg", "type": "egg", "egg_tier": "dragon", "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "SPECIAL"},
    {"name": "🧬 Shadow Fetal Voucher", "type": "egg", "egg_tier": "shadow_fetal", "price": 50_000_000, "stock": 1, "max_stock": 1, "badge": "MYTHICAL"},
    {"name": "🌱 Starter Mystery Egg", "type": "egg", "egg_tier": "starter", "price": 20_000_000, "stock": 1, "max_stock": 1, "badge": "SPECIAL"},
    {"name": "⚡ Paradox Capsule", "type": "egg", "egg_tier": "paradox", "price": 45_000_000, "stock": 1, "max_stock": 1, "badge": "SPECIAL"},
    {"name": "🎲 Smuggler Mystery Egg", "type": "egg", "egg_tier": "smuggler_mystery", "price": 15_000_000, "stock": 1, "max_stock": 1, "badge": "SPECIAL"},

    # === 6. Expedition Cartography & Tech (8 items) ===
    {"name": "📜 Ancient Map Trove (3x)", "type": "map_pack", "qty": 3, "price": 15_000_000, "stock": 1, "max_stock": 1, "badge": "SEALED"},
    {"name": "📜 Master Map Pack (5x)", "type": "map_pack", "qty": 5, "price": 22_000_000, "stock": 1, "max_stock": 1, "badge": "SEALED"},
    {"name": "🎫 Forged License (3x)", "type": "item", "item_key": "expedition_pass", "qty": 3, "price": 25_000_000, "stock": 1, "max_stock": 1, "badge": "TECH"},
    {"name": "🌬️ Smuggler's Warp Whistle", "type": "item", "item_key": "warp_whistle", "qty": 1, "price": 30_000_000, "stock": 1, "max_stock": 1, "badge": "TECH"},
    {"name": "🧭 Compass of the Deep", "type": "item", "item_key": "compass_of_deep", "qty": 1, "price": 25_000_000, "stock": 1, "max_stock": 1, "badge": "TECH"},
    {"name": "⚡ Energy Tonic (All)", "type": "item", "item_key": "expedition_energy_tonic", "qty": 1, "price": 18_000_000, "stock": 1, "max_stock": 1, "badge": "TECH"},
    {"name": "📜 Exped. Insurance", "type": "item", "item_key": "expedition_insurance", "qty": 1, "price": 20_000_000, "stock": 1, "max_stock": 1, "badge": "TECH"},
    {"name": "📡 Rocket Radar", "type": "item", "item_key": "rocket_radar", "qty": 1, "price": 25_000_000, "stock": 1, "max_stock": 1, "badge": "TECH"},

    # === 7. Contraband Mystery Crates (8 items) ===
    {"name": "📦 Rocket Black Box", "type": "mystery_crate", "crate_id": "rocket_black_box", "price": 15_000_000, "stock": 1, "max_stock": 1, "badge": "CRATE"},
    {"name": "🔒 Smuggler's Safe", "type": "mystery_crate", "crate_id": "smugglers_safe", "price": 20_000_000, "stock": 1, "max_stock": 1, "badge": "CRATE"},
    {"name": "🔬 Silph Prototype Crate", "type": "mystery_crate", "crate_id": "silph_prototype_crate", "price": 25_000_000, "stock": 1, "max_stock": 1, "badge": "CRATE"},
    {"name": "🏢 Devon Stolen Vault", "type": "mystery_crate", "crate_id": "devon_stolen_vault", "price": 25_000_000, "stock": 1, "max_stock": 1, "badge": "CRATE"},
    {"name": "🧪 Aether Specimen Jar", "type": "mystery_crate", "crate_id": "aether_specimen_jar", "price": 22_000_000, "stock": 1, "max_stock": 1, "badge": "CRATE"},
    {"name": "🏆 Golden Syndicate Chest", "type": "mystery_crate", "crate_id": "golden_syndicate_chest", "price": 50_000_000, "stock": 1, "max_stock": 1, "badge": "CRATE"},
    {"name": "💼 Shady Duffle Bag", "type": "mystery_crate", "crate_id": "shady_duffle_bag", "price": 12_000_000, "stock": 2, "max_stock": 2, "badge": "CRATE"},
    {"name": "🚢 Shipping Container", "type": "mystery_crate", "crate_id": "sealed_shipping_container", "price": 35_000_000, "stock": 1, "max_stock": 1, "badge": "CRATE"},

    # === 8. High-Roller Mega Stones & Orbs & Master Ball (18 items) ===
    {"name": "🌟 Master Ball", "type": "item", "item_key": "master_ball", "qty": 1, "price": 60_000_000, "stock": 1, "max_stock": 1, "badge": "RARE"},
    {"name": "🔮 Charizardite X", "type": "mega_stone", "stone_id": "6_X", "price": 45_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔮 Charizardite Y", "type": "mega_stone", "stone_id": "6_Y", "price": 45_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔮 Venusaurite", "type": "mega_stone", "stone_id": "3", "price": 40_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔮 Blastoisinite", "type": "mega_stone", "stone_id": "9", "price": 40_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔮 Gengarite", "type": "mega_stone", "stone_id": "94", "price": 45_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔮 Lucarionite", "type": "mega_stone", "stone_id": "448", "price": 45_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔮 Mewtwonite X", "type": "mega_stone", "stone_id": "150_X", "price": 55_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔮 Mewtwonite Y", "type": "mega_stone", "stone_id": "150_Y", "price": 55_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔮 Blazikenite", "type": "mega_stone", "stone_id": "257", "price": 45_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔮 Swampertite", "type": "mega_stone", "stone_id": "260", "price": 40_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔮 Sceptilite", "type": "mega_stone", "stone_id": "254", "price": 40_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔮 Salamencite", "type": "mega_stone", "stone_id": "373", "price": 50_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔮 Metagrossite", "type": "mega_stone", "stone_id": "376", "price": 50_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔮 Garchompite", "type": "mega_stone", "stone_id": "445", "price": 50_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔮 Tyranitarite", "type": "mega_stone", "stone_id": "248", "price": 50_000_000, "stock": 1, "max_stock": 1, "badge": "MEGA"},
    {"name": "🔵 Blue Orb", "type": "mega_stone", "stone_id": "382", "price": 60_000_000, "stock": 1, "max_stock": 1, "badge": "PRIMAL"},
    {"name": "🔴 Red Orb", "type": "mega_stone", "stone_id": "383", "price": 60_000_000, "stock": 1, "max_stock": 1, "badge": "PRIMAL"},

    # === 9. Counterfeits & Fraudulent Goods (12 items) ===
    {"name": "🍬 \"Rare Candy\"", "type": "item", "item_key": "fake_rare_candy", "qty": 1, "price": 2_000_000, "stock": 3, "max_stock": 3, "badge": "CHEAP!"},
    {"name": "🌟 \"Master Ball\"", "type": "item", "item_key": "fake_master_ball", "qty": 1, "price": 5_000_000, "stock": 1, "max_stock": 1, "badge": "90% OFF"},
    {"name": "⚡ \"Thunder Stone\"", "type": "item", "item_key": "fake_thunder_stone", "qty": 1, "price": 3_000_000, "stock": 2, "max_stock": 2, "badge": "HOT DEAL"},
    {"name": "💧 \"Water Stone\"", "type": "item", "item_key": "fake_water_stone", "qty": 1, "price": 3_000_000, "stock": 2, "max_stock": 2, "badge": "HOT DEAL"},
    {"name": "🔥 \"Fire Stone\"", "type": "item", "item_key": "fake_fire_stone", "qty": 1, "price": 3_000_000, "stock": 2, "max_stock": 2, "badge": "HOT DEAL"},
    {"name": "📜 \"Ancient Map\"", "type": "item", "item_key": "fake_ancient_map", "qty": 1, "price": 2_000_000, "stock": 2, "max_stock": 2, "badge": "HOT DEAL"},
    {"name": "🪙 \"Gold Nugget\"", "type": "item", "item_key": "fake_gold_nugget", "qty": 1, "price": 5_000_000, "stock": 2, "max_stock": 2, "badge": "LUXURY"},
    {"name": "🎒 \"Exp. Share\"", "type": "item", "item_key": "fake_exp_share", "qty": 1, "price": 4_000_000, "stock": 1, "max_stock": 1, "badge": "BARGAIN"},
    {"name": "🔔 \"Soothe Bell\"", "type": "item", "item_key": "fake_soothe_bell", "qty": 1, "price": 3_000_000, "stock": 1, "max_stock": 1, "badge": "BARGAIN"},
    {"name": "🔍 \"Scope Lens\"", "type": "item", "item_key": "fake_scope_lens", "qty": 1, "price": 4_000_000, "stock": 1, "max_stock": 1, "badge": "BARGAIN"},
    {"name": "🎗️ \"Focus Sash\"", "type": "item", "item_key": "fake_focus_sash", "qty": 1, "price": 3_000_000, "stock": 1, "max_stock": 1, "badge": "BARGAIN"},
    {"name": "🔮 \"Charizardite\"", "type": "item", "item_key": "fake_mega_stone", "qty": 1, "price": 8_000_000, "stock": 1, "max_stock": 1, "badge": "STEAL!"},
]

ALL_STONE_TYPES = [
    "water_stone", "fire_stone", "thunder_stone",
    "leaf_stone", "moon_stone", "sun_stone",
    "ice_stone", "shiny_stone", "dusk_stone", "dawn_stone"
]

def unpack_trove(deal: Dict[str, Any], qty: int = 1) -> Tuple[Dict[str, int], List[str]]:
    """Unpacks a sealed trove deal into concrete items and their user-facing names."""
    dtype = deal.get("type", "")
    items_to_add: Dict[str, int] = {}
    reveal_names: List[str] = []

    if dtype == "trove_stone":
        count = deal.get("qty", 3) * qty
        chosen = [random.choice(ALL_STONE_TYPES) for _ in range(count)]
        for s in chosen:
            items_to_add[s] = items_to_add.get(s, 0) + 1
            reveal_names.append(s.replace("_", " ").title())
    elif dtype == "trove_stone_fire":
        count = deal.get("qty", 3) * qty
        items_to_add["fire_stone"] = items_to_add.get("fire_stone", 0) + count
        reveal_names.extend(["Fire Stone"] * count)
    elif dtype == "trove_stone_water":
        count = deal.get("qty", 3) * qty
        items_to_add["water_stone"] = items_to_add.get("water_stone", 0) + count
        reveal_names.extend(["Water Stone"] * count)
    elif dtype == "trove_stone_thunder":
        count = deal.get("qty", 3) * qty
        items_to_add["thunder_stone"] = items_to_add.get("thunder_stone", 0) + count
        reveal_names.extend(["Thunder Stone"] * count)
    elif dtype == "trove_stone_leaf":
        count = deal.get("qty", 3) * qty
        items_to_add["leaf_stone"] = items_to_add.get("leaf_stone", 0) + count
        reveal_names.extend(["Leaf Stone"] * count)
    elif dtype == "trove_stone_celestial":
        items_to_add["moon_stone"] = items_to_add.get("moon_stone", 0) + qty
        items_to_add["sun_stone"] = items_to_add.get("sun_stone", 0) + qty
        for _ in range(qty):
            reveal_names.extend(["Moon Stone", "Sun Stone"])
    elif dtype == "trove_stone_sun":
        count = deal.get("qty", 3) * qty
        items_to_add["sun_stone"] = items_to_add.get("sun_stone", 0) + count
        reveal_names.extend(["Sun Stone"] * count)
    elif dtype == "trove_stone_twilight":
        items_to_add["dusk_stone"] = items_to_add.get("dusk_stone", 0) + qty
        items_to_add["dawn_stone"] = items_to_add.get("dawn_stone", 0) + qty
        for _ in range(qty):
            reveal_names.extend(["Dusk Stone", "Dawn Stone"])
    elif dtype == "map_pack":
        count = deal.get("qty", 3) * qty
        items_to_add["map_fragment"] = items_to_add.get("map_fragment", 0) + count
        reveal_names.extend([f"{count}x Map Fragments"])

    return items_to_add, reveal_names

def unpack_mystery_crate(crate_id: str, inv: Optional[Dict[str, int]] = None) -> Tuple[Dict[str, int], int, Optional[str], str]:
    """Unpacks a contraband mystery crate into inventory items, token grant, optional egg, and reveal text."""
    roll = random.random()
    items: Dict[str, int] = {}
    tokens = 0
    egg: Optional[str] = None
    from poketokenbar.game.models import MEGA_STONES

    if crate_id == "rocket_black_box":
        if roll < 0.10:
            if random.random() < 0.5:
                items["master_ball"] = 1
                desc = "🌟 JACKPOT! You found a genuine Master Ball!"
            else:
                egg = "legendary"
                desc = "🌟 JACKPOT! You found a Legendary Egg Voucher!"
        elif roll < 0.40:
            if random.random() < 0.5:
                items["rare_candy"] = 10
                desc = "🍬 GREAT FIND! Unpacked 10x Rare Candies!"
            else:
                pool = ["6_X", "6_Y", "94", "448"]
                unowned = [s for s in pool if not inv or inv.get(f"mega_stone_{s}", 0) == 0]
                if unowned:
                    s_key = random.choice(unowned)
                    items[f"mega_stone_{s_key}"] = 1
                    s_name = MEGA_STONES.get(s_key, f"stone #{s_key}")
                    desc = f"🔮 GREAT FIND! Unpacked a rare Mega Stone ({s_name})!"
                else:
                    items["rare_candy"] = 10
                    desc = "🍬 GREAT FIND! (Already owned Mega Stone converted to 10x Rare Candies!)"
        elif roll < 0.80:
            s1, s2, s3 = random.choices(ALL_STONE_TYPES, k=3)
            for s in [s1, s2, s3]: items[s] = items.get(s, 0) + 1
            items["map_fragment"] = items.get("map_fragment", 0) + 2
            desc = f"💎 Solid Haul! Unpacked 3x Evolution Stones and 2x Map Fragments!"
        else:
            items["berry_oran"] = 3
            desc = "💨 Dud! A smoke bomb went off! Left behind only 3x Oran Berries."

    elif crate_id == "smugglers_safe":
        if roll < 0.15:
            tokens = 25_000_000
            desc = "💰 JACKPOT! Safe opened to reveal a 25.0M Token Stash!"
        elif roll < 0.50:
            h = random.choice(["life_orb", "choice_band", "choice_scarf", "choice_specs"])
            items[h] = 1
            desc = f"🥊 Combat Gear! Unpacked a smuggled {h.replace('_', ' ').title()}!"
        elif roll < 0.80:
            for s in random.choices(ALL_STONE_TYPES, k=5):
                items[s] = items.get(s, 0) + 1
            desc = "💎 Gem Cache! Unpacked 5x Evolution Stones!"
        else:
            items["berry_oran"] = 5
            items["everstone"] = 1
            desc = "🪨 Dud! The safe was stuffed with 5x Oran Berries and a heavy Everstone."

    elif crate_id == "silph_prototype_crate":
        if roll < 0.20:
            if random.random() < 0.5:
                items["expedition_pass"] = 3
                desc = "🎫 Silph Tech! Unpacked 3x Forged Expedition Passes!"
            else:
                items["warp_whistle"] = 1
                desc = "🌬️ Silph Secret! Unpacked a Smuggler's Warp Whistle!"
        elif roll < 0.60:
            h = random.choice(["scope_lens", "exp_share", "choice_specs", "assault_vest"])
            items[h] = 1
            desc = f"🔬 High-Tech Prototype! Unpacked {h.replace('_', ' ').title()}!"
        elif roll < 0.90:
            items["map_fragment"] = 5
            desc = "📜 Cartography Files! Unpacked 5x Map Fragments!"
        else:
            items["fake_exp_share"] = 1
            desc = "🔋 Dud! The prototype was dead—corroded wires and a dead battery."

    elif crate_id == "devon_stolen_vault":
        if roll < 0.25:
            pool = ["254", "257", "260", "373", "376"]
            unowned = [s for s in pool if not inv or inv.get(f"mega_stone_{s}", 0) == 0]
            if unowned:
                s_key = random.choice(unowned)
                items[f"mega_stone_{s_key}"] = 1
                s_name = MEGA_STONES.get(s_key, f"stone #{s_key}")
                desc = f"🔮 Devon Masterpiece! Unpacked a Hoenn Mega Stone ({s_name})!"
            else:
                items["rare_candy"] = 15
                desc = "🍬 Devon Vault Sweetness! (Already owned Mega Stone converted to 15x Rare Candies!)"
        elif roll < 0.60:
            items["rare_candy"] = 15
            desc = "🍬 Devon Vault Sweetness! Unpacked 15x Rare Candies!"
        elif roll < 0.90:
            artifacts = ["metal_coat", "kings_rock", "dragon_scale", "upgrade", "protector"]
            for a in random.choices(artifacts, k=3):
                items[a] = items.get(a, 0) + 1
            desc = "⚙️ Corporate Artifacts! Unpacked 3x Syndicate Evolution Artifacts!"
        else:
            items["fake_gold_nugget"] = 1
            desc = "🪙 Dud! Stolen vault contained only a lump of fool's gold."

    elif crate_id == "aether_specimen_jar":
        if roll < 0.30:
            if random.random() < 0.5:
                egg = "paradox"
                desc = "⚡ Aether Experiment! Unpacked a preserved Paradox Capsule!"
            else:
                egg = "rare"
                desc = "🥚 Specimen Secured! Unpacked a Rare Egg Voucher!"
        elif roll < 0.70:
            items["berry_golden"] = 5
            desc = "🍇 Nutrient Gel! Unpacked 5x Golden Razz Berries!"
        elif roll < 0.90:
            items["mint"] = 10
            desc = "🌿 Genetic Mints! Unpacked 10x Mints!"
        else:
            items["berry_oran"] = 2
            desc = "🧪 Dud! The specimen broke into foul-smelling slime and 2x Oran Berries."

    elif crate_id == "golden_syndicate_chest":
        if roll < 0.25:
            if random.random() < 0.5:
                items["master_ball"] = 1
                desc = "🌟 SYNDICATE CROWN JEWEL! Unpacked a genuine Master Ball!"
            else:
                egg = "shadow_fetal"
                desc = "🧬 GENETIC MYTHIC! Unpacked a Shadow Fetal Voucher!"
        elif roll < 0.60:
            tokens = 75_000_000
            desc = "💰 MASSIVE JACKPOT! Found 75.0M Tokens in gold bullion!"
        elif roll < 0.90:
            pool = ["150_X", "150_Y", "382", "383", "94", "6_X"]
            unowned = [s for s in pool if not inv or inv.get(f"mega_stone_{s}", 0) == 0]
            if len(unowned) >= 2:
                s1, s2 = random.sample(unowned, 2)
                items[f"mega_stone_{s1}"] = 1
                items[f"mega_stone_{s2}"] = 1
                desc = "🔮 High-Roller Stash! Unpacked 2x Legendary Mega Stones / Orbs!"
            elif len(unowned) == 1:
                s1 = unowned[0]
                items[f"mega_stone_{s1}"] = 1
                tokens = 25_000_000
                s_name = MEGA_STONES.get(s1, s1)
                desc = f"🔮 High-Roller Stash! Unpacked 1x Mega Stone ({s_name}) & 25.0M Tokens!"
            else:
                tokens = 50_000_000
                desc = "💰 High-Roller Stash! (Already owned Mega Stones converted to 50.0M Tokens!)"
        else:
            items["rare_candy"] = 20
            desc = "🍬 Sweet Syndicate! Unpacked 20x Rare Candies!"

    elif crate_id == "shady_duffle_bag":
        if roll < 0.20:
            items["rare_candy"] = 5
            items["map_fragment"] = 1
            desc = "🍬 Shady Loot! Unpacked 5x Rare Candies and 1x Map Fragment!"
        elif roll < 0.50:
            items["berry_oran"] = 3
            items["mint"] = 2
            desc = "🫐 Street Supplies! Unpacked 3x Oran Berries and 2x Mints!"
        elif roll < 0.80:
            s = random.choice(ALL_STONE_TYPES)
            items[s] = 1
            desc = f"💎 Hidden Stone! Unpacked 1x {s.replace('_', ' ').title()}!"
        else:
            items["fake_master_ball"] = 1
            desc = "📦 Dud! The duffle bag contained only a cheap cardboard ball replica."

    else:  # sealed_shipping_container
        if roll < 0.20:
            tokens = 50_000_000
            desc = "💰 Contraband Freight! Found 50.0M Tokens in cash stashes!"
        elif roll < 0.50:
            egg = "legendary"
            desc = "🌟 Illicit Cargo! Unpacked a Legendary Egg Voucher!"
        elif roll < 0.80:
            items["map_fragment"] = 10
            desc = "📜 Full Cartography Archive! Unpacked 10x Map Fragments!"
        else:
            for s in random.choices(ALL_STONE_TYPES, k=15):
                items[s] = items.get(s, 0) + 1
            desc = "💎 Mineral Shipment! Unpacked 15x Evolution Stones!"

    return items, tokens, egg, desc

def get_fake_item_fraud_message(fake_key: str) -> str:
    """Returns humorous scam reveal text when a counterfeit item is used or inspected."""
    scams = {
        "fake_rare_candy": "Crunch! It's just dyed rock candy! Companion spat it out. +0 XP.",
        "fake_master_ball": "You inspect the Master Ball... It squished! It's painted cardboard!",
        "fake_thunder_stone": "The Thunder Stone crumbles into yellow chalk dust in your hands!",
        "fake_water_stone": "It's just an ordinary blue glass pebble from the beach. No evolution!",
        "fake_fire_stone": "Ouch! It's just a warm lump of burnt charcoal briquette!",
        "fake_ancient_map": "You unfurl the map... It's just crude pirate doodles drawn in red crayon!",
        "fake_gold_nugget": "A jeweler examines it: 'That's fool's gold (iron pyrite)!' You got +1 token.",
        "fake_exp_share": "You inspect the Exp. Share... It's just corroded wire and a dead AA battery!",
        "fake_soothe_bell": "The bell emits a screeching metallic scrape! Companion hated it (-5% Happiness).",
        "fake_scope_lens": "You look through the lens... It's just the curved bottom of a soda bottle!",
        "fake_focus_sash": "The Focus Sash tears in half immediately! It was made of crepe paper!",
        "fake_mega_stone": "You tap the Mega Stone. It's a hollow painted plaster paperweight!",
    }
    return scams.get(fake_key, "You were scammed! The item was an illicit fake.")
