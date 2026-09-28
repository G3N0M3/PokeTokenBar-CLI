"""Command routing and input dispatch engine for PokeTokenBar TUI."""

import math
from poketokenbar.utils.formatting import format_tokens
from poketokenbar.tui.modals.confirmations import handle_pending_confirmation


class CommandRouter:
    """Dispatches user terminal inputs to active modals, submodes, or tab handlers."""

    @staticmethod
    def dispatch(app, cmd: str) -> None:
        """Main command dispatch entrypoint."""
        # 1. Staged Confirmations
        if handle_pending_confirmation(app, cmd):
            return

        # 2. Interactive Expedition Picker Mode
        if getattr(app, "expedition_picker_mode", False):
            CommandRouter._handle_expedition_picker(app, cmd)
            return

        # 3. Submode 'back' exits
        if app.current_tab == 10 and getattr(app, "bank_subtab", "") == "stocks" and getattr(app, "stock_terminal", None) and cmd == "back":
            app.stock_terminal = None
            app.message = "Returned to Exchange Board."
            return
        if app.current_tab == 9 and getattr(app, "minigame_state", "menu") == "grunt_bribe" and cmd == "back":
            app.minigame_state = "slot"
            app.message = "You stepped away from the suspicious poster."
            return
        if app.current_tab == 9 and getattr(app, "minigame_state", "menu") != "menu" and cmd == "back":
            app.minigame_state = "menu"
            app.message = "Returned to Game Corner menu."
            return

        # 4. Secret developer Easter Egg
        if cmd == "250220":
            app.engine.state["spent_tokens"] = app.engine.state.get("spent_tokens", 0) - 50_000_000
            app.engine.save()
            app.message = "🎉 EASTER EGG UNLOCKED! Granted 50.0M Tokens! 🎉"
            return

        # 5. Direct tab switching (1-11 or 1-12)
        tab_max = 12 if app.engine.state.get("rocket_story_unlocked") else 11
        if cmd in [str(i) for i in range(1, tab_max + 1)]:
            app.expedition_picker_mode = False
            app.stock_terminal = None
            app.black_market_session = False
            if getattr(app, "shop_view", "normal") == "black_market":
                app.shop_view = "normal"
            app.current_tab = int(cmd)
            app.message = ""
            return

        # 6. Global telemetry refresh ('r')
        if cmd == "r":
            summary = app.tracker.get_summary(force=True)
            app.engine.process_usage(summary.get("raw_total_tokens", summary["total_tokens"]), summary.get("active_days"))
            app.message = f"Refreshed usage logs! Total indexed: {format_tokens(summary['total_tokens'])} tokens."
            return

        # 7. Global table pagination ('n', 'p', 'page <N>')
        if CommandRouter._handle_pagination(app, cmd):
            return

        # 8. Settings commands
        if CommandRouter._handle_settings_commands(app, cmd):
            return

        # 9. Global companion feeding & selection commands
        if cmd in ["pick", "picker"]:
            app.expedition_picker_mode = True
            app.current_tab = 5
            app.message = "Opened Expedition Dispatcher."
            return

        if cmd == "clear" and app.selected_expedition_targets:
            app.selected_expedition_targets.clear()
            app.message = "Cleared all selected companions."
            return

        if cmd.startswith("feed ") or cmd == "feed":
            app.handle_feed_command(cmd)
            return

        if cmd.startswith("sel ") or cmd == "sel":
            arg = cmd.split(maxsplit=1)[1].strip() if " " in cmd else ""
            if not arg:
                app.message = "Usage: sel <row>|#<dex>|egg to switch active companion"
            elif arg.lower() == "egg":
                ok, msg = app.engine.select_active_from_dex("egg")
                app.message = msg
            else:
                ok, msg = app.engine.select_active_from_dex(arg)
                app.message = msg
            return

        if cmd.startswith("claim"):
            parts = cmd.split()
            if app.current_tab == 10 and getattr(app, "bank_subtab", "") == "cd":
                target = parts[1] if len(parts) >= 2 else "all"
                ok, msg = app.engine.claim_cd(target)
                app.message = msg
            elif app.current_tab == 12:
                from poketokenbar.tui_tabs.rocket import handle_rocket_command
                handle_rocket_command(app, cmd)
            else:
                ok, msg = app.engine.claim_quest_reward(parts[-1] if len(parts) >= 2 else "all")
                app.message = msg
            return

        if cmd.startswith("send"):
            CommandRouter._handle_send_command(app, cmd)
            return

        if cmd.startswith("pass") and app.current_tab == 5:
            parts = cmd.split()
            if len(parts) >= 2:
                ok, msg = app.engine.use_expedition_pass(parts[1])
                app.message = msg
            else:
                app.message = "Usage: pass <idx>"
            return

        # 10. Game Corner minigames commands
        if CommandRouter._handle_game_corner_commands(app, cmd):
            return

        # 11. Profile trainer card
        if cmd == "card":
            app.message = app.engine.generate_trainer_card()
            return

        # 12. Bank & Stock commands
        if CommandRouter._handle_bank_commands(app, cmd):
            return

        # 13. Black Market access & exit
        if cmd == "black":
            bm = app.engine.get_or_init_black_market()
            if bm.get("natural_open") or getattr(app, "black_market_session", False):
                app.current_tab = 4
                app.shop_view = "black_market"
                app.message = ""
            else:
                app.message = "The back alley door is bolted shut from the inside."
            return

        if app.current_tab == 4 and getattr(app, "shop_view", "normal") == "black_market" and cmd == "back":
            if getattr(app, "black_market_session", False):
                app.black_market_session = False
                app.current_tab = 9
                app.minigame_state = "slot"
                app.shop_view = "normal"
                app.message = "Returned to the Game Corner slot machines."
            else:
                app.shop_view = "normal"
                app.message = ""
            return

        # 14. Tab 6 Mt. Silver Battles
        if app.current_tab == 6:
            if cmd.startswith("assemble ") or cmd in ["fight 1", "fight 2", "fight 3", "fight 4", "run", "restart"] or cmd.startswith("swap "):
                from poketokenbar.tui_tabs.red import handle_red_command
                handle_red_command(app, cmd)
            else:
                app.message = "Invalid command. Type a tab number (1-11), or battle command (assemble, fight, swap, run, restart)."
            return

        # 15. Rocket Armory global use commands
        if cmd == "use catalyst" or cmd.startswith("use catalyst"):
            ok, msg = app.engine.use_rocket_armory_item("catalyst")
            app.message = msg
            return
        if cmd == "use mist" or cmd.startswith("use mist") or cmd in ["use spray", "use morale mist"]:
            ok, msg = app.engine.use_rocket_armory_item("spray")
            app.message = msg
            return
        if cmd == "use chrono" or cmd.startswith("use chrono"):
            ok, msg = app.engine.use_rocket_armory_item("chrono")
            app.message = msg
            return

        # 16. Tab 4 Shop & Bag commands
        if app.current_tab == 4:
            if cmd.startswith("buy"):
                app.handle_shop_buy(cmd)
                return
            if cmd.startswith("use") or cmd.startswith("unequip"):
                app.handle_bag_use(cmd)
                return
            if cmd.startswith("sell"):
                app.handle_bag_sell(cmd)
                return
            if cmd in ["help", "info", "desc"] or cmd.startswith("help ") or cmd.startswith("info ") or cmd.startswith("desc "):
                app.handle_bag_help(cmd)
                return

        # 17. Tab 8 Mega Evolution commands
        if app.current_tab == 8:
            if cmd.startswith("use"):
                parts = cmd.split()
                if len(parts) > 1:
                    target = parts[1]
                    if hasattr(app, "mega_stone_map") and target in app.mega_stone_map:
                        active = app.engine.active_mon
                        if active and active.is_mega:
                            ok, msg = False, "Already Mega Evolved! Type 'revert' to return to standard form."
                        else:
                            ok, msg = app.engine.toggle_mega_evolution(app.mega_stone_map[target])
                    else:
                        ok, msg = False, "Invalid stone number!"
                else:
                    ok, msg = False, "Usage: use <number>"
                app.message = msg
                return
            if cmd == "revert":
                active = app.engine.active_mon
                if active and active.is_mega:
                    ok, msg = app.engine.toggle_mega_evolution(force_revert=True)
                elif active:
                    ok, msg = False, "Companion is not Mega Evolved!"
                else:
                    ok, msg = False, "No active companion to revert!"
                app.message = msg
                return

        # 18. Banking checking transactions
        if cmd.startswith("deposit") or cmd.startswith("withdraw") or cmd.startswith("loan") or cmd.startswith("payoff"):
            parts = cmd.split()
            if len(parts) >= 2:
                action = parts[0]
                amount_str = parts[1]
                ok, msg = app.engine.handle_bank_transaction(action, amount_str)
                app.message = msg
            else:
                app.message = "Usage: deposit, withdraw, loan, or payoff <amount>"
            return

        # 19. Team Rocket courier delivery
        if app.engine.state.get("pending_authority_delivery") and cmd in ["keep", "dismiss"]:
            ok, msg = app.engine.handle_authority_delivery(cmd)
            app.message = msg
            return

        # 20. Tab 12 Rocket HQ commands
        if app.current_tab == 12:
            from poketokenbar.tui_tabs.rocket import handle_rocket_command
            handle_rocket_command(app, cmd)
            return

    @staticmethod
    def _handle_expedition_picker(app, cmd: str) -> None:
        if cmd == "back":
            app.expedition_picker_mode = False
            app.message = "Exited Expedition Dispatcher."
        elif cmd in ["n", "next"]:
            dex = app.engine.state.get("dex", [])
            roster = [d for d in dex if d.get("status") != "evolved"]
            page_size = 8
            total_pages = max(1, math.ceil(len(roster) / page_size))
            if getattr(app, "picker_page", 1) < total_pages:
                app.picker_page = getattr(app, "picker_page", 1) + 1
            else:
                app.message = f"Already on the last page ({total_pages})."
        elif cmd in ["p", "prev"]:
            if getattr(app, "picker_page", 1) > 1:
                app.picker_page = getattr(app, "picker_page", 1) - 1
            else:
                app.message = "Already on page 1."
        elif cmd.startswith("page "):
            try:
                target_p = int(cmd.split()[1])
                dex = app.engine.state.get("dex", [])
                roster = [d for d in dex if d.get("status") != "evolved"]
                page_size = 8
                total_pages = max(1, math.ceil(len(roster) / page_size))
                if 1 <= target_p <= total_pages:
                    app.picker_page = target_p
                else:
                    app.message = f"Invalid page. Must be between 1 and {total_pages}."
            except ValueError:
                app.message = "Usage: page <number>"
        elif cmd == "clear":
            app.selected_expedition_targets.clear()
            app.message = "Cleared all selected companions."
        elif cmd == "all":
            indices = app._parse_indices_string("all")
            app._toggle_selection_indices(indices)
        elif cmd.startswith("feed ") or cmd == "feed":
            app.handle_feed_command(cmd)
        elif app._is_expedition_destination_cmd(cmd):
            area = app._resolve_expedition_destination(cmd)
            if not app.selected_expedition_targets:
                app.message = f"No companions selected! Enter row numbers (e.g. '1 2 3') first before choosing destination '{area}'."
            else:
                target_list = [str(i) for i in sorted(app.selected_expedition_targets)]
                ok, msg = app.engine.dispatch_expedition(target_list, area)
                if ok:
                    app.selected_expedition_targets.clear()
                    app.expedition_picker_mode = False
                app.message = msg
        else:
            clean_cmd = cmd.replace("toggle", "").replace("pick", "").replace("select", "").strip()
            indices = app._parse_indices_string(clean_cmd)
            if indices:
                app._toggle_selection_indices(indices)
            else:
                app.message = "Enter row numbers to toggle, destination ('viridian', 'mine', etc.) to launch, or 'back' to exit."

    @staticmethod
    def _handle_pagination(app, cmd: str) -> bool:
        paginated_tabs = [2, 3, 4, 5, 8, 11]
        is_paginated = (
            app.current_tab in paginated_tabs
            or (app.current_tab == 10 and getattr(app, "bank_subtab", "") in ["stocks", "cd"])
            or (app.current_tab == 12 and getattr(app, "rocket_subview", "ops") == "intel")
        )
        if not is_paginated:
            return False

        if cmd in ["n", "next"]:
            if app.current_tab == 2: app.pokedex_page += 1
            elif app.current_tab == 4:
                if not hasattr(app, "shop_page"): app.shop_page = 1
                app.shop_page += 1
            elif app.current_tab == 5:
                if not hasattr(app, "expedition_page"): app.expedition_page = 1
                app.expedition_page += 1
            elif app.current_tab == 8:
                if not hasattr(app, "mega_page"): app.mega_page = 1
                app.mega_page += 1
            elif app.current_tab == 10:
                if getattr(app, "bank_subtab", "") == "cd":
                    if not hasattr(app, "cd_page"): app.cd_page = 1
                    app.cd_page += 1
                else:
                    if not hasattr(app, "stock_page"): app.stock_page = 1
                    app.stock_page += 1
            elif app.current_tab == 11:
                if not hasattr(app, "settings_page"): app.settings_page = 1
                app.settings_page += 1
            elif app.current_tab == 12:
                if not hasattr(app, "intel_page"): app.intel_page = 1
                app.intel_page += 1
            else:
                app.roster_page += 1
            app.message = ""
            return True

        if cmd in ["p", "prev"]:
            if app.current_tab == 2: app.pokedex_page = max(1, app.pokedex_page - 1)
            elif app.current_tab == 4:
                if not hasattr(app, "shop_page"): app.shop_page = 1
                app.shop_page = max(1, app.shop_page - 1)
            elif app.current_tab == 5:
                if not hasattr(app, "expedition_page"): app.expedition_page = 1
                app.expedition_page = max(1, app.expedition_page - 1)
            elif app.current_tab == 8:
                if not hasattr(app, "mega_page"): app.mega_page = 1
                app.mega_page = max(1, app.mega_page - 1)
            elif app.current_tab == 10:
                if getattr(app, "bank_subtab", "") == "cd":
                    if not hasattr(app, "cd_page"): app.cd_page = 1
                    app.cd_page = max(1, app.cd_page - 1)
                else:
                    if not hasattr(app, "stock_page"): app.stock_page = 1
                    app.stock_page = max(1, app.stock_page - 1)
            elif app.current_tab == 11:
                if not hasattr(app, "settings_page"): app.settings_page = 1
                app.settings_page = max(1, app.settings_page - 1)
            elif app.current_tab == 12:
                if not hasattr(app, "intel_page"): app.intel_page = 1
                app.intel_page = max(1, app.intel_page - 1)
            else:
                app.roster_page = max(1, app.roster_page - 1)
            app.message = ""
            return True

        if cmd.startswith("page "):
            try:
                page = max(1, int(cmd.split()[1]))
                if app.current_tab == 2: app.pokedex_page = page
                elif app.current_tab == 4: app.shop_page = page
                elif app.current_tab == 5: app.expedition_page = page
                elif app.current_tab == 8: app.mega_page = page
                elif app.current_tab == 10:
                    if getattr(app, "bank_subtab", "") == "cd":
                        app.cd_page = page
                    else:
                        app.stock_page = page
                elif app.current_tab == 11:
                    app.settings_page = page
                elif app.current_tab == 12:
                    app.intel_page = page
                else:
                    app.roster_page = page
                app.message = ""
            except ValueError:
                app.message = "Usage: page <number>"
            return True

        return False

    @staticmethod
    def _handle_settings_commands(app, cmd: str) -> bool:
        if cmd.startswith("pagesize ") and app.current_tab == 11:
            parts = cmd.split()
            if len(parts) >= 3:
                target, size_str = parts[1], parts[2]
                try:
                    val = int(size_str)
                    if target == "dex":
                        app.engine.state["page_size_pokedex"] = val
                        app.message = f"Pokédex page size set to {val}."
                    elif target == "roster":
                        app.engine.state["page_size_roster"] = val
                        app.message = f"Roster page size set to {val}."
                    elif target in ["exp", "expeditions"]:
                        app.engine.state["page_size_expedition"] = val
                        app.message = f"Expeditions page size set to {val}."
                    elif target == "bag":
                        app.engine.state["page_size_bag"] = val
                        app.message = f"Bag page size set to {val}."
                    elif target == "mega":
                        app.engine.state["page_size_mega"] = val
                        app.message = f"Mega Evo page size set to {val}."
                    elif target in ["cd", "deposits"]:
                        app.engine.state["page_size_cd"] = val
                        app.message = f"Term Deposits page size set to {val}."
                    elif target in ["settings", "setting", "set"]:
                        if val < 1:
                            app.message = "Settings page size must be at least 1."
                        else:
                            app.engine.state["page_size_settings"] = val
                            app.message = f"Settings page size set to {val}."
                    else:
                        app.message = "Usage: pagesize <dex|roster|exp|bag|mega|cd|settings> <number>"
                    app.engine.save()
                except ValueError:
                    app.message = "Invalid size. Usage: pagesize <dex|roster|exp|bag|mega|cd|settings> <number>"
            return True

        if cmd.startswith("billing ") or cmd.startswith("cycle "):
            parts = cmd.split()
            if len(parts) >= 2:
                try:
                    day = int(parts[1])
                    ok, msg = app.engine.set_billing_cycle_day(day)
                    app.message = msg
                    if ok:
                        app.tracker.get_summary(force=True)
                except ValueError:
                    app.message = "Usage: billing <1-31> (day of month for billing cycle start)"
            else:
                app.message = "Usage: billing <1-31>"
            return True

        if cmd in ["tokens init", "token init"]:
            summary = app.tracker.get_summary(force=True)
            raw_total = summary.get("raw_total_tokens", summary.get("total_tokens", 0))
            ok, msg = app.engine.initialize_total_tokens(raw_total)
            app.message = msg
            if ok:
                app.tracker.get_summary(force=True)
            return True

        if cmd in ["tokens clear", "token clear"]:
            ok, msg = app.engine.clear_total_tokens_baseline()
            app.message = msg
            if ok:
                app.tracker.get_summary(force=True)
            return True

        if cmd == "reset" and app.current_tab == 11:
            app.pending_reset = True
            app.message = "⚠️ CONFIRMATION REQUIRED: Type 'RESET ALL' to wipe progress & restart fresh, or anything else to cancel!"
            return True

        if cmd.startswith("rocket init") or cmd.startswith("init rocket") or (app.current_tab == 11 and cmd in ["rocket reset", "reset rocket", "rocket"]):
            if "--force" in cmd or not app.engine.state.get("rocket_story_unlocked", False):
                ok, msg = app.engine.initialize_rocket_process()
                app.message = f"🚀 {msg}"
            else:
                app.pending_rocket_init = True
                app.message = "⚠️ CONFIRM: Type 'CONFIRM' to reset Team Rocket back to Op 1, or anything else to cancel!"
            return True

        if cmd.startswith("size") and app.current_tab == 11:
            parts = cmd.split()
            if len(parts) == 2 and parts[1].isdigit():
                new_size = int(parts[1])
                if 10 <= new_size <= 72:
                    app.engine.state["sprite_size"] = new_size
                    app.engine.save()
                    app.message = f"Sprite resolution set to {new_size} columns!"
                else:
                    app.message = "Sprite size must be between 10 and 72."
            else:
                app.message = "Usage: size <number> (e.g. 'size 30')"
            return True

        return False

    @staticmethod
    def _handle_send_command(app, cmd: str) -> None:
        cmd_body = cmd.split(maxsplit=1)[1] if " " in cmd else ""
        if not cmd_body:
            if app.selected_expedition_targets:
                app.message = f"{len(app.selected_expedition_targets)} companion(s) selected! Type: 'send viridian', 'send mine', etc."
            else:
                app.message = "Usage: send <rows|all> <area> (or 'pick' to open picker)"
        else:
            clean_body = cmd_body.strip().lower()
            if app.selected_expedition_targets and app._is_expedition_destination_cmd(clean_body):
                area = app._resolve_expedition_destination(clean_body)
                target_list = [str(i) for i in sorted(app.selected_expedition_targets)]
                ok, msg = app.engine.dispatch_expedition(target_list, area)
                if ok:
                    app.selected_expedition_targets.clear()
                app.message = msg
            else:
                targets, area = app._parse_send_args(cmd_body)
                ok, msg = app.engine.dispatch_expedition(targets, area)
                app.message = msg

    @staticmethod
    def _handle_game_corner_commands(app, cmd: str) -> bool:
        if cmd.startswith("play ") or (app.current_tab == 9 and cmd == "play"):
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
                    app.minigame_state = game_map[game]
                    app.message = ""
                else:
                    app.message = "Game not found! Type 'play <1-8>' (e.g. 'play 1' to 'play 8')."
            else:
                app.message = "Usage: play <idx> (e.g. 'play 1' to 'play 8')"
            return True

        if app.current_tab == 9 and getattr(app, "minigame_state", "menu") in ["slot", "menu"] and cmd == "poster":
            if app.engine.state.get("permanent_black_market", False):
                ok, msg = app.engine.bribe_grunt_for_black_market()
                app.minigame_state = "menu"
                app.black_market_session = True
                app.current_tab = 4
                app.shop_view = "black_market"
                app.message = "📯 Syndicate Black Pass recognized! You click the secret switch behind the poster and enter the Black Market directly!"
            elif getattr(app, "minigame_state", "menu") == "slot":
                app.minigame_state = "grunt_bribe"
                app.message = ""
            else:
                app.message = "There's a suspicious poster near the Token Slots! (Type 'play 3')"
            return True

        if app.current_tab == 9 and getattr(app, "minigame_state", "menu") == "grunt_bribe" and cmd in ["bribe", "enter"]:
            ok, msg = app.engine.bribe_grunt_for_black_market()
            if ok:
                app.minigame_state = "menu"
                app.black_market_session = True
                app.current_tab = 4
                app.shop_view = "black_market"
            app.message = msg
            return True

        if cmd.startswith("bet"):
            parts = cmd.split()
            if len(parts) >= 2:
                mg_state = getattr(app, "minigame_state", "menu")
                if mg_state == "poker":
                    ok, msg = app.engine.play_poker_bet(parts[1])
                elif mg_state == "blackjack":
                    ok, msg = app.engine.play_blackjack_bet(parts[1])
                elif mg_state == "voltorb":
                    lvl = None
                    if len(parts) >= 3:
                        if parts[2].isdigit():
                            lvl = int(parts[2])
                        else:
                            app.message = "Invalid level! Usage: bet <amount> [level 1-8] (e.g. 'bet 500k 3')"
                            return True
                    ok, msg = app.engine.play_voltorb_bet(parts[1], lvl)
                elif mg_state == "trivia":
                    ok, msg = app.engine.play_trivia_start(parts[1])
                elif mg_state == "derby":
                    if len(parts) >= 3:
                        ok, msg = app.engine.play_derby_bet(parts[1], parts[2])
                    else:
                        ok, msg = False, "Usage: bet <lane 1-4> <amount> (e.g. 'bet 1 500k')"
                elif mg_state == "excavator":
                    ok, msg = False, "Excavation has a fixed cost of 500K tokens. Type 'dig' to start!"
                else:
                    ok, msg = False, "You must open a Game Corner game to bet!"
                app.message = msg
            else:
                if getattr(app, "minigame_state", "menu") == "voltorb":
                    app.message = "Usage: bet <amount> [level 1-8] (e.g. 'bet 500k', 'bet 1m 5')"
                else:
                    app.message = "Usage: bet <amount> (e.g. 'bet 500k', 'bet 1m')"
            return True

        if cmd.startswith("spin") and getattr(app, "minigame_state", "menu") == "slot":
            parts = cmd.split()
            if len(parts) >= 2:
                ok, msg = app.engine.play_slots(parts[1])
                if ok:
                    app.animate_slot_spin(app.engine.slots.last_reels)
                app.message = msg
            else:
                app.message = "Usage: spin <amount> (e.g. 'spin 500k')"
            return True

        if cmd in ["check", "raise", "fold", "allin"] and getattr(app, "minigame_state", "menu") == "poker":
            ok, msg = app.engine.play_poker_hold(cmd)
            app.message = msg
            return True

        if cmd in ["hit", "stand", "double"] and getattr(app, "minigame_state", "menu") == "blackjack":
            ok, msg = app.engine.play_blackjack_action(cmd)
            app.message = msg
            return True

        if cmd.startswith("flip ") and getattr(app, "minigame_state", "menu") == "voltorb":
            parts = cmd.split()
            if len(parts) >= 3:
                ok, msg = app.engine.play_voltorb_flip(parts[1], parts[2])
                app.message = msg
            else:
                app.message = "Usage: flip <row 1-5> <col 1-5> (e.g. 'flip 1 3')"
            return True

        if cmd.startswith("memo ") and getattr(app, "minigame_state", "menu") == "voltorb":
            parts = cmd.split()
            if len(parts) >= 3:
                note = parts[3] if len(parts) >= 4 else ""
                ok, msg = app.engine.play_voltorb_memo(parts[1], parts[2], note)
                app.message = msg
            else:
                app.message = "Usage: memo <row 1-5> <col 1-5> [note]"
            return True

        if cmd == "cashout" and getattr(app, "minigame_state", "menu") == "voltorb":
            ok, msg = app.engine.play_voltorb_cashout()
            app.message = msg
            return True

        if cmd.startswith("pick ") and getattr(app, "minigame_state", "menu") == "excavator":
            parts = cmd.split()
            if len(parts) >= 3:
                ok, msg = app.engine.play_excavator_pick(parts[1], parts[2])
                app.message = msg
            else:
                app.message = "Usage: pick <row 1-6> <col 1-9> (e.g. 'pick 2 4')"
            return True

        if cmd.startswith("hammer ") and getattr(app, "minigame_state", "menu") == "excavator":
            parts = cmd.split()
            if len(parts) >= 3:
                ok, msg = app.engine.play_excavator_hammer(parts[1], parts[2])
                app.message = msg
            else:
                app.message = "Usage: hammer <row 1-6> <col 1-9> (e.g. 'hammer 3 5')"
            return True

        if (cmd == "dig" or cmd.startswith("dig ")) and getattr(app, "minigame_state", "menu") == "excavator":
            parts = cmd.split()
            if len(parts) > 1:
                app.message = "Excavation has a fixed cost of 500K tokens. Type 'dig' to start!"
            else:
                ok, msg = app.engine.play_excavator_start()
                app.message = msg
            return True

        if cmd.startswith("guess ") and getattr(app, "minigame_state", "menu") == "trivia":
            guess_str = cmd.split(maxsplit=1)[1].strip() if len(cmd.split()) > 1 else ""
            ok, msg = app.engine.play_trivia_guess(guess_str)
            app.message = msg
            return True

        if cmd == "hint" and getattr(app, "minigame_state", "menu") == "trivia":
            ok, msg = app.engine.play_trivia_hint()
            app.message = msg
            return True

        if cmd == "giveup" and getattr(app, "minigame_state", "menu") == "trivia":
            ok, msg = app.engine.play_trivia_pass()
            app.message = msg
            return True

        if cmd == "race" and getattr(app, "minigame_state", "menu") == "derby":
            if app.engine.derby.game_state == "bet_placed":
                frames = app.engine.derby.simulate_race()
                app.animate_derby_race(frames)
                ok, msg = app.engine.play_derby_race()
                app.message = "" if ok else msg
            else:
                app.message = "Place a bet first! Type 'bet <lane 1-4> <amount>'."
            return True

        if cmd == "start" and getattr(app, "minigame_state", "menu") == "derby":
            app.message = "Use 'race' to launch the derby race!"
            return True

        if cmd.startswith("pull"):
            parts = cmd.split()
            pull_type = parts[1] if len(parts) >= 2 else "1"
            ok, msg = app.engine.play_gacha(pull_type)
            app.message = msg
            return True

        return False

    @staticmethod
    def _handle_bank_commands(app, cmd: str) -> bool:
        if app.current_tab == 10 and cmd == "b":
            app.bank_subtab = "checking"
            app.stock_terminal = None
            app.message = ""
            return True

        if app.current_tab == 10 and cmd == "c":
            app.bank_subtab = "cd"
            app.stock_terminal = None
            app.message = ""
            return True

        if app.current_tab == 10 and cmd == "s" and not getattr(app, "stock_terminal", None):
            app.bank_subtab = "stocks"
            app.stock_terminal = None
            app.message = ""
            return True

        if app.current_tab == 10 and getattr(app, "bank_subtab", "") == "stocks" and getattr(app, "stock_terminal", None):
            if cmd.startswith("buy ") or cmd == "buy":
                app.handle_stock_terminal_buy(cmd)
                return True
            if cmd.startswith("sell ") or cmd == "sell":
                parts = cmd.split()
                shares = parts[1] if len(parts) >= 2 else "1"
                ok, msg = app.engine.divest_corporate(app.stock_terminal, shares)
                app.message = msg
                return True

        if app.current_tab == 10 and getattr(app, "bank_subtab", "") == "stocks" and (cmd.startswith("stock ") or cmd == "stock"):
            from poketokenbar.game.models import CORPORATIONS
            parts = cmd.split()
            if len(parts) >= 2:
                target = parts[1]
                if target.isdigit():
                    c_keys = list(CORPORATIONS.keys())
                    idx = int(target) - 1
                    key = c_keys[idx] if 0 <= idx < len(c_keys) else None
                else:
                    key = app.engine._resolve_corp_key(target)
                if key:
                    app.stock_terminal = key
                    app.message = f"Opened {CORPORATIONS[key].ticker} Trade Terminal."
                else:
                    app.message = f"Unknown stock code '{target}'!"
            else:
                app.message = "Usage: stock <idx|code> (e.g. 'stock 1' or 'stock SILPH')"
            return True

        if cmd.startswith("cd "):
            parts = cmd.split()
            action = parts[1] if len(parts) > 1 else ""
            if action == "open" and len(parts) >= 4:
                try:
                    days = int(parts[3])
                    ok, msg = app.engine.open_cd(parts[2], days)
                except ValueError:
                    ok, msg = False, "Term days must be 3, 7, or 14. E.g. 'cd open 10m 7'"
            elif action == "claim":
                target = parts[2] if len(parts) >= 3 else "all"
                ok, msg = app.engine.claim_cd(target)
            elif action == "break" and len(parts) >= 3:
                ok, msg = app.engine.break_cd(parts[2])
            elif action == "sort" and len(parts) >= 3:
                ok, msg = app.engine.set_cd_sort_criteria(parts[2])
            else:
                ok, msg = False, "CD Usage: 'cd open <amt> <3|7|14>', 'cd claim <id|all>', 'cd break <id>', or 'cd sort <days|amount|term>'"
            app.message = msg
            return True

        if app.current_tab == 10 and getattr(app, "bank_subtab", "") == "cd":
            if cmd.startswith("open "):
                parts = cmd.split()
                if len(parts) >= 3:
                    try:
                        days = int(parts[2])
                        ok, msg = app.engine.open_cd(parts[1], days)
                    except ValueError:
                        ok, msg = False, "Term days must be 3, 7, or 14. E.g. 'open 10m 7'"
                else:
                    ok, msg = False, "Usage: cd open <amt> <3|7|14>"
                app.message = msg
                return True
            if cmd.startswith("break "):
                parts = cmd.split()
                if len(parts) >= 2:
                    ok, msg = app.engine.break_cd(parts[1])
                else:
                    ok, msg = False, "Usage: cd break <id>"
                app.message = msg
                return True
            if cmd.startswith("claim "):
                parts = cmd.split()
                if len(parts) >= 2:
                    ok, msg = app.engine.claim_cd(parts[1])
                else:
                    ok, msg = False, "Usage: cd claim <id|all>"
                app.message = msg
                return True
            if cmd == "claim":
                ok, msg = app.engine.claim_cd("all")
                app.message = msg
                return True
            if cmd.startswith("sort ") or cmd == "sort":
                parts = cmd.split()
                if len(parts) >= 2:
                    ok, msg = app.engine.set_cd_sort_criteria(parts[1])
                else:
                    ok, msg = False, "Usage: sort <days|amount|term>"
                app.message = msg
                return True

        if cmd.startswith("invest "):
            app.handle_invest_command(cmd)
            return True

        if cmd.startswith("divest "):
            parts = cmd.split()
            if len(parts) >= 2:
                shares = parts[2] if len(parts) >= 3 else "1"
                ok, msg = app.engine.divest_corporate(parts[1], shares)
            else:
                ok, msg = False, "Usage: divest <code> <shares|all> (e.g. 'divest SILPH 1')"
            app.message = msg
            return True

        return False
