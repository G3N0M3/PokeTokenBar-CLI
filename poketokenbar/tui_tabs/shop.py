import random
import sys
import textwrap
from typing import Optional, Tuple, Dict, List, Any
from poketokenbar.game.models import ItemKind, Rarity
from poketokenbar.utils.formatting import format_tokens

HEADER = "\033[95m\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

BAG_CATALOG = [
    ("1", "rare_candy", "🍬 Rare Candy"),
    ("2", "mint", "🌿 Mint"),
    ("3", "berry_oran", "🫐 Oran Berry"),
    ("4", "berry_golden", "🍇 Golden Razz"),
    ("6", "poke_flute", "🪈 Poké Flute (Summons Boss)"),
    ("7", "master_ball", "🌟 Master Ball (Hatch Shiny)"),
    ("8", "map_fragment", "📜 Map"),
    ("9", "expedition_license", "📜 Exped. License (+10 slots)"),
    ("10", "everstone", "🪨 Everstone (No evolution)"),
    ("11", "lucky_egg", "🍀 Lucky Egg (+20% XP)"),
    ("12", "amulet_coin", "🪙 Amulet Coin (+50% tokens)"),
    ("13", "leftovers", "🍎 Leftovers (No hap. decay)"),
    ("14", "choice_scarf", "🥊 Choice Scarf (+20% spd)"),
    ("15", "exp_share", "🎒 Exp. Share (XP Sharing)"),
    ("16", "soothe_bell", "🔔 Soothe Bell (Hap. Boost)"),
    ("17", "scope_lens", "🔍 Scope Lens (2x Shiny)"),
    ("18", "life_orb", "🔮 Life Orb (+10% Tokens)"),
    ("19", "choice_band", "🥊 Choice Band (+50% Dmg)"),
    # Combat held items
    ("20", "choice_specs", "👓 Choice Specs (+50% SpAtk)"),
    ("21", "focus_sash", "🎗️ Focus Sash (Endure 1 HP)"),
    ("22", "rocky_helmet", "⛑️ Rocky Helmet (Recoil)"),
    ("23", "assault_vest", "🦺 Assault Vest (-30% SpDef)"),
    ("24", "heavy_boots", "🥾 Heavy Boots (Hazard Guard)"),
    ("25", "compass_of_deep", "🧭 Compass of Deep (+25% Spd)"),
    # Consumables & Field Tech
    ("26", "revitalizing_tonic", "⚗️ Revitalizing Tonic (100% Hap)"),
    ("27", "sacred_ash", "🏺 Sacred Ash (Full Red Revive)"),
    ("28", "warp_whistle", "🌬️ Warp Whistle (Finish All)"),
    ("29", "expedition_pass", "🎫 Expedition Pass"),
    ("30", "expedition_energy_tonic", "⚡ Energy Tonic (+50% Hap All)"),
    ("31", "expedition_insurance", "📜 Exped. Insurance Policy"),
    ("32", "rocket_radar", "📡 Rocket Radar (+50% Tokens)"),
    # Syndicate Evolution Artifacts
    ("33", "metal_coat", "⚙️ Metal Coat"),
    ("34", "kings_rock", "👑 King's Rock"),
    ("35", "dragon_scale", "🐉 Dragon Scale"),
    ("36", "upgrade", "💾 Upgrade"),
    ("37", "dubious_disc", "💿 Dubious Disc"),
    ("38", "protector", "🛡️ Protector"),
    ("39", "electirizer", "🔌 Electirizer"),
    ("40", "magmarizer", "🌋 Magmarizer"),
    ("41", "reaper_cloth", "👻 Reaper Cloth"),
    ("42", "prism_scale", "✨ Prism Scale"),
    # Evolution Stones
    ("43", "water_stone", "💎 Water Stone"),
    ("44", "fire_stone", "💎 Fire Stone"),
    ("45", "thunder_stone", "💎 Thunder Stone"),
    ("46", "leaf_stone", "💎 Leaf Stone"),
    ("47", "moon_stone", "💎 Moon Stone"),
    ("48", "sun_stone", "💎 Sun Stone"),
    ("49", "ice_stone", "💎 Ice Stone"),
    ("50", "shiny_stone", "💎 Shiny Stone"),
    ("51", "dusk_stone", "💎 Dusk Stone"),
    ("52", "dawn_stone", "💎 Dawn Stone"),
    # Fake Contraband items
    ("53", "fake_rare_candy", "🍬 \"Rare Candy\""),
    ("54", "fake_master_ball", "🌟 \"Master Ball\""),
    ("55", "fake_thunder_stone", "⚡ \"Thunder Stone\""),
    ("56", "fake_water_stone", "💧 \"Water Stone\""),
    ("57", "fake_fire_stone", "🔥 \"Fire Stone\""),
    ("58", "fake_ancient_map", "📜 \"Ancient Map\""),
    ("59", "fake_gold_nugget", "🪙 \"Gold Nugget\""),
    ("60", "fake_exp_share", "🎒 \"Exp. Share\""),
    ("61", "fake_soothe_bell", "🔔 \"Soothe Bell\""),
    ("62", "fake_scope_lens", "🔍 \"Scope Lens\""),
    ("63", "fake_focus_sash", "🎗️ \"Focus Sash\""),
    ("64", "fake_mega_stone", "🔮 \"Charizardite\""),
    # Special Rocket Bag items
    ("65", "dark_gene_catalyst", "🧬 Dark Gene Catalyst"),
    ("66", "rocket_master_ball", "🔮 Rocket Master Ball"),
]

BAG_CATALOG_MAP = {cid: key for cid, key, _ in BAG_CATALOG}
BAG_KEY_TO_ID = {key: cid for cid, key, _ in BAG_CATALOG}

ITEM_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "rare_candy": {
        "name": "🍬 Rare Candy",
        "clean_name": "Rare Candy",
        "category": "Consumable",
        "desc": "Instantly grants +60% of shop cost in XP to active companion.",
        "usage": "Type 'use <id> [qty]' to feed to active companion.",
    },
    "mint": {
        "name": "🌿 Mint",
        "clean_name": "Mint",
        "category": "Consumable",
        "desc": "Rerolls active companion's nature, altering stat multipliers.",
        "usage": "Type 'use <id>' to reroll active companion's nature.",
    },
    "berry_oran": {
        "name": "🫐 Oran Berry",
        "clean_name": "Oran Berry",
        "category": "Consumable",
        "desc": "Restores +25% Happiness per berry to active companion.",
        "usage": "Type 'use <id> [qty]' to feed to active companion.",
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
    "dark_gene_catalyst": {
        "name": "🧬 Dark Gene Catalyst",
        "clean_name": "Dark Gene Catalyst",
        "category": "Rocket Tech",
        "desc": "Mutates active companion into its next evolutionary stage.",
        "usage": "Type 'use <id>' with active companion to force evolution.",
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
    choice = choice.strip().lower()
    if not choice:
        return None
    bag_id_map = getattr(app, "bag_id_map", {})
    if choice in bag_id_map:
        return bag_id_map[choice]
    if choice in BAG_CATALOG_MAP:
        return BAG_CATALOG_MAP[choice]
    if choice in BAG_KEY_TO_ID:
        return choice
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
        if choice == c_name or choice in c_name:
            return k
    return None

def render_shop_tab(app):
    if getattr(app, "shop_view", "normal") == "black_market":
        _render_black_market_view(app)
        return

    avail = app.engine.available_tokens
    inv = app.engine.state.get("inventory", {})
    diff = app.engine.current_difficulty
    prices = diff.shop_prices
    has_devon = app.engine.has_perk("devon")
    disc = 0.90 if has_devon else 1.0

    p_rc = format_tokens(int(prices["rare_candy"] * disc))
    p_rc_xp = format_tokens(int(prices["rare_candy"] * 0.6))
    p_mint = format_tokens(int(prices["mint"] * disc))
    p_egg1 = format_tokens(int(prices["egg_normal"] * disc))
    p_egg2 = format_tokens(int(prices["egg_uncommon"] * disc))

    sys.stdout.write(f"\n  {BOLD}{YELLOW}🛒 Token Shop & Bag{RESET}  (Available Spendable Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET})\n")
    if has_devon:
        sys.stdout.write(f"  {BOLD}{GREEN}💼 Devon Corp Active: -10% discount applied to all shop items!{RESET}\n")

    bm = app.engine.get_or_init_black_market()
    if bm.get("natural_open"):
        sys.stdout.write(f"  {BOLD}{YELLOW}🕶️ [A faint \"R\" is etched beneath the counter. Type '{BOLD}{CYAN}black{RESET}{BOLD}{YELLOW}']{RESET}\n")
    sys.stdout.write("\n")

    sys.stdout.write(f"  {BOLD}Shop Items (Type 'buy <number> [qty]' to purchase):{RESET}\n")
    sys.stdout.write(f"  [1] 🍬 Rare Candy     - Cost: {p_rc:<6} tokens  (Grants +{p_rc_xp} XP)\n")
    sys.stdout.write(f"  [2] 🌿 Mint           - Cost: {p_mint:<6} tokens  (Rerolls nature)\n")
    sys.stdout.write(f"  [3] 🥚 Pokémon Egg    - Cost: {p_egg1:<6} tokens  (Incubate new egg)\n")
    sys.stdout.write(f"  [4] 🥚 Uncommon Egg   - Cost: {p_egg2:<6} tokens  (Guarantees Uncommon+ egg)\n")
    sys.stdout.write(f"  [5] 🫐 Oran Berry     - Cost: {format_tokens(int(1_000_000 * disc)):<6} tokens  (+25% Happiness)\n")
    sys.stdout.write(f"  [6] 🍇 Golden Razz    - Cost: {format_tokens(int(5_000_000 * disc)):<6} tokens  (Shiny egg odds 1/24)\n")
    sys.stdout.write(f"  [7] 📜 Exped. License - Cost: {format_tokens(int(200_000_000 * disc)):<6} tokens  (+10 expedition slots)\n")
    sys.stdout.write(f"  [8] 🪨 Everstone      - Cost: {format_tokens(int(500_000 * disc)):<6} tokens  (Prevents evolution)\n")
    sys.stdout.write(f"  [9] 🍀 Lucky Egg      - Cost: {format_tokens(int(5_000_000 * disc)):<6} tokens  (+20% XP gain)\n")
    sys.stdout.write(f"  [10] 🪙 Amulet Coin   - Cost: {format_tokens(int(2_000_000 * disc)):<6} tokens  (+50% token rewards)\n")
    sys.stdout.write(f"  [11] 🍎 Leftovers     - Cost: {format_tokens(int(2_000_000 * disc)):<6} tokens  (Protects happiness)\n")
    sys.stdout.write(f"  [12] 🥊 Choice Scarf  - Cost: {format_tokens(int(2_000_000 * disc)):<6} tokens  (+20% exp spd, hap-)\n\n")

    sys.stdout.write(f"  {BOLD}Your Bag (Type 'use <id>', 'sell <id>', 'help <id>', or 'unequip'):{RESET}\n")
    
    bag_items = []
    seen_keys = set()
    app.bag_id_map = {}

    for id_str, k, name in BAG_CATALOG:
        qty = inv.get(k, 0)
        if qty <= 0 and isinstance(inv.get("items"), dict):
            qty = inv["items"].get(k, 0)
        if qty > 0:
            bag_items.append((name, id_str, qty))
            app.bag_id_map[id_str] = k
            app.bag_id_map[k] = k
            seen_keys.add(k)

    # Dynamic fallback for uncataloged items (excluding mega stones)
    next_dyn_id = 67
    for k, v in inv.items():
        if k in seen_keys or k == "items":
            continue
        if k == "mega_stone" or k.startswith("mega_stone_"):
            continue
        if isinstance(v, int) and v > 0:
            dyn_id = str(next_dyn_id)
            next_dyn_id += 1
            disp_name = k.replace("_", " ").title()
            bag_items.append((f"📦 {disp_name}", dyn_id, v))
            app.bag_id_map[dyn_id] = k
            app.bag_id_map[k] = k

    page_size = app.engine.state.get("page_size_bag", 10)
    total_pages = max(1, (len(bag_items) - 1) // page_size + 1)
    if not hasattr(app, 'shop_page') or not isinstance(app.shop_page, int): app.shop_page = 1
    app.shop_page = max(1, min(app.shop_page, total_pages))
    
    if not bag_items:
        sys.stdout.write("  (Your bag is empty)\n\n")
    else:
        start_idx = (app.shop_page - 1) * page_size
        end_idx = start_idx + page_size
        for name, cmd_id, qty in bag_items[start_idx:end_idx]:
            sys.stdout.write(f"  [{cmd_id}] {name}: {qty} owned\n")
            
        if total_pages > 1:
            sys.stdout.write(f"\n  ➔ Page {app.shop_page}/{total_pages} - Type '{BOLD}n{RESET}', '{BOLD}p{RESET}', or '{BOLD}page <N>{RESET}' to navigate bag!\n")
        sys.stdout.write("\n")

def _render_black_market_view(app):
    avail = app.engine.available_tokens
    has_devon = app.engine.has_perk("devon")
    disc = 0.90 if has_devon else 1.0

    sys.stdout.write(f"\n  {BOLD}{YELLOW}🕶️ Rocket Syndicate — Underground Black Market{RESET}\n")
    sys.stdout.write(f"  Available Spendable Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n")
    if has_devon:
        sys.stdout.write(f"  {BOLD}{GREEN}💼 Devon Corp Active: -10% discount applied to deals!{RESET}\n")

    bm = app.engine.get_or_init_black_market()
    is_open = bm.get("natural_open", False) or getattr(app, "black_market_session", False) or bm.get("is_open", False)
    if not is_open:
        sys.stdout.write(f"\n  {YELLOW}The backroom is completely silent.{RESET}\n")
        sys.stdout.write(f"  Rocket Syndicate grunts operate discretely (5% daily chance).\n")
        if random.random() < 0.10:
            sys.stdout.write(f"  💡 {CYAN}Rumor: A secret entrance is hidden behind a poster{RESET}\n")
            sys.stdout.write(f"     {CYAN}in the Game Corner slot machines...{RESET}\n")
        sys.stdout.write(f"\n  ➔ Type '{BOLD}back{RESET}' to return to regular Token Shop.\n\n")
        return

    sys.stdout.write(f"\n  {BOLD}Today's Smuggled Contraband & Limited Offers:{RESET}\n")
    deals = bm.get("deals", [])
    for d in deals:
        did = d.get("id", 1)
        name = d.get("name", "Unknown Deal")
        cost = int(d.get("price", 0) * disc)
        cost_str = format_tokens(cost)
        stock = d.get("stock", 0)
        max_s = d.get("max_stock", 1)
        badge = d.get("badge", "")
        if stock > 0:
            stock_str = f"Stock: {stock}/{max_s}"
        else:
            stock_str = f"{RED}SOLD OUT{RESET}"
        badge_str = f" {YELLOW}[{badge}]{RESET}" if badge else ""
        sys.stdout.write(f"  [{did}] {name} - {BOLD}{CYAN}{cost_str}{RESET} ({stock_str}){badge_str}\n")

    sys.stdout.write(f"\n  {BOLD}Commands:{RESET}\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}buy <id> [qty]{RESET}' to purchase (e.g. 'buy 1')\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}back{RESET}' to return\n\n")

def handle_deal_buy(app, cmd: str):
    parts = cmd.split()
    if len(parts) < 2:
        app.message = "Usage: buy <id> [qty] (e.g. 'buy 1')"
        return
    deal_id = parts[1]
    qty = 1
    if len(parts) >= 3:
        try:
            qty = int(parts[2])
            if qty <= 0:
                app.message = "Quantity must be greater than 0."
                return
        except ValueError:
            app.message = "Invalid quantity."
            return
    ok, msg = app.engine.buy_black_market_deal(deal_id, qty)
    app.message = msg

def handle_shop_buy(app, cmd: str):
    if getattr(app, "shop_view", "normal") == "black_market":
        handle_deal_buy(app, cmd)
        return

    parts = cmd.split()
    choice = parts[1] if len(parts) > 1 else ""
    qty = 1
    if len(parts) >= 3:
        try:
            qty = int(parts[2])
        except ValueError:
            app.message = "Invalid quantity."
            return

    if choice == "1":
        ok, msg = app.engine.buy_item(ItemKind.RARE_CANDY, qty)
    elif choice == "2":
        ok, msg = app.engine.buy_item(ItemKind.MINT, qty)
    elif choice == "3":
        if qty > 1:
            app.message = "You can only hold one egg!"
            return
        ok, msg = app.engine.buy_egg(None)
    elif choice == "4":
        if qty > 1:
            app.message = "You can only hold one egg!"
            return
        ok, msg = app.engine.buy_egg(Rarity.UNCOMMON)
    elif choice == "5":
        ok, msg = app.engine.buy_item(ItemKind.BERRY_ORAN, qty)
    elif choice == "6":
        ok, msg = app.engine.buy_item(ItemKind.BERRY_GOLDEN, qty)
    elif choice == "7":
        ok, msg = app.engine.buy_item(ItemKind.EXPEDITION_LICENSE, qty)
    elif choice == "8":
        ok, msg = app.engine.buy_item(ItemKind.EVERSTONE, qty)
    elif choice == "9":
        ok, msg = app.engine.buy_item(ItemKind.LUCKY_EGG, qty)
    elif choice == "10":
        ok, msg = app.engine.buy_item(ItemKind.AMULET_COIN, qty)
    elif choice == "11":
        ok, msg = app.engine.buy_item(ItemKind.LEFTOVERS, qty)
    elif choice == "12":
        ok, msg = app.engine.buy_item(ItemKind.CHOICE_SCARF, qty)
    else:
        ok, msg = False, "Invalid shop selection."
    app.message = msg

def handle_bag_use(app, cmd: str):
    parts = cmd.split()
    if not parts:
        return
    if parts[0] == "unequip":
        ok, msg = app.engine.unequip_item()
        app.message = msg
        return
        
    choice = parts[1] if len(parts) > 1 else ""
    qty = 1
    if len(parts) > 2:
        try:
            qty = int(parts[2])
            if qty <= 0:
                app.message = "Quantity must be greater than 0."
                return
        except ValueError:
            app.message = "Invalid quantity."
            return

    target_key = resolve_bag_item(app, choice)
    if not target_key:
        if choice.startswith("mega_stone") or choice == "mega_stone":
            app.message = "Mega Stones must be used from Tab [8] Mega Evolution!"
        else:
            app.message = "Invalid bag selection."
        return

    if target_key == "map_fragment" or choice == "8":
        app.message = "Maps are used automatically when dispatching expeditions to Spear Pillar (3x required)!"
        return
    elif target_key == "mega_stone" or target_key.startswith("mega_stone_"):
        app.message = "Mega Stones must be used from Tab [8] Mega Evolution!"
        return

    try:
        item_target = ItemKind(target_key)
    except ValueError:
        item_target = target_key

    ok, msg = app.engine.use_item(item_target, qty)
    app.message = msg

def handle_bag_sell(app, cmd: str):
    parts = cmd.split()
    choice = parts[1] if len(parts) > 1 else ""
    qty = 1
    if len(parts) >= 3:
        try:
            qty = int(parts[2])
            if qty <= 0:
                app.message = "Quantity must be greater than 0."
                return
        except ValueError:
            app.message = "Invalid quantity."
            return

    target_key = resolve_bag_item(app, choice)
    if not target_key:
        if choice.startswith("mega_stone") or choice == "mega_stone":
            app.message = "Mega Stones are unique key artifacts and cannot be sold!"
        else:
            app.message = "Invalid bag selection."
        return

    if target_key == "mega_stone" or target_key.startswith("mega_stone_"):
        app.message = "Mega Stones are unique key artifacts and cannot be sold!"
        return

    inv = app.engine.state.get("inventory", {})
    count = inv.get(target_key, 0)
    if count <= 0 and isinstance(inv.get("items"), dict):
        count = inv["items"].get(target_key, 0)

    try:
        item_kind = ItemKind(target_key)
        item_name = item_kind.name_en
        item_emoji = item_kind.emoji
        sell_target = item_kind
    except ValueError:
        item_kind = None
        item_name = target_key.replace("_", " ").title()
        item_emoji = "📦"
        sell_target = target_key

    if count < qty:
        app.message = f"You don't have {qty}x {item_name} in your Bag to sell!"
        return

    if target_key.startswith("fake_"):
        sell_value = 1 * qty
    elif item_kind:
        cost = item_kind.price_for(app.engine.current_difficulty)
        sell_value = max(1, int(cost * 0.8)) * qty
    else:
        sell_value = 100_000 * qty

    sys.stdout.write(f"\n  {BOLD}{YELLOW}💰 SELL CONFIRMATION{RESET}\n")
    sys.stdout.write(f"  Sell {qty}x {item_name} ({item_emoji}) for +{format_tokens(sell_value)} Tokens?\n")
    sys.stdout.write(f"  Confirm (y/n)> ")
    sys.stdout.flush()
    
    ans = sys.stdin.readline().strip().lower()
    if ans in ["y", "yes"]:
        ok, msg = app.engine.sell_item(sell_target, qty)
        app.message = msg
    else:
        app.message = f"Canceled selling {qty}x {item_name}."

def handle_bag_help(app, cmd: str):
    parts = cmd.strip().split(maxsplit=1)
    if len(parts) < 2:
        app.message = "Usage: help <id> (e.g. 'help 16' or 'help life_orb')"
        return

    choice = parts[1].strip()
    target_key = resolve_bag_item(app, choice)
    if not target_key:
        app.message = f"Unknown item '{choice}'. Check your Bag item number."
        return

    info = ITEM_DESCRIPTIONS.get(target_key)
    if info:
        name = info["name"]
        clean_name = info["clean_name"]
        category = info["category"]
        desc = info["desc"]
        usage_tpl = info["usage"]
    elif target_key.startswith("mega_stone"):
        clean_name = target_key.replace("_", " ").title()
        name = f"🔮 {clean_name}"
        category = "Mega Stone"
        desc = "Key artifact used to trigger Mega Evolution."
        usage_tpl = "Navigate to Tab [8] Mega Evolution to activate."
    else:
        clean_name = target_key.replace("_", " ").title()
        name = f"📦 {clean_name}"
        category = "Item"
        desc = "An item stored in your Bag."
        usage_tpl = "Type 'use <id>' or 'sell <id>'."

    # Determine ownership: item must be in inventory, held by active companion, or held in roster
    inv = app.engine.state.get("inventory", {}) if hasattr(app, "engine") else {}
    count = inv.get(target_key, 0)
    if count <= 0 and isinstance(inv.get("items"), dict):
        count = inv["items"].get(target_key, 0)

    # Check mega stones if applicable
    if target_key.startswith("mega_stone") and hasattr(app, "engine"):
        owned_megas = app.engine.state.get("mega_stones", [])
        if target_key in owned_megas:
            count = max(count, 1)

    active = getattr(app.engine, "active_mon", None) if hasattr(app, "engine") else None
    companion_name = ""
    if active and hasattr(app.engine, "api"):
        try:
            companion_name = app.engine.api.get_species_name(active.current_id)
        except Exception:
            companion_name = "companion"

    is_held = (active is not None and getattr(active, "held_item", None) == target_key)

    # Check roster in dex
    held_by_roster = False
    roster_holder = ""
    if not is_held and hasattr(app, "engine"):
        dex = app.engine.state.get("dex", [])
        for d in dex:
            mst = d.get("mon_state")
            if isinstance(mst, dict) and mst.get("held_item") == target_key:
                held_by_roster = True
                sp_id = d.get("species_id", d.get("base_id"))
                if hasattr(app.engine, "api"):
                    try:
                        roster_holder = app.engine.api.get_species_name(sp_id)
                    except Exception:
                        roster_holder = "roster Pokémon"
                else:
                    roster_holder = "roster Pokémon"
                break

    if count <= 0 and not is_held and not held_by_roster:
        app.message = f"You do not own {clean_name} in your Bag!"
        return

    # Determine displayed ID for usage prompt
    display_id = BAG_KEY_TO_ID.get(target_key, target_key)
    bag_id_map = getattr(app, "bag_id_map", {})
    if choice.isdigit() and bag_id_map.get(choice) == target_key:
        display_id = choice
    else:
        for k_id, k_val in bag_id_map.items():
            if k_val == target_key and k_id.isdigit():
                display_id = k_id
                break

    usage = usage_tpl.replace("<id>", display_id)

    # Ownership status
    if is_held and count > 0:
        status = f"({count} in Bag, held by {companion_name})"
    elif is_held:
        status = f"(Held by {companion_name})"
        if category == "Held Item":
            usage = "Type 'unequip' to remove from companion."
    elif held_by_roster:
        if count > 0:
            status = f"({count} in Bag, held by {roster_holder})"
        else:
            status = f"(Held by {roster_holder})"
    else:
        status = f"(Owned: {count})"

    lines = [f"{name}  [{category}]  {status}"]
    for sub in textwrap.wrap(f"Effect: {desc}", width=62):
        lines.append(f"  {sub}")
    for sub in textwrap.wrap(f"Action: {usage}", width=62):
        lines.append(f"  {sub}")

    app.message = "\n".join(lines)
