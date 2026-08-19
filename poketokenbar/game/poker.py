import random
from typing import List, Tuple, Dict, Any

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}

PAYOUTS = {
    "Royal Flush": 250,
    "Straight Flush": 50,
    "Four of a Kind": 25,
    "Full House": 12,
    "Flush": 8,
    "Straight": 5,
    "Three of a Kind": 3,
    "Two Pair": 2,
    "Jacks or Better": 1,
    "High Card": 0
}

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
        self.hand: List[Card] = []
        self.current_bet = 0
        self.game_state = "idle" # "idle", "holding"

    def start_hand(self, bet_amount: int) -> Tuple[bool, str]:
        if bet_amount <= 0:
            return False, "Bet amount must be greater than 0!"
        self.deck = Deck()
        self.hand = self.deck.draw(5)
        self.current_bet = bet_amount
        self.game_state = "holding"
        rank_name, _ = self.evaluate_hand(self.hand)
        return True, f"Dealt hand! Current Rank: {rank_name}. Type 'hold 1 3 5' (or 'hold none' / 'hold all') to draw!"

    def play_draw(self, hold_indices: List[int]) -> Tuple[str, int, int]:
        """
        Swaps cards not in hold_indices (1-based), evaluates final hand, and returns:
        (rank_name, payout_multiplier, winnings)
        """
        # Keep held cards, replace others
        new_hand = []
        for idx in range(1, 6):
            if idx in hold_indices:
                new_hand.append(self.hand[idx - 1])
            else:
                new_hand.append(self.deck.draw(1)[0])

        self.hand = new_hand
        self.game_state = "idle"
        rank_name, mult = self.evaluate_hand(self.hand)
        winnings = self.current_bet * mult
        return rank_name, mult, winnings

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
                return "Royal Flush", PAYOUTS["Royal Flush"]
            return "Straight Flush", PAYOUTS["Straight Flush"]

        if counts == [4, 1]:
            return "Four of a Kind", PAYOUTS["Four of a Kind"]

        if counts == [3, 2]:
            return "Full House", PAYOUTS["Full House"]

        if is_flush:
            return "Flush", PAYOUTS["Flush"]

        if is_straight:
            return "Straight", PAYOUTS["Straight"]

        if counts == [3, 1, 1]:
            return "Three of a Kind", PAYOUTS["Three of a Kind"]

        if counts == [2, 2, 1]:
            return "Two Pair", PAYOUTS["Two Pair"]

        if counts == [2, 1, 1, 1]:
            pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
            if pair_rank >= 11:  # Jacks or Better
                return "Jacks or Better", PAYOUTS["Jacks or Better"]

        return "High Card", PAYOUTS["High Card"]
