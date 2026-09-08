import os
import sys
import time
import random
import datetime
import math
from typing import Optional, Tuple, Set, List

from poketokenbar.tracker.manager import UsageManager
from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.models import ItemKind, Rarity, PokemonBalance
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
        self.pokedex_page = 1
        self.roster_page = 1
        self.stock_page = 1
        self.stock_terminal = None
        self.selected_expedition_targets: Set[int] = set()
        self.expedition_picker_mode: bool = False
        self.picker_page: int = 1

    def clear_screen(self):
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()

    def run(self):
        """Main interactive event loop."""
        # Initial refresh
        summary = self.tracker.get_summary()
        self.engine.process_usage(summary["total_tokens"], summary.get("active_days"))

        while True:
            # Refresh usage and process growth on each frame
            summary = self.tracker.get_summary()
            self.engine.process_usage(summary["total_tokens"], summary.get("active_days"))

            # Check for evolution or graduation alerts to show celebration screen
            alerts = self.engine.state.get("unread_alerts", [])
            milestone_alerts = [a for a in alerts if "Evolution!" in a or "Graduation!" in a]
            if milestone_alerts:
                m_alert = milestone_alerts[0]
                alerts.remove(m_alert)
                self.engine.state["unread_alerts"] = alerts
                self.engine.save()

                self.clear_screen()
                is_grad = "Graduation!" in m_alert
                banner_title = "🎓 CONGRATULATIONS! YOUR COMPANION GRADUATED! 🎓" if is_grad else "✨ WHAT? YOUR COMPANION IS EVOLVING! ✨"

                sys.stdout.write(f"\n{HEADER}{'='*72}{RESET}\n")
                sys.stdout.write(f"  {BOLD}{YELLOW}{banner_title}{RESET}\n")
                sys.stdout.write(f"{HEADER}{'='*72}{RESET}\n\n")

                active = self.engine.active_mon
                if active:
                    sp_id = active.current_id
                    sprite_path = self.engine.api.download_sprite(sp_id, is_shiny=active.is_shiny)
                    if sprite_path:
                        sprite_size = self.engine.state.get("sprite_size", 30)
                        ansi = SpriteRenderer.render_png_to_ansi(sprite_path, max_cols=sprite_size, center_width=72)
                        sys.stdout.write(ansi + "\n\n")

                sys.stdout.write(f"  {BOLD}{GREEN}{m_alert}{RESET}\n\n")
                if active:
                    stage_str = f"Form {active.stage_index+1}/{active.total_forms}"
                    rarity_str = active.rarity.value.upper()
                    nature_str = active.nature.display_name if active.nature else "Unknown"
                    sys.stdout.write(f"  Stage: {stage_str}  |  Rarity: {YELLOW}{rarity_str}{RESET}  |  Nature: {CYAN}{nature_str}{RESET}\n\n")

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

            self.render_footer()

            sys.stdout.write(f"\n{BOLD}Select tab (1-11), command, r=Refresh, q=Quit: {RESET}")
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
                elif getattr(self, "expedition_picker_mode", False):
                    # In Interactive Expedition Picker mode
                    if cmd == "back":
                        self.expedition_picker_mode = False
                        self.message = "Exited Expedition Dispatcher."
                    elif cmd == "n":
                        dex = self.engine.state.get("dex", [])
                        roster = [d for d in dex if d.get("status") != "evolved"]
                        page_size = 8
                        total_pages = max(1, math.ceil(len(roster) / page_size))
                        if getattr(self, "picker_page", 1) < total_pages:
                            self.picker_page = getattr(self, "picker_page", 1) + 1
                        else:
                            self.message = f"Already on the last page ({total_pages})."
                    elif cmd == "p":
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
                elif self.current_tab == 9 and getattr(self, "minigame_state", "menu") != "menu" and cmd == "back":
                    self.minigame_state = "menu"
                    self.message = "Returned to Game Corner menu."
                elif cmd == "250220":
                    self.engine.state["spent_tokens"] = self.engine.state.get("spent_tokens", 0) - 50_000_000
                    self.engine.save()
                    self.message = "🎉 EASTER EGG UNLOCKED! Granted 50.0M Tokens! 🎉"
                elif self.current_tab == 10 and getattr(self, "bank_subtab", "") == "stocks" and not getattr(self, "stock_terminal", None) and cmd in ["1", "2", "3", "4", "5"]:
                    from poketokenbar.game.models import CORPORATIONS
                    c_keys = list(CORPORATIONS.keys())
                    idx = int(cmd) - 1
                    if 0 <= idx < len(c_keys):
                        self.stock_terminal = c_keys[idx]
                        self.message = f"Opened {CORPORATIONS[self.stock_terminal].ticker} Trade Terminal."
                elif cmd == "1":
                    self.expedition_picker_mode = False
                    self.current_tab = 1
                    self.message = ""
                elif cmd == "2":
                    self.expedition_picker_mode = False
                    self.current_tab = 2
                    self.message = ""
                elif cmd == "3":
                    self.expedition_picker_mode = False
                    self.current_tab = 3
                    self.message = ""
                elif cmd == "4":
                    self.expedition_picker_mode = False
                    self.current_tab = 4
                    self.message = ""
                elif cmd == "5":
                    self.expedition_picker_mode = False
                    self.current_tab = 5
                    self.message = ""
                elif cmd == "6":
                    self.expedition_picker_mode = False
                    self.current_tab = 6
                    self.message = ""
                elif cmd == "7":
                    self.expedition_picker_mode = False
                    self.current_tab = 7
                    self.message = ""
                elif cmd == "8":
                    self.expedition_picker_mode = False
                    self.current_tab = 8
                    self.message = ""
                elif cmd == "9":
                    self.expedition_picker_mode = False
                    self.current_tab = 9
                    self.message = ""
                elif cmd == "10":
                    self.expedition_picker_mode = False
                    self.current_tab = 10
                    self.message = ""
                elif cmd == "11":
                    self.expedition_picker_mode = False
                    self.current_tab = 11
                    self.message = ""
                elif cmd == "r":
                    summary = self.tracker.get_summary(force=True)
                    self.engine.process_usage(summary["total_tokens"], summary.get("active_days"))
                    self.message = f"Refreshed usage logs! Total indexed: {format_tokens(summary['total_tokens'])} tokens."
                elif cmd == "n" and (self.current_tab in [2, 3, 4, 5, 8] or (self.current_tab == 10 and getattr(self, "bank_subtab", "") == "stocks")):
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
                        if not hasattr(self, 'stock_page'): self.stock_page = 1
                        self.stock_page += 1
                    else: self.roster_page += 1
                    self.message = ""
                elif cmd == "p" and (self.current_tab in [2, 3, 4, 5, 8] or (self.current_tab == 10 and getattr(self, "bank_subtab", "") == "stocks")):
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
                        if not hasattr(self, 'stock_page'): self.stock_page = 1
                        self.stock_page = max(1, self.stock_page - 1)
                    else: self.roster_page = max(1, self.roster_page - 1)
                    self.message = ""
                elif cmd.startswith("page ") and (self.current_tab in [2, 3, 4, 5, 8] or (self.current_tab == 10 and getattr(self, "bank_subtab", "") == "stocks")):
                    try:
                        page = max(1, int(cmd.split()[1]))
                        if self.current_tab == 2: self.pokedex_page = page
                        elif self.current_tab == 4: self.shop_page = page
                        elif self.current_tab == 5: self.expedition_page = page
                        elif self.current_tab == 8: self.mega_page = page
                        elif self.current_tab == 10: self.stock_page = page
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
                            else:
                                self.message = "Usage: pagesize <dex|roster|exp|bag|mega> <number>"
                            self.engine.save()
                        except ValueError:
                            self.message = "Invalid size. Usage: pagesize <dex|roster|exp|bag|mega> <number>"
                elif cmd in ["pick", "picker"]:
                    self.expedition_picker_mode = True
                    self.current_tab = 5
                    self.message = "Opened Expedition Dispatcher."
                elif cmd == "clear" and self.selected_expedition_targets:
                    self.selected_expedition_targets.clear()
                    self.message = "Cleared all selected companions."
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
                elif cmd.startswith("play "):
                    parts = cmd.split()
                    if len(parts) >= 2:
                        game = parts[1]
                        if game == "1":
                            self.minigame_state = "poker"
                            self.message = ""
                        elif game == "2":
                            self.minigame_state = "gacha"
                            self.message = ""
                        elif game == "3":
                            self.minigame_state = "slot"
                            self.message = ""
                        elif game == "4":
                            self.minigame_state = "blackjack"
                            self.message = ""
                        else:
                            self.message = "Game not found! Type 'play 1' for Poker, 'play 2' for Gacha, etc."
                    else:
                        self.message = "Usage: play <idx> (e.g. 'play 1')"
                elif cmd in ["leave", "back", "quit game", "exit game", "quit", "exit"] and self.current_tab == 9 and getattr(self, "minigame_state", "menu") != "menu":
                    self.minigame_state = "menu"
                    self.message = "Returned to Game Corner menu."
                elif cmd.startswith("bet"):
                    parts = cmd.split()
                    if len(parts) >= 2:
                        if getattr(self, "minigame_state", "menu") == "poker":
                            ok, msg = self.engine.play_poker_bet(parts[1])
                        elif getattr(self, "minigame_state", "menu") == "blackjack":
                            ok, msg = self.engine.play_blackjack_bet(parts[1])
                        else:
                            ok, msg = False, "You must open Poker or Blackjack to bet."
                        self.message = msg
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
                    parts = cmd.split()
                    shares = parts[1] if len(parts) >= 2 else "1"
                    ok, msg = self.engine.invest_corporate(self.stock_terminal, shares)
                    self.message = msg
                elif self.current_tab == 10 and getattr(self, "bank_subtab", "") == "stocks" and getattr(self, "stock_terminal", None) and (cmd.startswith("sell ") or cmd == "sell"):
                    parts = cmd.split()
                    shares = parts[1] if len(parts) >= 2 else "1"
                    ok, msg = self.engine.divest_corporate(self.stock_terminal, shares)
                    self.message = msg
                elif self.current_tab == 10 and getattr(self, "bank_subtab", "") == "stocks" and (cmd.startswith("stock ") or cmd.startswith("view ")):
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
                        self.stock_terminal = None
                        self.message = ""
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
                    else:
                        ok, msg = False, "CD Usage: 'cd open <amt> <3|7|14>', 'cd claim <id|all>', or 'cd break <id>'"
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
                elif cmd.startswith("invest "):
                    parts = cmd.split()
                    if len(parts) >= 2:
                        shares = parts[2] if len(parts) >= 3 else "1"
                        ok, msg = self.engine.invest_corporate(parts[1], shares)
                    else:
                        ok, msg = False, "Usage: invest <code> <shares|all> (e.g. 'invest SILPH 2')"
                    self.message = msg
                elif cmd.startswith("divest "):
                    parts = cmd.split()
                    if len(parts) >= 2:
                        shares = parts[2] if len(parts) >= 3 else "1"
                        ok, msg = self.engine.divest_corporate(parts[1], shares)
                    else:
                        ok, msg = False, "Usage: divest <code> <shares|all> (e.g. 'divest SILPH 1')"
                    self.message = msg
                elif cmd == "black":
                    self.current_tab = 4
                    self.shop_view = "black_market"
                    self.message = ""
                elif self.current_tab == 4 and getattr(self, "shop_view", "normal") == "black_market" and cmd == "back":
                    self.shop_view = "normal"
                    self.message = ""
                elif self.current_tab == 6:
                    if cmd.startswith("assemble ") or cmd in ["fight 1", "fight 2", "fight 3", "fight 4", "run", "restart"] or cmd.startswith("swap "):
                        from poketokenbar.tui_tabs.red import handle_red_command
                        handle_red_command(self, cmd)
                    else:
                        self.message = "Invalid command. Type a tab number (1-11), or battle command (assemble, fight, swap, run, restart)."
                elif self.current_tab == 4 and cmd.startswith("buy"):
                    self.handle_shop_buy(cmd)
                elif self.current_tab == 4 and (cmd.startswith("use") or cmd.startswith("unequip")):
                    self.handle_bag_use(cmd)
                elif self.current_tab == 4 and cmd.startswith("sell"):
                    self.handle_bag_sell(cmd)
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

    def handle_bag_use(self, cmd: str):
        from poketokenbar.tui_tabs.shop import handle_bag_use
        handle_bag_use(self, cmd)

    def handle_bag_sell(self, cmd: str):
        from poketokenbar.tui_tabs.shop import handle_bag_sell
        handle_bag_sell(self, cmd)

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

def main():
    tui = PokeTokenBarTUI()
    tui.run()

if __name__ == "__main__":
    main()
