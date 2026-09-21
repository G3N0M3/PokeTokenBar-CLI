import sys
import math
import datetime
from poketokenbar.utils.formatting import format_tokens

HEADER = "\033[95m\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def get_settings_items(app):
    items = []

    # ── Group 1: Token Tracking & Billing ──────────────────────────────
    base_tokens = app.engine.state.get("baseline_total_tokens", 0)
    tokens_init_ts = app.engine.state.get("tokens_init_ts")
    base_date = app.engine.state.get("baseline_date")
    if tokens_init_ts or base_tokens > 0:
        date_info = f" (since {base_date})" if base_date else ""
        total_status = f"{BOLD}{GREEN}Initialized{date_info}{RESET}"
    else:
        total_status = f"{BOLD}{YELLOW}Uninitialized (lifetime tracking){RESET}"
    items.append((
        1,
        [
            f"  [1] Token Tracking Baseline:   {total_status}",
            f"      ➔ Type '{BOLD}tokens init{RESET}' to clear all token metrics to 0"
        ]
    ))

    b_day = app.engine.state.get("billing_cycle_day", 1)
    items.append((
        2,
        [
            f"  [2] Monthly Billing Cycle Day: {BOLD}Day {b_day} of each month{RESET}",
            f"      ➔ Type '{BOLD}billing <1-31>{RESET}' to adjust monthly token anchor"
        ]
    ))

    # ── Group 2: Display & Interface ───────────────────────────────────
    current_size = app.engine.state.get("sprite_size", 30)
    items.append((
        3,
        [
            f"  [3] Sprite Resolution:         {BOLD}{current_size} columns{RESET}",
            f"      ➔ Type '{BOLD}size <number>{RESET}' to adjust"
        ]
    ))

    settings_size = app.engine.state.get("page_size_settings", 6)
    items.append((
        4,
        [
            f"  [4] Settings Tab Page Size:    {BOLD}{settings_size} items{RESET}",
            f"      ➔ Type '{BOLD}pagesize settings <number>{RESET}' to adjust"
        ]
    ))

    # ── Group 3: Pagination & View Layouts ─────────────────────────────
    pokedex_size = app.engine.state.get("page_size_pokedex", 15)
    items.append((
        5,
        [
            f"  [5] Pokédex Page Size:         {BOLD}{pokedex_size} items{RESET}",
            f"      ➔ Type '{BOLD}pagesize dex <number>{RESET}' to adjust"
        ]
    ))

    roster_size = app.engine.state.get("page_size_roster", 14)
    items.append((
        6,
        [
            f"  [6] Roster Page Size:          {BOLD}{roster_size} items{RESET}",
            f"      ➔ Type '{BOLD}pagesize roster <number>{RESET}' to adjust"
        ]
    ))

    bag_size = app.engine.state.get("page_size_bag", 10)
    items.append((
        7,
        [
            f"  [7] Bag Page Size:             {BOLD}{bag_size} items{RESET}",
            f"      ➔ Type '{BOLD}pagesize bag <number>{RESET}' to adjust"
        ]
    ))

    expedition_size = app.engine.state.get("page_size_expedition", 10)
    items.append((
        8,
        [
            f"  [8] Expeditions Page Size:     {BOLD}{expedition_size} items{RESET}",
            f"      ➔ Type '{BOLD}pagesize exp <number>{RESET}' to adjust"
        ]
    ))

    mega_size = app.engine.state.get("page_size_mega", 14)
    items.append((
        9,
        [
            f"  [9] Mega Evo Page Size:        {BOLD}{mega_size} items{RESET}",
            f"      ➔ Type '{BOLD}pagesize mega <number>{RESET}' to adjust"
        ]
    ))

    cd_size = app.engine.state.get("page_size_cd", 5)
    items.append((
        10,
        [
            f"  [10] Term Deposits Page Size:  {BOLD}{cd_size} items{RESET}",
            f"      ➔ Type '{BOLD}pagesize cd <number>{RESET}' to adjust"
        ]
    ))

    # ── Group 4: Game Process & Management ─────────────────────────────
    is_unlocked = app.engine.state.get("rocket_story_unlocked", False)
    if is_unlocked:
        status_tag = f"{BOLD}{RED}ACTIVE{RESET}"
    else:
        status_tag = f"{BOLD}{YELLOW}UNINITIALIZED{RESET}"

    items.append((
        11,
        [
            f"  [11] Team Rocket Process:      {status_tag}",
            f"      ➔ Type '{BOLD}rocket init{RESET}' to initialize / reset campaign"
        ]
    ))

    items.append((
        12,
        [
            f"  [12] Reset Game Progress:      {BOLD}{RED}[DANGER]{RESET}",
            f"      ➔ Type '{BOLD}reset{RESET}' to clear all progress & restart"
        ]
    ))

    return items

def render_settings_tab(app):
    items = get_settings_items(app)
    page_size = app.engine.state.get("page_size_settings", 6)
    if not isinstance(page_size, int) or page_size < 1:
        page_size = 6

    total_items = len(items)
    total_pages = max(1, math.ceil(total_items / page_size))

    # Safely retrieve and clamp current page
    curr_page = getattr(app, "settings_page", 1)
    if not isinstance(curr_page, int) or curr_page < 1:
        curr_page = 1
    curr_page = min(curr_page, total_pages)
    if hasattr(app, "settings_page"):
        try:
            app.settings_page = curr_page
        except Exception:
            pass

    page_tag = f" {BOLD}(Page {curr_page}/{total_pages}){RESET}" if total_pages > 1 else ""
    now = datetime.datetime.now()
    date_hour_str = now.strftime("%Y-%m-%d %H")
    tod_str = "Day" if 6 <= now.hour < 18 else "Night"
    sys.stdout.write(f"\n  {BOLD}{CYAN}⚙️ Tracking & Application Settings{RESET}{page_tag}\n")
    sys.stdout.write(f"  🕒 System Date & Hour:         {BOLD}{date_hour_str}{RESET} ({tod_str})\n\n")

    start_idx = (curr_page - 1) * page_size
    page_items = items[start_idx : start_idx + page_size]

    for item_idx, lines in page_items:
        for line in lines:
            sys.stdout.write(f"{line}\n")
        sys.stdout.write("\n")

    if total_pages > 1:
        sys.stdout.write(f"  ➔ Page {curr_page}/{total_pages} - Type '{BOLD}n{RESET}', '{BOLD}p{RESET}', or '{BOLD}page <N>{RESET}' to navigate!\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}pagesize settings <num>{RESET}' to adjust items per page\n\n")
