import random
from dataclasses import dataclass
from typing import List, Tuple, Optional
from poketokenbar.utils.formatting import format_tokens


@dataclass
class VoltorbCard:
    value: int  # 0 = Voltorb, 1, 2, 3
    revealed: bool = False
    memo: str = ""  # e.g., "1", "2", "3", "v", "x"


class VoltorbFlipEngine:
    """Engine for Voltorb Flip, the HGSS deduction card puzzle."""

    # Level specs: (count_of_2s, count_of_3s, count_of_voltorbs)
    LEVEL_SPECS = {
        1: (3, 1, 6),
        2: (4, 2, 7),
        3: (3, 4, 8),
        4: (4, 4, 8),
        5: (5, 4, 9),
        6: (4, 5, 10),
        7: (3, 6, 10),
        8: (2, 7, 10),
    }

    def __init__(self):
        self.game_state: str = "idle"  # "idle", "playing", "game_over", "cleared", "cashed_out"
        self.current_level: int = 1
        self.current_bet: int = 0
        self.current_multiplier: int = 1
        self.board: List[List[VoltorbCard]] = []
        self.row_points: List[int] = [0] * 5
        self.row_voltorbs: List[int] = [0] * 5
        self.col_points: List[int] = [0] * 5
        self.col_voltorbs: List[int] = [0] * 5
        self.total_target_cards: int = 0
        self.target_cards_flipped: int = 0
        self.cards_flipped: int = 0
        self.last_result: str = ""
        self.last_winnings: int = 0

    def start_game(self, bet: int, level: Optional[int] = None) -> Tuple[bool, str]:
        if self.game_state == "playing":
            return False, "You already have an active Voltorb Flip game! Flip cards or type 'cashout'."

        if level is not None and 1 <= level <= 8:
            self.current_level = level

        spec = self.LEVEL_SPECS.get(self.current_level, self.LEVEL_SPECS[1])
        num_2s, num_3s, num_voltorbs = spec
        num_1s = 25 - (num_2s + num_3s + num_voltorbs)

        cards_pool = [2] * num_2s + [3] * num_3s + [0] * num_voltorbs + [1] * num_1s
        random.shuffle(cards_pool)

        self.board = []
        for r in range(5):
            row_cards = []
            for c in range(5):
                row_cards.append(VoltorbCard(value=cards_pool[r * 5 + c]))
            self.board.append(row_cards)

        self.total_target_cards = num_2s + num_3s
        self.target_cards_flipped = 0
        self.cards_flipped = 0
        self.current_bet = bet
        self.current_multiplier = 1
        self.last_winnings = 0
        self.last_result = ""

        # Compute row & column hints
        self.row_points = [sum(self.board[r][c].value for c in range(5)) for r in range(5)]
        self.row_voltorbs = [sum(1 for c in range(5) if self.board[r][c].value == 0) for r in range(5)]
        self.col_points = [sum(self.board[r][c].value for r in range(5)) for c in range(5)]
        self.col_voltorbs = [sum(1 for r in range(5) if self.board[r][c].value == 0) for c in range(5)]

        self.game_state = "playing"
        return True, f"Voltorb Flip Level {self.current_level} started with {format_tokens(bet)} bet! Type 'flip <row> <col>' to begin."

    def flip(self, row: int, col: int) -> Tuple[bool, str]:
        if self.game_state != "playing":
            return False, "No active game! Type 'bet <amount>' to start."

        if not (1 <= row <= 5 and 1 <= col <= 5):
            return False, "Invalid card coordinates! Rows and columns must be 1 to 5 (e.g. 'flip 1 3')."

        card = self.board[row - 1][col - 1]
        if card.revealed:
            return False, f"Card [{row}, {col}] has already been flipped!"

        card.revealed = True
        self.cards_flipped += 1

        if card.value == 0:
            # Voltorb explosion!
            self.game_state = "game_over"
            self.last_winnings = 0
            self.last_result = f"💥 KABOOM! You hit a Voltorb at [{row}, {col}]! Lost {format_tokens(self.current_bet)} tokens."
            # Demote level if very few cards flipped
            if self.cards_flipped < self.current_level:
                self.current_level = max(1, self.current_level - 1)
            # Reveal all cards
            for r in range(5):
                for c in range(5):
                    self.board[r][c].revealed = True
            return True, self.last_result

        # Safe card
        if card.value > 1:
            self.current_multiplier *= card.value
            self.target_cards_flipped += 1

        if self.target_cards_flipped == self.total_target_cards:
            # Board cleared!
            self.game_state = "cleared"
            self.last_winnings = self.current_bet * self.current_multiplier
            old_level = self.current_level
            self.current_level = min(8, self.current_level + 1)
            self.last_result = (
                f"🌟 BOARD CLEARED! All multipliers revealed!\n"
                f"  Payout: {self.current_multiplier}x ({format_tokens(self.last_winnings)} tokens)! "
                f"Advanced from Level {old_level} to Level {self.current_level}!"
            )
            # Reveal all remaining cards
            for r in range(5):
                for c in range(5):
                    self.board[r][c].revealed = True
            return True, self.last_result

        return True, f"Flipped card [{row}, {col}]: Value {card.value}! Multiplier: {self.current_multiplier}x (Potential: {format_tokens(self.current_bet * self.current_multiplier)})"

    def memo(self, row: int, col: int, note: str) -> Tuple[bool, str]:
        if not (1 <= row <= 5 and 1 <= col <= 5):
            return False, "Coordinates must be 1 to 5."
        card = self.board[row - 1][col - 1]
        if card.revealed:
            return False, "Cannot memo an already revealed card."
        note_clean = note.strip()[:3]
        card.memo = note_clean
        if note_clean:
            return True, f"Marked card [{row}, {col}] with memo '{note_clean}'."
        return True, f"Cleared memo on card [{row}, {col}]."

    def cashout(self) -> Tuple[bool, str, int]:
        if self.game_state != "playing":
            return False, "No active game to cash out from.", 0

        if self.current_multiplier <= 1 and self.cards_flipped == 0:
            return False, "You haven't flipped any cards yet!", 0

        self.game_state = "cashed_out"
        self.last_winnings = self.current_bet * self.current_multiplier
        self.last_result = f"💰 CASHED OUT! Banked {self.current_multiplier}x payout: won {format_tokens(self.last_winnings)} tokens!"

        # Reveal rest of board
        for r in range(5):
            for c in range(5):
                self.board[r][c].revealed = True

        return True, self.last_result, self.last_winnings
