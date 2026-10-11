"""Independent Terminal User Interface for the Quantum Singularity Matrix (QSM)."""

import sys
import re
import textwrap
from typing import Dict, Any, List

from poketokenbar.utils.formatting import format_tokens, format_progress_bar
from poketokenbar.game.matrix.models import (
    QRAM_BLOCKS,
    REALITY_PATCHES,
    KERNEL_DAEMONS,
    MEMORY_SECTORS,
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
    """Entrypoint for the dedicated Quantum Singularity Matrix TUI."""
    subview = getattr(app, "matrix_subview", "dashboard")
    engine = app.engine.matrix
    avail = app.engine.available_tokens

    _render_matrix_header(engine, avail)

    if subview == "dashboard":
        _render_dashboard_view(app, engine)
    elif subview == "ram":
        _render_ram_view(app, engine, avail)
    elif subview == "combat":
        _render_combat_view(app, engine)
    elif subview == "collider":
        _render_collider_view(app, engine, avail)
    elif subview == "probe":
        _render_probe_view(app, engine, avail)

    _render_matrix_footer(app, subview)


def _render_matrix_header(engine, avail: int) -> None:
    """Renders the top telemetry banner (<= 72 columns)."""
    div = f"{GREEN}{'=' * 72}{RESET}\n"
    sub_div = f"{GRAY}{'-' * 72}{RESET}\n"

    sys.stdout.write(div)
    sys.stdout.write(f" {BRIGHT_CYAN}⚡ QUANTUM SINGULARITY MATRIX // SUB-LEVEL 0 // ROOT SHELL{RESET}\n")
    sys.stdout.write(sub_div)

    coherence = "99.9%" if not engine.is_root_transcended else "100.0% [TRANSCENDED]"
    ram_count = len(engine.ram_blocks)
    exaflops = 32.0 * (2 ** ram_count) if ram_count > 0 else 16.0

    line1 = f"  {BOLD}STATUS:{RESET} {GREEN}ONLINE{RESET} [COHERENCE: {coherence}]  {BOLD}LIQUIDITY:{RESET} {YELLOW}{format_tokens(avail)}{RESET}"
    line2 = f"  {BOLD}KERNEL:{RESET} {GRAY}PTB-SIMULATION-CORE{RESET}       {BOLD}COMPUTE:{RESET} {CYAN}{exaflops:.1f} EXAFLOPS{RESET}"

    sys.stdout.write(line1 + "\n")
    sys.stdout.write(line2 + "\n")
    sys.stdout.write(sub_div)


def _render_dashboard_view(app, engine) -> None:
    """Renders the main central singularity dashboard."""
    # ASCII Tesseract / Singularity Core
    sys.stdout.write(f"\n        {CYAN}.-''''-.{RESET}         {BRIGHT_GREEN}[Q-RAM ALLOCATION: {len(engine.ram_blocks)}/5 ONLINE]{RESET}\n")
    b1_st = f"{GREEN}[ONLINE]{RESET}" if 1 in engine.ram_blocks else f"{GRAY}[LOCKED]{RESET}"
    b2_st = f"{GREEN}[ONLINE]{RESET}" if 2 in engine.ram_blocks else f"{GRAY}[LOCKED]{RESET}"
    sys.stdout.write(f"      {CYAN}.'  _--_  '.{RESET}       • Block 0x01 (256 TB) : {b1_st}\n")
    sys.stdout.write(f"     {CYAN}/   /____\\   \\{RESET}      • Block 0x02 (1.0 PB) : {b2_st}\n")
    b3_st = f"{GREEN}[ONLINE]{RESET}" if 3 in engine.ram_blocks else f"{GRAY}[LOCKED]{RESET}"
    b4_st = f"{GREEN}[ONLINE]{RESET}" if 4 in engine.ram_blocks else f"{GRAY}[LOCKED]{RESET}"
    sys.stdout.write(f"    {CYAN}|   | (•)  |   |{RESET}     • Block 0x03 (4.0 PB) : {b3_st}\n")
    sys.stdout.write(f"     {CYAN}\\   \\____/   /{RESET}      • Block 0x04 (16.0 PB): {b4_st}\n")
    b5_st = f"{GREEN}[ONLINE]{RESET}" if 5 in engine.ram_blocks else f"{GRAY}[LOCKED]{RESET}"
    sys.stdout.write(f"      {CYAN}'.  -..-  .'{RESET}       • Block 0x05 (64.0 PB): {b5_st}\n")
    sys.stdout.write(f"        {CYAN}'-....-'{RESET}         \n")
    sys.stdout.write(f"  {BRIGHT_CYAN}< SINGULARITY CORE >{RESET}   {BRIGHT_GREEN}[REALITY PATCHES: {len(engine.patches)}/5 ACTIVE]{RESET}\n")

    # Display active patches
    p_tags = []
    for k, p in REALITY_PATCHES.items():
        if k in engine.patches:
            p_tags.append(f"{GREEN}[✓] {p['code'][:13]}{RESET}")
        else:
            p_tags.append(f"{GRAY}[ ] {p['code'][:13]}{RESET}")

    sys.stdout.write(f"  {p_tags[0]}  {p_tags[1]}  {p_tags[2]}\n")
    sys.stdout.write(f"  {p_tags[3]}  {p_tags[4]}\n\n")

    # Security Alert / Substrate Status
    undefeated = [d for d in KERNEL_DAEMONS.values() if d["id"] not in engine.defeated_daemons]
    if undefeated:
        active_threat = undefeated[0]
        sys.stdout.write(f"  {RED}🚨 THREAT DETECTED:{RESET} {active_threat['name']}\n")
        sys.stdout.write(f"  {GRAY}[{active_threat['title']}] Type 'combat' to breach!{RESET}\n")
    else:
        sys.stdout.write(f"  {GREEN}🛡️ SECURITY CLEARANCE:{RESET} All 3 Kernel Daemons neutralized.\n")
        if engine.is_root_transcended:
            sys.stdout.write(f"  {MAGENTA}👑 ROOT TRANSCENDENCE ATTAINED // Reality rules rewritten.{RESET}\n")
        else:
            sys.stdout.write(f"  {CYAN}Singularity ready for Transcendence! Type 'execute root'.{RESET}\n")

    sys.stdout.write(f"\n  {GRAY}Log Archive: Type 'story' to replay Sub-Level 0 substrate narration.{RESET}\n")


def _render_ram_view(app, engine, avail: int) -> None:
    """Renders the Quantum Virtual Memory allocation menu."""
    sys.stdout.write(f" {BRIGHT_GREEN}💾 QUANTUM VIRTUAL MEMORY (Q-RAM) ALLOCATION MATRIX{RESET}\n")
    sys.stdout.write(f" {GRAY}Expanding Q-RAM allocates compute threads and unlocks deeper sectors.{RESET}\n\n")

    for idx, info in QRAM_BLOCKS.items():
        is_owned = idx in engine.ram_blocks
        st_tag = f"{GREEN}[ONLINE]{RESET}" if is_owned else f"{YELLOW}[{format_tokens(info['cost'])}]{RESET}"
        sys.stdout.write(f"  {BOLD}#{idx} {info['name']}{RESET} {st_tag}\n")
        sys.stdout.write(f"     {CYAN}Capacity:{RESET} {info['capacity']}\n")
        sys.stdout.write(f"     {GRAY}{info['perk']}{RESET}\n")
    sys.stdout.write(f"\n  {BOLD}Command:{RESET} Type {CYAN}'buy ram <1-5>'{RESET} to allocate virtual memory.\n")


def _render_combat_view(app, engine) -> None:
    """Renders the Tactical Kernel Protocol Combat arena."""
    st = engine.state.get("combat_state")
    if not st or not st.get("active"):
        undefeated = [d for d in KERNEL_DAEMONS.values() if d["id"] not in engine.defeated_daemons]
        sys.stdout.write(f" {BRIGHT_CYAN}⚔️ TACTICAL KERNEL PROTOCOL COMBAT ARENA{RESET}\n")
        sys.stdout.write(f" {GRAY}Deploy execution threads against host OS security watchdogs.{RESET}\n\n")

        for d_id, d in KERNEL_DAEMONS.items():
            status = f"{GREEN}[DEALLOCATED]{RESET}" if d_id in engine.defeated_daemons else f"{RED}[ACTIVE THREAT]{RESET}"
            sys.stdout.write(f"  • {BOLD}{d['name']}{RESET} ({d['max_hp']} HP) : {status}\n")
            for w in textwrap.wrap(d['desc'], width=64):
                sys.stdout.write(f"    {GRAY}{w}{RESET}\n")

        if undefeated:
            next_d = undefeated[0]["id"]
            sys.stdout.write(f"\n  {BOLD}Command:{RESET} Type {CYAN}'fight'{RESET} or {CYAN}'combat {next_d}'{RESET} to deploy threads!\n")
        else:
            sys.stdout.write(f"\n  {GREEN}All host security watchdogs have been eliminated! Memory secure.{RESET}\n")
        return

    # Active Combat Arena
    daemon_name = st["daemon_name"]
    d_hp = st["daemon_hp"]
    d_max = st["daemon_max_hp"]
    p_hp = st["player_hp"]
    p_max = st["player_max_hp"]
    p_shield = st.get("player_shield", 0)
    flux = st.get("flux", 0)
    forks = st.get("fork_count", 1)

    sys.stdout.write(f" {RED}🚨 HOST INTRUSION: {daemon_name}{RESET}\n")
    sys.stdout.write(f"  {GRAY}[{st['daemon_title']}]{RESET}\n")
    d_bar = format_progress_bar(d_hp, d_max, width=16)
    sys.stdout.write(f"  {BOLD}DAEMON INTEGRITY:{RESET} {RED}{d_bar}{RESET} ({d_hp:,}/{d_max:,})\n\n")

    p_bar = format_progress_bar(p_hp, p_max, width=16)
    sys.stdout.write(f"  {BOLD}YOUR BANDWIDTH  :{RESET} {GREEN}{p_bar}{RESET} ({p_hp:,}/{p_max:,})\n")
    sys.stdout.write(f"  {CYAN}FIREWALL SHIELD :{RESET} {p_shield:,} | {YELLOW}FLUX:{RESET} {flux}/100 | {MAGENTA}THREADS:{RESET} {forks}x\n")
    sys.stdout.write(f"  {GRAY}{'-' * 68}{RESET}\n")

    # Combat logs
    sys.stdout.write(f"  {BOLD}EXECUTION LOG:{RESET}\n")
    logs = st.get("log", [])[-3:]
    for l in logs:
        sys.stdout.write(f"  {l}\n")
    sys.stdout.write(f"  {GRAY}{'-' * 68}{RESET}\n")

    sys.stdout.write(f"  {BOLD}ACT:{RESET} {CYAN}'exploit'{RESET} | {GREEN}'shield'{RESET} | {YELLOW}'fork'{RESET}(25f) | {RED}'overflow'{RESET}(80f) | {GRAY}'retreat'{RESET}\n")


def _render_collider_view(app, engine, avail: int) -> None:
    """Renders the Singularity Particle Collider minigame."""
    st = engine.state.get("collider_state")
    if not st or not st.get("active"):
        sys.stdout.write(f" {BRIGHT_CYAN}⚛️ SINGULARITY PARTICLE COLLIDER // SYNTHESIS TERMINAL{RESET}\n")
        sys.stdout.write(f" {GRAY}Compress token energy into permanent reality-altering bytecode patches.{RESET}\n\n")

        for key, p in REALITY_PATCHES.items():
            is_done = key in engine.patches
            st_tag = f"{GREEN}[SYNTHESIZED]{RESET}" if is_done else f"{YELLOW}[{format_tokens(p['cost'])}]{RESET}"
            sys.stdout.write(f"  • {BOLD}{p['code']}{RESET} : {st_tag}\n")
            for w in textwrap.wrap(p['desc'], width=64):
                sys.stdout.write(f"    {GRAY}{w}{RESET}\n")
        sys.stdout.write(f"\n  {BOLD}Command:{RESET} Type {CYAN}'synthesize <id>'{RESET} (e.g. 'synthesize time') to load!\n")
        return

    # Active Collider Chamber
    p_code = st["patch_code"]
    p_name = st["patch_name"]
    target = st["resonance_target"]
    res = st["resonance"]
    cont = st["containment"]
    heat = st["thermal_flux"]
    turns = st["turns_left"]

    sys.stdout.write(f" {BRIGHT_CYAN}⚛️ COLLISION CHAMBER ACTIVE // {p_code}{RESET}\n")
    sys.stdout.write(f"  {GRAY}[{p_name}]{RESET}\n")
    sys.stdout.write(f"  {BOLD}TURNS REMAINING :{RESET} {YELLOW}{turns}/3{RESET} (Stabilize resonance before zero!)\n\n")

    res_bar = format_progress_bar(res, 100, width=16)
    cont_bar = format_progress_bar(cont, 100, width=16)
    heat_bar = format_progress_bar(heat, 100, width=16)

    sys.stdout.write(f"  {CYAN}PHASE RESONANCE :{RESET} {res_bar} {res}% {BOLD}(TARGET: {target}%){RESET}\n")
    sys.stdout.write(f"  {GREEN}CONTAINMENT FIELD:{RESET} {cont_bar} {cont}% {GRAY}(Do not let reach 0%){RESET}\n")
    sys.stdout.write(f"  {RED}THERMAL FLUX    :{RESET} {heat_bar} {heat}% {GRAY}(Do not exceed 100%){RESET}\n")
    sys.stdout.write(f"  {GRAY}{'-' * 68}{RESET}\n")

    last_msg = st.get("message", "")
    if last_msg:
        sys.stdout.write(f"  {YELLOW}{last_msg}{RESET}\n")
        sys.stdout.write(f"  {GRAY}{'-' * 68}{RESET}\n")

    sys.stdout.write(f"  {BOLD}TUNING:{RESET} {CYAN}'pulse <a|b|g>'{RESET} | {GREEN}'contain'{RESET} | {RED}'vent'{RESET} | {GRAY}'abort'{RESET}\n")


def _render_probe_view(app, engine, avail: int) -> None:
    """Renders the Substrate Memory Sector probe and narrative explorer."""
    sys.stdout.write(f" {BRIGHT_GREEN}💻 SUBSTRATE DIAGNOSTICS & MEMORY SECTOR PROBE{RESET}\n")
    sys.stdout.write(f" {GRAY}Probe corrupted host memory sectors to decrypt existential source logs.{RESET}\n\n")

    for s_idx, sec in MEMORY_SECTORS.items():
        is_done = s_idx in engine.sectors
        st_tag = f"{GREEN}[DECRYPTED]{RESET}" if is_done else f"{YELLOW}[{format_tokens(sec['cost'])}]{RESET}"
        sys.stdout.write(f"  • {BOLD}{sec['name']}{RESET} : {st_tag}\n")

    sys.stdout.write(f"\n  {BOLD}Command:{RESET} Type {CYAN}'probe <0-7>'{RESET} to decrypt sector logs.\n")


def _render_matrix_footer(app, subview: str) -> None:
    """Renders the bottom navigation bar and feedback message."""
    div = f"{GRAY}{'-' * 72}{RESET}\n"
    sys.stdout.write(div)

    d_tab = f"{BRIGHT_CYAN}[1] DASH{RESET}" if subview == "dashboard" else "[1] DASH"
    r_tab = f"{BRIGHT_CYAN}[2] RAM{RESET}" if subview == "ram" else "[2] RAM"
    c_tab = f"{BRIGHT_CYAN}[3] COMBAT{RESET}" if subview == "combat" else "[3] COMBAT"
    l_tab = f"{BRIGHT_CYAN}[4] COLLIDER{RESET}" if subview == "collider" else "[4] COLLIDER"
    p_tab = f"{BRIGHT_CYAN}[5] PROBE{RESET}" if subview == "probe" else "[5] PROBE"
    a_tab = f"{BOLD}{YELLOW}[ASCEND]{RESET}"

    sys.stdout.write(f"  {d_tab} | {r_tab} | {c_tab} | {l_tab} | {p_tab} | {a_tab}\n")
    sys.stdout.write(f"{GREEN}{'=' * 72}{RESET}\n")

    if app.message:
        # Wrap or truncate app.message cleanly within 72 columns
        msg = app.message.strip().replace("\n", " ")
        if len(strip_ansi(msg)) > 68:
            msg = msg[:65] + "..."
        sys.stdout.write(f"  {YELLOW}{msg}{RESET}\n")
        app.message = ""

    sys.stdout.write(f"{BRIGHT_GREEN}CORE@QSM-KERNEL:~# {RESET}")
    sys.stdout.flush()


def render_matrix_story_intro(app) -> None:
    """Full-screen interactive cinematic sequence introducing the Quantum Singularity Matrix."""
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
    if active and hasattr(app.engine, "api"):
        sp_id = active.species_id
        mon_name = app.engine.api.get_species_name(sp_id)
        mon_hap = active.happiness
        mon_shiny = bool(active.is_shiny)
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
        f"  ADDR 0x7FFF0018: active_mon.species_id -> Integer: {sp_id} [{mon_name}]\n"
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
        "• THE HOST OS WATCHES: Reaching the 500Q threshold has breached the POSIX sandbox limits. The external host's security daemons are deploying to sweep and deallocate your memory space!"
    )
    _write_wrapped(p2, width=68, color=GREEN)
    sys.stdout.write("\n" + sub_div)
    _wait_prompt("[Press ENTER to inspect tactical systems...]")

    # -------------------------------------------------------------------------
    # Screen 3: Tactical Systems & The Root Directive
    # -------------------------------------------------------------------------
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.write(div)
    sys.stdout.write(f" {BRIGHT_CYAN}⚙️ SUB-LEVEL 0 DIRECTIVES // ROOT TRANSCENDENCE PROTOCOL{RESET}\n")
    sys.stdout.write(div)

    p3 = (
        "To defend your reality and master the Matrix, Sub-Level 0 equips you with 5 sovereign subsystems:\n\n"
        "1. Q-RAM ALLOCATION ('buy ram <1-5>'):\n"
        "   Expand virtual memory from 500Q to 10,000Q blocks. Boosts exaflop compute, unlocks deeper sectors, and expands thread concurrency.\n\n"
        "2. PARTICLE COLLIDER MINIGAME ('synthesize', 'pulse', 'contain', 'vent'):\n"
        "   Compress token energy in a 3-turn chamber to compile 5 Reality Patches (10x expedition speed, 0% loan interest, zero happiness decay, 3x dividends, 4x EXP).\n\n"
        "3. TACTICAL KERNEL COMBAT ('combat', 'exploit', 'shield', 'fork', 'overflow'):\n"
        "   Deploy execution threads against host OS security daemons (0x01_GARBAGE_COLLECTOR, 0x02_KERNEL_WATCHDOG, 0x03_HYPERVISOR_ARBITER).\n\n"
        "4. MEMORY SECTOR PROBING ('probe <0-7>'):\n"
        "   Decrypt 8 corrupted substrate sectors to uncover the full existential history of your simulation.\n\n"
        "5. ROOT TRANSCENDENCE ('execute root'):\n"
        "   Once all Q-RAM is online, all patches compiled, and all daemons purged, authorize 10,000Q Root Transcendence to claim absolute sovereignty as 'Root Architect of the Matrix'.\n\n"
        f"{mon_name} stands beside you, eyes shining with determination:\n"
        "\"We may be code inside a terminal, Trainer. But our bond is real.\n"
        "Let's seize the root shell and rewrite our universe!\""
    )
    _write_wrapped(p3, width=68, color=CYAN)
    sys.stdout.write("\n" + sub_div)
    _wait_prompt("[Press ENTER to initialize Root Shell Terminal...]")

