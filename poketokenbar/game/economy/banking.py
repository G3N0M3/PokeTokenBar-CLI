import datetime
from typing import Dict, List, Tuple, Optional, Any, Union

from poketokenbar.utils.formatting import format_tokens, parse_tokens
from poketokenbar.game.models import ItemKind, CORPORATIONS


class BankingMixin:
    """Provides checking accounts, collateralized loans, CDs, interest, and repossession waterfall."""

    def handle_bank_transaction(self, action: str, amount_str: str) -> Tuple[bool, str]:
        clean_str = amount_str.lower().strip()
        if clean_str == "all":
            if action == "deposit":
                amount = self.available_tokens
            elif action == "withdraw":
                amount = self.state.get("bank_balance", 0)
            elif action == "payoff":
                amount = min(self.available_tokens, self.state.get("bank_loan", 0))
            else:
                return False, "Cannot use 'all' with loan!"
        else:
            amount = parse_tokens(amount_str)
            if amount < 0:
                return False, "Invalid amount! Example: 'deposit 500k', 'withdraw 1m', 'loan 10m', 'payoff all'."
        
        if amount <= 0:
            return False, "Amount must be greater than 0!"
            
        if action == "deposit":
            if amount > self.available_tokens:
                return False, f"Not enough tokens to deposit! You only have {format_tokens(self.available_tokens)}."
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + amount
            self.state["bank_balance"] = self.state.get("bank_balance", 0) + amount
            self.save()
            new_bal = self.state["bank_balance"]
            daily_int = int(new_bal * 1.05) - new_bal
            return True, f"🏦 Deposited {format_tokens(amount)} tokens. Balance: {format_tokens(new_bal)} (+{format_tokens(daily_int)}/day interest)"
            
        elif action == "withdraw":
            current_bank = self.state.get("bank_balance", 0)
            if current_bank - amount < 0:
                return False, f"🏦 You cannot withdraw {format_tokens(amount)} tokens! You only have {format_tokens(current_bank)} deposited."
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - amount
            self.state["bank_balance"] = current_bank - amount
            self.save()
            new_bal = self.state["bank_balance"]
            daily_int = int(new_bal * 1.05) - new_bal
            return True, f"🏦 Withdrew {format_tokens(amount)} tokens. Balance: {format_tokens(new_bal)} (+{format_tokens(daily_int)}/day interest)"
            
        elif action == "loan":
            current_loan = self.state.get("bank_loan", 0)
            bank_balance = self.state.get("bank_balance", 0)
            max_loan = max(500_000_000, int(bank_balance * 0.30))
            if current_loan + amount > max_loan:
                return False, f"🏦 Loan denied! Maximum token loan limit is {format_tokens(max_loan)}."
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - amount
            self.state["bank_loan"] = current_loan + amount
            if current_loan == 0:
                self.state["loan_days_active"] = 0
            self.save()
            new_loan = self.state["bank_loan"]
            daily_int = int(new_loan * 1.10) - new_loan
            return True, f"🏦 Took loan of {format_tokens(amount)} tokens. Debt: {format_tokens(new_loan)} (+{format_tokens(daily_int)}/day interest)"
            
        elif action == "payoff":
            current_loan = self.state.get("bank_loan", 0)
            if current_loan == 0:
                return False, "🏦 You do not have any active loans to pay off!"
            amount_to_pay = min(amount, current_loan)
            if amount_to_pay > self.available_tokens:
                return False, f"Not enough tokens to pay off! You only have {format_tokens(self.available_tokens)}."
                
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + amount_to_pay
            self.state["bank_loan"] = current_loan - amount_to_pay
            if self.state["bank_loan"] == 0:
                self.state["loan_days_active"] = 0
            self.save()
            new_loan = self.state["bank_loan"]
            if new_loan > 0:
                daily_int = int(new_loan * 1.10) - new_loan
                return True, f"🏦 Paid off {format_tokens(amount_to_pay)} tokens! Debt: {format_tokens(new_loan)} (+{format_tokens(daily_int)}/day interest)"
            else:
                return True, f"🏦 Paid off {format_tokens(amount_to_pay)} tokens! Loan debt fully cleared! 🎉"
        else:
            return False, "Invalid bank action."

    def open_cd(self, amount_str: str, term_days: int) -> Tuple[bool, str]:
        if term_days not in [3, 7, 14]:
            return False, "Invalid term! Available CD terms: 3 days (8%/day), 7 days (12%/day), or 14 days (20%/day)."
        
        rates = {3: 0.08, 7: 0.12, 14: 0.20}
        rate = rates[term_days]

        clean_str = amount_str.lower().strip()
        if clean_str == "all":
            amount = self.available_tokens
        else:
            amount = parse_tokens(amount_str)
            if amount < 0:
                return False, "Invalid amount! Example: 'cd open 5m 7', 'cd open 10m 14', 'cd open all 3'."

        if amount <= 0:
            return False, "Deposit amount must be greater than 0!"
        if amount > self.available_tokens:
            return False, f"Not enough tokens! You only have {format_tokens(self.available_tokens)} available."

        cds = self.state.setdefault("term_deposits", [])
        used_ids = {c.get("id", 0) for c in cds}
        next_id = 1
        while next_id in used_ids:
            next_id += 1
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")

        cd_entry = {
            "id": next_id,
            "principal": amount,
            "term_days": term_days,
            "days_elapsed": 0,
            "daily_rate": rate,
            "current_value": amount,
            "matured": False,
            "start_date": today_str
        }
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + amount
        cds.append(cd_entry)
        self.state["term_deposits"] = cds
        self.save()
        return True, f"🏦 Opened {term_days}-Day CD [{next_id}] for {format_tokens(amount)} tokens at {int(rate*100)}%/day interest! (Early break: 10% penalty, forfeits interest)"

    def get_sorted_cds(self) -> List[Dict[str, Any]]:
        """Returns active Term Deposits (CDs) sorted according to the active cd_sort_criteria.
        
        Criteria options:
        - 'days': Matured (claimable) first, then shortest remaining time to longest, then highest value, then id.
        - 'amount': Highest current value (or principal) first, then matured first, then days remaining, then id.
        - 'term': Longest term duration first (14d -> 7d -> 3d), then matured first, then days remaining, then id.
        """
        cds = list(self.state.get("term_deposits", []))
        criteria = self.state.get("cd_sort_criteria", "days")
        if not isinstance(criteria, str):
            criteria = "days"
        criteria = criteria.lower().strip()
        
        if criteria in ["amount", "amt", "value", "val", "principal"]:
            return sorted(
                cds,
                key=lambda c: (
                    -c.get("current_value", c.get("principal", 0)),
                    0 if c.get("matured") else 1,
                    max(0, c.get("term_days", 3) - c.get("days_elapsed", 0)),
                    c.get("id", 0)
                )
            )
        elif criteria in ["term", "duration"]:
            return sorted(
                cds,
                key=lambda c: (
                    -c.get("term_days", 3),
                    0 if c.get("matured") else 1,
                    max(0, c.get("term_days", 3) - c.get("days_elapsed", 0)),
                    -c.get("current_value", c.get("principal", 0)),
                    c.get("id", 0)
                )
            )
        else:  # default: "days"
            return sorted(
                cds,
                key=lambda c: (
                    0 if c.get("matured") else 1,
                    max(0, c.get("term_days", 3) - c.get("days_elapsed", 0)),
                    -c.get("current_value", c.get("principal", 0)),
                    c.get("id", 0)
                )
            )

    def set_cd_sort_criteria(self, criteria: str) -> Tuple[bool, str]:
        """Sets the ordering criteria for active Term Deposits in the Bank tab."""
        raw = criteria.lower().strip()
        if raw in ["days", "day", "days_left", "time", "date"]:
            normalized = "days"
            label = "Days Left (Matured First)"
        elif raw in ["amount", "amt", "value", "val", "principal"]:
            normalized = "amount"
            label = "Deposit Value (Highest First)"
        elif raw in ["term", "duration"]:
            normalized = "term"
            label = "Term Duration (Longest First)"
        else:
            return False, "Invalid sort criteria! Options: 'days' (days left), 'amount' (highest value), 'term' (term duration)."
        
        self.state["cd_sort_criteria"] = normalized
        self.save()
        return True, f"🏦 Term Deposits sort criteria updated: {label}."

    def claim_cd(self, cd_id_str: str) -> Tuple[bool, str]:
        cds = self.state.get("term_deposits", [])
        clean_str = cd_id_str.lower().strip().lstrip("#[").rstrip("]")
        if clean_str == "all":
            matured_cds = [c for c in cds if c.get("matured")]
            if not matured_cds:
                return False, "No matured CDs available to claim!"
            total_principal = sum(c["principal"] for c in matured_cds)
            total_value = sum(c["current_value"] for c in matured_cds)
            total_interest = total_value - total_principal
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - total_value
            self.state["term_deposits"] = [c for c in cds if not c.get("matured")]
            self.save()
            return True, f"🏦 Claimed {len(matured_cds)} matured CD(s)! Principal: {format_tokens(total_principal)} + Interest: {format_tokens(total_interest)} = {format_tokens(total_value)} tokens credited!"
        
        try:
            target_id = int(clean_str)
        except ValueError:
            return False, "Invalid CD ID. Example: 'cd claim 1' or 'cd claim all'."

        sorted_cds = self.get_sorted_cds()
        found = None
        # 1. Primary resolution: 1-based display index in the sorted list
        if 1 <= target_id <= len(sorted_cds):
            found = sorted_cds[target_id - 1]

        # 2. Fallback resolution: internal deposit ID
        if not found:
            for c in sorted_cds:
                if c.get("id") == target_id:
                    found = c
                    break

        if not found:
            return False, f"Certificate of Deposit [{target_id}] not found."

        disp_idx = sorted_cds.index(found) + 1 if found in sorted_cds else target_id
        if not found.get("matured"):
            days_left = max(0, found["term_days"] - found.get("days_elapsed", 0))
            return False, f"CD [{disp_idx}] has not matured yet ({days_left} day(s) remaining)! Type 'cd break {disp_idx}' for early withdrawal (forfeits interest + 10% penalty)."

        principal = found["principal"]
        val = found["current_value"]
        interest = val - principal
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - val
        cds.remove(found)
        self.state["term_deposits"] = cds
        self.save()
        return True, f"🏦 Claimed CD [{disp_idx}]! Principal: {format_tokens(principal)} + Interest: {format_tokens(interest)} = {format_tokens(val)} tokens credited to your spendable balance!"

    def break_cd(self, cd_id_str: str) -> Tuple[bool, str]:
        cds = self.state.get("term_deposits", [])
        clean_str = cd_id_str.strip().lstrip("#[").rstrip("]")
        try:
            target_id = int(clean_str)
        except ValueError:
            return False, "Invalid CD ID. Example: 'cd break 1'."

        sorted_cds = self.get_sorted_cds()
        found = None
        # 1. Primary resolution: 1-based display index in the sorted list
        if 1 <= target_id <= len(sorted_cds):
            found = sorted_cds[target_id - 1]

        # 2. Fallback resolution: internal deposit ID
        if not found:
            for c in sorted_cds:
                if c.get("id") == target_id:
                    found = c
                    break

        if not found:
            return False, f"Certificate of Deposit [{target_id}] not found."

        disp_idx = sorted_cds.index(found) + 1 if found in sorted_cds else target_id
        principal = found["principal"]
        refund = int(principal * 0.90)
        penalty = principal - refund
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - refund
        cds.remove(found)
        self.state["term_deposits"] = cds
        self.save()
        return True, f"⚠️ Early withdrawal of CD [{disp_idx}]: Forfeited all interest and paid 10% penalty ({format_tokens(penalty)}). Refunded {format_tokens(refund)} tokens to your spendable balance."

    def _apply_bank_day_rollover(self, days_to_apply: int, events: List[str]):
        """Processes daily interest for checking deposits and CDs, accrues loan interest, and handles repossession."""
        bank_balance = self.state.get("bank_balance", 0)
        bank_loan = self.state.get("bank_loan", 0)

        if bank_balance > 0:
            new_balance = bank_balance
            for _ in range(days_to_apply):
                new_balance = int(new_balance * 1.05)
            events.append(f"🏦 Your Token Bank earned {format_tokens(new_balance - bank_balance)} tokens in interest!")
            self.state["bank_balance"] = new_balance

        # Process Term Deposits (CDs)
        cds = self.state.get("term_deposits", [])
        for cd in cds:
            if not cd.get("matured"):
                rate = cd.get("daily_rate", 0.08)
                days_left = cd["term_days"] - cd.get("days_elapsed", 0)
                days_to_advance = min(days_to_apply, days_left)
                for _ in range(days_to_advance):
                    cd["current_value"] = int(cd["current_value"] * (1 + rate))
                cd["days_elapsed"] = cd.get("days_elapsed", 0) + days_to_advance
                if cd["days_elapsed"] >= cd["term_days"]:
                    cd["matured"] = True
                    events.append(f"🏦 Certificate of Deposit [{cd['id']}] ({cd['term_days']}d) has MATURED! Total Value: {format_tokens(cd['current_value'])} tokens (Type 'cd claim {cd['id']}')")

        if bank_loan > 0:
            new_loan = bank_loan
            for _ in range(days_to_apply):
                new_loan = int(new_loan * 1.10)
            events.append(f"🏦 Your Token Bank loan accumulated {format_tokens(new_loan - bank_loan)} tokens in interest!")
            self.state["bank_loan"] = new_loan

            loan_days = self.state.get("loan_days_active", 0) + days_to_apply
            self.state["loan_days_active"] = loan_days

            if loan_days >= 7:
                self._execute_repossession(new_loan, events)

    def _execute_repossession(self, remaining_loan: int, events: List[str]):
        """Liquidates assets across 6 tiers to cover defaulted loan debt."""
        # 1. Confiscate from Bank Balance
        bank_bal = self.state.get("bank_balance", 0)
        take_from_bank = min(bank_bal, remaining_loan)
        if take_from_bank > 0:
            self.state["bank_balance"] -= take_from_bank
            remaining_loan -= take_from_bank
            events.append(f"🚨 REPOSSESSION: Confiscated {format_tokens(take_from_bank)} tokens from your Bank deposits.")

        # 2. Confiscate from Available Tokens
        if remaining_loan > 0:
            avail_tokens = self.state.get("used_since_install", 0) - self.state.get("spent_tokens", 0)
            take_from_avail = min(avail_tokens, remaining_loan)
            if take_from_avail > 0:
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + take_from_avail
                remaining_loan -= take_from_avail
                events.append(f"🚨 REPOSSESSION: Confiscated {format_tokens(take_from_avail)} spendable tokens.")

        # 3. Liquidate Term Deposits (CDs)
        if remaining_loan > 0:
            cds = self.state.get("term_deposits", [])
            if cds:
                matured_cds = [c for c in cds if c.get("matured")]
                unmatured_cds = [c for c in cds if not c.get("matured")]
                ordered_cds = matured_cds + unmatured_cds

                repossessed_cds = []
                total_cd_seized = 0

                for cd in ordered_cds:
                    if remaining_loan <= 0:
                        break

                    if cd.get("matured"):
                        cd_val = cd.get("current_value", cd.get("principal", 0))
                    else:
                        # Early break: 10% penalty, forfeits accrued interest
                        cd_val = int(cd.get("principal", 0) * 0.90)

                    if cd_val <= 0:
                        repossessed_cds.append(cd)
                        continue

                    take = min(remaining_loan, cd_val)
                    remaining_loan -= take
                    total_cd_seized += take
                    repossessed_cds.append(cd)

                    if cd_val > take:
                        surplus = cd_val - take
                        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - surplus
                        events.append(f"🏦 Repossession refund: {format_tokens(surplus)} excess CD proceeds returned.")

                self.state["term_deposits"] = [c for c in cds if c not in repossessed_cds]
                if total_cd_seized > 0:
                    events.append(f"🚨 REPOSSESSION: Liquidated {len(repossessed_cds)} CD(s) for {format_tokens(total_cd_seized)} tokens.")

        # 4. Liquidate Corporate Stocks
        if remaining_loan > 0:
            invs = self.state.get("investments", {})
            sm = self.get_or_init_stock_market()
            sm_prices = sm.get("prices", {})
            cost_basis = sm.setdefault("cost_basis", {})

            total_stock_seized = 0
            stock_liquidated_notes = []

            for corp_key in list(invs.keys()):
                if remaining_loan <= 0:
                    break
                shares_owned = invs.get(corp_key, 0)
                if shares_owned <= 0:
                    continue

                corp_info = CORPORATIONS.get(corp_key)
                curr_price = sm_prices.get(corp_key, corp_info.share_price if corp_info else 10_000_000)
                # 10% liquidation fee / market spread (standard divest payout)
                per_share_val = int(curr_price * 0.90)
                if per_share_val <= 0:
                    continue

                needed_shares = min(shares_owned, (remaining_loan + per_share_val - 1) // per_share_val)
                gross_payout = needed_shares * per_share_val
                take = min(remaining_loan, gross_payout)

                avg_cost = cost_basis.get(corp_key, 0) // shares_owned if shares_owned > 0 else 0
                cost_basis[corp_key] = max(0, cost_basis.get(corp_key, 0) - (needed_shares * avg_cost))
                invs[corp_key] -= needed_shares

                remaining_loan -= take
                total_stock_seized += take

                ticker = corp_info.ticker if corp_info else corp_key.upper()
                stock_liquidated_notes.append(f"{needed_shares} {ticker}")

                if gross_payout > take:
                    surplus = gross_payout - take
                    self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - surplus
                    events.append(f"🏦 Repossession refund: {format_tokens(surplus)} excess stock proceeds returned.")

            self.state["investments"] = invs
            if total_stock_seized > 0:
                events.append(f"🚨 REPOSSESSION: Liquidated {', '.join(stock_liquidated_notes)} for {format_tokens(total_stock_seized)} tokens.")

        # 5. Liquidate Bag
        if remaining_loan > 0:
            inv = self.state.get("inventory", {})
            items_to_sell = list(inv.keys())
            liquidated_value = 0
            for item_key in items_to_sell:
                if remaining_loan <= 0:
                    break
                qty = inv.get(item_key, 0)
                if qty <= 0:
                    continue
                    
                try:
                    kind = ItemKind.MEGA_STONE if item_key.startswith("mega_stone_") else ItemKind(item_key)
                    sell_val = int(kind.price_for(self.current_difficulty) * 0.8)
                except ValueError:
                    sell_val = 0
                    
                if sell_val <= 0:
                    continue
                    
                sell_qty = min(qty, (remaining_loan + sell_val - 1) // sell_val)
                inv[item_key] -= sell_qty
                if inv[item_key] <= 0:
                    del inv[item_key]
                    
                take = min(remaining_loan, sell_qty * sell_val)
                surplus = (sell_qty * sell_val) - take
                remaining_loan -= take
                liquidated_value += take

                if surplus > 0:
                    self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - surplus
                    events.append(f"🏦 Repossession refund: {format_tokens(surplus)} excess item proceeds returned.")
                
            if liquidated_value > 0:
                events.append(f"🚨 REPOSSESSION: Liquidated inventory items for {format_tokens(liquidated_value)} tokens.")
            self.state["inventory"] = inv
        
        # 6. Forgive remaining debt
        if remaining_loan > 0:
            events.append(f"🏦 REPOSSESSION: {format_tokens(remaining_loan)} in unrecoverable loan debt was discharged.")
        else:
            events.append("🏦 REPOSSESSION: Outstanding loan debt was fully settled through asset liquidation.")
        self.state["bank_loan"] = 0
        self.state["loan_days_active"] = 0
        
        # 7. Distressed Companion(s)
        dex = self.state.get("dex", [])
        for d in dex:
            if d.get("status") != "evolved":
                m_state = d.get("mon_state", {})
                if "happiness" in m_state:
                    m_state["happiness"] = max(0, m_state["happiness"] - 50)
                    
        active = self.active_mon
        if active:
            active.happiness = max(0, active.happiness - 50)
            self.set_active_mon(active)

        events.append("💔 REPOSSESSION: All companions suffered a 50 happiness penalty due to bank seizure stress.")
