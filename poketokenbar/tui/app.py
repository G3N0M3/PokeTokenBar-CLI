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
from poketokenbar.tui.modals.celebration import check_and_render_celebration
from poketokenbar.tui.router import CommandRouter

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
        self.nursery_page = 1
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

            # Check for celebration modals
            if check_and_render_celebration(self):
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
                CommandRouter.dispatch(self, cmd)
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
        rocket_team_ids = self.engine.get_rocket_battle_active_pokemon_ids()

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
                if sp_id in rocket_team_ids:
                    skipped_reasons.append(f"{sp_name} (in Rocket battle)")
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
