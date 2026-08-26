import random
from typing import Tuple, List

class SlotMachineEngine:
    SYMBOLS = ["🍒", "🍋", "🍇", "🍉", "🔔", "💎", "⭐"]
    
    # Weightings for each symbol (lower weight = rarer)
    WEIGHTS = [40, 30, 20, 15, 10, 5, 2]
    
    PAYOUTS = {
        "🍒": 3,
        "🍋": 5,
        "🍇": 8,
        "🍉": 10,
        "🔔": 15,
        "💎": 25,
        "⭐": 100,
    }
    
    def __init__(self):
        self.last_reels = ["-", "-", "-"]
        self.last_payout_mult = 0.0
        self.last_win_amount = 0
    
    def spin(self, bet: int) -> Tuple[List[str], float, int]:
        """Spins the slots and returns (reels, multiplier, win_amount)"""
        # Spin 3 reels independently based on weights
        self.last_reels = random.choices(self.SYMBOLS, weights=self.WEIGHTS, k=3)
        
        # Check for 3 of a kind
        if self.last_reels[0] == self.last_reels[1] == self.last_reels[2]:
            self.last_payout_mult = self.PAYOUTS[self.last_reels[0]]
        # Or check for 2 cherries as a small consolation
        elif self.last_reels.count("🍒") == 2:
            self.last_payout_mult = 1.5
        # Or 1 cherry
        elif self.last_reels.count("🍒") == 1:
            self.last_payout_mult = 0.5
        else:
            self.last_payout_mult = 0.0
            
        self.last_win_amount = int(bet * self.last_payout_mult)
        return self.last_reels, self.last_payout_mult, self.last_win_amount
