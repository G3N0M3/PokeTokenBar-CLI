from typing import Tuple

from poketokenbar.utils.formatting import format_tokens, parse_tokens
from poketokenbar.game.gacha import GachaEngine, GACHA_COST_SINGLE, GACHA_COST_MULTI


class CasinoMixin:
    """Manages Game Corner casino games: Texas Hold'em Poker, Slots, Blackjack, and Capsule Gacha."""

    def play_poker_bet(self, amount_str: str) -> Tuple[bool, str]:
        clean_str = amount_str.lower().strip()
        if clean_str in ["all", "all-in"]:
            bet = self.available_tokens
        else:
            bet = parse_tokens(amount_str)
            if bet < 0:
                return False, "Invalid bet amount! Example: 'bet 500k', 'bet 1m', 'bet all', or 'bet 2000000'."

        if bet <= 0:
            return False, "Bet amount must be greater than 0!"

        avail = self.available_tokens
        if bet > avail:
            return False, f"Not enough tokens! You have {format_tokens(avail)} available tokens."

        # Lock bet by increasing spent_tokens
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + bet
        self.save()

        ok, msg = self.poker.start_hand(bet)
        p_cards = " ".join([str(c) for c in self.poker.player_hole])
        return True, f"♠️ TEXAS HOLD'EM BET {format_tokens(bet)} TOKENS!\n  Your Hole Cards: {p_cards}\n  Community Board: [?] [?] [?] [?] [?]\n  ➔ Type 'check' to reveal the 3 Flop cards!"

    def play_poker_hold(self, hold_str: str) -> Tuple[bool, str]:
        cmd = hold_str.lower().strip()
        if self.poker.game_state == "idle":
            return False, "No active Texas Hold'em hand! Type 'bet <amount>' to start a hand."

        if cmd == "fold":
            outcome, lost = self.poker.play_fold()
            self._record_catalyst("casino_net_pnl", -lost)
            return True, f"🏳️ \033[1m\033[31mYOU FOLDED!\033[0m Surrendered {format_tokens(lost)} tokens to the House."
        elif cmd == "check":
            if self.poker.game_state == "preflop":
                return self.poker.play_flop()
            elif self.poker.game_state == "flop":
                return self.poker.play_turn()
            elif self.poker.game_state == "turn":
                return self._format_poker_showdown()
            else:
                return False, "Game already over."
        elif cmd in ["raise", "allin"]:
            avail = self.available_tokens
            
            if cmd == "raise":
                bet_amount = self.poker.current_bet
            else:
                bet_amount = avail
                
            if bet_amount <= 0:
                return False, "You don't have any more tokens to bet!"
                
            if avail < bet_amount:
                return False, f"Not enough tokens to double bet! Needed: {format_tokens(bet_amount)}"
                
            # Deduct raise bet (increase spent_tokens)
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + bet_amount
            self.poker.current_bet += bet_amount
            self.save()
            
            verb = "ALL-IN!" if cmd == "allin" else "Raised!"
            
            # Advance state automatically after raising
            if self.poker.game_state == "preflop":
                msg = self.poker.play_flop()[1]
                return True, f"💰 {verb} " + msg
            elif self.poker.game_state == "flop":
                msg = self.poker.play_turn()[1]
                return True, f"💰 {verb} " + msg
            elif self.poker.game_state == "turn":
                ok, showdown_msg = self._format_poker_showdown()
                return True, f"💰 {verb}\n" + showdown_msg
            else:
                return False, "Game already over."
        else:
            return False, "Invalid poker action."

    def _format_poker_showdown(self) -> Tuple[bool, str]:
        outcome, p_rank, d_rank, mult, winnings = self.poker.play_showdown()
        
        mauv_mult = self.get_mauville_multiplier()
        if winnings > 0 and outcome == "WIN" and mauv_mult > 1.0:
            winnings = int(winnings * mauv_mult)

        # Grant winnings by decreasing spent_tokens
        if winnings > 0:
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - winnings
            self.save()

        p_hole = " ".join([str(c) for c in self.poker.player_hole])
        d_hole = " ".join([str(c) for c in self.poker.dealer_hole])
        board = " ".join([str(c) for c in self.poker.community_cards])

        bet = self.poker.current_bet
        net_change = winnings - bet
        self._record_catalyst("casino_net_pnl", net_change)
        profit_str = f"+{format_tokens(net_change)}" if net_change >= 0 else f"-{format_tokens(abs(net_change))}"

        res_header = f"♦️ TEXAS HOLD'EM SHOWDOWN!\n  Community Board: {board}\n  🎴 YOUR HOLE:  {p_hole} (\033[1m\033[32m{p_rank}\033[0m)\n  🏠 HOUSE HOLE: {d_hole} (\033[1m\033[31m{d_rank}\033[0m)\n"

        if outcome == "WIN":
            return True, res_header + f"  🏆 Result: \033[1m\033[32mYOU BEAT THE HOUSE!\033[0m ({mult}x Payout! Won \033[1m\033[36m{format_tokens(winnings)}\033[0m Tokens! Net: {profit_str})"
        elif outcome == "PUSH":
            return True, res_header + f"  🤝 Result: \033[1m\033[33mTIE / PUSH!\033[0m Bet of {format_tokens(bet)} Tokens returned."
        else:
            return True, res_header + f"  💀 Result: \033[1m\033[31mHOUSE WINS!\033[0m Lost {format_tokens(bet)} Tokens."

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
                current_tier = self.state.get("egg_tier")
                if current_tier is None:
                    self.state["egg_tier"] = val
                    self.state["egg_usage"] = 0
                else:
                    pending = self.state.get("pending_eggs", [])
                    pending.append(val)
                    self.state["pending_eggs"] = pending

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
