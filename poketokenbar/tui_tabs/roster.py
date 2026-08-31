import sys
import math

HEADER = "\033[95m\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def render(app):
    active = app.engine.active_mon
    if active:
        app.engine._register_to_dex(active, status="active")

    dex = app.engine.state.get("dex", [])
    sys.stdout.write(f"\n  {BOLD}{HEADER}🐾 Caught Pokémon Roster{RESET}\n\n")

    # Show Incubating Egg option ONLY if an egg is owned
    egg_tier = app.engine.state.get("egg_tier")
    if egg_tier:
        egg_usage = app.engine.state.get("egg_usage", 0)
        threshold = app.engine.current_difficulty.hatch_threshold
        pct = (egg_usage / threshold) * 100 if threshold > 0 else 0
        
        tier_name = egg_tier.capitalize()
        if active is None:
            egg_badge = f"{BOLD}{GREEN}[ACTIVE / INCUBATING]{RESET}"
        else:
            egg_badge = f"{BOLD}{YELLOW}[IN ROSTER]{RESET}"
        sys.stdout.write(f"   0. 🥚 {BOLD}Incubating {tier_name} Egg{RESET} ({pct:.1f}%) {egg_badge}\n")

    expeditions = app.engine.state.get("expeditions", [])
    exp_map = {e["sp_id"]: e for e in expeditions}
    # Filter dex to active roster (excluding pre-evolutions marked as 'evolved')
    roster = [d for d in dex if d.get("status") != "evolved"]

    if not roster:
        sys.stdout.write("   You don't have any companions in your roster yet!\n")
    else:
        page_size = app.engine.state.get("page_size_roster", 14)
        total = len(roster)
        total_pages = max(1, math.ceil(total / page_size))
        
        app.roster_page = min(app.roster_page, total_pages)
        start_idx = (app.roster_page - 1) * page_size
        page_roster = roster[start_idx : start_idx + page_size]

        for idx, entry in enumerate(page_roster, start_idx + 1):
            sp_id = entry.get("species_id", entry.get("final_id", entry.get("base_id")))
            name = app.engine.api.get_species_name(sp_id)
            shiny_str = f"{YELLOW}✨{RESET}" if entry.get("is_shiny") else ""
            rarity = entry.get("rarity", "common").upper()
            status = entry.get("status", "graduated")
            mon_data = entry.get("mon_state", {})
            hap_val = mon_data.get("happiness", 100) if isinstance(mon_data, dict) else 100

            if sp_id in exp_map:
                exp_info = exp_map[sp_id]
                pct = (exp_info["progress"] / exp_info["target"]) * 100
                status_badge = f"{BOLD}{CYAN}[ON EXPEDITION: {exp_info['area']} ({pct:.0f}%)] {RESET}"
            elif status == "active" and active is not None:
                status_badge = f"{BOLD}{GREEN}[ACTIVE]{RESET}"
            elif status == "inactive":
                status_badge = f"{BOLD}{YELLOW}[IN ROSTER]{RESET}"
            else:
                status_badge = f"{BOLD}{CYAN}[GRADUATED]{RESET}"

            sys.stdout.write(f"  {idx:2d}. {shiny_str} {BOLD}{name}{RESET} (#{sp_id}) [{rarity}] 💖{hap_val}% {status_badge}\n")

        if total_pages > 1:
            sys.stdout.write(f"\n  ➔ Page {app.roster_page}/{total_pages} - Type '{BOLD}next{RESET}', '{BOLD}prev{RESET}', or '{BOLD}page <N>{RESET}' to navigate!\n")

    sys.stdout.write(f"\n  ➔ Type '{BOLD}sel <row>|#<dex>|egg{RESET}' to switch active companion!\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}send <row>|#<dex> [area]{RESET}' on expedition!\n")
    sys.stdout.write(f"     Areas:\n")
    sys.stdout.write(f"       • '{BOLD}viridian{RESET}' (5M, Mint)\n")
    sys.stdout.write(f"       • '{BOLD}cerulean{RESET}' (15M, Rare Candy)\n")
    sys.stdout.write(f"       • '{BOLD}silver{RESET}'   (30M, Golden Razz)\n")
    sys.stdout.write(f"       • '{BOLD}spear{RESET}'    (100M, Leg. Egg - Req 3x Map, 100% Hap)\n\n")
