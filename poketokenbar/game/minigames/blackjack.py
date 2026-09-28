import random
from typing import Tuple, List

class BlackjackEngine:
    SUITS = ['♠', '♥', '♦', '♣']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    
    def __init__(self):
        self.game_state = "idle" # "idle", "playing", "finished"
        self.deck: List[str] = []
        self.player_hand: List[str] = []
        self.dealer_hand: List[str] = []
        self.current_bet = 0
        self.last_result = ""
        self.last_winnings = 0
        
    def get_value(self, hand: List[str]) -> int:
        value = 0
        aces = 0
        for card in hand:
            rank = card[:-1]
            if rank in ['J', 'Q', 'K']:
                value += 10
            elif rank == 'A':
                aces += 1
                value += 11
            else:
                value += int(rank)
        
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
            
        return value

    def reset_deck(self):
        self.deck = [f"{rank}{suit}" for suit in self.SUITS for rank in self.RANKS]
        random.shuffle(self.deck)

    def draw(self) -> str:
        if not self.deck:
            self.reset_deck()
        return self.deck.pop()

    def start_game(self, bet: int) -> Tuple[bool, str]:
        if self.game_state == "playing":
            return False, "You are already in a game!"
            
        self.reset_deck()
        self.current_bet = bet
        
        self.player_hand = [self.draw(), self.draw()]
        self.dealer_hand = [self.draw(), self.draw()]
        
        self.game_state = "playing"
        self.last_result = ""
        self.last_winnings = 0
        
        # Check for immediate Blackjack
        p_val = self.get_value(self.player_hand)
        if p_val == 21:
            self.game_state = "finished"
            d_val = self.get_value(self.dealer_hand)
            if d_val == 21:
                self.last_result = "Push (Tie) - Both got Blackjack!"
                self.last_winnings = bet
            else:
                self.last_result = "BLACKJACK! You win 2.5x!"
                self.last_winnings = int(bet * 2.5)
            return True, self.last_result
            
        return True, "Hand dealt! Type 'hit' or 'stand'."

    def hit(self) -> Tuple[bool, str]:
        if self.game_state != "playing":
            return False, "You are not in a game!"
            
        self.player_hand.append(self.draw())
        val = self.get_value(self.player_hand)
        
        if val > 21:
            self.game_state = "finished"
            self.last_result = "BUST! You went over 21."
            self.last_winnings = 0
            return True, self.last_result
        elif val == 21:
            return self.stand()
            
        return True, f"Hit! Your total is {val}."

    def double(self) -> Tuple[bool, str, int]:
        """Returns success, msg, extra_bet_amount"""
        if self.game_state != "playing":
            return False, "You are not in a game!", 0
        if len(self.player_hand) > 2:
            return False, "You can only double on your first two cards!", 0
            
        extra_bet = self.current_bet
        self.current_bet *= 2
        
        self.player_hand.append(self.draw())
        val = self.get_value(self.player_hand)
        
        if val > 21:
            self.game_state = "finished"
            self.last_result = "BUST on double! You went over 21."
            self.last_winnings = 0
            return True, self.last_result, extra_bet
            
        return self.stand(extra_bet_flag=True, extra_bet=extra_bet)

    def stand(self, extra_bet_flag=False, extra_bet=0) -> Tuple[bool, str] | Tuple[bool, str, int]:
        if self.game_state != "playing":
            if extra_bet_flag: return False, "You are not in a game!", 0
            return False, "You are not in a game!"
            
        self.game_state = "finished"
        
        # Dealer plays
        while self.get_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.draw())
            
        p_val = self.get_value(self.player_hand)
        d_val = self.get_value(self.dealer_hand)
        
        if d_val > 21:
            self.last_result = "Dealer BUSTS! You win!"
            self.last_winnings = self.current_bet * 2
        elif p_val > d_val:
            self.last_result = "You WIN!"
            self.last_winnings = self.current_bet * 2
        elif p_val < d_val:
            self.last_result = "Dealer WINS."
            self.last_winnings = 0
        else:
            self.last_result = "Push (Tie)."
            self.last_winnings = self.current_bet
            
        if extra_bet_flag:
            return True, self.last_result, extra_bet
        return True, self.last_result
