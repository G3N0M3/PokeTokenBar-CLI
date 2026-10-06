import random
import itertools
from typing import List, Tuple

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
        self.community_revealed: int = 0
        self.current_bet = 0
        self.game_state = "idle"  # "idle", "preflop", "flop", "turn"
        self.last_outcome: str = ""
        self.last_p_rank: str = ""
        self.last_d_rank: str = ""
        self.last_winnings: int = 0
        self.last_net: str = ""

    @property
    def player_hand(self) -> List[Card]:
        return self.player_hole

    @player_hand.setter
    def player_hand(self, cards: List[Card]):
        self.player_hole = cards

    @property
    def dealer_hand(self) -> List[Card]:
        return self.dealer_hole

    @dealer_hand.setter
    def dealer_hand(self, cards: List[Card]):
        self.dealer_hole = cards

    def start_hand(self, bet_amount: int) -> Tuple[bool, str]:
        if self.game_state != "idle":
            return False, "A hand is already in progress! Type 'check', 'raise', 'allin', or 'fold'."
        if bet_amount <= 0:
            return False, "Bet amount must be greater than 0!"
        self.deck = Deck()
        self.player_hole = self.deck.draw(2)
        self.dealer_hole = self.deck.draw(2)
        self.community_cards = self.deck.draw(5)
        self.community_revealed = 0
        self.current_bet = bet_amount
        self.game_state = "preflop"
        self.last_outcome = ""
        return True, "♠️ Hand dealt!"

    def play_flop(self) -> Tuple[bool, str]:
        if self.game_state != "preflop":
            return False, "Not in Pre-Flop phase! Start a hand with 'bet <amount>' first."

        self.community_revealed = 3
        self.game_state = "flop"
        return True, "♦️ Flop revealed!"

    def play_turn(self) -> Tuple[bool, str]:
        if self.game_state != "flop":
            return False, "Not in Flop phase! Type 'check' first."

        self.community_revealed = 4
        self.game_state = "turn"
        return True, "♦️ Turn revealed!"

    def play_fold(self) -> Tuple[str, int]:
        """Player surrenders current hand."""
        self.game_state = "idle"
        self.last_outcome = "FOLD"
        lost_amount = self.current_bet
        return "FOLD", lost_amount

    def play_showdown(self) -> Tuple[str, str, str, int, int]:
        """
        Evaluates best 5-card hands out of 7, and returns:
        (outcome, player_rank_name, dealer_rank_name, multiplier, total_winnings)
        """
        self.community_revealed = 5
        self.game_state = "idle"

        player_all = self.player_hole + self.community_cards
        dealer_all = self.dealer_hole + self.community_cards

        p_rank_name, p_score, _ = self.best_5_card_hand(player_all)
        d_rank_name, d_score, _ = self.best_5_card_hand(dealer_all)

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

        self.last_outcome = outcome
        self.last_p_rank = p_rank_name
        self.last_d_rank = d_rank_name
        self.last_winnings = winnings
        return outcome, p_rank_name, d_rank_name, mult, winnings

    def get_hand_type(self, hole_cards: List[Card], community_cards: List[Card] = None) -> str:
        """
        Returns the human-readable poker hand type (e.g. 'One Pair', 'Flush')
        for the given hole cards combined with currently revealed community cards.
        """
        if not hole_cards:
            return ""
        if community_cards is None:
            revealed = 5 if self.game_state == "idle" else self.community_revealed
            comm = self.community_cards[:revealed]
        else:
            comm = community_cards

        cards = list(hole_cards) + list(comm)
        if len(cards) < 5:
            ranks = [c.rank for c in cards]
            counts = {r: ranks.count(r) for r in set(ranks)}
            max_count = max(counts.values()) if counts else 1
            if max_count == 4:
                return "Four of a Kind"
            elif max_count == 3:
                return "Three of a Kind"
            elif max_count == 2:
                pair_count = sum(1 for c in counts.values() if c == 2)
                return "Two Pair" if pair_count >= 2 else "One Pair"
            return "High Card"

        name, _, _ = self.best_5_card_hand(cards)
        return name

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
        }
        return multipliers.get(rank_name, 2)

    @staticmethod
    def evaluate_5_cards(hand: List[Card]) -> Tuple[str, int]:
        ranks = sorted([c.value for c in hand], reverse=True)
        suits = [c.suit for c in hand]
        rank_counts = {r: ranks.count(r) for r in set(ranks)}
        
        # Sort by count descending, then rank descending
        # Example: Full house KKK22 -> [ (3, 13), (2, 2) ]
        sorted_rc = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        counts = [x[1] for x in sorted_rc]
        ordered_ranks = []
        for r, c in sorted_rc:
            ordered_ranks.extend([r] * c)
            
        is_flush = len(set(suits)) == 1
        
        # Check straight
        is_straight = False
        if ranks == [14, 5, 4, 3, 2]:
            is_straight = True
            ordered_ranks = [5, 4, 3, 2, 1] # Treat Ace as 1 for tiebreaker
        elif len(set(ranks)) == 5 and ranks[0] - ranks[4] == 4:
            is_straight = True
            ordered_ranks = ranks

        def score(tier, r):
            res = tier << 20
            for i, val in enumerate(r):
                res |= (val << (16 - i * 4))
            return res

        if is_straight and is_flush:
            if ordered_ranks[0] == 14:
                return "Royal Flush", score(9, ordered_ranks)
            return "Straight Flush", score(8, ordered_ranks)
            
        if counts == [4, 1]:
            return "Four of a Kind", score(7, ordered_ranks)
            
        if counts == [3, 2]:
            return "Full House", score(6, ordered_ranks)
            
        if is_flush:
            return "Flush", score(5, ordered_ranks)
            
        if is_straight:
            return "Straight", score(4, ordered_ranks)
            
        if counts == [3, 1, 1]:
            return "Three of a Kind", score(3, ordered_ranks)
            
        if counts == [2, 2, 1]:
            return "Two Pair", score(2, ordered_ranks)
            
        if counts == [2, 1, 1, 1]:
            return "One Pair", score(1, ordered_ranks)
            
        return "High Card", score(0, ordered_ranks)
