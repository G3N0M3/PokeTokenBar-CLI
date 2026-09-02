import sys
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
    sys.stdout.write(f"  ➔ Type '{BOLD}send <ROW INDEX>|#<POKEMON INDEX> [area]{RESET}' to dispatch!\n")
    
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
            sp_id = exp["sp_id"]
            sp_name = app.engine.api.get_species_name(sp_id)
            area = exp["area"]
            pct = (exp["progress"] / exp["target"]) * 100 if exp["target"] > 0 else 0
            sys.stdout.write(f"   [{i}] • {BOLD}{CYAN}{sp_name} (#{sp_id}){RESET} @ {area}: {format_tokens(exp['progress'])} / {format_tokens(exp['target'])} ({pct:.0f}%)\n")
            
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
            sys.stdout.write(f"   {log}\n")
        sys.stdout.write("\n")
