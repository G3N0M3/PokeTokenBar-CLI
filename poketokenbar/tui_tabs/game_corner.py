import sys
from poketokenbar.utils.formatting import format_tokens

HEADER = "\033[95m\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def render_game_corner_tab(app):
    state = getattr(app, 'minigame_state', 'menu')
    if state == 'poker':
        app.render_poker_tab()
    elif state == 'gacha':
        app.render_gacha_tab()
    elif state == 'slot':
        app.render_slot_tab()
    elif state == 'blackjack':
        app.render_blackjack_tab()
    else:
        app.render_game_corner_menu()

def render_game_corner_menu(app):
    sys.stdout.write(f"\n  {BOLD}{HEADER}🎰 Welcome to the Token Game Corner!{RESET}\n\n")
    sys.stdout.write(f"  {BOLD}Available Games:{RESET}\n")
    sys.stdout.write(f"   {CYAN}1. Hold'em Poker{RESET} - High stakes Texas Hold'em against the dealer.\n")
    sys.stdout.write(f"   {CYAN}2. Gacha Capsules{RESET} - Try your luck to win rare Pokémon, Eggs, and Mega Stones!\n")
    sys.stdout.write(f"   {CYAN}3. Token Slots{RESET}    - A fast-paced slot machine.\n")
    sys.stdout.write(f"   {CYAN}4. Blackjack{RESET}      - Classic 21 against the dealer.\n\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}play <idx>{RESET}' to start a game (e.g., 'play 1' for Poker).\n\n")
    
def render_slot_tab(app):
    avail = app.engine.available_tokens
    if getattr(app, 'slot_animating', False):
        avail = max(0, avail - app.engine.slots.last_win_amount)
        
    sys.stdout.write(f"\n  {BOLD}{HEADER}🎰 Token Slots{RESET}\n\n")
    sys.stdout.write(f"  Available Tokens to Bet: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n\n")
    
    sys.stdout.write(f"  {BOLD}Payouts (3 of a kind):{RESET}\n")
    sys.stdout.write(f"  ⭐ : 100x | 💎 : 25x | 🔔 : 15x | 🍉 : 10x | 🍇 : 8x | 🍋 : 5x | 🍒 : 3x\n")
    sys.stdout.write(f"  {BOLD}Consolation:{RESET} 🍒🍒 = 1.5x | 🍒 = 0.5x\n\n")
    
    if getattr(app, 'slot_animating', False):
        grid = getattr(app, 'slot_current_reels', [["?", "?", "?"], ["?", "?", "?"], ["?", "?", "?"]])
        sys.stdout.write(f"  {BOLD}Spinning:{RESET}\n")
        for row in grid:
            sys.stdout.write(f"   [ {' | '.join(row)} ]\n")
        sys.stdout.write(f"\n  {BOLD}{YELLOW}Good luck...{RESET}\n\n")
    elif app.engine.slots.last_win_amount > 0 or app.engine.slots.last_reels != [["-", "-", "-"], ["-", "-", "-"], ["-", "-", "-"]]:
        grid = app.engine.slots.last_reels
        sys.stdout.write(f"  {BOLD}Last Spin:{RESET}\n")
        for row in grid:
            sys.stdout.write(f"   [ {' | '.join(row)} ]\n")
        if app.engine.slots.last_win_amount > 0:
            sys.stdout.write(f"\n  {BOLD}{YELLOW}WINNER! {app.engine.slots.last_payout_mult:.1f}x total payout! Won {format_tokens(app.engine.slots.last_win_amount)}{RESET}\n\n")
        else:
            sys.stdout.write(f"\n  {BOLD}{RED}No payout.{RESET}\n\n")
    
    sys.stdout.write(f"  ➔ Type '{BOLD}spin <amount>{RESET}' to play (e.g. 'spin 500k', 'spin 1m').\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}leave{RESET}' to return to the Game Corner Menu.\n\n")
    
def render_blackjack_tab(app):
    avail = app.engine.available_tokens
    sys.stdout.write(f"\n  {BOLD}{HEADER}🃏 Casino Blackjack (21){RESET}\n\n")
    sys.stdout.write(f"  Available Tokens to Bet: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n\n")
    
    sys.stdout.write(f"  {BOLD}🃏 Rules:{RESET}\n")
    sys.stdout.write(f"   • Get closer to 21 than the dealer without going over (Bust).\n")
    sys.stdout.write(f"   • Dealer must hit on 16 and stand on 17. Blackjack pays 2.5x.\n\n")
    
    sys.stdout.write(f"  ➔ Step 1: Type '{BOLD}bet <amount>{RESET}' to start (e.g. 'bet 500k').\n")
    sys.stdout.write(f"  ➔ Step 2: Type '{BOLD}hit{RESET}' to take a card, or '{BOLD}stand{RESET}' to hold your total.\n")
    sys.stdout.write(f"  ➔ Step 3: Type '{BOLD}double{RESET}' to double your bet and take exactly one more card.\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}leave{RESET}' to return to the Game Corner Menu.\n\n")
    
    if app.engine.blackjack.game_state != "idle":
        state_str = "Dealing Phase" if app.engine.blackjack.game_state == "playing" else "Showdown Completed"
        p_hand = " ".join(app.engine.blackjack.player_hand)
        p_val = app.engine.blackjack.get_value(app.engine.blackjack.player_hand)
        
        if app.engine.blackjack.game_state == "playing":
            d_hand = app.engine.blackjack.dealer_hand[0] + " [?]"
            d_val_str = "?"
        else:
            d_hand = " ".join(app.engine.blackjack.dealer_hand)
            d_val_str = str(app.engine.blackjack.get_value(app.engine.blackjack.dealer_hand))
            
        sys.stdout.write(f"  {BOLD}Active Table [{state_str}]:{RESET}\n")
        sys.stdout.write(f"   👤 Your Hand:  {p_hand}  (Total: {p_val})\n")
        sys.stdout.write(f"   🏠 House Hand: {d_hand}  (Total: {d_val_str})\n")
        sys.stdout.write(f"   Current Bet: {BOLD}{YELLOW}{format_tokens(app.engine.blackjack.current_bet)}{RESET} tokens\n\n")
        
        if app.engine.blackjack.game_state == "finished":
            if app.engine.blackjack.last_winnings > 0:
                sys.stdout.write(f"  {BOLD}{GREEN}{app.engine.blackjack.last_result} Won {format_tokens(app.engine.blackjack.last_winnings)} tokens!{RESET}\n\n")
            else:
                sys.stdout.write(f"  {BOLD}{RED}{app.engine.blackjack.last_result} Lost {format_tokens(app.engine.blackjack.current_bet)} tokens.{RESET}\n\n")

def render_poker_tab(app):
    avail = app.engine.available_tokens
    sys.stdout.write(f"\n  {BOLD}{HEADER}♠️ Casino Texas Hold'em (You vs. The House!){RESET}\n\n")
    sys.stdout.write(f"  Available Tokens to Bet: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n\n")

    sys.stdout.write(f"  {BOLD}🃏 Rules & Payout Multipliers:{RESET}\n")
    sys.stdout.write(f"   • Receive 2 Hole Cards. Beat the House Dealer's best 5-card hand!\n")
    sys.stdout.write(f"   • Winning Bonus Multipliers: Royal Flush [50x] | Straight Flush [15x]\n")
    sys.stdout.write(f"   • Four of a Kind [8x] | Full House [5x] | Flush [4x] | Straight [3x]\n\n")

    sys.stdout.write(f"  ➔ Step 1: Type '{BOLD}bet <amount>{RESET}' to deal 2 Hole Cards (e.g. 'bet 1m').\n")
    sys.stdout.write(f"  ➔ Step 2: Type '{BOLD}check{RESET}' to reveal community cards, or '{BOLD}fold{RESET}'\n")
    sys.stdout.write(f"  ➔ Step 3: Type '{BOLD}raise{RESET}' to double your bet, or '{BOLD}allin{RESET}' to bet EVERYTHING!\n")
    sys.stdout.write(f"  ➔ Note: You can raise multiple times in a single hand.\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}leave{RESET}' to return to the Game Corner Menu.\n\n")

    if app.engine.poker.player_hole:
        p_hole = " ".join([str(c) for c in app.engine.poker.player_hole])
        if app.engine.poker.game_state == "preflop":
            board = "[?] [?] [?] [?] [?]"
            d_hole = "[?] [?]"
            state_str = "Pre-Flop (Type 'check', 'raise', 'allin', or 'fold')"
        elif app.engine.poker.game_state == "flop":
            board = " ".join([str(c) for c in app.engine.poker.community_cards[:3]]) + " [?] [?]"
            d_hole = "[?] [?]"
            state_str = "The Flop (Type 'check', 'raise', 'allin', or 'fold')"
        elif app.engine.poker.game_state == "turn":
            board = " ".join([str(c) for c in app.engine.poker.community_cards[:4]]) + " [?]"
            d_hole = "[?] [?]"
            state_str = "The Turn (Type 'check' for Showdown, 'raise', 'allin', or 'fold')"
        else:
            board = " ".join([str(c) for c in app.engine.poker.community_cards])
            d_hole = " ".join([str(c) for c in app.engine.poker.dealer_hole])
            state_str = "Showdown Completed"

        sys.stdout.write(f"  {BOLD}Active Table [{state_str}]:{RESET}\n")
        sys.stdout.write(f"   🎴 Your Hole Cards:  {p_hole}\n")
        sys.stdout.write(f"   ♦️ Community Board: {board}\n")
        sys.stdout.write(f"   🏠 House Hole:       {d_hole}\n")
        sys.stdout.write(f"   Current Bet: {BOLD}{YELLOW}{format_tokens(app.engine.poker.current_bet)}{RESET} tokens\n\n")

def render_gacha_tab(app):
    avail = app.engine.available_tokens
    sys.stdout.write(f"\n  {BOLD}{HEADER}🔮 Pokémon Gacha Capsule Machine{RESET}\n\n")
    sys.stdout.write(f"  Available Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n\n")

    sys.stdout.write(f"  {BOLD}🎰 Pull Options:{RESET}\n")
    sys.stdout.write(f"   • Single Capsule Pull (1x):  {BOLD}{YELLOW}5.0M Tokens{RESET}  (Type '{BOLD}pull 1{RESET}')\n")
    sys.stdout.write(f"   • Multi Capsule Pull (10x):  {BOLD}{YELLOW}45.0M Tokens{RESET} (Type '{BOLD}pull 10{RESET}' - 1 Free!)\n")
    sys.stdout.write(f"   • Custom Quantity Pull:      {BOLD}{YELLOW}Auto-Calculated{RESET} (Type '{BOLD}pull <qty>{RESET}' e.g. 'pull 45')\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}leave{RESET}' to return to the Game Corner Menu.\n\n")

    sys.stdout.write(f"  {BOLD}🎁 Drop Rates & Rewards:{RESET}\n")
    sys.stdout.write(f"   • 🌟 Legendary (2%):  Guaranteed Shiny Companion / +50M Tokens\n")
    sys.stdout.write(f"   • ✨ Epic (8%):       Shiny Charm ✨, Rare Egg 🥚 Tier\n")
    sys.stdout.write(f"   • 🔮 Rare (15%):      Standard/Uncommon Eggs 🥚, Mega Stone 🔮\n")
    sys.stdout.write(f"   • 🍬 Uncommon (30%):  Rare Candy 🍬, Golden Razz Berry 🍇, +3M Tokens\n")
    sys.stdout.write(f"   • 🫐 Common (45%):    Oran Berry 🫐, Mint 🌿, +1M Tokens\n\n")
