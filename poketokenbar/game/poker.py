import random
import itertools
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

class TexasHoldemEngine:
    def __init__(self):
        self.deck = Deck()
        self.player_hole: List[Card] = []
        self.dealer_hole: List[Card] = []
        self.community_cards: List[Card] = []
        self.current_bet = 0
        self.game_state = "idle" # "idle", "preflop", "flop", "turn", "river", "showdown"

    def start_hand(self, bet_amount: int) -> Tuple[bool, str]:
        if bet_amount <= 0:
            return False, "Bet amount must be greater than 0!"
        self.deck = Deck()
        self.player_hole = self.deck.draw(2)
        self.dealer_hole = self.deck.draw(2)
        self.community_cards = self.deck.draw(5)
        self.current_bet = bet_amount
        self.game_state = "flop"

        p_cards = " ".join([str(c) for c in self.player_hole])
        return True, f"♠️ TEXAS HOLD 'EM DEALT! Your Hole Cards: {p_cards}\n  Community Board: [?] [?] [?] [?] [?]\n  ➔ Type 'flop' (or 'call') to reveal the 3 Flop cards!"

    def play_flop(self) -> Tuple[bool, str]:
        if self.game_state != "flop":
            return False, "Not in Flop phase! Start a hand with 'bet <amount>' first."

        self.game_state = "turn"
        p_cards = " ".join([str(c) for c in self.player_hole])
        flop_cards = " ".join([str(c) for c in self.community_cards[:3]])
        return True, f"♦️ THE FLOP REVEALED!\n  Your Hole: {p_cards}\n  Board:     {flop_cards} [?] [?]\n  ➔ Type 'turn' to reveal the Turn & River, or 'raise' to double bet!"

    def play_raise(self) -> Tuple[bool, str]:
        if self.game_state not in ["flop", "turn"]:
            return False, "Cannot raise right now!"
        
        self.current_bet *= 2
        return self.play_showdown()

    def play_showdown(self) -> Tuple[str, str, str, int, int]:
        """
        Reveals Turn & River, evaluates best 5-card hands out of 7, and returns:
        (outcome, player_rank_name, dealer_rank_name, multiplier, total_winnings)
        """
        self.game_state = "idle"

        player_all = self.player_hole + self.community_cards
        dealer_all = self.dealer_hole + self.community_cards

        p_rank_name, p_score, p_best = self.best_5_card_hand(player_all)
        d_rank_name, d_score, d_best = self.best_5_card_hand(dealer_all)

        if p_score > d_score:
            mult = self._get_win_multiplier(p_rank_name)
            outcome = "WIN"
            winnings = self.current_bet * mult
        elif p_score == d_score:
            mult = 1
            outcome = "PUSH"
            winnings = self.current_bet
        else:
            mult = 0
            outcome = "LOSS"
            winnings = 0

        return outcome, p_rank_name, d_rank_name, mult, winnings

    @classmethod
    def best_5_card_hand(cls, cards7: List[Card]) -> Tuple[str, int, List[Card]]:
        best_score = -1
        best_rank_name = "High Card"
        best_combo = cards7[:5]

        for combo in itertools.combinations(cards7, 5):
            name, score = cls.evaluate_5_cards(list(combo))
            if score > best_score:
                best_score = score
                best_rank_name = name
                best_combo = list(combo)

        return best_rank_name, best_score, best_combo

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
    def evaluate_5_cards(hand: List[Card]) -> Tuple[str, int]:
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
