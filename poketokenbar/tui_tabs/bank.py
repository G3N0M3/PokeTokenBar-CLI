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

def render_bank_tab(app):
    avail = app.engine.available_tokens
    bank = app.engine.state.get("bank_balance", 0)
    loan = app.engine.state.get("bank_loan", 0)
    loan_days = app.engine.state.get("loan_days_active", 0)

    sys.stdout.write(f"\n  {BOLD}{GREEN}🏦 Token Bank{RESET}  (Available Spendable Tokens: {BOLD}{CYAN}{format_tokens(avail)}{RESET})\n\n")
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
    sys.stdout.write(f"  • {GREEN}Deposits:{RESET} +5% interest\n")
    max_loan = max(500_000_000, int(bank * 0.30))
    sys.stdout.write(f"  • {RED}Loans:{RESET}    -10% interest (Max Loan: {format_tokens(max_loan)})\n\n")
    sys.stdout.write(f"  {BOLD}Commands:{RESET}\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}deposit <amount>{RESET}' / '{BOLD}withdraw <amount>{RESET}' (e.g. 'deposit 1m')\n")
    sys.stdout.write(f"  ➔ Type '{BOLD}loan <amount>{RESET}' / '{BOLD}payoff <amount>{RESET}' (e.g. 'payoff all')\n\n")
