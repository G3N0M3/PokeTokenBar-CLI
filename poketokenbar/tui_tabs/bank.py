import sys
from poketokenbar.utils.formatting import format_tokens
from poketokenbar.game.models import CORPORATIONS

HEADER = "\033[95m\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def render_bank_tab(app):
    subtab = getattr(app, "bank_subtab", "checking")
    if subtab not in ["checking", "cd", "stocks"]:
        subtab = "checking"
        app.bank_subtab = subtab

    avail = app.engine.available_tokens

    # Subtab Navigation Bar (70 columns)
    b_tab = f"{BOLD}{CYAN}[B] Checking & Loans{RESET}" if subtab == "checking" else "[B] Checking & Loans"
    c_tab = f"{BOLD}{CYAN}[C] Term Deposits (CD){RESET}" if subtab == "cd" else "[C] Term Deposits (CD)"
    s_tab = f"{BOLD}{CYAN}[S] Corporate Stocks{RESET}" if subtab == "stocks" else "[S] Corporate Stocks"

    sys.stdout.write(f"\n  {b_tab} | {c_tab} | {s_tab}\n")
    sys.stdout.write("  " + "-" * 68 + "\n\n")

    if subtab == "checking":
        _render_checking_view(app, avail)
    elif subtab == "cd":
        _render_cd_view(app, avail)
    elif subtab == "stocks":
        _render_stocks_view(app, avail)

def _render_checking_view(app, avail: int):
    bank = app.engine.state.get("bank_balance", 0)
    loan = app.engine.state.get("bank_loan", 0)
    loan_days = app.engine.state.get("loan_days_active", 0)

    sys.stdout.write(f"  {BOLD}{GREEN}🏦 Token Checking & Loans{RESET}  (Spendable: {BOLD}{CYAN}{format_tokens(avail)}{RESET})\n\n")
    sys.stdout.write(f"  {BOLD}Deposited Balance:{RESET} {BOLD}{GREEN}{format_tokens(bank)}{RESET} tokens\n")
    sys.stdout.write(f"  {BOLD}Active Loan Debt:{RESET}  {BOLD}{RED}{format_tokens(loan)}{RESET} tokens\n")
    
    if loan > 0:
        if loan_days == 6:
            sys.stdout.write(f"  {BOLD}{RED}🚨 WARNING: FINAL DAY BEFORE REPOSSESSION! PAY OFF LOAN NOW!{RESET}\n")
        else:
            sys.stdout.write(f"  {BOLD}{RED}🚨 Loan Deadline:{RESET} {loan_days}/7 days until repossession!\n")
        sys.stdout.write(f"  {BOLD}{RED}Repossession Protocol:{RESET}\n")
        sys.stdout.write(f"   {RED}1. Confiscation of Bank Deposits (up to loan amount){RESET}\n")
        sys.stdout.write(f"   {RED}2. Confiscation of Spendable Tokens (if debt remains){RESET}\n")
        sys.stdout.write(f"   {RED}3. Liquidation of Inventory Items (if debt remains){RESET}\n")
        sys.stdout.write(f"   {RED}4. Happiness of ALL companions drops by 50!{RESET}\n")
        
    sys.stdout.write(f"\n  {BOLD}Interest Rates (Daily Compounding):{RESET}\n")
    sys.stdout.write(f"  • {GREEN}Deposits:{RESET} +5% interest daily\n")
    max_loan = max(500_000_000, int(bank * 0.30))
    sys.stdout.write(f"  • {RED}Loans:{RESET}    -10% interest daily (Max Loan: {format_tokens(max_loan)})\n\n")
    sys.stdout.write(f"  {BOLD}Commands:{RESET}\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}deposit <amount>{RESET}' / '{BOLD}withdraw <amount>{RESET}' (e.g. 'deposit 1m')\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}loan <amount>{RESET}' / '{BOLD}payoff <amount>{RESET}' (e.g. 'payoff all')\n\n")

def _render_cd_view(app, avail: int):
    cds = app.engine.state.get("term_deposits", [])
    sys.stdout.write(f"  {BOLD}{YELLOW}📜 Certificates of Deposit (CD){RESET}  (Spendable: {BOLD}{CYAN}{format_tokens(avail)}{RESET})\n")
    sys.stdout.write(f"  {CYAN}Locked fixed-term savings accounts with high compound yields.{RESET}\n\n")
    sys.stdout.write(f"  {BOLD}Available CD Terms & Daily Yields:{RESET}\n")
    sys.stdout.write(f"  • {GREEN}3-Day Term:{RESET}   {BOLD}8%/day{RESET}  (Early break: 10% penalty, forfeits interest)\n")
    sys.stdout.write(f"  • {GREEN}7-Day Term:{RESET}  {BOLD}12%/day{RESET}  (Early break: 10% penalty, forfeits interest)\n")
    sys.stdout.write(f"  • {GREEN}14-Day Term:{RESET} {BOLD}20%/day{RESET}  (Early break: 10% penalty, forfeits interest)\n\n")

    sys.stdout.write(f"  {BOLD}Active Term Deposits ({len(cds)} active):{RESET}\n")
    if not cds:
        sys.stdout.write("  (No active Term Deposits. Open one with 'cd open <amount> <days>')\n\n")
    else:
        for cd in cds:
            c_id = cd.get("id", 1)
            principal = format_tokens(cd.get("principal", 0))
            term = cd.get("term_days", 3)
            elapsed = cd.get("days_elapsed", 0)
            cur_val = format_tokens(cd.get("current_value", cd.get("principal", 0)))
            if cd.get("matured"):
                status_str = f"{BOLD}{GREEN}[MATURED! Claimable]{RESET}"
            else:
                days_left = max(0, term - elapsed)
                status_str = f"{YELLOW}[LOCKED] ({days_left}d left){RESET}"
            sys.stdout.write(f"  #{c_id:<2} {principal:<7} ({term}d term, {elapsed}/{term}d) -> {BOLD}{CYAN}{cur_val:<7}{RESET} | {status_str}\n")
        sys.stdout.write("\n")

    sys.stdout.write(f"  {BOLD}Commands:{RESET}\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}cd open <amount> <3|7|14>{RESET}' (e.g. 'cd open 10m 7')\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}cd claim <id|all>{RESET}' to claim matured deposits\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}cd break <id>{RESET}' for early withdrawal (10% penalty)\n\n")

def _render_stocks_view(app, avail: int):
    investments = app.engine.state.get("investments", {})
    streak = app.engine.state.get("streak_days", 1)
    streak_bonus = min(0.05, streak * 0.002)
    streak_bonus_pct = streak_bonus * 100

    sys.stdout.write(f"  {BOLD}{BLUE}📈 Pokémon Corporate Stock Exchange{RESET}  (Spendable: {BOLD}{CYAN}{format_tokens(avail)}{RESET})\n")
    sys.stdout.write(f"  🔥 Streak: {BOLD}{YELLOW}{streak}d{RESET} (Grants +{streak_bonus_pct:.1f}% bonus to all dividend yields!)\n\n")

    corp_items = list(CORPORATIONS.items())
    page_size = 3
    total_pages = max(1, (len(corp_items) - 1) // page_size + 1)
    if not hasattr(app, "stock_page") or not isinstance(app.stock_page, int):
        app.stock_page = 1
    app.stock_page = max(1, min(app.stock_page, total_pages))

    start_idx = (app.stock_page - 1) * page_size
    end_idx = start_idx + page_size
    visible_corps = corp_items[start_idx:end_idx]

    total_invested = sum(investments.get(k, 0) * c.share_price for k, c in CORPORATIONS.items())
    total_daily_div = sum(int(investments.get(k, 0) * c.share_price * (c.base_dividend + streak_bonus)) for k, c in CORPORATIONS.items())

    idx = start_idx + 1
    for key, corp in visible_corps:
        shares = investments.get(key, 0)
        eff_rate = corp.base_dividend + streak_bonus
        div_day = int(shares * corp.share_price * eff_rate)

        perk_status = f"{BOLD}{GREEN}[ACTIVE]{RESET}" if shares > 0 else f"{RED}[INACTIVE]{RESET}"
        owned_str = f"{BOLD}{GREEN}{shares} shares{RESET}" if shares > 0 else "0 shares"

        sys.stdout.write(f"  [{idx}] [{BOLD}{CYAN}{corp.ticker}{RESET}] {BOLD}{corp.name}{RESET} — {format_tokens(corp.share_price)}/sh | Own: {owned_str}\n")
        sys.stdout.write(f"      Div: {corp.base_dividend*100:.1f}% (+{streak_bonus_pct:.1f}% = {eff_rate*100:.1f}%/d) ➔ Yield: +{format_tokens(div_day)}/day\n")
        sys.stdout.write(f"      Perk: {BOLD}{corp.perk_name}{RESET} {perk_status}\n")
        sys.stdout.write(f"      Effect: {corp.perk_desc}\n\n")
        idx += 1

    if total_pages > 1:
        sys.stdout.write(f"  ➔ Page {app.stock_page}/{total_pages} - Type '{BOLD}next{RESET}', '{BOLD}prev{RESET}', or '{BOLD}page <N>{RESET}' to browse stocks\n\n")

    sys.stdout.write(f"  {BOLD}Portfolio Summary:{RESET} Total: {BOLD}{CYAN}{format_tokens(total_invested)}{RESET} | Daily Div: {BOLD}{GREEN}+{format_tokens(total_daily_div)}{RESET}/day\n\n")
    sys.stdout.write(f"  {BOLD}Commands:{RESET}\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}invest <code> <shares|all>{RESET}' (e.g. 'invest SILPH 2')\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}divest <code> <shares|all>{RESET}' to sell (10% spread)\n\n")
