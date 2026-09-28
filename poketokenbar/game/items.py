"""Item catalog, bag mapping, and item metadata for PokeTokenBar."""

from typing import Optional, Dict, List, Tuple
from poketokenbar.game.models import ItemKind

BAG_CATALOG: List[Tuple[str, str, str]] = [
    ("1", "rare_candy", "🍬 Rare Candy"),
    ("2", "berry_oran", "🫐 Oran Berry"),
    ("3", "berry_golden", "🍇 Golden Razz"),
    ("4", "poke_flute", "🪈 Poké Flute (Summons Boss)"),
    ("5", "master_ball", "🌟 Master Ball (Hatch Shiny)"),
    ("6", "map_fragment", "📜 Map"),
    ("7", "expedition_license", "📜 Exped. License (+10 slots)"),
    ("8", "everstone", "🪨 Everstone (No evolution)"),
    ("9", "lucky_egg", "🍀 Lucky Egg (+20% XP)"),
    ("10", "amulet_coin", "🪙 Amulet Coin (+50% tokens)"),
    ("11", "leftovers", "🍎 Leftovers (No hap. decay)"),
    ("12", "choice_scarf", "🥊 Choice Scarf (+20% spd)"),
    ("13", "exp_share", "🎒 Exp. Share (XP Sharing)"),
    ("14", "soothe_bell", "🔔 Soothe Bell (Hap. Boost)"),
    ("15", "scope_lens", "🔍 Scope Lens (2x Shiny)"),
    ("16", "life_orb", "🔮 Life Orb (+10% Tokens)"),
    ("17", "choice_band", "🥊 Choice Band (+50% Dmg)"),
    # Combat held items
    ("18", "choice_specs", "👓 Choice Specs (+50% SpAtk)"),
    ("19", "focus_sash", "🎗️ Focus Sash (Endure 1 HP)"),
    ("20", "rocky_helmet", "⛑️ Rocky Helmet (Recoil)"),
    ("21", "assault_vest", "🦺 Assault Vest (-30% SpDef)"),
    ("22", "heavy_boots", "🥾 Heavy Boots (Hazard Guard)"),
    ("23", "compass_of_deep", "🧭 Compass of Deep (+25% Spd)"),
    # Consumables & Field Tech
    ("24", "revitalizing_tonic", "⚗️ Revitalizing Tonic (100% Hap)"),
    ("25", "sacred_ash", "🏺 Sacred Ash (Full Red Revive)"),
    ("26", "warp_whistle", "🌬️ Warp Whistle (Finish All)"),
    ("27", "expedition_pass", "🎫 Expedition Pass"),
    ("28", "expedition_energy_tonic", "⚡ Energy Tonic (+50% Hap All)"),
    ("29", "expedition_insurance", "📜 Exped. Insurance Policy"),
    ("30", "rocket_radar", "📡 Rocket Radar (+50% Tokens)"),
    # Syndicate Evolution Artifacts
    ("31", "metal_coat", "⚙️ Metal Coat"),
    ("32", "kings_rock", "👑 King's Rock"),
    ("33", "dragon_scale", "🐉 Dragon Scale"),
    ("34", "upgrade", "💾 Upgrade"),
    ("35", "dubious_disc", "💿 Dubious Disc"),
    ("36", "protector", "🛡️ Protector"),
    ("37", "electirizer", "🔌 Electirizer"),
    ("38", "magmarizer", "🌋 Magmarizer"),
    ("39", "reaper_cloth", "👻 Reaper Cloth"),
    ("40", "prism_scale", "✨ Prism Scale"),
    # Evolution Stones
    ("41", "water_stone", "💎 Water Stone"),
    ("42", "fire_stone", "💎 Fire Stone"),
    ("43", "thunder_stone", "💎 Thunder Stone"),
    ("44", "leaf_stone", "💎 Leaf Stone"),
    ("45", "moon_stone", "💎 Moon Stone"),
    ("46", "sun_stone", "💎 Sun Stone"),
    ("47", "ice_stone", "💎 Ice Stone"),
    ("48", "shiny_stone", "💎 Shiny Stone"),
    ("49", "dusk_stone", "💎 Dusk Stone"),
    ("50", "dawn_stone", "💎 Dawn Stone"),
    # Fake Contraband items
    ("51", "fake_rare_candy", "🍬 \"Rare Candy\""),
    ("52", "fake_master_ball", "🌟 \"Master Ball\""),
    ("53", "fake_thunder_stone", "⚡ \"Thunder Stone\""),
    ("54", "fake_water_stone", "💧 \"Water Stone\""),
    ("55", "fake_fire_stone", "🔥 \"Fire Stone\""),
    ("56", "fake_ancient_map", "📜 \"Ancient Map\""),
    ("57", "fake_gold_nugget", "🪙 \"Gold Nugget\""),
    ("58", "fake_exp_share", "🎒 \"Exp. Share\""),
    ("59", "fake_soothe_bell", "🔔 \"Soothe Bell\""),
    ("60", "fake_scope_lens", "🔍 \"Scope Lens\""),
    ("61", "fake_focus_sash", "🎗️ \"Focus Sash\""),
    ("62", "fake_mega_stone", "🔮 \"Charizardite\""),
    # Special Rocket Bag items
    ("64", "rocket_master_ball", "🔮 Rocket Master Ball"),
]

BAG_CATALOG_MAP: Dict[str, str] = {cid: key for cid, key, _ in BAG_CATALOG}
BAG_KEY_TO_ID: Dict[str, str] = {key: cid for cid, key, _ in BAG_CATALOG}

ITEM_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "rare_candy": {
        "name": "🍬 Rare Candy",
        "clean_name": "Rare Candy",
        "category": "Consumable",
        "desc": "Instantly grants +60% of shop cost in XP to active companion.",
        "usage": "Type 'use <id> [qty]' to feed to active companion.",
    },
    "berry_oran": {
        "name": "🫐 Oran Berry",
        "clean_name": "Oran Berry",
        "category": "Consumable",
        "desc": "Restores +25% Happiness per berry. 4 berries fully revive exhausted Pokémon.",
        "usage": "Type 'feed <#[id]|<=[pct]|[pct]|0> [qty]' to feed Oran Berries 🫐.",
    },
    "berry_golden": {
        "name": "🍇 Golden Razz",
        "clean_name": "Golden Razz Berry",
        "category": "Consumable",
        "desc": "Boosts shiny hatch odds on your NEXT egg hatch to 1/24.",
        "usage": "Type 'use <id>' to activate shiny hatch boost.",
    },
    "poke_flute": {
        "name": "🪈 Poké Flute",
        "clean_name": "Poké Flute",
        "category": "Key Item",
        "desc": "Awakens and summons an undefeated Gym Boss for battle.",
        "usage": "Type 'use <id>' to summon a Gym Boss to fight.",
    },
    "master_ball": {
        "name": "🌟 Master Ball",
        "clean_name": "Master Ball",
        "category": "Key Item",
        "desc": "Instantly hatches your incubating egg into a guaranteed SHINY!",
        "usage": "Type 'use <id>' while incubating an egg.",
    },
    "map_fragment": {
        "name": "📜 Ancient Map",
        "clean_name": "Ancient Map",
        "category": "Key Item",
        "desc": "Unlocks Spear Pillar expedition once 3 fragments are collected.",
        "usage": "Used automatically when dispatching to Spear Pillar.",
    },
    "expedition_license": {
        "name": "📜 Exped. License",
        "clean_name": "Expedition License",
        "category": "Field Tech",
        "desc": "Permanently increases concurrent expedition slots by +10.",
        "usage": "Type 'use <id>' to expand expedition capacity.",
    },
    "everstone": {
        "name": "🪨 Everstone",
        "clean_name": "Everstone",
        "category": "Held Item",
        "desc": "Completely halts companion evolution while equipped.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "lucky_egg": {
        "name": "🍀 Lucky Egg",
        "clean_name": "Lucky Egg",
        "category": "Held Item",
        "desc": "Boosts XP gains by +20% from coding and all activities.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "amulet_coin": {
        "name": "🪙 Amulet Coin",
        "clean_name": "Amulet Coin",
        "category": "Held Item",
        "desc": "Boosts spendable token rewards by +50% from all sources.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "leftovers": {
        "name": "🍎 Leftovers",
        "clean_name": "Leftovers",
        "category": "Held Item",
        "desc": "Protects active companion from daily happiness decay.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "choice_scarf": {
        "name": "🥊 Choice Scarf",
        "clean_name": "Choice Scarf",
        "category": "Held Item",
        "desc": "Speeds up expeditions by +20%, but drains happiness faster.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "exp_share": {
        "name": "🎒 Exp. Share",
        "clean_name": "Exp. Share",
        "category": "Held Item",
        "desc": "Shares 25% of earned XP with inactive roster companions.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "soothe_bell": {
        "name": "🔔 Soothe Bell",
        "clean_name": "Soothe Bell",
        "category": "Held Item",
        "desc": "Doubles happiness gains and halts daily happiness decay.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "scope_lens": {
        "name": "🔍 Scope Lens",
        "clean_name": "Scope Lens",
        "category": "Held Item",
        "desc": "Doubles shiny hatching and encounter chances (2x odds).",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "life_orb": {
        "name": "🔮 Life Orb",
        "clean_name": "Life Orb",
        "category": "Held Item",
        "desc": "Channels +10% bonus token power from your coding activity.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "choice_band": {
        "name": "🥊 Choice Band",
        "clean_name": "Choice Band",
        "category": "Held Item",
        "desc": "Deals +50% more physical attack damage in battles.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "choice_specs": {
        "name": "👓 Choice Specs",
        "clean_name": "Choice Specs",
        "category": "Held Item",
        "desc": "Deals +50% more special attack damage in battles.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "focus_sash": {
        "name": "🎗️ Focus Sash",
        "clean_name": "Focus Sash",
        "category": "Held Item",
        "desc": "Allows companion to endure a lethal blow with 1 HP remaining.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "rocky_helmet": {
        "name": "⛑️ Rocky Helmet",
        "clean_name": "Rocky Helmet",
        "category": "Held Item",
        "desc": "Deals recoil damage to attackers when struck in combat.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "assault_vest": {
        "name": "🦺 Assault Vest",
        "clean_name": "Assault Vest",
        "category": "Held Item",
        "desc": "Reduces incoming combat damage taken by 30%.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "heavy_boots": {
        "name": "🥾 Heavy Boots",
        "clean_name": "Heavy Boots",
        "category": "Held Item",
        "desc": "Grants full immunity against environmental hazards.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "compass_of_deep": {
        "name": "🧭 Compass of Deep",
        "clean_name": "Compass of Deep",
        "category": "Held Item",
        "desc": "Speeds up all expeditions by +25% while equipped.",
        "usage": "Type 'use <id>' to equip to companion.",
    },
    "revitalizing_tonic": {
        "name": "⚗️ Revitalizing Tonic",
        "clean_name": "Revitalizing Tonic",
        "category": "Consumable",
        "desc": "Instantly restores active companion's Happiness to 100%.",
        "usage": "Type 'use <id>' to revitalize active companion.",
    },
    "sacred_ash": {
        "name": "🏺 Sacred Ash",
        "clean_name": "Sacred Ash",
        "category": "Consumable",
        "desc": "Fully revives and heals all Pokémon on your Mt. Silver roster.",
        "usage": "Type 'use <id>' to fully restore battle roster.",
    },
    "warp_whistle": {
        "name": "🌬️ Warp Whistle",
        "clean_name": "Warp Whistle",
        "category": "Field Tech",
        "desc": "Summons a whirlwind that instantly completes all expeditions.",
        "usage": "Type 'use <id>' to finish all active expeditions.",
    },
    "expedition_pass": {
        "name": "🎫 Expedition Pass",
        "clean_name": "Expedition Pass",
        "category": "Field Tech",
        "desc": "Instantly completes the first active expedition.",
        "usage": "Type 'use <id>' to finish first active expedition.",
    },
    "expedition_energy_tonic": {
        "name": "⚡ Energy Tonic",
        "clean_name": "Expedition Energy Tonic",
        "category": "Consumable",
        "desc": "Restores +50% happiness to all companions in party and roster.",
        "usage": "Type 'use <id>' to energize all companions.",
    },
    "expedition_insurance": {
        "name": "📜 Exped. Insurance Policy",
        "clean_name": "Expedition Insurance Policy",
        "category": "Field Tech",
        "desc": "Protects companions from happiness decay for next 3 expeditions.",
        "usage": "Type 'use <id>' to apply 3 insurance charges.",
    },
    "rocket_radar": {
        "name": "📡 Rocket Radar",
        "clean_name": "Rocket Radar",
        "category": "Field Tech",
        "desc": "Grants +50% bonus token yields for your next 3 expeditions.",
        "usage": "Type 'use <id>' to activate 3 radar charges.",
    },
    "metal_coat": {
        "name": "⚙️ Metal Coat",
        "clean_name": "Metal Coat",
        "category": "Syndicate Artifact",
        "desc": "Evolves Onix->Steelix, Scyther->Scizor; or gives +15% Steel dmg.",
        "usage": "Type 'use <id>' to evolve companion or equip for dmg bonus.",
    },
    "kings_rock": {
        "name": "👑 King's Rock",
        "clean_name": "King's Rock",
        "category": "Syndicate Artifact",
        "desc": "Evolves Poliwhirl into Politoed or Slowpoke into Slowking.",
        "usage": "Type 'use <id>' with compatible companion to evolve.",
    },
    "dragon_scale": {
        "name": "🐉 Dragon Scale",
        "clean_name": "Dragon Scale",
        "category": "Syndicate Artifact",
        "desc": "Evolves Seadra into Kingdra.",
        "usage": "Type 'use <id>' with Seadra companion to evolve.",
    },
    "upgrade": {
        "name": "💾 Upgrade",
        "clean_name": "Upgrade",
        "category": "Syndicate Artifact",
        "desc": "Evolves Porygon into Porygon2.",
        "usage": "Type 'use <id>' with Porygon companion to evolve.",
    },
    "dubious_disc": {
        "name": "💿 Dubious Disc",
        "clean_name": "Dubious Disc",
        "category": "Syndicate Artifact",
        "desc": "Evolves Porygon2 into Porygon-Z.",
        "usage": "Type 'use <id>' with Porygon2 companion to evolve.",
    },
    "protector": {
        "name": "🛡️ Protector",
        "clean_name": "Protector",
        "category": "Syndicate Artifact",
        "desc": "Evolves Rhydon into Rhyperior.",
        "usage": "Type 'use <id>' with Rhydon companion to evolve.",
    },
    "electirizer": {
        "name": "🔌 Electirizer",
        "clean_name": "Electirizer",
        "category": "Syndicate Artifact",
        "desc": "Evolves Electabuzz into Electivire.",
        "usage": "Type 'use <id>' with Electabuzz companion to evolve.",
    },
    "magmarizer": {
        "name": "🌋 Magmarizer",
        "clean_name": "Magmarizer",
        "category": "Syndicate Artifact",
        "desc": "Evolves Magmar into Magmortar.",
        "usage": "Type 'use <id>' with Magmar companion to evolve.",
    },
    "reaper_cloth": {
        "name": "👻 Reaper Cloth",
        "clean_name": "Reaper Cloth",
        "category": "Syndicate Artifact",
        "desc": "Evolves Dusclops into Dusknoir.",
        "usage": "Type 'use <id>' with Dusclops companion to evolve.",
    },
    "prism_scale": {
        "name": "✨ Prism Scale",
        "clean_name": "Prism Scale",
        "category": "Syndicate Artifact",
        "desc": "Evolves Feebas into Milotic.",
        "usage": "Type 'use <id>' with Feebas companion to evolve.",
    },
    "water_stone": {
        "name": "💎 Water Stone",
        "clean_name": "Water Stone",
        "category": "Evolution Stone",
        "desc": "Evolves compatible Water species (Eevee, Poliwhirl, Shellder).",
        "usage": "Type 'use <id>' with companion active to evolve.",
    },
    "fire_stone": {
        "name": "💎 Fire Stone",
        "clean_name": "Fire Stone",
        "category": "Evolution Stone",
        "desc": "Evolves compatible Fire species (Eevee, Vulpix, Growlithe).",
        "usage": "Type 'use <id>' with companion active to evolve.",
    },
    "thunder_stone": {
        "name": "💎 Thunder Stone",
        "clean_name": "Thunder Stone",
        "category": "Evolution Stone",
        "desc": "Evolves compatible Electric species (Pikachu, Eevee, Eelektrik).",
        "usage": "Type 'use <id>' with companion active to evolve.",
    },
    "leaf_stone": {
        "name": "💎 Leaf Stone",
        "clean_name": "Leaf Stone",
        "category": "Evolution Stone",
        "desc": "Evolves compatible Grass species (Gloom, Weepinbell, Exeggcute).",
        "usage": "Type 'use <id>' with companion active to evolve.",
    },
    "moon_stone": {
        "name": "💎 Moon Stone",
        "clean_name": "Moon Stone",
        "category": "Evolution Stone",
        "desc": "Evolves compatible species (Nidorina, Nidorino, Clefairy).",
        "usage": "Type 'use <id>' with companion active to evolve.",
    },
    "sun_stone": {
        "name": "💎 Sun Stone",
        "clean_name": "Sun Stone",
        "category": "Evolution Stone",
        "desc": "Evolves compatible species (Gloom, Sunkern, Cottonee, Petilil).",
        "usage": "Type 'use <id>' with companion active to evolve.",
    },
    "ice_stone": {
        "name": "💎 Ice Stone",
        "clean_name": "Ice Stone",
        "category": "Evolution Stone",
        "desc": "Evolves compatible Ice species (Alolan Vulpix, Alolan Sandshrew).",
        "usage": "Type 'use <id>' with companion active to evolve.",
    },
    "shiny_stone": {
        "name": "💎 Shiny Stone",
        "clean_name": "Shiny Stone",
        "category": "Evolution Stone",
        "desc": "Evolves compatible species (Togetic, Roselia, Minccino, Floette).",
        "usage": "Type 'use <id>' with companion active to evolve.",
    },
    "dusk_stone": {
        "name": "💎 Dusk Stone",
        "clean_name": "Dusk Stone",
        "category": "Evolution Stone",
        "desc": "Evolves compatible species (Murkrow, Misdreavus, Lampent).",
        "usage": "Type 'use <id>' with companion active to evolve.",
    },
    "dawn_stone": {
        "name": "💎 Dawn Stone",
        "clean_name": "Dawn Stone",
        "category": "Evolution Stone",
        "desc": "Evolves compatible species (Kirlia male, Snorunt female).",
        "usage": "Type 'use <id>' with companion active to evolve.",
    },
    "fake_rare_candy": {
        "name": "🍬 \"Rare Candy\"",
        "clean_name": "\"Rare Candy\"",
        "category": "Contraband / Fake",
        "desc": "Chalk candy manufactured by Team Rocket grunts. Useless!",
        "usage": "Type 'sell <id>' to dispose for 1 token.",
    },
    "fake_master_ball": {
        "name": "🌟 \"Master Ball\"",
        "clean_name": "\"Master Ball\"",
        "category": "Contraband / Fake",
        "desc": "Painted ping pong ball sold as a Master Ball. Complete fraud!",
        "usage": "Type 'sell <id>' to dispose for 1 token.",
    },
    "fake_thunder_stone": {
        "name": "⚡ \"Thunder Stone\"",
        "clean_name": "\"Thunder Stone\"",
        "category": "Contraband / Fake",
        "desc": "Yellow plastic rock with zero evolutionary energy.",
        "usage": "Type 'sell <id>' to dispose for 1 token.",
    },
    "fake_water_stone": {
        "name": "💧 \"Water Stone\"",
        "clean_name": "\"Water Stone\"",
        "category": "Contraband / Fake",
        "desc": "Blue glass marble sold as a genuine Water Stone.",
        "usage": "Type 'sell <id>' to dispose for 1 token.",
    },
    "fake_fire_stone": {
        "name": "🔥 \"Fire Stone\"",
        "clean_name": "\"Fire Stone\"",
        "category": "Contraband / Fake",
        "desc": "Red painted pebble with zero heat or evolutionary energy.",
        "usage": "Type 'sell <id>' to dispose for 1 token.",
    },
    "fake_ancient_map": {
        "name": "📜 \"Ancient Map\"",
        "clean_name": "\"Ancient Map\"",
        "category": "Contraband / Fake",
        "desc": "Crude crayon drawing on aged parchment leading nowhere.",
        "usage": "Type 'sell <id>' to dispose for 1 token.",
    },
    "fake_gold_nugget": {
        "name": "🪙 \"Gold Nugget\"",
        "clean_name": "\"Gold Nugget\"",
        "category": "Contraband / Fake",
        "desc": "Pyrite fool's gold that sells for 1 token.",
        "usage": "Type 'sell <id>' to dispose for 1 token.",
    },
    "fake_exp_share": {
        "name": "🎒 \"Exp. Share\"",
        "clean_name": "\"Exp. Share\"",
        "category": "Contraband / Fake",
        "desc": "Empty child's backpack. Shares no experience whatsoever.",
        "usage": "Type 'sell <id>' to dispose for 1 token.",
    },
    "fake_soothe_bell": {
        "name": "🔔 \"Soothe Bell\"",
        "clean_name": "\"Soothe Bell\"",
        "category": "Contraband / Fake",
        "desc": "Harsh grating cowbell. Actually lowers companion happiness!",
        "usage": "Type 'sell <id>' to dispose for 1 token.",
    },
    "fake_scope_lens": {
        "name": "🔍 \"Scope Lens\"",
        "clean_name": "\"Scope Lens\"",
        "category": "Contraband / Fake",
        "desc": "Cracked magnifying glass with no shiny-boosting properties.",
        "usage": "Type 'sell <id>' to dispose for 1 token.",
    },
    "fake_focus_sash": {
        "name": "🎗️ \"Focus Sash\"",
        "clean_name": "\"Focus Sash\"",
        "category": "Contraband / Fake",
        "desc": "Frayed ribbon that snaps immediately on first impact.",
        "usage": "Type 'sell <id>' to dispose for 1 token.",
    },
    "fake_mega_stone": {
        "name": "🔮 \"Charizardite\"",
        "clean_name": "\"Charizardite\"",
        "category": "Contraband / Fake",
        "desc": "Cheap resin replica. Does not trigger Mega Evolution.",
        "usage": "Type 'sell <id>' to dispose for 1 token.",
    },
    "rocket_master_ball": {
        "name": "🔮 Rocket Master Ball",
        "clean_name": "Rocket Master Ball",
        "category": "Rocket Tech",
        "desc": "Experimental capture device crafted by Team Rocket scientists.",
        "usage": "Rare syndicate prototype item.",
    },
}


def resolve_bag_item(app, choice: str) -> Optional[str]:
    """Resolves user input string or index to canonical bag item key."""
    choice = choice.strip().strip("[]").lower()
    if not choice:
        return None
    bag_id_map = getattr(app, "bag_id_map", {})
    if choice in bag_id_map:
        return bag_id_map[choice]
    if choice in BAG_CATALOG_MAP:
        return BAG_CATALOG_MAP[choice]
    if choice in BAG_KEY_TO_ID:
        return choice

    # Numeric choices must only resolve via bag_id_map or BAG_CATALOG_MAP.
    # Never do substring or name matching on numbers (e.g. '5' must not match '50% tokens' in Amulet Coin).
    if choice.isdigit():
        return None

    choice_norm = choice.replace(" ", "_").replace("-", "_")
    if choice_norm in BAG_KEY_TO_ID:
        return choice_norm
    if choice_norm in BAG_CATALOG_MAP:
        return BAG_CATALOG_MAP[choice_norm]
    for s in ItemKind:
        if choice == s.value or choice == s.value.replace("_", "") or choice_norm == s.value:
            return s.value
    inv = app.engine.state.get("inventory", {}) if hasattr(app, "engine") else {}
    if choice in inv:
        return choice
    if choice_norm in inv:
        return choice_norm
    for cid, k, name in BAG_CATALOG:
        c_name = "".join(ch for ch in name.lower() if ch.isalnum() or ch.isspace()).strip()
        if choice == c_name or choice == c_name.replace(" ", "_"):
            return k
        if choice in c_name.split():
            return k
    return None
