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

from poketokenbar.game.items import (
    BAG_CATALOG,
    BAG_CATALOG_MAP,
    BAG_KEY_TO_ID,
    ITEM_DESCRIPTIONS,
    resolve_bag_item,
)



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
