import sys
import textwrap
from poketokenbar.utils.formatting import format_tokens, format_progress_bar

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
    sys.stdout.write(f"  ➔ Type '{BOLD}accept{RESET}' or '{BOLD}1{RESET}' to initiate the Rocket Alliance.\n")
    sys.stdout.write(f"  ➔ Switch to any other tab ('1' through '11') at any time.\n\n")

def _render_ops_subtab(app):
    sys.stdout.write(f"  {BOLD}🎯 Covert Operations (Campaign vs. Oak's Syndicate){RESET}\n")
    sys.stdout.write(f"  Complete 10 operations to dismantle Oak's secret facilities.\n\n")

    operations = app.engine.get_rocket_operations()
    active_op = next((op for op in operations if op["status"] == "active"), None)

    # If an active op is a boss op, display tactical boss chamber banner
    if active_op and active_op["is_boss"] and active_op["boss_hp_remaining"] > 0:
        b_name = active_op["boss_name"]
        rem_hp = active_op["boss_hp_remaining"]
        max_hp = active_op["boss_hp"]
        bar = format_progress_bar(max_hp - rem_hp, max_hp, width=12)
        pct = (rem_hp * 100) // max_hp if max_hp > 0 else 0
        sys.stdout.write(f"  {BOLD}{RED}⚠️ ACTIVE BOSS CONFRONTATION:{RESET} {BOLD}{b_name}{RESET}\n")
        sys.stdout.write(f"  HP: {BOLD}{YELLOW}{rem_hp:,}/{max_hp:,}{RESET} | {bar} ({pct}% left)\n")
        mon_str = app.engine.api.get_species_name(app.engine.active_mon.current_id) if app.engine.active_mon else "None"
        sys.stdout.write(f"  Vanguard Companion: {BOLD}{CYAN}{mon_str}{RESET}\n")
        sys.stdout.write(f"  ➔ Tactical Commands: '{BOLD}attack{RESET}' | '{BOLD}burst{RESET}' (5M tokens: +5,000 DMG)\n")
        sys.stdout.write("  " + "-" * 68 + "\n\n")

    for op in operations:
        code = op["code"]
        name = op["name"]
        status = op["status"]
        prog = op["progress"]
        target = op["target"]
        claimed = op["claimed"]
        obj_done = op["objective_done"]
        is_boss = op["is_boss"]

        if claimed:
            badge = f"{BOLD}{GREEN}[COMPLETED]{RESET}"
        elif is_boss and obj_done:
            badge = f"{BOLD}{YELLOW}[BOSS DEFEATED - 'claim {code}']{RESET}"
        elif not is_boss and target > 0 and prog >= target and obj_done:
            badge = f"{BOLD}{YELLOW}[READY - 'claim {code}']{RESET}"
        elif status == "active":
            badge = f"{BOLD}{CYAN}[ACTIVE]{RESET}"
        elif status == "available":
            badge = f"{BOLD}{YELLOW}[AVAILABLE - 'start {code}']{RESET}"
        else:
            badge = f"{BOLD}[LOCKED]{RESET}"

        sys.stdout.write(f"  [{BOLD}{code:>2}{RESET}] {BOLD}{name[:38]:<38}{RESET} {badge}\n")
        if target > 0:
            bar = format_progress_bar(prog, target, width=8)
            pct = (prog * 100) // target if target > 0 else 100
            sys.stdout.write(f"       Tokens: {format_tokens(prog)}/{format_tokens(target)} | {bar} ({pct}%)\n")
        for tline in textwrap.wrap(f"Task: {op['target_desc']}", width=64):
            sys.stdout.write(f"       {tline}\n")
        for bline in textwrap.wrap(op['briefing'], width=64):
            sys.stdout.write(f"       {CYAN}{bline}{RESET}\n")
        sys.stdout.write(f"       Reward: {format_tokens(op['reward_tokens'])} tokens, Clearance: {op['reward_rank']}\n\n")

    sys.stdout.write(f"  ➔ Commands: '{BOLD}start <id>{RESET}' (e.g. 'start 1') | '{BOLD}claim <id>{RESET}'\n")
    sys.stdout.write(f"  ➔ Boss Combat: '{BOLD}attack{RESET}' | '{BOLD}burst{RESET}' (Op 3, 6, 9, 10)\n")
    sys.stdout.write(f"  ➔ Switch view: '{BOLD}i{RESET}' for Intel Dossier | '{BOLD}a{RESET}' for Armory\n\n")

def _render_intel_subtab(app):
    sys.stdout.write(f"  {BOLD}📁 Declassified Dossier: The Oak Syndicate Archives{RESET}\n")
    sys.stdout.write(f"  Recovered intelligence on Professor Oak and Red's synthesis.\n\n")

    dossier = app.engine.get_rocket_dossier()
    for item in dossier:
        idx = item["id"]
        title = item["title"]
        unlocked = item["unlocked"]
        if unlocked:
            badge = f"{BOLD}{GREEN}[DECRYPTED - 'read {idx}']{RESET}"
            sys.stdout.write(f"  [{BOLD}{idx:>2}{RESET}] {BOLD}{title[:36]:<36}{RESET} {badge}\n")
            sys.stdout.write(f"       Date: {item['date']} | Status: Declassified\n")
        else:
            badge = f"{BOLD}{YELLOW}[LOCKED - CLEAR OP {idx}]{RESET}"
            sys.stdout.write(f"  [{idx:>2}] {title[:36]:<36} {badge}\n")
            sys.stdout.write(f"       Clearance: Requires Operation {idx} completion\n")

    sys.stdout.write(f"\n  ➔ Type '{BOLD}read <1-10>{RESET}' to decrypt a dossier (e.g. 'read 1')\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}o{RESET}' to return to Operations menu\n\n")

def _render_read_intel(app):
    file_id = getattr(app, "rocket_reading_file", 1)
    dossier = app.engine.get_rocket_dossier()
    selected = next((item for item in dossier if item["id"] == file_id), None)

    if not selected or not selected["unlocked"]:
        sys.stdout.write(f"  {BOLD}{RED}⚠️ Clearance Denied: File #{file_id} is encrypted!{RESET}\n\n")
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
    sys.stdout.write(f"  ➔ Type '{BOLD}back{RESET}' or '{BOLD}i{RESET}' to return to Dossier index.\n\n")

def _render_armory_subtab(app):
    sys.stdout.write(f"  {BOLD}🛡️ Team Rocket Covert Tech Armory{RESET}\n")
    sys.stdout.write(f"  Skunkworks experimental equipment gated by operative clearance.\n\n")

    user_rank = app.engine.state.get("rocket_rank", "Informant")
    rank_order = {"Informant": 1, "Operative": 2, "Special Agent": 3, "Executive": 4, "Commander": 5}
    user_lvl = rank_order.get(user_rank, 1)

    armory_items = [
        ("elixir", "Shadow Elixir", 20_000_000, "Informant", "🧪", "Sets Happiness to 100% & grants 2h token rate boost"),
        ("chip", "Overclock Chip", 35_000_000, "Operative", "💾", "Cuts all active expedition durations in half"),
        ("scanner", "Syndicate Scanner", 45_000_000, "Operative", "🔍", "Reveals hidden bonus rewards & extra expedition drops"),
        ("radar", "Rocket Decryptor", 50_000_000, "Special Agent", "📡", "+2.0% Bank CD daily interest & insider market tips"),
        ("catalyst", "Dark Gene Catalyst", 75_000_000, "Executive", "🧬", "Stored in bag: Instantly evolves eligible companion"),
        ("ball", "Rocket Master Ball", 150_000_000, "Commander", "🔮", "Guaranteed 100% capture & highest shiny probability"),
    ]

    for code, name, price, min_rank, icon, desc in armory_items:
        req_lvl = rank_order.get(min_rank, 1)
        pr_str = format_tokens(price)
        if user_lvl >= req_lvl:
            badge = f"{BOLD}{GREEN}[CLEARANCE GRANTED]{RESET}"
        else:
            badge = f"{BOLD}{RED}[LOCKED - REQ: {min_rank.upper()}]{RESET}"

        sys.stdout.write(f"  {icon} {BOLD}{name:<19}{RESET} [{BOLD}{CYAN}{pr_str}{RESET}] ('{BOLD}{code}{RESET}') {badge}\n")
        for dline in textwrap.wrap(f"➔ {desc}", width=66):
            sys.stdout.write(f"     {dline}\n")
        sys.stdout.write("\n")

    sys.stdout.write(f"  ➔ Type '{BOLD}buy <code>{RESET}' to acquire tech (e.g. 'buy elixir')\n")
    sys.stdout.write(f"  ➔ Switch view: '{BOLD}o{RESET}' for Operations | '{BOLD}i{RESET}' for Intel\n\n")

def handle_rocket_command(app, cmd: str):
    """Processes user input while inside Tab [12]."""
    cmd = cmd.strip()

    # If dormant channel, handle alliance acceptance
    if not app.engine.state.get("rocket_alliance_accepted", False):
        if cmd.lower() in ["accept", "1", "yes", "y"]:
            app.engine.state["rocket_alliance_accepted"] = True
            app.engine.save()
            app.message = "🚀 Alliance initiated! Welcome to Team Rocket Covert HQ, Operative."
        else:
            app.message = "Type 'accept' to join the Rocket Alliance, or switch tabs (1-11)."
        return

    subview = getattr(app, "rocket_subview", "ops")

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
                app.message = f"File #{idx} is encrypted. Complete Operation {idx} to unlock."
            else:
                app.message = "Invalid file number. Use 'read 1' through 'read 10'."
        else:
            app.message = "Usage: read <1-10> (e.g. 'read 1')"
    elif cmd.startswith("start "):
        parts = cmd.split()
        if len(parts) >= 2:
            ok, msg = app.engine.start_rocket_operation(parts[1])
            app.message = msg
        else:
            app.message = "Usage: start <id> (e.g. 'start 1')"
    elif cmd.startswith("claim "):
        parts = cmd.split()
        if len(parts) >= 2:
            ok, msg = app.engine.claim_rocket_operation(parts[1])
            app.message = msg
        else:
            app.message = "Usage: claim <id> (e.g. 'claim 1')"
    elif cmd in ["attack", "strike", "a"] and subview == "ops":
        ok, msg = app.engine.attack_rocket_boss(burst=False)
        app.message = msg
    elif cmd in ["burst", "overclock"] and subview == "ops":
        ok, msg = app.engine.attack_rocket_boss(burst=True)
        app.message = msg
    elif cmd.startswith("buy ") and subview == "armory":
        parts = cmd.split()
        if len(parts) >= 2:
            ok, msg = app.engine.buy_rocket_armory_item(parts[1])
            app.message = msg
        else:
            app.message = "Usage: buy <elixir|chip|scanner|radar|catalyst|ball>"
    else:
        app.message = "Rocket command options: 'o', 'i', 'a', 'start <id>', 'claim <id>', 'attack', 'burst', 'buy <code>'."

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
