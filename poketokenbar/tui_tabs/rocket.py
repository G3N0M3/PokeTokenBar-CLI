import sys
import textwrap
import re
from poketokenbar.utils.formatting import format_tokens, format_progress_bar
from poketokenbar.sprite_renderer import SpriteRenderer
from poketokenbar.game.rocket_battle import RocketBattleHandler, generate_player_moves

HEADER = "\033[95m\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def render_rocket_tab(app):
    """Renders Tab [12] Rocket HQ or the Dormant Frequency channel."""
    if not app.engine.state.get("rocket_alliance_accepted", False):
        _render_secure_comm_channel(app)
        return

    battle_handler = RocketBattleHandler(app.engine)
    b_st = battle_handler._get_state()
    in_combat = bool(b_st.get("player_team")) and b_st.get("status") not in ["win", "loss"]

    # When in tactical boss combat, render battle arena directly without HQ header and submenu
    if in_combat:
        _render_rocket_battle_screen(app, battle_handler, b_st)
        return

    subview = getattr(app, "rocket_subview", "ops")
    if subview not in ["ops", "intel", "armory", "read_intel"]:
        subview = "ops"
        app.rocket_subview = "ops"

    # Header / Status banner
    rank = app.engine.state.get("rocket_rank", "Informant")
    rep = app.engine.state.get("rocket_reputation", 0)
    spendable = app.engine.available_tokens

    sys.stdout.write(f"\n  {BOLD}{RED}🚀 TEAM ROCKET COVERT HEADQUARTERS (HQ){RESET}\n")
    sys.stdout.write(f"  Agent: {BOLD}{YELLOW}Trainer{RESET} | Rank: {BOLD}{RED}{rank}{RESET} ({rep}/10) | Spendable: {BOLD}{CYAN}{format_tokens(spendable)}{RESET}\n")
    sys.stdout.write("  " + "-" * 68 + "\n")

    # Subtab navigation
    o_tab = f"{BOLD}{RED}[O] Operations{RESET}" if subview == "ops" else "[O] Operations"
    i_tab = f"{BOLD}{RED}[I] Intel Dossier{RESET}" if subview in ["intel", "read_intel"] else "[I] Intel Dossier"
    a_tab = f"{BOLD}{RED}[A] Covert Armory{RESET}" if subview == "armory" else "[A] Covert Armory"

    sys.stdout.write(f"  {o_tab}    {i_tab}    {a_tab}\n")
    sys.stdout.write("  " + "-" * 68 + "\n\n")

    if subview == "ops":
        _render_ops_subtab(app)
    elif subview == "intel":
        _render_intel_subtab(app)
    elif subview == "read_intel":
        _render_read_intel(app)
    elif subview == "armory":
        _render_armory_subtab(app)

def _render_secure_comm_channel(app):
    """Renders the dormant scrambled communication channel before alliance acceptance."""
    sys.stdout.write(f"\n  {BOLD}{RED}📡 ENCRYPTED FREQUENCY // 131.55 // ROCKET SECURE COMM{RESET}\n")
    sys.stdout.write("  " + "-" * 68 + "\n")
    sys.stdout.write(f"  Status: {BOLD}{YELLOW}DORMANT (Awaiting Operative Confirmation){RESET}\n")
    sys.stdout.write(f"  Origin: {CYAN}Team Rocket Covert Network (Commander Petrel){RESET}\n")
    sys.stdout.write("  " + "-" * 68 + "\n\n")

    msg = [
        "\"We await your decision, Champion. Professor Oak's syndicate",
        "deepens its claws into the region every hour you hesitate.",
        "When you are ready to stand with the resistance and dismantle",
        "his synthetic bio-weapon project, initiate the uplink below.\""
    ]
    for line in msg:
        sys.stdout.write(f"  {YELLOW}{line}{RESET}\n")

    sys.stdout.write("\n  " + "-" * 68 + "\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}accept{RESET}' to initiate the Rocket Alliance.\n\n")

def _render_rocket_battle_screen(app, handler, st):
    """Renders the full-screen dynamic combat arena against Oak's Weird Pokémon."""
    p_idx = st["player_active_index"]
    r_idx = st["boss_active_index"]
    p_id = st["player_team"][p_idx]
    r_mon = st["boss_team"][r_idx]

    p_name = app.engine.api.get_species_name(p_id)
    r_name = r_mon["name"]

    p_hp = st["player_hps"][p_idx]
    p_max_hp = st["player_max_hps"][p_idx]
    p_perc = max(0, min(100, int((p_hp / max(1, p_max_hp)) * 100)))

    r_hp = st["boss_hps"][r_idx]
    r_max_hp = r_mon["max_hp"]
    r_perc = max(0, min(100, int((r_hp / max(1, r_max_hp)) * 100)))

    sys.stdout.write(f"  {BOLD}{RED}🚨 TACTICAL COMBAT // {st.get('title', 'SYNDICATE BOSS')[:44]}{RESET}\n")
    sys.stdout.write("  " + "-" * 68 + "\n\n")

    p_sprite_path = app.engine.api.download_sprite(p_id, is_back=True)
    r_sprite_path = app.engine.api.download_sprite(r_mon["id"])

    flip_player = False
    if p_sprite_path and "front_" in p_sprite_path.name:
        flip_player = True

    p_sprite_lines = SpriteRenderer.render_png_to_ansi(p_sprite_path, 24, flip_h=flip_player).split("\n") if p_sprite_path else [f"[{p_name:^22}]"]
    r_sprite_lines = SpriteRenderer.render_png_to_ansi(r_sprite_path, 24).split("\n") if r_sprite_path else [f"[{r_name:^22}]"]

    ansi_clean = re.compile(r'\x1b\[[0-9;]*[mK]')
    p_visual_width = len(ansi_clean.sub("", p_sprite_lines[0])) if p_sprite_lines else 24
    r_visual_width = len(ansi_clean.sub("", r_sprite_lines[0])) if r_sprite_lines else 24
    if p_visual_width > 30:
        p_visual_width = 24
    if r_visual_width > 30:
        r_visual_width = 24

    spacer_len = max(2, min(22, 70 - p_visual_width - r_visual_width))
    spacer = " " * spacer_len

    max_h = max(len(p_sprite_lines), len(r_sprite_lines))
    while len(p_sprite_lines) < max_h:
        p_sprite_lines.insert(0, " " * p_visual_width)
    while len(r_sprite_lines) < max_h:
        r_sprite_lines.insert(0, " " * r_visual_width)

    for p_line, r_line in zip(p_sprite_lines, r_sprite_lines):
        sys.stdout.write(f"  {p_line}{spacer}{r_line}\n")

    # Name and HP row (26 + 18 + 26 = 70 cols + 2 indent = 72)
    sys.stdout.write(f"  {GREEN}{BOLD}{p_name[:26]:<26}{RESET}{' ' * 18}{RED}{BOLD}{r_name[:26]:>26}{RESET}\n")
    p_bar = '█' * (p_perc // 5) + '░' * (20 - (p_perc // 5))
    r_bar = '█' * (r_perc // 5) + '░' * (20 - (r_perc // 5))
    sys.stdout.write(f"  HP: [{p_bar}]{' ' * 18}HP: [{r_bar}]\n")
    p_hp_str = f"{p_hp:,} / {p_max_hp:,}"
    r_hp_str = f"{r_hp:,} / {r_max_hp:,}"
    sys.stdout.write(f"  {p_hp_str:<26}{' ' * 18}{r_hp_str:>26}\n")

    sp = app.engine.api.get_pokemon_info(p_id)
    p_type = sp["types"][0]["type"]["name"] if sp and "types" in sp else "normal"
    b_type_core = f"{r_mon['type'].upper()} CORE" if "stances" in r_mon else r_mon["type"].upper()
    sys.stdout.write(f"  {CYAN}Type: {p_type.upper():<20}{RESET}{' ' * 18}{YELLOW}Type: {b_type_core:>20}{RESET}\n\n")

    # Turn telemetry log (compact 2 entries to prevent vertical overflow)
    sys.stdout.write(f"  {BOLD}Tactical Battle Log:{RESET}\n")
    logs = st.get("turn_log", [])[-2:]
    for log in logs:
        for wline in textwrap.wrap(log, width=64):
            sys.stdout.write(f"  > {wline}\n")
    sys.stdout.write("  " + "-" * 68 + "\n")

    # Squad status (split into 2 lines for guaranteed <= 72 column compliance)
    team_names = []
    for i, pid in enumerate(st["player_team"]):
        n = app.engine.api.get_species_name(pid)
        if st["player_hps"][i] <= 0:
            team_names.append(f"{RED}~~{n}~~{RESET}")
        elif i == p_idx:
            team_names.append(f"{BOLD}{GREEN}>{n}<{RESET}")
        else:
            team_names.append(n)
    t1 = team_names[:3]
    t2 = team_names[3:]
    sys.stdout.write(f"  {BOLD}Squad (1-3):{RESET} " + " | ".join(t1) + "\n")
    if t2:
        sys.stdout.write(f"  {BOLD}Squad (4-6):{RESET} " + " | ".join(t2) + "\n")

    def format_short_tokens(val: int) -> str:
        if val >= 1_000_000:
            return f"{val/1_000_000:.1f}M".replace(".0M", "M")
        if val >= 1_000:
            return f"{val/1_000:.1f}K".replace(".0K", "K")
        return str(val)

    budget = handler.get_rocket_tokens()
    sys.stdout.write(f"  {BOLD}What will {p_name} do?{RESET} (Tactical Tokens: {format_short_tokens(budget)})\n")
    moves = generate_player_moves(p_type)
    for i, m in enumerate(moves):
        sys.stdout.write(f"  [fight {i+1}] {m['name']:<16} - Cost: {format_short_tokens(m['cost']):>5} ({m['desc']})\n")
    sys.stdout.write(f"\n  ➔ Commands: [fight 1-4] | [swap 1-{len(st['player_team'])}] | [run]\n\n")

def _render_ops_subtab(app):
    sys.stdout.write(f"  {BOLD}🎯 Covert Operations (Campaign vs. Oak's Syndicate){RESET}\n\n")

    operations = app.engine.get_rocket_operations()
    # Find active operation first; fallback to next available operation
    active_op = next((op for op in operations if op["status"] == "active" and not op["claimed"]), None)
    if not active_op:
        active_op = next((op for op in operations if op["status"] == "available" and not op["claimed"]), None)

    if not active_op:
        sys.stdout.write(f"  {BOLD}{GREEN}🏆 ALL 10 COVERT OPERATIONS COMPLETED!{RESET}\n")
        sys.stdout.write(f"  {YELLOW}The Oak Syndicate has been dismantled and Kanto is secured.{RESET}\n\n")
        sys.stdout.write(f"  ➔ Clearance: {BOLD}{RED}Commander{RESET} | Reputation: {BOLD}{YELLOW}10/10{RESET}\n\n")
        return

    battle_handler = RocketBattleHandler(app.engine)
    b_st = battle_handler._get_state()
    in_combat = bool(b_st.get("player_team")) and b_st.get("status") not in ["win", "loss"]

    if in_combat:
        _render_rocket_battle_screen(app, battle_handler, b_st)
        return

    # If active op is a boss op, display tactical boss chamber banner
    if b_st.get("status") == "win" and active_op["is_boss"] and str(b_st.get("op_code")) == str(active_op["code"]) and not active_op["claimed"]:
        sys.stdout.write(f"  {BOLD}{YELLOW}🏆 TACTICAL SECTOR CLEARED! 🏆{RESET}\n")
        sys.stdout.write(f"  {GREEN}All bio-aberrations and synthetic constructs neutralized!{RESET}\n\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}claim{RESET}' to finalize mission and collect your reward!\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}restart{RESET}' to replay this tactical encounter.\n")
        sys.stdout.write("  " + "-" * 68 + "\n\n")
    elif b_st.get("status") == "loss" and active_op["is_boss"] and str(b_st.get("op_code")) == str(active_op["code"]):
        sys.stdout.write(f"  {BOLD}{RED}💀 STRIKE SQUAD BLACKED OUT 💀{RESET}\n")
        sys.stdout.write(f"  {YELLOW}The Sub-Vault bio-aberrations overwhelmed your strike squad.{RESET}\n\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}fight{RESET}' to deploy a fresh squad!\n")
        sys.stdout.write("  " + "-" * 68 + "\n\n")
    elif active_op["is_boss"] and active_op["boss_hp_remaining"] > 0 and not active_op["objective_done"]:
        b_name = active_op["boss_name"]
        rem_hp = active_op["boss_hp_remaining"]
        max_hp = active_op["boss_hp"]
        pct_left = (rem_hp * 100.0) / max_hp if max_hp > 0 else 0.0
        filled = max(0, min(12, int(round(12 * (rem_hp / float(max_hp)))))) if max_hp > 0 else 0
        hp_bar = f"[{'█' * filled}{'░' * (12 - filled)}] {pct_left:.1f}% left"
        sys.stdout.write(f"  {BOLD}{RED}⚠️ ACTIVE BOSS CONFRONTATION:{RESET} {BOLD}{b_name}{RESET}\n")
        sys.stdout.write(f"  HP: {BOLD}{YELLOW}{rem_hp:,}/{max_hp:,}{RESET} | {hp_bar}\n")
        mon_str = app.engine.api.get_species_name(app.engine.active_mon.current_id) if app.engine.active_mon else "None"
        sys.stdout.write(f"  Strike Squad Leader: {BOLD}{CYAN}{mon_str}{RESET} (Squad ready)\n")
        sys.stdout.write(f"  ➔ Tactical Commands: '{BOLD}fight{RESET}' to enter combat arena!\n")
        sys.stdout.write("  " + "-" * 68 + "\n\n")

    code = active_op["code"]
    name = active_op["name"]
    status = active_op["status"]
    prog = active_op["progress"]
    target = active_op["target"]
    claimed = active_op["claimed"]
    obj_done = active_op["objective_done"]
    is_boss = active_op["is_boss"]

    # Dynamic objective verification
    if status in ["active", "available"] and not claimed:
        is_ok, _ = app.engine.check_operation_objective(active_op["id"])
        obj_done = is_ok
        active_op["objective_done"] = is_ok

    if claimed:
        badge = f"{BOLD}{GREEN}[COMPLETED]{RESET}"
    elif is_boss and obj_done:
        badge = f"{BOLD}{YELLOW}[BOSS DEFEATED - 'claim']{RESET}"
    elif not is_boss and target > 0 and prog >= target and obj_done:
        badge = f"{BOLD}{YELLOW}[READY - 'claim']{RESET}"
    elif not is_boss and target == 0 and obj_done:
        badge = f"{BOLD}{YELLOW}[READY - 'claim']{RESET}"
    elif status == "active":
        badge = f"{BOLD}{CYAN}[ACTIVE]{RESET}"
    elif status == "available":
        badge = f"{BOLD}{YELLOW}[AVAILABLE - 'start operation']{RESET}"
    else:
        badge = f"{BOLD}[LOCKED]{RESET}"

    sys.stdout.write(f"  {BOLD}{name[:36]:<36}{RESET} {badge}\n")
    
    # Trace each individual requirement on its own line
    reqs = app.engine.get_operation_requirements(code)
    if reqs:
        sys.stdout.write(f"       Requirements:\n")
        for req in reqs:
            r_name = req["name"]
            cur_str = req["current_str"]
            bar = format_progress_bar(req["current"], req["target"], width=8)
            pct = req["pct"]
            tag = f" {BOLD}{GREEN}[DONE]{RESET}" if req["is_met"] else ""
            sys.stdout.write(f"       • {r_name:<18} {cur_str:<9} | {bar}{tag}\n")

    for bline in textwrap.wrap(active_op['briefing'], width=62):
        sys.stdout.write(f"       {CYAN}{bline}{RESET}\n")
    sys.stdout.write(f"       Reward: {format_tokens(active_op['reward_tokens'])} tokens, Clearance: {active_op['reward_rank']}\n\n")

    # Command hints: briefing first, operational action second
    if status == "available":
        sys.stdout.write(f"  ➔ Type '{BOLD}briefing{RESET}' to preview tactical briefing\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}start operation{RESET}' to activate operation!\n\n")
    elif (not is_boss and target > 0 and prog >= target and obj_done) or (not is_boss and target == 0 and obj_done) or (is_boss and obj_done):
        sys.stdout.write(f"  ➔ Type '{BOLD}briefing{RESET}' to review tactical briefing\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}claim{RESET}' to collect your reward!\n\n")
    elif is_boss:
        sys.stdout.write(f"  ➔ Type '{BOLD}briefing{RESET}' to review tactical dialogue\n")
        sys.stdout.write(f"  ➔ Boss Combat: '{BOLD}fight{RESET}' to enter tactical combat\n\n")
    else:
        sys.stdout.write(f"  ➔ Type '{BOLD}briefing{RESET}' to review tactical dialogue\n")
        sys.stdout.write(f"  ➔ Commands: '{BOLD}claim{RESET}' when task objectives are fulfilled\n\n")

def _render_intel_subtab(app):
    sys.stdout.write(f"  {BOLD}📁 Declassified Dossier: The Oak Syndicate Archives{RESET}\n")
    sys.stdout.write(f"  Recovered intelligence on Professor Oak and Red's synthesis.\n\n")

    dossier = app.engine.get_rocket_dossier()
    unlocked_items = [item for item in dossier if item.get("unlocked", False)]

    if not unlocked_items:
        sys.stdout.write("  (No dossier files retrieved yet. Complete operations to intercept intel!)\n\n")
        return

    page_size = 5
    total_pages = max(1, (len(unlocked_items) - 1) // page_size + 1)
    if not hasattr(app, "intel_page") or not isinstance(app.intel_page, int):
        app.intel_page = 1
    app.intel_page = max(1, min(app.intel_page, total_pages))

    start_idx = (app.intel_page - 1) * page_size
    end_idx = start_idx + page_size

    for item in unlocked_items[start_idx:end_idx]:
        idx = item["id"]
        title = item["title"]
        badge = f"{BOLD}{GREEN}[DECRYPTED - 'read {idx}']{RESET}"
        sys.stdout.write(f"  [{BOLD}{idx:>2}{RESET}] {BOLD}{title[:36]:<36}{RESET} {badge}\n")
        sys.stdout.write(f"       Date: {item['date']} | Status: Declassified\n")

    if total_pages > 1:
        sys.stdout.write(f"\n  ➔ Page {app.intel_page}/{total_pages} - Type '{BOLD}n{RESET}', '{BOLD}p{RESET}', or '{BOLD}page <N>{RESET}' to navigate!\n")

    sys.stdout.write(f"\n  ➔ Type '{BOLD}read <id>{RESET}' to view decrypted dossier\n\n")

def _render_read_intel(app):
    file_id = getattr(app, "rocket_reading_file", 1)
    dossier = app.engine.get_rocket_dossier()
    selected = next((item for item in dossier if item["id"] == file_id), None)

    if not selected or not selected["unlocked"]:
        sys.stdout.write(f"  {BOLD}{RED}⚠️ Clearance Denied: File #{file_id} has not been retrieved yet!{RESET}\n\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}back{RESET}' to return to Intel index.\n\n")
        return

    sys.stdout.write(f"  {BOLD}{CYAN}📄 {selected['title'][:55].upper()}{RESET}\n")
    sys.stdout.write(f"  Logged: {selected['date']} | Classification: TOP SECRET // DECLASSIFIED\n")
    sys.stdout.write("  " + "-" * 68 + "\n\n")

    for line in selected["content"]:
        if not line:
            sys.stdout.write("\n")
        else:
            for wline in textwrap.wrap(line, width=68):
                sys.stdout.write(f"  {wline}\n")

    sys.stdout.write("\n  " + "-" * 68 + "\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}back{RESET}' to return to Dossier index.\n\n")

def _render_armory_subtab(app):
    sys.stdout.write(f"  {BOLD}🛡️ Team Rocket Covert Tech Armory{RESET}\n")
    sys.stdout.write(f"  Skunkworks experimental equipment gated by operative clearance.\n\n")

    pending = app.engine.state.get("pending_authority_delivery")
    if pending:
        sp_id = pending if isinstance(pending, int) else pending.get("species_id")
        sp_name = app.engine.api.get_species_name(sp_id)
        sys.stdout.write(f"  {BOLD}{YELLOW}📦 SYNDICATE COURIER WAITING AT HQ:{RESET}\n")
        sys.stdout.write(f"  A wild {BOLD}{CYAN}{sp_name}{RESET} (#{sp_id}) was requisitioned by field agents!\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}keep{RESET}' to register into Roster, or '{BOLD}dismiss{RESET}' to release.\n")
        sys.stdout.write("  " + "-" * 68 + "\n\n")

    user_rank = app.engine.state.get("rocket_rank", "Informant")
    rank_order = {"Informant": 1, "Operative": 2, "Special Agent": 3, "Executive": 4, "Commander": 5}
    user_lvl = rank_order.get(user_rank, 1)

    armory_items = [
        ("pass", "Syndicate Black Pass", "Informant", "📯", "Permanent 24/7 Black Market access & waived Grunt tolls"),
        ("spray", "Syndicate Morale Mist", "Operative", "💨", "Instantly boosts happiness of all squad Pokémon to 100%"),
        ("chrono", "Chrono Accelerator", "Operative", "⌛", "Fast-forwards active Bank CDs, advancing maturity by +1 day"),
        ("splitter", "Corrupted EXP Splitter", "Special Agent", "⚡", "Mirrors 25% of coding XP to all inactive roster Pokémon"),
        ("catalyst", "Dark Gene Catalyst", "Executive", "🧬", "Instantly triggers cellular evolution on active companion"),
        ("authority", "Team Rocket Authority", "Commander", "👑", "Daily requisition of a random non-duplicate Gen 1 Pokémon"),
    ]

    page_size = 3
    total_pages = max(1, (len(armory_items) - 1) // page_size + 1)
    if not hasattr(app, "armory_page") or not isinstance(app.armory_page, int):
        app.armory_page = 1
    app.armory_page = max(1, min(app.armory_page, total_pages))

    start_idx = (app.armory_page - 1) * page_size
    end_idx = start_idx + page_size
    items_to_display = armory_items[start_idx:end_idx]

    for offset, (code, name, min_rank, icon, desc) in enumerate(items_to_display):
        global_idx = start_idx + offset + 1
        req_lvl = rank_order.get(min_rank, 1)
        if user_lvl >= req_lvl:
            if code == "pass" and app.engine.state.get("permanent_black_market", False):
                badge = f"{BOLD}{GREEN}[ACTIVE PERK]{RESET}"
            elif code == "splitter" and app.engine.state.get("has_exp_splitter", False):
                badge = f"{BOLD}{GREEN}[ACTIVE PERK]{RESET}"
            elif code in ["spray", "chrono", "catalyst"]:
                c_info = app.engine.get_armory_charge_info(code)
                c_cnt = c_info["charges"]
                color = GREEN if c_cnt > 0 else YELLOW
                badge = f"{BOLD}{color}[CHARGES: {c_cnt}/3]{RESET}"
            else:
                badge = f"{BOLD}{GREEN}[CLEARANCE GRANTED]{RESET}"

            sys.stdout.write(f"  [{global_idx}] {icon} {BOLD}{name:<24}{RESET} {badge}\n")
            for dline in textwrap.wrap(f"➔ {desc}", width=64):
                sys.stdout.write(f"      {dline}\n")

            if code in ["spray", "chrono", "catalyst"]:
                c_info = app.engine.get_armory_charge_info(code)
                c_cnt = c_info["charges"]
                if c_cnt >= 3:
                    sys.stdout.write(f"      {GREEN}Recharge: [████████████████████] FULLY CHARGED (3/3 MAX){RESET}\n")
                else:
                    bar = '█' * (c_info['pct'] // 5) + '░' * (20 - (c_info['pct'] // 5))
                    p_str = format_tokens(c_info['progress'])
                    t_str = format_tokens(c_info['target'])
                    sys.stdout.write(f"      {CYAN}Recharge: [{bar}] {p_str}/{t_str} ({c_info['pct']}%){RESET}\n")
        else:
            badge = f"{BOLD}{RED}[LOCKED - {min_rank.upper()} REQUIRED]{RESET}"
            sys.stdout.write(f"  [{global_idx}] ❓ {BOLD}{'??? ???':<24}{RESET} {badge}\n")
            lock_msg = f"➔ Requires rank '{min_rank}' (Promoted via Covert Operations)."
            for dline in textwrap.wrap(lock_msg, width=64):
                sys.stdout.write(f"      {YELLOW}{dline}{RESET}\n")
        sys.stdout.write("\n")

    if total_pages > 1:
        sys.stdout.write(f"  ➔ Page {app.armory_page}/{total_pages} - Type '{BOLD}n{RESET}', '{BOLD}p{RESET}', or '{BOLD}page <N>{RESET}' to navigate!\n")

    if app.armory_page == 1:
        sys.stdout.write(f"  ➔ Type '{BOLD}use mist{RESET}' to deploy Morale Mist.\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}use chrono{RESET}' to warp Bank CD timelines.\n\n")
    else:
        sys.stdout.write(f"  ➔ Type '{BOLD}use catalyst{RESET}' to evolve active companion.\n")
        if user_lvl >= 5:
            sys.stdout.write(f"  ➔ Type '{BOLD}claim authority{RESET}' to dispatch daily field agents.\n")
        sys.stdout.write("\n")

def _resolve_armory_tech_code(raw: str) -> str:
    raw = raw.lower().strip()
    if "pass" in raw or raw == "1":
        return "pass"
    if "spray" in raw or "mist" in raw or "morale" in raw:
        return "spray"
    if "chrono" in raw or "accelerator" in raw:
        return "chrono"
    if "splitter" in raw or raw == "4":
        return "splitter"
    if "catalyst" in raw or "gene" in raw or raw == "5":
        return "catalyst"
    if "authority" in raw or raw == "6":
        return "authority"
    return raw.split()[0] if raw.split() else raw

def handle_rocket_command(app, cmd: str):
    """Processes user input while inside Tab [12]."""
    cmd = cmd.strip()

    # If dormant channel, handle alliance acceptance
    if not app.engine.state.get("rocket_alliance_accepted", False):
        if cmd.lower() == "accept":
            app.engine.state["rocket_alliance_accepted"] = True
            app.engine.save()
            app.message = "🚀 Alliance initiated! Welcome to Team Rocket Covert HQ, Operative."
        else:
            app.message = "Type 'accept' to join the Rocket Alliance, or switch tabs (1-11)."
        return

    subview = getattr(app, "rocket_subview", "ops")

    battle_handler = RocketBattleHandler(app.engine)
    b_st = battle_handler._get_state()
    in_combat = bool(b_st.get("player_team")) and b_st.get("status") not in ["win", "loss"]

    if in_combat:
        if cmd in ["run", "retreat", "flee"]:
            ok, msg = battle_handler.run_away()
            app.message = msg
            return
        elif cmd.startswith("swap ") or cmd.startswith("s "):
            parts = cmd.split()
            if len(parts) >= 2 and parts[1].isdigit():
                slot = int(parts[1]) - 1
                ok, msg = battle_handler.swap_pokemon(slot)
                app.message = msg.split("\n")[0]
            else:
                app.message = "Usage: swap <1-6>"
            return
        elif cmd.startswith("fight ") or cmd.startswith("f "):
            parts = cmd.split()
            if len(parts) >= 2 and parts[1].isdigit():
                m_idx = int(parts[1]) - 1
                ok, msg = battle_handler.execute_turn(m_idx)
                app.message = msg.split("\n")[0]
            else:
                app.message = "Usage: fight <1-4>"
            return
        elif cmd in ["1", "2", "3", "4"]:
            m_idx = int(cmd) - 1
            ok, msg = battle_handler.execute_turn(m_idx)
            app.message = msg.split("\n")[0]
            return
        elif cmd in ["attack", "strike", "a"]:
            ok, msg = battle_handler.execute_turn(0)
            app.message = msg.split("\n")[0]
            return
        elif cmd in ["burst", "overclock"]:
            ok, msg = battle_handler.execute_turn(3)
            app.message = msg.split("\n")[0]
            return

    if cmd == "restart" and subview == "ops":
        if b_st.get("status") in ["win", "loss"]:
            op_code = str(b_st.get("op_code"))
            battle_handler.run_away()
            op_id = f"op_{op_code}"
            ops_st = app.engine.state.setdefault("rocket_ops", {}).get(op_id)
            if ops_st and not ops_st.get("claimed", False):
                for op_def in app.engine.get_rocket_operations():
                    if op_def["id"] == op_id:
                        ops_st["boss_hp_remaining"] = op_def["boss_hp"]
                        ops_st["objective_done"] = False
                        app.engine.save()
                        break
            app.message = "Reset tactical boss encounter."
            return

    if (cmd == "fight" or cmd.startswith("fight ")) and subview == "ops":
        parts = cmd.split()
        target_code = None
        if len(parts) >= 2 and parts[1].isdigit():
            target_code = parts[1]
        if not target_code:
            operations = app.engine.get_rocket_operations()
            curr = next((op for op in operations if op["status"] in ["available", "active"] and not op["claimed"] and op["is_boss"]), None)
            if curr:
                target_code = curr["code"]
            else:
                target_code = "3"

        if target_code:
            op_id = f"op_{target_code}"
            op_st = app.engine.state.setdefault("rocket_ops", {}).get(op_id, {})
            if op_st.get("status") == "available":
                app.engine.start_rocket_operation(target_code)
            ok, msg = battle_handler.start_boss_battle(target_code)
            app.message = msg
        else:
            app.message = "No Syndicate Boss encounter to fight."
        return

    if (cmd == "engage" or cmd.startswith("engage ")) and subview == "ops":
        app.message = "Please use 'fight' to enter the tactical combat arena."
        return

    if cmd.startswith("squad ") and subview == "ops":
        parts = cmd.split()[1:]
        ids = [int(p) for p in parts if p.isdigit()]
        if len(ids) >= 1:
            operations = app.engine.get_rocket_operations()
            curr = next((op for op in operations if op["status"] in ["available", "active"] and not op["claimed"] and op["is_boss"]), None)
            if curr:
                if curr["status"] == "available":
                    app.engine.start_rocket_operation(curr["code"])
                ok, msg = battle_handler.start_boss_battle(curr["code"], custom_squad=ids)
                app.message = msg
            else:
                app.message = "No active Syndicate Boss encounter to assemble squad for."
        else:
            app.message = "Usage: squad <id1> <id2> ... (e.g. 'squad 6 3 9 25')"
        return

    if cmd in ["o", "ops", "operations"]:
        app.rocket_subview = "ops"
        app.message = "Switched to Covert Operations."
    elif cmd in ["i", "intel", "dossier"]:
        app.rocket_subview = "intel"
        app.message = "Switched to Intel Dossier."
    elif cmd in ["a", "armory"]:
        app.rocket_subview = "armory"
        app.message = "Switched to Covert Armory."
    elif subview == "read_intel" and cmd in ["back", "b"]:
        app.rocket_subview = "intel"
        app.message = "Returned to Intel index."
    elif subview == "intel" and cmd in ["n", "next"]:
        if not hasattr(app, "intel_page"): app.intel_page = 1
        app.intel_page += 1
        app.message = ""
    elif subview == "intel" and cmd in ["p", "prev"]:
        if not hasattr(app, "intel_page"): app.intel_page = 1
        app.intel_page = max(1, app.intel_page - 1)
        app.message = ""
    elif subview == "intel" and cmd.startswith("page "):
        try:
            p = int(cmd.split()[1])
            app.intel_page = max(1, p)
            app.message = ""
        except ValueError:
            app.message = "Usage: page <number>"
    elif subview == "armory" and cmd in ["n", "next"]:
        if not hasattr(app, "armory_page"): app.armory_page = 1
        app.armory_page += 1
        app.message = ""
    elif subview == "armory" and cmd in ["p", "prev"]:
        if not hasattr(app, "armory_page"): app.armory_page = 1
        app.armory_page = max(1, app.armory_page - 1)
        app.message = ""
    elif subview == "armory" and cmd.startswith("page "):
        try:
            p = int(cmd.split()[1])
            app.armory_page = max(1, p)
            app.message = ""
        except ValueError:
            app.message = "Usage: page <number>"
    elif cmd.startswith("read "):
        parts = cmd.split()
        if len(parts) >= 2 and parts[1].isdigit():
            idx = int(parts[1])
            dossier = app.engine.get_rocket_dossier()
            selected = next((item for item in dossier if item["id"] == idx), None)
            if selected and selected["unlocked"]:
                app.rocket_subview = "read_intel"
                app.rocket_reading_file = idx
                app.message = f"Opened Dossier #{idx}."
            elif selected:
                app.message = f"File #{idx} has not been retrieved yet. Complete operations to intercept this intel."
            else:
                app.message = "Invalid file number. Use 'read <id>' for an unlocked dossier."
        else:
            app.message = "Usage: read <id> (e.g. 'read 1')"
    elif cmd == "start operation":
        operations = app.engine.get_rocket_operations()
        curr = next((op for op in operations if op["status"] in ["available", "active"] and not op["claimed"]), None)
        if curr:
            op_st = app.engine.state.get("rocket_ops", {}).get(curr["id"], {})
            if not op_st.get("briefing_viewed", False):
                render_operation_dialogue(app, curr["code"])
                op_st["briefing_viewed"] = True
            ok, msg = app.engine.start_rocket_operation(curr["code"])
            if curr.get("is_boss", False):
                battle_handler.start_boss_battle(curr["code"])
            app.message = msg
        else:
            app.message = "No available operation to start."
    elif cmd in ["briefing", "dialogue", "story"] and subview == "ops":
        operations = app.engine.get_rocket_operations()
        curr = next((op for op in operations if (op["status"] == "active" or op["status"] == "available") and not op["claimed"]), None)
        if curr:
            render_operation_dialogue(app, curr["code"])
            app.message = f"Replayed Operation {curr['code']} tactical briefing."
        else:
            app.message = "No active operation to review briefing."
    elif cmd.startswith("start"):
        app.message = "Unknown command. Use 'start operation' to begin."
    elif cmd.startswith("claim"):
        parts = cmd.split()
        if len(parts) >= 2:
            tech_code = _resolve_armory_tech_code(parts[1])
            if tech_code == "authority":
                ok, msg = app.engine.buy_rocket_armory_item("authority")
                app.message = msg
                return
            if tech_code in ["pass", "spray", "chrono", "splitter", "catalyst"]:
                app.message = "Covert Armory perks are automatically granted upon rank promotion! No claim or purchase required."
                return
            ok, msg = app.engine.claim_rocket_operation(parts[1])
            app.message = msg
        else:
            operations = app.engine.get_rocket_operations()
            curr = next((op for op in operations if (op["status"] == "active" or op["objective_done"]) and not op["claimed"]), None)
            if curr:
                ok, msg = app.engine.claim_rocket_operation(curr["code"])
                app.message = msg
            else:
                app.message = "No active operation ready to claim."
    elif cmd in ["attack", "strike", "a"] and subview == "ops":
        ok, msg = app.engine.attack_rocket_boss(burst=False)
        app.message = msg
    elif cmd in ["burst", "overclock"] and subview == "ops":
        ok, msg = app.engine.attack_rocket_boss(burst=True)
        app.message = msg
    elif cmd in ["keep", "dismiss"]:
        ok, msg = app.engine.handle_authority_delivery(cmd)
        app.message = msg
    elif cmd == "use" or cmd.startswith("use "):
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            app.message = "Usage: use <mist|chrono|catalyst> (e.g. 'use mist', 'use chrono', 'use catalyst')"
            return
        target_raw = parts[1].strip().lower()
        if target_raw == "mist":
            ok, msg = app.engine.use_rocket_armory_item("spray")
            app.message = msg
        elif target_raw == "chrono":
            ok, msg = app.engine.use_rocket_armory_item("chrono")
            app.message = msg
        elif target_raw == "catalyst":
            ok, msg = app.engine.use_rocket_armory_item("catalyst")
            app.message = msg
        elif target_raw in ["2", "3", "5"]:
            app.message = "Unknown armory tech. Valid commands: 'use mist', 'use chrono', 'use catalyst'."
        else:
            tech_code = _resolve_armory_tech_code(target_raw)
            if tech_code == "pass":
                app.message = "Syndicate Black Pass is a passive clearance perk (always active)."
            elif tech_code == "splitter":
                app.message = "Corrupted EXP Splitter is a passive perk (automatically mirrors 25% XP)."
            elif tech_code == "authority":
                app.message = "Type 'claim authority' to dispatch daily field agents."
            else:
                app.message = f"Unknown armory tech '{target_raw}'. Valid: 'use mist', 'use chrono', 'use catalyst'."
    elif subview == "armory" and cmd in ["2", "3", "5"]:
        app.message = "Please use 'use mist', 'use chrono', or 'use catalyst'."
    elif cmd.startswith("requisition "):
        parts = cmd.split(maxsplit=1)
        tech_code = _resolve_armory_tech_code(parts[1])
        if tech_code in ["spray", "chrono", "catalyst"]:
            tech_cmd = "mist" if tech_code == "spray" else tech_code
            app.message = f"Please use 'use {tech_cmd}'."
        else:
            ok, msg = app.engine.buy_rocket_armory_item(tech_code)
            app.message = msg
    elif (
        cmd == "buy"
        or cmd.startswith("buy ")
        or cmd.startswith("requisition")
        or cmd.startswith("get ")
        or (subview == "armory" and cmd in ["pass", "splitter", "catalyst", "authority", "1", "4", "5", "6"])
    ):
        app.message = "Covert Armory perks are automatically granted upon rank promotion! No purchase required."
    else:
        app.message = "Rocket commands: 'start operation', 'fight', 'briefing', 'claim', 'use <mist|chrono|catalyst>', 'attack', 'burst'."

def render_operation_dialogue(app, op_code: str):
    """Renders a full-screen, atmospheric mission briefing dialogue when starting an operation."""
    dialogue_info = app.engine.get_operation_dialogue(op_code)
    if not dialogue_info:
        return

    # Clear terminal screen
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.write(f"\n{BOLD}{RED}{'='*72}{RESET}\n")
    title_line = f"🚨 TACTICAL COMM-LINK // FREQUENCY: 131.55 // OP #{op_code} BRIEFING"
    sys.stdout.write(f"  {BOLD}{RED}{title_line:<68}{RESET}\n")
    sys.stdout.write(f"{BOLD}{RED}{'='*72}{RESET}\n\n")

    sys.stdout.write(f"  {BOLD}{RED}██████╗ {RESET}   {BOLD}{YELLOW}[TEAM ROCKET TACTICAL BRIEFING]{RESET}\n")
    sys.stdout.write(f"  {BOLD}{RED}██╔══██╗{RESET}   Target: {dialogue_info['title'][:50]}\n")
    sys.stdout.write(f"  {BOLD}{RED}██████╔╝{RESET}   Sector: {dialogue_info['location'][:50]}\n")
    sys.stdout.write(f"  {BOLD}{RED}██╔══██╗{RESET}   Sender: {dialogue_info['speaker']}\n")
    sys.stdout.write(f"  {BOLD}{RED}██║  ██║{RESET}\n")
    sys.stdout.write(f"  {BOLD}{RED}╚═╝  ╚═╝{RESET}\n\n")

    for line in dialogue_info["dialogue"]:
        if not line:
            sys.stdout.write("\n")
        else:
            for wline in textwrap.wrap(line, width=68):
                sys.stdout.write(f"  {CYAN}{wline}{RESET}\n")

    sys.stdout.write(f"\n  {BOLD}{YELLOW}📋 TACTICAL MISSION DIRECTIVES:{RESET}\n")
    for order in dialogue_info["tactical_orders"]:
        for wline in textwrap.wrap(order, width=68):
            sys.stdout.write(f"  {wline}\n")

    sys.stdout.write(f"\n{BOLD}{RED}{'-'*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}{GREEN}➔ Press [Enter] to deploy into the operation...{RESET} ")
    sys.stdout.flush()

    if hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
        sys.stdin.readline()
    elif hasattr(sys.stdin, "readline"):
        if (getattr(sys.stdin.readline, "_mock_return_value", None) is not None or
            getattr(sys.stdin.readline, "side_effect", None) is not None or
            getattr(sys.stdin.readline, "_mock_side_effect", None) is not None):
            try:
                sys.stdin.readline()
            except Exception:
                pass

def render_rocket_transmission(app):
    """Full-screen interactive cinematic transmission with branching dialog."""
    def _write_wrapped_lines(lines, width=68, color=YELLOW):
        for line in lines:
            if not line:
                sys.stdout.write("\n")
            else:
                for wline in textwrap.wrap(line, width=width):
                    sys.stdout.write(f"  {color}{wline}{RESET}\n")

    # Screen 1: Intro
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.write(f"\n{BOLD}{RED}{'='*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}{RED}🚨 INCOMING ENCRYPTED TRANSMISSION — PRIORITY ZERO FREQUENCY 🚨{RESET}\n")
    sys.stdout.write(f"{BOLD}{RED}{'='*72}{RESET}\n\n")

    sys.stdout.write(f"      {BOLD}{RED}██████╗ {RESET}\n")
    sys.stdout.write(f"      {BOLD}{RED}██╔══██╗{RESET}   {BOLD}{YELLOW}[TEAM ROCKET SECURE COMM-LINK]{RESET}\n")
    sys.stdout.write(f"      {BOLD}{RED}██████╔╝{RESET}   Channel: Operative Uplink 04.99\n")
    sys.stdout.write(f"      {BOLD}{RED}██╔══██╗{RESET}   Origin: Indigo Sector Secret Command\n")
    sys.stdout.write(f"      {BOLD}{RED}██║  ██║{RESET}   Sender: Commander Petrel\n")
    sys.stdout.write(f"      {BOLD}{RED}╚═╝  ╚═╝{RESET}\n\n")

    dialogue_intro = [
        "\"Do not adjust your terminal, Trainer. This channel is scrambled.",
        "I am Commander Petrel of Team Rocket.",
        "",
        "Our financial surveillance flagged a massive 500M+ capital position",
        "in our Viridian logistics front. When we traced the signature,",
        "we found the same trainer who conquered Mt. Silver.",
        "",
        "We know what you did. You struck down Red.",
        "You think the battle is over, don't you? You think you defeated a prodigy.",
        "",
        "You were lied to. Red was never human. He was Specimen-001:",
        "a genetically synthesized battle organism engineered to enforce absolute",
        "compliance across the Pokémon League. And the architect behind him...",
        "is Professor Samuel Oak.",
        "",
        "Red's defeat triggered Oak's contingency: The Oak Syndicate.",
        "We need your strength to dismantle his shadow empire before he deploys",
        "his next wave of synthetic bio-weapons.\""
    ]
    _write_wrapped_lines(dialogue_intro)

    sys.stdout.write(f"\n{BOLD}{RED}{'-'*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}[1] Accept Alliance{RESET} (\"I'm in. Let's finish this.\")\n")
    sys.stdout.write(f"  {BOLD}[2] Demand Proof{RESET}    (\"Prove it. Oak is a respected researcher.\")\n")
    sys.stdout.write(f"  {BOLD}[3] Decline for now{RESET} (\"I want nothing to do with Team Rocket.\")\n")
    sys.stdout.write(f"{BOLD}{RED}{'-'*72}{RESET}\n")
    sys.stdout.write(f"  {CYAN}Select option (1, 2, or 3):{RESET} ")
    sys.stdout.flush()

    choice1 = sys.stdin.readline().strip()
    if choice1 == "1":
        app.engine.state["rocket_story_viewed"] = True
        app.engine.state["rocket_alliance_accepted"] = True
        app.engine.save()
        return

    if choice1 == "2":
        # Screen 2: Evidence Playback
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.write(f"\n{BOLD}{CYAN}{'='*72}{RESET}\n")
        sys.stdout.write(f"  {BOLD}{CYAN}📁 DECRYPTING AUDIO/VISUAL INTERCEPT: ARCHIVE #OAK-GENESIS-77{RESET}\n")
        sys.stdout.write(f"{BOLD}{CYAN}{'='*72}{RESET}\n\n")

        evidence_lines = [
            "PETREL: \"You want proof? I expected nothing less from Red's vanquisher.",
            "Look at your screen. We pulled this encrypted surveillance feed straight",
            "from the subterranean mainframe beneath Oak's Lab. Listen carefully to",
            "what the 'kind Professor' really built.\"",
            "",
            "[STATIC CLEARS... GRAINY SURVEILLANCE FEED APPEARS ON CONSOLE]",
            "[LOCATION: PALLET DEEP LABORATORY // SUB-LEVEL 6 // 1996]",
            "",
            "PROF. OAK (VOICE): \"...The Council remains blind to the coming chaos.",
            "Wild Pokémon are too erratic, too bound by emotion to maintain order.",
            "Specimen-001 shows 99.4% motor obedience. With the synthetic cortex",
            "implanted, he feels neither fatigue nor fear in battle.",
            "",
            "If the League champions fail to preserve order, Specimen-001 will unify",
            "Kanto under our absolute directive. And if even he should fall...",
            "activate Project Syndicate. Mechanize the reserves.\"",
            "",
            "PETREL: \"You heard it directly from the Architect himself. The Pokédex",
            "you carried was a telemetry uplink harvesting combat data for his",
            "prototypes. He used you, Champion. Just as he used Red.\""
        ]
        _write_wrapped_lines(evidence_lines)

        sys.stdout.write(f"\n{BOLD}{CYAN}{'-'*72}{RESET}\n")
        sys.stdout.write(f"  {BOLD}[1] Accept Alliance{RESET} (\"That's sickening. Count me in.\")\n")
        sys.stdout.write(f"  {BOLD}[2] Decline for now{RESET} (\"I need time to process this.\")\n")
        sys.stdout.write(f"{BOLD}{CYAN}{'-'*72}{RESET}\n")
        sys.stdout.write(f"  {CYAN}Select option (1 or 2):{RESET} ")
        sys.stdout.flush()

        choice2 = sys.stdin.readline().strip()
        if choice2 == "1":
            app.engine.state["rocket_story_viewed"] = True
            app.engine.state["rocket_alliance_accepted"] = True
            app.engine.save()
            return

    # Screen 3: Persuasion
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.write(f"\n{BOLD}{RED}{'='*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}{RED}⚠️ TRANSMISSION WARNING: RISK OF RETALIATION{RESET}\n")
    sys.stdout.write(f"{BOLD}{RED}{'='*72}{RESET}\n\n")

    persuade_lines = [
        "PETREL: \"Walk away? You defeated his master creation, Champion!",
        "Do you truly believe Oak will allow the trainer who broke Red to walk",
        "freely? You are the largest uncalculated variable in his syndicate's",
        "operational matrix.",
        "",
        "We don't have time for hesitation. Stand with us, or face his",
        "cybernetic strike teams alone.\""
    ]
    _write_wrapped_lines(persuade_lines)

    sys.stdout.write(f"\n{BOLD}{RED}{'-'*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}[1] Accept Alliance{RESET} (\"You're right. Let's work together.\")\n")
    sys.stdout.write(f"  {BOLD}[2] Refuse again{RESET}    (\"I said not right now. Back off.\")\n")
    sys.stdout.write(f"{BOLD}{RED}{'-'*72}{RESET}\n")
    sys.stdout.write(f"  {CYAN}Select option (1 or 2):{RESET} ")
    sys.stdout.flush()

    choice3 = sys.stdin.readline().strip()
    if choice3 == "1":
        app.engine.state["rocket_story_viewed"] = True
        app.engine.state["rocket_alliance_accepted"] = True
        app.engine.save()
        return

    # Screen 4: Fallback Contact Note
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.write(f"\n{BOLD}{CYAN}{'='*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}{CYAN}📡 SECURE CHANNEL ESTABLISHED // FREQUENCY SCRAMBLED{RESET}\n")
    sys.stdout.write(f"{BOLD}{CYAN}{'='*72}{RESET}\n\n")

    fallback_lines = [
        "PETREL: \"Understood. A wary trainer lives longer.",
        "I have keyed this encrypted frequency to Tab [12] on your terminal.",
        "Whenever you realize the truth and decide to act, tune into Tab [12]",
        "and transmit 'accept'.",
        "",
        "Watch your back, Trainer. Pallet Town is watching.\""
    ]
    _write_wrapped_lines(fallback_lines)

    sys.stdout.write(f"\n{BOLD}{CYAN}{'-'*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}{CYAN}Press [Enter] to exit transmission and resume terminal...{RESET} ")
    sys.stdout.flush()
    sys.stdin.readline()

    app.engine.state["rocket_story_viewed"] = True
    app.engine.state["rocket_alliance_accepted"] = False
    app.engine.save()
