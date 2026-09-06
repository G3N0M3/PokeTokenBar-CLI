import sys
import math
from poketokenbar.utils.formatting import format_tokens

HEADER = "\033[95m\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def render_expeditions_tab(app):
    expeditions = app.engine.state.get("expeditions", [])
    slot_limit = app.engine.state.get("expedition_slots", 10)
    sys.stdout.write(f"\n  {BOLD}{HEADER}🗺️ Pokédex Expeditions ({len(expeditions)}/{slot_limit} Active){RESET}\n\n")

    # Staged selection summary if any companions are selected
    selected_targets = getattr(app, "selected_expedition_targets", set())
    if isinstance(selected_targets, (set, list)) and len(selected_targets) > 0:
        roster = [d for d in app.engine.state.get("dex", []) if d.get("status") != "evolved"]
        names = []
        for s_idx in sorted(selected_targets):
            if 1 <= s_idx <= len(roster):
                s_sp = roster[s_idx - 1].get("species_id", roster[s_idx - 1].get("base_id"))
                names.append(f"{app.engine.api.get_species_name(s_sp)} (#{s_idx})")
        names_str = ", ".join(names)
        if len(names_str) > 50:
            names_str = names_str[:47] + "..."
        sys.stdout.write(f"  🎯 {BOLD}{GREEN}Selected for Dispatch ({len(selected_targets)}):{RESET} {names_str}\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}send <area>{RESET}' to dispatch! (e.g. 'send mine') | '{BOLD}clear{RESET}' to deselect\n\n")

    sys.stdout.write(f"  {BOLD}Available Expedition Destinations:{RESET}\n")
    sys.stdout.write(f"   (💡 {YELLOW}Hint: High Rarity/MEGA = Faster Expeditions!{RESET})\n")
    sys.stdout.write(f"   • Viridian Forest - Target: 5.0M tokens  - Reward: 🌿 Mint + XP + 🪙\n")
    sys.stdout.write(f"   • Evolution Mine  - Target: 10.0M tokens - Reward: 💎 Random Evo Stone\n")
    sys.stdout.write(f"   • Cerulean Cave   - Target: 15.0M tokens - Reward: 🍬 Rare Candy + XP + 🪙\n")
    sys.stdout.write(f"                       (+5% chance of finding a Map)\n")
    sys.stdout.write(f"   • Mt. Silver      - Target: 30.0M tokens - Reward: 🍇 Golden Razz + XP + 🪙\n")
    sys.stdout.write(f"                       (+15% chance of finding a Map)\n")
    sys.stdout.write(f"   • Spear Pillar    - Target: 100.0M tokens (Requires 3x Maps)\n")
    sys.stdout.write(f"                       Reward: 🌟 LEGENDARY EGG + XP + 🪙\n\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}dispatch{RESET}' or '{BOLD}send{RESET}' to open Interactive Multi-Select Picker!\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}send <row(s)|#dex|all> [area]{RESET}' to dispatch directly!\n")
    sys.stdout.write(f"     (e.g. 'send 1,2,3 viridian', 'send 1-5 mine', 'send all silver')\n")
    
    passes_count = app.engine.state.get("inventory", {}).get("expedition_pass", 0)
    sys.stdout.write(f"  ➔ Type '{BOLD}pass <idx>{RESET}' to instantly finish! (🎫 Passes: {BOLD}{YELLOW}{passes_count}{RESET})\n\n")

    sys.stdout.write(f"  {BOLD}🗺️ Active Expeditions Status:{RESET}\n")
    if not expeditions:
        sys.stdout.write("   No companions currently on expedition.\n\n")
    else:
        page_size = app.engine.state.get("page_size_expedition", 10)
        total_pages = max(1, (len(expeditions) - 1) // page_size + 1)
        if not hasattr(app, 'expedition_page'):
            app.expedition_page = 1
        app.expedition_page = min(app.expedition_page, total_pages)
        
        start_idx = (app.expedition_page - 1) * page_size
        page_exps = expeditions[start_idx : start_idx + page_size]
        
        for i, exp in enumerate(page_exps, start_idx + 1):
            sp_id = exp.get("sp_id")
            sp_name = app.engine.api.get_species_name(sp_id) if sp_id else "Unknown"
            area = exp.get("area", "Unknown Area")
            progress = exp.get("progress", 0)
            target = exp.get("target", 1)
            pct = (progress / target) * 100 if target > 0 else 0
            sys.stdout.write(f"   [{i}] • {BOLD}{CYAN}{sp_name} (#{sp_id}){RESET} @ {area}: {format_tokens(progress)} / {format_tokens(target)} ({pct:.0f}%)\n")
            
        if total_pages > 1:
            sys.stdout.write(f"\n  ➔ Page {app.expedition_page}/{total_pages} - Type '{BOLD}next{RESET}', '{BOLD}prev{RESET}', or '{BOLD}page <N>{RESET}' to navigate!\n")
        sys.stdout.write("\n")

    # Recent Expedition Logs
    exp_logs = app.engine.state.get("expedition_logs", [])
    sys.stdout.write(f"  {BOLD}📜 Recent Expedition Logs (Last 5 Expeditions):{RESET}\n")
    if not exp_logs:
        sys.stdout.write("   No completed expeditions recorded yet. Dispatch companions to start!\n\n")
    else:
        for log in exp_logs:
            fixed_log = log.replace("] 🗺️ ", "] ").replace("]   ", "] ")
            sys.stdout.write(f" {fixed_log}\n")
        sys.stdout.write("\n")

def render_expedition_picker(app):
    dex = app.engine.state.get("dex", [])
    roster = [d for d in dex if d.get("status") != "evolved"]
    expeditions = app.engine.state.get("expeditions", [])
    slot_limit = app.engine.state.get("expedition_slots", 10)
    deployed_ids = {e.get("sp_id") for e in expeditions if "sp_id" in e}
    avail_slots = max(0, slot_limit - len(expeditions))

    selected = getattr(app, "selected_expedition_targets", set())

    sys.stdout.write(f"\n  {BOLD}{HEADER}🗺️ Expedition Dispatcher — Multi-Select Picker{RESET}\n")
    sys.stdout.write(f"  {BOLD}Slots:{RESET} {len(expeditions)}/{slot_limit} active | {BOLD}Selected:{RESET} {len(selected)}/{avail_slots} available\n\n")

    if not roster:
        sys.stdout.write("   No companions available in your Roster!\n\n")
        return

    page_size = 10
    total_pages = max(1, math.ceil(len(roster) / page_size))
    if not hasattr(app, "picker_page"):
        app.picker_page = 1
    app.picker_page = max(1, min(app.picker_page, total_pages))

    start_idx = (app.picker_page - 1) * page_size
    page_roster = roster[start_idx : start_idx + page_size]

    sys.stdout.write(f"  {BOLD}{'Sel':^5} {'#':>3}  {'Companion':<15} {'Rarity':<8} {'Hap':^6} {'Status'}{RESET}\n")
    sys.stdout.write(f"  {'-'*68}\n")

    for idx, entry in enumerate(page_roster, start_idx + 1):
        sp_id = entry.get("species_id", entry.get("final_id", entry.get("base_id")))
        name = app.engine.api.get_species_name(sp_id)
        if len(name) > 13:
            name = name[:12] + "…"
        shiny = "✨" if entry.get("is_shiny") else " "
        rarity = entry.get("rarity", "common").upper()[:6]
        mon_data = entry.get("mon_state", {})
        hap = mon_data.get("happiness", 100) if isinstance(mon_data, dict) else 100

        is_deployed = sp_id in deployed_ids
        is_exhausted = hap <= 0
        is_sel = idx in selected

        if is_deployed:
            checkbox = f"{BLUE}[-]{RESET}"
            status_str = f"{BLUE}Deployed{RESET}"
        elif is_exhausted:
            checkbox = f"{RED}[x]{RESET}"
            status_str = f"{RED}0% Hap{RESET}"
        elif is_sel:
            checkbox = f"{BOLD}{GREEN}[✓]{RESET}"
            status_str = f"{BOLD}{GREEN}Selected{RESET}"
        else:
            checkbox = f"[ ]"
            status_str = f"{CYAN}Ready{RESET}"

        sys.stdout.write(f"  {checkbox} {idx:3d}. {shiny}{name:<13} {rarity:<8} {hap:3d}%  {status_str}\n")

    sys.stdout.write(f"  {'-'*68}\n")
    if total_pages > 1:
        sys.stdout.write(f"  ➔ Page {app.picker_page}/{total_pages} - Type '{BOLD}next{RESET}', '{BOLD}prev{RESET}', or '{BOLD}page <N>{RESET}'\n")

    if selected:
        selected_names = []
        for s_idx in sorted(selected):
            if 1 <= s_idx <= len(roster):
                s_entry = roster[s_idx - 1]
                s_sp = s_entry.get("species_id", s_entry.get("base_id"))
                selected_names.append(f"{app.engine.api.get_species_name(s_sp)} (#{s_idx})")
        names_str = ", ".join(selected_names)
        if len(names_str) > 50:
            names_str = names_str[:47] + "..."
        sys.stdout.write(f"  🎯 {BOLD}{GREEN}Selected ({len(selected)}):{RESET} {names_str}\n")

    sys.stdout.write(f"\n  ➔ {BOLD}Toggle Selection:{RESET} enter numbers (e.g. '{BOLD}1{RESET}', '{BOLD}1 2 3{RESET}', '{BOLD}1-5{RESET}', '{BOLD}all{RESET}', '{BOLD}clear{RESET}')\n")
    sys.stdout.write(f"  ➔ {BOLD}Dispatch Destination:{RESET}\n")
    sys.stdout.write(f"     • '{BOLD}viridian{RESET}' (5M)  • '{BOLD}mine{RESET}' (10M)  • '{BOLD}cerulean{RESET}' (15M)\n")
    sys.stdout.write(f"     • '{BOLD}silver{RESET}' (30M)   • '{BOLD}spear{RESET}' (100M, req 3x Map, 100% Hap)\n")
    sys.stdout.write(f"     (Shortcuts: '{BOLD}to 1{RESET}'..'{BOLD}to 5{RESET}' or '{BOLD}send <area>{RESET}')\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}back{RESET}' or '{BOLD}q{RESET}' to return to Expeditions view.\n\n")
