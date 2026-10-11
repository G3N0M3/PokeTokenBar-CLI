"""Resort Area Executive Luxury Suite TUI presentation and cinematic invitation."""

import sys
import re
import textwrap
from typing import Any
from poketokenbar.utils.formatting import format_tokens
from poketokenbar.game.models import (
    LUXURY_WEALTH_THRESHOLD,
    LUXURY_VIP_FEE,
    LUXURY_DEED_COST,
    LUXURY_FACILITIES,
    LUXURY_DECOR
)

HEADER = "\033[95m\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[mK]')


def strip_ansi(s: str) -> str:
    return ANSI_REGEX.sub('', s)


def print_bounded(s: str, max_width: int = 72):
    """Writes a line to stdout guaranteeing visible width <= max_width."""
    if len(strip_ansi(s)) <= max_width:
        sys.stdout.write(s + "\n")
        return
    out = []
    vis_count = 0
    in_ansi = False
    for char in s:
        if char == '\x1b':
            in_ansi = True
            out.append(char)
        elif in_ansi:
            out.append(char)
            if char in ('m', 'K'):
                in_ansi = False
        else:
            if vis_count < max_width - 1:
                out.append(char)
                vis_count += 1
            elif vis_count == max_width - 1:
                out.append('…')
                vis_count += 1
            else:
                break
    out.append(RESET)
    sys.stdout.write("".join(out) + "\n")


def _read_input_safe() -> str:
    try:
        if hasattr(sys.stdin, "readline"):
            return sys.stdin.readline().strip()
    except (EOFError, KeyboardInterrupt):
        return ""
    return ""


def render_luxury_invitation(app: Any):
    """Full-screen interactive cinematic luxury invitation for the Luxury Suite."""
    def _write_wrapped_lines(lines, width=68, color=YELLOW):
        for line in lines:
            if not line:
                sys.stdout.write("\n")
            else:
                for wline in textwrap.wrap(line, width=width):
                    print_bounded(f"  {color}{wline}{RESET}")

    # Screen 1: High-Society Gold Foil Dispatch
    sys.stdout.write("\033[H\033[2J")
    print_bounded(f"\n{BOLD}{YELLOW}{'='*72}{RESET}")
    print_bounded(f"  {BOLD}{YELLOW}⚜️  DIPLOMATIC DISPATCH — THE RIBBON SYNDICATE OF SINNOH  ⚜️{RESET}")
    print_bounded(f"{BOLD}{YELLOW}{'='*72}{RESET}\n")

    env_col = f"{BOLD}{YELLOW}"
    wax_col = f"{BOLD}{MAGENTA}"
    rst = RESET

    print_bounded(f"  {env_col}.--------------------.{rst}   {BOLD}{CYAN}[RESORT AREA DIPLOMATIC COURIER]{rst}")
    print_bounded(f"  {env_col}| \\                / |{rst}   {YELLOW}Registry: Sinnoh High Society Gazette{rst}")
    print_bounded(f"  {env_col}|  \\              /  |{rst}   {YELLOW}Origin: Ribbon Syndicate Sovereign Ridge{rst}")
    print_bounded(f"  {env_col}|===\\    {wax_col}( ⚜ ){env_col}   /===|{rst}   {YELLOW}Courier: Madame Vivienne, Grand Concierge{rst}")
    print_bounded(f"  {env_col}|   /            \\   |{rst}   {YELLOW}Seal: 24K Ribbon Syndicate Gold Wax{rst}")
    print_bounded(f"  {env_col}'--------------------'{rst}   {YELLOW}Dispatch: Sovereign Luxury Invitation{rst}\n")

    invitation_lines = [
        "\"Greetings, esteemed Trainer.",
        "",
        "The Ribbon Syndicate of Sinnoh extends its most distinguished compliments.",
        "Through our diplomatic financial telemetry, we have taken notice of your",
        f"extraordinary wealth ({format_tokens(LUXURY_WEALTH_THRESHOLD)}+ tokens), surpassing all conventional",
        "trainer standards across the continent.",
        "",
        "By unanimous decree of the Grand Council, you are formally invited to",
        "inspect and acquire the Sovereign Ridge diplomatic estate:",
        "the Resort Area Executive Luxury Suite.",
        "",
        "This private property is reserved exclusively for sovereigns of industry,",
        "corporate chairmen, and legendary trainers of peerless stature.\"",
        "",
        "— Madame Vivienne, Grand Concierge of the Ribbon Syndicate"
    ]
    _write_wrapped_lines(invitation_lines, color=YELLOW)

    print_bounded(f"\n{BOLD}{YELLOW}{'-'*72}{RESET}")
    print_bounded(f"  {BOLD}[1] Pay VIP Broker Fee ({format_tokens(LUXURY_VIP_FEE)}) & Accept Clearance{RESET}")
    print_bounded(f"  {BOLD}[2] Read Luxury Suite Dossier & Wing Specifications{RESET}")
    print_bounded(f"  {BOLD}[3] Politely postpone (review anytime at Bank Tab [10] [L] Luxury){RESET}")
    print_bounded(f"{BOLD}{YELLOW}{'-'*72}{RESET}")
    sys.stdout.write(f"  {YELLOW}Select option (1, 2, or 3):{RESET} ")
    sys.stdout.flush()

    choice = _read_input_safe()
    if choice == "1":
        ok, msg = app.engine.pay_luxury_vip_fee()
        if ok:
            app.current_tab = 10
            app.bank_subtab = "luxury"
            app.message = "⚜️ VIP Clearance Granted! Opened Luxury registry."
        else:
            app.engine.postpone_luxury_invitation()
            app.message = msg
        return

    elif choice == "2":
        # Screen 2: Luxury Suite Architectural Dossier
        sys.stdout.write("\033[H\033[2J")
        print_bounded(f"\n{BOLD}{CYAN}{'='*72}{RESET}")
        print_bounded(f"  {BOLD}{CYAN}🏰 THE RESORT AREA EXECUTIVE LUXURY SUITE — CONFIDENTIAL DOSSIER 🏰{RESET}")
        print_bounded(f"{BOLD}{CYAN}{'='*72}{RESET}\n")

        dossier_lines = [
            "Madame Vivienne slides a velvet-bound leather portfolio across the table.",
            "",
            "\"Your dossier on the Executive Luxury Suite:",
            "",
            f"• ⚜️ VIP BROKER CLEARANCE: {format_tokens(LUXURY_VIP_FEE)} tokens (non-refundable concierge fee).",
            f"• 📜 ESTATE DEED ACQUISITION: {format_tokens(LUXURY_DEED_COST)} tokens (perpetual sovereign ownership).",
            "",
            "Upon acquisition, you gain access to 4 high-technology executive wings:",
            "",
            "• 🥚 AUTOMATED CRYO-NURSERY:",
            "  Parallel background incubation for all queued eggs simultaneously at 2x speed.",
            "",
            "• 💧 HOT SPRINGS & BERRY GROVE:",
            "  Complete immunity to companion happiness decay + permanent +50% coding EXP.",
            "",
            "• 📊 QUANTUM TRADING TERMINAL:",
            "  Real-time market directional telemetry, auto-compounder, & Whale Catalyst.",
            "",
            "• ✨ CHROMATIC RESONATOR:",
            "  Permanent transmutation chamber converting any team companion into a Shiny.",
            "",
            "• 🛋️ 6 PRESTIGE FURNISHINGS:",
            "  Grand Piano, Diamond Chandelier, Golden Arceus Statue, Hologram, Fountain,",
            "  and the Sovereign Tycoon Throne (unlocks title '👑 Sovereign Tycoon').\""
        ]
        _write_wrapped_lines(dossier_lines, color=CYAN)

        print_bounded(f"\n{BOLD}{CYAN}{'-'*72}{RESET}")
        print_bounded(f"  {BOLD}[1] Pay VIP Fee ({format_tokens(LUXURY_VIP_FEE)}) & Unlock Clearance Now{RESET}")
        print_bounded(f"  {BOLD}[2] Return to terminal for now{RESET}")
        print_bounded(f"{BOLD}{CYAN}{'-'*72}{RESET}")
        sys.stdout.write(f"  {CYAN}Select option (1 or 2):{RESET} ")
        sys.stdout.flush()

        choice2 = _read_input_safe()
        if choice2 == "1":
            ok, msg = app.engine.pay_luxury_vip_fee()
            if ok:
                app.current_tab = 10
                app.bank_subtab = "luxury"
                app.message = "⚜️ VIP Clearance Granted! Opened Luxury registry."
            else:
                app.engine.postpone_luxury_invitation()
                app.message = msg
            return

    # Screen 3: Postponement
    sys.stdout.write("\033[H\033[2J")
    print_bounded(f"\n{BOLD}{YELLOW}{'='*72}{RESET}")
    print_bounded(f"  {BOLD}{YELLOW}⚜️  INVITATION HELD ON COURTESY FILE  ⚜️{RESET}")
    print_bounded(f"{BOLD}{YELLOW}{'='*72}{RESET}\n")

    fallback_lines = [
        "Madame Vivienne nods respectfully and seals the envelope with silk ribbon.",
        "",
        "\"A true tycoon never rushes an investment. Your private clearance docket",
        "remains reserved under your name at Bank Tab [10] [L] Luxury.",
        "",
        "Whenever you wish to review your invitation or grant clearance, simply",
        "tune your console to Bank Tab [10]. Good day, Trainer.\""
    ]
    _write_wrapped_lines(fallback_lines, color=YELLOW)

    print_bounded(f"\n{BOLD}{YELLOW}{'-'*72}{RESET}")
    sys.stdout.write(f"  {BOLD}{CYAN}Press [Enter] to resume terminal...{RESET} ")
    sys.stdout.flush()
    _read_input_safe()

    app.engine.postpone_luxury_invitation()


def render_luxury_view(app: Any, avail: int):
    """Renders the Luxury subtab within Bank Tab [10]."""
    # 1. Check if VIP Concierge clearance fee has been paid
    if not app.engine.is_luxury_vip_paid():
        _render_concierge_desk_view(app, avail)
        return

    # 2. Check if Help subview is active (accessible anytime after VIP clearance)
    active_subview = getattr(app, "luxury_subview", getattr(app, "penthouse_subview", "main"))
    if active_subview == "help":
        _render_wing_help_view(app, avail)
        return

    # 3. Check if Luxury deed has been purchased
    if not app.engine.is_luxury_unlocked():
        _render_deed_inspection_view(app, avail)
        return

    # 4. Render fully unlocked executive Luxury Suite
    _render_unlocked_luxury_view(app, avail)


def _render_concierge_desk_view(app: Any, avail: int):
    """Displays the VIP Concierge Desk when 500M clearance fee is pending."""
    print_bounded(f"  {BOLD}{YELLOW}⚜️ The Ribbon Syndicate VIP Concierge Desk{RESET}  (Resort Area)")
    print_bounded("  " + "-" * 68)
    print_bounded(f"  {CYAN}Location: Sovereign Ridge Diplomatic Registry, Sinnoh{RESET}")
    print_bounded(f"  {YELLOW}Status: PENDING VIP CLEARANCE (Wealth Qualification: 100.0B+ Verified){RESET}")
    sys.stdout.write("\n")
    print_bounded(f"  You have received an exclusive invitation from Madame Vivienne to")
    print_bounded(f"  inspect and acquire the Sovereign Executive Luxury Suite.")
    sys.stdout.write("\n")
    print_bounded(f"  {BOLD}VIP Concierge Fee:{RESET} {BOLD}{GREEN}{format_tokens(LUXURY_VIP_FEE)}{RESET} tokens  (Spendable: {BOLD}{CYAN}{format_tokens(avail)}{RESET})")
    print_bounded(f"  Paying this fee grants private clearance to view the deed registry and")
    print_bounded(f"  unlocks the option to purchase the Luxury Suite for {format_tokens(LUXURY_DEED_COST)} tokens.")
    print_bounded("  " + "-" * 68)
    print_bounded(f"  ➔ Type '{BOLD}pay{RESET}' to pay {format_tokens(LUXURY_VIP_FEE)} & unlock clearance")
    print_bounded(f"  ➔ Type '{BOLD}invite{RESET}' to re-read the luxury invitation dispatch")
    print_bounded(f"  ➔ Type '{BOLD}back{RESET}' to return to Checking & Loans")
    sys.stdout.write("\n")


def _render_deed_inspection_view(app: Any, avail: int):
    """Displays Luxury Suite inspection and deed purchase prompt after VIP clearance."""
    print_bounded(f"  {BOLD}{HEADER}🏰 Resort Area Executive Luxury Suite{RESET} (Deed: Unacquired)")
    print_bounded("  " + "-" * 68)
    print_bounded(f"  {GREEN}Status: VIP CLEARANCE GRANTED by Madame Vivienne{RESET}")
    print_bounded(f"  {CYAN}Location: Sovereign Ridge, Resort Area, Sinnoh{RESET}")
    print_bounded(f"  {YELLOW}The pinnacle of luxury & endgame executive power for tycoons.{RESET}")
    sys.stdout.write("\n")
    print_bounded(f"  {BOLD}Estate Acquisition Privileges:{RESET}")
    print_bounded(f"  • {BOLD}Cryo-Nursery Wing:{RESET} Incubate pending eggs concurrently in background")
    print_bounded(f"  • {BOLD}Hot Springs Wing:{RESET} Auto-feeding, decay immunity, +50% coding EXP")
    print_bounded(f"  • {BOLD}Trading Terminal Wing:{RESET} Stock market telemetry & Bull Rally catalyst")
    print_bounded(f"  • {BOLD}Chromatic Resonator:{RESET} Transmute companions to Shiny form")
    print_bounded(f"  • {BOLD}Luxury Furnishings:{RESET} 6 Furnishings & '👑 Sovereign Tycoon' title")
    sys.stdout.write("\n")
    print_bounded(f"  {BOLD}Deed Price:{RESET} {BOLD}{GREEN}{format_tokens(LUXURY_DEED_COST)}{RESET} tokens (Spendable: {BOLD}{CYAN}{format_tokens(avail)}{RESET})")
    print_bounded("  " + "-" * 68)
    print_bounded(f"  ➔ Type '{BOLD}acquire{RESET}' to buy deed | '{BOLD}help wing <1-4>{RESET}' guide | '{BOLD}back{RESET}'")
    sys.stdout.write("\n")


def _render_unlocked_luxury_view(app: Any, avail: int):
    """Displays the fully unlocked Executive Luxury Suite with wings and decor."""
    total_val = app.engine.get_luxury_total_value()
    decor_owned = app.engine.get_luxury_state().get("decor", [])
    has_title = len(decor_owned) == len(LUXURY_DECOR)
    status_title = f"{HEADER}👑 Sovereign Tycoon{RESET}" if has_title else f"{CYAN}Executive Tycoon{RESET}"

    print_bounded(f"  {BOLD}{HEADER}🏰 Resort Area Executive Luxury Suite{RESET} | Status: {status_title}")
    print_bounded(f"  Valuation: {BOLD}{GREEN}{format_tokens(total_val)}{RESET} tokens | Spendable: {BOLD}{CYAN}{format_tokens(avail)}{RESET}")
    print_bounded("  " + "-" * 68)

    # Wings Section (compact 1-line rows, use 'help wing <1-4>' for details)
    print_bounded(f"  {BOLD}Executive Wings:{RESET}  (Type '{BOLD}help wing <1-4>{RESET}' for details)")
    fac_keys = ["nursery", "springs", "trading_desk", "chromatic_lab"]
    for idx, f_key in enumerate(fac_keys, 1):
        fac = LUXURY_FACILITIES[f_key]
        cur_lvl = app.engine.get_luxury_facility_level(f_key)
        max_lvl = len(fac["levels"])
        name = fac["name"]
        icon = fac.get("icon", "🏛️")

        lvl_str = f"{BOLD}{GREEN}Lv {cur_lvl}/{max_lvl}{RESET}" if cur_lvl > 0 else f"{RED}Lv 0/{max_lvl}{RESET}"
        if cur_lvl < max_lvl:
            nxt_cost = format_tokens(fac["levels"][cur_lvl + 1]["cost"])
            cost_str = f"[{YELLOW}Next: {nxt_cost}{RESET}]"
        else:
            cost_str = f"[{GREEN}MAX UPGRADE{RESET}]"

        print_bounded(f"  [{idx}] {icon} {name:<26} {lvl_str:<18} {cost_str}")

    print_bounded("  " + "-" * 68)
    # Decor Section (shows aesthetic aura / passive perk tag)
    print_bounded(f"  {BOLD}Luxury Decor & Furnishings ({len(decor_owned)}/{len(LUXURY_DECOR)} installed):{RESET}")
    decor_keys = list(LUXURY_DECOR.keys())
    for idx, d_key in enumerate(decor_keys, 1):
        d_info = LUXURY_DECOR[d_key]
        is_owned = d_key in decor_owned
        tag = f"{BOLD}{GREEN}[INSTALLED]{RESET}" if is_owned else f"{YELLOW}{format_tokens(d_info['cost']):<11}{RESET}"
        icon = d_info["icon"]
        name = d_info["name"]
        perk = d_info.get("perk", "")
        print_bounded(f"  [{idx}] {icon} {name:<21} {tag} {CYAN}{perk}{RESET}")

    print_bounded("  " + "-" * 68)
    print_bounded(f"  ➔ '{BOLD}help wing <1-4>{RESET}' guide | '{BOLD}upgrade <1-4>{RESET}' | '{BOLD}furnish <1-6>{RESET}'")
    print_bounded(f"  ➔ '{BOLD}interact <1-6>{RESET}' use decor | '{BOLD}back{RESET}' to Checking")
    if app.engine.get_luxury_facility_level("chromatic_lab") >= 1:
        print_bounded(f"  ➔ '{BOLD}transmute <roster_idx>{RESET}' (Convert companion to Shiny)")
    if app.engine.get_luxury_facility_level("trading_desk") >= 3:
        print_bounded(f"  ➔ '{BOLD}catalyst <corp_ticker>{RESET}' (Deploy 1.0T tokens for Bull Rally)")
    if app.engine.is_luxury_fully_completed():
        matrix_st = app.engine.state.get("matrix", {})
        if matrix_st.get("unlocked", False):
            print_bounded(f"  ➔ '{BOLD}descend{RESET}' ({CYAN}Enter Sub-Level Quantum Singularity Matrix{RESET})")
        else:
            print_bounded(f"  ➔ '{BOLD}descend{RESET}' ({YELLOW}Unseal Sub-Level 0 Reactor for 500.0Q tokens{RESET})")
    sys.stdout.write("\n")


def _render_wing_help_view(app: Any, avail: int):
    """Displays technical specifications for Luxury wings."""
    target_wing = getattr(app, "luxury_help_wing", getattr(app, "penthouse_help_wing", None))
    all_fac_keys = ["nursery", "springs", "trading_desk", "chromatic_lab"]

    if target_wing and 1 <= target_wing <= len(all_fac_keys):
        active_indices = [target_wing]
        header_title = f"Wing [{target_wing}] Guide"
    else:
        active_indices = list(range(1, len(all_fac_keys) + 1))
        header_title = "Executive Wings Architectural Guide"

    print_bounded(f"  {BOLD}{HEADER}🏰 Executive Luxury Suite — {header_title}{RESET}")
    print_bounded(f"  Spendable: {BOLD}{CYAN}{format_tokens(avail)}{RESET} tokens | Type '{BOLD}back{RESET}' to return to Luxury Suite")
    print_bounded("  " + "-" * 68)

    for idx in active_indices:
        f_key = all_fac_keys[idx - 1]
        fac = LUXURY_FACILITIES[f_key]
        cur_lvl = app.engine.get_luxury_facility_level(f_key)
        max_lvl = len(fac["levels"])
        name = fac["name"]
        icon = fac.get("icon", "🏛️")

        lvl_tag = f"{BOLD}{GREEN}(Current: Lv {cur_lvl}/{max_lvl}){RESET}" if cur_lvl > 0 else f"{RED}(Current: Lv 0/{max_lvl}){RESET}"
        print_bounded(f"  {BOLD}[{idx}] {icon} {name.upper()}{RESET} {lvl_tag}")

        for lvl_num, lvl_data in fac["levels"].items():
            lvl_name = lvl_data["name"]
            lvl_cost = format_tokens(lvl_data["cost"])
            lvl_desc = lvl_data["desc"]
            is_active = cur_lvl >= lvl_num
            status_glyph = f"{GREEN}✓{RESET}" if is_active else f"{YELLOW}•{RESET}"
            cost_info = f"{GREEN}ACTIVE{RESET}" if is_active else f"{YELLOW}{lvl_cost}{RESET}"

            print_bounded(f"      {status_glyph} {BOLD}Lv {lvl_num}: {lvl_name}{RESET} [{cost_info}]")
            for wline in textwrap.wrap(lvl_desc, width=58):
                print_bounded(f"        {CYAN}{wline}{RESET}")

        if idx != active_indices[-1]:
            sys.stdout.write("\n")

    print_bounded("  " + "-" * 68)
    if target_wing and 1 <= target_wing <= len(all_fac_keys):
        print_bounded(f"  ➔ '{BOLD}upgrade {target_wing}{RESET}' upgrade this wing | '{BOLD}help wing <1-4>{RESET}' other wings")
        print_bounded(f"  ➔ '{BOLD}back{RESET}' return to Luxury Suite overview")
    else:
        print_bounded(f"  ➔ '{BOLD}upgrade <1-4>{RESET}' upgrade wing | '{BOLD}help wing <1-4>{RESET}' wing details")
        print_bounded(f"  ➔ '{BOLD}back{RESET}' return to Luxury Suite overview")
    sys.stdout.write("\n")


# Backward-compatible aliases
_render_facility_help_view = _render_wing_help_view
_render_unlocked_penthouse_view = _render_unlocked_luxury_view
render_penthouse_view = render_luxury_view
render_villa_view = render_luxury_view
render_penthouse_invitation = render_luxury_invitation
