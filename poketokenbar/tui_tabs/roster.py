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

import re
from poketokenbar.utils.formatting import format_tokens, format_progress_bar

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[mK]')

def strip_ansi(s: str) -> str:
    return ANSI_REGEX.sub('', s)

def render_nursery(app):
    sys.stdout.write(f"\n  {BOLD}{HEADER}🐾 Pokémon Nursery & Egg Reserves{RESET}\n\n")

    eggs = app.engine.get_all_nursery_eggs()
    if not eggs:
        sys.stdout.write("   No eggs in your Nursery reserves!\n")
        sys.stdout.write("   Obtain eggs from Mart, Casino, Expeditions, or Quests.\n\n")
    else:
        page_size = 7
        total = len(eggs)
        total_pages = max(1, math.ceil(total / page_size))
        if not hasattr(app, "nursery_page"):
            app.nursery_page = 1
        app.nursery_page = min(max(1, app.nursery_page), total_pages)
        start_idx = (app.nursery_page - 1) * page_size
        page_eggs = eggs[start_idx : start_idx + page_size]
        sort_crit = app.engine.state.get("nursery_sort_criteria", "default")
        sort_labels = {
            "default": "Default",
            "tier": "Tier",
            "progress": "Progress",
            "value": "Value"
        }
        curr_label = sort_labels.get(sort_crit, "Default")
        sys.stdout.write(f"  Sort: {BOLD}{curr_label}{RESET} • {total} egg(s) total\n\n")

        for egg in page_eggs:
            idx = egg["index"]
            tier_title = egg["tier"].replace("_", " ").title()
            prog = egg["progress"]
            thresh = egg["threshold"]
            pct = (prog / thresh) * 100 if thresh > 0 else 0
            bar = format_progress_bar(prog, thresh, width=10)
            val = app.engine.get_egg_token_value(egg["tier"])

            if egg["is_active"]:
                status_badge = f"{BOLD}{GREEN}[ACTIVE / INCUBATING]{RESET}"
            else:
                status_badge = f"{BOLD}{YELLOW}[IN NURSERY]{RESET}"

            line1 = f"  [{idx}] 🥚 {BOLD}{tier_title} Egg{RESET} • {bar} {status_badge}"
            if len(strip_ansi(line1)) > 72:
                line1 = f"  [{idx}] 🥚 {BOLD}{tier_title}{RESET} • {bar} {status_badge}"
            sys.stdout.write(f"{line1}\n")

            line2 = f"      Req: {format_tokens(thresh)} | Progress: {format_tokens(prog)} | Value: {format_tokens(val)}"
            if len(strip_ansi(line2)) > 72:
                line2 = f"      Prog: {format_tokens(prog)}/{format_tokens(thresh)} | Value: {format_tokens(val)}"
            sys.stdout.write(f"{line2}\n")

        if total_pages > 1:
            sys.stdout.write(f"\n  ➔ Page {app.nursery_page}/{total_pages} - Type '{BOLD}n{RESET}', '{BOLD}p{RESET}', or '{BOLD}page <N>{RESET}' to navigate!\n")

    sys.stdout.write(f"\n  ➔ Type '{BOLD}sel <#>{RESET}' to select active companion egg!\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}sell <#>{RESET}' to sell an egg for tokens!\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}sell all{RESET}' to sell all nursery reserve eggs!\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}sort <tier|progress|value|default>{RESET}' to sort eggs!\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}back{RESET}' to return to Caught Pokémon Roster.\n\n")

def render(app):
    if getattr(app, "roster_subview", "roster") == "eggs":
        render_nursery(app)
        return

    active = app.engine.active_mon
    if active:
        app.engine._register_to_dex(active, status="active")

    dex = app.engine.state.get("dex", [])
    sys.stdout.write(f"\n  {BOLD}{HEADER}🐾 Caught Pokémon Roster{RESET}\n\n")

    # Show Active Incubating Egg or Nursery summary
    all_eggs = app.engine.get_all_nursery_eggs()
    active_egg = next((e for e in all_eggs if e["is_active"]), None)
    if active_egg:
        tier_title = active_egg["tier"].replace("_", " ").title()
        prog = active_egg["progress"]
        thresh = active_egg["threshold"]
        pct = (prog / thresh) * 100 if thresh > 0 else 0
        sys.stdout.write(f"   0. 🥚 {BOLD}Incubating: {tier_title} Egg{RESET} ({pct:.1f}%) {BOLD}{GREEN}[ACTIVE COMPANION]{RESET}\n")

    if all_eggs:
        other_count = len([e for e in all_eggs if not e["is_active"]])
        if other_count > 0:
            res_line = f"      📦 Nursery: {other_count} other egg(s) resting (Type '{BOLD}eggs{RESET}')"
            sys.stdout.write(f"{res_line}\n")
        elif not active_egg:
            res_line = f"      📦 Nursery: {len(all_eggs)} egg(s) resting (Type '{BOLD}eggs{RESET}')"
            sys.stdout.write(f"{res_line}\n")

    expeditions = app.engine.state.get("expeditions", [])
    exp_map = {e.get("sp_id"): e for e in expeditions if "sp_id" in e}
    red_team_ids = app.engine.get_red_battle_active_pokemon_ids()
    rocket_team_ids = app.engine.get_rocket_battle_active_pokemon_ids()
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
                prog = exp_info.get("progress", 0)
                target = exp_info.get("target", 1)
                pct = min(100.0, (prog / target) * 100 if target > 0 else 100.0)
                area_str = str(exp_info.get("area", "Unknown")).capitalize()
                status_badge = f"{BOLD}{CYAN}[EXP: {area_str} {pct:.0f}%]{RESET}"
            elif sp_id in red_team_ids:
                status_badge = f"{BOLD}{RED}[BATTLE w/RED]{RESET}"
            elif sp_id in rocket_team_ids:
                status_badge = f"{BOLD}{RED}[ROCKET BTL]{RESET}"
            elif status == "active" and active is not None:
                status_badge = f"{BOLD}{GREEN}[ACTIVE]{RESET}"
            elif status == "inactive":
                status_badge = f"{BOLD}{YELLOW}[IN ROSTER]{RESET}"
            else:
                status_badge = f"{BOLD}{CYAN}[GRADUATED]{RESET}"

            selected_targets = getattr(app, "selected_expedition_targets", set())
            is_staged = idx in selected_targets
            staged_badge = f"{BOLD}{GREEN}[✓]{RESET} " if is_staged else ""

            sys.stdout.write(f"  {idx:2d}. {staged_badge}{shiny_str}{BOLD}{name}{RESET} (#{sp_id}) [{rarity}] 💖{hap_val}% {status_badge}\n")

        if total_pages > 1:
            sys.stdout.write(f"\n  ➔ Page {app.roster_page}/{total_pages} - Type '{BOLD}n{RESET}', '{BOLD}p{RESET}', or '{BOLD}page <N>{RESET}' to navigate!\n")

    selected_targets = getattr(app, "selected_expedition_targets", set())
    if isinstance(selected_targets, (set, list)) and len(selected_targets) > 0:
        sel_names = []
        for s_idx in sorted(selected_targets):
            if 1 <= s_idx <= len(roster):
                s_sp = roster[s_idx - 1].get("species_id", roster[s_idx - 1].get("base_id"))
                sel_names.append(f"{app.engine.api.get_species_name(s_sp)} (#{s_idx})")
        sel_str = ", ".join(sel_names)
        if len(sel_str) > 50:
            sel_str = sel_str[:47] + "..."
        sys.stdout.write(f"\n  🎯 {BOLD}{GREEN}Selected for Expedition ({len(selected_targets)}):{RESET} {sel_str}\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}send <area>{RESET}' to dispatch! | '{BOLD}feed [qty]{RESET}' to feed! | '{BOLD}clear{RESET}'\n")

    sys.stdout.write(f"\n  ➔ Type '{BOLD}feed <#[id]|<=[pct]|[pct]|0> [qty]{RESET}' to feed Oran Berries 🫐!\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}sel <row>|#<dex>{RESET}' to switch active companion!\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}eggs{RESET}' to open Nursery & select/sell eggs!\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}pick{RESET}' to open Interactive Multi-Select Dispatcher!\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}send <row(s)|#dex|all> [area]{RESET}' on expedition!\n")
    sys.stdout.write(f"     Areas:\n")
    sys.stdout.write(f"       • '{BOLD}viridian{RESET}' (5M)  • '{BOLD}mine{RESET}' (10M)  • '{BOLD}cerulean{RESET}' (15M)\n")
    sys.stdout.write(f"       • '{BOLD}silver{RESET}' (30M)   • '{BOLD}spear{RESET}' (100M, Req 3x Map)\n\n")

render_roster_tab = render
