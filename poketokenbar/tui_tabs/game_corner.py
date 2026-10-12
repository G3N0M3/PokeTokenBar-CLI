import random
import sys
import textwrap
from poketokenbar.utils.formatting import format_tokens
from poketokenbar.game.models import VELVET_PATRONS, VELVET_MARKS, POKER_VIP_MIN_BET

HEADER = "\033[95m\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"
DARK_GRAY = "\033[90m"
WHITE = "\033[37m"


def _read_input_safe() -> str:
    try:
        if hasattr(sys.stdin, "readline"):
            return sys.stdin.readline().strip()
    except (EOFError, KeyboardInterrupt):
        return ""
    return ""


def render_poker_vip_dialogue(app):
    """Interactive modal displayed when placing a >= 100T bet for the first time."""
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.write(f"\n{BOLD}{YELLOW}{'='*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}{YELLOW}🎰 CELADON GAME CORNER — HIGH-ROLLER INTERLUDE 🎰{RESET}\n")
    sys.stdout.write(f"{BOLD}{YELLOW}{'='*72}{RESET}\n\n")

    dialogue_blocks = [
        ("dealer", "Dealer: \"H-Hold on a moment, Trainer...! Did you just wager ONE HUNDRED TRILLION tokens on this felt?!\""),
        ("narration", "(The Dealer's hands tremble slightly as she adjusts her vest. Pit bosses and surrounding patrons freeze in stunned silence.)"),
        ("dealer", "Dealer: \"Gulp... An astronomical wager like this far exceeds our standard table limits! As our most distinguished patron, I can introduce you to our private high-roller room: The Velvet Salon."),
        ("quote_body", "It features private service, enhanced payout multipliers, and high-society opponents."),
        ("quote_body", "Would you like to move your wager to The Velvet Salon now, or would you prefer to finish playing this hand right here?\""),
    ]

    for block_type, text in dialogue_blocks:
        if block_type == "dealer":
            lines = textwrap.wrap(text, width=68, initial_indent="  ", subsequent_indent="           ")
        elif block_type == "narration":
            lines = textwrap.wrap(text, width=68, initial_indent="  ", subsequent_indent="   ")
        else:
            lines = textwrap.wrap(text, width=68, initial_indent="           ", subsequent_indent="           ")

        for wline in lines:
            sys.stdout.write(f"{CYAN}{wline}{RESET}\n")
        sys.stdout.write("\n")

    sys.stdout.write(f"\n{BOLD}{YELLOW}{'-'*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}{WHITE}[1] Accept & Move to The Velvet Salon{RESET}\n")
    sys.stdout.write(f"  {BOLD}{WHITE}[2] Decline & Finish Playing Here{RESET}\n")
    sys.stdout.write(f"{BOLD}{YELLOW}{'-'*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}{YELLOW}Select option (1 or 2): {RESET}")
    sys.stdout.flush()

    choice = _read_input_safe()
    if choice == "1":
        app.engine.state["poker_vip_unlocked"] = True
        app.engine.poker.table_mode = "vip"
        app.engine.poker.active_opponent = random.choice(VELVET_PATRONS)
        app.engine.save()
        app.message = "Dealer: 'Right this way, Tycoon! Welcome to The Velvet Salon.'"
    else:
        app.engine.state["poker_vip_unlocked"] = True
        app.engine.poker.table_mode = "standard"
        app.engine.poker.active_opponent = "The House"
        app.engine.save()
        app.message = "Dealer: 'Action stays on the main floor! Use 'table vip' anytime to visit the Salon.'"


def render_velvet_recruitment_dialogue(app):
    """Interactive modal displayed when player wins 10 hands and 500T tokens at The Velvet Salon."""
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.write(f"\n{BOLD}{YELLOW}{'='*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}{YELLOW}👑 THE VELVET SALON — RECRUITMENT INVITATION 👑{RESET}\n")
    sys.stdout.write(f"{BOLD}{YELLOW}{'='*72}{RESET}\n\n")

    dialogue_blocks = [
        ("vivienne", "Madame Vivienne: \"Remarkable card play, Trainer... Truly remarkable! Gentleman Walter and Duchess Eleanor have been thoroughly outmatched by your nerve at this felt.\""),
        ("narration", "(Madame Vivienne raises a crystal flute. The salon doors click shut, and Gentleman Walter slides a gold-embossed dossier across the table.)"),
        ("vivienne", "Madame Vivienne: \"To the casino pit bosses, we appear as merely wealthy dilettantes enjoying private high-stakes games. But in truth, we are an undercover syndicate."),
        ("quote_body", "Our target is Baron Salvatore Croix—a ruthless oligarch laundering stolen quadrillions through these very tables while strip-mining nature reserves across the continent."),
        ("quote_body", "We need a card shark of your exceptional caliber to lead our undercover operation: 'The Velvet Sting'."),
        ("quote_body", "We will coordinate wiretaps and legal strikes from the shadows, seating you directly across from Croix's financiers, investors, and enforcers to strip their capital."),
        ("quote_body", "Use the 'sting' command from now on to access your tactical dossiers and advance our campaign against Croix!\""),
    ]

    for block_type, text in dialogue_blocks:
        if block_type == "vivienne":
            lines = textwrap.wrap(text, width=68, initial_indent="  ", subsequent_indent="                    ")
        elif block_type == "narration":
            lines = textwrap.wrap(text, width=68, initial_indent="  ", subsequent_indent="   ")
        else:
            lines = textwrap.wrap(text, width=68, initial_indent="                    ", subsequent_indent="                    ")

        for wline in lines:
            sys.stdout.write(f"{CYAN}{wline}{RESET}\n")
        sys.stdout.write("\n")

    sys.stdout.write(f"\n{BOLD}{YELLOW}{'-'*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}{WHITE}[Press ENTER to accept the syndicate mission & unlock 'sting']{RESET}\n")
    sys.stdout.write(f"{BOLD}{YELLOW}{'-'*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}{YELLOW}Press ENTER to continue: {RESET}")
    sys.stdout.flush()

    _read_input_safe()
    app.message = "🚨 RECRUITED! You've joined The Velvet Sting syndicate! Type 'sting' to proceed!"


def render_velvet_sting_briefing(app):
    """Renders the full-screen mission briefing modal for The Velvet Sting."""
    briefing = app.engine.get_velvet_sting_briefing()
    if not briefing:
        return

    sting = app.engine.state.get("velvet_sting", {})
    curr_ch = sting.get("chapter", "1")

    sys.stdout.write("\033[H\033[2J")
    sys.stdout.write(f"\n{BOLD}{MAGENTA}{'='*72}{RESET}\n")
    if curr_ch == "epilogue":
        title_line = "⚜️ THE VELVET STING // CAMPAIGN FINALE & DEBRIEFING"
        banner_title = "[THE VELVET STING EPILOGUE]"
    else:
        title_line = f"⚜️ THE VELVET STING // OPERATION #{curr_ch} DOSSIER"
        banner_title = "[HIGH-ROLLER HEIST BRIEFING]"

    sys.stdout.write(f"  {BOLD}{YELLOW}{title_line:<68}{RESET}\n")
    sys.stdout.write(f"{BOLD}{MAGENTA}{'='*72}{RESET}\n\n")

    sys.stdout.write(f"  {BOLD}{YELLOW}👑 THE VELVET SYNDICATE{RESET}   {BOLD}{CYAN}{banner_title}{RESET}\n")
    sys.stdout.write(f"  Phase:  {briefing['title'][:58]}\n")
    sys.stdout.write(f"  Sector: {briefing['location'][:58]}\n")
    sys.stdout.write(f"  Sender: {briefing['speaker'][:58]}\n")
    if "opponent" in briefing:
        sys.stdout.write(f"  Target: {BOLD}{RED}{briefing['opponent'][:58]}{RESET}\n")
    sys.stdout.write("\n")

    for line in briefing["dialogue"]:
        if not line:
            sys.stdout.write("\n")
        else:
            for wline in textwrap.wrap(line, width=68):
                sys.stdout.write(f"  {WHITE}{wline}{RESET}\n")

    sys.stdout.write(f"\n  {BOLD}{YELLOW}📋 TACTICAL DIRECTIVES:{RESET}\n")
    for order in briefing["tactical_orders"]:
        for wline in textwrap.wrap(order, width=68):
            sys.stdout.write(f"  {CYAN}{wline}{RESET}\n")

    ready, status_msg = app.engine.check_velvet_sting_objective()
    sys.stdout.write(f"\n  {BOLD}Status:{RESET} ")
    if curr_ch == "epilogue" or sting.get("cleared", False):
        sys.stdout.write(f"{BOLD}{GREEN}🎉 CAMPAIGN COMPLETED! ({status_msg}){RESET}\n")
        prompt_txt = "➔ Press [Enter] to return to the tables: "
    elif ready:
        sys.stdout.write(f"{BOLD}{GREEN}✓ READY TO ADVANCE! ({status_msg}){RESET}\n")
        prompt_txt = "➔ Type 'advance' to proceed to next Chapter, or [Enter] to return: "
    else:
        sys.stdout.write(f"{BOLD}{YELLOW}IN PROGRESS ({status_msg}){RESET}\n")
        prompt_txt = "➔ Press [Enter] to return to the tables: "

    sys.stdout.write(f"\n{BOLD}{MAGENTA}{'-'*72}{RESET}\n")
    sys.stdout.write(f"  {BOLD}{YELLOW}{prompt_txt}{RESET}")
    sys.stdout.flush()

    choice = _read_input_safe().lower().strip()
    if ready and choice in ["advance", "next", "claim", "1"]:
        ok, adv_msg = app.engine.advance_velvet_sting()
        app.message = adv_msg

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
    mode = getattr(app.engine.poker, "table_mode", "standard")
    vip_unlocked = app.engine.state.get("poker_vip_unlocked", False)
    opp = getattr(app.engine.poker, "active_opponent", "The House")

    if mode in ["vip", "boss"]:
        if getattr(app.engine.poker, "boss_name", ""):
            sys.stdout.write(f"\n  {BOLD}{RED}⚔️ THE VELVET SALON — HEADS-UP BOSS SHOWDOWN ⚔️{RESET}\n")
            sys.stdout.write(f"  Target: {BOLD}{YELLOW}{opp}{RESET}\n")
            b_stack = getattr(app.engine.poker, "boss_stack", 0)
            b_max = getattr(app.engine.poker, "boss_max_stack", 1) or 1
            pct = max(0.0, min(1.0, b_stack / b_max))
            filled = int(pct * 16)
            bar = "█" * filled + "░" * (16 - filled)
            sys.stdout.write(f"  🏦 Treasury: [{bar}] {format_tokens(b_stack)} / {format_tokens(b_max)}\n")
        else:
            app.engine.check_and_reset_vip_bankrolls()
            avail_opps = app.engine.get_available_vip_opponents()
            clean_opp = opp.split("[")[0].strip() if opp else ""
            c_stack, _ = app.engine.get_vip_bankroll(clean_opp)

            if not avail_opps:
                sys.stdout.write(f"\n  {BOLD}{YELLOW}👑 THE VELVET SALON — HIGH-ROLLER SUITE 👑{RESET}\n")
                sys.stdout.write(f"  Active Patron: {BOLD}{RED}[TABLE CLOSED — SALON CLEAN SWEEP]{RESET}\n")
                sys.stdout.write(f"  {YELLOW}🏆 All VIP patrons busted! Bonus claimed (+10,000.0Q). Resets at 00:00.{RESET}\n")
            else:
                sys.stdout.write(f"\n  {BOLD}{YELLOW}👑 THE VELVET SALON — HIGH-ROLLER SUITE 👑{RESET}\n")
                sys.stdout.write(f"  Active Patron: {BOLD}{CYAN}{opp}{RESET}\n")
                if c_stack < POKER_VIP_MIN_BET:
                    sys.stdout.write(f"  Chips: {BOLD}{RED}0 tokens [BUSTED] (Resets at 00:00){RESET}\n")
                else:
                    sys.stdout.write(f"  Chips: {BOLD}{YELLOW}{format_tokens(c_stack)}{RESET} tokens\n")
        sys.stdout.write(f"  Available Tokens to Bet: {BOLD}{CYAN}{format_tokens(avail)}{RESET} (Min: 10.0T)\n\n")
        sys.stdout.write(f"  {BOLD}🃏 Rules & Multipliers (VIP Payouts):{RESET}\n")
        sys.stdout.write(f"   • Royal Flush [100x] | Str. Flush [25x] | 4-of-a-Kind [12x]\n")
        sys.stdout.write(f"   • Full House [6x] | Flush [5x] | Straight [4x] | Pair/High [2x]\n\n")
    else:
        sys.stdout.write(f"\n  {BOLD}{HEADER}♠️ Casino Texas Hold'em (You vs. The House!){RESET}\n\n")
        sys.stdout.write(f"  Available Tokens to Bet: {BOLD}{CYAN}{format_tokens(avail)}{RESET}\n\n")
        sys.stdout.write(f"  {BOLD}🃏 Rules & Payout Multipliers:{RESET}\n")
        sys.stdout.write(f"   • Receive 2 cards in hand. Beat the Dealer's best 5-card hand!\n")
        sys.stdout.write(f"   • Royal Flush [50x] | Str. Flush [15x] | 4-of-a-Kind [8x]\n")
        sys.stdout.write(f"   • Full House [5x] | Flush [4x] | Straight [3x] | Pair/High [2x]\n\n")

    pending = getattr(app.engine.poker, "opponent_pending_call", 0)
    sys.stdout.write(f"  ➔ Step 1: Type '{BOLD}bet <amount>{RESET}' to deal your hand (e.g. 'bet 1m').\n")
    if pending > 0:
        sys.stdout.write(f"  ➔ Bet Faced: '{BOLD}call{RESET}' ({format_tokens(pending)}) | '{BOLD}raise{RESET}' | '{BOLD}allin{RESET}' | '{BOLD}fold{RESET}'.\n")
    else:
        sys.stdout.write(f"  ➔ Step 2: Type '{BOLD}check{RESET}' to advance street, or '{BOLD}fold{RESET}' to surrender.\n")
        sys.stdout.write(f"  ➔ Step 3: Type '{BOLD}raise{RESET}' to double bet, or '{BOLD}allin{RESET}' to bet all.\n")
    if mode in ["vip", "boss"]:
        sting = app.engine.state.get("velvet_sting", {})
        if sting.get("recruited", False):
            sys.stdout.write(f"  ➔ Tables: '{BOLD}table std{RESET}' (floor) | '{BOLD}next{RESET}' (seat) | '{BOLD}sting{RESET}' (dossier).\n")
        else:
            sys.stdout.write(f"  ➔ Tables: '{BOLD}table std{RESET}' (floor) | '{BOLD}next{RESET}' (seat).\n")
    elif vip_unlocked:
        sys.stdout.write(f"  ➔ Navigation: Type '{BOLD}table vip{RESET}' to visit The Velvet Salon.\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}back{RESET}' to return to the Game Corner Menu.\n\n")

    if app.engine.poker.player_hole:
        p_hand_str = " ".join([str(c) for c in app.engine.poker.player_hole])
        p_type = app.engine.poker.get_hand_type(app.engine.poker.player_hole)
        p_badge = f"  ({CYAN}{p_type}{RESET})" if p_type else ""

        action_suffix = f" (call {format_tokens(pending)}/raise/allin/fold)" if pending > 0 else " (check/raise/allin/fold)"

        opp_label = opp.split("[")[0].strip() if mode in ["vip", "boss"] else "House"

        if app.engine.poker.game_state == "preflop":
            board = "[?] [?] [?] [?] [?]"
            d_hand_str = "[?] [?]"
            d_badge = ""
            state_str = f"Pre-Flop{action_suffix}"
        elif app.engine.poker.game_state == "flop":
            rev = [str(c) for c in app.engine.poker.community_cards[:3]]
            board = " ".join(rev) + " [?] [?]"
            d_hand_str = "[?] [?]"
            d_badge = ""
            state_str = f"The Flop{action_suffix}"
        elif app.engine.poker.game_state == "turn":
            rev = [str(c) for c in app.engine.poker.community_cards[:4]]
            board = " ".join(rev) + " [?]"
            d_hand_str = "[?] [?]"
            d_badge = ""
            state_str = f"The Turn{action_suffix}"
        else:
            board = " ".join([str(c) for c in app.engine.poker.community_cards])
            d_hand_str = " ".join([str(c) for c in app.engine.poker.dealer_hole])
            d_type = app.engine.poker.get_hand_type(app.engine.poker.dealer_hole)
            d_badge = f"  ({YELLOW}{d_type}{RESET})" if d_type else ""
            if getattr(app.engine.poker, "opponent_folded", False):
                state_str = f"{opp_label} Folded"
            elif getattr(app.engine.poker, "last_outcome", "") == "FOLD":
                state_str = "Hand Folded"
            else:
                state_str = "Showdown Completed"

        sys.stdout.write(f"  {BOLD}Active Table [{state_str}]:{RESET}\n")
        if getattr(app.engine.poker, "opponent_banner_quote", "") and mode in ["vip", "boss"]:
            quote = app.engine.poker.opponent_banner_quote
            sys.stdout.write(f"   💬 {BOLD}{YELLOW}{opp_label}:{RESET}\n")
            for qline in textwrap.wrap(quote, width=64):
                sys.stdout.write(f"      {CYAN}{qline}{RESET}\n")
        sys.stdout.write(f"   🎴 Your Hand:  {p_hand_str}{p_badge}\n")
        sys.stdout.write(f"   ♦️ Board:      {board}\n")
        sys.stdout.write(f"   🏠 {opp_label} Hand: {d_hand_str}{d_badge}\n")
        sys.stdout.write(f"   Current Bet: {BOLD}{YELLOW}{format_tokens(app.engine.poker.current_bet)}{RESET} tokens\n")

        if app.engine.poker.game_state == "idle" and getattr(app.engine.poker, "last_outcome", ""):
            outcome = app.engine.poker.last_outcome
            if getattr(app.engine.poker, "opponent_folded", False):
                sys.stdout.write(f"   {BOLD}{GREEN}🏆 Result: {opp_label.upper()} FOLDED! You win the pot!{RESET}\n")
            elif outcome == "WIN":
                sys.stdout.write(f"   {BOLD}{GREEN}🏆 Result: YOU BEAT {opp_label.upper()}! ({app.engine.poker.last_p_rank} vs {app.engine.poker.last_d_rank}){RESET}\n")
            elif outcome == "PUSH":
                sys.stdout.write(f"   {BOLD}{YELLOW}🤝 Result: TIE / PUSH! ({app.engine.poker.last_p_rank}){RESET}\n")
            elif outcome == "FOLD":
                sys.stdout.write(f"   {BOLD}{RED}🏳️ Result: FOLDED! Surrendered bet.{RESET}\n")
            else:
                sys.stdout.write(f"   {BOLD}{RED}💀 Result: {opp_label.upper()} WINS! ({app.engine.poker.last_d_rank} beats {app.engine.poker.last_p_rank}){RESET}\n")
        sys.stdout.write("\n")

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
                    winners = getattr(db, "winners", [])
                    is_winner = (r in winners) if winners else ((db.winner and db.winner.lane == r.lane) or (pos == max(positions.values())))
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

    # Live Standings (handles shared ranks on ties / dead heat)
    sorted_r = sorted(racers, key=lambda r: (positions.get(r.lane, 0), -r.lane), reverse=True)
    medals = ["1st", "2nd", "3rd", "4th"]
    st_parts = []
    prev_pos = None
    curr_rank = 1
    for idx_m, r in enumerate(sorted_r):
        p = positions.get(r.lane, 0)
        if idx_m > 0 and p < prev_pos:
            curr_rank = idx_m + 1
        prev_pos = p
        rank_str = medals[curr_rank - 1] if curr_rank <= 4 else f"{curr_rank}th"
        star = "*" if r.lane == bet_lane else ""
        st_parts.append(f"{rank_str}: {r.icon}{star} {p}m")
    sys.stdout.write(f"  {BOLD}Standings:{RESET} " + " | ".join(st_parts) + "\n")

    # Live Commentary
    if events:
        sys.stdout.write(f"  {BOLD}Live Commentary:{RESET}\n")
        for ev in events[:2]:
            sys.stdout.write(f"   📢 {ev}\n")
    else:
        sys.stdout.write(f"  {BOLD}Live Commentary:{RESET}\n   📢 💨 Racers thunder down the stadium hurdle track!\n")


