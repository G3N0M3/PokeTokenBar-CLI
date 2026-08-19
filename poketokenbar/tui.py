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
                    self.render_shop_tab()
                elif self.current_tab == 4:
                    self.render_monitor_tab(summary)
                elif self.current_tab == 5:
                    self.render_settings_tab()

                self.render_footer()

                interval = float(settings.get("refresh_interval", 3.0))
                auto_on = settings.get("auto_tracking_enabled", True)
                status_str = f"Auto: {'ON' if auto_on else 'OFF'} ({interval}s)"

                sys.stdout.write(f"\n{BOLD}Select tab (1-5), command, r=Refresh, q=Quit [{status_str}]: {RESET}")
                sys.stdout.flush()

                try:
                    import select
                    select_timeout = interval if auto_on else None
                    readable, _, _ = select.select([sys.stdin], [], [], select_timeout)
                    if readable:
                        cmd = sys.stdin.readline().strip().lower()
                        if cmd in ["q", "exit", "quit"]:
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
                        elif cmd in ["r", "refresh"]:
                            summary = self.tracker.get_summary()
                            events = self.engine.process_usage(summary["total_tokens"])
                            if events:
                                self.message = "Refreshed logs! " + " ".join(events)
                            else:
                                self.message = f"Refreshed usage logs! Total indexed: {format_tokens(summary['total_tokens'])} tokens."
                        elif cmd == "toggle" and self.current_tab == 5:
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
                        elif self.current_tab == 3 and cmd in ["buy 1", "buy 2", "buy 3", "buy 4", "buy 5"]:
                            self.handle_shop_buy(cmd)
                        elif self.current_tab == 3 and cmd in ["use 1", "use 2"]:
                            self.handle_bag_use(cmd)
                except KeyboardInterrupt:
                    print("\nExiting PokeTokenBar. Keep coding! 🐾")
                    break
        finally:
            self.auto_tracker.stop()

    def render_header(self, summary: dict):
        sys.stdout.write(f"{HEADER}========================================================================{RESET}\n")
        sys.stdout.write(f"{HEADER} ⚡ POKETOKENBAR — AI Token Pokémon Companion (Linux CLI Edition) 🐾 {RESET}\n")
        sys.stdout.write(f"{HEADER}========================================================================{RESET}\n\n")

    def render_tabs(self):
        t1 = f"{BOLD}{CYAN}[1] Companion{RESET}" if self.current_tab == 1 else "[1] Companion"
        t2 = f"{BOLD}{CYAN}[2] Pokédex{RESET}" if self.current_tab == 2 else "[2] Pokédex"
        t3 = f"{BOLD}{CYAN}[3] Shop & Bag{RESET}" if self.current_tab == 3 else "[3] Shop & Bag"
        t4 = f"{BOLD}{CYAN}[4] Live Monitor{RESET}" if self.current_tab == 4 else "[4] Live Monitor"
        t5 = f"{BOLD}{CYAN}[5] Settings{RESET}" if self.current_tab == 5 else "[5] Settings"
        sys.stdout.write(f"  {t1}   {t2}   {t3}   {t4}   {t5}\n")
        sys.stdout.write("------------------------------------------------------------------------\n")

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

            sys.stdout.write(f"\n  {BOLD}{GREEN}Active Companion: {shiny_str}{name} (#{sp_id}){RESET}\n")
            sys.stdout.write(f"  Rarity: {YELLOW}{active.rarity.value.upper()}{RESET}  |  Nature: {CYAN}{nature_name}{RESET}  |  Form: {active.stage_index+1}/{active.total_forms}\n")

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
                bar = format_progress_bar(target_xp, target_xp)
                next_id = active.path_ids[active.stage_index + 1]
                next_name = self.engine.api.get_species_name(next_id)
                sys.stdout.write(f"  Evolution to {next_name}: {bar} ({format_tokens(target_xp)} / {format_tokens(target_xp)}) {GREEN}[MAX / EVOLVED]{RESET}\n")
            elif active.stage_index < len(active.path_ids) - 1:
                bar = format_progress_bar(active.used_at_stage, target_xp)
                next_id = active.path_ids[active.stage_index + 1]
                next_name = self.engine.api.get_species_name(next_id)
                sys.stdout.write(f"  Evolution to {next_name}: {bar} ({format_tokens(active.used_at_stage)} / {format_tokens(target_xp)})\n")
            else:
                bar = format_progress_bar(active.used_at_stage, target_xp)
                sys.stdout.write(f"  Graduation to Pokédex: {bar} ({format_tokens(active.used_at_stage)} / {format_tokens(target_xp)})\n")

        sys.stdout.write("\n------------------------------------------------------------------------\n")
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

        # Show Incubating Egg option if present or active is None
        egg_usage = self.engine.state.get("egg_usage", 0)
        threshold = self.engine.current_difficulty.hatch_threshold
        pct = (egg_usage / threshold) * 100 if threshold > 0 else 0
        egg_badge = f"{BOLD}{GREEN}[ACTIVE / INCUBATING]{RESET}" if active is None else f"{BOLD}{YELLOW}[IN ROSTER]{RESET}"
        sys.stdout.write(f"   0. 🥚 {BOLD}Incubating Pokémon Egg{RESET} ({pct:.1f}%) {egg_badge}\n")

        if not dex:
            sys.stdout.write("\n  Your Pokédex is empty! Incubate and raise your Pokémon companions to fill it.\n\n")
        else:
            for idx, entry in enumerate(dex, 1):
                sp_id = entry.get("species_id", entry.get("final_id", entry.get("base_id")))
                name = self.engine.api.get_species_name(sp_id)
                shiny_str = f"{YELLOW}✨{RESET}" if entry.get("is_shiny") else ""
                rarity = entry.get("rarity", "common").upper()
                caught_at = entry.get("caught_at", "")[:10]
                status = entry.get("status", "graduated")
                if status == "active" and active is not None:
                    status_badge = f"{BOLD}{GREEN}[ACTIVE]{RESET}"
                elif status == "inactive":
                    status_badge = f"{BOLD}{YELLOW}[IN ROSTER]{RESET}"
                elif status == "evolved":
                    status_badge = f"{BOLD}{YELLOW}[EVOLVED]{RESET}"
                else:
                    status_badge = f"{BOLD}{CYAN}[GRADUATED]{RESET}"

                sys.stdout.write(f"  {idx:2d}. {shiny_str} {BOLD}{name}{RESET} (#{sp_id}) [{rarity}] {status_badge} - Discovered: {caught_at}\n")

        sys.stdout.write(f"\n  ➔ Type '{BOLD}select <number>{RESET}' or '{BOLD}select egg{RESET}' to make a Pokémon or Egg your active companion!\n\n")

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
        sys.stdout.write(f"  [4] 🥚 Pokémon Egg    - Cost: {p_egg1:<6} tokens  (Incubate new egg & save act. mon)\n")
        sys.stdout.write(f"  [5] 🥚 Uncommon Egg   - Cost: {p_egg2:<6} tokens  (Guarantees Uncommon+ egg & save act. mon)\n\n")

        sys.stdout.write(f"  {BOLD}Your Bag (Type 'use <number>' to use):{RESET}\n")
        sys.stdout.write(f"  [1] 🍬 Rare Candy: {inv.get('rare_candy', 0)} owned\n")
        sys.stdout.write(f"  [2] 🌿 Mint:       {inv.get('mint', 0)} owned\n")
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
        else:
            ok, msg = False, "Invalid shop selection."
        self.message = msg

    def handle_bag_use(self, cmd: str):
        choice = cmd.split()[-1]
        if choice == "1":
            ok, msg = self.engine.use_item(ItemKind.RARE_CANDY)
        elif choice == "2":
            ok, msg = self.engine.use_item(ItemKind.MINT)
        else:
            ok, msg = False, "Invalid bag selection."
        self.message = msg

    def render_monitor_tab(self, summary: dict):
        sys.stdout.write(f"\n  {BOLD}{CYAN}📡 Live Token Usage Monitor{RESET}\n\n")
        sys.stdout.write(f"  Active Log Sources Detected:\n")
        sys.stdout.write(f"   • Antigravity CLI (~/.gemini/antigravity-cli/conversations/*.db)\n")
        sys.stdout.write(f"   • Gemini CLI      (~/.gemini/tmp/**/chats/*.json*)\n")
        sys.stdout.write(f"   • Claude Code     (~/.claude/projects/**/*.jsonl)\n\n")
        sys.stdout.write(f"  Current Burn Rate: {BOLD}{YELLOW}{format_tokens(summary['burn_rate_tpm'])} tokens/minute{RESET}\n")
        sys.stdout.write(f"  Total Indexed Calls: {summary['total_entries']:,}\n")
        sys.stdout.write(f"  Last Scan Timestamp: {summary['last_updated'].strftime('%H:%M:%S')}\n\n")

    def render_settings_tab(self):
        settings = self.engine.get_settings()
        enabled = settings.get("auto_tracking_enabled", True)
        interval = float(settings.get("refresh_interval", 3.0))

        status_badge = f"{BOLD}{GREEN}[ON / ENABLED]{RESET}" if enabled else f"{BOLD}{RED}[OFF / DISABLED]{RESET}"

        sys.stdout.write(f"\n  {BOLD}{CYAN}⚙️ Tracking & Application Settings{RESET}\n\n")
        sys.stdout.write(f"  [1] Automatic Token Tracking: {status_badge}\n")
        sys.stdout.write(f"      ➔ Type '{BOLD}toggle{RESET}' or '{BOLD}track{RESET}' to switch ON/OFF\n\n")
        sys.stdout.write(f"  [2] Auto-Refresh Interval:    {BOLD}{YELLOW}{interval} seconds{RESET}\n")
        sys.stdout.write(f"      ➔ Type '{BOLD}interval <seconds>{RESET}' to change (e.g. 'interval 5' or 'interval 1')\n\n")

    def render_footer(self):
        if self.message:
            sys.stdout.write(f"\n  {GREEN}➔ {self.message}{RESET}\n")

def main():
    tui = PokeTokenBarTUI()
    tui.run()

if __name__ == "__main__":
    main()
