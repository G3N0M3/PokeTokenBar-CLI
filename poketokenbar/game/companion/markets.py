import copy
import datetime
import random
from typing import Dict, List, Optional, Tuple, Any

from poketokenbar.game.models import (
    CORPORATIONS, CorporateInfo, MARKET_HEADLINES,
    get_shareholder_rank, CORPORATE_TIER_PERKS
)
from poketokenbar.utils.formatting import format_tokens
from poketokenbar.game.economy.stock_market import StockMarketEngine
from poketokenbar.game.economy.black_market import BLACK_MARKET_POOL_100, unpack_trove, unpack_mystery_crate


class MarketsMixin:
    """Provides stock market trading, corporate perks, shareholder tiers, and black market illicit deals."""

    def has_perk(self, corp_key: str) -> bool:
        return self.state.get("investments", {}).get(corp_key.lower(), 0) > 0

    def get_corp_shares(self, corp_key: str) -> int:
        """Returns the number of shares owned for a corporation."""
        return self.state.get("investments", {}).get(corp_key.lower(), 0)

    def get_corp_rank(self, corp_key: str) -> Tuple[int, str]:
        """Returns (rank_id, rank_name) for a corporation based on owned shares."""
        shares = self.get_corp_shares(corp_key)
        return get_shareholder_rank(shares)

    def get_silph_multipliers(self) -> Tuple[float, float]:
        """Returns (speed_multiplier, token_multiplier) for Silph Co. shareholders."""
        rank, _ = self.get_corp_rank("silph")
        mult_map = {0: 1.0, 1: 1.10, 2: 1.15, 3: 1.20, 4: 1.25}
        m = mult_map.get(rank, 1.0)
        return m, m

    def get_devon_multiplier(self) -> float:
        """Returns price multiplier for Devon Corporation shareholders (shop items, eggs, black market)."""
        rank, _ = self.get_corp_rank("devon")
        disc_map = {0: 1.0, 1: 0.95, 2: 0.90, 3: 0.85, 4: 0.80}
        return disc_map.get(rank, 1.0)

    def get_devon_discount_pct(self) -> int:
        """Returns the integer percentage discount for Devon Corporation (e.g. 5, 10, 15, 20)."""
        return int(round((1.0 - self.get_devon_multiplier()) * 100))

    def get_aether_perks(self) -> Tuple[float, int]:
        """Returns (decay_shield_multiplier, daily_happiness_bonus) for Aether Foundation shareholders."""
        rank, _ = self.get_corp_rank("aether")
        perk_map = {
            0: (1.0, 0),
            1: (1.5, 3),
            2: (2.0, 5),
            3: (2.5, 8),
            4: (3.0, 12),
        }
        return perk_map.get(rank, (1.0, 0))

    def get_mauville_multiplier(self) -> float:
        """Returns payout bonus multiplier for Greater Mauville Holdings shareholders across all minigames."""
        rank, _ = self.get_corp_rank("mauville")
        mult_map = {0: 1.0, 1: 1.05, 2: 1.10, 3: 1.15, 4: 1.20}
        return mult_map.get(rank, 1.0)

    def get_macro_multiplier(self) -> float:
        """Returns token reward multiplier for Macro Cosmos shareholders across Gym boss raids and auto-battles."""
        rank, _ = self.get_corp_rank("macro")
        mult_map = {0: 1.0, 1: 1.10, 2: 1.20, 3: 1.30, 4: 1.40}
        return mult_map.get(rank, 1.0)

    def get_viridian_dividend_bonus(self) -> float:
        """Returns extra dividend yield bonus for Viridian Global Logistics shareholders."""
        rank, _ = self.get_corp_rank("viridian")
        bonus_map = {0: 0.0, 1: 0.005, 2: 0.010, 3: 0.015, 4: 0.020}
        return bonus_map.get(rank, 0.0)

    @staticmethod
    def _resolve_corp_key(code_or_name: str) -> Optional[str]:
        raw = code_or_name.lower().strip()
        for k, v in CORPORATIONS.items():
            if v.ticker.lower() == raw:
                return k
        if raw in CORPORATIONS:
            return raw
        aliases = {"devn": "devon", "athr": "aether", "slph": "silph", "vrdn": "viridian", "virg": "viridian"}
        return aliases.get(raw)

    def get_or_init_stock_market(self) -> dict:
        sm = self.state.setdefault("stock_market", {})
        default_prices = {
            "silph": 10_000_000,
            "devon": 10_000_000,
            "aether": 5_000_000,
            "mauville": 5_000_000,
            "macro": 20_000_000,
            "viridian": 25_000_000
        }
        sm.setdefault("prices", default_prices.copy())
        sm.setdefault("price_history", {k: [v] for k, v in sm["prices"].items()})
        sm.setdefault("cost_basis", {k: 0 for k in default_prices})
        sm.setdefault("latest_news", {
            "silph": "Silph Co. operations running steadily across Kanto.",
            "devon": "Devon Corp reports steady retail demand in Hoenn.",
            "aether": "Aether Foundation maintaining peaceful sanctuary conditions.",
            "mauville": "Greater Mauville Game Corner seeing standard foot traffic.",
            "macro": "Macro Cosmos power grid operating at nominal capacity.",
            "viridian": "Viridian Global Logistics freight operations proceeding on schedule."
        })
        sm.setdefault("daily_catalysts", {
            "expeditions_completed": 0,
            "shop_tokens_spent": 0,
            "casino_net_pnl": 0,
            "bosses_defeated": 0
        })
        sm.setdefault("market_headline", "📈 POKÉMON EXCHANGE: Indices opening with steady volume.")

        for k, v in default_prices.items():
            if k not in sm["prices"]:
                sm["prices"][k] = v
            if k not in sm["price_history"] or not sm["price_history"][k]:
                sm["price_history"][k] = [sm["prices"][k]]
            if k not in sm["cost_basis"]:
                sm["cost_basis"][k] = 0
            if k not in sm["latest_news"]:
                sm["latest_news"][k] = f"{CORPORATIONS[k].name} operating steadily."

        invs = self.state.get("investments", {})
        for k, shares in invs.items():
            if shares > 0 and sm["cost_basis"].get(k, 0) == 0:
                sm["cost_basis"][k] = shares * sm["prices"].get(k, default_prices.get(k, 10_000_000))

        StockMarketEngine.ensure_market_state(sm)
        return sm

    def _record_catalyst(self, key: str, amount: int):
        sm = self.get_or_init_stock_market()
        cats = sm.setdefault("daily_catalysts", {
            "expeditions_completed": 0,
            "shop_tokens_spent": 0,
            "casino_net_pnl": 0,
            "bosses_defeated": 0
        })
        cats[key] = cats.get(key, 0) + amount

    def _rollover_stock_market(self, days_to_apply: int, diff: int, current_streak: int, events: List[str]):
        sm = self.get_or_init_stock_market()
        previous_burn = self.state.get("tokens_burned_today", 0)

        # 1. Player In-Game Action Catalysts
        cats = sm.get("daily_catalysts", {})
        exp_count = cats.get("expeditions_completed", 0)
        shop_spent = cats.get("shop_tokens_spent", 0)
        casino_pnl = cats.get("casino_net_pnl", 0)
        boss_count = cats.get("bosses_defeated", 0)

        silph_boost = min(0.12, exp_count * 0.04)
        devon_boost = min(0.12, (shop_spent // 5_000_000) * 0.03)
        mauv_boost = 0.05 if casino_pnl < 0 else (-0.04 if casino_pnl > 0 else 0.0)
        macro_boost = min(0.18, boss_count * 0.06)

        dex = self.state.get("dex", [])
        active = self.active_mon
        all_haps = []
        if active:
            all_haps.append(active.happiness)
        for d in dex:
            m_st = d.get("mon_state", {})
            if "happiness" in m_st:
                all_haps.append(m_st["happiness"])
        avg_hap = (sum(all_haps) / len(all_haps)) if all_haps else 100.0
        has_shiny = any(d.get("is_shiny") for d in dex) or (active and active.is_shiny)
        aether_boost = 0.0
        if avg_hap >= 90.0:
            aether_boost += 0.04
        if has_shiny:
            aether_boost += 0.04

        corp_boosts = {
            "silph": silph_boost,
            "devon": devon_boost,
            "aether": aether_boost,
            "mauville": mauv_boost,
            "macro": macro_boost,
            "viridian": min(0.12, (previous_burn // 500_000) * 0.03)
        }

        # 2. Pattern Progression, Price Updates, and Forward News Hints
        price_changes = StockMarketEngine.step_day(
            sm_data=sm,
            days_to_apply=days_to_apply,
            streak=current_streak,
            burn_tokens=previous_burn,
            catalysts=cats,
            corp_boosts=corp_boosts
        )

        # 3. Top Market Headline
        avg_change = sum(price_changes.values()) / len(price_changes) if price_changes else 0.0
        if avg_change > 0.03:
            sentiment = "bullish"
        elif avg_change < -0.01:
            sentiment = "bearish"
        else:
            sentiment = "steady"
        sm["market_headline"] = random.choice(MARKET_HEADLINES.get(sentiment, ["📊 MARKET BALANCED: Indices hold steady across sectors."]))

        # 6. Reset Catalysts for the new day
        sm["daily_catalysts"] = {
            "expeditions_completed": 0,
            "shop_tokens_spent": 0,
            "casino_net_pnl": 0,
            "bosses_defeated": 0
        }

        # 7. Process Dynamic Corporate Stock Dividends
        investments = self.state.get("investments", {})
        streak_bonus = min(0.05, current_streak * 0.002)
        total_dividends = 0
        for c_key, shares in investments.items():
            if shares > 0 and c_key in CORPORATIONS:
                corp = CORPORATIONS[c_key]
                dyn_price = sm["prices"].get(c_key, corp.share_price)
                eff_rate = corp.base_dividend + streak_bonus
                if c_key == "viridian":
                    eff_rate += self.get_viridian_dividend_bonus()
                div_per_day = int(shares * dyn_price * eff_rate)
                total_dividends += div_per_day * days_to_apply

        if total_dividends > 0:
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - total_dividends
            events.append(f"📈 Corporate Dividends: Earned {format_tokens(total_dividends)} tokens from your stock portfolio! (🔥 {current_streak}d streak bonus applied)")

        events.append(f"📰 Market Tick: Pokémon Stock Exchange updated! {sm['market_headline']}")

    def get_stock_details(self, corp_code: str) -> Optional[dict]:
        key = self._resolve_corp_key(corp_code)
        if not key or key not in CORPORATIONS:
            return None
        corp = CORPORATIONS[key]
        sm = self.get_or_init_stock_market()
        current_price = sm["prices"].get(key, corp.share_price)
        history = sm["price_history"].get(key, [current_price])
        prev_price = history[-2] if len(history) >= 2 else current_price
        change_pct = ((current_price - prev_price) / prev_price * 100.0) if prev_price > 0 else 0.0

        owned = self.state.get("investments", {}).get(key, 0)
        cost_basis = sm["cost_basis"].get(key, 0)
        avg_cost = (cost_basis // owned) if owned > 0 else 0
        market_val = owned * current_price
        liq_val = int(market_val * 0.90)
        unrealized_pnl = (liq_val - cost_basis) if owned > 0 else 0
        unrealized_pnl_pct = ((liq_val - cost_basis) / cost_basis * 100.0) if cost_basis > 0 else 0.0

        latest_news = sm["latest_news"].get(key, "")
        streak = self.state.get("streak_days", 1)
        streak_bonus = min(0.05, streak * 0.002)
        eff_rate = corp.base_dividend + streak_bonus
        if key == "viridian":
            eff_rate += self.get_viridian_dividend_bonus()
        daily_div = int(owned * current_price * eff_rate)
        rank, tier_name = get_shareholder_rank(owned)
        tier_perk_desc = CORPORATE_TIER_PERKS.get(key, {}).get(rank, corp.perk_desc)

        return {
            "key": key,
            "corp": corp,
            "current_price": current_price,
            "prev_price": prev_price,
            "change_pct": change_pct,
            "price_history": history,
            "owned": owned,
            "cost_basis": cost_basis,
            "avg_cost": avg_cost,
            "market_val": market_val,
            "liq_val": liq_val,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "latest_news": latest_news,
            "eff_rate": eff_rate,
            "daily_div": daily_div,
            "rank": rank,
            "tier_name": tier_name,
            "tier_perk_desc": tier_perk_desc,
        }

    def invest_corporate(self, corp_code: str, shares_str: str) -> Tuple[bool, str]:
        key = self._resolve_corp_key(corp_code)
        if not key:
            tickers = ", ".join(f"'{v.ticker}' ({v.name})" for v in CORPORATIONS.values())
            return False, f"Unknown stock code '{corp_code}'! Available codes: {tickers}."

        corp = CORPORATIONS[key]
        sm = self.get_or_init_stock_market()
        current_price = sm["prices"].get(key, corp.share_price)

        clean_str = shares_str.lower().strip()
        if clean_str == "all":
            shares = self.available_tokens // current_price
            if shares <= 0:
                return False, f"Not enough tokens to buy 1 share of {corp.ticker} ({corp.name}) ({format_tokens(current_price)} tokens)!"
        else:
            try:
                shares = int(clean_str)
            except ValueError:
                return False, f"Invalid number of shares. Example: 'invest {corp.ticker} 2' or 'buy 2'."

        if shares <= 0:
            return False, "Shares must be at least 1."

        cost = shares * current_price
        if cost > self.available_tokens:
            return False, f"Not enough tokens! Buying {shares} share(s) of {corp.ticker} costs {format_tokens(cost)} (You have {format_tokens(self.available_tokens)})."

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
        invs = self.state.setdefault("investments", {"silph": 0, "devon": 0, "aether": 0, "mauville": 0, "macro": 0, "viridian": 0})
        invs[key] = invs.get(key, 0) + shares
        self.state["investments"] = invs

        # Update cost basis
        sm["cost_basis"][key] = sm["cost_basis"].get(key, 0) + cost

        # Check for Team Rocket story unlock
        self.check_rocket_story_unlock()

        self.save()
        return True, f"📈 Invested in {shares} share(s) of {corp.ticker} ({corp.name}) for {format_tokens(cost)} tokens ({format_tokens(current_price)}/sh)! ({corp.perk_name}: {corp.perk_desc} is now ACTIVE!)"

    def divest_corporate(self, corp_code: str, shares_str: str) -> Tuple[bool, str]:
        key = self._resolve_corp_key(corp_code)
        if not key:
            tickers = ", ".join(f"'{v.ticker}'" for v in CORPORATIONS.values())
            return False, f"Unknown stock code '{corp_code}'! Available codes: {tickers}."

        corp = CORPORATIONS[key]
        sm = self.get_or_init_stock_market()
        current_price = sm["prices"].get(key, corp.share_price)

        invs = self.state.setdefault("investments", {"silph": 0, "devon": 0, "aether": 0, "mauville": 0, "macro": 0, "viridian": 0})
        owned = invs.get(key, 0)
        if owned <= 0:
            return False, f"You don't own any shares of {corp.ticker} ({corp.name})!"

        clean_str = shares_str.lower().strip()
        if clean_str == "all":
            shares = owned
        else:
            try:
                shares = int(clean_str)
            except ValueError:
                return False, f"Invalid number of shares. Example: 'divest {corp.ticker} 1' or 'sell 1'."

        if shares <= 0 or shares > owned:
            return False, f"Invalid quantity! You own {owned} share(s) of {corp.ticker}."

        # 10% liquidation fee / market spread
        gross_value = shares * current_price
        payout = int(gross_value * 0.90)

        # Realized P&L calculation based on weighted-average cost
        old_cost_basis = sm["cost_basis"].get(key, 0)
        avg_cost = (old_cost_basis // owned) if owned > 0 else current_price
        cost_of_sold = int(shares * avg_cost)
        realized_pnl = payout - cost_of_sold

        remaining_shares = owned - shares
        if remaining_shares == 0:
            sm["cost_basis"][key] = 0
        else:
            sm["cost_basis"][key] = max(0, old_cost_basis - cost_of_sold)

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - payout
        invs[key] = remaining_shares
        self.state["investments"] = invs
        self.save()

        pnl_sign = "+" if realized_pnl >= 0 else ""
        pnl_str = f" | P&L: {pnl_sign}{format_tokens(realized_pnl)}"
        return True, f"📉 Sold {shares} share(s) of {corp.ticker} ({corp.name}) for {format_tokens(payout)} tokens (10% spread applied{pnl_str})."

    def get_or_init_black_market(self, force_open: bool = False) -> dict:
        if self.state.get("permanent_black_market", False):
            force_open = True
        bm = self.state.get("black_market")
        today_str = datetime.date.today().isoformat()
        needs_reroll = (
            bm is None
            or not bm.get("deals")
            or bm.get("deals_date") != today_str
            or len(bm.get("deals", [])) != 7
        )

        if needs_reroll or force_open:
            inv = self.state.get("inventory", {})
            valid_pool = [
                d for d in BLACK_MARKET_POOL_100
                if not (d.get("type") == "mega_stone" and inv.get(f"mega_stone_{d.get('stone_id')}", 0) >= 1)
            ]
            if len(valid_pool) < 7:
                valid_pool = BLACK_MARKET_POOL_100
            selected = random.sample(valid_pool, 7)
            deals = []
            for idx, d in enumerate(selected, 1):
                item = copy.deepcopy(d)
                item["id"] = idx
                deals.append(item)

            if not bm:
                bm = {
                    "is_open": force_open,
                    "natural_open": force_open,
                    "duration_days": 1,
                    "deals_date": today_str,
                    "deals": deals
                }
            else:
                if force_open:
                    bm["is_open"] = True
                    bm["natural_open"] = True
                    bm["duration_days"] = 1
                if needs_reroll:
                    bm["deals_date"] = today_str
                    bm["deals"] = deals

            self.state["black_market"] = bm
            self.save()
        if self.state.get("permanent_black_market", False):
            bm["is_open"] = True
            bm["natural_open"] = True

        # Ensure any deals offering already-owned Mega Stones are marked out of stock
        inv = self.state.get("inventory", {})
        for d in bm.get("deals", []):
            if d.get("type") == "mega_stone":
                s_id = d.get("stone_id")
                if inv.get(f"mega_stone_{s_id}", 0) >= 1:
                    d["stock"] = 0

        return bm

    def buy_black_market_deal(self, deal_id_str: str, qty: int = 1, confirm: bool = False) -> Tuple[bool, str]:
        bm = self.get_or_init_black_market()
        if not bm.get("is_open"):
            return False, "The Rocket Syndicate backroom is currently locked! Expected return on random days (5% chance)."

        try:
            deal_id = int(str(deal_id_str).strip())
        except ValueError:
            return False, "Invalid deal ID! Example: 'buy 1' or 'buy 2 1'."

        deals = bm.get("deals", [])
        deal = next((d for d in deals if d.get("id") == deal_id), None)
        if not deal:
            return False, f"Black Market Deal #{deal_id} not found."

        deal_type = deal.get("type", "item")
        inv = self.state.setdefault("inventory", {})

        if deal_type == "mega_stone":
            s_id = deal["stone_id"]
            k = f"mega_stone_{s_id}"
            if inv.get(k, 0) >= 1:
                return False, f"You already own {deal['name']}! (Only 1 per Mega Stone permitted)"
            if qty > 1:
                return False, f"You can only purchase 1 {deal['name']}!"

        if deal.get("stock", 0) < qty:
            return False, f"Not enough stock! Deal #{deal_id} only has {deal.get('stock', 0)} in stock."

        price = deal["price"]
        price = int(price * self.get_devon_multiplier())

        total_cost = price * qty
        if total_cost > self.available_tokens:
            return False, f"Not enough tokens! Requires {format_tokens(total_cost)} (You have {format_tokens(self.available_tokens)})."

        if confirm:
            prompt = f"🕶️ Buy {qty}x {deal['name']} for {format_tokens(total_cost)} tokens? Type 'confirm' (or 'y')"
            if len(prompt) > 72:
                prompt = f"🕶️ Buy {qty}x [{deal_id}] for {format_tokens(total_cost)} tokens? Type 'y'"
            if len(prompt) > 72:
                prompt = prompt[:69] + "..."
            return True, prompt

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + total_cost
        deal["stock"] -= qty

        # Progress active Rocket Operation #5 ONLY if status is active
        ops = self.state.get("rocket_ops", {})
        if ops.get("op_5", {}).get("status") == "active" and not ops.get("op_5", {}).get("claimed", False):
            ops["op_5"]["black_market_trades"] = ops["op_5"].get("black_market_trades", 0) + qty
            if ops["op_5"]["black_market_trades"] >= 1 and len(self.state.get("expeditions", [])) >= 2:
                ops["op_5"]["objective_done"] = True

        if deal_type == "item":
            k = deal["item_key"]
            item_qty = deal.get("qty", 1) * qty
            inv[k] = inv.get(k, 0) + item_qty
            msg = f"Purchased {qty}x {deal['name']} for {format_tokens(total_cost)} tokens! Added to your Bag."
        elif deal_type == "egg":
            tier = deal["egg_tier"]
            if not self.state.get("egg_tier"):
                self.state["egg_tier"] = tier
                self.state["egg_usage"] = 0
                msg = f"Purchased {deal['name']} for {format_tokens(total_cost)} tokens! Now incubating your fresh {tier.replace('_', ' ').title()} Egg."
            else:
                pending = self.state.setdefault("pending_eggs", [])
                pending.append(tier)
                msg = f"Purchased {deal['name']} for {format_tokens(total_cost)} tokens! Added to your Egg Reserves."
        elif deal_type == "mega_stone":
            s_id = deal["stone_id"]
            k = f"mega_stone_{s_id}"
            inv[k] = 1
            msg = f"Purchased {deal['name']} for {format_tokens(total_cost)} tokens! Unlocked in Tab [8] Mega Evolution."
        elif deal_type.startswith("trove_") or deal_type == "map_pack":
            items_to_add, reveal_names = unpack_trove(deal, qty)
            for k, v in items_to_add.items():
                inv[k] = inv.get(k, 0) + v
            reveals_str = ", ".join(reveal_names)
            msg = f"Purchased {deal['name']} for {format_tokens(total_cost)} tokens! Unpacked: {reveals_str}!"
        elif deal_type == "mystery_crate":
            last_desc = ""
            for _ in range(qty):
                c_items, c_tokens, c_egg, last_desc = unpack_mystery_crate(deal["crate_id"], inv=inv)
                for k, v in c_items.items():
                    if k.startswith("mega_stone_"):
                        if inv.get(k, 0) == 0:
                            inv[k] = 1
                        else:
                            # Safeguard against duplicate: convert to 10.0M tokens
                            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - 10_000_000
                    else:
                        inv[k] = inv.get(k, 0) + v
                if c_tokens > 0:
                    self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - c_tokens
                if c_egg:
                    if not self.state.get("egg_tier"):
                        self.state["egg_tier"] = c_egg
                        self.state["egg_usage"] = 0
                    else:
                        self.state.setdefault("pending_eggs", []).append(c_egg)
            msg = f"Purchased {deal['name']} for {format_tokens(total_cost)} tokens! {last_desc}"
        else:
            msg = f"Purchased {deal['name']}!"

        self._record_catalyst("shop_tokens_spent", total_cost)
        self.save()
        return True, msg

    def get_daily_grunt_bribe(self) -> int:
        bribe = self.state.get("daily_grunt_bribe")
        if not bribe or bribe not in [1_000_000, 2_000_000, 3_000_000, 4_000_000, 5_000_000]:
            bribe = random.choice([1_000_000, 2_000_000, 3_000_000, 4_000_000, 5_000_000])
            self.state["daily_grunt_bribe"] = bribe
            self.save()
        return bribe

    def bribe_grunt_for_black_market(self) -> Tuple[bool, str]:
        if self.state.get("permanent_black_market", False):
            bm = self.get_or_init_black_market(force_open=True)
            bm["is_open"] = True
            bm["natural_open"] = True
            self.state["black_market"] = bm
            self.save()
            return True, "📯 Syndicate Black Pass recognized! The Grunt snaps to attention and lets you through free of charge!"

        bribe = self.get_daily_grunt_bribe()
        if self.available_tokens < bribe:
            return False, f"You don't have enough tokens to bribe the Grunt! (Required: {format_tokens(bribe)}, Available: {format_tokens(self.available_tokens)})"

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + bribe
        bm = self.get_or_init_black_market()
        bm["is_open"] = True
        # NOTE: Backroom session opened. natural_open remains False for Mart alley.
        self.state["black_market"] = bm
        self._record_catalyst("casino_tokens_spent", bribe)
        self.save()
        return True, f"💰 You paid {format_tokens(bribe)} tokens to the Grunt! He clicks the secret switch behind the poster. The backroom opens!"
