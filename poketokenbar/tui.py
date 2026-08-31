import os
import sys
import time
import random
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
        events = self.engine.process_usage(summary["total_tokens"], summary.get("active_days"))
        if events:
            self.message = "\n".join(events)

        while True:
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
                self.render_mega_evo_tab()
            elif self.current_tab == 9:
                self.render_game_corner_tab()
            elif self.current_tab == 10:
                self.render_bank_tab()
            elif self.current_tab == 11:
                self.render_settings_tab()
            elif self.current_tab == 12:
                from poketokenbar.tui_tabs.red import render_red_tab
                render_red_tab(self)

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
                elif cmd == "314159":
                    is_unlocked = not self.engine.state.get("dev_red_unlocked", False)
                    self.engine.state["dev_red_unlocked"] = is_unlocked
                    if not is_unlocked:
                        self.engine.state.pop("red_battle_state", None)
                    self.engine.save()
                    status = "UNLOCKED" if is_unlocked else "LOCKED (and reset)"
                    self.message = f"🔧 DEV MODE: Red Battle {status} 🔧"
                elif cmd == "314159+":
                    self.engine.state["spent_tokens"] = self.engine.state.get("spent_tokens", 0) - 1_000_000
                    st = self.engine.state.get("red_battle_state")
                    if st:
                        st["red_spent_tokens"] = st.get("red_spent_tokens", 0) - 1_000_000
                    self.engine.save()
                    self.message = "🔧 DEV MODE: Granted 1,000,000 Tokens! 🔧"
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
                    badges = self.engine.state.get("gym_badges", [])
                    unlocked = self.engine.state.get("dev_red_unlocked", False) or "🏆 Champion Badge" in badges
                    if unlocked:
                        self.current_tab = 12
                        self.message = ""
                    else:
                        self.message = "You must defeat the Champion to unlock this tab!"
                elif cmd.startswith("difficulty "):
                    # Placeholder for potential difficulty commands
                    pass
                elif cmd in ["r", "refresh"]:
                    summary = self.tracker.get_summary(force=True)
                    events = self.engine.process_usage(summary["total_tokens"])
                    if events:
                        self.message = "Refreshed logs!\n" + "\n".join(events)
                    else:
                        self.message = f"Refreshed usage logs! Total indexed: {format_tokens(summary['total_tokens'])} tokens."
                elif cmd in ["n", "next"] and self.current_tab in [2, 3, 4, 5, 8]:
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
                    else: self.roster_page += 1
                    self.message = ""
                elif cmd in ["p", "prev", "previous"] and self.current_tab in [2, 3, 4, 5, 8]:
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
                    else: self.roster_page = max(1, self.roster_page - 1)
                    self.message = ""
                elif cmd.startswith("page ") and self.current_tab in [2, 3, 4, 5, 8]:
                    try:
                        page = max(1, int(cmd.split()[1]))
                        if self.current_tab == 2: self.pokedex_page = page
                        elif self.current_tab == 4: self.shop_page = page
                        elif self.current_tab == 5: self.expedition_page = page
                        elif self.current_tab == 8: self.mega_page = page
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
                elif self.current_tab == 10 and cmd.startswith("blackjack"):
                    self.handle_bank_blackjack(cmd)
                elif self.current_tab == 12 and (cmd.startswith("assemble") or cmd.startswith("fight") or cmd.startswith("swap") or cmd == "run" or cmd == "restart"):
                    from poketokenbar.tui_tabs.red import handle_red_command
                    handle_red_command(self, cmd)
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
        
        badges = self.engine.state.get("gym_badges", [])
        unlocked = self.engine.state.get("dev_red_unlocked", False) or "🏆 Champion Badge" in badges
        t12 = f"{BOLD}{RED}[12] Red{RESET}" if self.current_tab == 12 else "[12] Red"
        t12_str = f"   {t12}" if unlocked else ""

        sys.stdout.write(f"  {t1}   {t2}     {t3}      {t4}\n")
        sys.stdout.write(f"  {t5} {t6}     {t7}      {t8}\n")
        sys.stdout.write(f"  {t9} {t10}       {t11}{t12_str}\n")
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
        from poketokenbar.tui_tabs.expeditions import render_expeditions_tab
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
        sys.stdout.write("-" * 72 + "\n")
        if self.message and not getattr(self, 'slot_animating', False):
            for line in self.message.split("\n"):
                if line.lstrip().startswith("➔"):
                    sys.stdout.write(f"  {GREEN}  {line.lstrip()}{RESET}\n")
                elif line.startswith("  "):
                    sys.stdout.write(f"  {GREEN}{line}{RESET}\n")
                else:
                    sys.stdout.write(f"  {GREEN}➔ {line}{RESET}\n")

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
