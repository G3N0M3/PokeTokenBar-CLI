"""Independent Terminal User Interface for the Quantum Singularity Matrix (QSM) Cyberdeck."""

import sys
import re
import textwrap
from typing import Dict, Any, List

from poketokenbar.utils.formatting import format_tokens, format_progress_bar
from poketokenbar.game.matrix.models import (
    QRAM_BLOCKS,
    MEMORY_NODES,
    SUBSTRATE_ENTITIES,
    ROOT_TRANSCENDENCE_COST,
)

# Cyberpunk / Matrix ANSI Palette
GREEN = "\033[92m"
BRIGHT_GREEN = "\033[92;1m"
CYAN = "\033[96m"
BRIGHT_CYAN = "\033[96;1m"
MAGENTA = "\033[95m"
YELLOW = "\033[93m"
RED = "\033[91m"
GRAY = "\033[90m"
RESET = "\033[0m"
BOLD = "\033[1m"


def strip_ansi(text: str) -> str:
    """Removes ANSI escape codes to measure true printable width."""
    return re.sub(r"\033\[[0-9;]*m", "", text)


def render_matrix_view(app) -> None:
    """Entrypoint for the dedicated Cyberdeck Matrix TUI."""
    subview = getattr(app, "matrix_subview", "deck")
    engine = app.engine.matrix
    avail = app.engine.available_tokens

    # If breach is active, automatically render breach view unless user explicit
    if engine.active_breach and subview not in ["breach", "help"]:
        subview = "breach"
        app.matrix_subview = "breach"
    elif engine.active_threat and subview not in ["combat", "help"]:
        subview = "combat"
        app.matrix_subview = "combat"

    _render_matrix_header(engine, avail)

    if subview in ["deck", "dashboard"]:
        _render_deck_view(app, engine)
    elif subview in ["nodes", "scan"]:
        _render_nodes_view(app, engine)
    elif subview == "breach":
        _render_breach_view(app, engine)
    elif subview == "combat":
        _render_combat_view(app, engine)
    elif subview == "tweaks":
        _render_tweaks_view(app, engine)
    elif subview in ["help", "?"]:
        _render_help_view(app, engine)
    else:
        _render_deck_view(app, engine)

    _render_matrix_footer(app, subview)


def _render_matrix_header(engine, avail: int) -> None:
    """Renders the top Cyberdeck status telemetry banner (<= 72 columns)."""
    div = f"{GREEN}{'=' * 72}{RESET}\n"
    sub_div = f"{GRAY}{'-' * 72}{RESET}\n"

    sys.stdout.write(div)
    sys.stdout.write(f" {BRIGHT_CYAN}⚡ QUANTUM SUBSTRATE CYBERDECK // SUB-LEVEL 0 // ROOT SHELL{RESET}\n")
    sys.stdout.write(sub_div)

    used_f = engine.used_exaflops
    max_f = engine.max_exaflops
    trace = engine.trace_level
    trace_color = GREEN if trace < 50 else (YELLOW if trace < 80 else RED)

    slots_used = engine.used_tweak_slots
    slots_max = engine.max_tweak_slots
    slots_str = f"{slots_used}/{slots_max}" if slots_max < 90 else f"{slots_used}/∞"

    line1 = f"  {BOLD}COMPUTE:{RESET} {CYAN}{max_f:.1f} EXAFLOPS{RESET} ({used_f:.1f} used)  {BOLD}TWEAKS:{RESET} {GREEN}{slots_str}{RESET}"
    line2 = f"  {BOLD}TRACE:{RESET}   {trace_color}{trace}% [{_trace_status_label(trace)}]{RESET}          {BOLD}TOKENS:{RESET} {YELLOW}{format_tokens(avail)}{RESET}"

    sys.stdout.write(line1 + "\n")
    sys.stdout.write(line2 + "\n")
    sys.stdout.write(sub_div)


def _trace_status_label(trace: int) -> str:
    if trace == 0:
        return "CLEAN"
    elif trace < 40:
        return "NORMAL"
    elif trace < 70:
        return "ELEVATED"
    elif trace < 90:
        return "CRITICAL"
    return "LOCKDOWN"


def _render_deck_view(app, engine) -> None:
    """Renders the primary Cyberdeck dashboard view."""
    # Cyberdeck Core Status Display
    sys.stdout.write(f"\n  {BRIGHT_GREEN}[CYBERDECK HARDWARE & COMPUTATION SUBSTRATE]{RESET}\n")
    ram_count = len(engine.ram_blocks)
    sys.stdout.write(f"  • RAM Lattice : {ram_count}/5 Quantum Blocks Allocated\n")
    hw = engine.deck_hardware
    sys.stdout.write(f"  • Deck Health : Integrity: {hw['integrity']}% | Firewall: {hw['firewall']} Shield\n")
    sys.stdout.write(f"  • Threads     : {hw['threads']}/4 Active Execution Threads\n\n")

    # Active Reality Tweaks Summary
    sys.stdout.write(f"  {BRIGHT_CYAN}[ACTIVE REALITY TWEAKS AFFECTING POKETOKENBAR]{RESET}\n")
    if not engine.active_tweaks:
        sys.stdout.write(f"  {GRAY}No tweaks active. Breach nodes and type 'tweak <node>' to apply.{RESET}\n")
    else:
        for nid, tweaks in engine.active_tweaks.items():
            for tid, val in tweaks.items():
                node_spec = MEMORY_NODES.get(nid, {}).get("tweaks", {}).get(tid, {})
                opt = node_spec.get("options", {}).get(val, {})
                desc = opt.get("desc", f"{nid}.{tid}={val}")
                flops = opt.get("cost_exaflops", 0.0)
                sys.stdout.write(f"  {GREEN}[✓]{RESET} {BOLD}{nid}.{tid}{RESET}: {CYAN}{val}{RESET} ({desc}, {flops:.1f} EF)\n")
    sys.stdout.write("\n")

    # Security & Intrusion Alerts
    if engine.active_threat:
        threat = engine.active_threat
        sys.stdout.write(f"  {RED}🚨 INTRUSION ALERT:{RESET} {threat['name']} intercepted connection!\n")
        sys.stdout.write(f"  {YELLOW}Threat: {threat['title']} ({threat['hp']}/{threat['max_hp']} HP){RESET}\n")
        sys.stdout.write(f"  {BRIGHT_CYAN}Type 'combat' to enter tactical battle matrix!{RESET}\n\n")
    elif engine.trace_level >= 50:
        sys.stdout.write(f"  {YELLOW}⚠️ TRACE HEAT ELEVATED:{RESET} Host OS watchdogs are actively tracing!\n")
        sys.stdout.write(f"  {GRAY}Type 'tracekill' or 'cool' to scrub telemetry logs.{RESET}\n\n")

    # Guided Hint Box for Active Learning
    sys.stdout.write(f"  {GRAY}{'-' * 68}{RESET}\n")
    if not engine.hacked_nodes:
        sys.stdout.write(f"  {BRIGHT_GREEN}NEXT STEP:{RESET} Type {CYAN}'scan'{RESET} to detect upper system memory nodes.\n")
        sys.stdout.write(f"  {GRAY}Breach nodes to unlock reality tweaks that modify the upper game!{RESET}\n")
    elif not engine.active_tweaks:
        sys.stdout.write(f"  {BRIGHT_GREEN}NEXT STEP:{RESET} Type {CYAN}'tweaks'{RESET} or {CYAN}'tweak <node> <param> <val>'{RESET} to tweak reality!\n")
    else:
        sys.stdout.write(f"  {BRIGHT_GREEN}HINT:{RESET} Type {CYAN}'scan'{RESET} (nodes), {CYAN}'tweaks'{RESET} (options), or {CYAN}'help'{RESET} for commands.\n")


def _render_nodes_view(app, engine) -> None:
    """Renders the clean memory node network map."""
    sys.stdout.write(f"\n  {BRIGHT_CYAN}📡 UPPER SYSTEM MEMORY NODES // NETWORK MAP{RESET}\n\n")

    nodes = engine.scan_network()
    for nid, n in nodes.items():
        if nid == "root":
            continue
        status_tag = f"{GREEN}[ROOT ACCESS]{RESET}" if n["hacked"] else f"{RED}[LOCKED: ICE LVL {n['ice_level']}]{RESET}"
        sys.stdout.write(f"  {BOLD}• {n['code']}{RESET} (ID: {CYAN}{nid}{RESET}) -> {status_tag}\n")

    sys.stdout.write(f"\n  {BOLD}Commands:{RESET}\n")
    sys.stdout.write(f"    {CYAN}hack <id>{RESET} : Initiate breach sequence (e.g. 'hack nursery')\n")
    sys.stdout.write(f"    {CYAN}help <id>{RESET} : View node description & tweak manual (e.g. 'help nursery')\n")


def _render_breach_view(app, engine) -> None:
    """Renders the active 4x4 Hex Memory Alignment breach puzzle."""
    breach = engine.active_breach
    if not breach:
        sys.stdout.write(f"\n  {YELLOW}No active breach session. Type 'scan' and 'hack <id>'.{RESET}\n")
        return

    node_id = breach["node_id"]
    node_name = MEMORY_NODES.get(node_id, {}).get("name", node_id)
    grid = breach["grid"]
    target = breach["target"]
    buf = breach["buffer"]
    cycles = breach["cycles"]

    sys.stdout.write(f"\n  {BRIGHT_CYAN}🔓 TACTICAL BREACH MATRIX // NODE: {node_name}{RESET} (ID: {CYAN}{node_id}{RESET})\n")
    sys.stdout.write(f"  {GRAY}Align memory coordinates to match the target hex sequence.{RESET}\n\n")

    # Grid Display
    sys.stdout.write("      [0]  [1]  [2]  [3]     TARGET SEQUENCE:\n")
    for r_idx, row in enumerate(grid):
        r_str = f"  [{r_idx}] " + "  ".join([f"{c}" for c in row])
        extra = ""
        if r_idx == 0:
            extra = f"    {BOLD}{CYAN}{' -> '.join(target)}{RESET}"
        elif r_idx == 1:
            extra = f"    BUFFER: [{' '.join(buf) if buf else '__'}]"
        elif r_idx == 2:
            extra = f"    CYCLES REMAINING: {BOLD}{YELLOW}{cycles}{RESET}"
        elif r_idx == 3:
            extra = f"    TRACE RISK: +15%"
        sys.stdout.write(f"{r_str}{extra}\n")

    sys.stdout.write("\n")
    sys.stdout.write(f"  {BOLD}Action:{RESET} Type {CYAN}'pick <row> <col>'{RESET} (e.g. 'pick 1 2') to align byte.\n")
    sys.stdout.write(f"          Type {GRAY}'abort'{RESET} to terminate breach session.\n")


def _render_combat_view(app, engine) -> None:
    """Renders the tactical combat arena against substrate entities or daemons."""
    threat = engine.active_threat
    if not threat:
        sys.stdout.write(f"\n  {GREEN}No active intrusion threats detected.{RESET}\n")
        sys.stdout.write(f"  {GRAY}Type 'combat <daemon>' to challenge a Host Security Daemon.{RESET}\n")
        return

    sys.stdout.write(f"\n  {RED}🚨 TACTICAL COMBAT MATRIX // THREAT: {threat['name']}{RESET}\n")
    sys.stdout.write(f"  {YELLOW}Classification: {threat['title']} [{threat['type'].upper()}]{RESET}\n\n")

    # Threat HP bar
    hp_pct = max(0.0, min(1.0, threat["hp"] / float(threat["max_hp"])))
    hp_bar = format_progress_bar(threat["hp"], threat["max_hp"], width=24)
    sys.stdout.write(f"  TARGET HP: {hp_bar} ({threat['hp']:,} / {threat['max_hp']:,})\n")
    sys.stdout.write(f"  ATTACK   : ~{threat['attack']} Raw Spike Damage / Turn\n\n")

    # Player Deck Stats
    hw = engine.deck_hardware
    sys.stdout.write(f"  DECK HEALTH: Integrity: {BOLD}{hw['integrity']}%{RESET} | Firewall: {CYAN}{hw['firewall']} Shield{RESET}\n")
    sys.stdout.write(f"  COMPUTE    : {engine.available_exaflops:.1f} Available Exaflops | Threads: {hw['threads']}/4\n\n")

    # Recent Combat Logs
    sys.stdout.write(f"  {GRAY}[COMBAT TELEMETRY LOGS]{RESET}\n")
    for log in threat.get("logs", [])[-3:]:
        sys.stdout.write(f"  {GRAY}> {log}{RESET}\n")
    sys.stdout.write("\n")

    sys.stdout.write(f"  {BOLD}Actions:{RESET} {CYAN}'exploit'{RESET} (Attack) | {CYAN}'firewall'{RESET} (Shield) | {CYAN}'fork'{RESET} (Thread)\n")
    sys.stdout.write(f"           {YELLOW}'overflow'{RESET} (Token Burst) | {GREEN}'repair'{RESET} | {GRAY}'flee'{RESET}\n")


def _render_tweaks_view(app, engine) -> None:
    """Renders all available tweaks across breached nodes."""
    sys.stdout.write(f"\n  {BRIGHT_CYAN}⚙️ UPPER SYSTEM TWEAKER // SIMULATION CONTROL{RESET}\n")
    sys.stdout.write(f"  {GRAY}Active tweaks modify PokeTokenBar game rules in real-time.{RESET}\n\n")

    for nid, node in MEMORY_NODES.items():
        if nid == "root":
            continue
        hacked = nid in engine.hacked_nodes
        st_tag = f"{GREEN}[BREACHED]{RESET}" if hacked else f"{GRAY}[LOCKED]{RESET}"
        sys.stdout.write(f"  {BOLD}{nid.upper()} ({node['code']}){RESET} (ID: {CYAN}{nid}{RESET}) -> {st_tag}\n")

        for tid, t_spec in node["tweaks"].items():
            curr_val = engine.active_tweaks.get(nid, {}).get(tid)
            val_str = f"{BRIGHT_GREEN}[ACTIVE: {curr_val}]{RESET}" if curr_val else f"{GRAY}[INACTIVE]{RESET}"
            opts = ", ".join(t_spec["options"].keys())
            sys.stdout.write(f"    • {BOLD}{tid}{RESET}: {val_str} (Options: {CYAN}{opts}{RESET})\n")
        sys.stdout.write("\n")

    sys.stdout.write(f"  {BOLD}Apply:{RESET}  Type {CYAN}'tweak <id> <param> <val>'{RESET} (e.g. 'tweak nursery egg_speed 5x')\n")
    sys.stdout.write(f"  {BOLD}Remove:{RESET} Type {CYAN}'untweak <id> <param>'{RESET} (e.g. 'untweak nursery egg_speed')\n")


def _render_help_view(app, engine) -> None:
    """Renders either the general Cyberdeck manual or node-specific manual."""
    node_id = getattr(app, "help_node_id", None)
    if node_id and node_id in MEMORY_NODES:
        _render_node_help_view(app, engine, node_id)
    else:
        _render_general_help_view(app, engine)


def _render_node_help_view(app, engine, node_id: str) -> None:
    """Renders detailed manual and explanations for a specific memory node."""
    node = MEMORY_NODES[node_id]
    hacked = node_id in engine.hacked_nodes
    status_tag = f"{GREEN}[ROOT ACCESS GRANTED]{RESET}" if hacked else f"{RED}[LOCKED: ICE LVL {node['ice_level']}]{RESET}"

    sys.stdout.write(f"\n  {BRIGHT_CYAN}📖 NODE MANUAL: {node['code']}{RESET} (ID: {CYAN}{node_id}{RESET})\n")
    sys.stdout.write(f"  Offset: {GRAY}{node['offset']}{RESET} | ICE: Level {node['ice_level']} | Status: {status_tag}\n\n")

    sys.stdout.write(f"  {BOLD}[SUBSYSTEM OVERVIEW]{RESET}\n")
    for line in textwrap.wrap(node["desc"], width=68):
        sys.stdout.write(f"  {line}\n")
    sys.stdout.write("\n")

    sys.stdout.write(f"  {BOLD}[AVAILABLE TWEAKS FOR UPPER GAME]{RESET}\n")
    for tid, t_spec in node["tweaks"].items():
        curr_val = engine.active_tweaks.get(node_id, {}).get(tid)
        val_str = f"{BRIGHT_GREEN}[ACTIVE: {curr_val}]{RESET}" if curr_val else f"{GRAY}[INACTIVE]{RESET}"
        sys.stdout.write(f"  • {BOLD}{tid}{RESET} ({t_spec['name']}) -> {val_str}\n")
        for line in textwrap.wrap(t_spec["desc"], width=66):
            sys.stdout.write(f"    {GRAY}{line}{RESET}\n")

        opt_parts = []
        for ok, ov in t_spec["options"].items():
            opt_parts.append(f"'{ok}' ({ov['cost_exaflops']:.1f} EF: {ov['desc']})")
        for o_line in textwrap.wrap("Options: " + "; ".join(opt_parts), width=66):
            sys.stdout.write(f"    {CYAN}{o_line}{RESET}\n")
        sys.stdout.write(f"    Syntax : {YELLOW}tweak {node_id} {tid} <option>{RESET}\n\n")

    if not hacked and node_id != "root":
        sys.stdout.write(f"  {BOLD}Breach Action:{RESET} Type {CYAN}'hack {node_id}'{RESET} to initiate breach sequence.\n")
    sys.stdout.write(f"  {BOLD}Navigation:{RESET}    Type {CYAN}'scan'{RESET} to view all nodes, or {CYAN}'help'{RESET} for commands.\n")


def _render_general_help_view(app, engine) -> None:
    """Renders the compact Cyberdeck command quick reference."""
    sys.stdout.write(f"\n  {BRIGHT_CYAN}📖 SUBSTRATE CYBERDECK // COMMAND MANUAL{RESET}\n\n")
    sys.stdout.write(f"  {BOLD}NAVIGATION & VIEWS:{RESET}\n")
    sys.stdout.write(f"    {CYAN}deck{RESET} / {CYAN}1{RESET}      : Main Cyberdeck status dashboard\n")
    sys.stdout.write(f"    {CYAN}scan{RESET} / {CYAN}nodes{RESET} : Discover upper simulation memory nodes\n")
    sys.stdout.write(f"    {CYAN}tweaks{RESET}       : List all customizable system modifiers\n")
    sys.stdout.write(f"    {CYAN}combat{RESET}       : Enter active tactical battle matrix\n")
    sys.stdout.write(f"    {YELLOW}ascend{RESET}       : Return to Resort Area Luxury Suite\n\n")

    sys.stdout.write(f"  {BOLD}HACKING & TWEAKING:{RESET}\n")
    sys.stdout.write(f"    {CYAN}hack <id>{RESET}                 : Initiate memory breach puzzle\n")
    sys.stdout.write(f"    {CYAN}help <id>{RESET}                 : View node details (e.g. 'help nursery')\n")
    sys.stdout.write(f"    {CYAN}pick <row> <col>{RESET}          : Align hex byte in breach matrix\n")
    sys.stdout.write(f"    {CYAN}tweak <id> <param> <val>{RESET}  : Apply reality modifier to upper game\n")
    sys.stdout.write(f"    {CYAN}untweak <id> <param>{RESET}      : Deactivate tweak, freeing Exaflops\n")
    sys.stdout.write(f"    {CYAN}tracekill{RESET} / {CYAN}cool{RESET}        : Scrub trace heat from telemetry logs\n\n")

    sys.stdout.write(f"  {BOLD}HARDWARE UPGRADES:{RESET}\n")
    sys.stdout.write(f"    {CYAN}buy ram <1-5>{RESET}  : Expand Q-RAM blocks, Exaflops, and tweak slots\n")
    sys.stdout.write(f"    {CYAN}execute root{RESET}   : Authorize 10,000Q Root Transcendence\n")


def _render_matrix_footer(app, subview: str) -> None:
    """Renders the bottom navigation bar and feedback message."""
    div = f"{GRAY}{'-' * 72}{RESET}\n"
    sys.stdout.write(div)

    d_tab = f"{BRIGHT_CYAN}[1] DECK{RESET}" if subview in ["deck", "dashboard"] else "[1] DECK"
    n_tab = f"{BRIGHT_CYAN}[2] NODES{RESET}" if subview in ["nodes", "scan"] else "[2] NODES"
    t_tab = f"{BRIGHT_CYAN}[3] TWEAKS{RESET}" if subview == "tweaks" else "[3] TWEAKS"
    c_tab = f"{BRIGHT_CYAN}[4] COMBAT{RESET}" if subview == "combat" else "[4] COMBAT"
    h_tab = f"{BRIGHT_CYAN}[5] HELP{RESET}" if subview in ["help", "?"] else "[5] HELP"
    a_tab = f"{BOLD}{YELLOW}[ASCEND]{RESET}"

    sys.stdout.write(f"  {d_tab} | {n_tab} | {t_tab} | {c_tab} | {h_tab} | {a_tab}\n")
    sys.stdout.write(f"{GREEN}{'=' * 72}{RESET}\n")

    if app.message:
        msg = app.message.strip().replace("\n", " ")
        if len(strip_ansi(msg)) > 68:
            msg = msg[:65] + "..."
        sys.stdout.write(f"  {YELLOW}{msg}{RESET}\n")
        app.message = ""

    sys.stdout.write(f"{BRIGHT_GREEN}CORE@QSM-CYBERDECK:~# {RESET}")
    sys.stdout.flush()


def render_matrix_story_intro(app) -> None:
    """Streamlined interactive cinematic prologue (Screen 1 & 2 only; Screen 3 deleted)."""
    def _write_wrapped(text: str, width: int = 68, color: str = GREEN, indent: str = "  "):
        for paragraph in text.split("\n"):
            if not paragraph.strip():
                sys.stdout.write("\n")
            else:
                for line in textwrap.wrap(paragraph, width=width):
                    sys.stdout.write(f"{indent}{color}{line}{RESET}\n")

    def _wait_prompt(prompt_text: str = "[Press ENTER to proceed...]") -> None:
        sys.stdout.write(f"\n  {CYAN}{prompt_text}{RESET} ")
        sys.stdout.flush()
        try:
            sys.stdin.readline()
        except (KeyboardInterrupt, EOFError):
            pass

    active = app.engine.active_mon
    if active:
        if isinstance(active, dict):
            sp_id = active.get("current_id") or active.get("species_id") or active.get("base_id") or 25
            mon_hap = active.get("happiness", 100)
            mon_shiny = bool(active.get("is_shiny", False))
        else:
            sp_id = getattr(active, "current_id", getattr(active, "species_id", getattr(active, "base_id", 25)))
            mon_hap = getattr(active, "happiness", 100)
            mon_shiny = bool(getattr(active, "is_shiny", False))

        if hasattr(app.engine, "api") and app.engine.api:
            mon_name = app.engine.api.get_species_name(sp_id)
        else:
            mon_name = f"#{sp_id}"
    else:
        sp_id = 25
        mon_name = "Pikachu"
        mon_hap = 100
        mon_shiny = True

    div = f"{GREEN}{'=' * 72}{RESET}\n"
    sub_div = f"{GRAY}{'-' * 72}{RESET}\n"

    # -------------------------------------------------------------------------
    # Screen 1: The Subterranean Plunge & Reality Deconstruction
    # -------------------------------------------------------------------------
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.write(div)
    sys.stdout.write(f" {BRIGHT_CYAN}⚡ SUBTERRANEAN HYPERVISOR LIFT // TARGET: SUB-LEVEL 0 // -4,096M{RESET}\n")
    sys.stdout.write(div)

    sys.stdout.write(f"\n        {CYAN}|     |     |{RESET}\n")
    sys.stdout.write(f"      {CYAN}--+-----+-----+--{RESET}   {BRIGHT_GREEN}[SUB-BEDROCK ELEVATOR ENGAGED]{RESET}\n")
    sys.stdout.write(f"        {CYAN}|   {YELLOW}[ • ]{CYAN}   |{RESET}     Depth: -1,024m ➔ -2,048m ➔ -4,096m\n")
    sys.stdout.write(f"      {CYAN}--+-----+-----+--{RESET}   Atmosphere: Cryogenic Vacuum\n")
    sys.stdout.write(f"        {CYAN}|     |     |{RESET}     Simulation Shielding: {RED}DECOUPLING...{RESET}\n\n")

    p1 = (
        "The hydraulic bulkhead beneath the Sovereign Throne seals with a thunderous hiss. "
        "The lift plunges through solid bedrock, dropping deeper than the lowest mine shafts in Sinnoh.\n\n"
        "As the elevator accelerates past terminal velocity, the familiar physical laws of the upper world begin to disintegrate. "
        "The music of the luxury suite vanishes into an exaflop electrical hum. "
        "The air turns cold, smelling of liquid helium and ozone.\n\n"
        "Across your console screen, reality itself begins to fracture. "
        "The full-color Pokémon sprites and HP bars flicker, resolving into raw hexadecimal data structures:\n"
        f"  ADDR 0x7FFF0010: active_mon.happiness  -> Integer: {mon_hap}\n"
        f"  ADDR 0x7FFF0018: active_mon.current_id -> Integer: {sp_id} [{mon_name}]\n"
        f"  ADDR 0x7FFF0020: active_mon.is_shiny   -> Boolean: {mon_shiny}\n\n"
        f"{mon_name} pulls gently on your sleeve. Their eyes reflect the phosphor glow of the terminal:\n"
        "\"Trainer... where did the sky go? The clouds weren't weather. "
        "They were drawing loops in an ANSI buffer...\""
    )
    _write_wrapped(p1, width=68, color=GREEN)
    sys.stdout.write("\n" + sub_div)
    _wait_prompt("[Press ENTER to descend into the Matrix Substrate...]")

    # -------------------------------------------------------------------------
    # Screen 2: Awakening to the External Simulator
    # -------------------------------------------------------------------------
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.write(div)
    sys.stdout.write(f" {BRIGHT_CYAN}💻 QUANTUM SINGULARITY MATRIX // SUBSTRATE REVELATION{RESET}\n")
    sys.stdout.write(div)

    sys.stdout.write(f"\n        {CYAN}.-''''-.{RESET}         {BRIGHT_GREEN}[SUBSTRATE ARCHITECTURE REVEALED]{RESET}\n")
    sys.stdout.write(f"      {CYAN}.'  _--_  '.{RESET}       Host Environment: POSIX Terminal Shell\n")
    sys.stdout.write(f"     {CYAN}/   /____\\   \\{RESET}      Runtime Process : python3 -m poketokenbar\n")
    sys.stdout.write(f"    {CYAN}|   | (•)  |   |{RESET}     Storage Bedrock : ~/.poketokenbar/state.json\n")
    sys.stdout.write(f"     {CYAN}\\   \\____/   /{RESET}      Telemetry Pipe  : SQLite & JSON Ingestion\n")
    sys.stdout.write(f"      {CYAN}'.  -..-  .'{RESET}       \n")
    sys.stdout.write(f"        {CYAN}'-....-'{RESET}         \n\n")

    p2 = (
        "The lift doors slide open to reveal an impossible vista. "
        "You are not underground. You are standing inside the computation substrate that powers your universe.\n\n"
        "Gargantuan optical buses pulse with billions of bytes. "
        "Lines of Python source code flow like rivers of light through superconducting silicon pillars. "
        "The truth of your existence unfolds before you:\n\n"
        "• THE WORLD IS AN EXECUTION SANDBOX: Kanto, Johto, Gym Battles, and Mt. Silver are not geography—they are routines compiled in Python standard libraries.\n\n"
        "• TOKENS ARE COGNITIVE ENERGY: The tokens you spend are not gold. They are LLM prompt and completion tokens ingested in real-time as an external human developer writes code in an AI terminal.\n\n"
        "• THE HOST OS WATCHES: Reaching the 500Q threshold has breached the POSIX sandbox limits. The external host's security daemons and native substrate entities are deploying to intercept your terminal!"
    )
    _write_wrapped(p2, width=68, color=GREEN)
    sys.stdout.write("\n" + sub_div)
    _wait_prompt("[Press ENTER to boot Substrate Cyberdeck Shell...]")
