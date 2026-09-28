"""Celebration modal screen for evolution, egg hatch, and graduation alerts."""

import sys
import re
from poketokenbar.game.models import MonState, Rarity
from poketokenbar.game.storage import StorageManager
from poketokenbar.sprite_renderer import SpriteRenderer

HEADER = "\033[95m\033[1m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check_and_render_celebration(app) -> bool:
    """Checks for pending celebration alerts and renders milestone screen if present.
    
    Returns True if a celebration was displayed (and loop should continue).
    """
    alerts = app.engine.state.get("unread_alerts", [])
    milestone_alerts = [a for a in alerts if "Evolution!" in a or "Graduation!" in a or "Egg Hatched!" in a]
    if not milestone_alerts:
        return False

    m_alert = milestone_alerts[0]
    alerts.remove(m_alert)
    app.engine.state["unread_alerts"] = alerts
    app.engine.save()

    app.clear_screen()
    is_hatch = "Egg Hatched!" in m_alert
    is_grad = "Graduation!" in m_alert
    if is_hatch:
        banner_title = "🐣 CONGRATULATIONS! YOUR EGG HATCHED! 🐣"
    elif is_grad:
        banner_title = "🎓 CONGRATULATIONS! YOUR COMPANION GRADUATED! 🎓"
    else:
        banner_title = "✨ WHAT? YOUR COMPANION IS EVOLVING! ✨"

    sys.stdout.write(f"\n{HEADER}{'='*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}{YELLOW}{banner_title}{RESET}\n")
    sys.stdout.write(f"{HEADER}{'='*72}{RESET}\n\n")

    # 1. Parse target Pokémon species ID from the alert message
    sp_id = None
    m_ids = re.findall(r"#(\d+)", m_alert)
    if m_ids:
        sp_id = int(m_ids[-1])
    else:
        m_name = re.search(
            r"(?:Hatched! You got a|evolved into|Graduation!)\s+(?:✨\s*Shiny\s+)?([A-Za-z0-9\- ']+?)(?:\s*\(|\s+has graduated|\s*!|$)",
            m_alert,
        )
        if m_name:
            cand_name = m_name.group(1).strip()
            for d in app.engine.state.get("dex", []):
                cid = d.get("species_id") or d.get("base_id")
                if cid and app.engine.api.get_species_name(cid).lower() == cand_name.lower():
                    sp_id = cid
                    break
        if sp_id is None and app.engine.active_mon:
            sp_id = app.engine.active_mon.current_id

    is_shiny = "Shiny" in m_alert

    target_mon = None
    target_entry = None
    dex = app.engine.state.get("dex", [])

    if sp_id:
        for d in dex:
            if d.get("species_id") == sp_id:
                target_entry = d
                m_data = d.get("mon_state")
                if m_data:
                    target_mon = StorageManager.dict_to_mon(m_data)
                break

    active = app.engine.active_mon
    if target_mon is None and active and sp_id:
        if active.current_id == sp_id:
            target_mon = active
        elif active.base_id == sp_id and active.stage_index == 0:
            target_mon = active
        elif hasattr(active, "path_ids") and sp_id in active.path_ids:
            stage_idx = active.path_ids.index(sp_id)
            target_mon = MonState(
                base_id=active.base_id,
                path_ids=active.path_ids,
                planned_path_ids=active.planned_path_ids,
                stage_index=stage_idx,
                used_at_stage=0,
                rarity=active.rarity,
                total_forms=active.total_forms,
                is_shiny=active.is_shiny,
                happiness=active.happiness,
            )

    if target_mon and not is_shiny:
        is_shiny = getattr(target_mon, "is_shiny", False)
    elif target_entry and not is_shiny:
        is_shiny = bool(target_entry.get("is_shiny", False))

    stage_str = ""
    rarity_str = ""

    if target_mon:
        if is_grad:
            stage_str = f"Final Form ({target_mon.total_forms}/{target_mon.total_forms})"
        else:
            stage_str = f"Form {target_mon.stage_index+1}/{target_mon.total_forms}"
        rarity_str = target_mon.rarity.value.upper()
    elif target_entry:
        rarity_val = target_entry.get("rarity")
        if rarity_val:
            rarity_str = str(rarity_val).upper()
        if is_grad:
            stage_str = "Final Form (Graduated)"
        elif is_hatch:
            stage_str = "Form 1 (Hatched)"
        else:
            stage_str = "Evolved Form"

    if not rarity_str:
        r_match = re.search(r"Rarity:\s*([A-Za-z+]+)", m_alert)
        if r_match:
            rarity_str = r_match.group(1).upper()
        elif sp_id:
            sp_data = app.engine.api.get_pokemon_species(sp_id)
            if sp_data:
                cap_rate = sp_data.get("capture_rate", 255)
                is_leg = sp_data.get("is_legendary", False) or sp_data.get("is_mythical", False)
                rarity_str = Rarity.from_capture_rate(cap_rate, is_leg).value.upper()

    if not stage_str:
        if is_grad:
            stage_str = "Final Form (Graduated)"
        elif is_hatch:
            stage_str = "Form 1 (Hatched)"
        else:
            stage_str = "Evolved Form"

    if sp_id:
        sprite_path = app.engine.api.download_sprite(sp_id, is_shiny=is_shiny)
        if sprite_path:
            sprite_size = app.engine.state.get("sprite_size", 30)
            ansi = SpriteRenderer.render_png_to_ansi(sprite_path, max_cols=sprite_size, center_width=72)
            sys.stdout.write(ansi + "\n\n")

    sys.stdout.write(f"  {BOLD}{GREEN}{m_alert}{RESET}\n\n")
    if stage_str and rarity_str:
        sys.stdout.write(f"  Stage: {stage_str}  |  Rarity: {YELLOW}{rarity_str}{RESET}\n\n")
    elif stage_str:
        sys.stdout.write(f"  Stage: {stage_str}\n\n")

    sys.stdout.write(f"  {BOLD}{CYAN}Press [Enter] to continue...{RESET} ")
    sys.stdout.flush()
    sys.stdin.readline()
    return True
