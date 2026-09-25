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

def render_shop_tab(app):
    if getattr(app, "shop_view", "normal") == "black_market":
        _render_black_market_view(app)
        return

    avail = app.engine.available_tokens
    inv = app.engine.state.get("inventory", {})
    diff = app.engine.current_difficulty
    prices = diff.shop_prices
    devon_mult = app.engine.get_devon_multiplier()
    disc = devon_mult
    devon_rank, devon_tier = app.engine.get_corp_rank("devon")
    devon_disc_pct = app.engine.get_devon_discount_pct()

    p_rc = format_tokens(int(prices["rare_candy"] * disc))
    p_rc_xp = format_tokens(int(prices["rare_candy"] * 0.6))
    p_egg1 = format_tokens(int(prices["egg_normal"] * disc))
    p_egg2 = format_tokens(int(prices["egg_uncommon"] * disc))

    sys.stdout.write(f"\n  {BOLD}{YELLOW}🛒 Token Shop & Bag{RESET}  (Available Spendable Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET})\n")
    if devon_rank > 0:
        sys.stdout.write(f"  {BOLD}{GREEN}💼 Devon Corp [{devon_tier.upper()}]: -{devon_disc_pct}% discount applied to shop items!{RESET}\n")

    bm = app.engine.get_or_init_black_market()
    if bm.get("natural_open"):
        sys.stdout.write(f"  {BOLD}{YELLOW}🕶️ [A faint \"R\" is etched beneath the counter. Type '{BOLD}{CYAN}black{RESET}{BOLD}{YELLOW}']{RESET}\n")
    sys.stdout.write("\n")

    sys.stdout.write(f"  {BOLD}Shop Items (Type 'buy <number> [qty]' to purchase):{RESET}\n")
    sys.stdout.write(f"  [1] 🍬 Rare Candy     - Cost: {p_rc:<6} tokens  (Grants +{p_rc_xp} XP)\n")
    sys.stdout.write(f"  [2] 🥚 Pokémon Egg    - Cost: {p_egg1:<6} tokens  (Incubate new egg)\n")
    sys.stdout.write(f"  [3] 🥚 Uncommon Egg   - Cost: {p_egg2:<6} tokens  (Guarantees Uncommon+ egg)\n")
    sys.stdout.write(f"  [4] 🫐 Oran Berry     - Cost: {format_tokens(int(1_000_000 * disc)):<6} tokens  (+25% Happiness)\n")
    sys.stdout.write(f"  [5] 🍇 Golden Razz    - Cost: {format_tokens(int(5_000_000 * disc)):<6} tokens  (Shiny egg odds 1/24)\n")
    sys.stdout.write(f"  [6] 📜 Exped. License - Cost: {format_tokens(int(200_000_000 * disc)):<6} tokens  (+10 expedition slots)\n")
    sys.stdout.write(f"  [7] 🪨 Everstone      - Cost: {format_tokens(int(500_000 * disc)):<6} tokens  (Prevents evolution)\n")
    sys.stdout.write(f"  [8] 🍀 Lucky Egg      - Cost: {format_tokens(int(5_000_000 * disc)):<6} tokens  (+20% XP gain)\n")
    sys.stdout.write(f"  [9] 🪙 Amulet Coin   - Cost: {format_tokens(int(2_000_000 * disc)):<6} tokens  (+50% token rewards)\n")
    sys.stdout.write(f"  [10] 🍎 Leftovers     - Cost: {format_tokens(int(2_000_000 * disc)):<6} tokens  (Protects happiness)\n")
    sys.stdout.write(f"  [11] 🥊 Choice Scarf  - Cost: {format_tokens(int(2_000_000 * disc)):<6} tokens  (+20% exp spd, hap-)\n\n")

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

    # Dynamic fallback for uncataloged items (excluding mega stones, legacy mint, and armory tech)
    next_dyn_id = max((int(cid) for cid, _, _ in BAG_CATALOG if cid.isdigit()), default=64) + 1
    for k, v in inv.items():
        if k in seen_keys or k in ["items", "mint", "dark_gene_catalyst", "catalyst"]:
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
    devon_mult = app.engine.get_devon_multiplier()
    disc = devon_mult
    devon_rank, devon_tier = app.engine.get_corp_rank("devon")
    devon_disc_pct = app.engine.get_devon_discount_pct()

    sys.stdout.write(f"\n  {BOLD}{YELLOW}🕶️ Rocket Syndicate — Underground Black Market{RESET}\n")
    sys.stdout.write(f"  Available Spendable Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n")
    if devon_rank > 0:
        sys.stdout.write(f"  {BOLD}{GREEN}💼 Devon Corp [{devon_tier.upper()}]: -{devon_disc_pct}% discount applied to deals!{RESET}\n")

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
    raw_parts = cmd.split()
    bypass_confirm = False
    parts = []
    for p in raw_parts:
        if p.lower() in ["-y", "--yes", "confirm"]:
            bypass_confirm = True
        else:
            parts.append(p)

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

    bm = app.engine.get_or_init_black_market()
    deals = bm.get("deals", [])
    matched_deal = None
    for d in deals:
        if str(d.get("id")) == str(deal_id):
            matched_deal = d
            break

    if not matched_deal:
        app.message = f"Deal [{deal_id}] not found on the Black Market."
        return

    stock = matched_deal.get("stock", 0)
    if stock < qty:
        app.message = f"Deal [{deal_id}] only has {stock} in stock!"
        return

    unit_cost = matched_deal.get("cost", 0)
    total_cost = unit_cost * qty
    if app.engine.available_tokens < total_cost:
        app.message = f"Not enough tokens! Required: {format_tokens(total_cost)}, Available: {format_tokens(app.engine.available_tokens)}"
        return

    if qty > 5 and not bypass_confirm:
        d_name = matched_deal.get("name", f"Deal #{deal_id}")
        prompt = f"🕶️ Buy {qty}x {d_name} for {format_tokens(total_cost)} tokens? Type 'confirm' (or 'y')"
        if len(prompt) > 72:
            prompt = f"🕶️ Buy {qty}x [{deal_id}] for {format_tokens(total_cost)} tokens? Type 'y'"
        if len(prompt) > 72:
            prompt = prompt[:69] + "..."

        app.pending_buy = {
            "type": "black_market",
            "deal_id": deal_id,
            "qty": qty,
            "cost": total_cost,
            "name": d_name,
            "prompt": prompt,
        }
        app.message = prompt
        return

    ok, msg = app.engine.buy_black_market_deal(deal_id, qty)
    app.message = msg

def handle_shop_buy(app, cmd: str):
    if getattr(app, "shop_view", "normal") == "black_market":
        handle_deal_buy(app, cmd)
        return

    raw_parts = cmd.split()
    bypass_confirm = False
    clean_parts = []
    for p in raw_parts:
        if p.lower() in ["-y", "--yes", "confirm"]:
            bypass_confirm = True
        else:
            clean_parts.append(p)

    choice = clean_parts[1] if len(clean_parts) > 1 else ""
    qty = 1
    if len(clean_parts) >= 3:
        try:
            qty = int(clean_parts[2])
            if qty <= 0:
                app.message = "Quantity must be greater than 0."
                return
        except ValueError:
            app.message = "Invalid quantity."
            return

    # Map choice to ItemKind or egg
    item_kind = None
    if choice == "1":
        item_kind = ItemKind.RARE_CANDY
    elif choice == "2":
        if qty > 1:
            app.message = "You can only hold one egg!"
            return
        ok, msg = app.engine.buy_egg(None)
        app.message = msg
        return
    elif choice == "3":
        if qty > 1:
            app.message = "You can only hold one egg!"
            return
        ok, msg = app.engine.buy_egg(Rarity.UNCOMMON)
        app.message = msg
        return
    elif choice == "4":
        item_kind = ItemKind.BERRY_ORAN
    elif choice == "5":
        item_kind = ItemKind.BERRY_GOLDEN
    elif choice == "6":
        item_kind = ItemKind.EXPEDITION_LICENSE
    elif choice == "7":
        item_kind = ItemKind.EVERSTONE
    elif choice == "8":
        item_kind = ItemKind.LUCKY_EGG
    elif choice == "9":
        item_kind = ItemKind.AMULET_COIN
    elif choice == "10":
        item_kind = ItemKind.LEFTOVERS
    elif choice == "11":
        item_kind = ItemKind.CHOICE_SCARF
    else:
        name_map = {
            "rare_candy": ItemKind.RARE_CANDY,
            "candy": ItemKind.RARE_CANDY,
            "oran": ItemKind.BERRY_ORAN,
            "berry_oran": ItemKind.BERRY_ORAN,
            "golden": ItemKind.BERRY_GOLDEN,
            "golden_razz": ItemKind.BERRY_GOLDEN,
            "berry_golden": ItemKind.BERRY_GOLDEN,
            "license": ItemKind.EXPEDITION_LICENSE,
            "everstone": ItemKind.EVERSTONE,
            "lucky_egg": ItemKind.LUCKY_EGG,
            "amulet_coin": ItemKind.AMULET_COIN,
            "leftovers": ItemKind.LEFTOVERS,
            "choice_scarf": ItemKind.CHOICE_SCARF,
        }
        item_kind = name_map.get(choice.lower().replace("-", "_"))

    if not item_kind:
        app.message = "Invalid shop selection. Usage: buy <1-11> [qty]"
        return

    diff = app.engine.current_difficulty
    unit_cost = item_kind.price_for(diff)
    devon_mult = app.engine.get_devon_multiplier()
    unit_cost = int(unit_cost * devon_mult)
    total_cost = unit_cost * qty

    if app.engine.available_tokens < total_cost:
        app.message = f"Not enough tokens! Required: {format_tokens(total_cost)}, Available: {format_tokens(app.engine.available_tokens)}"
        return

    if qty > 5 and not bypass_confirm:
        prompt = f"🛒 Buy {qty}x {item_kind.name_en} {item_kind.emoji} for {format_tokens(total_cost)} tokens? Type 'confirm' (or 'y')"
        if len(prompt) > 72:
            prompt = f"🛒 Buy {qty}x {item_kind.emoji} for {format_tokens(total_cost)} tokens? Type 'y'"
        if len(prompt) > 72:
            prompt = f"Buy {qty}x {item_kind.name_en} for {format_tokens(total_cost)}? [y/N]"
        if len(prompt) > 72:
            prompt = prompt[:69] + "..."

        app.pending_buy = {
            "type": "shop_item",
            "item_kind": item_kind,
            "qty": qty,
            "cost": total_cost,
            "name": item_kind.name_en,
            "emoji": item_kind.emoji,
            "prompt": prompt,
        }
        app.message = prompt
        return

    ok, msg = app.engine.buy_item(item_kind, qty)
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
    if choice in ["catalyst", "dark_gene_catalyst"]:
        ok, msg = app.engine.use_rocket_armory_item("catalyst")
        app.message = msg
        return
    if choice in ["mist", "spray", "morale_mist", "morale mist"]:
        ok, msg = app.engine.use_rocket_armory_item("spray")
        app.message = msg
        return
    if choice in ["chrono", "accelerator", "chrono_accelerator"]:
        ok, msg = app.engine.use_rocket_armory_item("chrono")
        app.message = msg
        return

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

    raw_choice = parts[1].strip()
    choice = raw_choice.strip("[]").lower()
    target_key = resolve_bag_item(app, choice)
    if not target_key:
        if choice.isdigit():
            app.message = f"You do not have item [{choice}] in your Bag!"
        else:
            app.message = f"You do not have '{raw_choice}' in your Bag!"
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
        app.message = f"You do not have {clean_name} in your Bag!"
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
