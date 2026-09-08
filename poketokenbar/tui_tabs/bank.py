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

SPARK_CHARS = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

def generate_sparkline(history: list) -> str:
    if not history:
        return "[ " + "▄" * 7 + " ]"
    pts = list(history)
    if len(pts) < 7:
        pts = [pts[0]] * (7 - len(pts)) + pts
    else:
        pts = pts[-7:]
    min_v, max_v = min(pts), max(pts)
    rng = max_v - min_v
    res = []
    for p in pts:
        if rng == 0:
            res.append("▄")
        else:
            norm = (p - min_v) / rng
            idx = min(len(SPARK_CHARS) - 1, max(0, int(norm * (len(SPARK_CHARS) - 1))))
            res.append(SPARK_CHARS[idx])
    return "[ " + "".join(res) + " ]"

def _render_stocks_view(app, avail: int):
    stock_term = getattr(app, "stock_terminal", None)
    if stock_term and isinstance(stock_term, str) and stock_term.lower() in CORPORATIONS:
        _render_stock_terminal(app, avail, stock_term.lower())
        return

    sm = app.engine.get_or_init_stock_market()
    streak = app.engine.state.get("streak_days", 1)
    streak_bonus = min(0.05, streak * 0.002)
    streak_bonus_pct = streak_bonus * 100

    sys.stdout.write(f"  {BOLD}{BLUE}📈 Pokémon Corporate Stock Exchange{RESET}\n")
    streak_str = f"🔥 Streak: {BOLD}{YELLOW}{streak}d{RESET} (+{streak_bonus_pct:.1f}% div)"
    bal_str = f"Spendable: {BOLD}{CYAN}{format_tokens(avail)}{RESET}"
    sys.stdout.write(f"  {streak_str} | {bal_str}\n")

    headline = sm.get("market_headline", "POKÉMON EXCHANGE: Indices opening with steady volume.")
    if len(headline) > 64:
        headline = headline[:61] + "..."
    sys.stdout.write(f"  📰 {BOLD}{CYAN}{headline}{RESET}\n")
    sys.stdout.write("  " + "-" * 68 + "\n\n")

    corp_items = list(CORPORATIONS.items())
    page_size = 3
    total_pages = max(1, (len(corp_items) - 1) // page_size + 1)
    if not hasattr(app, "stock_page") or not isinstance(app.stock_page, int):
        app.stock_page = 1
    app.stock_page = max(1, min(app.stock_page, total_pages))

    start_idx = (app.stock_page - 1) * page_size
    end_idx = start_idx + page_size
    visible_corps = corp_items[start_idx:end_idx]

    total_invested = 0
    total_market_val = 0
    total_daily_div = 0

    for key, corp in corp_items:
        details = app.engine.get_stock_details(key)
        if details:
            total_invested += details["cost_basis"]
            total_market_val += details["liq_val"]
            total_daily_div += details["daily_div"]

    portfolio_pnl = total_market_val - total_invested
    pnl_sign = "+" if portfolio_pnl >= 0 else ""

    idx = start_idx + 1
    for key, corp in visible_corps:
        details = app.engine.get_stock_details(key)
        if not details:
            continue

        c_price = details["current_price"]
        chg = details["change_pct"]
        owned = details["owned"]
        cost_basis = details["cost_basis"]
        avg_cost = details["avg_cost"]
        eff_rate = details["eff_rate"]
        spark = generate_sparkline(details["price_history"])
        news = details["latest_news"]

        if chg > 0:
            chg_str = f"{GREEN}▲+{chg:.1f}%{RESET}"
        elif chg < 0:
            chg_str = f"{RED}▼{chg:.1f}%{RESET}"
        else:
            chg_str = f"{YELLOW}— 0.0%{RESET}"

        status_badge = f"{BOLD}{GREEN}[ACTIVE]{RESET}" if owned > 0 else f"{RED}[INACTIVE]{RESET}"

        sys.stdout.write(f"  [{idx}] [{BOLD}{CYAN}{corp.ticker}{RESET}] {BOLD}{corp.name}{RESET} — {format_tokens(c_price)}/sh ({chg_str}) {status_badge}\n")
        sys.stdout.write(f"      7d: {spark} | Div: {corp.base_dividend*100:.1f}% (+{streak_bonus_pct:.1f}% = {eff_rate*100:.1f}%/d)\n")

        if owned > 0:
            unreal_pnl = details["unrealized_pnl"]
            u_sign = "+" if unreal_pnl >= 0 else ""
            pnl_col = GREEN if unreal_pnl >= 0 else RED
            sys.stdout.write(f"      Own: {BOLD}{CYAN}{owned} sh{RESET} ({format_tokens(details['market_val'])}) | Cost: {format_tokens(avg_cost)} | P&L: {pnl_col}{u_sign}{format_tokens(unreal_pnl)}{RESET}\n")
        else:
            sys.stdout.write(f"      Perk: {BOLD}{corp.perk_name}{RESET} — {corp.perk_desc}\n")

        if len(news) > 52:
            news = news[:49] + "..."
        sys.stdout.write(f"      News: \"{CYAN}{news}{RESET}\"\n\n")
        idx += 1

    sys.stdout.write("  " + "-" * 68 + "\n")
    pnl_col = GREEN if portfolio_pnl >= 0 else RED
    pnl_display = f"{pnl_col}{pnl_sign}{format_tokens(portfolio_pnl)}{RESET}"
    sys.stdout.write(f"  {BOLD}Portfolio:{RESET} Cost: {BOLD}{CYAN}{format_tokens(total_invested)}{RESET} | Val: {BOLD}{GREEN}{format_tokens(total_market_val)}{RESET} | P&L: {pnl_display} | Div: +{format_tokens(total_daily_div)}/d\n")
    sys.stdout.write(f"  Page {app.stock_page}/{total_pages} ('n'/'p') | Type '{BOLD}stock <idx|code>{RESET}' for Terminal\n")
    sys.stdout.write(f"  ➔ Commands: '{BOLD}invest <code> <qty>{RESET}', '{BOLD}divest <code> <qty>{RESET}'\n\n")

def _render_stock_terminal(app, avail: int, corp_key: str):
    details = app.engine.get_stock_details(corp_key)
    if not details:
        sys.stdout.write(f"  {RED}Error: Corporation '{corp_key}' not found.{RESET}\n")
        sys.stdout.write(f"  Type '{BOLD}back{RESET}' to return to Exchange Board.\n\n")
        return

    corp = details["corp"]
    c_price = details["current_price"]
    chg = details["change_pct"]
    spark = generate_sparkline(details["price_history"])
    owned = details["owned"]
    cost_basis = details["cost_basis"]
    avg_cost = details["avg_cost"]
    market_val = details["market_val"]
    liq_val = details["liq_val"]
    unreal_pnl = details["unrealized_pnl"]
    unreal_pct = details["unrealized_pnl_pct"]
    news = details["latest_news"]
    eff_rate = details["eff_rate"]
    daily_div = details["daily_div"]

    if chg > 0:
        chg_str = f"{GREEN}▲ +{chg:.1f}%{RESET}"
    elif chg < 0:
        chg_str = f"{RED}▼ {abs(chg):.1f}%{RESET}"
    else:
        chg_str = f"{YELLOW}— 0.0%{RESET}"

    pnl_col = GREEN if unreal_pnl >= 0 else RED
    pnl_sign = "+" if unreal_pnl >= 0 else ""
    active_badge = f"{BOLD}{GREEN}[ACTIVE]{RESET}" if owned > 0 else f"{RED}[INACTIVE]{RESET}"

    sys.stdout.write(f"  {BOLD}{CYAN}🏢 TRADE TERMINAL: [{corp.ticker}] {corp.name}{RESET}\n")
    sys.stdout.write(f"  Price: {BOLD}{GREEN}{format_tokens(c_price)}{RESET}/sh ({chg_str}) | 7d: {spark}\n")
    sys.stdout.write("  " + "-" * 68 + "\n\n")

    sys.stdout.write(f"  {BOLD}Your Position & Analytics:{RESET}\n")
    sys.stdout.write(f"  • Shares Owned:       {BOLD}{CYAN}{owned} share(s){RESET} {active_badge}\n")
    sys.stdout.write(f"  • Weighted Cost:      {format_tokens(avg_cost)}/sh (Total: {format_tokens(cost_basis)})\n")
    sys.stdout.write(f"  • Market Value:       {format_tokens(market_val)} tokens\n")
    sys.stdout.write(f"  • Liquidation Value:  {format_tokens(liq_val)} tokens (10% spread applied)\n")
    pnl_str = f"{pnl_col}{pnl_sign}{format_tokens(unreal_pnl)} ({pnl_sign}{unreal_pct:.1f}%){RESET}"
    sys.stdout.write(f"  • Unrealized P&L:     {pnl_str}\n")
    sys.stdout.write(f"  • Daily Dividend:     {BOLD}{GREEN}+{format_tokens(daily_div)}{RESET}/day ({eff_rate*100:.1f}% yield)\n\n")

    sys.stdout.write(f"  {BOLD}Corporate Profile & Catalysts:{RESET}\n")
    sys.stdout.write(f"  • Perk:     {BOLD}{corp.perk_name}{RESET} — {corp.perk_desc}\n")
    cat_desc = corp.catalyst_desc if len(corp.catalyst_desc) <= 52 else corp.catalyst_desc[:49] + "..."
    sys.stdout.write(f"  • Catalyst: {cat_desc}\n")
    if len(news) > 52:
        news = news[:49] + "..."
    sys.stdout.write(f"  • Headline: \"{CYAN}{news}{RESET}\"\n\n")

    sys.stdout.write("  " + "-" * 68 + "\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}buy <qty|all>{RESET}' or '{BOLD}sell <qty|all>{RESET}' to trade\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}back{RESET}' to return to Exchange Board (Spendable: {CYAN}{format_tokens(avail)}{RESET})\n\n")
