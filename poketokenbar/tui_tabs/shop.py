import sys
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

def render_shop_tab(app):
    avail = app.engine.available_tokens
    inv = app.engine.state.get("inventory", {})
    diff = app.engine.current_difficulty
    prices = diff.shop_prices

    p_rc = format_tokens(prices["rare_candy"])
    p_rc_xp = format_tokens(int(prices["rare_candy"] * 0.6))
    p_mint = format_tokens(prices["mint"])
    p_egg1 = format_tokens(prices["egg_normal"])
    p_egg2 = format_tokens(prices["egg_uncommon"])

    sys.stdout.write(f"\n  {BOLD}{YELLOW}🛒 Token Shop & Bag{RESET}  (Available Spendable Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET})\n\n")
    sys.stdout.write(f"  {BOLD}Shop Items (Type 'buy <number> [qty]' to purchase):{RESET}\n")
    sys.stdout.write(f"  [1] 🍬 Rare Candy     - Cost: {p_rc:<6} tokens  (Grants +{p_rc_xp} XP)\n")
    sys.stdout.write(f"  [2] 🌿 Mint           - Cost: {p_mint:<6} tokens  (Rerolls nature)\n")
    sys.stdout.write(f"  [3] 🥚 Pokémon Egg    - Cost: {p_egg1:<6} tokens  (Incubate new egg)\n")
    sys.stdout.write(f"  [4] 🥚 Uncommon Egg   - Cost: {p_egg2:<6} tokens  (Guarantees Uncommon+ egg)\n")
    sys.stdout.write(f"  [5] 🫐 Oran Berry     - Cost: 1.0M   tokens  (+25% Companion Happiness)\n")
    sys.stdout.write(f"  [6] 🍇 Golden Razz    - Cost: 5.0M   tokens  (Boosts next egg shiny odds to 1/24!)\n")
    sys.stdout.write(f"  [7] 📜 Exped. License - Cost: 200.0M tokens  (+10 expedition slots)\n")
    sys.stdout.write(f"  [8] 🪨 Everstone      - Cost: 500.0K tokens  (Prevents evolution when equipped)\n")
    sys.stdout.write(f"  [9] 🍀 Lucky Egg      - Cost: 5.0M   tokens  (+20% XP gain when equipped)\n")
    sys.stdout.write(f"  [10] 🪙 Amulet Coin   - Cost: 2.0M   tokens  (+50% token gain from battles/expeditions)\n")
    sys.stdout.write(f"  [11] 🍎 Leftovers     - Cost: 2.0M   tokens  (Protects happiness from daily decay)\n")
    sys.stdout.write(f"  [12] 🥊 Choice Scarf  - Cost: 2.0M   tokens  (+20% expedition speed, faster happiness drain)\n\n")

    sys.stdout.write(f"  {BOLD}Your Bag (Type 'use <id>', 'sell <id> [qty]', or 'unequip'):{RESET}\n")
    
    bag_items = []
    if inv.get('rare_candy', 0) > 0: bag_items.append(("🍬 Rare Candy", "1", inv['rare_candy']))
    if inv.get('mint', 0) > 0: bag_items.append(("🌿 Mint", "2", inv['mint']))
    if inv.get('berry_oran', 0) > 0: bag_items.append(("🫐 Oran Berry", "3", inv['berry_oran']))
    if inv.get('berry_golden', 0) > 0: bag_items.append(("🍇 Golden Razz", "4", inv['berry_golden']))
    if inv.get('poke_flute', 0) > 0: bag_items.append(("🪈 Poké Flute (Summons Gym Boss)", "6", inv['poke_flute']))
    if inv.get('master_ball', 0) > 0: bag_items.append(("🌟 Master Ball (Hatches Shiny)", "7", inv['master_ball']))
    if inv.get('map_fragment', 0) > 0: bag_items.append(("📜 Map", "8", inv['map_fragment']))
    if inv.get('expedition_license', 0) > 0: bag_items.append(("📜 Exped. License (+10 exp. slots)", "9", inv['expedition_license']))
    if inv.get('everstone', 0) > 0: bag_items.append(("🪨 Everstone (Prevents evolution)", "10", inv['everstone']))
    if inv.get('lucky_egg', 0) > 0: bag_items.append(("🍀 Lucky Egg (+20% XP)", "11", inv['lucky_egg']))
    if inv.get('amulet_coin', 0) > 0: bag_items.append(("🪙 Amulet Coin (+50% battle/exp tokens)", "12", inv['amulet_coin']))
    if inv.get('leftovers', 0) > 0: bag_items.append(("🍎 Leftovers (Protects happiness)", "13", inv['leftovers']))
    if inv.get('choice_scarf', 0) > 0: bag_items.append(("🥊 Choice Scarf (+20% exp speed)", "14", inv['choice_scarf']))
    
    stone_keys = ["water_stone", "fire_stone", "thunder_stone", "leaf_stone", "moon_stone", "sun_stone", "ice_stone", "shiny_stone", "dusk_stone", "dawn_stone"]
    for k in stone_keys:
        if inv.get(k, 0) > 0:
            bag_items.append((f"💎 {k.replace('_', ' ').title()}", k, inv[k]))
            
    page_size = app.engine.state.get("page_size_bag", 10)
    total_pages = max(1, (len(bag_items) - 1) // page_size + 1)
    if not hasattr(app, 'shop_page'): app.shop_page = 1
    app.shop_page = max(1, min(app.shop_page, total_pages))
    
    if not bag_items:
        sys.stdout.write("  (Your bag is empty)\n\n")
    else:
        start_idx = (app.shop_page - 1) * page_size
        end_idx = start_idx + page_size
        for name, cmd_id, qty in bag_items[start_idx:end_idx]:
            sys.stdout.write(f"  [{cmd_id}] {name}: {qty} owned\n")
            
        if total_pages > 1:
            sys.stdout.write(f"\n  ➔ Page {app.shop_page}/{total_pages} - Type '{BOLD}next{RESET}', '{BOLD}prev{RESET}', or '{BOLD}page <N>{RESET}' to navigate bag!\n")
        sys.stdout.write("\n")

def handle_shop_buy(app, cmd: str):
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
    if parts[0] == "unequip":
        ok, msg = app.engine.unequip_item()
        app.message = msg
        return
        
    choice = parts[1] if len(parts) > 1 else ""
    qty = 1
    if len(parts) > 2:
        try:
            qty = int(parts[2])
        except ValueError:
            app.message = "Invalid quantity."
            return

    if choice == "1":
        ok, msg = app.engine.use_item(ItemKind.RARE_CANDY, qty)
    elif choice == "2":
        ok, msg = app.engine.use_item(ItemKind.MINT, qty)
    elif choice == "3":
        ok, msg = app.engine.use_item(ItemKind.BERRY_ORAN, qty)
    elif choice == "4":
        ok, msg = app.engine.use_item(ItemKind.BERRY_GOLDEN, qty)
    elif choice == "6":
        ok, msg = app.engine.use_item(ItemKind.POKE_FLUTE, qty)
    elif choice == "7":
        ok, msg = app.engine.use_item(ItemKind.MASTER_BALL, qty)
    elif choice == "9":
        ok, msg = app.engine.use_item(ItemKind.EXPEDITION_LICENSE, qty)
    elif choice == "10":
        ok, msg = app.engine.use_item(ItemKind.EVERSTONE, qty)
    elif choice == "11":
        ok, msg = app.engine.use_item(ItemKind.LUCKY_EGG, qty)
    elif choice == "12":
        ok, msg = app.engine.use_item(ItemKind.AMULET_COIN, qty)
    elif choice == "13":
        ok, msg = app.engine.use_item(ItemKind.LEFTOVERS, qty)
    elif choice == "14":
        ok, msg = app.engine.use_item(ItemKind.CHOICE_SCARF, qty)
    elif choice in [s.value for s in ItemKind if s.value.endswith("_stone") and s != ItemKind.MEGA_STONE]:
        ok, msg = app.engine.use_item(ItemKind(choice), qty)
    else:
        ok, msg = False, "Invalid bag selection."
    app.message = msg

def handle_bag_sell(app, cmd: str):
    parts = cmd.split()
    choice = parts[1] if len(parts) > 1 else ""
    qty = 1
    if len(parts) >= 3:
        try:
            qty = int(parts[2])
        except ValueError:
            app.message = "Invalid quantity."
            return

    mapping = {
        "1": ItemKind.RARE_CANDY,
        "2": ItemKind.MINT,
        "3": ItemKind.BERRY_ORAN,
        "4": ItemKind.BERRY_GOLDEN,
        "6": ItemKind.POKE_FLUTE,
        "7": ItemKind.MASTER_BALL,
        "8": ItemKind.MAP_FRAGMENT,
        "9": ItemKind.EXPEDITION_LICENSE,
        "10": ItemKind.EVERSTONE,
        "11": ItemKind.LUCKY_EGG,
        "12": ItemKind.AMULET_COIN,
        "13": ItemKind.LEFTOVERS,
        "14": ItemKind.CHOICE_SCARF,
    }
    
    for s in ItemKind:
        if s.value.endswith("_stone") and s != ItemKind.MEGA_STONE:
            mapping[s.value] = s

    item_kind = mapping.get(choice)
    if not item_kind:
        app.message = "Invalid bag selection."
        return

    inv = app.engine.state.get("inventory", {})
    if inv.get(item_kind.value, 0) < qty:
        app.message = f"You don't have {qty}x {item_kind.name_en} in your Bag to sell!"
        return

    cost = item_kind.price_for(app.engine.current_difficulty)
    sell_value = int(cost * 0.8) * qty

    item_name = item_kind.name_en
    if item_kind == item_kind.MEGA_STONE:
        found_key = "mega_stone"
        item_name = "Universal Mega Stone"
        if inv.get("mega_stone", 0) < qty:
            found_key = None
            from poketokenbar.game.models import MEGA_STONES
            for sp_id, s_name in MEGA_STONES.items():
                k = f"mega_stone_{sp_id}"
                if inv.get(k, 0) >= qty:
                    found_key = k
                    item_name = s_name
                    break
        if not found_key:
            app.message = f"You don't have {qty}x of any specific Mega Stone in your Bag to sell!"
            return

    sys.stdout.write(f"\n  {BOLD}{YELLOW}💰 SELL CONFIRMATION{RESET}\n")
    sys.stdout.write(f"  Are you sure you want to sell {qty}x {item_name} ({item_kind.emoji}) for +{format_tokens(sell_value)} Tokens? (y/n)> ")
    sys.stdout.flush()
    
    ans = sys.stdin.readline().strip().lower()
    if ans in ["y", "yes"]:
        ok, msg = app.engine.sell_item(item_kind, qty)
        app.message = msg
    else:
        app.message = f"Canceled selling {qty}x {item_kind.name_en}."
