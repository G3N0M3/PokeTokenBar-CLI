import random
from typing import List, Tuple, Dict, Any

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}

class Card:
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit

    @property
    def value(self) -> int:
        return RANK_VALUES[self.rank]

    def __str__(self) -> str:
        color_code = "\033[91m" if self.suit in ["♥", "♦"] else "\033[97m"
        reset = "\033[0m"
        return f"{color_code}[{self.rank:>2}{self.suit}]{reset}"

class Deck:
    def __init__(self):
        self.cards = [Card(r, s) for s in SUITS for r in RANKS]
        random.shuffle(self.cards)

    def draw(self, count: int = 1) -> List[Card]:
        drawn = self.cards[:count]
        self.cards = self.cards[count:]
        return drawn

class PokerEngine:
    def __init__(self):
        self.deck = Deck()
        self.player_hand: List[Card] = []
        self.dealer_hand: List[Card] = []
        self.current_bet = 0
        self.game_state = "idle" # "idle", "holding"

    def start_hand(self, bet_amount: int) -> Tuple[bool, str]:
        if bet_amount <= 0:
            return False, "Bet amount must be greater than 0!"
        self.deck = Deck()
        self.player_hand = self.deck.draw(5)
        self.dealer_hand = self.deck.draw(5)
        self.current_bet = bet_amount
        self.game_state = "holding"

        p_name, p_score = self.evaluate_hand(self.player_hand)
        return True, f"Dealt hand! Your Current Rank: {p_name}. Dealer has 5 face-down cards. Type 'hold 1 3 5' (or 'hold none' / 'hold all') to draw against the House!"

    def play_showdown(self, hold_indices: List[int]) -> Tuple[str, str, str, int, int]:
        """
        Executes draw for Player and Dealer AI, compares hands, and returns:
        (outcome_str, player_rank_name, dealer_rank_name, payout_multiplier, total_winnings)
        """
        # 1. Player Draw
        new_player_hand = []
        for idx in range(1, 6):
            if idx in hold_indices:
                new_player_hand.append(self.player_hand[idx - 1])
            else:
                new_player_hand.append(self.deck.draw(1)[0])
        self.player_hand = new_player_hand

        # 2. Dealer AI Strategy Draw
        dealer_holds = self._dealer_ai_strategy(self.dealer_hand)
        new_dealer_hand = []
        for idx in range(1, 6):
            if idx in dealer_holds:
                new_dealer_hand.append(self.dealer_hand[idx - 1])
            else:
                new_dealer_hand.append(self.deck.draw(1)[0])
        self.dealer_hand = new_dealer_hand

        self.game_state = "idle"

        # 3. Evaluate Hands
        p_name, p_score = self.evaluate_hand(self.player_hand)
        d_name, d_score = self.evaluate_hand(self.dealer_hand)

        # 4. Compare Hands against the House
        if p_score > d_score:
            # Player Wins! Determine payout multiplier
            mult = self._get_win_multiplier(p_name)
            outcome = "WIN"
            winnings = self.current_bet * mult
        elif p_score == d_score:
            # Push / Tie
            mult = 1
            outcome = "PUSH"
            winnings = self.current_bet
        else:
            # House Wins
            mult = 0
            outcome = "LOSS"
            winnings = 0

        return outcome, p_name, d_name, mult, winnings

    def _dealer_ai_strategy(self, hand: List[Card]) -> List[int]:
        """Dealer AI determines 1-based card indices to hold."""
        ranks = [c.value for c in hand]
        rank_counts = {r: ranks.count(r) for r in set(ranks)}

        # Holds indices of paired/tripled cards
        holds = []
        for idx, card in enumerate(hand, 1):
            if rank_counts[card.value] >= 2:
                holds.append(idx)

        if not holds:
            # High card: Hold top 2 cards
            sorted_with_idx = sorted(enumerate(hand, 1), key=lambda x: x[1].value, reverse=True)
            holds = [sorted_with_idx[0][0], sorted_with_idx[1][0]]

        return holds

    @staticmethod
    def _get_win_multiplier(rank_name: str) -> int:
        multipliers = {
            "Royal Flush": 50,
            "Straight Flush": 15,
            "Four of a Kind": 8,
            "Full House": 5,
            "Flush": 4,
            "Straight": 3,
            "Three of a Kind": 2,
            "Two Pair": 2,
            "One Pair": 2,
            "High Card": 2
        }
        return multipliers.get(rank_name, 2)

    @staticmethod
    def evaluate_hand(hand: List[Card]) -> Tuple[str, int]:
        ranks = sorted([c.value for c in hand])
        suits = [c.suit for c in hand]
        rank_counts = {r: ranks.count(r) for r in set(ranks)}
        counts = sorted(rank_counts.values(), reverse=True)

        is_flush = len(set(suits)) == 1
        is_straight = (len(set(ranks)) == 5) and (ranks[4] - ranks[0] == 4 or ranks == [2, 3, 4, 5, 14])

        if is_straight and is_flush:
            if ranks == [10, 11, 12, 13, 14]:
                return "Royal Flush", 10_000_000 + max(ranks)
            return "Straight Flush", 9_000_000 + max(ranks)

        if counts == [4, 1]:
            four_rank = [r for r, c in rank_counts.items() if c == 4][0]
            return "Four of a Kind", 8_000_000 + four_rank * 100 + max(ranks)

        if counts == [3, 2]:
            three_rank = [r for r, c in rank_counts.items() if c == 3][0]
            pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
            return "Full House", 7_000_000 + three_rank * 100 + pair_rank

        if is_flush:
            return "Flush", 6_000_000 + sum(ranks)

        if is_straight:
            return "Straight", 5_000_000 + max(ranks)

        if counts == [3, 1, 1]:
            three_rank = [r for r, c in rank_counts.items() if c == 3][0]
            return "Three of a Kind", 4_000_000 + three_rank * 100 + sum(ranks)

        if counts == [2, 2, 1]:
            pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
            kicker = [r for r, c in rank_counts.items() if c == 1][0]
            return "Two Pair", 3_000_000 + pairs[0] * 1000 + pairs[1] * 100 + kicker

        if counts == [2, 1, 1, 1]:
            pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
            return "One Pair", 2_000_000 + pair_rank * 100 + sum(ranks)

        return "High Card", 1_000_000 + max(ranks) * 100 + sum(ranks)
