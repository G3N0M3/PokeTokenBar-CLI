import os
import sys
import time
import random
import datetime
import math
import re
from typing import Optional, Tuple, Set, List

from poketokenbar.tracker.manager import UsageManager
from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.models import ItemKind, Rarity, PokemonBalance, MonState
from poketokenbar.game.storage import StorageManager
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

class PokeTokenBarTUI:
    """Interactive Linux CLI Terminal User Interface for PokeTokenBar."""

    def __init__(self):
        self.tracker = UsageManager()
        self.engine = CompanionEngine()
        self.current_tab = 1
        self.message = ""
        self.pending_reset = False
        self.pending_rocket_init = False
        self.pokedex_page = 1
        self.roster_page = 1
        self.stock_page = 1
        self.stock_terminal = None
        self.selected_expedition_targets: Set[int] = set()
        self.expedition_picker_mode: bool = False
        self.picker_page: int = 1
        self.settings_page: int = 1
        self.armory_page: int = 1
        self.pending_feed = None
        self.pending_buy = None

    def clear_screen(self):
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()

    def run(self):
        """Main interactive event loop."""
        # Initial refresh
        summary = self.tracker.get_summary()
        self.engine.process_usage(summary.get("raw_total_tokens", summary["total_tokens"]), summary.get("active_days"))

        while True:
            # Refresh usage and process growth on each frame
            summary = self.tracker.get_summary()
            self.engine.process_usage(summary.get("raw_total_tokens", summary["total_tokens"]), summary.get("active_days"))

            # Check for evolution, graduation, or egg hatch alerts to show celebration screen
            alerts = self.engine.state.get("unread_alerts", [])
            milestone_alerts = [a for a in alerts if "Evolution!" in a or "Graduation!" in a or "Egg Hatched!" in a]
            if milestone_alerts:
                m_alert = milestone_alerts[0]
                alerts.remove(m_alert)
                self.engine.state["unread_alerts"] = alerts
                self.engine.save()

                self.clear_screen()
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
                    # Fallback for legacy alerts without (#id): try to match species name
                    m_name = re.search(
                        r"(?:Hatched! You got a|evolved into|Graduation!)\s+(?:✨\s*Shiny\s+)?([A-Za-z0-9\- ']+?)(?:\s*\(|\s+has graduated|\s*!|$)",
                        m_alert,
                    )
                    if m_name:
                        cand_name = m_name.group(1).strip()
                        for d in self.engine.state.get("dex", []):
                            cid = d.get("species_id") or d.get("base_id")
                            if cid and self.engine.api.get_species_name(cid).lower() == cand_name.lower():
                                sp_id = cid
                                break
                    if sp_id is None and self.engine.active_mon:
                        sp_id = self.engine.active_mon.current_id

                # 2. Determine shiny status
                is_shiny = "Shiny" in m_alert

                # 3. Locate target companion state or dex entry for stage and rarity
                target_mon = None
                target_entry = None
                dex = self.engine.state.get("dex", [])

                if sp_id:
                    for d in dex:
                        if d.get("species_id") == sp_id:
                            target_entry = d
                            m_data = d.get("mon_state")
                            if m_data:
                                target_mon = StorageManager.dict_to_mon(m_data)
                            break

                active = self.engine.active_mon
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

                # 4. Determine stage_str and rarity_str
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

                # Fallback for rarity if still missing
                if not rarity_str:
                    r_match = re.search(r"Rarity:\s*([A-Za-z+]+)", m_alert)
                    if r_match:
                        rarity_str = r_match.group(1).upper()
                    elif sp_id:
                        sp_data = self.engine.api.get_pokemon_species(sp_id)
                        if sp_data:
                            cap_rate = sp_data.get("capture_rate", 255)
                            is_leg = sp_data.get("is_legendary", False) or sp_data.get("is_mythical", False)
                            rarity_str = Rarity.from_capture_rate(cap_rate, is_leg).value.upper()

                # Fallback for stage if still missing
                if not stage_str:
                    if is_grad:
                        stage_str = "Final Form (Graduated)"
                    elif is_hatch:
                        stage_str = "Form 1 (Hatched)"
                    else:
                        stage_str = "Evolved Form"

                if sp_id:
                    sprite_path = self.engine.api.download_sprite(sp_id, is_shiny=is_shiny)
                    if sprite_path:
                        sprite_size = self.engine.state.get("sprite_size", 30)
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
                continue

            pending_eggs = self.engine.state.get("pending_eggs", [])
            if pending_eggs:
                new_egg = pending_eggs[0]
                curr_egg = self.engine.state.get("egg_tier")
                if curr_egg is None:
                    # User has an open slot, auto-assign the egg
                    self.engine.state["egg_tier"] = new_egg
                    self.engine.state["egg_usage"] = 0
                    self.engine.state["pending_eggs"] = pending_eggs[1:]
                    self.engine.save()
                    sys.stdout.write(f"\n  {GREEN}You found a {new_egg.capitalize()} Egg! It is now incubating.{RESET}\n")
                    continue
                    
                self.clear_screen()
                sys.stdout.write(f"\n  {BOLD}{YELLOW}🥚 EGG DECISION!{RESET}\n\n")
                sys.stdout.write(f"  You found a {BOLD}{new_egg.capitalize()}{RESET} Egg, but you can only carry one egg at a time!\n")
                sys.stdout.write(f"  You are currently holding a {BOLD}{curr_egg.capitalize()}{RESET} Egg.\n\n")
                sys.stdout.write(f"  Do you want to SWAP your {curr_egg.capitalize()} Egg for the {new_egg.capitalize()} Egg? (y/n)> ")
                sys.stdout.flush()
                cmd = sys.stdin.readline().strip().lower()
                
                egg_payouts = {
                    "common": 500_000,
                    "uncommon": 1_000_000,
                    "rare": 2_500_000,
                    "epic": 5_000_000,
                    "legendary": 10_000_000,
                    "mysterious fetal form": 50_000_000,
                    "normal": 500_000
                }
                
                if cmd in ["y", "yes"]:
                    payout = egg_payouts.get(curr_egg.lower(), 500_000)
                    self.engine.state["spent_tokens"] = self.engine.state.get("spent_tokens", 0) - payout
                    self.engine.state["egg_tier"] = new_egg
                    self.engine.state["egg_usage"] = 0
                    self.engine.state["pending_eggs"] = pending_eggs[1:]
                    self.engine.save()
                    sys.stdout.write(f"\n  {GREEN}Swapped! You are now holding a {new_egg.capitalize()} Egg!{RESET}\n")
                    sys.stdout.write(f"  {YELLOW}The discarded {curr_egg.capitalize()} Egg was sold for {format_tokens(payout)} tokens!{RESET}\n")
                    time.sleep(2)
                elif cmd in ["n", "no"]:
                    payout = egg_payouts.get(new_egg.lower(), 500_000)
                    self.engine.state["spent_tokens"] = self.engine.state.get("spent_tokens", 0) - payout
                    self.engine.state["pending_eggs"] = pending_eggs[1:]
                    self.engine.save()
                    sys.stdout.write(f"\n  {YELLOW}Discarded the {new_egg.capitalize()} Egg and sold it for {format_tokens(payout)} tokens!{RESET}\n")
                    time.sleep(2)
                else:
                    sys.stdout.write(f"\n  {RED}Invalid choice. Please type 'y' or 'n'.{RESET}\n")
                    time.sleep(1)
                continue

            if self.engine.state.get("rocket_story_unlocked") and not self.engine.state.get("rocket_story_viewed"):
                from poketokenbar.tui_tabs.rocket import render_rocket_transmission
                render_rocket_transmission(self)
                self.current_tab = 12
                continue

            # Auto-display operation briefing transmission if not yet viewed
            if self.current_tab == 12 and getattr(self, "rocket_subview", "ops") == "ops" and self.engine.state.get("rocket_alliance_accepted", False):
                operations = self.engine.get_rocket_operations()
                active_op = next((op for op in operations if op["status"] == "active" and not op["claimed"]), None)
                if not active_op:
                    active_op = next((op for op in operations if op["status"] == "available" and not op["claimed"]), None)
                if active_op:
                    op_st = self.engine.state.get("rocket_ops", {}).get(active_op["id"], {})
                    if not op_st.get("briefing_viewed", False):
                        from poketokenbar.tui_tabs.rocket import render_operation_dialogue
                        render_operation_dialogue(self, active_op["code"])
                        op_st["briefing_viewed"] = True
                        self.engine.save()
                        continue

            self.clear_screen()
            summary = self.tracker.get_summary()

            self.render_header(summary)
            self.render_tabs()

            if self.current_tab == 1:
                self.render_companion_tab(summary)
            elif self.current_tab == 2:
                self.render_pokedex_tab()
            elif self.current_tab == 3:
                self.render_roster_tab()
            elif self.current_tab == 4:
                self.render_shop_tab()
            elif self.current_tab == 5:
                self.render_expeditions_tab()
            elif self.current_tab == 6:
                self.render_battles_tab()
            elif self.current_tab == 7:
                self.render_quests_tab()
            elif self.current_tab == 8:
                self.render_mega_evo_tab()
            elif self.current_tab == 9:
                self.render_game_corner_tab()
            elif self.current_tab == 10:
                self.render_bank_tab()
            elif self.current_tab == 11:
                self.render_settings_tab()
            elif self.current_tab == 12:
                from poketokenbar.tui_tabs.rocket import render_rocket_tab
                render_rocket_tab(self)

            self.render_footer()

            tab_max = 12 if self.engine.state.get("rocket_story_unlocked") else 11
            sys.stdout.write(f"\n{BOLD}Select tab (1-{tab_max}), command, r=Refresh, q=Quit: {RESET}")
            sys.stdout.flush()

            try:
                line = sys.stdin.readline()
                if not line:
                    break
                cmd = line.strip().lower()
                if cmd == "q":
                    print("\nExiting PokeTokenBar. Keep coding! 🐾")
                    break
                if self.pending_reset:
                    self.pending_reset = False
                    if cmd == "reset all":
                        ok, msg = self.engine.reset_game_state()
                        self.message = f"🧹 {msg}"
                    else:
                        self.message = "❌ Reset cancelled."
                elif getattr(self, "pending_rocket_init", False):
                    self.pending_rocket_init = False
                    if cmd in ["confirm", "confirm rocket", "rocket init", "yes", "y"]:
                        ok, msg = self.engine.initialize_rocket_process()
                        self.message = f"🚀 {msg}"
                    else:
                        self.message = "❌ Team Rocket initialization cancelled."
                elif getattr(self, "pending_feed", None) is not None:
                    plan = self.pending_feed
                    self.pending_feed = None
                    if cmd in ["confirm", "yes", "y", "ok"]:
                        ok, msg = self.engine.execute_feed_plan(plan)
                        self.message = msg
                    elif cmd.startswith("feed ") or cmd == "feed":
                        self.handle_feed_command(cmd)
                    else:
                        self.message = "❌ Feeding cancelled."
                        tab_max = 12 if self.engine.state.get("rocket_story_unlocked") else 11
                        if cmd in [str(i) for i in range(1, tab_max + 1)]:
                            self.current_tab = int(cmd)
                            self.message = ""
                elif getattr(self, "pending_buy", None) is not None:
                    plan = self.pending_buy
                    self.pending_buy = None
                    if cmd in ["confirm", "yes", "y", "ok", "buy"]:
                        ok, msg = self.execute_pending_buy(plan)
                        self.message = msg
                    elif self.current_tab == 4 and (cmd.startswith("buy ") or cmd == "buy"):
                        self.handle_shop_buy(cmd)
                    elif self.current_tab == 10 and (cmd.startswith("buy ") or cmd == "buy" or cmd.startswith("invest ")):
                        if cmd.startswith("invest "):
                            self.handle_invest_command(cmd)
                        else:
                            self.handle_stock_terminal_buy(cmd)
                    else:
                        self.message = "❌ Purchase cancelled."
                        tab_max = 12 if self.engine.state.get("rocket_story_unlocked") else 11
                        if cmd in [str(i) for i in range(1, tab_max + 1)]:
                            self.current_tab = int(cmd)
                            self.message = ""
                elif getattr(self, "expedition_picker_mode", False):
                    # In Interactive Expedition Picker mode
                    if cmd == "back":
                        self.expedition_picker_mode = False
                        self.message = "Exited Expedition Dispatcher."
                    elif cmd in ["n", "next"]:
                        dex = self.engine.state.get("dex", [])
                        roster = [d for d in dex if d.get("status") != "evolved"]
                        page_size = 8
                        total_pages = max(1, math.ceil(len(roster) / page_size))
                        if getattr(self, "picker_page", 1) < total_pages:
                            self.picker_page = getattr(self, "picker_page", 1) + 1
                        else:
                            self.message = f"Already on the last page ({total_pages})."
                    elif cmd in ["p", "prev"]:
                        if getattr(self, "picker_page", 1) > 1:
                            self.picker_page = getattr(self, "picker_page", 1) - 1
                        else:
                            self.message = "Already on page 1."
                    elif cmd.startswith("page "):
                        try:
                            target_p = int(cmd.split()[1])
                            dex = self.engine.state.get("dex", [])
                            roster = [d for d in dex if d.get("status") != "evolved"]
                            page_size = 8
                            total_pages = max(1, math.ceil(len(roster) / page_size))
                            if 1 <= target_p <= total_pages:
                                self.picker_page = target_p
                            else:
                                self.message = f"Invalid page. Must be between 1 and {total_pages}."
                        except ValueError:
                            self.message = "Usage: page <number>"
                    elif cmd == "clear":
                        self.selected_expedition_targets.clear()
                        self.message = "Cleared all selected companions."
                    elif cmd == "all":
                        indices = self._parse_indices_string("all")
                        self._toggle_selection_indices(indices)
                    elif cmd.startswith("feed ") or cmd == "feed":
                        self.handle_feed_command(cmd)
                    elif self._is_expedition_destination_cmd(cmd):
                        area = self._resolve_expedition_destination(cmd)
                        if not self.selected_expedition_targets:
                            self.message = f"No companions selected! Enter row numbers (e.g. '1 2 3') first before choosing destination '{area}'."
                        else:
                            target_list = [str(i) for i in sorted(self.selected_expedition_targets)]
                            ok, msg = self.engine.dispatch_expedition(target_list, area)
                            if ok:
                                self.selected_expedition_targets.clear()
                                self.expedition_picker_mode = False
                            self.message = msg
                    else:
                        clean_cmd = cmd.replace("toggle", "").replace("pick", "").replace("select", "").strip()
                        indices = self._parse_indices_string(clean_cmd)
                        if indices:
                            self._toggle_selection_indices(indices)
                        else:
                            self.message = "Enter row numbers to toggle, destination ('viridian', 'mine', etc.) to launch, or 'back' to exit."
                elif self.current_tab == 10 and getattr(self, "bank_subtab", "") == "stocks" and getattr(self, "stock_terminal", None) and cmd == "back":
                    self.stock_terminal = None
                    self.message = "Returned to Exchange Board."
                elif self.current_tab == 9 and getattr(self, "minigame_state", "menu") == "grunt_bribe" and cmd == "back":
                    self.minigame_state = "slot"
                    self.message = "You stepped away from the suspicious poster."
                elif self.current_tab == 9 and getattr(self, "minigame_state", "menu") != "menu" and cmd == "back":
                    self.minigame_state = "menu"
                    self.message = "Returned to Game Corner menu."
                elif cmd == "250220":
                    self.engine.state["spent_tokens"] = self.engine.state.get("spent_tokens", 0) - 50_000_000
                    self.engine.save()
                    self.message = "🎉 EASTER EGG UNLOCKED! Granted 50.0M Tokens! 🎉"
                elif cmd in [str(i) for i in range(1, 13 if self.engine.state.get("rocket_story_unlocked") else 12)]:
                    self.expedition_picker_mode = False
                    self.stock_terminal = None
                    self.black_market_session = False
                    if getattr(self, "shop_view", "normal") == "black_market":
                        self.shop_view = "normal"
                    self.current_tab = int(cmd)
                    self.message = ""
                elif cmd == "r":
                    summary = self.tracker.get_summary(force=True)
                    self.engine.process_usage(summary.get("raw_total_tokens", summary["total_tokens"]), summary.get("active_days"))
                    self.message = f"Refreshed usage logs! Total indexed: {format_tokens(summary['total_tokens'])} tokens."
                elif cmd in ["n", "next"] and (self.current_tab in [2, 3, 4, 5, 8, 11] or (self.current_tab == 10 and getattr(self, "bank_subtab", "") in ["stocks", "cd"]) or (self.current_tab == 12 and getattr(self, "rocket_subview", "ops") == "intel")):
                    if self.current_tab == 2: self.pokedex_page += 1
                    elif self.current_tab == 4:
                        if not hasattr(self, 'shop_page'): self.shop_page = 1
                        self.shop_page += 1
                    elif self.current_tab == 5:
                        if not hasattr(self, 'expedition_page'): self.expedition_page = 1
                        self.expedition_page += 1
                    elif self.current_tab == 8:
                        if not hasattr(self, 'mega_page'): self.mega_page = 1
                        self.mega_page += 1
                    elif self.current_tab == 10:
                        if getattr(self, "bank_subtab", "") == "cd":
                            if not hasattr(self, 'cd_page'): self.cd_page = 1
                            self.cd_page += 1
                        else:
                            if not hasattr(self, 'stock_page'): self.stock_page = 1
                            self.stock_page += 1
                    elif self.current_tab == 11:
                        if not hasattr(self, 'settings_page'): self.settings_page = 1
                        self.settings_page += 1
                    elif self.current_tab == 12:
                        if not hasattr(self, 'intel_page'): self.intel_page = 1
                        self.intel_page += 1
                    else: self.roster_page += 1
                    self.message = ""
                elif cmd in ["p", "prev"] and (self.current_tab in [2, 3, 4, 5, 8, 11] or (self.current_tab == 10 and getattr(self, "bank_subtab", "") in ["stocks", "cd"]) or (self.current_tab == 12 and getattr(self, "rocket_subview", "ops") == "intel")):
                    if self.current_tab == 2: self.pokedex_page = max(1, self.pokedex_page - 1)
                    elif self.current_tab == 4:
                        if not hasattr(self, 'shop_page'): self.shop_page = 1
                        self.shop_page = max(1, self.shop_page - 1)
                    elif self.current_tab == 5:
                        if not hasattr(self, 'expedition_page'): self.expedition_page = 1
                        self.expedition_page = max(1, self.expedition_page - 1)
                    elif self.current_tab == 8:
                        if not hasattr(self, 'mega_page'): self.mega_page = 1
                        self.mega_page = max(1, self.mega_page - 1)
                    elif self.current_tab == 10:
                        if getattr(self, "bank_subtab", "") == "cd":
                            if not hasattr(self, 'cd_page'): self.cd_page = 1
                            self.cd_page = max(1, self.cd_page - 1)
                        else:
                            if not hasattr(self, 'stock_page'): self.stock_page = 1
                            self.stock_page = max(1, self.stock_page - 1)
                    elif self.current_tab == 11:
                        if not hasattr(self, 'settings_page'): self.settings_page = 1
                        self.settings_page = max(1, self.settings_page - 1)
                    elif self.current_tab == 12:
                        if not hasattr(self, 'intel_page'): self.intel_page = 1
                        self.intel_page = max(1, self.intel_page - 1)
                    else: self.roster_page = max(1, self.roster_page - 1)
                    self.message = ""
                elif cmd.startswith("page ") and (self.current_tab in [2, 3, 4, 5, 8, 11] or (self.current_tab == 10 and getattr(self, "bank_subtab", "") in ["stocks", "cd"]) or (self.current_tab == 12 and getattr(self, "rocket_subview", "ops") == "intel")):
                    try:
                        page = max(1, int(cmd.split()[1]))
                        if self.current_tab == 2: self.pokedex_page = page
                        elif self.current_tab == 4: self.shop_page = page
                        elif self.current_tab == 5: self.expedition_page = page
                        elif self.current_tab == 8: self.mega_page = page
                        elif self.current_tab == 10:
                            if getattr(self, "bank_subtab", "") == "cd":
                                self.cd_page = page
                            else:
                                self.stock_page = page
                        elif self.current_tab == 11:
                            self.settings_page = page
                        elif self.current_tab == 12:
                            self.intel_page = page
                        else: self.roster_page = page
                        self.message = ""
                    except ValueError:
                        self.message = "Usage: page <number>"
                elif cmd.startswith("pagesize ") and self.current_tab == 11:
                    parts = cmd.split()
                    if len(parts) >= 3:
                        target, size_str = parts[1], parts[2]
                        try:
                            val = int(size_str)
                            if target == "dex":
                                self.engine.state["page_size_pokedex"] = val
                                self.message = f"Pokédex page size set to {val}."
                            elif target == "roster":
                                self.engine.state["page_size_roster"] = val
                                self.message = f"Roster page size set to {val}."
                            elif target in ["exp", "expeditions"]:
                                self.engine.state["page_size_expedition"] = val
                                self.message = f"Expeditions page size set to {val}."
                            elif target == "bag":
                                self.engine.state["page_size_bag"] = val
                                self.message = f"Bag page size set to {val}."
                            elif target == "mega":
                                self.engine.state["page_size_mega"] = val
                                self.message = f"Mega Evo page size set to {val}."
                            elif target in ["cd", "deposits"]:
                                self.engine.state["page_size_cd"] = val
                                self.message = f"Term Deposits page size set to {val}."
                            elif target in ["settings", "setting", "set"]:
                                if val < 1:
                                    self.message = "Settings page size must be at least 1."
                                else:
                                    self.engine.state["page_size_settings"] = val
                                    self.message = f"Settings page size set to {val}."
                            else:
                                self.message = "Usage: pagesize <dex|roster|exp|bag|mega|cd|settings> <number>"
                            self.engine.save()
                        except ValueError:
                            self.message = "Invalid size. Usage: pagesize <dex|roster|exp|bag|mega|cd|settings> <number>"
                elif cmd.startswith("billing ") or cmd.startswith("cycle "):
                    parts = cmd.split()
                    if len(parts) >= 2:
                        try:
                            day = int(parts[1])
                            ok, msg = self.engine.set_billing_cycle_day(day)
                            self.message = msg
                            if ok:
                                self.tracker.get_summary(force=True)
                        except ValueError:
                            self.message = "Usage: billing <1-31> (day of month for billing cycle start)"
                    else:
                        self.message = "Usage: billing <1-31>"
                elif cmd in ["tokens init", "token init"]:
                    summary = self.tracker.get_summary(force=True)
                    raw_total = summary.get("raw_total_tokens", summary.get("total_tokens", 0))
                    ok, msg = self.engine.initialize_total_tokens(raw_total)
                    self.message = msg
                    if ok:
                        self.tracker.get_summary(force=True)
                elif cmd in ["pick", "picker"]:
                    self.expedition_picker_mode = True
                    self.current_tab = 5
                    self.message = "Opened Expedition Dispatcher."
                elif cmd == "clear" and self.selected_expedition_targets:
                    self.selected_expedition_targets.clear()
                    self.message = "Cleared all selected companions."
                elif cmd.startswith("feed ") or cmd == "feed":
                    self.handle_feed_command(cmd)
                elif cmd.startswith("sel ") or cmd == "sel":
                    arg = cmd.split(maxsplit=1)[1].strip() if " " in cmd else ""
                    if not arg:
                        self.message = "Usage: sel <row>|#<dex>|egg to switch active companion"
                    elif arg.lower() == "egg":
                        ok, msg = self.engine.select_active_from_dex("egg")
                        self.message = msg
                    else:
                        ok, msg = self.engine.select_active_from_dex(arg)
                        self.message = msg
                elif cmd.startswith("claim"):
                    parts = cmd.split()
                    if self.current_tab == 10 and getattr(self, "bank_subtab", "") == "cd":
                        target = parts[1] if len(parts) >= 2 else "all"
                        ok, msg = self.engine.claim_cd(target)
                        self.message = msg
                    elif self.current_tab == 12:
                        from poketokenbar.tui_tabs.rocket import handle_rocket_command
                        handle_rocket_command(self, cmd)
                    else:
                        ok, msg = self.engine.claim_quest_reward(parts[-1] if len(parts) >= 2 else "all")
                        self.message = msg
                elif cmd.startswith("send"):
                    cmd_body = cmd.split(maxsplit=1)[1] if " " in cmd else ""
                    if not cmd_body:
                        if self.selected_expedition_targets:
                            self.message = f"{len(self.selected_expedition_targets)} companion(s) selected! Type: 'send viridian', 'send mine', etc."
                        else:
                            self.message = "Usage: send <rows|all> <area> (or 'pick' to open picker)"
                    else:
                        clean_body = cmd_body.strip().lower()
                        if self.selected_expedition_targets and self._is_expedition_destination_cmd(clean_body):
                            area = self._resolve_expedition_destination(clean_body)
                            target_list = [str(i) for i in sorted(self.selected_expedition_targets)]
                            ok, msg = self.engine.dispatch_expedition(target_list, area)
                            if ok:
                                self.selected_expedition_targets.clear()
                            self.message = msg
                        else:
                            targets, area = self._parse_send_args(cmd_body)
                            ok, msg = self.engine.dispatch_expedition(targets, area)
                            self.message = msg
                elif cmd.startswith("pass") and self.current_tab == 5:
                    parts = cmd.split()
                    if len(parts) >= 2:
                        ok, msg = self.engine.use_expedition_pass(parts[1])
                        self.message = msg
                    else:
                        self.message = "Usage: pass <idx>"
                elif cmd.startswith("play ") or (self.current_tab == 9 and cmd == "play"):
                    parts = cmd.split()
                    if len(parts) >= 2:
                        game = parts[1].strip()
                        game_map = {
                            "1": "poker",
                            "2": "gacha",
                            "3": "slot",
                            "4": "blackjack",
                            "5": "voltorb",
                            "6": "excavator",
                            "7": "trivia",
                            "8": "derby",
                        }
                        if game in game_map:
                            self.minigame_state = game_map[game]
                            self.message = ""
                        else:
                            self.message = "Game not found! Type 'play <1-8>' (e.g. 'play 1' to 'play 8')."
                    else:
                        self.message = "Usage: play <idx> (e.g. 'play 1' to 'play 8')"
                elif self.current_tab == 9 and getattr(self, "minigame_state", "menu") == "slot" and cmd == "poster":
                    if self.engine.state.get("permanent_black_market", False):
                        ok, msg = self.engine.bribe_grunt_for_black_market()
                        self.minigame_state = "menu"
                        self.black_market_session = True
                        self.current_tab = 4
                        self.shop_view = "black_market"
                        self.message = "📯 Syndicate Black Pass recognized! You click the secret switch behind the poster and enter the Black Market directly!"
                    else:
                        self.minigame_state = "grunt_bribe"
                        self.message = ""
                elif self.current_tab == 9 and getattr(self, "minigame_state", "menu") == "menu" and cmd == "poster":
                    if self.engine.state.get("permanent_black_market", False):
                        ok, msg = self.engine.bribe_grunt_for_black_market()
                        self.minigame_state = "menu"
                        self.black_market_session = True
                        self.current_tab = 4
                        self.shop_view = "black_market"
                        self.message = "📯 Syndicate Black Pass recognized! You click the secret switch behind the poster and enter the Black Market directly!"
                    else:
                        self.message = "There's a suspicious poster near the Token Slots! (Type 'play 3')"
                elif self.current_tab == 9 and getattr(self, "minigame_state", "menu") == "grunt_bribe" and cmd in ["bribe", "enter"]:
                    ok, msg = self.engine.bribe_grunt_for_black_market()
                    if ok:
                        self.minigame_state = "menu"
                        self.black_market_session = True
                        self.current_tab = 4
                        self.shop_view = "black_market"
                    self.message = msg
                elif cmd.startswith("bet"):
                    parts = cmd.split()
                    if len(parts) >= 2:
                        mg_state = getattr(self, "minigame_state", "menu")
                        if mg_state == "poker":
                            ok, msg = self.engine.play_poker_bet(parts[1])
                        elif mg_state == "blackjack":
                            ok, msg = self.engine.play_blackjack_bet(parts[1])
                        elif mg_state == "voltorb":
                            lvl = None
                            if len(parts) >= 3:
                                if parts[2].isdigit():
                                    lvl = int(parts[2])
                                else:
                                    self.message = "Invalid level! Usage: bet <amount> [level 1-8] (e.g. 'bet 500k 3')"
                                    return
                            ok, msg = self.engine.play_voltorb_bet(parts[1], lvl)
                        elif mg_state == "trivia":
                            ok, msg = self.engine.play_trivia_start(parts[1])
                        elif mg_state == "derby":
                            if len(parts) >= 3:
                                ok, msg = self.engine.play_derby_bet(parts[1], parts[2])
                            else:
                                ok, msg = False, "Usage: bet <lane 1-4> <amount> (e.g. 'bet 1 500k')"
                        elif mg_state == "excavator":
                            ok, msg = False, "Excavation has a fixed cost of 500K tokens. Type 'dig' to start!"
                        else:
                            ok, msg = False, "You must open a Game Corner game to bet!"
                        self.message = msg
                    else:
                        if getattr(self, "minigame_state", "menu") == "voltorb":
                            self.message = "Usage: bet <amount> [level 1-8] (e.g. 'bet 500k', 'bet 1m 5')"
                        else:
                            self.message = "Usage: bet <amount> (e.g. 'bet 500k', 'bet 1m')"
                elif cmd.startswith("spin") and getattr(self, "minigame_state", "menu") == "slot":
                    parts = cmd.split()
                    if len(parts) >= 2:
                        ok, msg = self.engine.play_slots(parts[1])
                        if ok:
                            self.animate_slot_spin(self.engine.slots.last_reels)
                        self.message = msg
                    else:
                        self.message = "Usage: spin <amount> (e.g. 'spin 500k')"
                elif cmd in ["check", "raise", "fold", "allin"] and getattr(self, "minigame_state", "menu") == "poker":
                    ok, msg = self.engine.play_poker_hold(cmd)
                    self.message = msg
                elif cmd in ["hit", "stand", "double"] and getattr(self, "minigame_state", "menu") == "blackjack":
                    ok, msg = self.engine.play_blackjack_action(cmd)
                    self.message = msg
                elif cmd.startswith("flip ") and getattr(self, "minigame_state", "menu") == "voltorb":
                    parts = cmd.split()
                    if len(parts) >= 3:
                        ok, msg = self.engine.play_voltorb_flip(parts[1], parts[2])
                        self.message = msg
                    else:
                        self.message = "Usage: flip <row 1-5> <col 1-5> (e.g. 'flip 1 3')"
                elif cmd.startswith("memo ") and getattr(self, "minigame_state", "menu") == "voltorb":
                    parts = cmd.split()
                    if len(parts) >= 3:
                        note = parts[3] if len(parts) >= 4 else ""
                        ok, msg = self.engine.play_voltorb_memo(parts[1], parts[2], note)
                        self.message = msg
                    else:
                        self.message = "Usage: memo <row 1-5> <col 1-5> [note]"
                elif cmd == "cashout" and getattr(self, "minigame_state", "menu") == "voltorb":
                    ok, msg = self.engine.play_voltorb_cashout()
                    self.message = msg
                elif cmd.startswith("pick ") and getattr(self, "minigame_state", "menu") == "excavator":
                    parts = cmd.split()
                    if len(parts) >= 3:
                        ok, msg = self.engine.play_excavator_pick(parts[1], parts[2])
                        self.message = msg
                    else:
                        self.message = "Usage: pick <row 1-6> <col 1-9> (e.g. 'pick 2 4')"
                elif cmd.startswith("hammer ") and getattr(self, "minigame_state", "menu") == "excavator":
                    parts = cmd.split()
                    if len(parts) >= 3:
                        ok, msg = self.engine.play_excavator_hammer(parts[1], parts[2])
                        self.message = msg
                    else:
                        self.message = "Usage: hammer <row 1-6> <col 1-9> (e.g. 'hammer 3 5')"
                elif (cmd == "dig" or cmd.startswith("dig ")) and getattr(self, "minigame_state", "menu") == "excavator":
                    parts = cmd.split()
                    if len(parts) > 1:
                        self.message = "Excavation has a fixed cost of 500K tokens. Type 'dig' to start!"
                    else:
                        ok, msg = self.engine.play_excavator_start()
                        self.message = msg
                elif cmd.startswith("guess ") and getattr(self, "minigame_state", "menu") == "trivia":
                    guess_str = cmd.split(maxsplit=1)[1].strip() if len(cmd.split()) > 1 else ""
                    ok, msg = self.engine.play_trivia_guess(guess_str)
                    self.message = msg
                elif cmd == "hint" and getattr(self, "minigame_state", "menu") == "trivia":
                    ok, msg = self.engine.play_trivia_hint()
                    self.message = msg
                elif cmd == "giveup" and getattr(self, "minigame_state", "menu") == "trivia":
                    ok, msg = self.engine.play_trivia_pass()
                    self.message = msg
                elif cmd == "race" and getattr(self, "minigame_state", "menu") == "derby":
                    if self.engine.derby.game_state == "bet_placed":
                        frames = self.engine.derby.simulate_race()
                        self.animate_derby_race(frames)
                        ok, msg = self.engine.play_derby_race()
                        self.message = msg
                    else:
                        self.message = "Place a bet first! Type 'bet <lane 1-4> <amount>'."
                elif cmd == "start" and getattr(self, "minigame_state", "menu") == "derby":
                    self.message = "Use 'race' to launch the derby race!"
                elif cmd.startswith("pull"):
                    parts = cmd.split()
                    pull_type = parts[1] if len(parts) >= 2 else "1"
                    ok, msg = self.engine.play_gacha(pull_type)
                    self.message = msg
                elif cmd == "card":
                    self.message = self.engine.generate_trainer_card()
                elif cmd == "reset" and self.current_tab == 11:
                    self.pending_reset = True
                    self.message = "⚠️ CONFIRMATION REQUIRED: Type 'RESET ALL' to wipe progress & restart fresh, or anything else to cancel!"
                elif cmd.startswith("rocket init") or cmd.startswith("init rocket") or (self.current_tab == 11 and cmd in ["rocket reset", "reset rocket", "rocket"]):
                    if "--force" in cmd:
                        ok, msg = self.engine.initialize_rocket_process()
                        self.message = f"🚀 {msg}"
                    elif not self.engine.state.get("rocket_story_unlocked", False):
                        ok, msg = self.engine.initialize_rocket_process()
                        self.message = f"🚀 {msg}"
                    else:
                        self.pending_rocket_init = True
                        self.message = "⚠️ CONFIRM: Type 'CONFIRM' to reset Team Rocket back to Op 1, or anything else to cancel!"
                elif cmd.startswith("size") and self.current_tab == 11:
                    parts = cmd.split()
                    if len(parts) == 2 and parts[1].isdigit():
                        new_size = int(parts[1])
                        if 10 <= new_size <= 72:
                            self.engine.state["sprite_size"] = new_size
                            self.engine.save()
                            self.message = f"Sprite resolution set to {new_size} columns!"
                        else:
                            self.message = "Sprite size must be between 10 and 72."
                    else:
                        self.message = "Usage: size <number> (e.g. 'size 30')"
                elif self.current_tab == 10 and cmd == "b":
                    self.bank_subtab = "checking"
                    self.stock_terminal = None
                    self.message = ""
                elif self.current_tab == 10 and cmd == "c":
                    self.bank_subtab = "cd"
                    self.stock_terminal = None
                    self.message = ""
                elif self.current_tab == 10 and cmd == "s" and not getattr(self, "stock_terminal", None):
                    self.bank_subtab = "stocks"
                    self.stock_terminal = None
                    self.message = ""
                elif self.current_tab == 10 and getattr(self, "bank_subtab", "") == "stocks" and getattr(self, "stock_terminal", None) and (cmd.startswith("buy ") or cmd == "buy"):
                    self.handle_stock_terminal_buy(cmd)
                elif self.current_tab == 10 and getattr(self, "bank_subtab", "") == "stocks" and getattr(self, "stock_terminal", None) and (cmd.startswith("sell ") or cmd == "sell"):
                    parts = cmd.split()
                    shares = parts[1] if len(parts) >= 2 else "1"
                    ok, msg = self.engine.divest_corporate(self.stock_terminal, shares)
                    self.message = msg
                elif self.current_tab == 10 and getattr(self, "bank_subtab", "") == "stocks" and (cmd.startswith("stock ") or cmd == "stock"):
                    from poketokenbar.game.models import CORPORATIONS
                    parts = cmd.split()
                    if len(parts) >= 2:
                        target = parts[1]
                        if target.isdigit():
                            c_keys = list(CORPORATIONS.keys())
                            idx = int(target) - 1
                            key = c_keys[idx] if 0 <= idx < len(c_keys) else None
                        else:
                            key = self.engine._resolve_corp_key(target)
                        if key:
                            self.stock_terminal = key
                            self.message = f"Opened {CORPORATIONS[key].ticker} Trade Terminal."
                        else:
                            self.message = f"Unknown stock code '{target}'!"
                    else:
                        self.message = "Usage: stock <idx|code> (e.g. 'stock 1' or 'stock SILPH')"
                elif cmd.startswith("cd "):
                    parts = cmd.split()
                    action = parts[1] if len(parts) > 1 else ""
                    if action == "open" and len(parts) >= 4:
                        try:
                            days = int(parts[3])
                            ok, msg = self.engine.open_cd(parts[2], days)
                        except ValueError:
                            ok, msg = False, "Term days must be 3, 7, or 14. E.g. 'cd open 10m 7'"
                    elif action == "claim":
                        target = parts[2] if len(parts) >= 3 else "all"
                        ok, msg = self.engine.claim_cd(target)
                    elif action == "break" and len(parts) >= 3:
                        ok, msg = self.engine.break_cd(parts[2])
                    elif action == "sort" and len(parts) >= 3:
                        ok, msg = self.engine.set_cd_sort_criteria(parts[2])
                    else:
                        ok, msg = False, "CD Usage: 'cd open <amt> <3|7|14>', 'cd claim <id|all>', 'cd break <id>', or 'cd sort <days|amount|term>'"
                    self.message = msg
                elif self.current_tab == 10 and getattr(self, "bank_subtab", "") == "cd" and cmd.startswith("open "):
                    parts = cmd.split()
                    if len(parts) >= 3:
                        try:
                            days = int(parts[2])
                            ok, msg = self.engine.open_cd(parts[1], days)
                        except ValueError:
                            ok, msg = False, "Term days must be 3, 7, or 14. E.g. 'open 10m 7'"
                    else:
                        ok, msg = False, "Usage: cd open <amt> <3|7|14>"
                    self.message = msg
                elif self.current_tab == 10 and getattr(self, "bank_subtab", "") == "cd" and cmd.startswith("break "):
                    parts = cmd.split()
                    if len(parts) >= 2:
                        ok, msg = self.engine.break_cd(parts[1])
                    else:
                        ok, msg = False, "Usage: cd break <id>"
                    self.message = msg
                elif self.current_tab == 10 and getattr(self, "bank_subtab", "") == "cd" and cmd.startswith("claim "):
                    parts = cmd.split()
                    if len(parts) >= 2:
                        ok, msg = self.engine.claim_cd(parts[1])
                    else:
                        ok, msg = False, "Usage: cd claim <id|all>"
                    self.message = msg
                elif self.current_tab == 10 and getattr(self, "bank_subtab", "") == "cd" and cmd == "claim":
                    ok, msg = self.engine.claim_cd("all")
                    self.message = msg
                elif self.current_tab == 10 and getattr(self, "bank_subtab", "") == "cd" and (cmd.startswith("sort ") or cmd == "sort"):
                    parts = cmd.split()
                    if len(parts) >= 2:
                        ok, msg = self.engine.set_cd_sort_criteria(parts[1])
                    else:
                        ok, msg = False, "Usage: sort <days|amount|term>"
                    self.message = msg
                elif cmd.startswith("invest "):
                    self.handle_invest_command(cmd)
                elif cmd.startswith("divest "):
                    parts = cmd.split()
                    if len(parts) >= 2:
                        shares = parts[2] if len(parts) >= 3 else "1"
                        ok, msg = self.engine.divest_corporate(parts[1], shares)
                    else:
                        ok, msg = False, "Usage: divest <code> <shares|all> (e.g. 'divest SILPH 1')"
                    self.message = msg
                elif cmd == "black":
                    bm = self.engine.get_or_init_black_market()
                    if bm.get("natural_open") or getattr(self, "black_market_session", False):
                        self.current_tab = 4
                        self.shop_view = "black_market"
                        self.message = ""
                    else:
                        self.message = "The back alley door is bolted shut from the inside."
                elif self.current_tab == 4 and getattr(self, "shop_view", "normal") == "black_market" and cmd == "back":
                    if getattr(self, "black_market_session", False):
                        self.black_market_session = False
                        self.current_tab = 9
                        self.minigame_state = "slot"
                        self.shop_view = "normal"
                        self.message = "Returned to the Game Corner slot machines."
                    else:
                        self.shop_view = "normal"
                        self.message = ""
                elif self.current_tab == 6:
                    if cmd.startswith("assemble ") or cmd in ["fight 1", "fight 2", "fight 3", "fight 4", "run", "restart"] or cmd.startswith("swap "):
                        from poketokenbar.tui_tabs.red import handle_red_command
                        handle_red_command(self, cmd)
                    else:
                        self.message = "Invalid command. Type a tab number (1-11), or battle command (assemble, fight, swap, run, restart)."
                elif cmd == "use catalyst" or cmd.startswith("use catalyst"):
                    ok, msg = self.engine.use_rocket_armory_item("catalyst")
                    self.message = msg
                elif cmd == "use mist" or cmd.startswith("use mist") or cmd in ["use spray", "use morale mist"]:
                    ok, msg = self.engine.use_rocket_armory_item("spray")
                    self.message = msg
                elif cmd == "use chrono" or cmd.startswith("use chrono"):
                    ok, msg = self.engine.use_rocket_armory_item("chrono")
                    self.message = msg
                elif self.current_tab == 4 and cmd.startswith("buy"):
                    self.handle_shop_buy(cmd)
                elif self.current_tab == 4 and (cmd.startswith("use") or cmd.startswith("unequip")):
                    self.handle_bag_use(cmd)
                elif self.current_tab == 4 and cmd.startswith("sell"):
                    self.handle_bag_sell(cmd)
                elif self.current_tab == 4 and (cmd == "help" or cmd.startswith("help ") or cmd == "info" or cmd.startswith("info ") or cmd == "desc" or cmd.startswith("desc ")):
                    self.handle_bag_help(cmd)
                elif self.current_tab == 8 and cmd.startswith("use"):
                    parts = cmd.split()
                    if len(parts) > 1:
                        target = parts[1]
                        if hasattr(self, 'mega_stone_map') and target in self.mega_stone_map:
                            active = self.engine.active_mon
                            if active and active.is_mega:
                                ok, msg = False, "Already Mega Evolved! Type 'revert' to return to standard form."
                            else:
                                ok, msg = self.engine.toggle_mega_evolution(self.mega_stone_map[target])
                        else:
                            ok, msg = False, "Invalid stone number!"
                    else:
                        ok, msg = False, "Usage: use <number>"
                    self.message = msg
                elif self.current_tab == 8 and cmd == "revert":
                    active = self.engine.active_mon
                    if active and active.is_mega:
                        ok, msg = self.engine.toggle_mega_evolution(force_revert=True)
                    elif active:
                        ok, msg = False, "Companion is not Mega Evolved!"
                    else:
                        ok, msg = False, "No active companion to revert!"
                    self.message = msg
                elif cmd.startswith("deposit") or cmd.startswith("withdraw") or cmd.startswith("loan") or cmd.startswith("payoff"):
                    parts = cmd.split()
                    if len(parts) >= 2:
                        action = parts[0]
                        amount_str = parts[1]
                        ok, msg = self.engine.handle_bank_transaction(action, amount_str)
                        self.message = msg
                    else:
                        self.message = "Usage: deposit, withdraw, loan, or payoff <amount>"
                elif self.engine.state.get("pending_authority_delivery") and cmd in ["keep", "dismiss"]:
                    ok, msg = self.engine.handle_authority_delivery(cmd)
                    self.message = msg
                elif self.current_tab == 12:
                    from poketokenbar.tui_tabs.rocket import handle_rocket_command
                    handle_rocket_command(self, cmd)
            except KeyboardInterrupt:
                print("\nExiting PokeTokenBar. Keep coding! 🐾")
                break

    @staticmethod
    def _parse_send_args(arg_str: str) -> Tuple[str, str]:
        """Parses user input for the send command into (targets, area)."""
        arg_str = arg_str.strip()
        if not arg_str:
            return "", "viridian"

        tokens = arg_str.split()
        if len(tokens) == 1:
            return tokens[0], "viridian"

        known_areas = {
            "viridian forest", "cerulean cave", "mt silver", "mt. silver", "mount silver",
            "spear pillar", "spear pillar (deep)", "evolution mine",
            "viridian", "cerulean", "silver", "spear", "mine", "deep", "evolution"
        }

        # Check for 2-word area at tail (e.g. "viridian forest", "mt silver", "cerulean cave")
        if len(tokens) >= 3:
            tail_2 = f"{tokens[-2]} {tokens[-1]}".lower().strip(".,")
            if tail_2 in known_areas:
                return " ".join(tokens[:-2]), tail_2

        # Check for 1-word area at tail (e.g. "viridian", "mine", "silver")
        tail_1 = tokens[-1].lower().strip(".,")
        if tail_1 in known_areas:
            return " ".join(tokens[:-1]), tail_1

        # If commas exist, comma-separated targets were provided without trailing area
        if "," in arg_str:
            return arg_str, "viridian"

        # Check if tail token looks like a target (digit, #id, range, or 'all'):
        is_target_token = (
            tokens[-1].isdigit()
            or tokens[-1].startswith("#")
            or ("-" in tokens[-1] and all(p.isdigit() for p in tokens[-1].split("-") if p))
            or (".." in tokens[-1] and all(p.isdigit() for p in tokens[-1].split("..") if p))
            or tokens[-1].lower() == "all"
        )
        if is_target_token:
            return arg_str, "viridian"

        # Otherwise, treat the tail token as destination area (e.g. typos like 'ine')
        return " ".join(tokens[:-1]), tokens[-1]

    @staticmethod
    def _is_expedition_destination_cmd(cmd: str) -> bool:
        cmd = cmd.strip().lower()
        if cmd.startswith("to ") or cmd.startswith("go ") or cmd.startswith("send "):
            return True
        known_areas = {
            "viridian", "viridian forest", "mine", "evolution mine", "evolution",
            "cerulean", "cerulean cave", "silver", "mt silver", "mt. silver", "mount silver",
            "spear", "spear pillar", "deep"
        }
        return cmd in known_areas

    @staticmethod
    def _resolve_expedition_destination(cmd: str) -> str:
        cmd = cmd.strip().lower()
        if cmd.startswith("to "):
            cmd = cmd[3:].strip()
        elif cmd.startswith("go "):
            cmd = cmd[3:].strip()
        elif cmd.startswith("send "):
            cmd = cmd[5:].strip()

        dest_map = {
            "1": "viridian", "2": "mine", "3": "cerulean", "4": "silver", "5": "spear",
            "viridian": "viridian", "viridian forest": "viridian",
            "mine": "mine", "evolution mine": "mine", "evolution": "mine",
            "cerulean": "cerulean", "cerulean cave": "cerulean",
            "silver": "silver", "mt silver": "silver", "mt. silver": "silver", "mount silver": "silver",
            "spear": "spear", "spear pillar": "spear", "deep": "spear"
        }
        return dest_map.get(cmd, cmd)

    def _parse_indices_string(self, raw_str: str) -> List[int]:
        """Parses a string of indices, ranges, species IDs, or 'all' into 1-based roster indices."""
        raw_str = raw_str.strip()
        if not raw_str:
            return []
        
        roster = [d for d in self.engine.state.get("dex", []) if d.get("status") != "evolved"]
        if raw_str.lower() == "all":
            return list(range(1, len(roster) + 1))

        norm = raw_str.replace(",", " ")
        tokens: List[int] = []
        for part in norm.split():
            part = part.strip()
            if not part:
                continue
            if part.startswith("#"):
                sp_id_str = part[1:]
                for idx, d in enumerate(roster, 1):
                    if str(d.get("species_id", d.get("base_id"))) == sp_id_str:
                        tokens.append(idx)
                        break
                continue
            if "-" in part:
                sub = part.split("-")
                if len(sub) == 2 and sub[0].isdigit() and sub[1].isdigit():
                    tokens.extend(list(range(int(sub[0]), int(sub[1]) + 1)))
                    continue
            if ".." in part:
                sub = part.split("..")
                if len(sub) == 2 and sub[0].isdigit() and sub[1].isdigit():
                    tokens.extend(list(range(int(sub[0]), int(sub[1]) + 1)))
                    continue
            if part.isdigit():
                tokens.append(int(part))
        return tokens

    def _toggle_selection_indices(self, indices: List[int]):
        roster = [d for d in self.engine.state.get("dex", []) if d.get("status") != "evolved"]
        expeditions = self.engine.state.get("expeditions", [])
        slot_limit = self.engine.state.get("expedition_slots", 10)
        avail_slots = max(0, slot_limit - len(expeditions))
        deployed_ids = {e.get("sp_id") for e in expeditions if "sp_id" in e}
        red_team_ids = self.engine.get_red_battle_active_pokemon_ids()

        toggled_on = []
        toggled_off = []
        skipped_reasons = []

        for idx in indices:
            if not (1 <= idx <= len(roster)):
                skipped_reasons.append(f"#{idx} out of range")
                continue
            entry = roster[idx - 1]
            sp_id = entry.get("species_id", entry.get("base_id"))
            sp_name = self.engine.api.get_species_name(sp_id)

            if idx in self.selected_expedition_targets:
                self.selected_expedition_targets.remove(idx)
                toggled_off.append(sp_name)
            else:
                if sp_id in deployed_ids:
                    skipped_reasons.append(f"{sp_name} (deployed)")
                    continue
                if sp_id in red_team_ids:
                    skipped_reasons.append(f"{sp_name} (in Red battle)")
                    continue
                mon_data = entry.get("mon_state", {})
                hap = mon_data.get("happiness", 100) if isinstance(mon_data, dict) else 100
                if hap <= 0:
                    skipped_reasons.append(f"{sp_name} (exhausted)")
                    continue
                if len(self.selected_expedition_targets) >= avail_slots:
                    skipped_reasons.append(f"slots full (max {avail_slots})")
                    break
                self.selected_expedition_targets.add(idx)
                toggled_on.append(sp_name)

        parts = []
        if toggled_on:
            parts.append(f"Selected: {', '.join(toggled_on)}")
        if toggled_off:
            parts.append(f"Deselected: {', '.join(toggled_off)}")
        if skipped_reasons:
            parts.append(f"Skipped: {', '.join(skipped_reasons)}")
        
        tot = len(self.selected_expedition_targets)
        status_tail = f" [{tot}/{avail_slots} selected. Type 'send <area>' or destination to launch!]" if tot > 0 else " [0 selected]"
        self.message = " | ".join(parts) + status_tail if parts else f"No changes made.{status_tail}"

    def render_header(self, summary: dict):
        sys.stdout.write(f"{HEADER}{'='*72}{RESET}\n")
        sys.stdout.write(f"{HEADER} ⚡ POKETOKENBAR — AI Token Pokémon Companion (Linux CLI Edition) 🐾 {RESET}\n")
        sys.stdout.write(f"{HEADER}{'='*72}{RESET}\n")

    def render_tabs(self):
        t1 = f"{BOLD}{CYAN}[1] Companion{RESET}" if self.current_tab == 1 else "[1] Companion"
        t2 = f"{BOLD}{CYAN}[2] Pokédex{RESET}" if self.current_tab == 2 else "[2] Pokédex"
        t3 = f"{BOLD}{CYAN}[3] Roster{RESET}" if self.current_tab == 3 else "[3] Roster"
        t4 = f"{BOLD}{CYAN}[4] Shop & Bag{RESET}" if self.current_tab == 4 else "[4] Shop & Bag"
        t5 = f"{BOLD}{CYAN}[5] Expeditions{RESET}" if self.current_tab == 5 else "[5] Expeditions"
        t6 = f"{BOLD}{CYAN}[6] Battles{RESET}" if self.current_tab == 6 else "[6] Battles"
        t7 = f"{BOLD}{CYAN}[7] Quests{RESET}" if self.current_tab == 7 else "[7] Quests"
        t8 = f"{BOLD}{CYAN}[8] Mega-Evo{RESET}" if self.current_tab == 8 else "[8] Mega-Evo"
        t9 = f"{BOLD}{CYAN}[9] Game Corner{RESET}" if self.current_tab == 9 else "[9] Game Corner"
        t10 = f"{BOLD}{CYAN}[10] Bank{RESET}" if self.current_tab == 10 else "[10] Bank"
        t11 = f"{BOLD}{CYAN}[11] Settings{RESET}" if self.current_tab == 11 else "[11] Settings"
        
        sys.stdout.write(f"  {t1}   {t2}     {t3}      {t4}\n")
        sys.stdout.write(f"  {t5} {t6}     {t7}      {t8}\n")
        if self.engine.state.get("rocket_story_unlocked", False):
            if self.engine.state.get("rocket_alliance_accepted", False):
                t12 = f"{BOLD}{RED}[12] Rocket HQ{RESET}" if self.current_tab == 12 else "[12] Rocket HQ"
            else:
                t12 = f"{BOLD}{YELLOW}[12] Secure Comm{RESET}" if self.current_tab == 12 else "[12] Secure Comm"
            sys.stdout.write(f"  {t9} {t10}       {t11}   {t12}\n")
        else:
            sys.stdout.write(f"  {t9} {t10}       {t11}\n")
        sys.stdout.write("-" * 72 + "\n")

    def render_companion_tab(self, summary: dict):
        from poketokenbar.tui_tabs.companion import render
        render(self, summary)

    def render_pokedex_tab(self):
        from poketokenbar.tui_tabs.pokedex import render
        render(self)

    def render_roster_tab(self):
        from poketokenbar.tui_tabs.roster import render
        render(self)

    def render_shop_tab(self):
        from poketokenbar.tui_tabs.shop import render_shop_tab
        render_shop_tab(self)

    def handle_shop_buy(self, cmd: str):
        from poketokenbar.tui_tabs.shop import handle_shop_buy
        handle_shop_buy(self, cmd)

    def execute_pending_buy(self, plan: dict) -> Tuple[bool, str]:
        p_type = plan.get("type")
        if p_type == "shop_item":
            return self.engine.buy_item(plan["item_kind"], plan["qty"])
        elif p_type == "black_market":
            return self.engine.buy_black_market_deal(plan["deal_id"], plan["qty"])
        elif p_type == "stock":
            return self.engine.invest_corporate(plan["corp_key"], str(plan["shares"]))
        return False, "Unknown purchase plan."

    def handle_stock_terminal_buy(self, cmd: str):
        from poketokenbar.game.models import CORPORATIONS
        parts = cmd.split()
        bypass_confirm = any(p.lower() in ["-y", "--yes", "confirm"] for p in parts)
        clean_parts = [p for p in parts if p.lower() not in ["-y", "--yes", "confirm"]]
        shares_str = clean_parts[1] if len(clean_parts) >= 2 else "1"
        corp_key = getattr(self, "stock_terminal", None)
        if not corp_key or corp_key not in CORPORATIONS:
            ok, msg = self.engine.invest_corporate(corp_key, shares_str)
            self.message = msg
            return

        corp = CORPORATIONS[corp_key]
        sm = self.engine.get_or_init_stock_market()
        price = sm["prices"].get(corp_key, corp.share_price)

        if shares_str.lower() == "all":
            shares = self.engine.available_tokens // price
        else:
            try:
                shares = int(shares_str)
            except ValueError:
                shares = 1

        if shares > 5 and not bypass_confirm:
            total_cost = shares * price
            ticker = corp.ticker
            prompt = f"📈 Buy {shares} shares of {ticker} for {format_tokens(total_cost)} tokens? Type 'confirm' (or 'y')"
            if len(prompt) > 72:
                prompt = f"📈 Buy {shares} {ticker} shares for {format_tokens(total_cost)}? Type 'y'"
            if len(prompt) > 72:
                prompt = prompt[:69] + "..."
            self.pending_buy = {
                "type": "stock",
                "corp_key": corp_key,
                "shares": shares_str,
                "cost": total_cost,
                "prompt": prompt,
            }
            self.message = prompt
        else:
            ok, msg = self.engine.invest_corporate(self.stock_terminal, shares_str)
            self.message = msg

    def handle_invest_command(self, cmd: str):
        from poketokenbar.game.models import CORPORATIONS
        parts = cmd.split()
        bypass_confirm = any(p.lower() in ["-y", "--yes", "confirm"] for p in parts)
        clean_parts = [p for p in parts if p.lower() not in ["-y", "--yes", "confirm"]]
        if len(clean_parts) < 2:
            self.message = "Usage: invest <code> <shares|all> (e.g. 'invest SILPH 2')"
            return

        code = clean_parts[1]
        shares_str = clean_parts[2] if len(clean_parts) >= 3 else "1"
        corp_key = self.engine._resolve_corp_key(code)
        if not corp_key or corp_key not in CORPORATIONS:
            ok, msg = self.engine.invest_corporate(code, shares_str)
            self.message = msg
            return

        corp = CORPORATIONS[corp_key]
        sm = self.engine.get_or_init_stock_market()
        price = sm["prices"].get(corp_key, corp.share_price)

        if shares_str.lower() == "all":
            shares = self.engine.available_tokens // price
        else:
            try:
                shares = int(shares_str)
            except ValueError:
                shares = 1

        if shares > 5 and not bypass_confirm:
            total_cost = shares * price
            ticker = corp.ticker
            prompt = f"📈 Buy {shares} shares of {ticker} for {format_tokens(total_cost)} tokens? Type 'confirm' (or 'y')"
            if len(prompt) > 72:
                prompt = f"📈 Buy {shares} {ticker} shares for {format_tokens(total_cost)}? Type 'y'"
            if len(prompt) > 72:
                prompt = prompt[:69] + "..."
            self.pending_buy = {
                "type": "stock",
                "corp_key": corp_key,
                "shares": shares_str,
                "cost": total_cost,
                "prompt": prompt,
            }
            self.message = prompt
        else:
            ok, msg = self.engine.invest_corporate(code, shares_str)
            self.message = msg

    def handle_bag_use(self, cmd: str):
        from poketokenbar.tui_tabs.shop import handle_bag_use
        handle_bag_use(self, cmd)

    def handle_bag_sell(self, cmd: str):
        from poketokenbar.tui_tabs.shop import handle_bag_sell
        handle_bag_sell(self, cmd)

    def handle_bag_help(self, cmd: str):
        from poketokenbar.tui_tabs.shop import handle_bag_help
        handle_bag_help(self, cmd)

    def handle_feed_command(self, cmd: str):
        raw_parts = cmd.split()
        bypass_confirm = False
        parts = []
        for p in raw_parts:
            if p.lower() in ["-y", "--yes", "confirm"]:
                bypass_confirm = True
            else:
                parts.append(p)

        target = None
        qty = None

        if len(parts) == 1:
            if getattr(self, "selected_expedition_targets", None):
                target = [f"#{self.engine.state.get('dex', [])[i-1].get('species_id')}" for i in sorted(self.selected_expedition_targets) if 1 <= i <= len(self.engine.state.get('dex', []))]
            else:
                target = None
        elif len(parts) == 2:
            arg = parts[1].strip()
            # If on Tab 1 (Companion) and a number is provided, treat as qty for active mon
            if self.current_tab == 1 and arg.isdigit() and int(arg) > 0 and self.engine.active_mon:
                target = "active"
                qty = int(arg)
            else:
                target = arg
        else:
            if parts[1] in ["<=", "<", "=", "=="] and len(parts) >= 3:
                target = parts[1] + parts[2]
                if len(parts) >= 4:
                    try:
                        qty = int(parts[3].strip())
                    except ValueError:
                        self.message = "Usage: feed <#[id]|<=[pct]|<[pct]|[pct]|0> [qty] (e.g. 'feed <=70 2', 'feed =70', 'feed 0', 'feed #25 4')"
                        return
            else:
                target = parts[1].strip()
                try:
                    qty = int(parts[2].strip())
                except ValueError:
                    self.message = "Usage: feed <#[id]|<=[pct]|<[pct]|[pct]|0> [qty] (e.g. 'feed <=70 2', 'feed =70', 'feed 0', 'feed #25 4')"
                    return

        # If feeding active companion explicitly or on Tab 1, execute immediately without confirmation
        if (target in ["active", "current"] or (target is None and self.current_tab == 1)) and self.engine.active_mon:
            bypass_confirm = True

        plan = self.engine.get_feed_plan(target=target, qty=qty)
        if not plan.get("ok"):
            self.message = plan.get("error", "Could not feed Pokémon.")
            return

        if bypass_confirm:
            ok, msg = self.engine.execute_feed_plan(plan)
            self.message = msg
        else:
            self.pending_feed = plan
            self.message = plan.get("prompt", "Confirm feeding?")

    def render_quests_tab(self):
        from poketokenbar.tui_tabs.quests import render_quests_tab
        render_quests_tab(self)

    def render_expeditions_tab(self):
        from poketokenbar.tui_tabs.expeditions import render_expeditions_tab, render_expedition_picker
        if getattr(self, "expedition_picker_mode", False):
            render_expedition_picker(self)
        else:
            render_expeditions_tab(self)

    def render_battles_tab(self):
        from poketokenbar.tui_tabs.battles import render_battles_tab
        render_battles_tab(self)

    def render_mega_evo_tab(self):
        from poketokenbar.tui_tabs.mega_evo import render_mega_evo_tab
        render_mega_evo_tab(self)

    def render_game_corner_tab(self):
        from poketokenbar.tui_tabs.game_corner import render_game_corner_tab
        render_game_corner_tab(self)

    def render_game_corner_menu(self):
        from poketokenbar.tui_tabs.game_corner import render_game_corner_menu
        render_game_corner_menu(self)
        
    def render_slot_tab(self):
        from poketokenbar.tui_tabs.game_corner import render_slot_tab
        render_slot_tab(self)
        
    def render_blackjack_tab(self):
        from poketokenbar.tui_tabs.game_corner import render_blackjack_tab
        render_blackjack_tab(self)

    def render_poker_tab(self):
        from poketokenbar.tui_tabs.game_corner import render_poker_tab
        render_poker_tab(self)

    def render_gacha_tab(self):
        from poketokenbar.tui_tabs.game_corner import render_gacha_tab
        render_gacha_tab(self)

    def render_bank_tab(self):
        from poketokenbar.tui_tabs.bank import render_bank_tab
        render_bank_tab(self)

    def render_settings_tab(self):
        from poketokenbar.tui_tabs.settings import render_settings_tab
        render_settings_tab(self)

    def render_footer(self):
        alerts = self.engine.state.get("unread_alerts", [])
        if alerts:
            alert_str = "\n".join(alerts)
            if self.message:
                self.message += "\n" + alert_str
            else:
                self.message = alert_str
            self.engine.state["unread_alerts"] = []
            self.engine.save()

        sys.stdout.write("-" * 72 + "\n")
        if self.message and not getattr(self, 'slot_animating', False):
            for line in self.message.split("\n"):
                if line.lstrip().startswith("➔"):
                    sys.stdout.write(f"  {GREEN}  {line.lstrip()}{RESET}\n")
                elif line.startswith("  "):
                    sys.stdout.write(f"  {GREEN}{line}{RESET}\n")
                else:
                    sys.stdout.write(f"  {GREEN}➔ {line}{RESET}\n")
            self.message = ""

    def animate_slot_spin(self, final_reels):
        import io
        self.slot_animating = True
        symbols = ["🍒", "🍋", "🍇", "🍉", "🔔", "💎", "⭐"]
        spins = 20
        
        # Cache summary to prevent heavy disk I/O on every frame
        cached_summary = self.tracker.get_summary()
        
        for i in range(spins):
            grid = []
            for r in range(3):
                col1 = final_reels[r][0] if i > spins * 0.4 else random.choice(symbols)
                col2 = final_reels[r][1] if i > spins * 0.7 else random.choice(symbols)
                col3 = final_reels[r][2] if i > spins * 0.9 else random.choice(symbols)
                grid.append([col1, col2, col3])
                
            self.slot_current_reels = grid
            
            # Intercept standard output to buffer the frame
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            
            self.render_header(cached_summary)
            self.render_tabs()
            self.render_slot_tab()
            self.render_footer()
            
            sys.stdout = old_stdout
            # Inject line-clears (\033[K) to prevent ghost artifacts from previous frames
            frame_str = buf.getvalue().replace("\n", "\033[K\n")
            
            # Write entire frame instantly
            sys.stdout.write("\033[H" + frame_str + "\033[J")
            sys.stdout.flush()
            
            delay = 0.05 + (i / spins) * 0.1
            time.sleep(delay)
            
        self.slot_animating = False

    def animate_derby_race(self, frames):
        import io
        from poketokenbar.tui_tabs.game_corner import render_derby_race_screen

        # 1. Countdown Sequence at Starting Gate
        countdown_steps = [
            ("3", ["🚦 Drivers take your marks! Starting in 3..."], 0.75),
            ("2", ["🚦 Engines revving! Racers tense in the gates... 2..."], 0.75),
            ("1", ["🚦 Flag raised high... 1..."], 0.75),
            ("GO!", ["🚩 GONG! AND THEY'RE OFF! Racers burst from the gates!"], 0.85),
        ]
        start_frame = frames[0] if frames else {"positions": {1: 0, 2: 0, 3: 0, 4: 0}, "events": []}
        for stage, evts, delay in countdown_steps:
            c_frame = {"positions": start_frame["positions"], "events": evts}
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            render_derby_race_screen(self, c_frame, 0, len(frames), countdown_stage=stage)
            sys.stdout = old_stdout
            frame_str = buf.getvalue().replace("\n", "\033[K\n")
            sys.stdout.write("\033[H" + frame_str + "\033[J")
            sys.stdout.flush()
            time.sleep(delay)

        # 2. Race Turn Animation
        total_frames = len(frames)
        for idx, frame in enumerate(frames):
            for r in self.engine.derby.racers:
                r.position = frame["positions"].get(r.lane, r.position)

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf

            render_derby_race_screen(self, frame, idx, total_frames)

            sys.stdout = old_stdout
            frame_str = buf.getvalue().replace("\n", "\033[K\n")
            sys.stdout.write("\033[H" + frame_str + "\033[J")
            sys.stdout.flush()

            if idx == total_frames - 1:
                time.sleep(1.50)
            else:
                time.sleep(0.70)

def main():
    tui = PokeTokenBarTUI()
    tui.run()

if __name__ == "__main__":
    main()
