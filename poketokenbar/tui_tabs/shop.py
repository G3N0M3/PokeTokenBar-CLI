import random
import sys
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
    for s in ItemKind:
        if choice == s.value or choice == s.value.replace("_", ""):
            return s.value
    inv = app.engine.state.get("inventory", {}) if hasattr(app, "engine") else {}
    if choice in inv:
        return choice
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

    sys.stdout.write(f"  {BOLD}Your Bag (Type 'use <id>', 'sell <id> [qty]', or 'unequip'):{RESET}\n")
    
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
