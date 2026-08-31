import sys
BOLD = "\033[1m"
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
from poketokenbar.sprite_renderer import SpriteRenderer
from poketokenbar.game.red_battle import RedBattleHandler, RED_TEAM, generate_player_moves

def render_red_tab(app):
    
    handler = RedBattleHandler(app.engine)
    st = handler._get_state()
    
    if st.get("status") == "win":
        sys.stdout.write(f"  {BOLD}{YELLOW}🏆 HALL OF FAME 🏆{RESET}\n\n")
        sys.stdout.write(f"  You defeated PKMN Trainer Red!\n")
        sys.stdout.write(f"  Total Wins: {app.engine.state.get('red_wins', 0)}\n\n")
        
        hof = app.engine.state.get("red_hof", [])
        if hof:
            last_team = hof[-1]
            names = [app.engine.api.get_species_name(pid) for pid in last_team]
            sys.stdout.write(f"  {CYAN}Winning Team:{RESET} {', '.join(names)}\n\n")
            
        sys.stdout.write(f"  Type '{BOLD}restart{RESET}' to challenge him again!\n")
        return

    if st.get("status") == "loss":
        sys.stdout.write(f"  {BOLD}{RED}You blacked out...{RESET}\n\n")
        sys.stdout.write(f"  Red's team was too strong this time.\n\n")
        sys.stdout.write(f"  Type '{BOLD}restart{RESET}' to assemble a new team and try again!\n")
        return
    
    if not st.get("player_team"):
        sys.stdout.write(f"  {BOLD}Red silently stares at you from the snowy peak...{RESET}\n")
        sys.stdout.write(f"  {YELLOW}You must assemble a party of 6 Pokémon to challenge him!{RESET}\n\n")
        sys.stdout.write(f"  Type '{BOLD}assemble <dex_1> ... <dex_6>{RESET}' (use Pokédex IDs).\n")
        sys.stdout.write(f"  Example: assemble 3 6 9 25 143 149\n")
        return
        
    
    
    p_idx = st["player_active_index"]
    r_idx = st["red_active_index"]
    p_id = st["player_team"][p_idx]
    
    # Red's Pokemon info
    r_mon = st["red_team"][r_idx]
    r_hp = st["red_hps"][r_idx]
    r_max_hp = r_mon["max_hp"]
    r_perc = max(0, int((r_hp / r_max_hp) * 100))
    
    # Player's Pokemon info
    p_hp = st["player_hps"][p_idx]
    p_max_hp = st["player_max_hps"][p_idx]
    p_perc = max(0, int((p_hp / max(1, p_max_hp)) * 100))
    p_name = app.engine.api.get_species_name(p_id)
    
    p_sprite_path = app.engine.api.download_sprite(p_id, is_back=True)
    r_sprite_path = app.engine.api.download_sprite(r_mon["id"])
    
    p_sprite_lines = SpriteRenderer.render_png_to_ansi(p_sprite_path, 30).split("\n") if p_sprite_path else [f"[ {p_name} ]"]
    r_sprite_lines = SpriteRenderer.render_png_to_ansi(r_sprite_path, 30).split("\n") if r_sprite_path else [f"[ {r_mon['name']} ]"]
    
    # Find visual width of p_sprite_lines for alignment
    p_visual_width = 30
    if p_sprite_lines and p_sprite_path:
        p_visual_width = len(p_sprite_lines[0].replace("\033[0m", "").replace("\033[", "").replace("38;2;", "").replace("m▀", "").replace("m", "").replace(";", ""))
        if p_visual_width > 50: p_visual_width = 30 # fallback if regex-ish replacement failed
        
    # Bottom align sprites by padding the top of the shorter one
    max_h = max(len(p_sprite_lines), len(r_sprite_lines))
    while len(p_sprite_lines) < max_h:
        p_sprite_lines.insert(0, " " * p_visual_width)
    while len(r_sprite_lines) < max_h:
        r_sprite_lines.insert(0, " " * 30)
        
    for p_line, r_line in zip(p_sprite_lines, r_sprite_lines):
        sys.stdout.write(f"  {p_line}        {r_line}\n")
        
    # HP Bars
    sys.stdout.write(f"  {GREEN}{BOLD}{p_name:<28}{RESET}          {RED}{BOLD}Red's {r_mon['name']}{RESET}\n")
    sys.stdout.write(f"  HP: [{'█' * (p_perc//5)}{'░' * (20 - p_perc//5)}]          HP: [{'█' * (r_perc//5)}{'░' * (20 - r_perc//5)}]\n")
    sys.stdout.write(f"  {p_hp:,} / {p_max_hp:<22,}      {r_hp:,} / {r_max_hp:,}\n")
    
    # Turn log
    sys.stdout.write(f"  {BOLD}Battle Log:{RESET}\n")
    # Show only last 3 logs to save vertical space
    logs = st.get("turn_log", [])[-3:]
    for log in logs:
        sys.stdout.write(f"  > {log}\n")
        
    sys.stdout.write("  " + "=" * 68 + "\n")
    
    # Team display
    team_names = []
    for i, pid in enumerate(st["player_team"]):
        n = app.engine.api.get_species_name(pid)
        if st["player_hps"][i] <= 0:
            team_names.append(f"{RED}~~{n}~~{RESET}")
        elif i == p_idx:
            team_names.append(f"{BOLD}{GREEN}>{n}<{RESET}")
        else:
            team_names.append(n)
    sys.stdout.write(f"  {BOLD}Your Team:{RESET} " + ", ".join(team_names) + "\n")
    
    # Battle Menu
    sys.stdout.write(f"  {BOLD}What will {p_name} do?{RESET} (Spendable: {app.engine.available_tokens:,})\n")
    
    # Generate moves
    sp = app.engine.api.get_pokemon_info(p_id)
    if sp and "types" in sp:
        p_type = sp["types"][0]["type"]["name"]
    else:
        p_type = "normal"
    moves = generate_player_moves(p_type)
    
    for i, m in enumerate(moves):
        sys.stdout.write(f"  [fight {i+1}] {m['name']:<15} - Cost: {m['cost']:>8,} tokens ({m['desc']})\n")
        
    sys.stdout.write(f"\n  [swap 1-6] Swap Pokémon (Currently Active: Slot {p_idx+1})\n")
    sys.stdout.write(f"  [run]      Flee the battle (Resets Red's team)\n")
    
def handle_red_command(app, cmd: str):
    if cmd == "restart":
        st = app.engine.state.get("red_battle_state", {})
        if st.get("status") in ["win", "loss"]:
            app.engine.state.pop("red_battle_state", None)
            app.engine.save()
            app.message = "Red battle restarted. Assemble your team!"
        else:
            app.message = "You can only restart after the battle ends."
        return

    handler = RedBattleHandler(app.engine)
    parts = cmd.split()
    
    if cmd.startswith("assemble"):
        if len(parts) != 7:
            app.message = "Usage: assemble <id1> <id2> <id3> <id4> <id5> <id6>"
            return
        try:
            ids = [int(x) for x in parts[1:]]
        except ValueError:
            app.message = "IDs must be numbers!"
            return
            
        ok, msg = handler.assemble_team(ids)
        app.message = msg
        
    elif cmd.startswith("fight"):
        if len(parts) != 2:
            app.message = "Usage: fight <1-4>"
            return
        try:
            move_idx = int(parts[1]) - 1
            ok, msg = handler.execute_turn(move_idx)
            app.message = msg if not ok else "Turn ended."
        except ValueError:
            app.message = "Invalid move number."
            
    elif cmd.startswith("swap"):
        if len(parts) != 2:
            app.message = "Usage: swap <1-6>"
            return
        try:
            idx = int(parts[1]) - 1
            ok, msg = handler.swap_pokemon(idx)
            app.message = msg
        except ValueError:
            app.message = "Invalid slot number."
            
    elif cmd == "run":
        ok, msg = handler.run_away()
        app.message = msg
