import random
from typing import Tuple, List

class SlotMachineEngine:
    SYMBOLS = ["🍒", "🍋", "🍇", "🍉", "🔔", "💎", "⭐"]
    
    # Weightings for each symbol (lower weight = rarer)
    WEIGHTS = [40, 30, 20, 15, 10, 5, 2]
    
    PAYOUTS = {
        "🍒": 5,
        "🍋": 10,
        "🍇": 15,
        "🍉": 25,
        "🔔": 50,
        "💎": 100,
        "⭐": 250,
    }
    
    def __init__(self):
        self.last_reels = [["-", "-", "-"], ["-", "-", "-"], ["-", "-", "-"]]
        self.last_payout_mult = 0.0
        self.last_win_amount = 0
    
    def spin(self, bet: int) -> Tuple[List[List[str]], float, int]:
        """Spins the slots and returns (reels, multiplier, win_amount)"""
        # Spin 3x3 grid
        self.last_reels = [
            random.choices(self.SYMBOLS, weights=self.WEIGHTS, k=3),
            random.choices(self.SYMBOLS, weights=self.WEIGHTS, k=3),
            random.choices(self.SYMBOLS, weights=self.WEIGHTS, k=3)
        ]
        
        paylines = [
            self.last_reels[0], # Top row
            self.last_reels[1], # Middle row
            self.last_reels[2], # Bottom row
            [self.last_reels[0][0], self.last_reels[1][1], self.last_reels[2][2]], # Diagonal 1
            [self.last_reels[2][0], self.last_reels[1][1], self.last_reels[0][2]]  # Diagonal 2
        ]
        
        total_mult = 0.0
        for line in paylines:
            if line[0] == line[1] == line[2]:
                total_mult += self.PAYOUTS[line[0]]
            elif line.count("🍒") == 2:
                total_mult += 2.0
            elif line.count("🍒") == 1:
                total_mult += 0.5
            
        self.last_payout_mult = total_mult / 5.0
        self.last_win_amount = int(bet * self.last_payout_mult)
        return self.last_reels, self.last_payout_mult, self.last_win_amount
