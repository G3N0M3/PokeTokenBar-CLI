import random
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
DARK_GRAY = "\033[90m"
WHITE = "\033[37m"

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
    elif state == 'voltorb':
        render_voltorb_tab(app)
    elif state == 'excavator':
        render_excavator_tab(app)
    elif state == 'trivia':
        render_trivia_tab(app)
    elif state == 'derby':
        render_derby_tab(app)
    elif state == 'grunt_bribe':
        render_grunt_bribe_tab(app)
    else:
        render_game_corner_menu(app)

def render_game_corner_menu(app):
    sys.stdout.write(f"\n  {BOLD}{HEADER}🎰 Welcome to the Token Game Corner!{RESET}\n\n")
    sys.stdout.write(f"  {BOLD}Available Games:{RESET}\n")
    sys.stdout.write(f"   {CYAN}1. Hold'em Poker{RESET}    - High stakes Texas Hold'em vs Dealer.\n")
    sys.stdout.write(f"   {CYAN}2. Gacha Capsules{RESET}   - Pull for rare items & companions!\n")
    sys.stdout.write(f"   {CYAN}3. Token Slots{RESET}      - Fast-paced 3-reel slot machine.\n")
    sys.stdout.write(f"   {CYAN}4. Blackjack{RESET}        - Classic 21 casino showdown.\n")
    sys.stdout.write(f"   {CYAN}5. Voltorb Flip{RESET}     - Deduction card puzzle with multipliers!\n")
    sys.stdout.write(f"   {CYAN}6. Underground Dig{RESET}  - Sledgehammer excavation for rare fossils.\n")
    sys.stdout.write(f"   {CYAN}7. Silhouette Quiz{RESET}  - Who's That Pokémon trivia challenge!\n")
    sys.stdout.write(f"   {CYAN}8. Stadium Derby{RESET}    - 4-lane hurdle track race betting.\n\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}play <1-8>{RESET}' to start (e.g. 'play 1' to 'play 8').\n\n")
    
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
    
    has_pass = app.engine.state.get("permanent_black_market", False)
    if has_pass:
        sys.stdout.write(f"  📯 {YELLOW}Note: The Team Rocket poster conceals your secret switch ('poster').{RESET}\n")
    elif random.random() < 0.10:
        sys.stdout.write(f"  👀 {YELLOW}Note: A Team Rocket poster hangs crookedly on the wall...{RESET}\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}spin <amount>{RESET}' to play (e.g. 'spin 500k', 'spin 1m').\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}back{RESET}' to return to the Game Corner Menu.\n\n")

def render_grunt_bribe_tab(app):
    avail = app.engine.available_tokens
    has_pass = app.engine.state.get("permanent_black_market", False)
    bribe_amt = 0 if has_pass else app.engine.get_daily_grunt_bribe()

    sys.stdout.write(f"\n  {BOLD}{RED}🏢 Team Rocket Secret Switch{RESET}\n\n")
    sys.stdout.write(f"  You slide the crooked poster aside to inspect the wall...\n")
    sys.stdout.write(f"  {BOLD}Click!{RESET} A hidden switch is exposed!\n\n")
    sys.stdout.write(f"  Suddenly, a shady {BOLD}{RED}Team Rocket Grunt{RESET} steps out from the shadows!\n\n")
    if has_pass:
        sys.stdout.write(f"  {YELLOW}\"Hold it right th— Wait! That's a Syndicate Black Pass!\"{RESET}\n")
        sys.stdout.write(f"  {YELLOW}The Grunt snaps to attention and salutes respectfully.{RESET}\n")
        sys.stdout.write(f"  {YELLOW}\"Pardon the intrusion, Commander! Right this way!\"{RESET}\n\n")
        sys.stdout.write(f"  Available Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n")
        sys.stdout.write(f"  Access Clearance: {BOLD}{GREEN}Syndicate Black Pass VIP (Toll: WAIVED){RESET}\n\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}enter{RESET}' to proceed into the Black Market.\n")
    else:
        sys.stdout.write(f"  {YELLOW}\"Hey kid! What are you doing snooping back here? Looking for the{RESET}\n")
        sys.stdout.write(f"  {YELLOW}underground Black Market? It'll cost you {BOLD}{CYAN}{format_tokens(bribe_amt)}{RESET}{YELLOW} tokens for me{RESET}\n")
        sys.stdout.write(f"  {YELLOW}to look the other way!\"{RESET}\n\n")
        sys.stdout.write(f"  Available Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n")
        sys.stdout.write(f"  Bribe Demanded:   {BOLD}{YELLOW}{format_tokens(bribe_amt)} tokens{RESET}\n\n")
        sys.stdout.write(f"  ➔ Type '{BOLD}bribe{RESET}' to pay the Grunt and enter the Black Market.\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}back{RESET}' to return to the Slot Machine.\n\n")
    
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
    sys.stdout.write(f"  ➔ Type '{BOLD}back{RESET}' to return to the Game Corner Menu.\n\n")
    
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
    sys.stdout.write(f"  ➔ Type '{BOLD}back{RESET}' to return to the Game Corner Menu.\n\n")

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

    sys.stdout.write(f"  ➔ Type '{BOLD}pull <qty>{RESET}' to pull (5.0M tokens each, 1 free every 10 pulls!).\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}back{RESET}' to return to the Game Corner Menu.\n\n")

    sys.stdout.write(f"  {BOLD}🎁 Drop Rates & Rewards:{RESET}\n")
    sys.stdout.write(f"   • 🌟 Legendary (2%):  Guaranteed Shiny Companion / +50M Tokens\n")
    sys.stdout.write(f"   • ✨ Epic (8%):       Shiny Charm ✨, Rare Egg 🥚 Tier\n")
    sys.stdout.write(f"   • 🔮 Rare (15%):      Standard/Uncommon Eggs 🥚, Mega Stone 🔮\n")
    sys.stdout.write(f"   • 🍬 Uncommon (30%):  Rare Candy 🍬, Golden Razz Berry 🍇, +3M Tokens\n")
    sys.stdout.write(f"   • 🫐 Common (45%):    Oran Berry 🫐, +1.0M Tokens\n\n")

def render_voltorb_tab(app):
    v = app.engine.voltorb
    avail = app.engine.available_tokens
    sys.stdout.write(f"\n  {BOLD}{HEADER}⚡ Voltorb Flip [Level {v.current_level}/8]{RESET}\n\n")
    sys.stdout.write(f"  Available Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n")
    if v.game_state == "playing":
        sys.stdout.write(f"  Bet: {BOLD}{YELLOW}{format_tokens(v.current_bet)}{RESET} | Multiplier: {BOLD}{GREEN}{v.current_multiplier}x{RESET} | Bank: {BOLD}{CYAN}{format_tokens(v.current_bet * v.current_multiplier)}{RESET}\n\n")
    else:
        sys.stdout.write(f"  Status: {BOLD}{YELLOW}{v.game_state.replace('_', ' ').title()}{RESET}\n\n")

    sys.stdout.write(f"  {BOLD}Commands:{RESET}\n")
    sys.stdout.write(f"   • '{BOLD}bet <amt> [lvl 1-8]{RESET}' - Start game (e.g. 'bet 500k', 'bet 1m 5')\n")
    sys.stdout.write(f"   • '{BOLD}flip <r> <c>{RESET}'       - Uncover card (e.g. 'flip 1 3')\n")
    sys.stdout.write(f"   • '{BOLD}memo <r> <c> <note>{RESET}' - Mark notes (e.g. 'memo 2 4 v')\n")
    sys.stdout.write(f"   • '{BOLD}cashout{RESET}'             - Bank payout | '{BOLD}back{RESET}' to exit\n")
    sys.stdout.write(f"  💡 {YELLOW}Clear all 2s & 3s to advance, or pick level via 'bet <amt> <1-8>'.{RESET}\n\n")

    if v.board:
        sys.stdout.write("        1     2     3     4     5\n")
        sys.stdout.write("     ┌─────┬─────┬─────┬─────┬─────┐\n")
        for r in range(5):
            row_str = f"   {r+1} │"
            for c in range(5):
                card = v.board[r][c]
                if card.revealed:
                    if card.value == 0:
                        cell = f" [{RED}{BOLD}0{RESET}] "
                    else:
                        color = GREEN if card.value > 1 else CYAN
                        cell = f" [{color}{card.value}{RESET}] "
                elif card.memo:
                    cell = f" {YELLOW}{card.memo[:3]:^3}{RESET} "
                else:
                    cell = " [?] "
                row_str += cell + "│"
            pts = v.row_points[r]
            volts = v.row_voltorbs[r]
            row_str += f"  Pts: {pts:>2} | ⚡: {volts}\n"
            sys.stdout.write(row_str)
            if r < 4:
                sys.stdout.write("     ├─────┼─────┼─────┼─────┼─────┤\n")
        sys.stdout.write("     └─────┴─────┴─────┴─────┴─────┘\n")
        pts_line = "  Pts " + " ".join(f"{p:^5}" for p in v.col_points) + "\n"
        volts_line = f"   {RED}⚡{RESET} " + " ".join(f"{vo:^5}" for vo in v.col_voltorbs) + "\n\n"
        sys.stdout.write(pts_line)
        sys.stdout.write(volts_line)

    if v.last_result:
        sys.stdout.write(f"  {BOLD}Last Outcome:{RESET}\n  {v.last_result}\n\n")

def _format_excavator_tile(sym: str, col_code: str) -> str:
    import unicodedata
    is_wide = (unicodedata.east_asian_width(sym[0]) in ('W', 'F') or len(sym) > 1 or ord(sym[0]) > 0x2000) and sym not in ('▓', '▒', '░', '■', ' ')
    if is_wide:
        return f"{col_code}{sym}{RESET} "
    else:
        return f" {col_code}{sym}{RESET} "

def render_excavator_tab(app):
    ex = app.engine.excavator
    avail = app.engine.available_tokens
    sys.stdout.write(f"\n  {BOLD}{HEADER}⛏️ Underground Fossil Excavator{RESET}\n\n")
    sys.stdout.write(f"  Available Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n")

    bar_len = 16
    filled = int(bar_len * max(0, ex.integrity) / ex.MAX_INTEGRITY)
    color = GREEN if ex.integrity > 12 else (YELLOW if ex.integrity > 5 else RED)
    bar = f"{color}{'█' * filled}{RESET}{'░' * (bar_len - filled)}"
    sys.stdout.write(f"  Wall Integrity: [{bar}] {ex.integrity}/{ex.MAX_INTEGRITY}\n\n")

    sys.stdout.write(f"  {BOLD}Excavation Controls:{RESET}\n")
    sys.stdout.write(f"   • '{BOLD}pick <r 1-6> <c 1-9>{RESET}'  - 1 tile: 1 hit, costs 1 integrity\n")
    sys.stdout.write(f"   • '{BOLD}hammer <r 1-6> <c 1-9>{RESET}' - Blast area: 3 hits, costs 3 integrity\n")
    sys.stdout.write(f"   • '{BOLD}dig{RESET}'                  - Start new wall (costs 500K tokens)\n")
    sys.stdout.write(f"   • '{BOLD}back{RESET}'                 - Return to Game Corner menu\n\n")

    if ex.strata:
        sys.stdout.write("      1  2  3  4  5  6  7  8  9\n")
        sys.stdout.write("    ┌───────────────────────────┐\n")
        for r in range(ex.ROWS):
            row_str = f"  {r+1} │"
            for c in range(ex.COLS):
                sym, col_code = ex.get_tile_display(r, c)
                row_str += _format_excavator_tile(sym, col_code)
            row_str += "│\n"
            sys.stdout.write(row_str)
        sys.stdout.write("    └───────────────────────────┘\n")
        sys.stdout.write(f"    Strata: {DARK_GRAY}▓{RESET} Rock | {YELLOW}▒{RESET} Dirt | {WHITE}░{RESET} Soil | {RED}■{RESET} Iron Barrier\n\n")

    if ex.treasures:
        uncovered = [t for t in ex.treasures if t.uncovered and t.kind != "barrier"]
        if uncovered:
            items_str = ", ".join(f"{t.symbol} {t.name}" for t in uncovered)
            sys.stdout.write(f"  {BOLD}{GREEN}Uncovered Relics:{RESET} {items_str}\n\n")

    if ex.last_action_msg:
        sys.stdout.write(f"  {BOLD}Last Action:{RESET} {ex.last_action_msg}\n\n")

def render_trivia_tab(app):
    tr = app.engine.trivia
    avail = app.engine.available_tokens
    sys.stdout.write(f"\n  {BOLD}{HEADER}❓ \"Who's That Pokémon?!\" Silhouette Quiz{RESET}\n\n")
    sys.stdout.write(f"  Available Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n")

    streak_str = f" | {YELLOW}Streak: {tr.streak} 🔥{RESET}" if tr.streak > 0 else ""
    if tr.game_state == "guessing" and tr.current_target:
        types_str = " / ".join(tr.current_target["types"])
        sys.stdout.write(f"  Wager: {BOLD}{YELLOW}{format_tokens(tr.current_bet)}{RESET} | Multiplier: {BOLD}{GREEN}{tr.current_multiplier:.1f}x{RESET}{streak_str}\n")
        sys.stdout.write(f"  Type: {BOLD}{CYAN}{types_str}{RESET} | Guesses Left: {BOLD}{YELLOW}{tr.guesses_left}/3{RESET}\n\n")
    else:
        sys.stdout.write(f"  Status: {BOLD}{YELLOW}{tr.game_state.replace('_', ' ').title()}{RESET}{streak_str}\n\n")

    sys.stdout.write(f"  {BOLD}Commands:{RESET}\n")
    sys.stdout.write(f"   • '{BOLD}bet <amount>{RESET}' to start round (e.g. 'bet 500k', 'bet 1m')\n")
    sys.stdout.write(f"   • '{BOLD}guess <name>{RESET}' to submit guess (e.g. 'guess pikachu')\n")
    sys.stdout.write(f"   • '{BOLD}hint{RESET}' for next clue (drops mult) | '{BOLD}giveup{RESET}' to surrender\n")
    sys.stdout.write(f"   • '{BOLD}back{RESET}' to return to Game Corner menu\n\n")

    # Render Silhouette or Color Sprite
    if tr.current_target:
        species_id = tr.current_target["id"]
        from poketokenbar.sprite_renderer import SpriteRenderer
        sprite_path = app.engine.api.download_sprite(species_id, is_shiny=False, is_back=False)
        is_sil = (tr.game_state == "guessing")
        if sprite_path and sprite_path.exists():
            art = SpriteRenderer.render_png_to_ansi(sprite_path, max_cols=22, center_width=28, silhouette=is_sil)
            sys.stdout.write(f"{art}\n\n")
        else:
            if is_sil:
                sys.stdout.write(f"       \033[38;2;35;40;55m▄█████████▄\033[0m\n")
                sys.stdout.write(f"      \033[38;2;35;40;55m████  ?  ████\033[0m\n")
                sys.stdout.write(f"       \033[38;2;35;40;55m▀█████████▀\033[0m\n\n")
            else:
                sys.stdout.write(f"      [{BOLD}{GREEN}★ {tr.current_target['name'].upper()} ★{RESET}]\n\n")

    # Render unlocked hints
    if tr.current_target and tr.hints_used > 0:
        sys.stdout.write(f"  {BOLD}Revealed Hints:{RESET}\n")
        target = tr.current_target
        if tr.hints_used >= 1:
            sys.stdout.write(f"   1. Category: {CYAN}{target['cat']}{RESET} (Height: {target['ht']}, Weight: {target['wt']})\n")
        if tr.hints_used >= 2:
            sys.stdout.write(f"   2. Name: Starts with '{CYAN}{target['name'][0]}{RESET}' ({len(target['name'])} letters)\n")
        if tr.hints_used >= 3:
            import re
            dex_redacted = re.sub(re.escape(target["name"]), "______", target["dex"], flags=re.IGNORECASE)
            sys.stdout.write(f"   3. Pokédex: \"{YELLOW}{dex_redacted}{RESET}\"\n")
        sys.stdout.write("\n")

    if tr.last_result:
        sys.stdout.write(f"  {BOLD}Outcome:{RESET} {tr.last_result}\n\n")

def render_derby_tab(app):
    db = app.engine.derby
    avail = app.engine.available_tokens
    sys.stdout.write(f"\n  {BOLD}{HEADER}🏇 Pokémon Stadium Derby{RESET}\n\n")
    sys.stdout.write(f"  Available Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n")
    if db.game_state == "bet_placed":
        chosen = db.racers[db.bet_lane - 1]
        sys.stdout.write(f"  Active Bet: {BOLD}{YELLOW}{format_tokens(db.bet_amount)}{RESET} on Lane {db.bet_lane} [{chosen.icon} {chosen.name}] ({chosen.odds:.1f}x)\n\n")
    else:
        sys.stdout.write(f"  Status: {BOLD}{YELLOW}{db.game_state.replace('_', ' ').title()}{RESET}\n\n")

    sys.stdout.write(f"  {BOLD}Racers & Track Odds:{RESET}\n")
    for r in db.racers:
        tag = f" {GREEN}[YOUR PICK]{RESET}" if db.game_state == "bet_placed" and r.lane == db.bet_lane else ""
        sys.stdout.write(f"   {CYAN}Lane {r.lane}:{RESET} {r.icon} {BOLD}{r.name:<8}{RESET} ({YELLOW}{r.odds:>4.1f}x{RESET}){tag}\n")
        sys.stdout.write(f"     {DARK_GRAY}└─ {r.style}{RESET}\n")
    sys.stdout.write("\n")

    sys.stdout.write(f"  {BOLD}Commands:{RESET}\n")
    sys.stdout.write(f"   • '{BOLD}bet <lane 1-4> <amt>{RESET}' (e.g. 'bet 1 500k', 'bet 4 1m')\n")
    sys.stdout.write(f"   • '{BOLD}race{RESET}' to launch the race!\n")
    sys.stdout.write(f"   • '{BOLD}back{RESET}' to return to Game Corner menu\n\n")

    sys.stdout.write(f"  {BOLD}Track [Hurdles: ║ at 12m, 24m]:{RESET}\n")
    for r in db.racers:
        pos = min(db.TRACK_LENGTH, r.position)
        track_chars = []
        for i in range(db.TRACK_LENGTH + 1):
            if i == pos:
                track_chars.append(f"{YELLOW}●{RESET}")
            elif i in db.HURDLES:
                track_chars.append(f"{RED}║{RESET}")
            else:
                track_chars.append("─")
        track_str = "".join(track_chars)
        flag = "🚩" if pos >= db.TRACK_LENGTH else "🏁"
        sys.stdout.write(f"   {r.lane} [{r.icon} {r.name:<8}] {track_str}{flag} ({pos:>2}m)\n")
    sys.stdout.write("\n")

    if db.race_frames and len(db.race_frames) > 1:
        last_evts = db.race_frames[-1].get("events", [])
        if last_evts:
            sys.stdout.write(f"  {BOLD}Race Commentary:{RESET}\n")
            for ev in last_evts[:3]:
                sys.stdout.write(f"   📢 {ev}\n")
            sys.stdout.write("\n")

    if db.last_result:
        sys.stdout.write(f"  {BOLD}Final Result:{RESET}\n  {db.last_result}\n\n")

def render_derby_race_screen(app, frame, frame_idx: int, total_frames: int, countdown_stage=None):
    """Renders the standalone vertical track stadium screen during race animation."""
    db = app.engine.derby
    positions = frame.get("positions", {})
    events = frame.get("events", [])
    bet_lane = db.bet_lane
    bet_amount = db.bet_amount
    racers = db.racers

    chosen = next((r for r in racers if r.lane == bet_lane), racers[0])

    sys.stdout.write(f"\n  {BOLD}{HEADER}🏟️  POKÉMON STADIUM DERBY — LIVE HURDLE RACE 🏟️{RESET}\n")
    if countdown_stage:
        stage_icons = {
            "3": f"{RED}🔴 3{RESET}",
            "2": f"{YELLOW}🟡 2{RESET}",
            "1": f"{YELLOW}🟡 1{RESET}",
            "GO!": f"{GREEN}🟢 GO!{RESET}",
        }
        sig = stage_icons.get(countdown_stage, countdown_stage)
        status_str = f"🚦 [ {sig} ]"
    else:
        status_str = f"Turn {frame_idx + 1}/{total_frames}" if total_frames > 0 else "Live Race"
    sys.stdout.write(f"  {status_str} | Bet: {BOLD}{YELLOW}{format_tokens(bet_amount)}{RESET} on Lane {bet_lane} [{chosen.icon} {chosen.name}] ({chosen.odds:.1f}x)\n\n")

    pfx = "           "
    sys.stdout.write(f"{pfx}┌────────────┬────────────┬────────────┬────────────┐\n")

    # Row 1: Lane numbers
    sys.stdout.write(f"{pfx}│" + "".join(f"   {CYAN}Lane {r.lane}{RESET}   │" for r in racers) + "\n")

    # Row 2: Racer names (each formatted to exactly 12 display columns)
    name_cells = [
        " 🐴 Ponyta  ",
        " 🐦 Dodrio  ",
        " ⚡ Jolteon ",
        "🐢 Slowpoke ",
    ]
    sys.stdout.write(f"{pfx}│" + "".join(f"{BOLD}{name_cells[r.lane - 1]}{RESET}│" for r in racers) + "\n")

    # Row 3: Pick indicator or odds (each formatted to exactly 12 display columns)
    odds_cells = []
    for r in racers:
        if r.lane == bet_lane:
            odds_cells.append(f" {GREEN}★YOUR BET★{RESET} ")
        else:
            odds_cells.append(f"  ({r.odds:>4.1f}x)   ")
    sys.stdout.write(f"{pfx}│" + "│".join(odds_cells) + "│\n")

    sys.stdout.write(f"{pfx}├────────────┼────────────┼────────────┼────────────┤\n")

    # Prefixes for each of the 19 vertical track rows (18 down to 0 for 36m track)
    prefixes = {
        18: f"  36m {YELLOW}🏁{RESET} ──│",
        17: "  34m    ──│",
        16: "  32m    ──│",
        15: "  30m    ──│",
        14: "  28m    ──│",
        13: "  26m    ──│",
        12: f"  24m {RED}||{RESET} ──│",
        11: "  22m    ──│",
        10: "  20m    ──│",
         9: "  18m    ──│",
         8: "  16m    ──│",
         7: "  14m    ──│",
         6: f"  12m {RED}||{RESET} ──│",
         5: "  10m    ──│",
         4: "   8m    ──│",
         3: "   6m    ──│",
         2: "   4m    ──│",
         1: "   2m    ──│",
         0: f"   0m {CYAN}🚩{RESET} ──│",
    }

    # Render each vertical row from finish line (36m) down to start line (0m)
    for row in range(18, -1, -1):
        line = prefixes[row]
        for r in racers:
            pos = positions.get(r.lane, 0)
            r_row = min(18, max(0, pos // 2))
            is_pick = (r.lane == bet_lane)
            if row == r_row:
                if pos >= 36:
                    is_winner = (db.winner and db.winner.lane == r.lane) or (pos == max(positions.values()))
                    if is_winner:
                        cell = f" {YELLOW}🏆 WIN (36m){RESET}"
                    else:
                        cell = f" {GREEN}🏁 FIN (36m){RESET}"
                else:
                    star = f"{GREEN}*" if is_pick else " "
                    cell = f"{star}{r.icon} ({pos:>2}m)   {RESET}"
            else:
                if row == 18:
                    cell = f"{YELLOW} ═ ═ ═ ═ ═  {RESET}"
                elif row in (12, 6):
                    cell = f"{RED} ═══[||]═══ {RESET}"
                elif row == 0:
                    cell = f"{CYAN} ══════════ {RESET}"
                else:
                    cell = f"{DARK_GRAY}     ·      {RESET}"
            line += cell + "│"
        sys.stdout.write(line + "\n")

    sys.stdout.write(f"{pfx}└────────────┴────────────┴────────────┴────────────┘\n")

    # Live Standings
    sorted_r = sorted(racers, key=lambda r: (positions.get(r.lane, 0), -r.lane), reverse=True)
    medals = ["1st", "2nd", "3rd", "4th"]
    st_parts = []
    for idx_m, r in enumerate(sorted_r):
        p = positions.get(r.lane, 0)
        star = "*" if r.lane == bet_lane else ""
        st_parts.append(f"{medals[idx_m]}: {r.icon}{star} {p}m")
    sys.stdout.write(f"  {BOLD}Standings:{RESET} " + " | ".join(st_parts) + "\n")

    # Live Commentary
    if events:
        sys.stdout.write(f"  {BOLD}Live Commentary:{RESET}\n")
        for ev in events[:2]:
            sys.stdout.write(f"   📢 {ev}\n")
    else:
        sys.stdout.write(f"  {BOLD}Live Commentary:{RESET}\n   📢 💨 Racers thunder down the stadium hurdle track!\n")


