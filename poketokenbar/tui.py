import os
import sys
import time
import datetime
from typing import Optional

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

    def clear_screen(self):
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()

    def run(self):
        """Main interactive event loop."""
        # Initial refresh
        summary = self.tracker.get_summary()
        self.engine.process_usage(summary["total_tokens"], summary.get("active_days"))

        while True:
            pending_eggs = self.engine.state.get("pending_eggs", [])
            if pending_eggs:
                self.clear_screen()
                new_egg = pending_eggs[0]
                curr_egg = self.engine.state.get("egg_tier")
                sys.stdout.write(f"\n  {BOLD}{YELLOW}🥚 EGG DECISION!{RESET}\n\n")
                sys.stdout.write(f"  You found a {BOLD}{new_egg.capitalize()}{RESET} Egg, but you can only carry one egg at a time!\n")
                sys.stdout.write(f"  You are currently holding a {BOLD}{curr_egg.capitalize()}{RESET} Egg.\n\n")
                sys.stdout.write(f"  Do you want to SWAP your {curr_egg.capitalize()} Egg for the {new_egg.capitalize()} Egg? (y/n)> ")
                sys.stdout.flush()
                cmd = sys.stdin.readline().strip().lower()
                
                if cmd in ["y", "yes"]:
                    self.engine.state["egg_tier"] = new_egg
                    self.engine.state["egg_usage"] = 0
                    self.engine.state["pending_eggs"] = pending_eggs[1:]
                    self.engine.save()
                    sys.stdout.write(f"\n  {GREEN}Swapped! You are now holding a {new_egg.capitalize()} Egg!{RESET}\n")
                    time.sleep(2)
                elif cmd in ["n", "no"]:
                    self.engine.state["pending_eggs"] = pending_eggs[1:]
                    self.engine.save()
                    sys.stdout.write(f"\n  {YELLOW}Discarded the {new_egg.capitalize()} Egg.{RESET}\n")
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
                self.render_monitor_tab(summary)
            elif self.current_tab == 9:
                self.render_poker_tab()
            elif self.current_tab == 10:
                self.render_gacha_tab()
            elif self.current_tab == 11:
                self.render_bank_tab()
            elif self.current_tab == 12:
                self.render_settings_tab()

            self.render_footer()

            sys.stdout.write(f"\n{BOLD}Select tab (1-12), command, r=Refresh, q=Quit: {RESET}")
            sys.stdout.flush()

            try:
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
                elif cmd == "250220":
                    self.engine.state["spent_tokens"] = self.engine.state.get("spent_tokens", 0) - 50_000_000
                    self.engine.save()
                    self.message = "🎉 EASTER EGG UNLOCKED! Granted 50.0M Tokens! 🎉"
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
                elif cmd == "12":
                    self.current_tab = 12
                    self.message = ""
                elif cmd in ["r", "refresh"]:
                    summary = self.tracker.get_summary()
                    events = self.engine.process_usage(summary["total_tokens"])
                    if events:
                        self.message = "Refreshed logs! " + " ".join(events)
                    else:
                        self.message = f"Refreshed usage logs! Total indexed: {format_tokens(summary['total_tokens'])} tokens."
                elif cmd in ["n", "next"] and self.current_tab in [2, 3]:
                    if self.current_tab == 2: self.pokedex_page += 1
                    else: self.roster_page += 1
                    self.message = ""
                elif cmd in ["p", "prev", "previous"] and self.current_tab in [2, 3]:
                    if self.current_tab == 2: self.pokedex_page = max(1, self.pokedex_page - 1)
                    else: self.roster_page = max(1, self.roster_page - 1)
                    self.message = ""
                elif cmd.startswith("page ") and self.current_tab in [2, 3]:
                    try:
                        page = max(1, int(cmd.split()[1]))
                        if self.current_tab == 2: self.pokedex_page = page
                        else: self.roster_page = page
                        self.message = ""
                    except ValueError:
                        self.message = "Usage: page <number>"
                elif cmd.startswith("select") or cmd.startswith("sel ") or cmd == "sel":
                    parts = cmd.split()
                    if len(parts) >= 2:
                        ok, msg = self.engine.select_active_from_dex(parts[1])
                        self.message = msg
                    else:
                        self.message = "Usage: sel <ROW INDEX>|#<POKEMON INDEX>, or sel egg"
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
                        self.message = "Usage: send <ROW INDEX>|#<POKEMON INDEX> [area]"
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
                elif cmd == "reset" and self.current_tab == 12:
                    self.pending_reset = True
                    self.message = "⚠️ CONFIRMATION REQUIRED: Type 'RESET ALL' to wipe progress & restart fresh, or anything else to cancel!"
                elif self.current_tab == 4 and cmd.startswith("buy"):
                    self.handle_shop_buy(cmd)
                elif self.current_tab == 4 and cmd.startswith("use"):
                    self.handle_bag_use(cmd)
                elif self.current_tab == 4 and cmd.startswith("sell"):
                    self.handle_bag_sell(cmd)
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
        t11 = f"{BOLD}{CYAN}[11] Bank{RESET}" if self.current_tab == 11 else "[11] Bank"
        t12 = f"{BOLD}{CYAN}[12] Settings{RESET}" if self.current_tab == 12 else "[12] Settings"

        sys.stdout.write(f"  {t1}   {t2}     {t3}      {t4}\n")
        sys.stdout.write(f"  {t5} {t6}     {t7}      {t8}\n")
        sys.stdout.write(f"  {t9}    {t10}      {t11}       {t12}\n")
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
            render_id = sp_id
            if active.is_mega:
                mega_map = {
                    3: 10033,   # Mega Venusaur
                    6: 10034,   # Mega Charizard X
                    9: 10036,   # Mega Blastoise
                    94: 10038,  # Mega Gengar
                    150: 10043, # Mega Mewtwo X
                    448: 10059  # Mega Lucario
                }
                render_id = mega_map.get(sp_id, sp_id)
                
            sprite_path = self.engine.api.download_sprite(render_id, is_shiny=active.is_shiny)
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

            page_size = 15
            total_pages = max(1, (len(dex) - 1) // page_size + 1)
            self.pokedex_page = max(1, min(self.pokedex_page, total_pages))

            start_idx = (self.pokedex_page - 1) * page_size
            end_idx = start_idx + page_size
            page_dex = dex[start_idx:end_idx]

            for idx, entry in enumerate(page_dex, start_idx + 1):
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

            if total_pages > 1:
                sys.stdout.write(f"\n  ➔ Page {self.pokedex_page}/{total_pages} - Type '{BOLD}next{RESET}', '{BOLD}prev{RESET}', or '{BOLD}page <N>{RESET}' to navigate!\n")
            else:
                sys.stdout.write(f"\n  ➔ Complete evolutions and hatch eggs to discover all Pokédex entries!\n\n")

    def render_roster_tab(self):
        active = self.engine.active_mon
        if active:
            self.engine._register_to_dex(active, status="active")

        dex = self.engine.state.get("dex", [])
        sys.stdout.write(f"\n  {BOLD}{HEADER}🐾 Caught Pokémon Roster{RESET}\n\n")

        # Show Incubating Egg option ONLY if an egg is owned
        egg_tier = self.engine.state.get("egg_tier")
        if egg_tier:
            egg_usage = self.engine.state.get("egg_usage", 0)
            threshold = self.engine.current_difficulty.hatch_threshold
            pct = (egg_usage / threshold) * 100 if threshold > 0 else 0
            
            tier_name = egg_tier.capitalize()
            if active is None:
                egg_badge = f"{BOLD}{GREEN}[ACTIVE / INCUBATING]{RESET}"
            else:
                egg_badge = f"{BOLD}{YELLOW}[IN ROSTER]{RESET}"
            sys.stdout.write(f"   0. 🥚 {BOLD}Incubating {tier_name} Egg{RESET} ({pct:.1f}%) {egg_badge}\n")

        expeditions = self.engine.state.get("expeditions", [])
        exp_map = {e["sp_id"]: e for e in expeditions}
        # Filter dex to active roster (excluding pre-evolutions marked as 'evolved')
        roster = [d for d in dex if d.get("status") != "evolved"]

        if not roster:
            sys.stdout.write("  No active companions in your roster. Incubate an egg to start!\n\n")
        else:
            page_size = 14
            import math
            total = len(roster)
            total_pages = max(1, math.ceil(total / page_size))
            
            self.roster_page = min(self.roster_page, total_pages)
            start_idx = (self.roster_page - 1) * page_size
            page_roster = roster[start_idx : start_idx + page_size]

            for idx, entry in enumerate(page_roster, start_idx + 1):
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

            if total_pages > 1:
                sys.stdout.write(f"\n  ➔ Page {self.roster_page}/{total_pages} - Type '{BOLD}next{RESET}', '{BOLD}prev{RESET}', or '{BOLD}page <N>{RESET}' to navigate!\n")

        sys.stdout.write(f"\n  ➔ Type '{BOLD}sel <ROW INDEX>|#<POKEMON INDEX>{RESET}', or '{BOLD}sel egg{RESET}' to switch active companion!\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}send <ROW INDEX>|#<POKEMON INDEX> [area]{RESET}' on expedition!\n")
        sys.stdout.write(f"     Areas:\n")
        sys.stdout.write(f"       • '{BOLD}viridian{RESET}' (5M, Mint)\n")
        sys.stdout.write(f"       • '{BOLD}cerulean{RESET}' (15M, Rare Candy)\n")
        sys.stdout.write(f"       • '{BOLD}silver{RESET}'   (30M, Golden Razz)\n\n")

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
        sys.stdout.write(f"  {BOLD}Shop Items (Type 'buy <number> [qty]' to purchase):{RESET}\n")
        sys.stdout.write(f"  [1] 🍬 Rare Candy     - Cost: {p_rc:<6} tokens  (Grants +{p_rc_xp} XP)\n")
        sys.stdout.write(f"  [2] 🌿 Mint           - Cost: {p_mint:<6} tokens  (Rerolls nature)\n")
        sys.stdout.write(f"  [3] ✨ Shiny Charm    - Cost: {p_charm:<6} tokens  (Passive 1/48 shiny odds)\n")
        sys.stdout.write(f"  [4] 🥚 Pokémon Egg    - Cost: {p_egg1:<6} tokens  (Incubate new egg)\n")
        sys.stdout.write(f"  [5] 🥚 Uncommon Egg   - Cost: {p_egg2:<6} tokens  (Guarantees Uncommon+ egg)\n")
        sys.stdout.write(f"  [6] 🫐 Oran Berry     - Cost: 1.0M   tokens  (+25% Companion Happiness)\n")
        sys.stdout.write(f"  [7] 🍇 Golden Razz    - Cost: 5.0M   tokens  (Boosts next egg shiny odds to 1/24!)\n")
        sys.stdout.write(f"  [8] 🔮 Mega Stone     - Cost: 50.0M  tokens  (Mega Evolve eligible final forms!)\n\n")

        sys.stdout.write(f"  {BOLD}Your Bag (Type 'use <number>' to use, or 'sell <number> [qty]' to sell):{RESET}\n")
        sys.stdout.write(f"  [1] 🍬 Rare Candy: {inv.get('rare_candy', 0)} owned\n")
        sys.stdout.write(f"  [2] 🌿 Mint:       {inv.get('mint', 0)} owned\n")
        sys.stdout.write(f"  [3] 🫐 Oran Berry: {inv.get('berry_oran', 0)} owned\n")
        sys.stdout.write(f"  [4] 🍇 Golden Razz: {inv.get('berry_golden', 0)} owned\n")
        sys.stdout.write(f"  [5] 🔮 Mega Stone:  {inv.get('mega_stone', 0)} owned\n")
        sys.stdout.write(f"  [6] 🎫 Expedition Pass: {inv.get('expedition_pass', 0)} owned\n")
        sys.stdout.write(f"  [7] 🪈 Poké Flute:  {inv.get('poke_flute', 0)} owned\n")
        sys.stdout.write(f"  [8] 🌟 Master Ball: {inv.get('master_ball', 0)} owned\n")
        has_charm = "OWNED (Active)" if inv.get("shiny_charm", 0) > 0 else "Not owned"
        sys.stdout.write(f"  [+] ✨ Shiny Charm: {has_charm}\n\n")

    def handle_shop_buy(self, cmd: str):
        parts = cmd.split()
        choice = parts[1] if len(parts) > 1 else ""
        qty = 1
        if len(parts) >= 3:
            try:
                qty = int(parts[2])
            except ValueError:
                self.message = "Invalid quantity."
                return

        if choice == "1":
            ok, msg = self.engine.buy_item(ItemKind.RARE_CANDY, qty)
        elif choice == "2":
            ok, msg = self.engine.buy_item(ItemKind.MINT, qty)
        elif choice == "3":
            ok, msg = self.engine.buy_item(ItemKind.SHINY_CHARM, qty)
        elif choice == "4":
            if qty > 1:
                self.message = "You can only hold one egg!"
                return
            ok, msg = self.engine.buy_egg(None)
        elif choice == "5":
            if qty > 1:
                self.message = "You can only hold one egg!"
                return
            ok, msg = self.engine.buy_egg(Rarity.UNCOMMON)
        elif choice == "6":
            ok, msg = self.engine.buy_item(ItemKind.BERRY_ORAN, qty)
        elif choice == "7":
            ok, msg = self.engine.buy_item(ItemKind.BERRY_GOLDEN, qty)
        elif choice == "8":
            ok, msg = self.engine.buy_item(ItemKind.MEGA_STONE, qty)
        else:
            ok, msg = False, "Invalid shop selection."
        self.message = msg

    def handle_bag_use(self, cmd: str):
        parts = cmd.split()
        choice = parts[1] if len(parts) > 1 else ""
        qty = 1
        if len(parts) > 2:
            try:
                qty = int(parts[2])
            except ValueError:
                self.message = "Invalid quantity."
                return

        if choice == "1":
            ok, msg = self.engine.use_item(ItemKind.RARE_CANDY, qty)
        elif choice == "2":
            ok, msg = self.engine.use_item(ItemKind.MINT, qty)
        elif choice == "3":
            ok, msg = self.engine.use_item(ItemKind.BERRY_ORAN, qty)
        elif choice == "4":
            ok, msg = self.engine.use_item(ItemKind.BERRY_GOLDEN, qty)
        elif choice == "5":
            ok, msg = self.engine.use_item(ItemKind.MEGA_STONE, qty)
        elif choice == "6":
            ok, msg = self.engine.use_item(ItemKind.EXPEDITION_PASS, qty)
        elif choice == "7":
            ok, msg = self.engine.use_item(ItemKind.POKE_FLUTE, qty)
        elif choice == "8":
            ok, msg = self.engine.use_item(ItemKind.MASTER_BALL, qty)
        else:
            ok, msg = False, "Invalid bag selection."
        self.message = msg

    def handle_bag_sell(self, cmd: str):
        parts = cmd.split()
        choice = parts[1] if len(parts) > 1 else ""
        qty = 1
        if len(parts) >= 3:
            try:
                qty = int(parts[2])
            except ValueError:
                self.message = "Invalid quantity."
                return

        mapping = {
            "1": ItemKind.RARE_CANDY,
            "2": ItemKind.MINT,
            "3": ItemKind.BERRY_ORAN,
            "4": ItemKind.BERRY_GOLDEN,
            "5": ItemKind.MEGA_STONE,
            "6": ItemKind.EXPEDITION_PASS,
            "7": ItemKind.POKE_FLUTE,
            "8": ItemKind.MASTER_BALL,
        }
        item_kind = mapping.get(choice)
        if not item_kind:
            self.message = "Invalid bag selection."
            return

        inv = self.engine.state.get("inventory", {})
        if inv.get(item_kind.value, 0) < qty:
            self.message = f"You don't have {qty}x {item_kind.name_en} in your Bag to sell!"
            return

        cost = item_kind.price_for(self.engine.current_difficulty)
        sell_value = int(cost * 0.8) * qty

        sys.stdout.write(f"\n  {BOLD}{YELLOW}💰 SELL CONFIRMATION{RESET}\n")
        sys.stdout.write(f"  Are you sure you want to sell {qty}x {item_kind.name_en} ({item_kind.emoji}) for +{format_tokens(sell_value)} Tokens? (y/n)> ")
        sys.stdout.flush()
        
        ans = sys.stdin.readline().strip().lower()
        if ans in ["y", "yes"]:
            ok, msg = self.engine.sell_item(item_kind, qty)
            self.message = msg
        else:
            self.message = f"Canceled selling {qty}x {item_kind.name_en}."

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
        sys.stdout.write(f"  ➔ Type '{BOLD}send <ROW INDEX>|#<POKEMON INDEX> [area]{RESET}' to dispatch!\n\n")

        sys.stdout.write(f"  {BOLD}🗺️ Active Expeditions Status:{RESET}\n")
        if not expeditions:
            sys.stdout.write("   No companions currently on expedition.\n\n")
        else:
            for exp in expeditions:
                sp_id = exp["sp_id"]
                sp_name = self.engine.api.get_species_name(sp_id)
                area = exp["area"]
                sys.stdout.write(f"   • {BOLD}{CYAN}{sp_name} (#{sp_id}){RESET} @ {area}: {format_tokens(exp['progress'])} / {format_tokens(exp['target'])}\n")
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
        sys.stdout.write(f"  ➔ Step 2: Type '{BOLD}check{RESET}' to reveal community cards for free, or '{BOLD}fold{RESET}'\n")
        sys.stdout.write(f"  ➔ Step 3: Type '{BOLD}raise{RESET}' anytime to double your bet before the next card is revealed!\n")
        sys.stdout.write(f"  ➔ Note: You can raise multiple times in a single hand.\n\n")

        if self.engine.poker.player_hole:
            p_hole = " ".join([str(c) for c in self.engine.poker.player_hole])
            if self.engine.poker.game_state == "preflop":
                board = "[?] [?] [?] [?] [?]"
                d_hole = "[?] [?]"
                state_str = "Pre-Flop (Type 'check' to see Flop, 'raise' to double bet, or 'fold')"
            elif self.engine.poker.game_state == "flop":
                board = " ".join([str(c) for c in self.engine.poker.community_cards[:3]]) + " [?] [?]"
                d_hole = "[?] [?]"
                state_str = "The Flop (Type 'check' to see Turn, 'raise' to double bet, or 'fold')"
            elif self.engine.poker.game_state == "turn":
                board = " ".join([str(c) for c in self.engine.poker.community_cards[:4]]) + " [?]"
                d_hole = "[?] [?]"
                state_str = "The Turn (Type 'check' for Showdown, 'raise' to double bet, or 'fold')"
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

    def render_bank_tab(self):
        avail = self.engine.available_tokens
        bank = self.engine.state.get("bank_balance", 0)
        loan = self.engine.state.get("bank_loan", 0)
        loan_days = self.engine.state.get("loan_days_active", 0)

        sys.stdout.write(f"\n  {BOLD}{GREEN}🏦 Token Bank{RESET}  (Available Spendable Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET})\n\n")
        sys.stdout.write(f"  {BOLD}Deposited Balance:{RESET} {BOLD}{GREEN}{format_tokens(bank)}{RESET} tokens\n")
        sys.stdout.write(f"  {BOLD}Active Loan Debt:{RESET}  {BOLD}{RED}{format_tokens(loan)}{RESET} tokens\n")
        
        if loan > 0:
            sys.stdout.write(f"  {BOLD}{RED}🚨 Loan Deadline:{RESET} {loan_days}/7 days until repossession!\n")
            
        sys.stdout.write(f"\n  {BOLD}Interest Rates (Daily Compounding):{RESET}\n")
        sys.stdout.write(f"  • {GREEN}Deposits:{RESET} +5% interest\n")
        sys.stdout.write(f"  • {RED}Loans:{RESET}    -10% interest (Max Loan: 500.0M tokens)\n\n")
        sys.stdout.write(f"  {BOLD}Commands:{RESET}\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}deposit <amount>{RESET}' / '{BOLD}withdraw <amount>{RESET}' (e.g. 'deposit 1m')\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}loan <amount>{RESET}' / '{BOLD}payoff <amount>{RESET}' (e.g. 'payoff all')\n\n")

    def render_settings_tab(self):
        sys.stdout.write(f"\n  {BOLD}{CYAN}⚙️ Tracking & Application Settings{RESET}\n\n")
        sys.stdout.write(f"  [1] Reset Game Progress:       {BOLD}{RED}[DANGER]{RESET}\n")
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
