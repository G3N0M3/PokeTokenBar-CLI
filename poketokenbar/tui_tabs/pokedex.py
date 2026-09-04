import sys

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
    sys.stdout.write(f"\n  {BOLD}{HEADER}📖 Pokédex Archives ({len(dex)} species registered){RESET}\n\n")

    if not dex:
        sys.stdout.write("   Your Pokédex is currently empty. Hatch eggs to discover Pokémon!\n")
    else:
        page_size = app.engine.state.get("page_size_pokedex", 15)
        total_pages = max(1, (len(dex) - 1) // page_size + 1)
        app.pokedex_page = max(1, min(app.pokedex_page, total_pages))

        start_idx = (app.pokedex_page - 1) * page_size
        end_idx = start_idx + page_size
        page_dex = dex[start_idx:end_idx]

        expeditions = app.engine.state.get("expeditions", [])
        exp_map = {e["sp_id"]: e for e in expeditions}

        for idx, entry in enumerate(page_dex, start_idx + 1):
            sp_id = entry.get("species_id", entry.get("final_id", entry.get("base_id")))
            name = app.engine.api.get_species_name(sp_id)
            shiny_str = f"{YELLOW}✨{RESET}" if entry.get("is_shiny") else ""
            rarity = entry.get("rarity", "common").upper()
            status = entry.get("status", "discovered")

            if sp_id in exp_map:
                exp_info = exp_map[sp_id]
                pct = min(100.0, (exp_info["progress"] / exp_info["target"]) * 100 if exp_info.get("target", 0) > 0 else 100.0)
                status_badge = f"{BOLD}{CYAN}[EXP: {exp_info['area'].capitalize()} {pct:.0f}%]{RESET}"
            elif active and active.current_id == sp_id:
                status_badge = f"{BOLD}{GREEN}[ACTIVE]{RESET}"
            elif status == "graduated":
                status_badge = f"{BOLD}{CYAN}[GRADUATED]{RESET}"
            elif status == "evolved":
                status_badge = f"{BOLD}{YELLOW}[EVOLVED]{RESET}"
            else:
                status_badge = f"{BOLD}{YELLOW}[DISCOVERED]{RESET}"

            sys.stdout.write(f"  {idx:2d}. {shiny_str} {BOLD}{name}{RESET} (#{sp_id}) [{rarity}] {status_badge}\n")

        if total_pages > 1:
            sys.stdout.write(f"\n  ➔ Page {app.pokedex_page}/{total_pages} - Type '{BOLD}next{RESET}', '{BOLD}prev{RESET}', or '{BOLD}page <N>{RESET}' to navigate!\n")
        else:
            sys.stdout.write(f"\n  ➔ Complete evolutions and hatch eggs to discover all Pokédex entries!\n\n")
