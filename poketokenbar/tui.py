import os
import sys
import time
import datetime
from typing import Optional

from poketokenbar.tracker.manager import UsageManager
from poketokenbar.tracker.auto_tracker import AutoTracker
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

        # Background auto-tracker
        self.auto_tracker = AutoTracker(callback=self._on_auto_events)

    def _on_auto_events(self, events: list):
        if events:
            self.message = "\n".join(events)

    def clear_screen(self):
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()

    def run(self):
        """Main interactive event loop."""
        # Initial refresh
        summary = self.tracker.get_summary()
        self.engine.process_usage(summary["total_tokens"])
        
        # Start background auto tracker
        self.auto_tracker.start()

        try:
            while True:
                self.clear_screen()
                settings = self.engine.get_settings()
                summary = self.tracker.get_summary()

                # Process growth if tracking is enabled
                if settings.get("auto_tracking_enabled", True):
                    events = self.engine.process_usage(summary["total_tokens"])
                    if events:
                        self.message = "\n".join(events)

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
                    self.render_monitor_tab(summary)
                elif self.current_tab == 9:
                    self.render_poker_tab()
                elif self.current_tab == 10:
                    self.render_gacha_tab()
                elif self.current_tab == 11:
                    self.render_settings_tab()

                self.render_footer()

                interval = float(settings.get("refresh_interval", 3.0))
                auto_on = settings.get("auto_tracking_enabled", True)
                status_str = f"Auto: {'ON' if auto_on else 'OFF'} ({interval}s)"

                sys.stdout.write(f"\n{BOLD}Select tab (1-11), command, r=Refresh, q=Quit [{status_str}]: {RESET}")
                sys.stdout.flush()

                try:
                    import select
                    select_timeout = interval if auto_on else None
                    readable, _, _ = select.select([sys.stdin], [], [], select_timeout)
                    if readable:
                        cmd = sys.stdin.readline().strip().lower()
                        if self.pending_reset:
                            self.pending_reset = False
                            if cmd == "reset all":
                                ok, msg = self.engine.reset_game_state()
                                self.message = f"🧹 {msg}"
                            else:
                                self.message = "❌ Reset cancelled."
                        elif cmd in ["q", "exit", "quit"]:
                            print("\nExiting PokeTokenBar. Keep coding! 🐾")
                            break
                        elif cmd == "1":
                            self.current_tab = 1
                            self.message = ""
                        elif cmd == "2":
                            self.current_tab = 2
                            self.message = ""
                        elif cmd == "3":
                            self.current_tab = 3
                            self.message = ""
                        elif cmd == "4":
                            self.current_tab = 4
                            self.message = ""
                        elif cmd == "5":
                            self.current_tab = 5
                            self.message = ""
                        elif cmd == "6":
                            self.current_tab = 6
                            self.message = ""
                        elif cmd == "7":
                            self.current_tab = 7
                            self.message = ""
                        elif cmd == "8":
                            self.current_tab = 8
                            self.message = ""
                        elif cmd == "9":
                            self.current_tab = 9
                            self.message = ""
                        elif cmd == "10":
                            self.current_tab = 10
                            self.message = ""
                        elif cmd == "11":
                            self.current_tab = 11
                            self.message = ""
                        elif cmd in ["r", "refresh"]:
                            summary = self.tracker.get_summary()
                            events = self.engine.process_usage(summary["total_tokens"])
                            if events:
                                self.message = "Refreshed logs! " + " ".join(events)
                            else:
                                self.message = f"Refreshed usage logs! Total indexed: {format_tokens(summary['total_tokens'])} tokens."
                        elif cmd == "toggle" and self.current_tab == 11:
                            curr_on = settings.get("auto_tracking_enabled", True)
                            ok, msg = self.engine.update_settings(auto_tracking_enabled=not curr_on)
                            self.message = f"Automatic tracking set to: {'ON' if not curr_on else 'OFF'}"
                        elif cmd.startswith("select"):
                            parts = cmd.split()
                            if len(parts) >= 2:
                                ok, msg = self.engine.select_active_from_dex(parts[-1])
                                self.message = msg
                            else:
                                self.message = "Usage: select <number> (e.g. 'select 1' or 'select 570')"
                        elif cmd.startswith("claim"):
                            parts = cmd.split()
                            ok, msg = self.engine.claim_quest_reward(parts[-1] if len(parts) >= 2 else "all")
                            self.message = msg
                        elif cmd.startswith("send") or cmd.startswith("expedition"):
                            parts = cmd.split()
                            if len(parts) >= 2:
                                area = parts[2] if len(parts) >= 3 else "viridian"
                                ok, msg = self.engine.dispatch_expedition(parts[1], area)
                                self.message = msg
                            else:
                                self.message = "Usage: send <number/species_id> [viridian/cerulean/silver]"
                        elif cmd.startswith("bet"):
                            parts = cmd.split()
                            if len(parts) >= 2:
                                ok, msg = self.engine.play_poker_bet(parts[1])
                                self.message = msg
                            else:
                                self.message = "Usage: bet <amount> (e.g. 'bet 500k', 'bet 1m')"
                        elif cmd in ["flop", "turn", "river", "call", "check", "raise", "fold"] or cmd.startswith("hold"):
                            ok, msg = self.engine.play_poker_hold(cmd)
                            self.message = msg
                        elif cmd.startswith("pull"):
                            parts = cmd.split()
                            pull_type = parts[1] if len(parts) >= 2 else "1"
                            ok, msg = self.engine.play_gacha(pull_type)
                            self.message = msg
                        elif cmd == "card":
                            self.message = self.engine.generate_trainer_card()
                        elif cmd.startswith("interval"):
                            parts = cmd.split()
                            if len(parts) >= 2:
                                try:
                                    val = float(parts[-1])
                                    ok, msg = self.engine.update_settings(refresh_interval=val)
                                    self.message = msg
                                except ValueError:
                                    self.message = "Invalid interval number. Usage: interval <seconds>"
                            else:
                                self.message = "Usage: interval <seconds> (e.g. 'interval 5')"
                        elif cmd == "reset" and self.current_tab == 11:
                            self.pending_reset = True
                            self.message = "⚠️ CONFIRMATION REQUIRED: Type 'RESET ALL' to wipe progress & restart fresh, or anything else to cancel!"
                        elif self.current_tab == 4 and cmd.startswith("buy"):
                            self.handle_shop_buy(cmd)
                        elif self.current_tab == 4 and cmd.startswith("use"):
                            self.handle_bag_use(cmd)
                except KeyboardInterrupt:
                    print("\nExiting PokeTokenBar. Keep coding! 🐾")
                    break
        finally:
            self.auto_tracker.stop()

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
        t8 = f"{BOLD}{CYAN}[8] Monitor{RESET}" if self.current_tab == 8 else "[8] Monitor"
        t9 = f"{BOLD}{CYAN}[9] Hold 'em{RESET}" if self.current_tab == 9 else "[9] Hold 'em"
        t10 = f"{BOLD}{CYAN}[10] Gacha{RESET}" if self.current_tab == 10 else "[10] Gacha"
        t11 = f"{BOLD}{CYAN}[11] Settings{RESET}" if self.current_tab == 11 else "[11] Settings"

        sys.stdout.write(f"  {t1}   {t2}     {t3}      {t4}\n")
        sys.stdout.write(f"  {t5} {t6}     {t7}      {t8}\n")
        sys.stdout.write(f"  {t9}    {t10}    {t11}\n")
        sys.stdout.write("-" * 72 + "\n")

    def render_companion_tab(self, summary: dict):
        active = self.engine.active_mon

        if active is None:
            # Egg state
            egg_usage = self.engine.state.get("egg_usage", 0)
            threshold = PokemonBalance.EGG_HATCH_THRESHOLD
            bar = format_progress_bar(egg_usage, threshold)

            sys.stdout.write(f"\n  {YELLOW}🥚 Pokémon Egg Incubating...{RESET}\n")
            sys.stdout.write(f"  Incubation Progress: {bar} ({format_tokens(egg_usage)} / {format_tokens(threshold)} tokens)\n")
            sys.stdout.write("  Keep spending tokens in Antigravity CLI to hatch your egg!\n\n")
        else:
            # Active Pokémon
            sp_id = active.current_id
            name = self.engine.api.get_species_name(sp_id)
            shiny_str = f"{YELLOW}✨ SHINY {RESET}" if active.is_shiny else ""
            nature_name = active.nature.display_name if active.nature else "Unknown"
            mega_badge = f" {BOLD}{HEADER}[✨ MEGA EVOLVED +50% XP]{RESET}" if active.is_mega else ""

            sys.stdout.write(f"\n  {BOLD}{GREEN}Active Companion: {shiny_str}{name} (#{sp_id}){mega_badge}{RESET}\n")
            sys.stdout.write(f"  Rarity: {YELLOW}{active.rarity.value.upper()}{RESET}  |  Nature: {CYAN}{nature_name}{RESET}  |  Form: {active.stage_index+1}/{active.total_forms}\n")

            happiness = active.happiness if active else self.engine.state.get("happiness", 100)
            streak = self.engine.state.get("streak_days", 1)
            hap_boost = f" {GREEN}(+20% Bonus XP!){RESET}" if happiness >= 100 else ""
            sys.stdout.write(f"  Happiness: {RED}💖 {happiness}%{RESET}{hap_boost}  |  Coding Streak: {YELLOW}🔥 {streak} Days{RESET}\n")

            # Try rendering sprite
            sprite_path = self.engine.api.download_sprite(sp_id, is_shiny=active.is_shiny)
            if sprite_path:
                sprite_ansi = SpriteRenderer.render_png_to_ansi(sprite_path, max_cols=24)
                sys.stdout.write("\n" + sprite_ansi + "\n\n")

            # Growth / Evolution progress
            target_xp = PokemonBalance.phase_threshold(active.rarity, active.total_forms, active.stage_index, self.engine.current_difficulty)
            
            # Check if this stage has already evolved into next stage
            dex = self.engine.state.get("dex", [])
            discovered_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))) for d in dex}
            is_already_evolved = (active.stage_index < len(active.path_ids) - 1) and (active.path_ids[active.stage_index + 1] in discovered_sp_ids)

            if is_already_evolved:
                bar = format_progress_bar(target_xp, target_xp, width=12)
                next_id = active.path_ids[active.stage_index + 1]
                next_name = self.engine.api.get_species_name(next_id)
                sys.stdout.write(f"  Evo -> {next_name}: {bar} ({format_tokens(target_xp)}/{format_tokens(target_xp)}) {GREEN}[EVOLVED]{RESET}\n")
            elif active.stage_index < len(active.path_ids) - 1:
                bar = format_progress_bar(active.used_at_stage, target_xp, width=12)
                next_id = active.path_ids[active.stage_index + 1]
                next_name = self.engine.api.get_species_name(next_id)
                sys.stdout.write(f"  Evo -> {next_name}: {bar} ({format_tokens(active.used_at_stage)} / {format_tokens(target_xp)})\n")
            else:
                bar = format_progress_bar(active.used_at_stage, target_xp, width=12)
                sys.stdout.write(f"  Graduation: {bar} ({format_tokens(active.used_at_stage)} / {format_tokens(target_xp)})\n")

        sys.stdout.write("\n" + "-" * 72 + "\n")
        sys.stdout.write(f" {BOLD}📊 Token Usage Metrics:{RESET}\n")
        sys.stdout.write(f"  • Today's Tokens: {BOLD}{CYAN}{format_tokens(summary['today_tokens'])}{RESET}  (Antigravity: {format_tokens(summary['antigravity_today'])})\n")
        sys.stdout.write(f"  • 7-Day Tokens:   {format_tokens(summary['week_tokens'])}\n")
        sys.stdout.write(f"  • Monthly Tokens: {format_tokens(summary['month_tokens'])}\n")
        sys.stdout.write(f"  • Total Tokens:   {format_tokens(summary['total_tokens'])}\n")
        sys.stdout.write(f"  • Active Burn:    {format_tokens(summary['burn_rate_tpm'])} tokens/min\n")

    def render_pokedex_tab(self):
        active = self.engine.active_mon
        if active:
            self.engine._register_to_dex(active, status="active")

        dex = self.engine.state.get("dex", [])
        sys.stdout.write(f"\n  {BOLD}{HEADER}📖 Pokédex Archives ({len(dex)} species registered){RESET}\n\n")

        if not dex:
            sys.stdout.write("  Your Pokédex is empty! Incubate and raise your Pokémon companions to fill it.\n\n")
        else:
            expeditions = self.engine.state.get("expeditions", [])
            exp_map = {e["sp_id"]: e for e in expeditions}

            for idx, entry in enumerate(dex, 1):
                sp_id = entry.get("species_id", entry.get("final_id", entry.get("base_id")))
                name = self.engine.api.get_species_name(sp_id)
                shiny_str = f"{YELLOW}✨{RESET}" if entry.get("is_shiny") else ""
                rarity = entry.get("rarity", "common").upper()
                status = entry.get("status", "discovered")

                if sp_id in exp_map:
                    exp_info = exp_map[sp_id]
                    pct = (exp_info["progress"] / exp_info["target"]) * 100
                    status_badge = f"{BOLD}{CYAN}[ON EXPEDITION: {exp_info['area']} ({pct:.0f}%)] {RESET}"
                elif active and active.current_id == sp_id:
                    status_badge = f"{BOLD}{GREEN}[ACTIVE]{RESET}"
                elif status == "graduated":
                    status_badge = f"{BOLD}{CYAN}[GRADUATED]{RESET}"
                elif status == "evolved":
                    status_badge = f"{BOLD}{YELLOW}[EVOLVED]{RESET}"
                else:
                    status_badge = f"{BOLD}{YELLOW}[DISCOVERED]{RESET}"

                sys.stdout.write(f"  {idx:2d}. {shiny_str} {BOLD}{name}{RESET} (#{sp_id}) [{rarity}] {status_badge}\n")

        sys.stdout.write(f"\n  ➔ Complete evolutions and hatch eggs to discover all Pokédex entries!\n\n")

    def render_roster_tab(self):
        active = self.engine.active_mon
        if active:
            self.engine._register_to_dex(active, status="active")

        dex = self.engine.state.get("dex", [])
        sys.stdout.write(f"\n  {BOLD}{HEADER}🐾 Caught Pokémon Roster{RESET}\n\n")

        # Show Incubating Egg option ONLY if an egg is owned/incubating or active is None
        incubating_eggs = self.engine.state.get("incubating_eggs", {})
        has_egg = bool(incubating_eggs) or bool(self.engine.state.get("egg_tier")) or (active is None)
        if has_egg:
            egg_usage = self.engine.state.get("egg_usage", 0)
            threshold = self.engine.current_difficulty.hatch_threshold
            pct = (egg_usage / threshold) * 100 if threshold > 0 else 0
            egg_badge = f"{BOLD}{GREEN}[ACTIVE / INCUBATING]{RESET}" if active is None else f"{BOLD}{YELLOW}[IN ROSTER]{RESET}"
            sys.stdout.write(f"   0. 🥚 {BOLD}Incubating Pokémon Egg{RESET} ({pct:.1f}%) {egg_badge}\n")

        expeditions = self.engine.state.get("expeditions", [])
        exp_map = {e["sp_id"]: e for e in expeditions}
        # Filter dex to active roster (plus any species currently on expedition)
        roster = [d for d in dex if (d.get("status") != "evolved" or d.get("species_id", d.get("final_id", d.get("base_id"))) in exp_map)]

        if not roster:
            sys.stdout.write("  No active companions in your roster. Incubate an egg to start!\n\n")
        else:
            for idx, entry in enumerate(roster, 1):
                sp_id = entry.get("species_id", entry.get("final_id", entry.get("base_id")))
                name = self.engine.api.get_species_name(sp_id)
                shiny_str = f"{YELLOW}✨{RESET}" if entry.get("is_shiny") else ""
                rarity = entry.get("rarity", "common").upper()
                status = entry.get("status", "graduated")
                mon_data = entry.get("mon_state", {})
                hap_val = mon_data.get("happiness", 100) if isinstance(mon_data, dict) else 100

                if sp_id in exp_map:
                    exp_info = exp_map[sp_id]
                    pct = (exp_info["progress"] / exp_info["target"]) * 100
                    status_badge = f"{BOLD}{CYAN}[ON EXPEDITION: {exp_info['area']} ({pct:.0f}%)] {RESET}"
                elif status == "active" and active is not None:
                    status_badge = f"{BOLD}{GREEN}[ACTIVE]{RESET}"
                elif status == "inactive":
                    status_badge = f"{BOLD}{YELLOW}[IN ROSTER]{RESET}"
                else:
                    status_badge = f"{BOLD}{CYAN}[GRADUATED]{RESET}"

                sys.stdout.write(f"  {idx:2d}. {shiny_str} {BOLD}{name}{RESET} (#{sp_id}) [{rarity}] 💖{hap_val}% {status_badge}\n")

        sys.stdout.write(f"\n  ➔ Type '{BOLD}select <id>{RESET}' or '{BOLD}select egg{RESET}' to switch active companion!\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}send <id> [viridian/cerulean/silver]{RESET}' on expedition!\n\n")

    def render_shop_tab(self):
        avail = self.engine.available_tokens
        inv = self.engine.state.get("inventory", {})
        diff = self.engine.current_difficulty
        prices = diff.shop_prices

        p_rc = format_tokens(prices["rare_candy"])
        p_rc_xp = format_tokens(int(prices["rare_candy"] * 0.6))
        p_mint = format_tokens(prices["mint"])
        p_charm = format_tokens(prices["shiny_charm"])
        p_egg1 = format_tokens(prices["egg_normal"])
        p_egg2 = format_tokens(prices["egg_uncommon"])

        sys.stdout.write(f"\n  {BOLD}{YELLOW}🛒 Token Shop & Bag{RESET}  (Available Spendable Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET})\n\n")
        sys.stdout.write(f"  {BOLD}Shop Items (Type 'buy <number>' to purchase):{RESET}\n")
        sys.stdout.write(f"  [1] 🍬 Rare Candy     - Cost: {p_rc:<6} tokens  (Grants +{p_rc_xp} XP)\n")
        sys.stdout.write(f"  [2] 🌿 Mint           - Cost: {p_mint:<6} tokens  (Rerolls nature)\n")
        sys.stdout.write(f"  [3] ✨ Shiny Charm    - Cost: {p_charm:<6} tokens  (Passive 1/48 shiny odds)\n")
        sys.stdout.write(f"  [4] 🥚 Pokémon Egg    - Cost: {p_egg1:<6} tokens  (Incubate new egg)\n")
        sys.stdout.write(f"  [5] 🥚 Uncommon Egg   - Cost: {p_egg2:<6} tokens  (Guarantees Uncommon+ egg)\n")
        sys.stdout.write(f"  [6] 🫐 Oran Berry     - Cost: 1.0M   tokens  (+25% Companion Happiness)\n")
        sys.stdout.write(f"  [7] 🍇 Golden Razz    - Cost: 5.0M   tokens  (Boosts next egg shiny odds to 1/24!)\n")
        sys.stdout.write(f"  [8] 🔮 Mega Stone     - Cost: 50.0M  tokens  (Mega Evolve eligible final forms!)\n\n")

        sys.stdout.write(f"  {BOLD}Your Bag (Type 'use <number>' to use):{RESET}\n")
        sys.stdout.write(f"  [1] 🍬 Rare Candy: {inv.get('rare_candy', 0)} owned\n")
        sys.stdout.write(f"  [2] 🌿 Mint:       {inv.get('mint', 0)} owned\n")
        sys.stdout.write(f"  [3] 🫐 Oran Berry: {inv.get('berry_oran', 0)} owned\n")
        sys.stdout.write(f"  [4] 🍇 Golden Razz: {inv.get('berry_golden', 0)} owned\n")
        sys.stdout.write(f"  [5] 🔮 Mega Stone:  {inv.get('mega_stone', 0)} owned\n")
        has_charm = "OWNED (Active)" if inv.get("shiny_charm", 0) > 0 else "Not owned"
        sys.stdout.write(f"  [+] ✨ Shiny Charm: {has_charm}\n\n")

    def handle_shop_buy(self, cmd: str):
        choice = cmd.split()[-1]
        if choice == "1":
            ok, msg = self.engine.buy_item(ItemKind.RARE_CANDY)
        elif choice == "2":
            ok, msg = self.engine.buy_item(ItemKind.MINT)
        elif choice == "3":
            ok, msg = self.engine.buy_item(ItemKind.SHINY_CHARM)
        elif choice == "4":
            ok, msg = self.engine.buy_egg(None)
        elif choice == "5":
            ok, msg = self.engine.buy_egg(Rarity.UNCOMMON)
        elif choice == "6":
            ok, msg = self.engine.buy_item(ItemKind.BERRY_ORAN)
        elif choice == "7":
            ok, msg = self.engine.buy_item(ItemKind.BERRY_GOLDEN)
        elif choice == "8":
            ok, msg = self.engine.buy_item(ItemKind.MEGA_STONE)
        else:
            ok, msg = False, "Invalid shop selection."
        self.message = msg

    def handle_bag_use(self, cmd: str):
        choice = cmd.split()[-1]
        if choice == "1":
            ok, msg = self.engine.use_item(ItemKind.RARE_CANDY)
        elif choice == "2":
            ok, msg = self.engine.use_item(ItemKind.MINT)
        elif choice == "3":
            ok, msg = self.engine.use_item(ItemKind.BERRY_ORAN)
        elif choice == "4":
            ok, msg = self.engine.use_item(ItemKind.BERRY_GOLDEN)
        elif choice == "5":
            ok, msg = self.engine.use_item(ItemKind.MEGA_STONE)
        else:
            ok, msg = False, "Invalid bag selection."
        self.message = msg

    def render_quests_tab(self):
        qdata = self.engine.state.get("daily_quests", {})
        quests = qdata.get("quests", [])
        badges = self.engine.state.get("gym_badges", [])
        achievements = self.engine.state.get("achievements", [])

        sys.stdout.write(f"\n  {BOLD}{HEADER}🏆 Quests, Badges & Achievements{RESET}\n\n")

        # 1. Daily Quests
        sys.stdout.write(f"  {BOLD}🎯 Daily Quests (Type 'claim <id>' to collect rewards):{RESET}\n")
        if not quests:
            sys.stdout.write("   No daily quests active today. Spend tokens to refresh!\n")
        else:
            for q in quests:
                q_id = q["id"]
                txt = q["text"]
                prog = q["progress"]
                target = q["target"]
                claimed = q["claimed"]
                if claimed:
                    status = f"{BOLD}{GREEN}[CLAIMED]{RESET}"
                elif prog >= target:
                    status = f"{BOLD}{YELLOW}[READY - TYPE 'claim {q_id}']{RESET}"
                else:
                    status = f"({format_tokens(prog)} / {format_tokens(target)})"
                sys.stdout.write(f"   [{q_id}] {txt:<38} {status}\n")

        # 2. Gym Badges Collected
        sys.stdout.write(f"\n  {BOLD}🏅 Gym Badges Collected ({len(badges)}/10):{RESET}\n")
        if not badges:
            sys.stdout.write("   No badges earned yet. Defeat Gym Bosses to earn badges!\n")
        else:
            for i in range(0, len(badges), 4):
                chunk = badges[i:i+4]
                sys.stdout.write("   " + "   ".join([f"{BOLD}{YELLOW}{b}{RESET}" for b in chunk]) + "\n")

        # 3. Achievements Unlocked
        sys.stdout.write(f"\n  {BOLD}🎖️ Achievements ({len(achievements)} Unlocked):{RESET}\n")
        all_achievements = [
            ("shiny_hunter", "🌟 Shiny Hunter", "Hatch a rare Shiny Pokémon"),
            ("token_tycoon", "💎 Token Tycoon", "Burn 100M+ lifetime tokens"),
            ("dex_collector", "📖 Dex Collector", "Register 5+ species in Pokédex"),
            ("gym_champion", "🏆 Gym Champion", "Defeat your first Gym Boss Raid"),
            ("streak_master", "⚡ Streak Master", "Maintain a 3+ day coding streak")
        ]
        unlocked_set = set(achievements)
        for code, title, desc in all_achievements:
            if code in unlocked_set:
                badge = f"{BOLD}{GREEN}[UNLOCKED]{RESET}"
                sys.stdout.write(f"   • {BOLD}{title:<18}{RESET} - {desc:<36} {badge}\n")
            else:
                badge = f"{BOLD}{YELLOW}[LOCKED]{RESET}"
                sys.stdout.write(f"   • {title:<18} - {desc:<36} {badge}\n")
        sys.stdout.write("\n")

    def render_expeditions_tab(self):
        expeditions = self.engine.state.get("expeditions", [])
        sys.stdout.write(f"\n  {BOLD}{HEADER}🗺️ Pokédex Expeditions ({len(expeditions)} Active){RESET}\n\n")
        sys.stdout.write(f"  {BOLD}Available Expedition Destinations:{RESET}\n")
        sys.stdout.write(f"   • Viridian Forest - Target: 5.0M tokens  - Reward: 🌿 Mint\n")
        sys.stdout.write(f"   • Cerulean Cave   - Target: 15.0M tokens - Reward: 🍬 Rare Candy\n")
        sys.stdout.write(f"   • Mt. Silver      - Target: 30.0M tokens - Reward: 🍇 Golden Razz Berry\n\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}send <number/species_id> [viridian/cerulean/silver]{RESET}' to dispatch!\n\n")

        sys.stdout.write(f"  {BOLD}🗺️ Active Expeditions Status:{RESET}\n")
        if not expeditions:
            sys.stdout.write("   No companions currently on expedition.\n\n")
        else:
            for exp in expeditions:
                sp_id = exp["sp_id"]
                sp_name = self.engine.api.get_species_name(sp_id)
                area = exp["area"]
                bar = format_progress_bar(exp["progress"], exp["target"], width=10)
                sys.stdout.write(f"   • {BOLD}{CYAN}{sp_name} (#{sp_id}){RESET} @ {area}: {bar} ({format_tokens(exp['progress'])} / {format_tokens(exp['target'])})\n")
            sys.stdout.write("\n")

        # Recent Expedition Logs
        exp_logs = self.engine.state.get("expedition_logs", [])
        sys.stdout.write(f"  {BOLD}📜 Recent Expedition Logs (Last 5 Expeditions):{RESET}\n")
        if not exp_logs:
            sys.stdout.write("   No completed expeditions recorded yet. Dispatch companions to start!\n\n")
        else:
            for log in exp_logs:
                sys.stdout.write(f"   {log}\n")
            sys.stdout.write("\n")

    def render_battles_tab(self):
        boss = self.engine.state.get("active_boss")
        battles = self.engine.state.get("trainer_battles", {"wins": 0, "losses": 0})
        logs = self.engine.state.get("battle_logs", [])

        sys.stdout.write(f"\n  {BOLD}{HEADER}⚔️ Gym Boss Raids & Trainer Auto-Battles{RESET}\n\n")

        # 1. Active Gym Boss Raid
        sys.stdout.write(f"  {BOLD}⚔️ Active Gym Boss Raid:{RESET}\n")
        if boss:
            b_name = boss["name"]
            b_sp_id = boss["sp_id"]
            hp_cur = boss["current_hp"]
            hp_tot = boss["total_hp"]
            badge = boss["badge"]
            bar = format_progress_bar(hp_cur, hp_tot)
            sys.stdout.write(f"   Boss: {BOLD}{RED}{b_name} (#{b_sp_id}){RESET} - Reward: {badge}\n")
            sys.stdout.write(f"   Boss HP: {bar} ({format_tokens(hp_cur)} / {format_tokens(hp_tot)})\n")
            sys.stdout.write("   ➔ Attack the boss by spending tokens in Antigravity CLI!\n\n")
        else:
            sys.stdout.write("   No active Boss Raid. Reach daily token milestones to summon Gym Bosses!\n\n")

        # 2. Mini-Trainer Auto-Battle Record
        sys.stdout.write(f"  {BOLD}⚔️ Mini-Trainer Auto-Battle Record:{RESET}\n")
        sys.stdout.write(f"   Wins: {BOLD}{GREEN}{battles.get('wins', 0)}{RESET}  |  Losses: {BOLD}{RED}{battles.get('losses', 0)}{RESET} (Triggers auto-battles every 2.0M tokens!)\n\n")

        # 3. Recent Auto-Battle Logs (Last 5 Fights)
        sys.stdout.write(f"  {BOLD}📜 Recent Auto-Battle Logs (Last 5 Fights):{RESET}\n")
        if not logs:
            sys.stdout.write("   No recent auto-battles recorded yet. Keep coding to trigger fights!\n\n")
        else:
            for log in logs:
                sys.stdout.write(f"   {log}\n")
            sys.stdout.write("\n")

    def render_monitor_tab(self, summary: dict):
        sys.stdout.write(f"\n  {BOLD}{CYAN}📡 Live Token Usage Monitor{RESET}\n\n")
        sys.stdout.write(f"  Active Log Sources Detected:\n")
        sys.stdout.write(f"   • Antigravity CLI (~/.gemini/antigravity-cli/conversations/*.db)\n")
        sys.stdout.write(f"   • Gemini CLI      (~/.gemini/tmp/**/chats/*.json*)\n")
        sys.stdout.write(f"   • Claude Code     (~/.claude/projects/**/*.jsonl)\n\n")
        sys.stdout.write(f"  Current Burn Rate: {BOLD}{YELLOW}{format_tokens(summary['burn_rate_tpm'])} tokens/minute{RESET}\n")
        sys.stdout.write(f"  Total Indexed Calls: {summary['total_entries']:,}\n")
        sys.stdout.write(f"  Last Scan Timestamp: {summary['last_updated'].strftime('%H:%M:%S')}\n\n")

    def render_poker_tab(self):
        avail = self.engine.available_tokens
        sys.stdout.write(f"\n  {BOLD}{HEADER}♠️ Casino Texas Hold 'em (You vs. The House!){RESET}\n\n")
        sys.stdout.write(f"  Available Tokens to Bet: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n\n")

        sys.stdout.write(f"  {BOLD}🃏 Rules & Payout Multipliers:{RESET}\n")
        sys.stdout.write(f"   • Receive 2 Hole Cards. Beat the House Dealer's best 5-card hand!\n")
        sys.stdout.write(f"   • Winning Bonus Multipliers: Royal Flush [50x] | Straight Flush [15x]\n")
        sys.stdout.write(f"   • Four of a Kind [8x] | Full House [5x] | Flush [4x] | Straight [3x]\n\n")

        sys.stdout.write(f"  ➔ Step 1: Type '{BOLD}bet <amount>{RESET}' to deal 2 Hole Cards (e.g. 'bet 500k', 'bet 1m')\n")
        sys.stdout.write(f"  ➔ Step 2: Type '{BOLD}flop{RESET}' to reveal 3 Flop Community Cards (or '{BOLD}fold{RESET}')\n")
        sys.stdout.write(f"  ➔ Step 3: Type '{BOLD}turn{RESET}' to reveal the 4th Turn Card (or '{BOLD}fold{RESET}')\n")
        sys.stdout.write(f"  ➔ Step 4: Type '{BOLD}river{RESET}' (or '{BOLD}call{RESET}') for Showdown! (or '{BOLD}raise{RESET}' to double bet)\n\n")

        if self.engine.poker.player_hole:
            p_hole = " ".join([str(c) for c in self.engine.poker.player_hole])
            if self.engine.poker.game_state == "preflop":
                board = "[?] [?] [?] [?] [?]"
                d_hole = "[?] [?]"
                state_str = "Pre-Flop (Type 'flop' to reveal community cards, or 'fold')"
            elif self.engine.poker.game_state == "flop":
                board = " ".join([str(c) for c in self.engine.poker.community_cards[:3]]) + " [?] [?]"
                d_hole = "[?] [?]"
                state_str = "The Flop (Type 'turn' to reveal 4th card, or 'fold')"
            elif self.engine.poker.game_state == "turn":
                board = " ".join([str(c) for c in self.engine.poker.community_cards[:4]]) + " [?]"
                d_hole = "[?] [?]"
                state_str = "The Turn (Type 'river' or 'call' for Showdown, or 'fold')"
            else:
                board = " ".join([str(c) for c in self.engine.poker.community_cards])
                d_hole = " ".join([str(c) for c in self.engine.poker.dealer_hole])
                state_str = "Showdown Completed"

            sys.stdout.write(f"  {BOLD}Active Table [{state_str}]:{RESET}\n")
            sys.stdout.write(f"   🎴 Your Hole Cards:  {p_hole}\n")
            sys.stdout.write(f"   ♦️ Community Board: {board}\n")
            sys.stdout.write(f"   🏠 House Hole:       {d_hole}\n")
            sys.stdout.write(f"   Current Bet: {BOLD}{YELLOW}{format_tokens(self.engine.poker.current_bet)}{RESET} tokens\n\n")

    def render_gacha_tab(self):
        avail = self.engine.available_tokens
        sys.stdout.write(f"\n  {BOLD}{HEADER}🔮 Pokémon Gacha Capsule Machine{RESET}\n\n")
        sys.stdout.write(f"  Available Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n\n")

        sys.stdout.write(f"  {BOLD}🎰 Pull Options:{RESET}\n")
        sys.stdout.write(f"   • Single Capsule Pull (1x):  {BOLD}{YELLOW}5.0M Tokens{RESET}  (Type '{BOLD}pull 1{RESET}')\n")
        sys.stdout.write(f"   • Multi Capsule Pull (10x):  {BOLD}{YELLOW}45.0M Tokens{RESET} (Type '{BOLD}pull 10{RESET}' - 1 Free!)\n\n")

        sys.stdout.write(f"  {BOLD}🎁 Drop Rates & Rewards:{RESET}\n")
        sys.stdout.write(f"   • 🌟 Legendary (2%):  Guaranteed Shiny Companion / +50M Tokens\n")
        sys.stdout.write(f"   • ✨ Epic (8%):       Shiny Charm ✨, Rare Egg 🥚 Tier\n")
        sys.stdout.write(f"   • 🔮 Rare (15%):      Standard/Uncommon Eggs 🥚, Mega Stone 🔮\n")
        sys.stdout.write(f"   • 🍬 Uncommon (30%):  Rare Candy 🍬, Golden Razz Berry 🍇, +3M Tokens\n")
        sys.stdout.write(f"   • 🫐 Common (45%):    Oran Berry 🫐, Mint 🌿, +1M Tokens\n\n")

    def render_settings_tab(self):
        settings = self.engine.get_settings()
        enabled = settings.get("auto_tracking_enabled", True)
        interval = float(settings.get("refresh_interval", 3.0))

        status_badge = f"{BOLD}{GREEN}[ON / ENABLED]{RESET}" if enabled else f"{BOLD}{RED}[OFF / DISABLED]{RESET}"

        sys.stdout.write(f"\n  {BOLD}{CYAN}⚙️ Tracking & Application Settings{RESET}\n\n")
        sys.stdout.write(f"  [1] Automatic Token Tracking: {status_badge}\n")
        sys.stdout.write(f"      ➔ Type '{BOLD}toggle{RESET}' to switch ON/OFF\n\n")
        sys.stdout.write(f"  [2] Auto-Refresh Interval:    {BOLD}{YELLOW}{interval} seconds{RESET}\n")
        sys.stdout.write(f"      ➔ Type '{BOLD}interval <seconds>{RESET}' to change (e.g. 'interval 5')\n\n")
        sys.stdout.write(f"  [3] Reset Game Progress:       {BOLD}{RED}[DANGER]{RESET}\n")
        sys.stdout.write(f"      ➔ Type '{BOLD}reset{RESET}' to clear all saved progress & restart fresh\n\n")

    def render_footer(self):
        sys.stdout.write("-" * 72 + "\n")
        if self.message:
            sys.stdout.write(f"  {GREEN}➔ {self.message}{RESET}\n")

def main():
    tui = PokeTokenBarTUI()
    tui.run()

if __name__ == "__main__":
    main()
