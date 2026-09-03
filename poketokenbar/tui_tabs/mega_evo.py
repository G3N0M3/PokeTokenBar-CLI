import sys

HEADER = "\033[95m\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def render_mega_evo_tab(app):
    sys.stdout.write(f"\n  {BOLD}{HEADER}🔮 Mega Evolution Interface{RESET}\n\n")
    
    inv = app.engine.state.get("inventory", {})
    stones = []
    from poketokenbar.game.models import MEGA_STONES
    
    app.mega_stone_map = {}
    idx = 1
    for sid, stone_name in MEGA_STONES.items():
        k = f"mega_stone_{sid}"
        c = inv.get(k, 0)
        if c > 0: 
            stones.append((idx, f"{stone_name} x{c}"))
            app.mega_stone_map[str(idx)] = k
            idx += 1
            
    if inv.get("mega_stone", 0) > 0: 
        stones.append((idx, f"Universal Stone x{inv['mega_stone']}"))
        app.mega_stone_map[str(idx)] = "mega_stone"
        idx += 1
        
    active = app.engine.active_mon
    if active:
        sp_name = app.engine.api.get_species_name(active.current_id)
        sp_id = str(active.current_id)
        is_eligible = any(str(k) == sp_id or str(k).startswith(f"{sp_id}_") for k in MEGA_STONES.keys())
        
        sys.stdout.write(f"  {BOLD}Active Companion:{RESET} {CYAN}{sp_name} (#{active.current_id}){RESET}\n")
        if is_eligible:
            if active.is_mega:
                form_str = f" {active.mega_form}" if getattr(active, 'mega_form', None) in ["X", "Y"] else ""
                sys.stdout.write(f"  {BOLD}Status:{RESET} {GREEN}MEGA EVOLVED! ✨ (Form{form_str} +50% Bonus XP active){RESET}\n")
                sys.stdout.write(f"  {BOLD}Usable Items:{RESET} {YELLOW}Type 'revert' to return to standard form{RESET}\n")
            else:
                usable_idxs = []
                for s_idx, k in app.mega_stone_map.items():
                    if k == "mega_stone" or k == f"mega_stone_{sp_id}" or k.startswith(f"mega_stone_{sp_id}_"):
                        usable_idxs.append(f"[{s_idx}]")
                        
                sys.stdout.write(f"  {BOLD}Status:{RESET} Standard Form (Available for Mega-Evo!)\n")
                if usable_idxs:
                    sys.stdout.write(f"  {BOLD}Usable Items:{RESET} {YELLOW}Type 'use <idx>' with {', '.join(usable_idxs)}{RESET}\n")
                else:
                    sys.stdout.write(f"  {BOLD}Usable Items:{RESET} {RED}None owned! (You need the specific Mega Stone or a Universal Stone){RESET}\n")
        else:
            sys.stdout.write(f"  {BOLD}Status:{RESET} {RED}Not Eligible for Mega Evolution{RESET}\n")
    else:
        sys.stdout.write(f"  {BOLD}Active Companion:{RESET} None (Select a companion from the Roster!)\n")
    
    sys.stdout.write(f"\n  {BOLD}Your Mega Stones:{RESET}\n")
    
    page_size = app.engine.state.get("page_size_mega", 21)
    total_pages = max(1, (len(stones) - 1) // page_size + 1)
    if not hasattr(app, 'mega_page'): app.mega_page = 1
    app.mega_page = max(1, min(app.mega_page, total_pages))
    
    if not stones:
        sys.stdout.write("   You don't own any Mega Stones yet. Find them in the Gacha or Shop!\n")
    else:
        start_idx = (app.mega_page - 1) * page_size
        end_idx = start_idx + page_size
        visible_stones = stones[start_idx:end_idx]

        for i in range(0, len(visible_stones), 3):
            col1 = f"[{visible_stones[i][0]}] {visible_stones[i][1]}"
            col2 = f"[{visible_stones[i+1][0]}] {visible_stones[i+1][1]}" if i + 1 < len(visible_stones) else ""
            col3 = f"[{visible_stones[i+2][0]}] {visible_stones[i+2][1]}" if i + 2 < len(visible_stones) else ""
            sys.stdout.write(f"   {col1:<22} {col2:<22} {col3}\n".rstrip() + "\n")
                
        if total_pages > 1:
            sys.stdout.write(f"\n  ➔ Page {app.mega_page}/{total_pages} - Type '{BOLD}next{RESET}', '{BOLD}prev{RESET}', or '{BOLD}page <N>{RESET}' to navigate!\n")
            
    sys.stdout.write(f"\n  ➔ Type '{BOLD}use <number>{RESET}' to Mega Evolve, or '{BOLD}revert{RESET}' to return to standard form!\n\n")
