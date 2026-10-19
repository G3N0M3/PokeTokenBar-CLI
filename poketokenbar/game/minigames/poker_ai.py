import random
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional

from poketokenbar.utils.formatting import format_tokens


@dataclass
class OpponentProfile:
    name: str
    title: str
    aggression: float  # 0.0 to 1.0: Likelihood of betting/raising on playable hands
    bluff_rate: float  # 0.0 to 1.0: Likelihood of bluffing with weak/air hands
    fold_resistance: float  # 0.0 to 1.0: Resistance to folding when facing player raises
    bet_ratio: float  # Fraction of current bet to add when betting (e.g. 0.5 to 1.5)
    quotes: Dict[str, List[str]] = field(default_factory=dict)


OPPONENT_PROFILES: Dict[str, OpponentProfile] = {
    # Pre-Recruitment VIP Patrons (Chapter 1)
    "Duchess Eleanor": OpponentProfile(
        name="Duchess Eleanor",
        title="Dilettante",
        aggression=0.40,
        bluff_rate=0.15,
        fold_resistance=0.45,
        bet_ratio=0.5,
        quotes={
            "check": [
                '"Let us see the next card, darling." (Checks)',
                '"A quiet felt speaks volumes." (Checks)',
            ],
            "bet": [
                '"Let us see if fortune smiles upon your courage." (+{amt})',
                '"A modest wager to test your resolve, darling." (+{amt})',
            ],
            "call": [
                '"Very well, I shall see your wager."',
                '"Charming nerve. I call."',
            ],
            "fold": [
                '"A gracious concession. The cards are yours."',
                '"I know when discretion outvalues pride. Fold."',
            ],
            "raise": [
                '"Splendid raise! But I must test you further!" (+{amt})',
            ],
            "showdown_win": [
                '"A delightful hand, darling. Better luck on the next deal."',
                '"Class and composure always triumph at this felt, darling."',
            ],
            "showdown_loss": [
                '"My goodness! Such extraordinary cards! Well played, darling."',
                '"A splendid victory! You certainly know how to command the room."',
            ],
            "showdown_push": [
                '"A deadlock between peers! How utterly fascinating."',
            ],
            "player_fold": [
                '"A prudent retreat, darling. I shall collect the chips gracefully."',
                '"Discretion is so terribly underrated. Until the next deal."',
            ],
        },
    ),
    "Gentleman Walter": OpponentProfile(
        name="Gentleman Walter",
        title="Dilettante",
        aggression=0.35,
        bluff_rate=0.08,
        fold_resistance=0.55,
        bet_ratio=0.5,
        quotes={
            "check": [
                '"Check to you, kid. Make your move." (Checks)',
                '"Patience is the sharpest blade." (Checks)',
            ],
            "bet": [
                '"A steady hand builds the strongest fortress." (+{amt})',
                '"Can\'t let you see the felt for free, kid." (+{amt})',
            ],
            "call": [
                '"I can match that. Let\'s see the felt."',
                '"Fair enough, kid. Call."',
            ],
            "fold": [
                '"Discretion is the better part of valor. Fold."',
                '"You got me this time, kid. Mucked."',
            ],
            "raise": [
                '"You\'re pushing hard, kid. Let\'s push back!" (+{amt})',
            ],
            "showdown_win": [
                '"Tough break, kid. Experience counts for a lot at this table."',
                '"Read you like an open ledger. Hand goes to the old timer."',
            ],
            "showdown_loss": [
                '"I\'ll be damned! You really out-played me there, kid. Great hand."',
                '"Sharp as a razor! Take the pot, you earned every token."',
            ],
            "showdown_push": [
                '"Standoff! We live to fight another round, kid."',
            ],
            "player_fold": [
                '"Smart move folding when you\'re beat. Live to fight another hand."',
                '"Can\'t fault a clean fold, kid. Pot is mine."',
            ],
        },
    ),
    "Madame Vivienne": OpponentProfile(
        name="Madame Vivienne",
        title="Salon Matron",
        aggression=0.55,
        bluff_rate=0.28,
        fold_resistance=0.60,
        bet_ratio=0.75,
        quotes={
            "check": [
                '"The board is intriguing... check." (Checks)',
                '"Let us watch the story unfold." (Checks)',
            ],
            "bet": [
                '"Are you certain you want to walk down this path?" (+{amt})',
                '"A calculated wager from the shadows." (+{amt})',
            ],
            "call": [
                '"Intriguing. Let us see where this leads."',
                '"I shall call your bluff—or your brilliance."',
            ],
            "fold": [
                '"A clever strike, Trainer. You win this round."',
                '"Folded. I respect a sharp blade."',
            ],
            "raise": [
                '"Did you think you were the only one holding cards?" (+{amt})',
            ],
            "showdown_win": [
                '"The cards favor the prepared mind. A commendable attempt, Trainer."',
                '"You walked into my web, darling. The pot stays with the salon."',
            ],
            "showdown_loss": [
                '"Astonishing... You dismantled my hand completely. Brilliant play."',
                '"I see fire in your eyes, Trainer. You truly belong at this felt."',
            ],
            "showdown_push": [
                '"Evenly matched. The tension in this room is delicious."',
            ],
            "player_fold": [
                '"A wise surrender. Knowing when to fold is the mark of a master."',
                '"You retreat to strike again. I expect nothing less from you."',
            ],
        },
    ),
    # Chapter 2: Financier Vance
    "Financier Vance": OpponentProfile(
        name="Financier Vance",
        title="Money Runner",
        aggression=0.30,
        bluff_rate=0.10,
        fold_resistance=0.20,  # Very fold-prone to player pressure!
        bet_ratio=0.5,
        quotes={
            "check": [
                '"The numbers are murky... check." (Checks)',
                '"Let\'s keep the ledger clean. Check." (Checks)',
            ],
            "bet": [
                '"Croix wants results. Here is my bet!" (+{amt})',
                '"The ledger says I hold the edge. Match this." (+{amt})',
            ],
            "call": [
                '"Fine, fine... I\'ll call it."',
                '"Just verifying the transaction. Call."',
            ],
            "fold": [
                '"No way! I\'m not risking Croix\'s liquidity! I fold!"',
                '"Take the pot! My margin limit has been reached!"',
            ],
            "raise": [
                '"Wait, my balance sheet has room to squeeze!" (+{amt})',
            ],
            "showdown_win": [
                '"Ha! The numbers never lie! My spreadsheet predicted this win!"',
                '"Transaction settled in my favor! Croix will be pleased with this."',
            ],
            "showdown_loss": [
                '"What?! But the probability models... My balance sheet is ruined!"',
                '"No, no, no! That hand was statistically impossible! Unbelievable!"',
            ],
            "showdown_push": [
                '"A break-even trade? I suppose my margin remains intact..."',
            ],
            "player_fold": [
                '"Yes! Run along! Croix\'s liquidity remains undefeated!"',
                '"Smart of you to fold! You couldn\'t afford this balance sheet anyway!"',
            ],
        },
    ),
    # Chapter 3: Viktor Rostov [Enforcer] (Mini-Boss 1)
    "Viktor Rostov": OpponentProfile(
        name="Viktor Rostov",
        title="Enforcer",
        aggression=0.80,
        bluff_rate=0.45,
        fold_resistance=0.85,  # Stubborn brute!
        bet_ratio=1.0,
        quotes={
            "check": [
                '"Hmph! Let\'s see the next one." (Checks)',
                '"Check! Don\'t get comfortable, punk!" (Checks)',
            ],
            "bet": [
                '"You think you\'re tough, kid?! Eat this raise!" (+{amt})',
                '"The Bull stomps on weak bets! Match THIS!" (+{amt})',
                '"I came here to break bankrolls! Ante up!" (+{amt})',
            ],
            "call": [
                '"You think you can scare The Bull?! I CALL!"',
                '"I\'m not budging! Call!"',
            ],
            "fold": [
                '"Grrr... Lucky punk! Next hand I break you!"',
                '"Tch! Take your crumbs! The war chest remains!"',
            ],
            "raise": [
                '"You call THAT a raise?! THIS is a raise!" (+{amt})',
                '"Nobody pushes Viktor Rostov around! RE-RAISE!" (+{amt})',
            ],
            "showdown_win": [
                '"HAHAHA! The Bull crushes another soft punk! Leave your tokens!"',
                '"You thought you could out-muscle Rostov?! Get wrecked, kid!"',
            ],
            "showdown_loss": [
                '"WHAT?! You cracked my monsters?! Don\'t smirk, punk, this ain\'t over!"',
                '"GRRR! You got lucky on that river! The war chest can take it!"',
            ],
            "showdown_push": [
                '"Bah! A tie?! Next hand I put you in the ground!"',
            ],
            "player_fold": [
                '"Tuck your tail and run, coward! The Bull owns this table!"',
                '"That\'s right, fold! Real men stay in the ring, punks muck!"',
            ],
            "bankrupt": [
                '"IMPOSSIBLE! My 50 Trillion war chest... wiped clean by a kid?!"',
                '"GAAAH! Croix is going to have my head! How did you beat The Bull?!"',
            ],
        },
    ),
    # Chapter 4: Countess Beverly
    "Countess Beverly": OpponentProfile(
        name="Countess Beverly",
        title="Bondholder",
        aggression=0.70,
        bluff_rate=0.35,
        fold_resistance=0.70,
        bet_ratio=0.75,
        quotes={
            "check": [
                '"Oh, let\'s see what pretty card comes next!" (Checks)',
                '"Checking! Keep the champagne flowing, darling!" (Checks)',
            ],
            "bet": [
                '"Don\'t be boring! Let\'s make this exciting!" (+{amt})',
                '"What is a few trillion between friends? Raise!" (+{amt})',
            ],
            "call": [
                '"Call! You play with such delicious drama!"',
                '"I simply must see what you are holding! Call!"',
            ],
            "fold": [
                '"Ugh, dreadful bore! You can have the chips!"',
                '"I fold! My manicurist is arriving shortly anyway."',
            ],
            "raise": [
                '"More drama?! How thrilling! Double raise!" (+{amt})',
            ],
            "showdown_win": [
                '"Oh, darling, champagne for the victor! Better luck next time, sweetie!"',
                '"Magnificent! Another mountain of chips for my private yacht fund!"',
            ],
            "showdown_loss": [
                '"Oh, how simply outrageous! You took the entire pot from my hands!"',
                '"Dreadful villain! But oh, the drama of it was simply divine!"',
            ],
            "showdown_push": [
                '"A tie? How utterly anticlimactic! Dealer, pour more champagne!"',
            ],
            "player_fold": [
                '"Leaving already? Oh, darling, and here I thought we were flirting!"',
                '"A boring fold! Well, at least my manicure remains immaculate."',
            ],
        },
    ),
    # Chapter 5: Lord Sterling
    "Lord Sterling": OpponentProfile(
        name="Lord Sterling",
        title="Syndicator",
        aggression=0.75,
        bluff_rate=0.40,
        fold_resistance=0.60,
        bet_ratio=0.75,
        quotes={
            "check": [
                '"Hmph. Proceed with the street." (Checks)',
                '"I shall permit you another card." (Checks)',
            ],
            "bet": [
                '"An amateur cannot fathom my range! Pay the toll!" (+{amt})',
                '"You sit at MY felt! Face the syndicator\'s bet!" (+{amt})',
            ],
            "call": [
                '"Your petty raise doesn\'t intimidate me. Call."',
                '"Hmph. I shall humiliate you at showdown. Call."',
            ],
            "fold": [
                '"Insolent cheat! I refuse to indulge your luck!"',
                '"Mucked! My secondary portfolios outshine your winnings!"',
            ],
            "raise": [
                '"How dare you challenge a Sterling?! RE-RAISE!" (+{amt})',
            ],
            "showdown_win": [
                '"Did you truly imagine an unpedigreed amateur could rival a Sterling?!"',
                '"A predictable defeat. High finance is no playground for tourists."',
            ],
            "showdown_loss": [
                '"Insolent upstart! You dare humiliate a Sterling at his own felt?!"',
                '"Outrageous luck! My syndicates will crush your portfolio for this!"',
            ],
            "showdown_push": [
                '"A draw? Consider it an act of noblesse oblige on my part."',
            ],
            "player_fold": [
                '"Crawl away, beggar. You never possessed the pedigree for this pot."',
                '"Folds like cheap paper. Stick to low-stakes parlor games, amateur."',
            ],
        },
    ),
    # Chapter 6: Oligarch Thorne
    "Oligarch Thorne": OpponentProfile(
        name="Oligarch Thorne",
        title="Consortium Partner",
        aggression=0.85,
        bluff_rate=0.40,
        fold_resistance=0.80,
        bet_ratio=1.0,
        quotes={
            "check": [
                '"Checking. Let\'s see the big card." (Checks)',
                '"Go on, deal." (Checks)',
            ],
            "bet": [
                '"Pocket change to me, kid! Let\'s see you survive THIS!" (+{amt})',
                '"The consortium buys this pot! Pay up or pack up!" (+{amt})',
            ],
            "call": [
                '"Call. You can\'t out-spend a titan."',
                '"Trivial sum. Calling your bluff."',
            ],
            "fold": [
                '"Bah! A drop in the ocean! Take it!"',
                '"Folded. I have gold mines that earn more per second."',
            ],
            "raise": [
                '"You want a whale war?! Swallow THIS!" (+{amt})',
            ],
            "showdown_win": [
                '"Pocket change to pocket change! The consortium always sweeps the felt!"',
                '"Swallowed whole by the whale! You can\'t out-spend a titan, kid!"',
            ],
            "showdown_loss": [
                '"Bah! A minor dent in my gold mines! Enjoy your lucky pennies, kid!"',
                '"You cracked my hand?! Tch, I make that back before my coffee cools!"',
            ],
            "showdown_push": [
                '"A push?! Bah! Dealer, double the blinds and let\'s go again!"',
            ],
            "player_fold": [
                '"Smartest thing you\'ve done all night! Run before you lose your shirt!"',
                '"Broke and running scared! Next time bring a whale-sized bankroll!"',
            ],
        },
    ),
    # Chapter 7: Corinne Vane [Chief Auditor] (Mini-Boss 2)
    "Corinne Vane": OpponentProfile(
        name="Corinne Vane",
        title="Chief Auditor",
        aggression=0.65,
        bluff_rate=0.08,
        fold_resistance=0.50,
        bet_ratio=0.75,
        quotes={
            "check": [
                '"Expected value neutral. Check." (Checks)',
                '"Variance acceptable. Check." (Checks)',
            ],
            "bet": [
                '"Actuarial certainty: your win rate is sub-optimal." (+{amt})',
                '"Statistical leverage applied. Raising stake." (+{amt})',
            ],
            "call": [
                '"Pot odds dictate a positive expectation. Call."',
                '"Calling. Probability remains in corporate favor."',
            ],
            "fold": [
                '"Variance has turned negative. Optimal action: fold."',
                '"Risk parameters exceeded. Corporate stack preserved. Fold."',
            ],
            "raise": [
                '"Re-computing odds: corporate liquidity re-raise!" (+{amt})',
            ],
            "showdown_win": [
                '"Audit completed. Your assets have been liquidated under corporate law."',
                '"Actuarial precision. The syndicate\'s house edge is mathematically absolute."',
            ],
            "showdown_loss": [
                '"Variance anomaly detected... Error margin exceeded. Impressive play."',
                '"Statistical deviation recorded. You exploited a flaw in my calculations."',
            ],
            "showdown_push": [
                '"Net expectation zero. Books are balanced for this street."',
            ],
            "player_fold": [
                '"Rational decision. Folding minimizes downside risk under negative expectation."',
                '"Forfeit logged into corporate records. Capital effectively retained."',
            ],
            "bankrupt": [
                '"CRITICAL ALERT: Corporate treasury at absolute zero... I have failed the audit."',
                '"Ledger insolvency reached! The syndicate\'s legal firewall has been breached!"',
            ],
        },
    ),
    # Chapters 8-10: Baron Salvatore Croix (Boss)
    "Baron Salvatore Croix": OpponentProfile(
        name="Baron Salvatore Croix",
        title="Tycoon",
        aggression=0.80,
        bluff_rate=0.35,
        fold_resistance=0.85,
        bet_ratio=1.0,
        quotes={
            "check": [
                '"Hmph. Let us see the card, dealer." (Checks)',
                '"A brief respite before your ruin." (Checks)',
            ],
            "bet": [
                '"A pitiful stack from a pitiful novice! Match capital!" (+{amt})',
                '"I built an empire on blood and gold! You cannot stop me!" (+{amt})',
                '"Wager your future or surrender your chair!" (+{amt})',
            ],
            "call": [
                '"You cannot bluff the emperor of Celadon! Call!"',
                '"I shall peel back your petty cards myself! Call!"',
            ],
            "fold": [
                '"Insolent wretch! A temporary tactical mucking!"',
                '"Tch! Enjoy your minor victory! My empire is boundless!"',
            ],
            "raise": [
                '"YOU DARE RAISE SALVATORE CROIX?! DOUBLE DOWN!" (+{amt})',
                '"I will strip your bankroll to atoms! RE-RAISE!" (+{amt})',
            ],
            "showdown_win": [
                '"You sit in my salon, play with my chips, and bow to my empire! Hahaha!"',
                '"Did you think you could topple Salvatore Croix?! Know your place, worm!"',
            ],
            "showdown_loss": [
                '"Insolent insect! A petty scratch on a sovereign diamond!"',
                '"Tch! Savor your brief windfall! My Swiss vaults are bottomless!"',
            ],
            "showdown_push": [
                '"A temporary stalemate. Your execution is merely delayed."',
            ],
            "player_fold": [
                '"Bow your head and surrender! All who face Croix inevitably crumble!"',
                '"Pathetic coward! You dare not look upon my cards!"',
            ],
            "bankrupt": [
                '"What?! My personal reserves... drained?! Guards! This is an outrage!"',
            ],
        },
    ),
}


def get_opponent_profile(raw_name: str, chapter: str = "1") -> OpponentProfile:
    """Extracts base opponent name and returns the matching OpponentProfile."""
    clean = raw_name.split("[")[0].strip()
    if clean in OPPONENT_PROFILES:
        prof = OPPONENT_PROFILES[clean]
        # Dynamically adjust Baron Croix's aggression and quotes based on story chapter tilt
        if clean == "Baron Salvatore Croix":
            if chapter == "9":  # Cornered Vulture / Tilted Madman
                return OpponentProfile(
                    name=prof.name,
                    title="Cornered Vulture",
                    aggression=0.90,
                    bluff_rate=0.50,
                    fold_resistance=0.92,
                    bet_ratio=1.25,
                    quotes={
                        "check": ['"Hurry up and deal! I have quadrillions on the line!" (Checks)'],
                        "bet": [
                            '"I don\'t care what you hold! I am buying this board!" (+{amt})',
                            '"Emergency wire cleared! Swallow my fury!" (+{amt})',
                        ],
                        "call": ['"I CALL! My Swiss vaults will crush you!"'],
                        "fold": ['"Gaaah! The cards are rigged! Fold!"'],
                        "raise": ['"YOU WILL NOT HUMILIATE ME! ALL IN OR RE-RAISE!" (+{amt})'],
                        "showdown_win": [
                            '"YES! TAKE THAT, YOU SCUM! THE CROIX SYNDICATE CANNOT DIE!"',
                            '"I WON! I TOLD YOU MY WIRES WOULD CLEAR! SURRENDER YOUR LIFE!"',
                        ],
                        "showdown_loss": [
                            '"NOOOO! RIGGED! THE DEALER IS WORKING FOR YOU! THIS CANNOT BE!"',
                            '"GAAAAH! Another hundred trillion gone?! I\'LL TEAR THIS ROOM APART!"',
                        ],
                        "showdown_push": [
                            '"Pushed?! DEAL FASTER! I NEED TO RECOVER MY QUADRILLIONS!"',
                        ],
                        "player_fold": [
                            '"RUN, YOU WEAKLING! CROIX\'S EMPIRE FEEDS ON YOUR COWARDICE!"',
                            '"HA! You couldn\'t handle the pressure! Leave your tokens and crawl away!"',
                        ],
                        "bankrupt": [
                            '"MY EMPIRE! MY WIRES HAVE FROZEN! NO... NO! THE BOARD HAS ABANDONED ME!"',
                        ],
                    }
                )
            elif chapter == "10":  # Velvet Guillotine Climax
                return OpponentProfile(
                    name=prof.name,
                    title="Total Insolvency",
                    aggression=0.95,
                    bluff_rate=0.45,
                    fold_resistance=0.95,
                    bet_ratio=1.5,
                    quotes={
                        "check": ['"The deed is on the table... deal the river!" (Checks)'],
                        "bet": [
                            '"MY ENTIRE EMPIRE IS ON THIS FELT! MATCH ME!" (+{amt})',
                            '"The Velvet Guillotine falls on YOU! RAISE!" (+{amt})',
                        ],
                        "call": ['"ONE FINAL SHOWDOWN! I CALL!"'],
                        "fold": ['"No... NO! My deeds! Fold!"'],
                        "raise": ['"EVERY TOKEN I OWN SAYS YOU ARE DEAD! RE-RAISE!" (+{amt})'],
                        "showdown_win": [
                            '"MY EMPIRE LIVES! I WILL BUY THE ENTIRE REGION AND CRUSH YOU!"',
                            '"THE FELT BELONGS TO SALVATORE CROIX! BOW BEFORE YOUR MASTER!"',
                        ],
                        "showdown_loss": [
                            '"THE DEED... MY EMPIRE\'S DEED IS GONE! WHAT HAVE YOU DONE TO ME?!"',
                            '"NOOOOO! THE VELVET GUILLOTINE HAS FALLEN UPON MY NECK!"',
                        ],
                        "showdown_push": [
                            '"A push?! No! One final showdown! My life for your ruin!"',
                        ],
                        "player_fold": [
                            '"YOU RUN BEFORE THE EXECUTIONER?! I WILL HUNT YOU TO THE ENDS OF KANTO!"',
                        ],
                        "bankrupt": [
                            '"TOTAL INSOLVENCY... My deeds, my empire, my name... all turned to dust!"',
                        ],
                    }
                )
        return prof

    # Fallback default
    return OpponentProfile(
        name=raw_name,
        title="High-Roller",
        aggression=0.45,
        bluff_rate=0.20,
        fold_resistance=0.50,
        bet_ratio=0.5,
        quotes={
            "check": ['"Check." (Checks)'],
            "bet": ['"I\'ll raise the stakes." (+{amt})'],
            "call": ['"Call."'],
            "fold": ['"I fold."'],
            "raise": ['"Re-raise!" (+{amt})'],
            "showdown_win": ['"Good game. Fortune favored my cards."'],
            "showdown_loss": ['"Well played. The pot is yours."'],
            "showdown_push": ['"A push. We split the honors."'],
            "player_fold": ['"A prudent fold. Until the next hand."'],
            "bankrupt": ['"I have nothing left to wager..."'],
        }
    )


def evaluate_opponent_street_action(
    profile: OpponentProfile,
    dealer_rank_name: str,
    dealer_score: int,
    current_bet: int,
    available_tokens: int,
) -> Tuple[str, int, str]:
    """
    Evaluates whether the opponent checks or bets on the Flop/Turn.
    Returns: (action, bet_amount, quote_line)
    """
    is_monster = dealer_rank_name in ["Royal Flush", "Straight Flush", "Four of a Kind", "Full House", "Flush", "Straight"]
    is_strong = dealer_rank_name in ["Three of a Kind", "Two Pair"]
    is_marginal = dealer_rank_name in ["One Pair"]

    roll = random.random()
    should_bet = False

    if is_monster:
        should_bet = roll < (profile.aggression + 0.35)
    elif is_strong:
        should_bet = roll < profile.aggression
    elif is_marginal:
        should_bet = roll < (profile.aggression * 0.6)
    else:  # Air / Weak
        should_bet = roll < profile.bluff_rate

    if should_bet and current_bet > 0:
        raw_amt = int(current_bet * profile.bet_ratio)
        bet_amt = max(10_000_000_000_000, raw_amt)
        if available_tokens > 0:
            bet_amt = min(bet_amt, available_tokens)
        
        quote_tpl = random.choice(profile.quotes.get("bet", ['"I raise." (+{amt})']))
        quote = quote_tpl.format(amt=format_tokens(bet_amt))
        return "bet", bet_amt, quote

    # Check
    quote = random.choice(profile.quotes.get("check", ['"Check."']))
    return "check", 0, quote


def evaluate_opponent_reaction_to_raise(
    profile: OpponentProfile,
    dealer_rank_name: str,
    dealer_score: int,
    current_bet: int,
    raise_amount: int,
    is_allin: bool,
) -> Tuple[str, int, str]:
    """
    Evaluates how the opponent responds when the player raises or goes all-in.
    Returns: (action, bet_amount, quote_line)
    action can be: 'call', 'raise' (3-bet), or 'fold'.
    """
    top_rank = (dealer_score >> 16) & 0xF
    second_rank = (dealer_score >> 12) & 0xF
    is_high_pair = (dealer_rank_name == "One Pair" and top_rank >= 12)
    is_broadway_ace = (dealer_rank_name == "High Card" and top_rank == 14 and second_rank >= 12)

    is_monster = dealer_rank_name in ["Royal Flush", "Straight Flush", "Four of a Kind", "Full House", "Flush", "Straight"]
    is_strong = dealer_rank_name in ["Three of a Kind", "Two Pair"] or is_high_pair
    is_marginal = (dealer_rank_name in ["One Pair"] and not is_high_pair) or is_broadway_ace
    is_air = (dealer_rank_name in ["High Card"] and not is_broadway_ace)

    roll = random.random()

    # 1. Monster hands never fold; sometimes re-raise (3-bet) if not already all-in
    if is_monster:
        if not is_allin and roll < (profile.aggression * 0.4):
            re_raise = max(10_000_000_000_000, int(raise_amount * 0.5))
            quote = random.choice(profile.quotes.get("raise", ['"Re-raise!" (+{amt})'])).format(amt=format_tokens(re_raise))
            return "raise", re_raise, quote
        quote = random.choice(profile.quotes.get("call", ['"Call."']))
        return "call", 0, quote

    # 2. Strong hands call almost always, fold very rarely to massive shoves
    if is_strong:
        if is_allin and roll > (profile.fold_resistance + 0.2):
            quote = random.choice(profile.quotes.get("fold", ['"I fold."']))
            return "fold", 0, quote
        quote = random.choice(profile.quotes.get("call", ['"Call."']))
        return "call", 0, quote

    # 3. Marginal hands fold if fold_resistance is low
    if is_marginal:
        if roll > profile.fold_resistance:
            quote = random.choice(profile.quotes.get("fold", ['"I fold."']))
            return "fold", 0, quote
        quote = random.choice(profile.quotes.get("call", ['"Call."']))
        return "call", 0, quote

    # 4. Air / Bluffs fold heavily to raises unless hyper-stubborn (like Viktor)
    if is_air:
        if roll > (profile.fold_resistance * 0.4):
            quote = random.choice(profile.quotes.get("fold", ['"I fold."']))
            return "fold", 0, quote
        quote = random.choice(profile.quotes.get("call", ['"Call."']))
        return "call", 0, quote

    quote = random.choice(profile.quotes.get("call", ['"Call."']))
    return "call", 0, quote


def evaluate_opponent_end_quote(profile: OpponentProfile, situation: str) -> str:
    """
    Returns an appropriate in-character end-of-game quote for the given situation:
    - 'showdown_win': Opponent beats player at showdown
    - 'showdown_loss': Player beats opponent at showdown
    - 'showdown_push': Showdown ends in tie/push
    - 'player_fold': Player folds to opponent
    - 'bankrupt': Boss treasury stack is depleted to 0
    """
    quotes_list = profile.quotes.get(situation, [])
    if not quotes_list:
        if situation == "bankrupt":
            quotes_list = profile.quotes.get("showdown_loss", ['"Impossible... I have lost everything."'])
        elif situation == "player_fold":
            quotes_list = ['"You fold. The pot is mine."']
        elif situation == "showdown_win":
            quotes_list = ['"I take the pot. Good hand."']
        elif situation == "showdown_loss":
            quotes_list = ['"Well played. The chips are yours."']
        elif situation == "showdown_push":
            quotes_list = ['"A draw. The chips are divided."']
        else:
            quotes_list = ['"..."']
    return random.choice(quotes_list)
