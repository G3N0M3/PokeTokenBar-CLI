import datetime
import random
import textwrap
from typing import Tuple, Optional, Dict, Any, List

from poketokenbar.utils.formatting import format_tokens, parse_tokens
from poketokenbar.game.minigames.gacha import GachaEngine, GACHA_COST_SINGLE, GACHA_COST_MULTI
from poketokenbar.game.models import (
    POKER_VIP_TRIGGER_BET,
    POKER_VIP_MIN_BET,
    VELVET_STING_CHAPTERS,
    VELVET_PATRONS,
    VELVET_MARKS,
    VIP_PATRON_DAILY_BANKROLLS,
    VIP_CLEAN_SWEEP_BOUNTY,
)


def _format_poker_quote_block(opp_name: str, quote: str) -> str:
    """Formats an opponent quote block wrapped at width <= 64 with 3-space indentation."""
    if not quote or not opp_name or opp_name == "The House":
        return ""
    clean_name = opp_name.split("[")[0].strip()
    full_text = f"⚔️ {clean_name}: {quote}"
    lines = textwrap.wrap(full_text, width=64)
    if not lines:
        return ""
    return "\n" + "\n".join(f"   {line}" for line in lines)


class CasinoMixin:
    """Manages Game Corner casino games: Texas Hold'em Poker, Slots, Blackjack, and Capsule Gacha."""

    def check_and_reset_vip_bankrolls(self, today_str: Optional[str] = None) -> bool:
        if not today_str:
            today_str = datetime.date.today().isoformat()
        last_date = self.state.get("vip_bankrolls_date", "")
        if last_date != today_str:
            bankrolls = self.state.setdefault("vip_bankrolls", {})
            for name, max_val in VIP_PATRON_DAILY_BANKROLLS.items():
                bankrolls[name] = {"current": max_val, "max": max_val}
            self.state["vip_bankrolls_date"] = today_str
            self.state["vip_clean_sweep_claimed"] = False
            self.save()
            return True
        return False

    check_and_refill_vip_bankrolls = check_and_reset_vip_bankrolls

    def get_vip_bankroll(self, name: str) -> Tuple[int, int]:
        clean_name = name.split("[")[0].strip()
        vb = self.state.setdefault("vip_bankrolls", {})
        if clean_name not in vb:
            max_val = VIP_PATRON_DAILY_BANKROLLS.get(clean_name, 2_500_000_000_000_000_000)
            vb[clean_name] = {"current": max_val, "max": max_val}
        entry = vb[clean_name]
        return entry.get("current", 0), entry.get("max", 0)

    def update_vip_bankroll(self, name: str, delta: int) -> int:
        clean_name = name.split("[")[0].strip()
        vb = self.state.setdefault("vip_bankrolls", {})
        if clean_name not in vb:
            max_val = VIP_PATRON_DAILY_BANKROLLS.get(clean_name, 2_500_000_000_000_000_000)
            vb[clean_name] = {"current": max_val, "max": max_val}
        curr = vb[clean_name].get("current", 0)
        new_val = max(0, curr + delta)
        vb[clean_name]["current"] = new_val
        self.save()
        return new_val

    def get_available_vip_opponents(self) -> List[str]:
        self.check_and_reset_vip_bankrolls()
        sting = self.state.get("velvet_sting", {})
        ch = sting.get("chapter", "1")
        is_cleared = sting.get("cleared", False) or ch == "epilogue"
        if is_cleared:
            pool = list(VIP_PATRON_DAILY_BANKROLLS.keys())
        elif sting.get("recruited", False):
            ch_info = VELVET_STING_CHAPTERS.get(ch, {})
            ch_opp = ch_info.get("opponent", "").split("[")[0].strip()
            pool = [p for p in VELVET_PATRONS]
            if ch_opp and not ch_info.get("is_boss", False) and ch_opp not in pool:
                pool.append(ch_opp)
        else:
            pool = [p for p in VELVET_PATRONS]

        available = []
        for p in pool:
            cur, _ = self.get_vip_bankroll(p)
            if cur >= POKER_VIP_MIN_BET:
                available.append(p)
        return available

    def cycle_vip_opponent(self) -> Tuple[bool, str]:
        if self.poker.game_state != "idle":
            return False, "Finish your active hand before changing opponents!"
        if self.poker.table_mode != "vip":
            return False, "Patron selection is only available at The Velvet Salon ('table vip')!"
        if getattr(self.poker, "boss_name", ""):
            return False, f"You are currently facing {self.poker.boss_name} in a syndicate boss duel!"

        avail = self.get_available_vip_opponents()
        if not avail:
            return False, "All VIP patrons are busted for today! The tables will reset tomorrow at midnight (00:00)."

        curr = self.poker.active_opponent.split("[")[0].strip()
        if curr in avail:
            idx = avail.index(curr)
            next_opp = avail[(idx + 1) % len(avail)]
        else:
            next_opp = avail[0]

        self.poker.active_opponent = next_opp
        c_stack, _ = self.get_vip_bankroll(next_opp)
        return True, f"Seated across from {next_opp}! (Chips: {format_tokens(c_stack)} tokens)."

    def check_vip_clean_sweep(self) -> Tuple[bool, str]:
        avail = self.get_available_vip_opponents()
        if not avail and not self.state.get("vip_clean_sweep_claimed", False):
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - VIP_CLEAN_SWEEP_BOUNTY
            self.state["vip_clean_sweep_claimed"] = True
            self.state["vip_clean_sweeps_count"] = self.state.get("vip_clean_sweeps_count", 0) + 1
            self.save()
            return True, f"\n   🏆 \033[1m\033[93m[SALON CLEAN SWEEP] You stripped all VIP patrons of their tokens! Claimed +{format_tokens(VIP_CLEAN_SWEEP_BOUNTY)} Clean Sweep Bounty!\033[0m"
        return False, ""

    def play_poker_bet(self, amount_str: str) -> Tuple[bool, str]:
        if self.poker.game_state != "idle":
            return False, "A hand is already in progress! Type 'check', 'raise', 'allin', or 'fold'."
        clean_str = amount_str.lower().strip()
        if clean_str in ["all", "all-in"]:
            bet = self.available_tokens
        else:
            bet = parse_tokens(amount_str)
            if bet < 0:
                return False, "Invalid bet amount! Example: 'bet 500k', 'bet 1m', 'bet all', or 'bet 2000000'."

        if bet <= 0:
            return False, "Bet amount must be greater than 0!"

        if self.poker.table_mode == "vip" and bet < POKER_VIP_MIN_BET:
            return False, f"Minimum bet at The Velvet Salon is {format_tokens(POKER_VIP_MIN_BET)} tokens!"

        if self.poker.table_mode == "vip":
            self.check_and_reset_vip_bankrolls()
            sting = self.state.setdefault("velvet_sting", {
                "chapter": "1",
                "recruited": False,
                "cleared": False,
                "boss_stack": 0,
                "boss_max_stack": 0,
                "syndicate_wins": 0,
                "vip_winnings": 0,
                "max_pot_won": 0,
                "ranked_wins": 0,
            })
            ch = sting.get("chapter", "1")
            is_cleared = sting.get("cleared", False) or ch == "epilogue"
            ch_info = VELVET_STING_CHAPTERS.get(ch, {}) if (sting.get("recruited", False) and not is_cleared) else {}

            if ch_info.get("is_boss", False) and not is_cleared:
                boss_name = ch_info.get("opponent", "The Boss")
                b_stack = sting.get("boss_stack", 0)
                if b_stack <= 0:
                    return False, f"{boss_name} has already been stripped of their stack! Type 'sting' to advance."
                self.poker.boss_name = boss_name
                self.poker.boss_stack = b_stack
                self.poker.boss_max_stack = sting.get("boss_max_stack", ch_info.get("boss_max_stack", 50_000_000_000_000))
                self.poker.active_opponent = boss_name
            else:
                self.poker.boss_name = ""
                self.poker.boss_stack = 0
                self.poker.boss_max_stack = 0
                avail_opps = self.get_available_vip_opponents()
                if not avail_opps:
                    clean_msg = "All VIP patrons are busted for today! The Velvet Salon tables will reset tomorrow at midnight (00:00)."
                    if self.state.get("vip_clean_sweep_claimed", False):
                        clean_msg = f"All VIP patrons have been wiped out today! (Clean Sweep Bonus claimed: +{format_tokens(VIP_CLEAN_SWEEP_BOUNTY)} tokens). Tables reset at 00:00."
                    return False, clean_msg

                curr_opp = self.poker.active_opponent.split("[")[0].strip() if self.poker.active_opponent else ""
                if curr_opp not in avail_opps:
                    self.poker.active_opponent = random.choice(avail_opps)

                # Table stakes: cap bet to active opponent's remaining chips
                opp_cur, _ = self.get_vip_bankroll(self.poker.active_opponent)
                if bet > opp_cur:
                    bet = opp_cur

        avail = self.available_tokens
        if bet > avail:
            return False, f"Not enough tokens! You have {format_tokens(avail)} available tokens."

        # Lock bet by increasing spent_tokens
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + bet
        self.save()

        ok, msg = self.poker.start_hand(bet)
        if not ok:
            # Revert bet
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - bet
            self.save()
            return False, msg

        opp = self.poker.active_opponent
        table_label = f" [{opp}]" if opp != "The House" else ""
        return True, f"♠️ Dealt {format_tokens(bet)} tokens{table_label}! Type 'check' to reveal Flop, 'raise', 'allin', or 'fold'."

    def switch_poker_table(self, mode: str) -> Tuple[bool, str]:
        clean_mode = mode.lower().strip()
        if clean_mode in ["std", "standard", "floor"]:
            if self.poker.game_state != "idle":
                return False, "Finish your active hand before switching tables!"
            self.poker.table_mode = "standard"
            self.poker.active_opponent = "The House"
            self.poker.boss_name = ""
            return True, "Returned to the Main Casino Poker Floor."

        elif clean_mode in ["vip", "salon", "velvet"]:
            if not self.state.get("poker_vip_unlocked", False):
                return False, "The Velvet Salon is for VIP high-rollers only. Place a wager of >= 100.0T tokens on the main floor to receive an invitation!"
            if self.poker.game_state != "idle":
                return False, "Finish your active hand before switching tables!"
            self.poker.table_mode = "vip"
            sting = self.state.setdefault("velvet_sting", {})
            ch = sting.get("chapter", "1")
            is_cleared = sting.get("cleared", False) or ch == "epilogue"
            ch_info = VELVET_STING_CHAPTERS.get(ch, {}) if (sting.get("recruited", False) and not is_cleared) else {}
            if ch_info.get("is_boss", False) and not is_cleared:
                self.poker.boss_name = ch_info.get("opponent", "The Boss")
                self.poker.boss_stack = sting.get("boss_stack", ch_info.get("boss_max_stack", 50_000_000_000_000))
                self.poker.boss_max_stack = sting.get("boss_max_stack", ch_info.get("boss_max_stack", 50_000_000_000_000))
                self.poker.active_opponent = self.poker.boss_name
                return True, f"Stepped into The Velvet Salon across from {self.poker.boss_name}! (Min bet: 10.0T tokens)."
            else:
                self.poker.boss_name = ""
                self.poker.boss_stack = 0
                self.poker.boss_max_stack = 0
                self.check_and_reset_vip_bankrolls()
                avail_opps = self.get_available_vip_opponents()
                if not avail_opps:
                    self.poker.active_opponent = "None"
                    return True, "Dealer: 'Welcome to The Velvet Salon. All VIP patrons have tapped out for today! The tables will reset tomorrow at midnight (00:00).'"
                curr = self.poker.active_opponent.split("[")[0].strip() if self.poker.active_opponent else ""
                if curr not in avail_opps:
                    self.poker.active_opponent = random.choice(avail_opps)
                c_stack, _ = self.get_vip_bankroll(self.poker.active_opponent)
                if is_cleared:
                    return True, f"Dealer: 'Welcome back, Master of the Velvet Sting!' Across from {self.poker.active_opponent} (Chips: {format_tokens(c_stack)} tokens)."
                return True, f"Dealer: 'Right this way! Welcome to The Velvet Salon.' Across from {self.poker.active_opponent} (Chips: {format_tokens(c_stack)} tokens)."

        elif clean_mode in ["boss", "croix", "heist"]:
            return False, "The 'table boss' command has been removed. Boss encounters take place directly at The Velvet Salon ('table vip')!"

        return False, "Usage: table <std|vip>"

    def _format_opponent_fold(self, quote: str) -> Tuple[bool, str]:
        outcome, winnings = self.poker.opponent_fold()
        mauv_mult = self.get_mauville_multiplier()
        if winnings > 0 and mauv_mult > 1.0:
            winnings = int(winnings * mauv_mult)

        # Grant winnings
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - winnings
        self.save()

        bet = self.poker.current_bet
        net_change = winnings - bet
        self._record_catalyst("casino_net_pnl", net_change)
        profit_str = f"+{format_tokens(net_change)}" if net_change >= 0 else f"-{format_tokens(abs(net_change))}"
        self.poker.last_net = profit_str

        boss_msg = ""
        sting_msg = ""

        if self.poker.table_mode in ["vip", "boss"]:
            sting = self.state.setdefault("velvet_sting", {
                "chapter": "1",
                "recruited": False,
                "cleared": False,
                "boss_stack": 0,
                "boss_max_stack": 0,
                "syndicate_wins": 0,
                "vip_winnings": 0,
                "chapter_winnings": 0,
                "chapter_pot": 0,
                "max_pot_won": 0,
                "ranked_wins": 0,
            })
            if getattr(self.poker, "boss_name", ""):
                sting["boss_stack"] = self.poker.boss_stack
                self.save()
                boss_msg = f"\n   💥 {self.poker.boss_name} Treasury Drained: -{format_tokens(winnings)}! (Remaining: {format_tokens(self.poker.boss_stack)})"
            else:
                sting["syndicate_wins"] = sting.get("syndicate_wins", 0) + 1
                sting["vip_winnings"] = sting.get("vip_winnings", 0) + winnings
                sting["max_pot_won"] = max(sting.get("max_pot_won", 0), winnings)
                sting["chapter_pot"] = max(sting.get("chapter_pot", 0), winnings)
                sting["chapter_winnings"] = sting.get("chapter_winnings", 0) + winnings
                self.save()

                opp_clean = self.poker.active_opponent.split("[")[0].strip()
                rem = self.update_vip_bankroll(opp_clean, -winnings)
                if rem < POKER_VIP_MIN_BET:
                    swept, sweep_msg = self.check_vip_clean_sweep()
                    if swept:
                        boss_msg = f"\n   💥 {opp_clean.upper()} HAS BUSTED FOR TODAY! (0 chips remaining){sweep_msg}"
                    else:
                        avail = self.get_available_vip_opponents()
                        if avail:
                            next_patron = random.choice(avail)
                            self.poker.active_opponent = next_patron
                            boss_msg = f"\n   💥 {opp_clean.upper()} HAS BUSTED FOR TODAY! Dealer: 'Seating {next_patron} at the felt!'"
                        else:
                            boss_msg = f"\n   💥 {opp_clean.upper()} HAS BUSTED FOR TODAY! All VIP patrons are tapped out until midnight!"
                else:
                    boss_msg = f"\n   📉 {opp_clean} Chips: -{format_tokens(winnings)} (Remaining: {format_tokens(rem)})"

                if not sting.get("recruited", False):
                    if sting["syndicate_wins"] >= 10 and sting["vip_winnings"] >= 500_000_000_000_000:
                        sting["recruited"] = True
                        self.save()
                        sting_msg = f"\n   👑 \033[1m\033[93m[RECRUITED] Madame Vivienne approaches your table! You play remarkably well!\033[0m"

            ready, _ = self.check_velvet_sting_objective()
            is_cleared = sting.get("cleared", False) or sting.get("chapter", "1") == "epilogue"
            if ready and sting.get("recruited", False) and not is_cleared:
                sting_msg = f"\n   🚨 \033[1m\033[93m[THE VELVET STING] Tactical objective achieved! Type 'sting' to advance!\033[0m"

        opp_name = self.poker.active_opponent.split("[")[0].strip()
        return True, f"🏳️ {opp_name.upper()} FOLDED!\n   🏆 YOU WIN THE POT! Won {format_tokens(winnings)} Tokens! (Net: {profit_str}){boss_msg}{sting_msg}"

    def play_poker_action(self, action_str: str) -> Tuple[bool, str]:
        cmd = action_str.lower().strip()
        if self.poker.game_state == "idle":
            return False, "No active Texas Hold'em hand! Type 'bet <amount>' to start a hand."

        sting = self.state.setdefault("velvet_sting", {})
        curr_ch = sting.get("chapter", "1")
        opp = self.poker.active_opponent
        opp_name = opp.split("[")[0].strip()

        if cmd == "fold":
            outcome, lost = self.poker.play_fold()
            self.poker.opponent_pending_call = 0
            end_quote = self.poker.process_opponent_end_quote("player_fold", chapter=curr_ch)
            self._record_catalyst("casino_net_pnl", -lost)
            opp_gain_msg = ""
            if self.poker.table_mode in ["vip", "boss"] and not getattr(self.poker, "boss_name", ""):
                rem = self.update_vip_bankroll(opp_name, lost)
                opp_gain_msg = f" ({opp_name} Chips: {format_tokens(rem)})"
            rebate_msg = ""
            if self.poker.table_mode in ["vip", "boss"] and self.state.get("luxury", {}).get("unlocked"):
                rebate = int(lost * 0.10)
                if rebate > 0:
                    self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - rebate
                    self.save()
                    rebate_msg = f" (🛡️ Sovereign Rebate: +{format_tokens(rebate)} tokens refunded!)"
            return True, f"🏳️ YOU FOLDED! Surrendered {format_tokens(lost)} tokens to {opp_name}.{rebate_msg}{opp_gain_msg}"

        elif cmd == "call":
            if self.poker.opponent_pending_call <= 0:
                return False, "No pending opponent bet to call! Type 'check' to advance street."

            pending = self.poker.opponent_pending_call
            avail = self.available_tokens
            call_cost = min(avail, pending)
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + call_cost
            self.poker.current_bet += call_cost
            self.poker.opponent_pending_call = 0
            self.save()

            call_note = f"💰 Called {format_tokens(call_cost)} tokens! "
            if self.poker.game_state == "preflop":
                self.poker.play_flop()
                action, bet_amt, quote = self.poker.process_opponent_action(chapter=curr_ch, available_tokens=self.available_tokens)
                if action == "bet":
                    return True, f"{call_note}♦️ Flop revealed! ({opp_name} bets {format_tokens(bet_amt)}).\n   ➔ Actions: 'call' ({format_tokens(bet_amt)}) | 'raise' | 'allin' | 'fold'"
                return True, f"{call_note}♦️ Flop revealed! ({opp_name} checks). Type 'check' for Turn, 'raise', 'allin', or 'fold'."
            elif self.poker.game_state == "flop":
                self.poker.play_turn()
                action, bet_amt, quote = self.poker.process_opponent_action(chapter=curr_ch, available_tokens=self.available_tokens)
                if action == "bet":
                    return True, f"{call_note}♦️ Turn revealed! ({opp_name} bets {format_tokens(bet_amt)}).\n   ➔ Actions: 'call' ({format_tokens(bet_amt)}) | 'raise' | 'allin' | 'fold'"
                return True, f"{call_note}♦️ Turn revealed! ({opp_name} checks). Type 'check' for Showdown, 'raise', 'allin', or 'fold'."
            elif self.poker.game_state == "turn":
                ok, showdown_msg = self._format_poker_showdown()
                return True, f"{call_note}{showdown_msg}"
            else:
                return False, "Hand already completed."

        elif cmd == "check":
            if self.poker.opponent_pending_call > 0:
                return False, f"Opponent has placed a bet of {format_tokens(self.poker.opponent_pending_call)}! Type 'call' to match, 'raise', 'allin', or 'fold'."

            if self.poker.game_state == "preflop":
                self.poker.play_flop()
                action, bet_amt, quote = self.poker.process_opponent_action(chapter=curr_ch, available_tokens=self.available_tokens)
                if action == "bet":
                    return True, f"♦️ Flop revealed! ({opp_name} bets {format_tokens(bet_amt)}).\n   ➔ Actions: 'call' ({format_tokens(bet_amt)}) | 'raise' | 'allin' | 'fold'"
                return True, f"♦️ Flop revealed! ({opp_name} checks). Type 'check' for Turn, 'raise', 'allin', or 'fold'."
            elif self.poker.game_state == "flop":
                self.poker.play_turn()
                action, bet_amt, quote = self.poker.process_opponent_action(chapter=curr_ch, available_tokens=self.available_tokens)
                if action == "bet":
                    return True, f"♦️ Turn revealed! ({opp_name} bets {format_tokens(bet_amt)}).\n   ➔ Actions: 'call' ({format_tokens(bet_amt)}) | 'raise' | 'allin' | 'fold'"
                return True, f"♦️ Turn revealed! ({opp_name} checks). Type 'check' for Showdown, 'raise', 'allin', or 'fold'."
            elif self.poker.game_state == "turn":
                return self._format_poker_showdown()
            else:
                return False, "Hand already completed."

        elif cmd in ["raise", "allin"]:
            avail = self.available_tokens
            pending = self.poker.opponent_pending_call
            if cmd == "allin":
                bet_amount = avail
            else:
                raise_increment = max(self.poker.current_bet, 10_000_000_000_000 if self.poker.table_mode in ["vip", "boss"] else 1)
                bet_amount = pending + raise_increment

            if bet_amount <= 0:
                return False, "You don't have any more tokens to bet!"
            if avail < bet_amount:
                if avail > pending and pending > 0:
                    bet_amount = avail
                else:
                    return False, f"Not enough tokens to raise! Needed: {format_tokens(bet_amount)}, Available: {format_tokens(avail)}"

            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + bet_amount
            self.poker.current_bet += bet_amount
            self.poker.opponent_pending_call = 0
            self.save()

            # Opponent reaction to player's raise
            action, re_raise_amt, quote = self.poker.process_opponent_reaction(
                raise_amount=bet_amount,
                is_allin=(cmd == "allin"),
                chapter=curr_ch
            )

            if action == "fold":
                return self._format_opponent_fold(quote)

            if action == "raise":
                return True, f"💥 {opp_name.upper()} RE-RAISED! (+{format_tokens(re_raise_amt)})\n   ➔ Actions: 'call' ({format_tokens(re_raise_amt)}) | 'raise' | 'allin' | 'fold'"

            # Opponent called player's raise!
            opp_call_note = f"💰 {opp_name} CALLED your raise!\n"
            if self.poker.game_state == "preflop":
                self.poker.play_flop()
                return True, f"{opp_call_note}♦️ Flop revealed! Type 'check' for Turn, 'raise', 'allin', or 'fold'."
            elif self.poker.game_state == "flop":
                self.poker.play_turn()
                return True, f"{opp_call_note}♦️ Turn revealed! Type 'check' for Showdown, 'raise', 'allin', or 'fold'."
            elif self.poker.game_state == "turn":
                ok, showdown_msg = self._format_poker_showdown()
                return True, f"{opp_call_note}{showdown_msg}"
            else:
                return False, "Hand already completed."

        else:
            return False, "Invalid poker action. Valid: 'check', 'call', 'raise', 'allin', or 'fold'."

    play_poker_hold = play_poker_action

    def _format_poker_showdown(self) -> Tuple[bool, str]:
        outcome, p_rank, d_rank, mult, winnings = self.poker.play_showdown()

        mauv_mult = self.get_mauville_multiplier()
        if winnings > 0 and outcome == "WIN" and mauv_mult > 1.0:
            winnings = int(winnings * mauv_mult)

        # Grant winnings by decreasing spent_tokens
        if winnings > 0:
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - winnings
            self.save()

        bet = self.poker.current_bet
        net_change = winnings - bet
        self._record_catalyst("casino_net_pnl", net_change)
        profit_str = f"+{format_tokens(net_change)}" if net_change >= 0 else f"-{format_tokens(abs(net_change))}"

        self.poker.last_net = profit_str

        rebate_msg = ""
        boss_msg = ""
        sting_msg = ""

        if outcome == "WIN":
            if self.poker.table_mode in ["vip", "boss"]:
                sting = self.state.setdefault("velvet_sting", {
                    "chapter": "1",
                    "recruited": False,
                    "cleared": False,
                    "boss_stack": 0,
                    "boss_max_stack": 0,
                    "syndicate_wins": 0,
                    "vip_winnings": 0,
                    "max_pot_won": 0,
                    "ranked_wins": 0,
                })
                if getattr(self.poker, "boss_name", ""):
                    sting["boss_stack"] = self.poker.boss_stack
                    self.save()
                    boss_msg = f"\n   💥 {self.poker.boss_name} Treasury Drained: -{format_tokens(winnings)}! (Remaining: {format_tokens(self.poker.boss_stack)})"
                else:
                    sting["syndicate_wins"] = sting.get("syndicate_wins", 0) + 1
                    sting["vip_winnings"] = sting.get("vip_winnings", 0) + winnings
                    sting["max_pot_won"] = max(sting.get("max_pot_won", 0), winnings)
                    sting["chapter_pot"] = max(sting.get("chapter_pot", 0), winnings)
                    sting["chapter_winnings"] = sting.get("chapter_winnings", 0) + winnings
                    if p_rank in ["Two Pair", "Three of a Kind", "Straight", "Flush", "Full House", "Four of a Kind", "Straight Flush", "Royal Flush"]:
                        sting["ranked_wins"] = sting.get("ranked_wins", 0) + 1
                    self.save()

                    opp_clean = self.poker.active_opponent.split("[")[0].strip()
                    rem = self.update_vip_bankroll(opp_clean, -winnings)
                    if rem < POKER_VIP_MIN_BET:
                        swept, sweep_msg = self.check_vip_clean_sweep()
                        if swept:
                            boss_msg = f"\n   💥 {opp_clean.upper()} HAS BUSTED FOR TODAY! (0 chips remaining){sweep_msg}"
                        else:
                            avail = self.get_available_vip_opponents()
                            if avail:
                                next_patron = random.choice(avail)
                                self.poker.active_opponent = next_patron
                                boss_msg = f"\n   💥 {opp_clean.upper()} HAS BUSTED FOR TODAY! Dealer: 'Seating {next_patron} at the felt!'"
                            else:
                                boss_msg = f"\n   💥 {opp_clean.upper()} HAS BUSTED FOR TODAY! All VIP patrons are tapped out until midnight!"
                    else:
                        boss_msg = f"\n   📉 {opp_clean} Chips: -{format_tokens(winnings)} (Remaining: {format_tokens(rem)})"

                    if not sting.get("recruited", False):
                        if sting["syndicate_wins"] >= 10 and sting["vip_winnings"] >= 500_000_000_000_000:
                            sting["recruited"] = True
                            self.save()
                            sting_msg = f"\n   👑 \033[1m\033[93m[RECRUITED] Madame Vivienne approaches your table! You play remarkably well!\033[0m"

                ready, _ = self.check_velvet_sting_objective()
                is_cleared = sting.get("cleared", False) or sting.get("chapter", "1") == "epilogue"
                if ready and sting.get("recruited", False) and not is_cleared:
                    sting_msg = f"\n   🚨 \033[1m\033[93m[THE VELVET STING] Tactical objective achieved! Type 'sting' to advance!\033[0m"

        elif outcome == "LOSS":
            if self.poker.table_mode in ["vip", "boss"]:
                if not getattr(self.poker, "boss_name", ""):
                    opp_clean = self.poker.active_opponent.split("[")[0].strip()
                    rem = self.update_vip_bankroll(opp_clean, bet)
                    boss_msg = f"\n   📈 {opp_clean} collected your wager! (Stack: {format_tokens(rem)})"
            if self.poker.table_mode in ["vip", "boss"] and self.state.get("luxury", {}).get("unlocked"):
                rebate = int(bet * 0.10)
                if rebate > 0:
                    self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - rebate
                    self.save()
                    rebate_msg = f"\n   🛡️ Sovereign Rebate: +{format_tokens(rebate)} tokens refunded to your account!"

        # Determine opponent end quote situation
        opp_clean = self.poker.active_opponent.split("[")[0].strip()
        opp_cur, _ = self.get_vip_bankroll(opp_clean) if self.poker.table_mode == "vip" else (1, 1)
        is_bankrupt = (
            ((bool(getattr(self.poker, "boss_name", "")) or self.poker.table_mode == "boss") and self.poker.boss_stack <= 0)
            or (self.poker.table_mode == "vip" and not getattr(self.poker, "boss_name", "") and opp_cur < POKER_VIP_MIN_BET)
        )
        if is_bankrupt:
            situation = "bankrupt"
        elif outcome == "WIN":
            situation = "showdown_loss"
        elif outcome == "LOSS":
            situation = "showdown_win"
        else:
            situation = "showdown_push"

        curr_ch = self.state.get("velvet_sting", {}).get("chapter", "1")
        self.poker.process_opponent_end_quote(situation, chapter=curr_ch)
        opp = self.poker.active_opponent

        if outcome == "WIN":
            return True, f"🏆 YOU BEAT {opp.upper()}! ({p_rank} vs {d_rank}) Won {format_tokens(winnings)} Tokens! (Net: {profit_str}){boss_msg}{sting_msg}"
        elif outcome == "PUSH":
            return True, f"🤝 TIE / PUSH! ({p_rank}) Bet of {format_tokens(bet)} Tokens returned."
        else:
            return True, f"💀 {opp.upper()} WINS! ({d_rank} beats {p_rank}) Lost {format_tokens(bet)} Tokens.{rebate_msg}"

    def get_velvet_sting_briefing(self) -> Optional[Dict[str, Any]]:
        sting = self.state.setdefault("velvet_sting", {
            "chapter": "1",
            "cleared": False,
            "boss_stack": 0,
            "boss_max_stack": 0,
            "syndicate_wins": 0,
            "vip_winnings": 0,
            "max_pot_won": 0,
            "ranked_wins": 0,
        })
        ch = sting.get("chapter", "1")
        return VELVET_STING_CHAPTERS.get(ch)

    def check_velvet_sting_objective(self) -> Tuple[bool, str]:
        sting = self.state.setdefault("velvet_sting", {
            "chapter": "1",
            "cleared": False,
            "boss_stack": 0,
            "boss_max_stack": 0,
            "syndicate_wins": 0,
            "vip_winnings": 0,
            "max_pot_won": 0,
            "ranked_wins": 0,
        })
        ch = sting.get("chapter", "1")
        if ch == "epilogue" or sting.get("cleared", False):
            return True, "Campaign cleared! The Velvet Sting was a complete success."

        if ch == "1":
            wins = sting.get("syndicate_wins", 0)
            winnings = sting.get("vip_winnings", 0)
            req_wins = 10
            req_winnings = 500_000_000_000_000
            if wins >= req_wins and winnings >= req_winnings:
                return True, f"Recruitment trial complete! (Wins: {wins}/{req_wins}, Winnings: {format_tokens(winnings)}/500.0T)"
            return False, f"Recruitment trial: Need 10 wins (Current: {wins}/{req_wins}) AND 500.0T total winnings (Current: {format_tokens(winnings)}/500.0T)."

        elif ch == "2":
            pot = sting.get("chapter_pot", 0)
            req = 25_000_000_000_000
            if pot >= req:
                return True, f"Telemetry intercepted! Single pot against Vance: {format_tokens(pot)} / 25.0T tokens."
            return False, f"Win a single pot >= 25.0T tokens against Financier Vance. Current best: {format_tokens(pot)} / 25.0T."

        elif ch == "3":
            stack = sting.get("boss_stack", 1)
            if stack <= 0:
                return True, "Viktor Rostov's security war chest completely depleted!"
            return False, f"Deplete Viktor's 50.0T war chest. Remaining: {format_tokens(stack)}."

        elif ch == "4":
            winnings = sting.get("chapter_winnings", 0)
            req = 50_000_000_000_000
            if winnings >= req:
                return True, f"Injunction collateral secured! (VIP Winnings: {format_tokens(winnings)} / 50.0T tokens)"
            return False, f"Accumulate 50.0T VIP winnings against Countess Beverly. Current: {format_tokens(winnings)} / 50.0T."

        elif ch == "5":
            rw = sting.get("ranked_wins", 0)
            if rw >= 3:
                return True, f"Table mastery proven! (Ranked wins: {rw}/3 against Lord Sterling)"
            return False, f"Win 3 hands showing Two Pair or higher against Lord Sterling. Current: {rw}/3."

        elif ch == "6":
            pot = sting.get("chapter_pot", 0)
            req = 100_000_000_000_000
            if pot >= req:
                return True, f"Baron Croix baited! Whale pot: {format_tokens(pot)} / 100.0T tokens."
            return False, f"Win a pot >= 100.0T tokens against Oligarch Thorne. Current best: {format_tokens(pot)} / 100.0T."

        elif ch in ["7", "8", "9", "10"]:
            stack = sting.get("boss_stack", 1)
            ch_info = VELVET_STING_CHAPTERS.get(ch, {})
            boss_name = ch_info.get("opponent", "The Boss")
            if stack <= 0:
                return True, f"{boss_name} bankrupted!"
            return False, f"Deplete {boss_name}'s stack to 0. Remaining: {format_tokens(stack)}."

        return False, "Unknown chapter status."

    def advance_velvet_sting(self) -> Tuple[bool, str]:
        ready, msg = self.check_velvet_sting_objective()
        if not ready:
            return False, f"Objective not yet complete: {msg}"

        sting = self.state.setdefault("velvet_sting", {})
        curr_ch = sting.get("chapter", "1")
        if curr_ch == "epilogue" or sting.get("cleared", False):
            return False, "The Velvet Sting campaign is already complete!"

        if curr_ch == "10":
            sting["chapter"] = "epilogue"
            sting["cleared"] = True
            # Clear boss attributes from poker engine and seat a salon patron or mark
            self.poker.boss_name = ""
            self.poker.boss_stack = 0
            self.poker.boss_max_stack = 0
            pool = [p for p in (VELVET_PATRONS + VELVET_MARKS) if "Croix" not in p]
            self.poker.active_opponent = random.choice(pool)
            # Grant 100T bounty
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - 100_000_000_000_000
            # Add title
            achs = set(self.state.get("achievements", []))
            achs.add("♠️ Master of the Velvet Sting")
            self.state["achievements"] = list(achs)
            # Add Luxury Suite decor watch if luxury suite initialized
            lux = self.state.setdefault("luxury", {})
            dec = lux.setdefault("decor", [])
            if "watch" not in dec:
                dec.append("watch")
            self.save()
            return True, "🎉 Campaign Cleared! Seized 100.0T tokens bounty, Title '♠️ Master of the Velvet Sting', and Baron's 24K Sovereign Watch awarded!"

        # Advance to next chapter
        next_num = int(curr_ch) + 1
        next_ch = str(next_num)
        sting["chapter"] = next_ch
        # Reset per-chapter progress trackers so each mission is played fresh
        sting["chapter_pot"] = 0
        sting["chapter_winnings"] = 0
        sting["ranked_wins"] = 0
        ch_info = VELVET_STING_CHAPTERS.get(next_ch, {})

        if ch_info.get("is_boss", False):
            max_st = ch_info.get("boss_max_stack", 50_000_000_000_000)
            sting["boss_stack"] = max_st
            sting["boss_max_stack"] = max_st
            self.poker.boss_stack = max_st
            self.poker.boss_max_stack = max_st
            self.poker.boss_name = ch_info.get("opponent", "The Boss")
            self.poker.active_opponent = self.poker.boss_name
        else:
            self.poker.boss_stack = 0
            self.poker.boss_max_stack = 0
            self.poker.boss_name = ""
            self.poker.active_opponent = ch_info.get("opponent", random.choice(VELVET_MARKS))

        self.save()
        return True, f"Advanced to Chapter {next_ch}: {ch_info.get('title', '')}!"

    def reset_velvet_sting(self) -> Tuple[bool, str]:
        """Resets The Velvet Salon VIP access and storyline progression back to uninitialized state."""
        self.state["poker_vip_unlocked"] = False
        self.state["velvet_sting"] = {
            "chapter": "1",
            "recruited": False,
            "cleared": False,
            "boss_stack": 0,
            "boss_max_stack": 0,
            "syndicate_wins": 0,
            "vip_winnings": 0,
            "chapter_winnings": 0,
            "chapter_pot": 0,
            "max_pot_won": 0,
            "ranked_wins": 0,
        }
        self.poker.table_mode = "standard"
        self.poker.boss_stack = 0
        self.poker.boss_max_stack = 0
        self.poker.boss_name = ""
        self.poker.active_opponent = "The House"
        if self.poker.game_state != "idle":
            self.poker.game_state = "idle"
            self.poker.current_bet = 0
        self.save()
        return True, "The Velvet Salon VIP access & 'The Velvet Sting' storyline have been reset to Chapter 1!"

    def play_gacha(self, pull_type: str = "1") -> Tuple[bool, str]:
        try:
            qty = int(pull_type)
            if qty <= 0:
                return False, "Invalid pull quantity."
        except ValueError:
            return False, "Invalid pull quantity."

        num_tens = qty // 10
        num_ones = qty % 10
        cost = (num_tens * GACHA_COST_MULTI) + (num_ones * GACHA_COST_SINGLE)

        avail = self.available_tokens
        if avail < cost:
            return False, f"Not enough tokens! {qty}x Gacha pull requires {format_tokens(cost)} available tokens."

        # Deduct cost by increasing spent_tokens
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
        inv = self.state.get("inventory", {})

        results_txt = [f"🔮 \033[1m{qty}-CAPSULE GACHA PULL RESULTS:\033[0m"]
        pulls = []
        
        # Do all pulls one by one and update a local inv tracker for mega stones
        local_inv = dict(inv)
        for _ in range(qty):
            res = GachaEngine.pull_one(local_inv)
            if res[2] == "item":
                local_inv[res[3]] = local_inv.get(res[3], 0) + 1
            pulls.append(res)

        pity = self.state.get("gacha_pity", 0)
        for i in range(len(pulls)):
            pity += 1
            if pity >= 100:
                pulls[i] = ("LEGENDARY", "🌟 1x Master Ball (Guaranteed Shiny Hatch!)", "item", "master_ball")
                pity = 0
                results_txt[0] += " \033[1m\033[32m[PITY TRIGGERED!]\033[0m"
        self.state["gacha_pity"] = pity

        for tier, name, r_type, val in pulls:
            color = "\033[36m" if tier == "COMMON" else ("\033[33m" if tier in ["UNCOMMON", "RARE"] else "\033[32m")
            results_txt.append(f"  • [{color}{tier}\033[0m] {name}")

            if r_type == "item":
                if isinstance(val, str) and val.startswith("mega_stone_"):
                    if inv.get(val, 0) == 0:
                        inv[val] = 1
                    else:
                        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - 5_000_000
                else:
                    inv[val] = inv.get(val, 0) + 1
            elif r_type == "tokens":
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - val
            elif r_type == "egg":
                ok_egg, msg_egg, cash_egg = self.obtain_egg(val)
                if cash_egg:
                    results_txt[-1] = results_txt[-1] + f" (Full Roster: Converted to {format_tokens(cash_egg)} tokens!)"
                elif ok_egg and msg_egg:
                    if "Nursery" in msg_egg or "Reserves" in msg_egg:
                        results_txt[-1] = results_txt[-1] + " (Queued in Nursery)"
                    else:
                        results_txt[-1] = results_txt[-1] + " (Now Incubating)"

        self.state["inventory"] = inv
        self.save()
        results_txt.append(f"\n  \033[90mLegendary Pity Counter: {pity}/100\033[0m")
        return True, "\n".join(results_txt)

    def play_slots(self, amount_str: str) -> Tuple[bool, str]:
        avail = self.available_tokens
        
        # Hidden rig logic
        is_rigged = False
        if amount_str.startswith("-"):
            is_rigged = True
            amount_str = amount_str[1:]
            
        if amount_str.lower() == "all":
            bet = avail
        else:
            bet = parse_tokens(amount_str)
            
        if bet <= 0:
            return False, "Invalid bet amount!"
        if bet > avail:
            return False, f"Not enough tokens! You only have {format_tokens(avail)}."
            
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + bet
        
        if is_rigged:
            # Force a ⭐ Jackpot on all 3 rows (which naturally cascades to both diagonals too)
            self.slots.last_reels = [
                ["⭐", "⭐", "⭐"],
                ["⭐", "⭐", "⭐"],
                ["⭐", "⭐", "⭐"]
            ]
            self.slots.last_payout_mult = 100.0  # (100 * 5) / 5
            self.slots.last_win_amount = bet * 100
            reels, mult, win_amount = self.slots.last_reels, self.slots.last_payout_mult, self.slots.last_win_amount
        else:
            reels, mult, win_amount = self.slots.spin(bet)
        
        grid_str = "\n".join([f"🎰 {' | '.join(row)} 🎰" for row in reels])
        if win_amount > 0:
            mauv_mult = self.get_mauville_multiplier()
            if mauv_mult > 1.0:
                win_amount = int(win_amount * mauv_mult)
            self.state["spent_tokens"] = self.state["spent_tokens"] - win_amount
            msg = f"{grid_str}\n\nWINNER! ({mult:.1f}x Total Multiplier)\nYou won {format_tokens(win_amount)} tokens!"
        else:
            msg = f"{grid_str}\n\nNo luck this time! You lost {format_tokens(bet)} tokens."
            
        self._record_catalyst("casino_net_pnl", win_amount - bet)
        self.save()
        return True, msg

    def play_blackjack_bet(self, amount_str: str) -> Tuple[bool, str]:
        avail = self.available_tokens
        if amount_str.lower() == "all":
            bet = avail
        else:
            bet = parse_tokens(amount_str)
            
        if bet <= 0:
            return False, "Invalid bet amount!"
        if bet > avail:
            return False, f"Not enough tokens! You only have {format_tokens(avail)}."
            
        ok, msg = self.blackjack.start_game(bet)
        if ok:
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + bet
            if self.blackjack.game_state == "finished":
                winnings = getattr(self.blackjack, "last_winnings", 0)
                mauv_mult = self.get_mauville_multiplier()
                if winnings > 0 and mauv_mult > 1.0:
                    winnings = int(winnings * mauv_mult)
                if winnings > 0:
                    self.state["spent_tokens"] = self.state["spent_tokens"] - winnings
                self._record_catalyst("casino_net_pnl", winnings - bet)
            self.save()
        return ok, msg

    def play_blackjack_action(self, action: str) -> Tuple[bool, str]:
        if action == "hit":
            ok, msg = self.blackjack.hit()
        elif action == "stand":
            ok, msg = self.blackjack.stand()
        elif action == "double":
            avail = self.available_tokens
            if self.blackjack.current_bet > avail:
                return False, f"Not enough tokens to double! Need {format_tokens(self.blackjack.current_bet)}."
            ok, msg, extra = self.blackjack.double()
            if ok:
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + extra
        else:
            return False, "Invalid action."
        if ok and self.blackjack.game_state == "finished":
            winnings = self.blackjack.last_winnings
            mauv_mult = self.get_mauville_multiplier()
            if winnings > 0 and mauv_mult > 1.0:
                winnings = int(winnings * mauv_mult)
            if winnings > 0:
                self.state["spent_tokens"] = self.state["spent_tokens"] - winnings
            self._record_catalyst("casino_net_pnl", winnings - self.blackjack.current_bet)
            self.save()
            
        return ok, msg

    # ==========================================
    # 5. Voltorb Flip (HGSS Deduction Puzzle)
    # ==========================================
    def play_voltorb_bet(self, amount_str: str, level: int = None) -> Tuple[bool, str]:
        avail = self.available_tokens
        bet = parse_tokens(amount_str) if amount_str.lower() != "all" else avail
        if bet <= 0:
            return False, "Invalid bet amount! Example: 'bet 500k', 'bet 1m'."
        if bet > avail:
            return False, f"Not enough tokens! You only have {format_tokens(avail)}."

        ok, msg = self.voltorb.start_game(bet, level)
        if ok:
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + bet
            self.save()
        return ok, msg

    def play_voltorb_flip(self, row_str: str, col_str: str) -> Tuple[bool, str]:
        try:
            r = int(row_str)
            c = int(col_str)
        except ValueError:
            return False, "Row and column must be numbers 1 to 5 (e.g. 'flip 1 3')."

        ok, msg = self.voltorb.flip(r, c)
        if ok and self.voltorb.game_state in ["cleared", "game_over"]:
            winnings = self.voltorb.last_winnings
            mauv_mult = self.get_mauville_multiplier()
            if winnings > 0 and mauv_mult > 1.0:
                winnings = int(winnings * mauv_mult)
            if winnings > 0:
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - winnings
            self._record_catalyst("casino_net_pnl", winnings - self.voltorb.current_bet)
            self.save()
        return ok, msg

    def play_voltorb_memo(self, row_str: str, col_str: str, note: str = "") -> Tuple[bool, str]:
        try:
            r = int(row_str)
            c = int(col_str)
        except ValueError:
            return False, "Row and column must be numbers 1 to 5."
        return self.voltorb.memo(r, c, note)

    def play_voltorb_cashout(self) -> Tuple[bool, str]:
        ok, msg, winnings = self.voltorb.cashout()
        if ok:
            mauv_mult = self.get_mauville_multiplier()
            if winnings > 0 and mauv_mult > 1.0:
                winnings = int(winnings * mauv_mult)
            if winnings > 0:
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - winnings
            self._record_catalyst("casino_net_pnl", winnings - self.voltorb.current_bet)
            self.save()
        return ok, msg

    # ==========================================
    # 6. Underground Fossil Excavator
    # ==========================================
    def play_excavator_start(self, cost_str: Optional[str] = None) -> Tuple[bool, str]:
        avail = self.available_tokens
        cost = self.excavator.DEFAULT_COST
        if cost > avail:
            return False, f"Not enough tokens! Excavation requires {format_tokens(cost)} (you have {format_tokens(avail)})."

        ok, msg = self.excavator.start_game()
        if ok:
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
            self.save()
        return ok, msg

    def play_excavator_pick(self, row_str: str, col_str: str) -> Tuple[bool, str]:
        try:
            r = int(row_str)
            c = int(col_str)
        except ValueError:
            return False, "Usage: pick <row 1-6> <col 1-9> (e.g. 'pick 2 4')."

        ok, msg, rewards = self.excavator.pick(r, c)
        if ok and rewards:
            self._apply_excavator_rewards(rewards)
        return ok, msg

    def play_excavator_hammer(self, row_str: str, col_str: str) -> Tuple[bool, str]:
        try:
            r = int(row_str)
            c = int(col_str)
        except ValueError:
            return False, "Usage: hammer <row 1-6> <col 1-9> (e.g. 'hammer 3 5')."

        ok, msg, rewards = self.excavator.hammer(r, c)
        if ok and rewards:
            self._apply_excavator_rewards(rewards)
        return ok, msg

    def _apply_excavator_rewards(self, rewards: list):
        inv = self.state.setdefault("inventory", {})
        total_tokens = 0
        for r in rewards:
            k = r.get("kind")
            val = r.get("val", 0)
            if k == "token":
                total_tokens += val
            elif k in ["item", "fossil"]:
                item_key = r.get("key")
                inv[item_key] = inv.get(item_key, 0) + 1

        if total_tokens > 0:
            mauv_mult = self.get_mauville_multiplier()
            if mauv_mult > 1.0:
                total_tokens = int(total_tokens * mauv_mult)
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - total_tokens

        self._record_catalyst("casino_net_pnl", total_tokens - self.excavator.entry_cost)
        self.save()

    # ==========================================
    # 7. "Who's That Pokémon?" Silhouette Trivia
    # ==========================================
    def play_trivia_start(self, bet_str: str = "500k") -> Tuple[bool, str]:
        avail = self.available_tokens
        bet = parse_tokens(bet_str) if bet_str.lower() != "all" else avail
        if bet <= 0:
            bet = 500_000
        if bet > avail:
            return False, f"Not enough tokens! You have {format_tokens(avail)}."

        ok, msg = self.trivia.start_game(bet)
        if ok:
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + bet
            self.save()
        return ok, msg

    def play_trivia_guess(self, name_str: str) -> Tuple[bool, str]:
        if not name_str.strip():
            return False, "Usage: guess <pokemon name> (e.g. 'guess pikachu')."

        finished, msg, winnings = self.trivia.guess(name_str)
        if finished:
            mauv_mult = self.get_mauville_multiplier()
            if winnings > 0 and mauv_mult > 1.0:
                winnings = int(winnings * mauv_mult)
            if winnings > 0:
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - winnings
            self._record_catalyst("casino_net_pnl", winnings - self.trivia.current_bet)
            self.save()
        return True, msg

    def play_trivia_hint(self) -> Tuple[bool, str]:
        return self.trivia.request_hint()

    def play_trivia_pass(self) -> Tuple[bool, str]:
        ok, msg = self.trivia.give_up()
        if ok:
            self._record_catalyst("casino_net_pnl", -self.trivia.current_bet)
            self.save()
        return ok, msg

    # ==========================================
    # 8. Pokémon Stadium Derby (Hurdle Track)
    # ==========================================
    def play_derby_bet(self, lane_str: str, amount_str: str) -> Tuple[bool, str]:
        try:
            lane = int(lane_str)
        except ValueError:
            return False, "Usage: bet <lane 1-4> <amount> (e.g. 'bet 1 500k')."

        avail = self.available_tokens
        bet = parse_tokens(amount_str) if amount_str.lower() != "all" else avail
        if bet <= 0:
            return False, "Bet amount must be greater than 0!"
        if bet > avail:
            return False, f"Not enough tokens! You only have {format_tokens(avail)}."

        ok, msg = self.derby.place_bet(lane, bet)
        if ok:
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + bet
            self.save()
        return ok, msg

    def play_derby_race(self) -> Tuple[bool, str]:
        ok, msg, winnings = self.derby.resolve_race()
        if ok:
            mauv_mult = self.get_mauville_multiplier()
            if winnings > 0 and mauv_mult > 1.0:
                winnings = int(winnings * mauv_mult)
            if winnings > 0:
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - winnings
            self._record_catalyst("casino_net_pnl", winnings - self.derby.bet_amount)
            self.save()
        return ok, msg

