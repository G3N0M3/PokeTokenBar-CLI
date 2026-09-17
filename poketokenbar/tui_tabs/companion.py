import sys
import datetime
from poketokenbar.game.models import PokemonBalance
from poketokenbar.sprite_renderer import SpriteRenderer
from poketokenbar.utils.formatting import format_tokens, format_progress_bar

HEADER = "\033[95m\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def render(app, summary: dict):
    active = app.engine.active_mon

    if active is None:
        egg_tier = app.engine.state.get("egg_tier")
        if egg_tier:
            # Egg state
            egg_usage = app.engine.state.get("egg_usage", 0)
            threshold = PokemonBalance.EGG_HATCH_THRESHOLD
            bar = format_progress_bar(egg_usage, threshold)

            sys.stdout.write(f"\n  {YELLOW}🥚 Pokémon Egg Incubating...{RESET}\n")
            sys.stdout.write(f"  Incubation: {bar} ({format_tokens(egg_usage)} / {format_tokens(threshold)} tokens)\n")
            sys.stdout.write("  Keep spending tokens in Antigravity CLI to hatch your egg!\n\n")
        else:
            sys.stdout.write(f"\n  {BOLD}{RED}No active companion selected!{RESET}\n")
            sys.stdout.write("  Visit the Roster tab (3) and type 'sel <number>' to select a companion to travel with you!\n\n")
    else:
        # Active Pokémon
        sp_id = active.current_id
        name = app.engine.api.get_species_name(sp_id)
        shiny_str = f"{YELLOW}✨ SHINY {RESET}" if active.is_shiny else ""
        nature_name = active.nature.display_name if active.nature else "Unknown"
        mega_badge = f" {BOLD}{HEADER}[✨ MEGA EVOLVED +50% XP]{RESET}" if active.is_mega else ""

        sys.stdout.write(f"\n  {BOLD}{GREEN}Active Companion: {shiny_str}{name} (#{sp_id}){mega_badge}{RESET}\n")
        sys.stdout.write(f"  Rarity: {YELLOW}{active.rarity.value.upper()}{RESET}  |  Nature: {CYAN}{nature_name}{RESET}  |  Form: {active.stage_index+1}/{active.total_forms}\n")

        held_str = "None"
        if active.held_item:
            from poketokenbar.game.models import ItemKind
            try:
                kind = ItemKind(active.held_item)
                held_str = f"{kind.emoji} {kind.name_en}"
            except ValueError:
                held_str = str(active.held_item)

        happiness = active.happiness if active else app.engine.state.get("happiness", 100)
        streak = app.engine.state.get("streak_days", 1)
        hap_boost = f" {GREEN}(+20% XP){RESET}" if happiness >= 100 else ""
        sys.stdout.write(f"  Happiness: {RED}💖 {happiness}%{RESET}{hap_boost}  |  Streak: {YELLOW}🔥 {streak}d{RESET}  |  Held: {BOLD}{CYAN}{held_str}{RESET}\n")
        
        last_milestone = app.engine.state.get("last_milestone") or app.engine.state.get("last_evolution")
        if last_milestone:
            if "hatched" in last_milestone.lower():
                icon = "🐣"
            elif "graduated" in last_milestone.lower():
                icon = "🎓"
            else:
                icon = "🎉"
            prefix = "" if any(last_milestone.startswith(e) for e in ["🐣", "🎉", "🎓", "✨"]) else f"{icon} "
            clean_text = f"{prefix}{last_milestone}"
            import re
            visible_len = len(re.sub(r'\033\[[0-9;]*m', '', clean_text))
            if visible_len > 59:
                clean_text = clean_text[:56] + "..."
            sys.stdout.write(f"  {BOLD}{CYAN}Milestone:{RESET} {clean_text}\n")

        # Try rendering sprite
        render_id = sp_id
        if active.is_mega:
            mega_map = {
                "3": 10033, "6_X": 10034, "6_Y": 10035, "9": 10036, "15": 10090,
                "18": 10073, "65": 10037, "80": 10071, "94": 10038, "115": 10039,
                "127": 10040, "130": 10041, "142": 10042, "150_X": 10043, "150_Y": 10044,
                "154": 10282, "160": 10283,
                "181": 10045, "208": 10072, "212": 10046, "214": 10047, "229": 10048,
                "248": 10049, "254": 10065, "257": 10050, "260": 10064, "282": 10051,
                "302": 10066, "303": 10052, "306": 10053, "308": 10054, "310": 10055,
                "319": 10070, "323": 10087, "334": 10067, "354": 10056, "359": 10057,
                "362": 10074, "373": 10089, "376": 10076, "380": 10062, "381": 10063,
                "382": 10077, "383": 10078, "384": 10079, "428": 10088, "445": 10058,
                "448": 10059, "460": 10060, "475": 10068, "531": 10069, "719": 10075
            }
            form_key = f"{sp_id}_{active.mega_form}" if getattr(active, 'mega_form', None) in ["X", "Y"] else str(sp_id)
            render_id = mega_map.get(form_key, sp_id)
            
        sprite_path = app.engine.api.download_sprite(render_id, is_shiny=active.is_shiny)
        if sprite_path:
            sprite_size = app.engine.state.get("sprite_size", 30)
            sprite_ansi = SpriteRenderer.render_png_to_ansi(sprite_path, max_cols=sprite_size, center_width=72)
            sys.stdout.write("\n" + sprite_ansi + "\n\n")


        # Growth / Evolution progress
        target_xp = PokemonBalance.phase_threshold(active.rarity, active.total_forms, active.stage_index, app.engine.current_difficulty)

        if active.stage_index < len(active.path_ids) - 1:
            next_id = app.engine.get_next_evolution_id(active)
            if not next_id:
                next_id = active.path_ids[active.stage_index + 1]
            next_name = app.engine.api.get_species_name(next_id)
            time_tag = ""
            if app.engine.is_time_based_evolution(active):
                tod = app.engine.get_current_time_of_day()
                time_tag = " (☀️ Day)" if tod == "day" else " (🌙 Night)"
            bar = format_progress_bar(active.used_at_stage, target_xp, width=12)
            dex = app.engine.state.get("dex", [])
            discovered_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))) for d in dex}

            evo_label = f"  Evo -> {next_name}{time_tag}: "
            status_tag = ""
            status_clean = ""
            if active.held_item == "everstone":
                status_tag = f" {YELLOW}[EVERSTONE]{RESET}"
                status_clean = " [EVERSTONE]"
            elif next_id in discovered_sp_ids:
                status_tag = f" {YELLOW}[OWNED]{RESET}"
                status_clean = " [OWNED]"

            base_str = f"{evo_label}{bar} ({format_tokens(active.used_at_stage)} / {format_tokens(target_xp)})"
            if len(base_str) + len(status_clean) > 72:
                compact_tag = " (☀️)" if app.engine.get_current_time_of_day() == "day" else " (🌙)" if time_tag else ""
                evo_label = f"  Evo -> {next_name}{compact_tag}: "
                base_str = f"{evo_label}{bar} ({format_tokens(active.used_at_stage)} / {format_tokens(target_xp)})"
                if len(base_str) + len(status_clean) > 72:
                    evo_label = f"  Evo -> {next_name}: "

            sys.stdout.write(f"{evo_label}{bar} ({format_tokens(active.used_at_stage)} / {format_tokens(target_xp)}){status_tag}\n")
        else:
            bar = format_progress_bar(active.used_at_stage, target_xp, width=12)
            sys.stdout.write(f"  Graduation: {bar} ({format_tokens(active.used_at_stage)} / {format_tokens(target_xp)})\n")

    sys.stdout.write("\n" + "-" * 72 + "\n")
    sys.stdout.write(f" {BOLD}📊 Token Usage Metrics:{RESET}\n")
    sys.stdout.write(f"  • Today's Tokens: {BOLD}{CYAN}{format_tokens(summary.get('today_tokens', 0))}{RESET}  (Antigravity: {format_tokens(summary.get('antigravity_today', 0))})\n")
    sys.stdout.write(f"  • 7-Day Tokens:   {format_tokens(summary.get('week_tokens', 0))}\n")

    b_day = summary.get("billing_cycle_day", app.engine.state.get("billing_cycle_day", 1))
    cycle_start = summary.get("billing_cycle_start")
    if not cycle_start:
        from poketokenbar.tracker.manager import get_billing_cycle_start
        cycle_start = get_billing_cycle_start(datetime.datetime.now().astimezone(), b_day).strftime("%Y-%m-%d")
    cycle_extra = f" | Cycle: Day {b_day}" if b_day != 1 else ""
    month_tag = f"  (since {cycle_start}{cycle_extra})"
    sys.stdout.write(f"  • Monthly Tokens: {format_tokens(summary.get('month_tokens', 0))}{month_tag}\n")

    base_tok = summary.get("baseline_total_tokens", app.engine.state.get("baseline_total_tokens", 0))
    if base_tok > 0:
        base_date = summary.get("baseline_date") or app.engine.state.get("baseline_date") or app.engine.state.get("last_active_date") or datetime.datetime.now().strftime("%Y-%m-%d")
        total_tag = f"  (since {base_date} | re-baselined)"
    else:
        earliest_date = summary.get("earliest_date") or (summary.get("active_days") and summary.get("active_days")[0]) or app.engine.state.get("last_active_date") or datetime.datetime.now().strftime("%Y-%m-%d")
        total_tag = f"  (since {earliest_date})"
    sys.stdout.write(f"  • Total Tokens:   {format_tokens(summary.get('total_tokens', 0))}{total_tag}\n")
    sys.stdout.write(f"  • Active Burn:    {format_tokens(summary.get('burn_rate_tpm', 0))} tokens/min\n")
