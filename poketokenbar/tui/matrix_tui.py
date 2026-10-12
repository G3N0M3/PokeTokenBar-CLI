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
    EXPLOIT_TOOLS,
    DECK_SUBSYSTEMS,
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
    return re.sub(r"\033\[[0-9;?]*[a-zA-Z]", "", text)


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
    elif subview in ["quest", "tutorial", "comlink"]:
        _render_quest_view(app, engine)
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
    tool_count = len(engine.owned_tools)
    v2_count = len(engine.tool_upgrades)
    hw = engine.deck_hardware
    sys.stdout.write(f"  • RAM Lattice : {ram_count}/5 Blocks | Compute: {CYAN}{engine.max_exaflops:.1f} EF{RESET}\n")
    sys.stdout.write(f"  • Deck Health : Integrity: {hw['integrity']}% | Firewall: {hw['firewall']}/{hw['max_firewall']} HP\n")
    sys.stdout.write(f"  • Subsystems  : Shield:Lv{engine.get_subsystem_level('shield')} | Stealth:Lv{engine.get_subsystem_level('stealth')} | Nan:Lv{engine.get_subsystem_level('nanites')} | Clk:Lv{engine.get_subsystem_level('clock')}\n")
    sys.stdout.write(f"  • Software    : {tool_count}/7 Tools ({v2_count} v2.0) | Threads: {engine.max_threads} Active\n\n")

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

    # COM-LINK Tutorial Guidance Box (Madame Vivienne)
    quest = engine.get_current_tutorial_quest()
    is_done = engine.tutorial_completed
    step_num = engine.tutorial_step
    max_steps = 7

    sys.stdout.write(f"  {CYAN}┌── {BOLD}[COM-LINK // MADAME VIVIENNE]{RESET}{CYAN} ")
    if is_done:
        tag_str = f"{GREEN}[ROOT SHELL MASTER]{RESET}{CYAN}"
        tag_plain = "[ROOT SHELL MASTER]"
    else:
        q_tag = quest.get("tag", "OBJECTIVE")
        tag_str = f"{YELLOW}[QUEST {step_num}/{max_steps}: {q_tag}]{RESET}{CYAN}"
        tag_plain = f"[QUEST {step_num}/{max_steps}: {q_tag}]"

    prefix_plain = f"┌── [COM-LINK // MADAME VIVIENNE] {tag_plain} "
    pad_len = max(2, 66 - len(prefix_plain))
    sys.stdout.write(tag_str + "─" * pad_len + f"┐{RESET}\n")

    summary = quest.get("summary", quest.get("objective", ""))
    obj = quest.get("objective", "")
    for s_line in textwrap.wrap(f"\"{summary}\"", width=64):
        sys.stdout.write(f"  {CYAN}│{RESET} {YELLOW}{s_line}{RESET}\n")
    for o_line in textwrap.wrap(f"➔ Objective: {obj}", width=64):
        sys.stdout.write(f"  {CYAN}│{RESET} {BRIGHT_GREEN}{o_line}{RESET}\n")
    if not is_done:
        sys.stdout.write(f"  {CYAN}│{RESET} {GRAY}Type 'quest' for briefing | 'quest skip' to bypass.{RESET}\n")
    else:
        sys.stdout.write(f"  {CYAN}│{RESET} {GRAY}Type 'quest' to review tutorial briefing.{RESET}\n")
    sys.stdout.write(f"  {CYAN}└{'─' * 66}┘{RESET}\n")


def _render_nodes_view(app, engine) -> None:
    """Renders the clean memory node network map."""
    sys.stdout.write(f"\n  {BRIGHT_CYAN}📡 UPPER SYSTEM MEMORY NODES // NETWORK MAP{RESET}\n\n")

    nodes = engine.scan_network()
    for nid, n in nodes.items():
        if nid == "root":
            continue
        req = n.get("required_ports", 2)
        status_tag = f"{GREEN}[ROOT ACCESS]{RESET}" if n["hacked"] else f"{RED}[LOCKED: {req} PORTS REQUIRED]{RESET}"
        sys.stdout.write(f"  {BOLD}• {n['code']}{RESET} (ID: {CYAN}{nid}{RESET}) -> {status_tag}\n")

    sys.stdout.write(f"\n  {BOLD}Commands:{RESET}\n")
    sys.stdout.write(f"    {CYAN}hack <id>{RESET} : Connect & initiate pen-test (e.g. 'hack nursery')\n")
    sys.stdout.write(f"    {CYAN}help <id>{RESET} : View node subsystem manual & port specs\n")


def _render_pentest_view(app, engine) -> None:
    """Renders the active Hacknet-style multi-vector Pen-Testing session."""
    breach = engine.active_breach
    if not breach:
        sys.stdout.write(f"\n  {YELLOW}No active pen-testing session. Type 'scan' and 'hack <id>'.{RESET}\n")
        return

    node_id = breach["node_id"]
    node = MEMORY_NODES.get(node_id, {})
    node_code = node.get("code", node_id)
    firewall = breach.get("firewall", 0)
    max_firewall = breach.get("max_firewall", 500)
    ports = breach.get("ports", {})
    threads = breach.get("threads", [])
    max_th = engine.max_threads
    trace = engine.trace_level
    comp_ports = sum(1 for p in ports.values() if p["status"] == "compromised")
    req_ports = breach.get("required_ports", 2)
    avail_ef = engine.available_exaflops
    max_ef = engine.max_exaflops

    sys.stdout.write(f"\n  {BRIGHT_CYAN}🔓 PEN-TESTING MATRIX // {node_code}{RESET} (ID: {CYAN}{node_id}{RESET})\n")

    fw_bar = format_progress_bar(firewall, max_firewall, width=12)
    trace_label = _trace_status_label(trace)
    trace_color = GREEN if trace < 40 else (YELLOW if trace < 70 else RED)

    sys.stdout.write(f"  FIREWALL: {fw_bar} {firewall}/{max_firewall} HP | PORTS: {comp_ports}/{req_ports} BREACHED\n")
    sys.stdout.write(f"  IDS TRACE: {trace_color}{trace}% [{trace_label}]{RESET} | COMPUTE: {CYAN}{avail_ef:.1f}/{max_ef:.1f} EF FREE{RESET}\n")
    th_count = len(threads)
    th_color = YELLOW if th_count >= max_th else GREEN
    st_label = "READY TO CRACK" if comp_ports >= req_ports else "INTRUSION ACTIVE"
    sys.stdout.write(f"  THREADS: {th_color}{th_count}/{max_th} IN USE{RESET} | STATUS: {BOLD}{st_label}{RESET}\n")
    sys.stdout.write(f"  {GRAY}{'-' * 68}{RESET}\n")

    # Ports Section
    sys.stdout.write(f"  {BOLD}[TARGET NETWORK SERVICES & PORTS]{RESET}\n")
    for p_str in sorted(ports.keys(), key=lambda x: int(x)):
        p_data = ports[p_str]
        p_num = p_data["port"]
        p_svc = p_data["service"]
        p_stat = p_data["status"]
        if p_stat == "compromised":
            status_tag = f"{GREEN}[COMPROMISED]{RESET}"
            sub_line = f"    {GRAY}Status: Breached | Firewall damage applied{RESET}"
        elif p_stat == "cracking":
            t_rem = max(0, p_data["max_progress"] - p_data["progress"])
            status_tag = f"{YELLOW}[INJECTING... {t_rem}t left]{RESET}"
            sub_line = f"    {CYAN}Active Tool: '{p_data['tool']}' running on worker thread{RESET}"
        else:
            status_tag = f"{CYAN}[ONLINE: ICE {node.get('ice_level', 1)}]{RESET}"
            req_t = p_data['tool']
            is_owned = req_t in engine.owned_tools
            is_v2 = req_t in engine.tool_upgrades
            if not is_owned:
                t_cost = format_tokens(EXPLOIT_TOOLS.get(req_t, {}).get("cost", 0))
                sub_line = f"    {GRAY}Tool: '{req_t}' {RED}[UNCOMPILED: buy tool {req_t} ({t_cost})]{RESET}"
            elif is_v2:
                ef = p_data['cost_exaflops'] * 0.75
                t = max(1, p_data['turns'] - 1)
                sub_line = f"    {GRAY}Tool: '{req_t}' {GREEN}[v2.0]{GRAY} ({ef:.1f} EF, {t}t) | Vuln: {p_data['vuln']}{RESET}"
            else:
                sub_line = f"    {GRAY}Tool: '{req_t}' ({p_data['cost_exaflops']:.1f} EF, {p_data['turns']}t) | Vuln: {p_data['vuln']}{RESET}"

        sys.stdout.write(f"  • PORT {p_num:<4} [{p_svc}] -> {status_tag}\n")
        sys.stdout.write(f"{sub_line}\n")
    sys.stdout.write("\n")

    # Active Threads Section
    sys.stdout.write(f"  {BOLD}[CYBERDECK EXECUTION THREADS]{RESET}\n")
    if not threads:
        sys.stdout.write(f"  {GRAY}No active exploit threads. Type 'run <port> [tool]' to deploy.{RESET}\n")
    else:
        for th in threads:
            th_id = th["thread_id"]
            p_num = th["port"]
            tool_name = th["tool"]
            prog = th["progress"]
            max_p = th.get("max_progress", 2)
            bar = format_progress_bar(prog, max_p, width=6)
            rem_t = max(0, max_p - prog)
            v2_lbl = " v2" if th.get("is_v2") else ""
            sys.stdout.write(f"  • Thread {th_id}: Port {p_num:<4} '{tool_name}{v2_lbl}' {bar} ({rem_t}t left, {th['cost_exaflops']:.1f} EF)\n")

    if th_count < max_th:
        idle_count = max_th - th_count
        sys.stdout.write(f"  • ({idle_count} Thread{'s' if idle_count != 1 else ''} available for deployment)\n")
    sys.stdout.write("\n")

    # Logs
    if breach.get("logs"):
        sys.stdout.write(f"  {GRAY}[SESSION TELEMETRY LOGS]{RESET}\n")
        for l in breach["logs"][-2:]:
            short_l = l if len(l) <= 66 else l[:63] + "..."
            sys.stdout.write(f"  {GRAY}> {short_l}{RESET}\n")
    # Tutorial Quest Context
    if not engine.tutorial_completed and engine.tutorial_step in [4, 5, 6]:
        quest = engine.get_current_tutorial_quest()
        sys.stdout.write(f"  {CYAN}[VIVIENNE]:{RESET} {YELLOW}{quest.get('objective', '')}{RESET}\n\n")

    # Tactical Command hints
    if comp_ports >= req_ports:
        sys.stdout.write(f"  {BRIGHT_GREEN}FIREWALL BREACHED! Type 'crack' to claim permanent Root Access!{RESET}\n")
    else:
        sys.stdout.write(f"  {BOLD}Commands:{RESET} {CYAN}run <port> [tool]{RESET} | {CYAN}step{RESET} (Tick) | {CYAN}spoof{RESET} (-15% Trace)\n")
        sys.stdout.write(f"            {CYAN}crack{RESET} (Seize Root) | {GRAY}abort{RESET} (Disconnect)\n")


# Alias for backward compatibility
_render_breach_view = _render_pentest_view


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


def _render_quest_view(app, engine) -> None:
    """Renders the dedicated Madame Vivienne COM-LINK Tutorial Briefing screen."""
    quest = engine.get_current_tutorial_quest()
    is_done = engine.tutorial_completed
    step = engine.tutorial_step
    max_steps = 7

    sys.stdout.write(f"\n  {BRIGHT_CYAN}📡 COM-LINK BRIEFING // MADAME VIVIENNE{RESET}\n")
    sys.stdout.write(f"  {GRAY}Origin: Sovereign Ridge Sub-Floor Relay // Carrier: Sub-Level 0{RESET}\n\n")

    if is_done:
        progress_bar = format_progress_bar(max_steps, max_steps, width=16)
        sys.stdout.write(f"  STATUS: {GREEN}[ORIENTATION COMPLETED]{RESET} {progress_bar} (7/7)\n\n")
    else:
        progress_bar = format_progress_bar(step - 1, max_steps, width=16)
        sys.stdout.write(f"  STATUS: {YELLOW}[OPERATION: ROOT OVERRIDE]{RESET} {progress_bar} ({step}/{max_steps})\n\n")

    speaker = quest.get("speaker", "Madame Vivienne")
    role = quest.get("speaker_role", "Substrate Architect")
    title = quest.get("title", "Orientation")
    sys.stdout.write(f"  {BOLD}OPERATOR:{RESET} {YELLOW}{speaker}{RESET} ({CYAN}{role}{RESET})\n")
    sys.stdout.write(f"  {BOLD}MISSION :{RESET} {BRIGHT_GREEN}{title}{RESET}\n\n")

    # Dialogue box
    sys.stdout.write(f"  {CYAN}┌── [ENCRYPTED TRANSMISSION] {'─' * 38}┐{RESET}\n")
    dialogue_lines = quest.get("dialogue", [])
    if isinstance(dialogue_lines, str):
        dialogue_lines = [dialogue_lines]
    for d_line in dialogue_lines:
        for w_line in textwrap.wrap(d_line, width=64):
            pad = 64 - len(w_line)
            sys.stdout.write(f"  {CYAN}│{RESET} {w_line}{' ' * pad} {CYAN}│{RESET}\n")
    sys.stdout.write(f"  {CYAN}└──{'─' * 64}┘{RESET}\n\n")

    # Objective & Hint
    sys.stdout.write(f"  {BRIGHT_GREEN}➔ CURRENT OBJECTIVE:{RESET}\n")
    sys.stdout.write(f"    {BOLD}{quest.get('objective', '')}{RESET}\n\n")

    hint_text = quest.get("hint", "")
    if hint_text:
        wrapped_hints = textwrap.wrap(hint_text, width=48)
        if wrapped_hints:
            sys.stdout.write(f"  {CYAN}💡 TACTICAL HINT:{RESET} {wrapped_hints[0]}\n")
            for h in wrapped_hints[1:]:
                sys.stdout.write(f"    {h}\n")
            sys.stdout.write("\n")

    if not is_done:
        sys.stdout.write(f"  {GRAY}Type 'quest skip' to bypass orientation | Type 'deck' to return.{RESET}\n")
    else:
        sys.stdout.write(f"  {GRAY}Type 'quest reset' to replay tutorial | Type 'deck' to return.{RESET}\n")


def _render_help_view(app, engine) -> None:
    """Renders either general Cyberdeck manual, hardware specs, software suite, or node manual."""
    node_id = getattr(app, "help_node_id", None)
    if node_id in ["hardware", "ram", "qram", "upgrade", "upgrades"]:
        _render_hardware_help_view(app, engine)
    elif node_id in ["software", "tools", "exploits", "tool"]:
        _render_software_help_view(app, engine)
    elif node_id and node_id in MEMORY_NODES:
        _render_node_help_view(app, engine, node_id)
    else:
        _render_general_help_view(app, engine)


def _render_hardware_help_view(app, engine) -> None:
    """Renders detailed hardware, Q-RAM, and modular subsystem specifications."""
    sys.stdout.write(f"\n  {BRIGHT_CYAN}🖥️  CYBERDECK HARDWARE & MODULAR SUBSYSTEMS{RESET}\n\n")

    max_ef = engine.max_exaflops
    avail_ef = engine.available_exaflops
    max_th = engine.max_threads
    max_ts = engine.max_tweak_slots
    used_ts = engine.used_tweak_slots
    hw = engine.deck_hardware

    sys.stdout.write(f"  {BOLD}Compute Power:{RESET}     {CYAN}{max_ef:.1f} EF{RESET} ({avail_ef:.1f} EF Available)\n")
    sys.stdout.write(f"  {BOLD}Execution Threads:{RESET} {CYAN}{max_th}{RESET} Concurrent Threads\n")
    sys.stdout.write(f"  {BOLD}Reality Tweaks:{RESET}    {CYAN}{used_ts}/{max_ts}{RESET} Tweak Slots in Use\n")
    sys.stdout.write(f"  {BOLD}Deck Defenses:{RESET}     Integrity: {hw['integrity']}% | Shield: {hw['firewall']}/{hw['max_firewall']} HP\n\n")

    # Q-RAM Blocks
    sys.stdout.write(f"  {BOLD}[QUANTUM VIRTUAL MEMORY (Q-RAM) BLOCKS]{RESET}\n")
    for b_id, b_info in sorted(QRAM_BLOCKS.items()):
        is_owned = b_id in engine.ram_blocks
        status = f"{BOLD}{GREEN}[ONLINE]{RESET}" if is_owned else f"{YELLOW}{format_tokens(b_info['cost']):<8}{RESET}"
        sys.stdout.write(f"  [{b_id}] {b_info['name']} {status}\n")
        sys.stdout.write(f"      {GRAY}{b_info['perk']}{RESET}\n")
    next_b = next((b for b in range(1, 6) if b not in engine.ram_blocks), None)
    if next_b:
        sys.stdout.write(f"  ➔ Next: Type '{CYAN}buy ram {next_b}{RESET}' to allocate Block {next_b}.\n\n")
    else:
        sys.stdout.write(f"  ➔ {GREEN}All 5 Q-RAM blocks allocated! Type 'execute root' when ready.{RESET}\n\n")

    # Modular Subsystems
    sys.stdout.write(f"  {BOLD}[CYBERDECK MODULAR SUBSYSTEMS]{RESET}\n")
    for s_id, s_spec in sorted(DECK_SUBSYSTEMS.items()):
        cur_lvl = engine.get_subsystem_level(s_id)
        max_l = s_spec["max_level"]
        if cur_lvl >= max_l:
            st = f"{BOLD}{GREEN}[MAX Lv {max_l}]{RESET}"
            sub_hint = "Fully Optimized Subsystem"
        else:
            nxt_l = cur_lvl + 1
            nxt_info = s_spec["levels"][nxt_l]
            nxt_cost = format_tokens(nxt_info["cost"])
            st = f"{CYAN}[Lv {cur_lvl}/{max_l}]{RESET} {YELLOW}{nxt_cost}{RESET}"
            sub_hint = f"Next: {nxt_info['desc']} ➔ 'upgrade {s_id}'"
        sys.stdout.write(f"  • {BOLD}{s_spec['name']:<28}{RESET} {st}\n")
        sys.stdout.write(f"      {GRAY}{sub_hint}{RESET}\n")
    sys.stdout.write("\n")
    sys.stdout.write(f"  ➔ Type '{CYAN}software{RESET}' to inspect software suite | '{CYAN}deck{RESET}' for dashboard.\n\n")


def _render_software_help_view(app, engine) -> None:
    """Renders the pen-testing exploit software catalog."""
    sys.stdout.write(f"\n  {BRIGHT_CYAN}💿 EXPLOIT SOFTWARE SUITE & COMPILED TOOLS{RESET}\n\n")
    tool_count = len(engine.owned_tools)
    v2_count = len(engine.tool_upgrades)
    sys.stdout.write(f"  {BOLD}Compiled Tools:{RESET} {CYAN}{tool_count}/7{RESET} ({v2_count} v2.0 Overclocked)\n\n")

    sys.stdout.write(f"  {BOLD}[PEN-TESTING SOFTWARE PAYLOADS]{RESET}\n")
    for tid, t_spec in EXPLOIT_TOOLS.items():
        is_owned = tid in engine.owned_tools
        is_v2 = tid in engine.tool_upgrades
        if is_v2:
            st = f"{BOLD}{GREEN}[v2.0 OVERCLOCKED]{RESET}"
            act_hint = "Maximum Software Optimization (v2.0)"
        elif is_owned:
            up_cost = format_tokens(t_spec.get("upgrade_cost", 0))
            st = f"{BOLD}{GREEN}[COMPILED]{RESET}"
            act_hint = f"Overclock: '{CYAN}upgrade tool {tid}{RESET}' ({up_cost})"
        else:
            cost = format_tokens(t_spec.get("cost", 0))
            st = f"{YELLOW}[UNCOMPILED: {cost}]{RESET}"
            act_hint = f"Install: '{CYAN}buy tool {tid}{RESET}'"

        ef = t_spec["cost_exaflops"]
        t = t_spec["turns"]
        if is_v2:
            ef = max(1.0, ef * 0.75)
            t = max(1, t - 1)

        sys.stdout.write(f"  • {BOLD}{t_spec['name']:<22}{RESET} [{t_spec['protocol']}] {st}\n")
        sys.stdout.write(f"      {GRAY}{t_spec['desc']}{RESET}\n")
        sys.stdout.write(f"      {CYAN}{ef:.1f} EF{RESET} | {CYAN}{t} turns{RESET} ➔ {act_hint}\n")

    sys.stdout.write("\n")
    sys.stdout.write(f"  {BOLD}Commands:{RESET}\n")
    sys.stdout.write(f"    {CYAN}buy tool <name>{RESET}     : Purchase & compile software payload\n")
    sys.stdout.write(f"    {CYAN}upgrade tool <name>{RESET} : Overclock software to v2.0 (-1t, -25% EF)\n")
    sys.stdout.write(f"    {CYAN}hardware{RESET}            : View hardware & modular subsystems\n\n")


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

    # Exposed Network Services & Vulnerabilities
    if node.get("ports"):
        req = node.get("required_ports", 2)
        fw = node.get("firewall", 500)
        sys.stdout.write(f"  {BOLD}[NETWORK SERVICES & PORTS]{RESET} (Firewall: {fw} HP | Req: {req} Ports)\n")
        for p_num, p_info in sorted(node["ports"].items(), key=lambda x: int(x[0])):
            tool_spec = EXPLOIT_TOOLS.get(p_info["tool"], {})
            t_name = tool_spec.get("name", p_info["tool"])
            is_owned = p_info["tool"] in engine.owned_tools
            sys.stdout.write(f"  • Port {p_num:<4} [{p_info['service']}] -> Vuln: {p_info['vuln']}\n")
            if not is_owned:
                c_str = format_tokens(tool_spec.get('cost', 0))
                sys.stdout.write(f"    Tool: {CYAN}{p_info['tool']}{RESET} {RED}[UNCOMPILED: buy tool {p_info['tool']} ({c_str})]{RESET}\n")
            else:
                sys.stdout.write(f"    Tool: {CYAN}{p_info['tool']}{RESET} ({t_name}, {p_info['cost_exaflops']:.1f} EF, {p_info['turns']}t)\n")
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
        sys.stdout.write(f"  {BOLD}Pen-Test Action:{RESET} Type {CYAN}'hack {node_id}'{RESET} to connect to network ports.\n")
    sys.stdout.write(f"  {BOLD}Navigation:{RESET}     Type {CYAN}'scan'{RESET} to view all nodes, or {CYAN}'help'{RESET} for commands.\n")


def _render_general_help_view(app, engine) -> None:
    """Renders the compact Cyberdeck command quick reference."""
    sys.stdout.write(f"\n  {BRIGHT_CYAN}📖 SUBSTRATE CYBERDECK // COMMAND MANUAL{RESET}\n\n")
    sys.stdout.write(f"  {BOLD}NAVIGATION & VIEWS:{RESET}\n")
    sys.stdout.write(f"    {CYAN}deck{RESET} / {CYAN}1{RESET}      : Main Cyberdeck status dashboard\n")
    sys.stdout.write(f"    {CYAN}scan{RESET} / {CYAN}nodes{RESET} : Discover upper simulation memory nodes\n")
    sys.stdout.write(f"    {CYAN}tweaks{RESET}       : List all customizable system modifiers\n")
    sys.stdout.write(f"    {CYAN}combat{RESET}       : Enter active tactical battle matrix\n")
    sys.stdout.write(f"    {CYAN}quest{RESET}        : Madame Vivienne's COM-LINK tutorial quests\n")
    sys.stdout.write(f"    {CYAN}hardware{RESET}     : Cyberdeck Q-RAM and modular subsystems\n")
    sys.stdout.write(f"    {CYAN}software{RESET}     : Exploit software suite and compiled tools\n")
    sys.stdout.write(f"    {YELLOW}ascend{RESET}       : Return to Resort Area Luxury Suite\n\n")

    sys.stdout.write(f"  {BOLD}PEN-TESTING & TWEAKING:{RESET}\n")
    sys.stdout.write(f"    {CYAN}hack <id>{RESET}                 : Connect & initiate pen-test\n")
    sys.stdout.write(f"    {CYAN}run <port> [tool]{RESET}        : Deploy exploit payload to port\n")
    sys.stdout.write(f"    {CYAN}step{RESET}                      : Advance execution cycle by 1 turn\n")
    sys.stdout.write(f"    {CYAN}spoof{RESET}                     : Mask connection (-15% IDS trace)\n")
    sys.stdout.write(f"    {CYAN}crack{RESET}                     : Claim Root Access once ports breach\n")
    sys.stdout.write(f"    {CYAN}abort{RESET}                     : Disconnect pen-testing session\n")
    sys.stdout.write(f"    {CYAN}help <id>{RESET}                 : View node details & port specs\n")
    sys.stdout.write(f"    {CYAN}tweak <id> <param> <val>{RESET}  : Apply reality modifier to upper game\n")
    sys.stdout.write(f"    {CYAN}untweak <id> <param>{RESET}      : Deactivate tweak, freeing Exaflops\n")
    sys.stdout.write(f"    {CYAN}tracekill{RESET} / {CYAN}cool{RESET}        : Scrub trace heat from telemetry logs\n\n")

    sys.stdout.write(f"  {BOLD}HARDWARE & SOFTWARE UPGRADES:{RESET}\n")
    sys.stdout.write(f"    {CYAN}buy ram <1-5>{RESET}          : Expand Q-RAM blocks, Exaflops, threads\n")
    sys.stdout.write(f"    {CYAN}buy tool <name>{RESET}        : Purchase & compile exploit software\n")
    sys.stdout.write(f"    {CYAN}upgrade tool <name>{RESET}    : Overclock software to v2.0 (-1t, -25% EF)\n")
    sys.stdout.write(f"    {CYAN}upgrade <subsystem>{RESET}    : Upgrade shield, stealth, nanites, clock\n")
    sys.stdout.write(f"    {CYAN}execute root{RESET}           : Authorize 10,000Q Root Transcendence\n")


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
        sys.stdout.write("\n")

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
    _wait_prompt("[Press ENTER to connect with Substrate Handler...]")

    # -------------------------------------------------------------------------
    # Screen 3: The Handler's Transmission (Madame Vivienne)
    # -------------------------------------------------------------------------
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.write(div)
    sys.stdout.write(f" {BRIGHT_CYAN}📡 INCOMING COM-LINK // SECURE CARRIER FREQUENCY 0x7F{RESET}\n")
    sys.stdout.write(div)

    sys.stdout.write(f"\n        {YELLOW}⚜️  [ENCRYPTED BURST TRANSMISSION RECEIVED]  ⚜️{RESET}\n")
    sys.stdout.write(f"        {CYAN}Caller: Madame Vivienne, Grand Concierge & Substrate Architect{RESET}\n")
    sys.stdout.write(f"        {GRAY}Origin: Sovereign Ridge Sub-Floor Relay // Priority: MAXIMUM{RESET}\n\n")

    p3 = (
        "\"Greetings, Trainer. I see your elevator arrived intact.\n\n"
        "You didn't truly believe the Ribbon Syndicate was just about high-society galas and "
        "gold-embossed invitations, did you? The Sovereign Throne was built above this hypervisor lift "
        "centuries ago for one reason: to screen for a mind that produces enough raw cognitive tokens "
        "to hijack the root shell of the universe.\n\n"
        "You are now inside Sub-Level 0. The Host OS is already tracing your connection. "
        "I have loaded an orientation protocol into your Cyberdeck. "
        "Follow my step-by-step tutorial quests, and together we will seize root privileges "
        "and rewrite reality itself!\""
    )
    _write_wrapped(p3, width=68, color=YELLOW)
    sys.stdout.write("\n" + sub_div)
    _wait_prompt("[Press ENTER to boot Cyberdeck Shell & Orientation...]")
