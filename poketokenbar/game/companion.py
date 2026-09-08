import random
import datetime
from typing import Dict, List, Optional, Tuple, Any, Union

from poketokenbar.game.models import (
    MonState, DexEntry, Rarity, PokemonNature, PokemonBalance, ItemKind, DifficultyMode,
    CORPORATIONS, CorporateInfo, CORPORATE_LORE_EVENTS, MARKET_HEADLINES
)
from poketokenbar.game.pokeapi import PokeAPIClient
from poketokenbar.game.storage import StorageManager
from poketokenbar.utils.formatting import format_tokens, parse_tokens

from poketokenbar.game.poker import TexasHoldemEngine
from poketokenbar.game.slots import SlotMachineEngine
from poketokenbar.game.blackjack import BlackjackEngine
from poketokenbar.game.gacha import GachaEngine, GACHA_COST_SINGLE, GACHA_COST_MULTI

# Expanded pool of starters, base species, and all legendary/mythical Pokémon (Gens 1-7)
BASE_SPECIES_STARTERS = [
    # === LEGENDARY & MYTHICAL POKÉMON (Generations 1 - 7) ===
    # Gen 1
    (144, "Articuno", 3, True), (145, "Zapdos", 3, True), (146, "Moltres", 3, True),
    (150, "Mewtwo", 3, True), (151, "Mew", 45, True),
    # Gen 2
    (243, "Raikou", 3, True), (244, "Entei", 3, True), (245, "Suicune", 3, True),
    (249, "Lugia", 3, True), (250, "Ho-Oh", 3, True), (251, "Celebi", 45, True),
    # Gen 3
    (377, "Regirock", 3, True), (378, "Regice", 3, True), (379, "Registeel", 3, True),
    (380, "Latias", 3, True), (381, "Latios", 3, True), (382, "Kyogre", 3, True),
    (383, "Groudon", 3, True), (384, "Rayquaza", 3, True), (385, "Jirachi", 3, True),
    (386, "Deoxys", 3, True),
    # Gen 4
    (480, "Uxie", 3, True), (481, "Mesprit", 3, True), (482, "Azelf", 3, True),
    (483, "Dialga", 3, True), (484, "Palkia", 3, True), (485, "Heatran", 3, True),
    (486, "Regigigas", 3, True), (487, "Giratina", 3, True), (488, "Cresselia", 3, True),
    (489, "Phione", 30, True), (490, "Manaphy", 3, True), (491, "Darkrai", 3, True),
    (492, "Shaymin", 45, True), (493, "Arceus", 3, True),
    # Gen 5
    (494, "Victini", 3, True), (638, "Cobalion", 3, True), (639, "Terrakion", 3, True),
    (640, "Virizion", 3, True), (641, "Tornadus", 3, True), (642, "Thundurus", 3, True),
    (643, "Reshiram", 3, True), (644, "Zekrom", 3, True), (645, "Landorus", 3, True),
    (646, "Kyurem", 3, True), (647, "Keldeo", 3, True), (648, "Meloetta", 3, True),
    (649, "Genesect", 3, True),
    # Gen 6
    (716, "Xerneas", 45, True), (717, "Yveltal", 45, True), (718, "Zygarde", 3, True),
    (719, "Diancie", 3, True), (720, "Hoopa", 3, True), (721, "Volcanion", 3, True),
    # Gen 7
    (785, "Tapu Koko", 3, True), (786, "Tapu Lele", 3, True),
    (787, "Tapu Bulu", 3, True), (788, "Tapu Fini", 3, True),
    (789, "Cosmog", 45, True), (793, "Nihilego", 45, True),
    (794, "Buzzwole", 45, True), (795, "Pheromosa", 45, True),
    (796, "Xurkitree", 45, True), (797, "Celesteela", 45, True),
    (798, "Kartana", 255, True), (799, "Guzzlord", 45, True),
    (800, "Necrozma", 3, True), (801, "Magearna", 3, True),
    (802, "Marshadow", 3, True), (804, "Poipole", 45, True),
    (805, "Stakataka", 30, True), (806, "Blacephalon", 30, True),
    (807, "Zeraora", 3, True),

    # === STARTERS (Gens 1 - 7) ===
    (1, "Bulbasaur", 45, False), (4, "Charmander", 45, False), (7, "Squirtle", 45, False),
    (152, "Chikorita", 45, False), (155, "Cyndaquil", 45, False), (158, "Totodile", 45, False),
    (252, "Treecko", 45, False), (255, "Torchic", 45, False), (258, "Mudkip", 45, False),
    (387, "Turtwig", 45, False), (390, "Chimchar", 45, False), (393, "Piplup", 45, False),
    (495, "Snivy", 45, False), (498, "Tepig", 45, False), (501, "Oshawott", 45, False),
    (650, "Chespin", 45, False), (653, "Fennekin", 45, False), (656, "Froakie", 45, False),
    (722, "Rowlet", 45, False), (725, "Litten", 45, False), (728, "Popplio", 45, False),

    # === PSEUDO-LEGENDARIES & RARE / FOSSIL BASE SPECIES ===
    (147, "Dratini", 45, False), (246, "Larvitar", 45, False), (371, "Bagon", 45, False),
    (374, "Beldum", 3, False), (443, "Gible", 45, False), (633, "Deino", 45, False),
    (704, "Goomy", 45, False), (782, "Jangmo-o", 45, False),
    (131, "Lapras", 45, False), (143, "Snorlax", 25, False), (142, "Aerodactyl", 45, False),
    (138, "Omanyte", 45, False), (140, "Kabuto", 45, False), (175, "Togepi", 190, False),
    (447, "Riolu", 75, False), (570, "Zorua", 75, False), (636, "Larvesta", 45, False),
    (610, "Axew", 75, False), (679, "Honedge", 120, False), (778, "Mimikyu", 45, False),
    (359, "Absol", 30, False), (479, "Rotom", 45, False), (442, "Spiritomb", 100, False),
    (227, "Skarmory", 25, False), (214, "Heracross", 45, False), (123, "Scyther", 45, False),
    (127, "Pinsir", 45, False), (133, "Eevee", 45, False), (137, "Porygon", 45, False),

    # === UNCOMMON & COMMON BASE SPECIES ===
    (10, "Caterpie", 255, False), (13, "Weedle", 255, False), (16, "Pidgey", 255, False),
    (19, "Rattata", 255, False), (25, "Pikachu", 190, False), (27, "Sandshrew", 255, False),
    (37, "Vulpix", 190, False), (41, "Zubat", 255, False), (43, "Oddish", 255, False),
    (54, "Psyduck", 190, False), (58, "Growlithe", 190, False), (60, "Poliwag", 255, False),
    (63, "Abra", 200, False), (66, "Machop", 180, False), (69, "Bellsprout", 255, False),
    (74, "Geodude", 255, False), (77, "Ponyta", 190, False), (79, "Slowpoke", 190, False),
    (81, "Magnemite", 190, False), (92, "Gastly", 190, False), (95, "Onix", 45, False),
    (129, "Magikarp", 255, False), (172, "Pichu", 190, False), (179, "Mareep", 235, False),
    (183, "Marill", 190, False), (194, "Wooper", 255, False), (228, "Houndour", 120, False),
    (231, "Phanpy", 120, False), (280, "Ralts", 235, False), (285, "Shroomish", 255, False),
    (287, "Slakoth", 255, False), (304, "Aron", 180, False), (307, "Meditite", 180, False),
    (309, "Electrike", 120, False), (328, "Trapinch", 255, False), (333, "Swablu", 255, False),
    (349, "Feebas", 255, False), (403, "Shinx", 235, False), (427, "Buneary", 190, False),
    (453, "Croagunk", 140, False), (459, "Snover", 120, False), (540, "Sewaddle", 255, False),
    (543, "Venipede", 255, False), (551, "Sandile", 180, False), (559, "Scraggy", 180, False),
    (607, "Litwick", 190, False), (624, "Pawniard", 120, False), (661, "Fletchling", 255, False),
    (674, "Pancham", 190, False), (686, "Inkay", 190, False), (736, "Grubbin", 255, False),
    (744, "Rockruff", 190, False), (747, "Mareanie", 190, False), (759, "Stufful", 140, False)
]

class CompanionEngine:
    """Manages active Pokémon companion, hatching, evolution, Pokédex, and inventory."""

    def __init__(self):
        self.api = PokeAPIClient()
        self.state = StorageManager.load_state()
        
        # Migrate Earth Badge from crown to globe
        if "gym_badges" in self.state:
            self.state["gym_badges"] = [b.replace("👑 Earth Badge", "🌍 Earth Badge") for b in self.state["gym_badges"]]
        if "active_boss" in self.state and self.state["active_boss"] and "badge" in self.state["active_boss"]:
            self.state["active_boss"]["badge"] = self.state["active_boss"]["badge"].replace("👑 Earth Badge", "🌍 Earth Badge")
            
        self.poker = TexasHoldemEngine()
        self.blackjack = BlackjackEngine()
        self.slots = SlotMachineEngine()
        
        import json
        self._last_saved_state_str = json.dumps(self.state, sort_keys=True)

        if "install_date" not in self.state:
            dex = self.state.get("dex", [])
            caught_dates = [d.get("caught_at", "")[:10] for d in dex if d.get("caught_at")]
            self.state["install_date"] = min(caught_dates) if caught_dates else datetime.datetime.now().strftime("%Y-%m-%d")
            self.save()

    def save(self):
        import json
        state_str = json.dumps(self.state, sort_keys=True)
        if state_str != self._last_saved_state_str:
            StorageManager.save_state(self.state)
            self._last_saved_state_str = state_str

    def reset_game_state(self) -> Tuple[bool, str]:
        """Resets all game progress, inventory, companions, and Pokédex entries."""
        self.state = StorageManager.default_state()
        self.save()
        return True, "✨ Game progress has been completely reset! Started fresh."

    @property
    def available_tokens(self) -> int:
        used = self.state.get("used_since_install", 0)
        spent = self.state.get("spent_tokens", 0)
        return max(0, used - spent)

    @property
    def active_mon(self) -> Optional[MonState]:
        return StorageManager.dict_to_mon(self.state.get("active_mon"))

    def set_active_mon(self, mon: Optional[MonState]):
        if mon:
            self.state["happiness"] = mon.happiness
        self.state["active_mon"] = StorageManager.mon_to_dict(mon) if mon else None
        self.save()

    @property
    def current_difficulty(self) -> DifficultyMode:
        diff_str = self.state.get("settings", {}).get("difficulty", "medium")
        try:
            return DifficultyMode(diff_str)
        except Exception:
            return DifficultyMode.MEDIUM

    def has_perk(self, corp_key: str) -> bool:
        return self.state.get("investments", {}).get(corp_key.lower(), 0) > 0

    def _calculate_streak_from_active_days(self, active_days: List[str], today_str: str) -> int:
        if not active_days:
            return 1

        days_set = set(active_days)
        try:
            today_dt = datetime.datetime.strptime(today_str, "%Y-%m-%d")
        except Exception:
            return 1
        
        # Check if today has entries or if we start counting back from yesterday
        if today_str in days_set:
            curr_dt = today_dt
        else:
            curr_dt = today_dt - datetime.timedelta(days=1)
            if curr_dt.strftime("%Y-%m-%d") not in days_set:
                return 1

        streak = 0
        while True:
            d_str = curr_dt.strftime("%Y-%m-%d")
            if d_str in days_set:
                streak += 1
                curr_dt -= datetime.timedelta(days=1)
            else:
                break
        return max(1, streak)

    def process_usage(self, new_total_tokens: int, active_days: Optional[List[str]] = None) -> List[str]:
        """Call this with cumulative tokens used since install."""
        events = []
        old_used = self.state.get("used_since_install", 0)

        if not self.state.get("install_baseline_set", False):
            self.state["used_since_install"] = new_total_tokens
            self.state["install_baseline_set"] = True
            if not self.state.get("install_date"):
                self.state["install_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
            self.save()
            self._update_streak_and_quests(0, events, active_days)
            return events

        # Handle case where logs were cleared/rotated (total_tokens dropped)
        # Instead of subtracting from spent_tokens, we accumulate the missing tokens.
        indexed_tokens = self.state.get("indexed_tokens", old_used)
        archived_tokens = self.state.get("archived_tokens", 0)
        
        if new_total_tokens < indexed_tokens:
            diff = indexed_tokens - new_total_tokens
            archived_tokens += diff
            self.state["archived_tokens"] = archived_tokens
            
        self.state["indexed_tokens"] = new_total_tokens
        
        # Calculate true lifetime total tokens
        true_total_tokens = new_total_tokens + archived_tokens
        
        # Now we process delta based on true_total_tokens
        old_used = self.state.get("used_since_install", 0)

        # Always evaluate day rollover, streak, and daily quests first
        delta = max(0, true_total_tokens - old_used)
        self._update_streak_and_quests(delta, events, active_days)

        if delta == 0:
            return events

        self.state["used_since_install"] = true_total_tokens
        active = self.active_mon
        diff = self.current_difficulty

        if active:
            used_total = self.state.get("used_since_install", 0)
            last_decay = self.state.get("last_happiness_decay_token", used_total)
            if active.held_item in ["leftovers", "soothe_bell"]:
                decay_rate = 999_999_999_999
            else:
                base_decay = 800_000 if active.held_item == "choice_scarf" else 1_000_000
                decay_rate = base_decay * 2 if self.has_perk("aether") else base_decay
            decay_amount = (used_total - last_decay) // decay_rate
            
            if decay_amount > 0:
                old_hap = active.happiness
                active.happiness = max(0, active.happiness - decay_amount)
                self.set_active_mon(active)
                self.state["last_happiness_decay_token"] = last_decay + (decay_amount * decay_rate)
                
                if old_hap >= 50 and active.happiness < 50:
                    events.append(f"⚠️ {self.api.get_species_name(active.current_id)} is hungry (Happiness: {active.happiness}%)! Feed an Oran Berry 🫐 from the Shop!")
                    
            happiness = active.happiness
        else:
            happiness = 100

        if happiness == 0:
            effective_xp = 0
            xp_multiplier = 0.0
        else:
            # Happiness XP multiplier (+20% bonus if 100% happy)
            xp_multiplier = 1.20 if happiness >= 100 else 1.0
            if active and active.is_mega:
                xp_multiplier += 0.50  # Mega Evolution grants +50% XP boost!
            if active and active.held_item == "lucky_egg":
                xp_multiplier += 0.20  # Lucky Egg grants +20% XP boost!
            if active and active.held_item == "life_orb":
                xp_multiplier += 0.10  # Life Orb grants +10% XP boost!
            effective_xp = int(delta * xp_multiplier)

        if happiness > 0:
            # Update boss battle damage if active
            boss_events = self._update_boss_battle(delta)
            events.extend(boss_events)

        # Update Pokédex expeditions progress (benefits from Happiness & Mega multipliers!)
        self._update_expeditions(effective_xp, events)

        if happiness > 0:
            # Check mini-trainer auto-battles
            self._check_trainer_battle(delta, events)

        if active is None:
            egg_tier = self.state.get("egg_tier")
            if egg_tier is None:
                # Active mon is None, but no egg either (should be impossible in normal flow but fail gracefully)
                return events

            egg_usage = self.state.get("egg_usage", 0) + effective_xp
            self.state["egg_usage"] = egg_usage

            threshold = PokemonBalance.EGG_HATCH_THRESHOLD
            if egg_usage >= threshold:
                mon, hatch_events = self.hatch_egg(initial_xp=egg_usage - threshold)
                events.extend(hatch_events)
                evo_events = self._check_growth(mon)
                events.extend(evo_events)
            self.save()
        else:
            active.used_at_stage += effective_xp

            # Check evolution / graduation threshold
            self.set_active_mon(active)
            evo_events = self._check_growth(active)
            events.extend(evo_events)

            # Check Exp. Share held item
            if active.held_item == "exp_share" and effective_xp > 0:
                shared_xp = int(effective_xp * 0.25)
                dex = self.state.get("dex", [])
                for d in dex:
                    if d.get("status") not in ["graduated", "evolved"]:
                        m_data = d.get("mon_state")
                        if m_data:
                            sub_mon = StorageManager.dict_to_mon(m_data)
                            if sub_mon and sub_mon.base_id != active.base_id and sub_mon.stage_index < len(sub_mon.path_ids) - 1:
                                sub_mon.used_at_stage += shared_xp
                                sub_evos = self._check_growth(sub_mon)
                                events.extend(sub_evos)
                                d["mon_state"] = StorageManager.mon_to_dict(sub_mon)

        # Check achievements
        ach_events = self._check_achievements()
        events.extend(ach_events)

        if events:
            alerts = self.state.get("unread_alerts", [])
            for e in events:
                if e not in alerts:  # basic deduplication for safety
                    alerts.append(e)
            self.state["unread_alerts"] = alerts
            self.save()

        return events

    def _update_streak_and_quests(self, delta: int, events: List[str], active_days: Optional[List[str]] = None):
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        last_date = self.state.get("last_active_date", "")
        active = self.active_mon

        # Natural streak progression based on last_date
        current_streak = self.state.get("streak_days", 1)
        if last_date and last_date != today_str:
            try:
                last_dt = datetime.datetime.strptime(last_date, "%Y-%m-%d")
                today_dt = datetime.datetime.strptime(today_str, "%Y-%m-%d")
                diff = (today_dt - last_dt).days
                if diff == 1:
                    current_streak += 1
                elif diff > 1:
                    current_streak = 1
            except Exception:
                current_streak = 1
        
        # Retroactive log check
        if active_days:
            log_streak = self._calculate_streak_from_active_days(active_days, today_str)
            current_streak = max(current_streak, log_streak)
            
        self.state["streak_days"] = current_streak

        if last_date != today_str:
            if last_date:
                try:
                    last_dt = datetime.datetime.strptime(last_date, "%Y-%m-%d")
                    today_dt = datetime.datetime.strptime(today_str, "%Y-%m-%d")
                    diff = (today_dt - last_dt).days
                    
                    bank_balance = self.state.get("bank_balance", 0)
                    bank_loan = self.state.get("bank_loan", 0)
                    
                    if diff > 0:
                        days_to_apply = min(diff, 100)
                        
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
                                    events.append(f"🏦 Certificate of Deposit #{cd['id']} ({cd['term_days']}d) has MATURED! Total Value: {format_tokens(cd['current_value'])} tokens (Type 'cd claim {cd['id']}')")

                        # Process Corporate Stock Market Rollover & Dynamic Dividends
                        self._rollover_stock_market(days_to_apply, diff, current_streak, events)

                        # Process Black Market rotation
                        bm = self.state.get("black_market")
                        if bm:
                            if bm.get("is_open"):
                                dur = bm.get("duration_days", 1) - days_to_apply
                                if dur <= 0:
                                    bm["is_open"] = False
                                    bm["days_until_next"] = 3
                                    events.append("🕵️ The Wandering Merchant packed up and left town.")
                                else:
                                    bm["duration_days"] = dur
                            else:
                                until = bm.get("days_until_next", 3) - days_to_apply
                                if until <= 0:
                                    self.get_or_init_black_market(force_open=True)
                                    events.append("🕵️ A Wandering Merchant has arrived in town with Black Market contraband! (Type 'black' in Shop)")
                                else:
                                    bm["days_until_next"] = until

                        if bank_loan > 0:
                            new_loan = bank_loan
                            for _ in range(days_to_apply):
                                new_loan = int(new_loan * 1.10)
                            events.append(f"🏦 Your Token Bank loan accumulated {format_tokens(new_loan - bank_loan)} tokens in interest!")
                            self.state["bank_loan"] = new_loan
                            
                            loan_days = self.state.get("loan_days_active", 0) + days_to_apply
                            self.state["loan_days_active"] = loan_days
                            
                            if loan_days >= 7:
                                remaining_loan = new_loan
                                
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
                                
                                # 3. Liquidate Bag
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
                                            
                                        remaining_loan -= (sell_qty * sell_val)
                                        liquidated_value += (sell_qty * sell_val)
                                        
                                    if liquidated_value > 0:
                                        events.append(f"🚨 REPOSSESSION: Liquidated inventory items for {format_tokens(liquidated_value)} tokens.")
                                    self.state["inventory"] = inv
                                
                                # 4. Forgive remaining debt
                                self.state["bank_loan"] = 0
                                self.state["loan_days_active"] = 0
                                
                                # 5. Distressed Companion(s)
                                dex = self.state.get("dex", [])
                                for d in dex:
                                    if d.get("status") != "evolved":
                                        m_state = d.get("mon_state", {})
                                        if "happiness" in m_state:
                                            m_state["happiness"] = max(0, m_state["happiness"] - 50)
                                            
                                if active:
                                    active.happiness = max(0, active.happiness - 50)
                                    self.set_active_mon(active)
                                    
                                events.append("💔 REPOSSESSION: All companions suffered a 50 happiness penalty due to bank seizure stress.")

                    if diff == 1:
                        if active:
                            bonus = 15 if active.held_item == "leftovers" else 10
                            if active.held_item == "soothe_bell":
                                bonus = 25
                            if self.has_perk("aether"):
                                bonus += 5
                            active.happiness = min(100, active.happiness + bonus)
                            self.set_active_mon(active)
                    elif diff > 1:
                        if active and active.held_item in ["leftovers", "soothe_bell"]:
                            protect_item = ItemKind(active.held_item).name_en
                            events.append(f"🍎 Your companion missed {diff-1} day(s), but was protected by {protect_item}! Happiness preserved!")
                        else:
                            decay = (diff - 1) * 25
                            if self.has_perk("aether"):
                                decay = max(1, decay // 2)
                            if active:
                                active.happiness = max(0, active.happiness - decay)
                                self.set_active_mon(active)
                                hap_val = active.happiness
                            else:
                                hap_val = 0
                            events.append(f"💔 You missed {diff-1} day(s) of coding! Companion Happiness dropped to {hap_val}%. Feed Oran Berries 🫐 to cheer them up!")
                except Exception:
                    pass
            self.state["last_active_date"] = today_str
            self.state["tokens_burned_today"] = 0
            self.save()

        if delta > 0:
            self.state["tokens_burned_today"] = self.state.get("tokens_burned_today", 0) + delta

        # Generate / check daily quests dynamically
        qdata = self.state.get("daily_quests", {})
        quests = qdata.get("quests", [])
        has_invalid = any("type" not in q for q in quests)
        if qdata.get("date") != today_str or has_invalid:
            qdata = self._generate_daily_quests(today_str)
            self.state["daily_quests"] = qdata

        # Update quest progress
        for q in qdata.get("quests", []):
            if not q.get("claimed", False):
                q_type = q.get("type", "burn_today")
                if q_type == "burn_today":
                    q["progress"] += delta
                    if q["progress"] >= q["target"]:
                        q["progress"] = q["target"]
                        events.append(f"🎯 Quest Complete: [{q['text']}]! Type 'claim {q['id']}' to collect your reward!")
                elif q_type == "streak" and self.state.get("streak_days", 1) >= q["target"]:
                    q["progress"] = q["target"]
                    events.append(f"🎯 Quest Complete: [{q['text']}]! Type 'claim {q['id']}' to collect your reward!")
                elif q_type == "happiness" and (active.happiness if active else 100) >= q["target"]:
                    q["progress"] = q["target"]
                    events.append(f"🎯 Quest Complete: [{q['text']}]! Type 'claim {q['id']}' to collect your reward!")

    def _progress_quest_by_type(self, q_type: str, delta: int = 1) -> List[str]:
        events = []
        qdata = self.state.get("daily_quests", {})
        for q in qdata.get("quests", []):
            if q.get("type") == q_type and not q.get("claimed", False):
                q["progress"] += delta
                if q["progress"] >= q["target"]:
                    q["progress"] = q["target"]
                    events.append(f"🎯 Quest Complete: [{q['text']}]! Type 'claim {q['id']}' to collect your reward!")
        return events

    def _generate_daily_quests(self, date_str: str) -> Dict[str, Any]:
        """Dynamically generates 3 daily quests using a deterministic seed for today's date."""
        rng = random.Random(date_str)

        burn_options = [
            ("q1", "Burn 1.0M tokens today", 1_000_000, "mint", "burn_today"),
            ("q1", "Burn 2.5M tokens today", 2_500_000, "rare_candy", "burn_today"),
            ("q1", "Burn 5.0M tokens today", 5_000_000, "rare_candy", "burn_today"),
        ]
        comp_options = [
            ("q2", "Hatch an egg or evolve a companion", 1, "mint", "progression"),
            ("q2", "Reach 100% Companion Happiness", 100, "rare_candy", "happiness"),
            ("q2", "Maintain a 2+ Day Coding Streak", 2, "mint", "streak"),
        ]
        epic_options = [
            ("q3", "Burn 10.0M tokens today", 10_000_000, "tokens_10m", "burn_today"),
            ("q3", "Burn 20.0M tokens today", 20_000_000, "tokens_20m", "burn_today"),
            ("q3", "Maintain a 3+ Day Coding Streak", 3, "rare_candy", "streak"),
        ]

        q1 = rng.choice(burn_options)
        q2 = rng.choice(comp_options)
        q3 = rng.choice(epic_options)

        quests = [
            {"id": q1[0], "text": q1[1], "target": q1[2], "progress": 0, "reward": q1[3], "type": q1[4], "claimed": False},
            {"id": q2[0], "text": q2[1], "target": q2[2], "progress": 0, "reward": q2[3], "type": q2[4], "claimed": False},
            {"id": q3[0], "text": q3[1], "target": q3[2], "progress": 0, "reward": q3[3], "type": q3[4], "claimed": False},
        ]
        return {"date": date_str, "quests": quests}

    def claim_quest_reward(self, q_id: str) -> Tuple[bool, str]:
        qdata = self.state.get("daily_quests", {})
        quests = qdata.get("quests", [])
        claimed_any = False
        msgs = []
        inv = self.state.get("inventory", {})

        for q in quests:
            if (q["id"] == q_id or q_id == "all") and q["progress"] >= q["target"] and not q.get("claimed", False):
                q["claimed"] = True
                claimed_any = True
                reward_type = q["reward"]
                
                if reward_type == "rare_candy":
                    inv["rare_candy"] = inv.get("rare_candy", 0) + 1
                    msgs.append(f"+1 Rare Candy 🍬 for [{q['text']}]")
                elif reward_type == "mint":
                    inv["mint"] = inv.get("mint", 0) + 1
                    msgs.append(f"+1 Mint 🌿 for [{q['text']}]")
                elif reward_type == "tokens_10m":
                    self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - 10_000_000
                    msgs.append(f"+10.0M Tokens 💰 for [{q['text']}]")
                elif reward_type == "tokens_20m":
                    self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - 20_000_000
                    msgs.append(f"+20.0M Tokens 💰 for [{q['text']}]")

        if not claimed_any:
            return False, "No completed unclaimed quest found!"

        self.state["daily_quests"] = qdata
        self.state["inventory"] = inv
        self.save()
        return True, "Claimed Rewards:\n  " + "\n  ".join(msgs)

        return False, "Unknown reward type."

    def _update_boss_battle(self, delta: int) -> List[str]:
        events = []
        bosses = [
            {"id": "boss_1", "name": "Brock & Geodude", "sp_id": 74, "badge": "🪨 Boulder Badge", "threshold": 5_000_000, "hp": 2_000_000, "reward": "rare_candy"},
            {"id": "boss_2", "name": "Misty & Starmie", "sp_id": 121, "badge": "💧 Cascade Badge", "threshold": 15_000_000, "hp": 5_000_000, "reward": "mint"},
            {"id": "boss_3", "name": "Lt. Surge & Raichu", "sp_id": 26, "badge": "⚡ Thunder Badge", "threshold": 30_000_000, "hp": 10_000_000, "reward": "tokens_10m"},
            {"id": "boss_4", "name": "Erika & Vileplume", "sp_id": 45, "badge": "🌸 Rainbow Badge", "threshold": 50_000_000, "hp": 18_000_000, "reward": "rare_candy"},
            {"id": "boss_5", "name": "Koga & Weezing", "sp_id": 110, "badge": "🟣 Soul Badge", "threshold": 75_000_000, "hp": 25_000_000, "reward": "mint"},
            {"id": "boss_6", "name": "Sabrina & Alakazam", "sp_id": 65, "badge": "🔮 Marsh Badge", "threshold": 105_000_000, "hp": 35_000_000, "reward": "tokens_15m"},
            {"id": "boss_7", "name": "Blaine & Arcanine", "sp_id": 59, "badge": "🔥 Volcano Badge", "threshold": 140_000_000, "hp": 45_000_000, "reward": "rare_candy"},
            {"id": "boss_8", "name": "Giovanni & Mewtwo", "sp_id": 150, "badge": "🌍 Earth Badge", "threshold": 180_000_000, "hp": 60_000_000, "reward": "master_ball"},
            {"id": "boss_9", "name": "Lance & Dragonite", "sp_id": 149, "badge": "🐉 Dragon Badge", "threshold": 230_000_000, "hp": 80_000_000, "reward": "tokens_20m"},
            {"id": "boss_10", "name": "Cynthia & Garchomp", "sp_id": 445, "badge": "🏆 Champion Badge", "threshold": 300_000_000, "hp": 100_000_000, "reward": "tokens_50m"}
        ]

        active_boss = self.state.get("active_boss")
        if active_boss:
            for b in bosses:
                if b["id"] == active_boss.get("id"):
                    active_boss["name"] = b["name"]

        # Deduplicate pre-existing gym badges (e.g. old '⚡ Boulder Badge' vs new '🪨 Boulder Badge')
        raw_badges = self.state.get("gym_badges", [])
        cleaned_badges = []
        seen_badge_names = set()
        for b in raw_badges:
            base_name = " ".join(b.split()[1:]) if len(b.split()) > 1 else b
            if base_name == "Boulder Badge":
                b = "🪨 Boulder Badge"
            if base_name not in seen_badge_names:
                seen_badge_names.add(base_name)
                cleaned_badges.append(b)
        
        # Sort badges by official order
        official_order = [b["badge"] for b in bosses]
        cleaned_badges.sort(key=lambda x: official_order.index(x) if x in official_order else 999)
        self.state["gym_badges"] = cleaned_badges
        gym_badges = set(cleaned_badges)
        used_today = self.state.get("used_since_install", 0)

        if active_boss is None:
            # Check if we should spawn a boss
            for b in bosses:
                if b["badge"] not in gym_badges and used_today >= b["threshold"]:
                    active_boss = {
                        "id": b["id"],
                        "name": b["name"],
                        "sp_id": b["sp_id"],
                        "badge": b["badge"],
                        "total_hp": b["hp"],
                        "current_hp": b["hp"],
                        "reward": b["reward"]
                    }
                    self.state["active_boss"] = active_boss
                    events.append(f"⚔️ BOSS RAID! Gym Boss {b['name']} (#{b['sp_id']}) has appeared! (HP: {format_tokens(b['hp'])})")
                    break

        if active_boss is not None:
            active = self.active_mon
            damage = int(delta * 2.0) if (active and active.is_mega) else delta
            if active and active.held_item == "choice_band":
                damage = int(damage * 1.5)
            active_boss["current_hp"] -= damage
            if active_boss["current_hp"] <= 0:
                active_boss["current_hp"] = 0
                badge = active_boss["badge"]
                b_name = active_boss["name"]
                if badge not in cleaned_badges:
                    cleaned_badges.append(badge)
                    cleaned_badges.sort(key=lambda x: official_order.index(x) if x in official_order else 999)
                self.state["gym_badges"] = cleaned_badges

                # Grant reward
                r_type = active_boss["reward"]
                inv = self.state.get("inventory", {})
                is_mega = active and active.is_mega
                multiplier = 1.5 if is_mega else 1.0
                if self.has_perk("macro"):
                    multiplier *= 1.20
                
                if r_type == "rare_candy":
                    inv["rare_candy"] = inv.get("rare_candy", 0) + 1
                    self.state["inventory"] = inv
                elif r_type == "mint":
                    inv["mint"] = inv.get("mint", 0) + 1
                    self.state["inventory"] = inv
                elif r_type == "tokens_10m":
                    self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - int(10_000_000 * multiplier)
                elif r_type == "tokens_15m":
                    self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - int(15_000_000 * multiplier)
                elif r_type == "tokens_20m":
                    self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - int(20_000_000 * multiplier)
                elif r_type == "tokens_50m":
                    self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - int(50_000_000 * multiplier)

                events.append(f"🏆 BOSS DEFEATED! You defeated Boss {b_name} and earned the {badge}!")
                if is_mega and r_type.startswith("tokens_"):
                    events.append("✨ MEGA BONUS! Gym Boss token reward increased by 1.5x!")
                self._record_catalyst("bosses_defeated", 1)
                self.state["active_boss"] = None

        self.save()
        return events

    def _check_achievements(self) -> List[str]:
        events = []
        achievements = set(self.state.get("achievements", []))
        dex = self.state.get("dex", [])
        used_total = self.state.get("used_since_install", 0)
        gym_badges = self.state.get("gym_badges", [])
        streak = self.state.get("streak_days", 1)

        checks = [
            ("shiny_hunter", "🌟 Shiny Hunter Badge", any(d.get("is_shiny") for d in dex)),
            ("token_tycoon", "💎 Token Tycoon Badge", used_total >= 100_000_000),
            ("dex_collector", "📖 Dex Collector Badge", len(dex) >= 5),
            ("gym_champion", "⚔️ Gym Champion Badge", len(gym_badges) >= 1),
            ("streak_master", "⚡ Streak Master Badge", streak >= 3)
        ]

        for code, title, cond in checks:
            if code not in achievements and cond:
                achievements.add(code)
                events.append(f"🎖️ ACHIEVEMENT UNLOCKED! Earned {title}!")

        self.state["achievements"] = list(achievements)
        self.save()
        return events

    def _check_growth(self, mon: MonState) -> List[str]:
        events = []
        diff = self.current_difficulty
        dex = self.state.get("dex", [])
        discovered_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))) for d in dex}

        target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, mon.stage_index, diff)

        # If holding Everstone, cap XP at threshold and halt evolution
        if mon.stage_index < len(mon.path_ids) - 1 and mon.held_item == "everstone":
            mon.used_at_stage = min(mon.used_at_stage, target_xp)
            self.set_active_mon(mon)
            return events

        # If next evolution stage already exists in Pokédex, automatically halt evolution
        if mon.stage_index < len(mon.path_ids) - 1:
            next_sp_id = mon.path_ids[mon.stage_index + 1]
            if next_sp_id in discovered_sp_ids:
                mon.used_at_stage = min(mon.used_at_stage, target_xp)
                self.set_active_mon(mon)
                return events

        while mon.used_at_stage >= target_xp:
            if mon.stage_index < len(mon.path_ids) - 1:
                # Evolve to next stage!
                prev_name = self.api.get_species_name(mon.current_id)
                mon.used_at_stage -= target_xp
                mon.stage_index += 1
                new_id = mon.current_id
                mon_name = self.api.get_species_name(new_id)
                
                # Update rarity based on the evolved form's capture rate
                sp_data = self.api.get_pokemon_species(new_id)
                if sp_data:
                    cap_rate = sp_data.get("capture_rate", 255)
                    is_leg = sp_data.get("is_legendary", False) or sp_data.get("is_mythical", False)
                    mon.rarity = Rarity.from_capture_rate(cap_rate, is_leg)

                # Check Ditto reveal
                if mon.ditto_disguise and not mon.ditto_revealed:
                    mon.ditto_revealed = True
                    events.append(f"✨ Surprised! Your Pokémon was actually Ditto disguised as #{mon.base_id}!")

                shiny_str = "✨ Shiny " if mon.is_shiny else ""
                evo_str = f"🎉 Evolution! {shiny_str}{prev_name} evolved into {shiny_str}{mon_name} (#{new_id})!"
                events.append(evo_str)
                self.state["last_evolution"] = f"{shiny_str}{prev_name} evolved into {shiny_str}{mon_name} (#{new_id})!"
                events.extend(self._progress_quest_by_type("progression"))
                self._register_to_dex(mon, status="active")
                target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, mon.stage_index, diff)
            else:
                # Final form + reached graduation threshold!
                mon_name = self.api.get_species_name(mon.current_id)
                shiny_str = "✨ Shiny " if mon.is_shiny else ""
                grad_str = f"🎓 Graduation! {shiny_str}{mon_name} has graduated to your Pokédex!"
                events.append(grad_str)
                self.state["last_evolution"] = f"{shiny_str}{mon_name} graduated to Pokédex!"

                # Add to Pokédex as graduated
                self._register_to_dex(mon, status="graduated")
                
                # Reset to new egg
                self.set_active_mon(None)
                self.state["egg_tier"] = None
                self.save()
                return events

        self.set_active_mon(mon)
        return events

    def _register_to_dex(self, mon: MonState, status: str = "active"):
        dex = self.state.get("dex", [])
        diff = self.current_difficulty
        existing_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))): d for d in dex}

        # Register/update all forms up to current stage_index
        unlocked_ids = mon.path_ids[:mon.stage_index + 1] if mon.path_ids else [mon.base_id]
        
        for idx, sp_id in enumerate(unlocked_ids):
            stage_rarity = mon.rarity
            if sp_id != mon.current_id:
                sp_data = self.api.get_pokemon_species(sp_id)
                if sp_data:
                    cap_rate = sp_data.get("capture_rate", 255)
                    is_leg = sp_data.get("is_legendary", False) or sp_data.get("is_mythical", False)
                    stage_rarity = Rarity.from_capture_rate(cap_rate, is_leg)

            target_xp = PokemonBalance.phase_threshold(stage_rarity, mon.total_forms, idx, diff)
            if status == "graduated" or idx < mon.stage_index:
                sp_status = "graduated" if status == "graduated" else "evolved"
                stage_xp = target_xp
            else:
                sp_status = status  # "active" or "inactive"
                stage_xp = mon.used_at_stage

            # Create a mon_state snippet corresponding to this stage
            sub_stage_mon = MonState(
                base_id=mon.base_id,
                path_ids=mon.path_ids,
                planned_path_ids=mon.planned_path_ids,
                stage_index=idx,
                used_at_stage=stage_xp,
                rarity=stage_rarity,
                total_forms=mon.total_forms,
                is_shiny=mon.is_shiny,
                nature=mon.nature,
                happiness=mon.happiness,
                ditto_disguise=mon.ditto_disguise,
                ditto_revealed=mon.ditto_revealed,
                is_mega=mon.is_mega if idx == mon.stage_index else False,
                mega_form=mon.mega_form if idx == mon.stage_index else None,
                held_item=mon.held_item if idx == mon.stage_index else None
            )
            sub_dict = StorageManager.mon_to_dict(sub_stage_mon)

            if sp_id in existing_sp_ids:
                entry = existing_sp_ids[sp_id]
                entry["status"] = sp_status
                entry["mon_state"] = sub_dict
                if mon.is_shiny:
                    entry["is_shiny"] = True
                if mon.nature:
                    entry["nature"] = mon.nature.value
            else:
                entry = {
                    "id": f"sp_{sp_id}",
                    "species_id": sp_id,
                    "base_id": mon.base_id,
                    "chain_order": mon.path_ids,
                    "rarity": mon.rarity.value,
                    "caught_at": datetime.datetime.now().isoformat(),
                    "is_shiny": mon.is_shiny,
                    "nature": mon.nature.value if mon.nature else None,
                    "status": sp_status,
                    "mon_state": sub_dict
                }
                dex.append(entry)
                existing_sp_ids[sp_id] = entry

        # Retroactive migration for pre-existing dex entries
        new_dex = []
        seen = set()
        for d in dex:
            sp_id = d.get("species_id", d.get("final_id", d.get("base_id")))
            d["species_id"] = sp_id
            if sp_id not in seen:
                new_dex.append(d)
                seen.add(sp_id)

            # Check if pre-evolutions are missing
            chain = d.get("chain_order", [])
            if chain and sp_id in chain:
                idx_in_chain = chain.index(sp_id)
                for pre_id in chain[:idx_in_chain]:
                    if pre_id not in seen:
                        new_dex.append({
                            "id": f"sp_{pre_id}",
                            "species_id": pre_id,
                            "base_id": d.get("base_id", pre_id),
                            "chain_order": chain,
                            "rarity": d.get("rarity", "common"),
                            "caught_at": d.get("caught_at", datetime.datetime.now().isoformat()),
                            "is_shiny": d.get("is_shiny", False),
                            "nature": d.get("nature"),
                            "status": "evolved",
                        })
                        seen.add(pre_id)

        # Ensure any pre-evolution entry whose higher evolutionary form is unlocked is marked as 'evolved'
        all_discovered_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))) for d in new_dex}
        for d in new_dex:
            sp_id = d.get("species_id", d.get("final_id", d.get("base_id")))
            chain = d.get("chain_order", [])
            if chain and sp_id in chain:
                idx_in_chain = chain.index(sp_id)
                higher_forms = chain[idx_in_chain + 1:]
                if any(h in all_discovered_sp_ids for h in higher_forms):
                    if d.get("status") not in ["active", "inactive"]:
                        d["status"] = "evolved"

        self.state["dex"] = sorted(new_dex, key=lambda x: x.get("species_id", 0))
        if status == "graduated":
            collected = set(self.state.get("collected_finals", []))
            collected.add(f"{mon.base_id}_{mon.current_id}")
            self.state["collected_finals"] = list(collected)

        self.save()

    def select_active_from_dex(self, selection_input: str) -> Tuple[bool, str]:
        # Handle 'select egg' or 'select 0'
        if selection_input.lower().startswith("egg") or selection_input == "0":
            if not self.state.get("egg_tier"):
                return False, "You don't own any Pokémon Eggs!"
                
            curr_active = self.active_mon
            if curr_active:
                self._register_to_dex(curr_active, status="inactive")
            
            self.set_active_mon(None)
            egg_usage = self.state.get("egg_usage", 0)
            threshold = self.current_difficulty.hatch_threshold
            pct = (egg_usage / threshold) * 100 if threshold > 0 else 0
            return True, f"Switched active companion to Incubating Egg! ({pct:.1f}% hatched)"

        dex = self.state.get("dex", [])
        expeditions = self.state.get("expeditions", [])
        exp_map = {e.get("sp_id"): e for e in expeditions if "sp_id" in e}
        roster = [d for d in dex if d.get("status") != "evolved"]
        target_entry = None
        s_input = selection_input.strip()

        # If input starts with '#', match strictly by species_id (e.g. 'select #570')
        if s_input.startswith("#"):
            target_sp = s_input[1:]
            for d in dex:
                sp_id = str(d.get("species_id", d.get("base_id")))
                if target_sp == sp_id:
                    target_entry = d
                    break
        else:
            # 1. Try matching by 1-based index in active roster
            try:
                idx = int(s_input)
                if 1 <= idx <= len(roster):
                    target_entry = roster[idx - 1]
            except ValueError:
                pass

            # 2. Fallback: match by species_id across all entries
            if target_entry is None:
                for d in dex:
                    sp_id = str(d.get("species_id", d.get("base_id")))
                    if s_input == sp_id:
                        target_entry = d
                        break

            # 3. Fallback: match by species name across all entries (case-insensitive)
            if target_entry is None:
                for d in dex:
                    sp_id = d.get("species_id", d.get("base_id"))
                    if s_input.lower() == self.api.get_species_name(sp_id).lower():
                        target_entry = d
                        break

        if target_entry is None:
            return False, f"Pokémon '{selection_input}' not found in Roster or Pokédex! Use roster index (1..{len(roster)}), species ID (e.g. #570), or name."

        sp_id = target_entry.get("species_id", target_entry.get("base_id"))
        sp_name = self.api.get_species_name(sp_id)

        # Prevent selecting a companion currently on an expedition
        expeditions = self.state.get("expeditions", [])
        if any(e.get("sp_id") == sp_id for e in expeditions):
            return False, f"Cannot select {sp_name}! They are currently on an expedition."

        # Prevent selecting a companion that has already evolved into a higher form
        entry_status = target_entry.get("status", "")
        chain = target_entry.get("chain_order", [])
        all_discovered_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))) for d in dex}

        if chain and sp_id in chain:
            idx_in_chain = chain.index(sp_id)
            higher_forms = [h for h in chain[idx_in_chain + 1:] if h in all_discovered_sp_ids]
            if entry_status == "evolved":
                next_name = self.api.get_species_name(higher_forms[-1]) if higher_forms else "its evolved form"
                return False, f"Cannot select {sp_name}! It has already evolved into {next_name}. Select {next_name} instead."

        # First, save current active mon into dex as inactive if exists
        curr_active = self.active_mon
        if curr_active:
            self._register_to_dex(curr_active, status="inactive")

        # Load or reconstruct target MonState
        mon_data = target_entry.get("mon_state")
        mon = StorageManager.dict_to_mon(mon_data) if mon_data else None

        diff = self.current_difficulty

        if mon is None:
            # Reconstruct fallback MonState for target species
            base_id = target_entry.get("base_id", sp_id)
            chain = target_entry.get("chain_order", [sp_id])
            rarity_val = target_entry.get("rarity", "common")
            stage_idx = chain.index(sp_id) if sp_id in chain else 0
            target_xp = PokemonBalance.phase_threshold(Rarity(rarity_val), len(chain), stage_idx, diff)
            init_xp = target_xp if (target_entry.get("status") in ["evolved", "graduated"] or stage_idx < len(chain) - 1) else 0

            mon = MonState(
                base_id=base_id,
                path_ids=chain,
                planned_path_ids=chain,
                stage_index=stage_idx,
                used_at_stage=init_xp,
                rarity=Rarity(rarity_val),
                total_forms=len(chain),
                is_shiny=target_entry.get("is_shiny", False),
                nature=PokemonNature(target_entry["nature"]) if target_entry.get("nature") else None
            )

        # Check if this species is an already-evolved pre-evolution stage
        target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, mon.stage_index, diff)
        discovered_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))) for d in dex}
        is_already_evolved = (target_entry.get("status") in ["evolved", "graduated"]) or \
                            (mon.stage_index < len(mon.path_ids) - 1 and mon.path_ids[mon.stage_index + 1] in discovered_sp_ids)

        if is_already_evolved:
            mon.used_at_stage = target_xp

        # Set new active mon
        self.set_active_mon(mon)
        self._register_to_dex(mon, status="active")
        
        shiny_str = "✨ Shiny " if mon.is_shiny else ""
        return True, f"Switched active companion to {shiny_str}{sp_name} (#{sp_id})!"

    def hatch_egg(self, initial_xp: int = 0, force_tier: Optional[str] = None, force_shiny: bool = False) -> Tuple[MonState, List[str]]:
        events = []
        used_tier = force_tier or self.state.get("egg_tier") or "common"
        if used_tier == "normal":
            used_tier = "common"
        
        # Clean up keys completely
        self.state["egg_tier"] = None
        self.state["egg_usage"] = 0
        self.state.pop("incubating_eggs", None)
        self.state.pop("current_egg_tier", None)
        
        if used_tier == "mysterious fetal form":
            base_id = 151
            rarity = Rarity.LEGENDARY
            chain_ids = [151]
            is_legendary = True
        else:
            # Select base species
            base_id, rarity, chain_ids, is_legendary = self._pick_species(used_tier)

        # Roll Shiny odds (1/64 base, or 1/24 with Golden Razz Berry)
        denom = 64
        if self.state.get("golden_razz_active", False):
            denom = 24
        if self.active_mon and self.active_mon.held_item == "scope_lens":
            denom = max(2, denom // 2)
            
        is_shiny = force_shiny or (random.randint(1, denom) == 1)
        self.state["golden_razz_active"] = False

        # Roll Nature
        nature = random.choice(list(PokemonNature))

        # Roll Ditto disguise (1 in 128 for 2+ form commons)
        ditto_disguise = None
        if rarity == Rarity.COMMON and len(chain_ids) >= 2:
            if random.randint(1, 128) == 1:
                ditto_disguise = 132  # Ditto species ID

        total_forms = len(chain_ids)
        mon = MonState(
            base_id=base_id,
            path_ids=chain_ids,
            planned_path_ids=chain_ids,
            stage_index=0,
            used_at_stage=initial_xp,
            rarity=rarity,
            total_forms=total_forms,
            is_shiny=is_shiny,
            nature=nature,
            ditto_disguise=ditto_disguise
        )

        species_name = self.api.get_species_name(base_id)
        shiny_str = "✨ Shiny " if is_shiny else ""
        nature_str = nature.display_name

        self.state["egg_usage"] = 0
        self.set_active_mon(mon)
        self._register_to_dex(mon, status="active")

        events.append(f"🐣 Egg Hatched! You got a {shiny_str}{species_name} (#{base_id})! Nature: {nature_str}, Rarity: {rarity.value.upper()}")
        events.extend(self._progress_quest_by_type("progression"))
        return mon, events

    def _pick_species(self, tier_guarantee: Optional[str] = None) -> Tuple[int, Rarity, List[int], bool]:
        # 1. Collect all owned species IDs, base IDs, and chain IDs across Pokédex and Active Companion
        owned_ids = set()
        dex = self.state.get("dex", [])
        for d in dex:
            sp_id = d.get("species_id") or d.get("base_id")
            if sp_id:
                try: owned_ids.add(int(sp_id))
                except (ValueError, TypeError): pass
            base_id = d.get("base_id")
            if base_id:
                try: owned_ids.add(int(base_id))
                except (ValueError, TypeError): pass
            final_id = d.get("final_id")
            if final_id:
                try: owned_ids.add(int(final_id))
                except (ValueError, TypeError): pass
            for ch_id in d.get("chain_order", []):
                try: owned_ids.add(int(ch_id))
                except (ValueError, TypeError): pass
            mon_st = d.get("mon_state")
            if isinstance(mon_st, dict):
                m_base = mon_st.get("base_id")
                if m_base:
                    try: owned_ids.add(int(m_base))
                    except (ValueError, TypeError): pass
                for p_id in mon_st.get("path_ids", []):
                    try: owned_ids.add(int(p_id))
                    except (ValueError, TypeError): pass

        active = self.active_mon
        if active:
            try: owned_ids.add(int(active.base_id))
            except (ValueError, TypeError): pass
            for p_id in active.path_ids:
                try: owned_ids.add(int(p_id))
                except (ValueError, TypeError): pass

        # 2. Select candidate pool based on tier guarantee
        if tier_guarantee == "legendary":
            candidates = [c for c in BASE_SPECIES_STARTERS if c[3]]
        else:
            candidates = [c for c in BASE_SPECIES_STARTERS if not c[3]]
            if tier_guarantee:
                req_rank = Rarity(tier_guarantee).sort_rank
                candidates = [c for c in candidates if Rarity.from_capture_rate(c[2], c[3]).sort_rank >= req_rank]
                if not candidates:
                    candidates = [c for c in BASE_SPECIES_STARTERS if not c[3]]

        # 3. Strict No-Duplicate Filter: exclude any species that is already owned in any form
        filtered_candidates = [c for c in candidates if c[0] not in owned_ids]

        # 4. Fallback if requested tier is exhausted: search unowned species from broader pool
        if not filtered_candidates:
            if tier_guarantee == "legendary":
                # If all legendaries are owned, find any unowned rare/pseudo-legendary species
                filtered_candidates = [c for c in BASE_SPECIES_STARTERS if c[0] not in owned_ids]
            else:
                # If tier pool is exhausted, search any unowned non-legendary species
                filtered_candidates = [c for c in BASE_SPECIES_STARTERS if not c[3] and c[0] not in owned_ids]

        # 5. True 100% full-game completion fallback (only occurs if player literally owns all 150+ species)
        if not filtered_candidates:
            filtered_candidates = candidates

        # Use capture rate as weight for random selection
        weights = [c[2] for c in filtered_candidates]
        chosen = random.choices(filtered_candidates, weights=weights, k=1)[0]

        sp_id, name, cap_rate, is_leg = chosen
        rarity = Rarity.from_capture_rate(cap_rate, is_leg)

        # Try to query evolution chain from API
        chain_ids = [sp_id]
        sp_data = self.api.get_pokemon_species(sp_id)
        if sp_data and "evolution_chain" in sp_data:
            chain_url = sp_data["evolution_chain"]["url"]
            try:
                chain_id = int(chain_url.rstrip("/").split("/")[-1])
                evo_data = self.api.get_evolution_chain(chain_id)
                if evo_data:
                    chain_ids = self._parse_evo_tree(evo_data["chain"])
            except Exception:
                pass

        if not chain_ids:
            chain_ids = [sp_id]

        return sp_id, rarity, chain_ids, is_leg

    def _parse_evo_tree(self, chain_node: Dict[str, Any]) -> List[int]:
        ids = []
        try:
            sp_url = chain_node["species"]["url"]
            sp_id = int(sp_url.rstrip("/").split("/")[-1])
            ids.append(sp_id)
            if chain_node.get("evolves_to"):
                # Pick first evolution branch
                next_node = chain_node["evolves_to"][0]
                ids.extend(self._parse_evo_tree(next_node))
        except Exception:
            pass
        return ids

    def _find_stone_evolution(self, current_id: int, api_item_name: str) -> Optional[int]:
        sp_data = self.api.get_pokemon_species(current_id)
        if not sp_data or "evolution_chain" not in sp_data:
            return None
        
        chain_url = sp_data["evolution_chain"]["url"]
        try:
            chain_id = int(chain_url.rstrip("/").split("/")[-1])
            evo_data = self.api.get_evolution_chain(chain_id)
            if not evo_data:
                return None
                
            def search_chain(node, target_id):
                sp_url = node["species"]["url"]
                node_id = int(sp_url.rstrip("/").split("/")[-1])
                
                if node_id == target_id:
                    for branch in node.get("evolves_to", []):
                        for detail in branch.get("evolution_details", []):
                            trigger = detail.get("trigger", {}).get("name") if detail.get("trigger") else None
                            item = detail.get("item", {})
                            item_name = item.get("name") if item else None
                            
                            if trigger == "use-item" and item_name == api_item_name:
                                branch_url = branch["species"]["url"]
                                return int(branch_url.rstrip("/").split("/")[-1])
                    return None
                    
                for branch in node.get("evolves_to", []):
                    res = search_chain(branch, target_id)
                    if res is not None:
                        return res
                return None
                
            return search_chain(evo_data["chain"], current_id)
        except Exception:
            return None

    def buy_item(self, item_kind: ItemKind, qty: int = 1) -> Tuple[bool, str]:
        if qty <= 0:
            return False, "Quantity must be greater than 0!"
            
        diff = self.current_difficulty
        unit_cost = item_kind.price_for(diff)
        if self.has_perk("devon"):
            unit_cost = int(unit_cost * 0.90)
        cost = unit_cost * qty
        
        if self.available_tokens < cost:
            return False, f"Not enough tokens! Required: {format_tokens(cost)}, Available: {format_tokens(self.available_tokens)}"

        inv = self.state.get("inventory", {})


        if item_kind == ItemKind.MEGA_STONE:
            import random
            from poketokenbar.game.models import MEGA_STONES
            stone_id = random.choice(list(MEGA_STONES.keys()))
            stone_key = f"mega_stone_{stone_id}"
            stone_name = MEGA_STONES[stone_id]
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
            inv[stone_key] = inv.get(stone_key, 0) + qty
            self.state["inventory"] = inv
            self._record_catalyst("shop_tokens_spent", cost)
            self.save()
            return True, f"Successfully purchased {qty}x Mystery Mega Stone! You unboxed: 🔮 {stone_name}!"

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
        inv[item_kind.value] = inv.get(item_kind.value, 0) + qty
        self.state["inventory"] = inv
        self._record_catalyst("shop_tokens_spent", cost)
        self.save()
        return True, f"Successfully purchased {qty}x {item_kind.name_en} ({item_kind.emoji})!"

    def sell_item(self, item_kind: ItemKind, qty: int = 1) -> Tuple[bool, str]:
        if qty <= 0:
            return False, "Quantity must be greater than 0!"
            
        inv = self.state.get("inventory", {})
        
        if item_kind == ItemKind.MEGA_STONE:
            target_key = None
            target_name = None
            from poketokenbar.game.models import MEGA_STONES
            for sp_id, s_name in MEGA_STONES.items():
                k = f"mega_stone_{sp_id}"
                if inv.get(k, 0) >= qty:
                    target_key = k
                    target_name = s_name
                    break
            if not target_key:
                return False, f"You don't have {qty}x of any specific Mega Stone in your Bag to sell!"
            
            diff = self.current_difficulty
            unit_cost = item_kind.price_for(diff)
            sell_value = int(unit_cost * 0.8) * qty
            inv[target_key] -= qty
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - sell_value
            self.state["inventory"] = inv
            self.save()
            return True, f"Successfully sold {qty}x {target_name} (🔮) for +{format_tokens(sell_value)} Tokens!"

        count = inv.get(item_kind.value, 0)
        if count < qty:
            return False, f"You don't have {qty}x {item_kind.name_en} in your Bag to sell!"

        diff = self.current_difficulty
        unit_cost = item_kind.price_for(diff)
        sell_value = int(unit_cost * 0.8) * qty

        inv[item_kind.value] -= qty
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - sell_value
        self.state["inventory"] = inv
        self.save()
        
        return True, f"Successfully sold {qty}x {item_kind.name_en} ({item_kind.emoji}) for +{format_tokens(sell_value)} Tokens!"

    def use_item(self, item_kind: ItemKind, qty: int = 1) -> Tuple[bool, str]:
        if qty <= 0:
            return False, "Quantity must be greater than 0."
            
        inv = self.state.get("inventory", {})
        count = inv.get(item_kind.value, 0)
        if count < qty:
            return False, f"You don't have enough {item_kind.name_en} in your Bag!"

        active = self.active_mon
        if item_kind == ItemKind.RARE_CANDY:
            if active is None:
                return False, "You need an active Pokémon companion to give Rare Candy!"
            inv[item_kind.value] -= qty
            self.state["inventory"] = inv

            xp_grant = int(self.current_difficulty.shop_prices["rare_candy"] * 0.6) * qty
            active.used_at_stage += xp_grant
            self.set_active_mon(active)

            events = self._check_growth(active)
            if events:
                alerts = self.state.get("unread_alerts", [])
                for e in events:
                    if e not in alerts:
                        alerts.append(e)
                self.state["unread_alerts"] = alerts
            self.save()
            active_name = self.api.get_species_name(active.current_id)
            msg = f"Fed {qty}x Rare Candy to {active_name}! (+{format_tokens(xp_grant)} XP)"
            if events:
                msg += "\n" + "\n".join(events)
            return True, msg
            
        elif item_kind in [
            ItemKind.EVERSTONE, ItemKind.LUCKY_EGG, ItemKind.AMULET_COIN,
            ItemKind.LEFTOVERS, ItemKind.CHOICE_SCARF, ItemKind.EXP_SHARE,
            ItemKind.SOOTHE_BELL, ItemKind.SCOPE_LENS, ItemKind.LIFE_ORB,
            ItemKind.CHOICE_BAND
        ]:
            if active is None:
                return False, f"You need an active Pokémon to equip a {item_kind.name_en}!"
            if qty > 1:
                return False, f"You can only equip one {item_kind.name_en} at a time."
                
            if active.held_item:
                # Unequip whatever is held first
                inv[active.held_item] = inv.get(active.held_item, 0) + 1
                
            active.held_item = item_kind.value
            inv[item_kind.value] -= 1
            self.state["inventory"] = inv
            self.set_active_mon(active)
            self.save()
            
            effect_text = {
                ItemKind.EVERSTONE: "Its evolution is now halted.",
                ItemKind.LUCKY_EGG: "It will now gain +20% more XP!",
                ItemKind.AMULET_COIN: "It will now find +50% more tokens in battles and expeditions!",
                ItemKind.LEFTOVERS: "It will now be protected from daily happiness decay!",
                ItemKind.CHOICE_SCARF: "It will now complete expeditions 20% faster, but drain happiness faster!",
                ItemKind.EXP_SHARE: "It will now share 25% of earned XP with inactive companions in your roster!",
                ItemKind.SOOTHE_BELL: "It will now double happiness gains and halt daily happiness decay!",
                ItemKind.SCOPE_LENS: "It will now double shiny hatching and encounter chances!",
                ItemKind.LIFE_ORB: "It will now channel +10% bonus token power from your coding!",
                ItemKind.CHOICE_BAND: "It will now deal +50% more damage in Boss and Trainer battles!"
            }.get(item_kind, "")
            
            return True, f"Equipped {item_kind.name_en} {item_kind.emoji} to {self.api.get_species_name(active.current_id)}! {effect_text}"

        elif item_kind == ItemKind.MINT:
            if qty > 1:
                return False, "You can only use one Mint at a time!"
            if active is None:
                return False, "You need an active Pokémon companion to use a Mint!"
            inv[item_kind.value] -= 1
            new_nature = random.choice(list(PokemonNature))
            active.nature = new_nature
            self.set_active_mon(active)
            self.state["inventory"] = inv
            self.save()
            return True, f"Used Mint! Nature changed to {new_nature.display_name}!"

        elif item_kind == ItemKind.BERRY_ORAN:
            if active is None:
                return False, "You need an active Pokémon companion to feed an Oran Berry!"
            inv[item_kind.value] -= qty
            active.happiness = min(100, active.happiness + (25 * qty))
            self.set_active_mon(active)
            self.state["inventory"] = inv
            self.save()
            return True, f"Fed {qty} Oran Berry 🫐 to {self.api.get_species_name(active.current_id)}! (+{25 * qty}% Happiness! Current: {active.happiness}%)"

        elif item_kind == ItemKind.BERRY_GOLDEN:
            if qty > 1:
                return False, "You can only use one Golden Razz Berry at a time!"
            inv[item_kind.value] -= 1
            self.state["golden_razz_active"] = True
            self.state["inventory"] = inv
            self.save()
            return True, "Used Golden Razz Berry 🍇! Shiny odds on your NEXT egg hatch boosted to 1/24! ✨"

        elif item_kind == ItemKind.MEGA_STONE:
            if qty > 1:
                return False, "You can only use one Mega Stone at a time!"
            return self.toggle_mega_evolution()

        elif item_kind.value.endswith("_stone") and item_kind != ItemKind.MEGA_STONE:
            if qty > 1:
                return False, "You can only use one Evolution Stone at a time!"
            active = self.active_mon
            if not active:
                return False, "You need an active companion to use an Evolution Stone!"
            
            # Check for Everstone
            if active.held_item == "everstone":
                return False, "Your companion is holding an Everstone! It cannot evolve."
            
            api_item_name = item_kind.value.replace("_", "-")
            target_evo_id = self._find_stone_evolution(active.current_id, api_item_name)
            
            if not target_evo_id:
                return False, f"The {item_kind.name_en} has no effect on {self.api.get_species_name(active.current_id)}!"

            # Block stone evolution if target evolved form already exists in Pokédex
            dex = self.state.get("dex", [])
            discovered_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))) for d in dex}
            if target_evo_id in discovered_sp_ids:
                next_name = self.api.get_species_name(target_evo_id)
                return False, f"Cannot evolve into {next_name}! {next_name} (#{target_evo_id}) already exists in your Pokédex."
                
            inv[item_kind.value] -= 1
            if inv[item_kind.value] <= 0:
                del inv[item_kind.value]
                
            prev_name = self.api.get_species_name(active.current_id)
            active.stage_index += 1
            
            if active.stage_index >= len(active.path_ids):
                active.path_ids.append(target_evo_id)
            else:
                active.path_ids[active.stage_index] = target_evo_id
                active.path_ids = active.path_ids[:active.stage_index + 1]
                
            active.total_forms = len(active.path_ids)
            new_name = self.api.get_species_name(target_evo_id)
            
            sp_data = self.api.get_pokemon_species(target_evo_id)
            if sp_data:
                cap_rate = sp_data.get("capture_rate", 255)
                is_leg = sp_data.get("is_legendary", False) or sp_data.get("is_mythical", False)
                active.rarity = Rarity.from_capture_rate(cap_rate, is_leg)
                
            active.used_at_stage = 0 
            
            self._register_to_dex(active, status="active")
            self.set_active_mon(active)
            self.state["inventory"] = inv
            self.save()
            
            shiny_str = "✨ Shiny " if active.is_shiny else ""
            quests_msg = "\n".join(self._progress_quest_by_type("progression"))
            msg = f"🎉 Amazing! {shiny_str}{prev_name} evolved into {shiny_str}{new_name} using the {item_kind.name_en}!"
            if quests_msg:
                msg += f"\n{quests_msg}"
            return True, msg

        elif item_kind == ItemKind.EXPEDITION_PASS:
            if qty > 1:
                return False, "You can only use one Expedition Pass at a time!"
            expeditions = self.state.get("expeditions", [])
            if not expeditions:
                return False, "You have no active expeditions to complete!"
            inv[item_kind.value] -= 1
            # Complete the first expedition instantly
            exp = expeditions[0]
            remaining_xp = max(0, exp.get("target", 0) - exp.get("progress", 0))
            events = []
            self._update_expeditions(remaining_xp, events)
            self.state["inventory"] = inv
            self.save()
            return True, "\n".join(events)

        elif item_kind == ItemKind.POKE_FLUTE:
            if qty > 1:
                return False, "You can only use one Poké Flute at a time!"
            if self.state.get("active_boss"):
                return False, "A Gym Boss is already active! Defeat them first!"
            
            # Find an undefeated boss, or pick a random one if all defeated
            bosses = [
                {"id": "boss_1", "name": "Brock & Geodude", "sp_id": 74, "badge": "🪨 Boulder Badge", "hp": 2_000_000, "reward": "rare_candy"},
                {"id": "boss_2", "name": "Misty & Starmie", "sp_id": 121, "badge": "💧 Cascade Badge", "hp": 5_000_000, "reward": "mint"},
                {"id": "boss_3", "name": "Lt. Surge & Raichu", "sp_id": 26, "badge": "⚡ Thunder Badge", "hp": 10_000_000, "reward": "tokens_10m"},
                {"id": "boss_4", "name": "Erika & Vileplume", "sp_id": 45, "badge": "🌸 Rainbow Badge", "hp": 18_000_000, "reward": "rare_candy"},
                {"id": "boss_5", "name": "Koga & Weezing", "sp_id": 110, "badge": "🟣 Soul Badge", "hp": 25_000_000, "reward": "mint"},
                {"id": "boss_6", "name": "Sabrina & Alakazam", "sp_id": 65, "badge": "🔮 Marsh Badge", "hp": 35_000_000, "reward": "tokens_15m"},
                {"id": "boss_7", "name": "Blaine & Arcanine", "sp_id": 59, "badge": "🔥 Volcano Badge", "hp": 45_000_000, "reward": "rare_candy"},
                {"id": "boss_8", "name": "Giovanni & Mewtwo", "sp_id": 150, "badge": "🌍 Earth Badge", "hp": 60_000_000, "reward": "master_ball"},
                {"id": "boss_9", "name": "Lance & Dragonite", "sp_id": 149, "badge": "🐉 Dragon Badge", "hp": 80_000_000, "reward": "tokens_20m"},
                {"id": "boss_10", "name": "Cynthia & Garchomp", "sp_id": 445, "badge": "🏆 Champion Badge", "hp": 100_000_000, "reward": "tokens_50m"}
            ]
            gym_badges = set(self.state.get("gym_badges", []))
            available = [b for b in bosses if b["badge"] not in gym_badges]
            
            if not available:
                available = bosses  # All defeated, spawn any for fun
            
            b = random.choice(available)
            active_boss = {
                "id": b["id"],
                "name": b["name"],
                "sp_id": b["sp_id"],
                "badge": b["badge"],
                "total_hp": b["hp"],
                "current_hp": b["hp"],
                "reward": b["reward"]
            }
            self.state["active_boss"] = active_boss
            inv[item_kind.value] -= 1
            self.state["inventory"] = inv
            self.save()
            return True, f"🪈 You played the Poké Flute! A wild Gym Boss {b['name']} (#{b['sp_id']}) was summoned! (HP: {format_tokens(b['hp'])})"

        elif item_kind == ItemKind.MASTER_BALL:
            eggs = self.state.get("incubating_eggs", {})
            if not eggs:
                # If they have an active legacy egg
                if self.active_mon is None:
                    curr_tier = self.state.get("current_egg_tier") or self.state.get("egg_tier") or "normal"
                    eggs[curr_tier] = self.state.get("egg_usage", 0)
                else:
                    return False, "You need an incubating egg to use the Master Ball!"
            
            inv[item_kind.value] -= 1
            
            # Find the egg with the most progress to hatch
            best_tier = max(eggs.keys(), key=lambda t: eggs[t])
            events = []
            
            # Ensure the current active mon (if any) is archived first just in case
            if self.active_mon:
                self._register_to_dex(self.active_mon, status="inactive")
                
            mon, hatch_events = self.hatch_egg(initial_xp=0, force_tier=best_tier, force_shiny=True)
            events.extend(hatch_events)
            eggs.pop(best_tier, None)
            self.state["incubating_eggs"] = eggs
            self.state["inventory"] = inv
            self.save()
            return True, f"Threw a Master Ball 🌟! Guaranteed Shiny hatch!\n" + "\n".join(events)

        elif item_kind == ItemKind.EXPEDITION_LICENSE:
            inv[item_kind.value] -= 1
            self.state["expedition_slots"] = self.state.get("expedition_slots", 10) + 10
            self.state["inventory"] = inv
            self.save()
            return True, "📜 Used an Expedition License! You can now send 10 more Pokémon on expeditions simultaneously!"

        return False, f"{item_kind.name_en} is not usable directly from the Bag."

    def unequip_item(self) -> Tuple[bool, str]:
        active = self.active_mon
        if not active:
            return False, "You don't have an active Pokémon!"
        if not active.held_item:
            return False, "Your active companion is not holding any item."
        
        held = active.held_item
        active.held_item = None
        self.set_active_mon(active)
        
        inv = self.state.get("inventory", {})
        inv[held] = inv.get(held, 0) + 1
        self.state["inventory"] = inv
        
        events = self._check_growth(active)
        self.save()
        
        from poketokenbar.game.models import ItemKind
        try:
            kind_name = ItemKind(held).name_en
        except ValueError:
            kind_name = held
            
        msg = f"Unequipped {kind_name} from your companion!"
        if events:
            msg += "\n" + "\n".join(events)
        return True, msg

    def toggle_mega_evolution(self, target_stone_key: Optional[str] = None, force_revert: bool = False) -> Tuple[bool, str]:
        active = self.active_mon
        if active is None:
            return False, "You need an active Pokémon companion to Mega Evolve!"

        if force_revert:
            active.is_mega = False
            active.mega_form = None
            self.set_active_mon(active)
            return True, f"{self.api.get_species_name(active.current_id)} reverted back to standard form."

        sp_id = str(active.current_id)
        
        inv = self.state.get("inventory", {})
        from poketokenbar.game.models import MEGA_STONES
        
        is_eligible = any(str(k) == sp_id or str(k).startswith(f"{sp_id}_") for k in MEGA_STONES.keys())
        if not is_eligible:
            return False, f"Species #{sp_id} ({self.api.get_species_name(active.current_id)}) is not eligible for Mega Evolution!"
            
        owned_forms = []
        
        if f"{sp_id}_X" in MEGA_STONES and inv.get(f"mega_stone_{sp_id}_X", 0) > 0:
            owned_forms.append("X")
        if f"{sp_id}_Y" in MEGA_STONES and inv.get(f"mega_stone_{sp_id}_Y", 0) > 0:
            owned_forms.append("Y")
        if sp_id in MEGA_STONES and inv.get(f"mega_stone_{sp_id}", 0) > 0:
            owned_forms.append("Normal")
            
        if not owned_forms:
            return False, f"You need a corresponding Mega Stone 🔮 to Mega Evolve {self.api.get_species_name(active.current_id)}!"
            
        if target_stone_key:
            if not (target_stone_key == f"mega_stone_{sp_id}" or target_stone_key.startswith(f"mega_stone_{sp_id}_")):
                stone_name = "Mega Stone"
                for k, v in MEGA_STONES.items():
                    if f"mega_stone_{k}" == target_stone_key:
                        stone_name = v
                        break
                return False, f"The {stone_name} is not compatible with {self.api.get_species_name(active.current_id)}!"
            
            if target_stone_key == f"mega_stone_{sp_id}_X":
                req_form = "X"
            elif target_stone_key == f"mega_stone_{sp_id}_Y":
                req_form = "Y"
            else:
                req_form = "Normal"
            
            curr = active.mega_form if getattr(active, 'mega_form', None) else "Normal"
            if active.is_mega and curr == req_form:
                next_form = None
            else:
                next_form = req_form
        else:
            if not active.is_mega:
                next_form = owned_forms[0]
            else:
                current_idx = -1
                curr = active.mega_form if getattr(active, 'mega_form', None) else "Normal"
                if curr in owned_forms:
                    current_idx = owned_forms.index(curr)
                
                if current_idx + 1 < len(owned_forms):
                    next_form = owned_forms[current_idx + 1]
                else:
                    next_form = None 
                
        if next_form is None:
            active.is_mega = False
            active.mega_form = None
            msg = f"{self.api.get_species_name(active.current_id)} reverted back to standard form."
        else:
            active.is_mega = True
            active.mega_form = next_form if next_form in ["X", "Y"] else None
            form_str = f" {next_form}" if next_form in ["X", "Y"] else ""
            msg = f"✨ MEGA EVOLUTION! {self.api.get_species_name(active.current_id)} has Mega Evolved into Mega Form{form_str}! (+50% Bonus XP active!)"

        self.set_active_mon(active)
        return True, msg

    def _update_expeditions(self, effective_xp: int, events: List[str]):
        expeditions = self.state.get("expeditions", [])
        if not expeditions:
            return

        from poketokenbar.game.models import Rarity
        
        remaining = []
        for exp in expeditions:
            sp_id = exp.get("sp_id")
            if not sp_id:
                continue
            sp_name = self.api.get_species_name(sp_id)
            area = exp.get("area", "Viridian Forest")
            reward = exp.get("reward")
            if not reward:
                area_l = str(area).lower()
                if "cerulean" in area_l:
                    reward = "rare_candy"
                elif "silver" in area_l:
                    reward = "berry_golden"
                elif "spear" in area_l:
                    reward = "legendary_egg"
                elif "mine" in area_l:
                    reward = "evo_stone"
                else:
                    reward = "mint"
                exp["reward"] = reward

            if "progress" not in exp:
                exp["progress"] = 0
            if "target" not in exp:
                exp["target"] = 5_000_000

            # Fetch rarity from dex to apply multiplier
            dex = self.state.get("dex", [])
            rarity_val = "common"
            if exp.get("is_mega", False):
                rarity_val = "mega"
            else:
                for d in dex:
                    if d.get("species_id", d.get("base_id")) == sp_id:
                        if d.get("mon_state", {}).get("is_mega", False):
                            rarity_val = "mega"
                        else:
                            rarity_val = d.get("rarity", "common")
                        break
            
            try:
                rarity = Rarity(rarity_val)
            except ValueError:
                rarity = Rarity.COMMON

            mult = 1.0
            if rarity == Rarity.UNCOMMON:
                mult = 1.25
            elif rarity == Rarity.RARE:
                mult = 1.5
            elif rarity == Rarity.LEGENDARY:
                mult = 3.0
            elif rarity == Rarity.MEGA:
                mult = 5.0

            if exp.get("shiny"):
                mult *= 2.0
            
            active = self.active_mon
            if active and active.held_item == "choice_scarf":
                mult *= 1.20
            if self.has_perk("silph"):
                mult *= 1.15

            exp["progress"] += int(effective_xp * mult)
            
            if exp["progress"] >= exp["target"]:

                # Grant reward
                inv = self.state.get("inventory", {})
                if reward == "rare_candy":
                    inv["rare_candy"] = inv.get("rare_candy", 0) + 1
                    reward_str = "+1 Rare Candy 🍬"
                    if random.random() < 0.05:
                        inv["map_fragment"] = inv.get("map_fragment", 0) + 1
                        reward_str += " & +1 Map 📜!"
                elif reward == "mint":
                    inv["mint"] = inv.get("mint", 0) + 1
                    reward_str = "+1 Mint 🌿"
                elif reward == "legendary_egg":
                    current_tier = self.state.get("egg_tier")
                    if current_tier is None:
                        self.state["egg_tier"] = "legendary"
                        self.state["egg_usage"] = 0
                    else:
                        pending = self.state.get("pending_eggs", [])
                        pending.append("legendary")
                        self.state["pending_eggs"] = pending
                    reward_str = "a LEGENDARY EGG 🌟!"
                elif reward == "evo_stone":
                    stone_types = [
                        "water_stone", "fire_stone", "thunder_stone", 
                        "leaf_stone", "moon_stone", "sun_stone", 
                        "ice_stone", "shiny_stone", "dusk_stone", "dawn_stone"
                    ]
                    st_key = random.choice(stone_types)
                    inv[st_key] = inv.get(st_key, 0) + 1
                    st_name = st_key.replace("_", " ").title()
                    reward_str = f"+1 {st_name} 💎"
                else:
                    inv["berry_golden"] = inv.get("berry_golden", 0) + 1
                    reward_str = "+1 Golden Razz Berry 🍇"
                    if random.random() < 0.15:
                        inv["map_fragment"] = inv.get("map_fragment", 0) + 1
                        reward_str += " & +1 Map 📜!"

                self.state["inventory"] = inv

                dex = self.state.get("dex", [])
                xp_gain = int(exp["target"] * 0.5)
                tokens_gain = int(exp["target"] * 0.2)
                
                # Check for held item Amulet Coin
                if active and active.held_item == "amulet_coin":
                    tokens_gain = int(tokens_gain * 1.5)
                if self.has_perk("silph"):
                    tokens_gain = int(tokens_gain * 1.15)

                # Grant tokens by refunding spent_tokens
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - tokens_gain
                
                from poketokenbar.game.models import MonState, PokemonBalance
                for d in dex:
                    sp_id_dex = d.get("species_id", d.get("base_id"))
                    if sp_id_dex == sp_id:
                        if "mon_state" in d and isinstance(d["mon_state"], dict):
                            mon = StorageManager.dict_to_mon(d["mon_state"])
                        else:
                            mon = StorageManager.dict_to_mon(d)
                            
                        mon.happiness = max(0, mon.happiness - 10)
                        mon.used_at_stage += xp_gain
                        
                        target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, mon.stage_index, self.current_difficulty)
                        if mon.used_at_stage > target_xp:
                            mon.used_at_stage = target_xp
                            
                        self._register_to_dex(mon, status=d.get("status", "inactive"))
                        break

                now_str = datetime.datetime.now().strftime("%H:%M:%S")
                logs = self.state.get("expedition_logs", [])
                logs.append(f"[{now_str}] {sp_name}: {reward_str} | +{format_tokens(tokens_gain)} 🪙 | +{format_tokens(xp_gain)} XP")
                self.state["expedition_logs"] = logs[-3:]
                self._record_catalyst("expeditions_completed", 1)
                events.append(f"🗺️ {sp_name} finished {area}: {reward_str} | +{format_tokens(tokens_gain)} 🪙 | +{format_tokens(xp_gain)} XP")
            else:
                remaining.append(exp)

        self.state["expeditions"] = remaining
        self.save()

    def use_expedition_pass(self, idx_str: str) -> Tuple[bool, str]:
        try:
            idx = int(idx_str) - 1
        except ValueError:
            return False, "Invalid index. Usage: pass <idx>"
            
        expeditions = self.state.get("expeditions", [])
        if not (0 <= idx < len(expeditions)):
            return False, f"Invalid expedition index. Must be between 1 and {len(expeditions)}."
            
        inv = self.state.get("inventory", {})
        if inv.get("expedition_pass", 0) <= 0:
            return False, "You don't have any Expedition Passes (🎫)!"
            
        exp = expeditions[idx]
        exp["progress"] = exp.get("target", 0)
        inv["expedition_pass"] -= 1
        if inv["expedition_pass"] <= 0:
            del inv["expedition_pass"]
            
        self.state["inventory"] = inv
        self.save()
        
        # Instantly process completions
        events = []
        self._update_expeditions(0, events)
        
        event_str = " ".join(events) if events else f"Expedition {idx + 1} instantly completed!"
        return True, f"Used 🎫 Expedition Pass! {event_str}"

    def _find_roster_entry(self, s_input: str, roster: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        s_input = s_input.strip()
        if not s_input:
            return None

        # 1. If starts with '#', match strictly by species_id within ROSTER
        if s_input.startswith("#"):
            target_sp = s_input[1:]
            for d in roster:
                sp_id = str(d.get("species_id", d.get("base_id")))
                if target_sp == sp_id:
                    return d
            return None

        # 2. Try matching by 1-based index in ROSTER (matching Tab 3 Roster exactly)
        try:
            idx = int(s_input)
            if 1 <= idx <= len(roster):
                return roster[idx - 1]
        except ValueError:
            pass

        # 3. Fallback to species_id match within ROSTER
        for d in roster:
            sp_id = str(d.get("species_id", d.get("base_id")))
            if s_input == sp_id:
                return d

        # 4. Fallback to species name match within ROSTER (case-insensitive)
        s_lower = s_input.lower()
        for d in roster:
            sp_id = d.get("species_id", d.get("base_id"))
            if s_lower == self.api.get_species_name(sp_id).lower():
                return d

        return None

    def dispatch_expedition(self, selection_input: Union[str, List[str]], area_name: str = "Viridian Forest") -> Tuple[bool, str]:
        dex = self.state.get("dex", [])
        if not dex:
            return False, "Your Pokédex is empty! Register companions before dispatching expeditions."

        from poketokenbar.game.models import PokemonBalance
        areas = {
            "viridian": ("Viridian Forest", PokemonBalance.EXPEDITION_VIRIDIAN, "mint"),
            "cerulean": ("Cerulean Cave", PokemonBalance.EXPEDITION_CERULEAN, "rare_candy"),
            "silver": ("Mt. Silver", PokemonBalance.EXPEDITION_SILVER, "berry_golden"),
            "spear": ("Spear Pillar (Deep)", PokemonBalance.EXPEDITION_SPEAR_PILLAR, "legendary_egg"),
            "mine": ("Evolution Mine", 10_000_000, "evo_stone")
        }

        clean_area = area_name.strip().lower()
        key = None
        if clean_area in ("viridian", "viridian forest"):
            key = "viridian"
        elif clean_area in ("cerulean", "cerulean cave"):
            key = "cerulean"
        elif clean_area in ("silver", "mt silver", "mt. silver", "mount silver", "mt"):
            key = "silver"
        elif clean_area in ("spear", "spear pillar", "spear pillar (deep)", "deep"):
            key = "spear"
        elif clean_area in ("mine", "evolution mine", "evolution"):
            key = "mine"
        else:
            words = clean_area.split()
            for w in words:
                w_clean = w.strip(".,")
                if w_clean == "viridian":
                    key = "viridian"
                    break
                elif w_clean == "cerulean":
                    key = "cerulean"
                    break
                elif w_clean in ("silver", "mount"):
                    key = "silver"
                    break
                elif w_clean in ("spear", "pillar"):
                    key = "spear"
                    break
                elif w_clean in ("mine", "evolution"):
                    key = "mine"
                    break

        if not key or key not in areas:
            return False, f"Expedition destination '{area_name}' is not one of the available options! Available destinations: viridian, mine, cerulean, silver, spear."

        expeditions = self.state.get("expeditions", [])
        slot_limit = self.state.get("expedition_slots", 10)
        if len(expeditions) >= slot_limit:
            return False, f"You have reached the maximum limit of {slot_limit} active expeditions! You must wait for them to finish or use an Expedition License (📜) to expand your slots."

        roster = [d for d in dex if d.get("status") != "evolved"]

        is_all = False
        target_tokens: List[str] = []
        if isinstance(selection_input, list):
            target_tokens = [str(x).strip() for x in selection_input if str(x).strip()]
        else:
            s_raw = str(selection_input).strip()
            if s_raw.lower() == "all":
                is_all = True
            elif "," in s_raw:
                raw_pieces = [p.strip() for p in s_raw.split(",") if p.strip()]
                for piece in raw_pieces:
                    if "-" in piece and not piece.startswith("#"):
                        sub = piece.split("-")
                        if len(sub) == 2 and sub[0].isdigit() and sub[1].isdigit():
                            target_tokens.extend([str(i) for i in range(int(sub[0]), int(sub[1]) + 1)])
                            continue
                    elif ".." in piece and not piece.startswith("#"):
                        sub = piece.split("..")
                        if len(sub) == 2 and sub[0].isdigit() and sub[1].isdigit():
                            target_tokens.extend([str(i) for i in range(int(sub[0]), int(sub[1]) + 1)])
                            continue
                    target_tokens.append(piece)
            else:
                raw_pieces = s_raw.split()
                for piece in raw_pieces:
                    if "-" in piece and not piece.startswith("#"):
                        sub = piece.split("-")
                        if len(sub) == 2 and sub[0].isdigit() and sub[1].isdigit():
                            target_tokens.extend([str(i) for i in range(int(sub[0]), int(sub[1]) + 1)])
                            continue
                    elif ".." in piece and not piece.startswith("#"):
                        sub = piece.split("..")
                        if len(sub) == 2 and sub[0].isdigit() and sub[1].isdigit():
                            target_tokens.extend([str(i) for i in range(int(sub[0]), int(sub[1]) + 1)])
                            continue
                    target_tokens.append(piece)

        # Single companion dispatch path (100% backwards compatible)
        if not is_all and len(target_tokens) == 1:
            s_input = target_tokens[0]
            target_entry = self._find_roster_entry(s_input, roster)

            if target_entry is None:
                return False, f"Companion '{selection_input}' not found in Roster! Only active companions in your Roster can be dispatched on expeditions (use roster index 1..{len(roster)}, species ID, or name)."

            sp_id = target_entry.get("species_id", target_entry.get("base_id"))
            sp_name = self.api.get_species_name(sp_id)

            if any(e.get("sp_id") == sp_id for e in expeditions):
                return False, f"{sp_name} is already on an expedition!"

            mon_state_dict = target_entry.get("mon_state", {})
            current_hap = mon_state_dict.get("happiness", target_entry.get("happiness", 100)) if isinstance(mon_state_dict, dict) else target_entry.get("happiness", 100)

            if current_hap <= 0:
                return False, f"{sp_name} is completely exhausted (0% Happiness) and refuses to go on an expedition! Please feed it Oran Berries 🫐 first."

            if key == "spear":
                inv = self.state.get("inventory", {})
                if inv.get("map_fragment", 0) < 3:
                    return False, "You need 3x Maps to dispatch a Deep Expedition to Spear Pillar!"
                if current_hap < 100:
                    return False, "Only a companion with 100% Happiness can brave a Deep Expedition to Spear Pillar!"
                inv["map_fragment"] -= 3
                self.state["inventory"] = inv

            active = self.active_mon
            is_mega_dispatch = False
            active_current_id = active.path_ids[active.stage_index] if active and active.stage_index < len(active.path_ids) else (active.base_id if active else None)
            if active and (target_entry.get("status") == "active" or active_current_id == sp_id):
                is_mega_dispatch = active.is_mega
                self._register_to_dex(active, status="inactive")
                self.set_active_mon(None)

            area_title, target_xp, reward_type = areas[key]
            target_entry["happiness"] = max(0, target_entry.get("happiness", 100) - 10)
            if isinstance(mon_state_dict, dict):
                mon_state_dict["happiness"] = target_entry["happiness"]

            expeditions.append({
                "sp_id": sp_id,
                "area": area_title,
                "progress": 0,
                "target": target_xp,
                "reward": reward_type,
                "is_mega": is_mega_dispatch
            })
            self.state["expeditions"] = expeditions
            self.save()
            return True, f"🗺️ Dispatched {sp_name} on an expedition to {area_title}! ({format_tokens(target_xp)} tokens required)"

        # Multi-companion batch dispatch path
        area_title, target_xp, reward_type = areas[key]
        candidate_entries: List[Dict[str, Any]] = []
        not_found: List[str] = []
        seen_entry_ids = set()

        if is_all:
            candidate_entries = list(roster)
        else:
            for tok in target_tokens:
                entry = self._find_roster_entry(tok, roster)
                if entry is None:
                    not_found.append(tok)
                else:
                    eid = entry.get("id") or str(entry.get("species_id", entry.get("base_id")))
                    if eid not in seen_entry_ids:
                        seen_entry_ids.add(eid)
                        candidate_entries.append(entry)

        if not candidate_entries:
            if not_found:
                return False, f"None of the specified companions ({', '.join(not_found)}) were found in your Roster!"
            return False, "No eligible companions available to dispatch!"

        inv = self.state.get("inventory", {})
        dispatched_names: List[str] = []
        skipped_notes: List[str] = []

        for entry in candidate_entries:
            if len(expeditions) >= slot_limit:
                skipped_notes.append("slots full")
                break

            sp_id = entry.get("species_id", entry.get("base_id"))
            sp_name = self.api.get_species_name(sp_id)

            if any(e.get("sp_id") == sp_id for e in expeditions):
                skipped_notes.append(f"{sp_name} (already deployed)")
                continue

            mon_state_dict = entry.get("mon_state", {})
            hap = mon_state_dict.get("happiness", entry.get("happiness", 100)) if isinstance(mon_state_dict, dict) else entry.get("happiness", 100)

            if hap <= 0:
                skipped_notes.append(f"{sp_name} (exhausted)")
                continue

            if key == "spear":
                if hap < 100:
                    skipped_notes.append(f"{sp_name} (<100% hap)")
                    continue
                if inv.get("map_fragment", 0) < 3:
                    skipped_notes.append("need 3x Maps each")
                    break
                inv["map_fragment"] -= 3

            active = self.active_mon
            is_mega_dispatch = False
            active_current_id = active.path_ids[active.stage_index] if active and active.stage_index < len(active.path_ids) else (active.base_id if active else None)
            if active and (entry.get("status") == "active" or active_current_id == sp_id):
                is_mega_dispatch = active.is_mega
                self._register_to_dex(active, status="inactive")
                self.set_active_mon(None)

            entry["happiness"] = max(0, entry.get("happiness", 100) - 10)
            if isinstance(mon_state_dict, dict):
                mon_state_dict["happiness"] = entry["happiness"]

            expeditions.append({
                "sp_id": sp_id,
                "area": area_title,
                "progress": 0,
                "target": target_xp,
                "reward": reward_type,
                "is_mega": is_mega_dispatch
            })
            dispatched_names.append(sp_name)

        if not dispatched_names:
            reason_str = ", ".join(skipped_notes) if skipped_notes else "conditions not met"
            return False, f"Could not dispatch companions to {area_title} ({reason_str})."

        if key == "spear":
            self.state["inventory"] = inv
        self.state["expeditions"] = expeditions
        self.save()

        count = len(dispatched_names)
        if count <= 4:
            names_summary = ", ".join(dispatched_names)
        else:
            names_summary = f"{', '.join(dispatched_names[:3])}, +{count - 3} more"

        msg = f"🗺️ Dispatched {count} Pokémon ({names_summary}) on expedition to {area_title}! ({format_tokens(target_xp)} tokens required each)"
        if skipped_notes:
            msg += f" (Note: {len(skipped_notes)} skipped: {', '.join(skipped_notes[:2])})"
        return True, msg

    def _check_trainer_battle(self, delta: int, events: List[str]):
        # Trigger mini trainer encounter every 2.0M tokens
        used_total = self.state.get("used_since_install", 0)
        last_battle_token = self.state.get("last_battle_token", 0)

        if used_total - last_battle_token >= 2_000_000:
            self.state["last_battle_token"] = used_total
            battles = self.state.get("trainer_battles", {"wins": 0, "losses": 0})

            opponents = [
                ("Youngster Joey & Rattata", 1),
                ("Bug Catcher Rick & Caterpie", 1),
                ("Team Rocket Grunt & Koffing", 2),
                ("Rival Blue & Pidgeot", 3)
            ]
            opp_name, req_stage = random.choice(opponents)
            active = self.active_mon

            player_stage = active.stage_index + 1 if active else 0
            if active and active.is_mega:
                player_stage += 2

            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            logs = self.state.get("battle_logs", [])

            if player_stage >= req_stage or random.randint(1, 3) != 1:
                battles["wins"] += 1
                
                if active and active.is_mega:
                    token_reward = 3_000_000
                    reward_str = "3.0M"
                    bonus_msg = " ✨ MEGA BONUS!"
                else:
                    token_reward = 2_000_000
                    reward_str = "2.0M"
                    bonus_msg = ""
                    
                active = self.active_mon
                if active and active.held_item == "amulet_coin":
                    token_reward = int(token_reward * 1.5)
                    reward_str = f"{token_reward / 1_000_000:.1f}M"
                    bonus_msg += " (🪙 Amulet Coin Bonus!)"
                if self.has_perk("macro"):
                    token_reward = int(token_reward * 1.20)
                    reward_str = f"{token_reward / 1_000_000:.1f}M"
                    bonus_msg += " (⚡ Macro Cosmos Perk!)"
                    
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - token_reward
                msg = f"⚔️ TRAINER BATTLE! You defeated {opp_name} in an auto-battle! Earned +{reward_str} Spendable Tokens!{bonus_msg}"
                events.append(msg)
                logs.append(f"[{now_str}] 🏆 WIN vs {opp_name} (Earned +{reward_str} Tokens)")
            else:
                battles["losses"] += 1
                if active:
                    active.happiness = max(0, active.happiness - 10)
                    self.set_active_mon(active)
                    hap_val = active.happiness
                else:
                    self.state["happiness"] = max(0, self.state.get("happiness", 100) - 10)
                    hap_val = self.state["happiness"]
                
                msg = f"⚔️ TRAINER BATTLE! {opp_name} put up a tough fight! Companion Happiness dropped to {hap_val}%!"
                events.append(msg)
                logs.append(f"[{now_str}] ❌ LOSS vs {opp_name}")

            self.state["battle_logs"] = logs[-5:]
            self.state["trainer_battles"] = battles
            self.save()

    def generate_trainer_card(self) -> str:
        used_total = self.state.get("used_since_install", 0)
        badges = self.state.get("gym_badges", [])
        streak = self.state.get("streak_days", 1)
        active = self.active_mon
        held_str = ""
        if active and active.held_item:
            try:
                kind = ItemKind(active.held_item)
                held_str = f" [{kind.emoji} {kind.name_en}]"
            except ValueError:
                held_str = f" [{active.held_item}]"
        mon_str = f"{self.api.get_species_name(active.current_id)} (#{active.current_id}){held_str}" if active else "Incubating Egg"

        rank = "Junior Coder"
        if used_total >= 100_000_000:
            rank = "Master Developer"
        elif used_total >= 30_000_000:
            rank = "Senior Engineer"
        elif used_total >= 10_000_000:
            rank = "Staff Coder"

        lines = [
            "========================================================================",
            " 📇 POKETOKENBAR — TRAINER PROFILE CARD",
            "========================================================================",
            f" Trainer Rank:     {rank}",
            f" Active Companion: {mon_str}",
            f" Coding Streak:    🔥 {streak} Days",
            f" Tokens Burned:    {format_tokens(used_total)} tokens",
            f" Gym Badges:       {len(badges)}/10 (" + ", ".join(badges[:4]) + ("..." if len(badges) > 4 else "") + ")",
            "========================================================================"
        ]
        return "\n".join(lines)

    def buy_egg(self, tier: Optional[Rarity] = None) -> Tuple[bool, str]:
        diff = self.current_difficulty
        costs = diff.shop_prices
        tier_key = tier.value if tier else "normal"
        cost = costs.get("egg_rare" if tier == Rarity.RARE else ("egg_uncommon" if tier == Rarity.UNCOMMON else "egg_normal"), 30_000_000)
        if self.has_perk("devon"):
            cost = int(cost * 0.90)

        current_tier = self.state.get("egg_tier")
        if current_tier is not None:
            return False, f"You already own a {current_tier.capitalize()} Pokémon Egg! You can only carry one egg at a time."

        if self.available_tokens < cost:
            return False, f"Not enough tokens! Required: {format_tokens(cost)}, Available: {format_tokens(self.available_tokens)}"

        # Save current active mon into dex roster if exists
        curr_active = self.active_mon
        if curr_active:
            self._register_to_dex(curr_active, status="inactive")

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
        self.set_active_mon(None)
        self.state["egg_usage"] = 0
        self.state["egg_tier"] = tier_key
        
        # Clean up old keys
        self.state.pop("incubating_eggs", None)
        self.state.pop("current_egg_tier", None)
        
        self._record_catalyst("shop_tokens_spent", cost)
        self.save()
        tier_str = f"{tier.value.upper()}+" if tier else "Standard"
        return True, f"Obtained a fresh {tier_str} Pokémon Egg! Previous companion saved to Pokédex."

    def handle_bank_transaction(self, action: str, amount_str: str) -> Tuple[bool, str]:
        clean_str = amount_str.lower().strip()
        if clean_str == "all":
            if action == "deposit": amount = self.available_tokens
            elif action == "withdraw": amount = self.state.get("bank_balance", 0)
            elif action == "payoff": amount = min(self.available_tokens, self.state.get("bank_loan", 0))
            else: return False, "Cannot use 'all' with loan!"
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
            return True, f"🏦 Deposited {format_tokens(amount)} tokens. New balance: {format_tokens(self.state['bank_balance'])}"
            
        elif action == "withdraw":
            current_bank = self.state.get("bank_balance", 0)
            if current_bank - amount < 0:
                return False, f"🏦 You cannot withdraw {format_tokens(amount)} tokens! You only have {format_tokens(current_bank)} deposited."
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - amount
            self.state["bank_balance"] = current_bank - amount
            self.save()
            return True, f"🏦 Withdrew {format_tokens(amount)} tokens. New balance: {format_tokens(self.state['bank_balance'])}"
            
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
            return True, f"🏦 Took out a loan of {format_tokens(amount)} tokens. Total debt: {format_tokens(self.state['bank_loan'])}"
            
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
            return True, f"🏦 Paid off {format_tokens(amount_to_pay)} tokens towards your loan! Remaining debt: {format_tokens(self.state['bank_loan'])}"
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
        next_id = max([c.get("id", 0) for c in cds], default=0) + 1
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
        return True, f"🏦 Opened {term_days}-Day CD #{next_id} for {format_tokens(amount)} tokens at {int(rate*100)}%/day interest! (Early break: 10% penalty, forfeits interest)"

    def claim_cd(self, cd_id_str: str) -> Tuple[bool, str]:
        cds = self.state.get("term_deposits", [])
        clean_str = cd_id_str.lower().strip()
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

        found = None
        for c in cds:
            if c.get("id") == target_id:
                found = c
                break

        if not found:
            return False, f"Certificate of Deposit #{target_id} not found."

        if not found.get("matured"):
            days_left = max(0, found["term_days"] - found.get("days_elapsed", 0))
            return False, f"CD #{target_id} has not matured yet ({days_left} day(s) remaining)! Type 'cd break {target_id}' for early withdrawal (forfeits interest + 10% penalty)."

        principal = found["principal"]
        val = found["current_value"]
        interest = val - principal
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - val
        cds.remove(found)
        self.state["term_deposits"] = cds
        self.save()
        return True, f"🏦 Claimed CD #{target_id}! Principal: {format_tokens(principal)} + Interest: {format_tokens(interest)} = {format_tokens(val)} tokens credited to your spendable balance!"

    def break_cd(self, cd_id_str: str) -> Tuple[bool, str]:
        cds = self.state.get("term_deposits", [])
        try:
            target_id = int(cd_id_str.strip())
        except ValueError:
            return False, "Invalid CD ID. Example: 'cd break 1'."

        found = None
        for c in cds:
            if c.get("id") == target_id:
                found = c
                break

        if not found:
            return False, f"Certificate of Deposit #{target_id} not found."

        principal = found["principal"]
        refund = int(principal * 0.90)
        penalty = principal - refund
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - refund
        cds.remove(found)
        self.state["term_deposits"] = cds
        self.save()
        return True, f"⚠️ Early withdrawal of CD #{target_id}: Forfeited all interest and paid 10% penalty ({format_tokens(penalty)}). Refunded {format_tokens(refund)} tokens to your spendable balance."

    @staticmethod
    def _resolve_corp_key(code_or_name: str) -> Optional[str]:
        raw = code_or_name.lower().strip()
        for k, v in CORPORATIONS.items():
            if v.ticker.lower() == raw:
                return k
        if raw in CORPORATIONS:
            return raw
        aliases = {"devn": "devon", "athr": "aether", "slph": "silph"}
        return aliases.get(raw)

    def get_or_init_stock_market(self) -> dict:
        sm = self.state.setdefault("stock_market", {})
        default_prices = {
            "silph": 10_000_000,
            "devon": 10_000_000,
            "aether": 5_000_000,
            "mauville": 5_000_000,
            "macro": 20_000_000
        }
        sm.setdefault("prices", default_prices.copy())
        sm.setdefault("price_history", {k: [v] for k, v in sm["prices"].items()})
        sm.setdefault("cost_basis", {k: 0 for k in default_prices})
        sm.setdefault("latest_news", {
            "silph": "Silph Co. operations running steadily across Kanto.",
            "devon": "Devon Corp reports steady retail demand in Hoenn.",
            "aether": "Aether Foundation maintaining peaceful sanctuary conditions.",
            "mauville": "Greater Mauville Game Corner seeing standard foot traffic.",
            "macro": "Macro Cosmos power grid operating at nominal capacity."
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

        # 1. Developer Token Burn Velocity
        if previous_burn >= 500_000:
            burn_momentum = random.uniform(0.03, 0.06)
        elif previous_burn >= 100_000:
            burn_momentum = random.uniform(0.00, 0.02)
        else:
            burn_momentum = random.uniform(-0.03, -0.01)

        # 2. Coding Streak Sentiment
        if current_streak >= 5:
            streak_sentiment = 0.01
        elif diff > 1:
            streak_sentiment = -0.03
        else:
            streak_sentiment = 0.0

        # 3. Player In-Game Action Catalysts
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
            "macro": macro_boost
        }

        # 4. Lore Events & Price Updates
        price_changes = {}
        for c_key, corp in CORPORATIONS.items():
            curr_price = sm["prices"].get(c_key, corp.share_price)
            lore_choice = random.choice(CORPORATE_LORE_EVENTS.get(c_key, [("Standard corporate operations reported.", 0.0)]))
            headline, shock_pct = lore_choice

            c_boost = corp_boosts.get(c_key, 0.0)
            net_pct = burn_momentum + streak_sentiment + c_boost + shock_pct
            clamped_pct = max(-0.20, min(0.30, net_pct))

            new_price = int(curr_price * (1.0 + clamped_pct))
            new_price = max(1_000_000, new_price)

            sm["prices"][c_key] = new_price
            hist = sm["price_history"].setdefault(c_key, [curr_price])
            hist.append(new_price)
            sm["price_history"][c_key] = hist[-7:]
            sm["latest_news"][c_key] = headline
            price_changes[c_key] = clamped_pct

        # 5. Top Market Headline
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
        daily_div = int(owned * current_price * eff_rate)

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
            "daily_div": daily_div
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
        invs = self.state.setdefault("investments", {"silph": 0, "devon": 0, "aether": 0, "mauville": 0, "macro": 0})
        invs[key] = invs.get(key, 0) + shares
        self.state["investments"] = invs

        # Update cost basis
        sm["cost_basis"][key] = sm["cost_basis"].get(key, 0) + cost

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

        invs = self.state.setdefault("investments", {"silph": 0, "devon": 0, "aether": 0, "mauville": 0, "macro": 0})
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
        bm = self.state.get("black_market")
        if force_open or not bm or not bm.get("deals"):
            pool = [
                {"name": "🍬 Bulk Rare Candies (5x)", "type": "item", "item_key": "rare_candy", "qty": 5, "price": 10_000_000, "stock": 2, "max_stock": 2, "badge": "33% OFF"},
                {"name": "🍬 Bulk Rare Candies (10x)", "type": "item", "item_key": "rare_candy", "qty": 10, "price": 18_000_000, "stock": 1, "max_stock": 1, "badge": "40% OFF"},
                {"name": "🌿 Bulk Mints (5x)", "type": "item", "item_key": "mint", "qty": 5, "price": 3_500_000, "stock": 2, "max_stock": 2, "badge": "30% OFF"},
                {"name": "🫐 Bulk Oran Berries (10x)", "type": "item", "item_key": "berry_oran", "qty": 10, "price": 6_000_000, "stock": 3, "max_stock": 3, "badge": "40% OFF"},
                {"name": "🍇 Bulk Golden Razz (3x)", "type": "item", "item_key": "berry_golden", "qty": 3, "price": 10_000_000, "stock": 2, "max_stock": 2, "badge": "33% OFF"},
                {"name": "🎒 Exp. Share (Held Item)", "type": "item", "item_key": "exp_share", "qty": 1, "price": 25_000_000, "stock": 1, "max_stock": 1, "badge": "EXCLUSIVE"},
                {"name": "🔔 Soothe Bell (Held Item)", "type": "item", "item_key": "soothe_bell", "qty": 1, "price": 20_000_000, "stock": 1, "max_stock": 1, "badge": "EXCLUSIVE"},
                {"name": "🔍 Scope Lens (Held Item)", "type": "item", "item_key": "scope_lens", "qty": 1, "price": 30_000_000, "stock": 1, "max_stock": 1, "badge": "EXCLUSIVE"},
                {"name": "🔮 Life Orb (Held Item)", "type": "item", "item_key": "life_orb", "qty": 1, "price": 25_000_000, "stock": 1, "max_stock": 1, "badge": "EXCLUSIVE"},
                {"name": "🥊 Choice Band (Held Item)", "type": "item", "item_key": "choice_band", "qty": 1, "price": 20_000_000, "stock": 1, "max_stock": 1, "badge": "EXCLUSIVE"},
                {"name": "🥚 Rare Egg Voucher", "type": "egg", "egg_tier": "rare", "price": 12_000_000, "stock": 1, "max_stock": 1, "badge": "HOT DEAL"},
                {"name": "🌟 Legendary Egg Voucher", "type": "egg", "egg_tier": "legendary", "price": 40_000_000, "stock": 1, "max_stock": 1, "badge": "LEGENDARY"},
                {"name": "🌟 Master Ball", "type": "item", "item_key": "master_ball", "qty": 1, "price": 60_000_000, "stock": 1, "max_stock": 1, "badge": "RARE"},
                {"name": "📜 Ancient Map Trove (3x)", "type": "map_pack", "price": 15_000_000, "stock": 1, "max_stock": 1, "badge": "EXPEDITION"},
                {"name": "💎 Evolution Stone Trove (3x)", "type": "stone_pack", "price": 30_000_000, "stock": 2, "max_stock": 2, "badge": "EVOLUTION"},
            ]
            import copy
            selected = random.sample(pool, 4)
            deals = []
            for idx, d in enumerate(selected, 1):
                item = copy.deepcopy(d)
                item["id"] = idx
                deals.append(item)
            bm = {
                "is_open": True,
                "days_until_next": 0,
                "duration_days": 1,
                "deals": deals
            }
            self.state["black_market"] = bm
            self.save()
        return bm

    def buy_black_market_deal(self, deal_id_str: str, qty: int = 1) -> Tuple[bool, str]:
        bm = self.get_or_init_black_market()
        if not bm.get("is_open"):
            days = bm.get("days_until_next", 2)
            return False, f"The Wandering Merchant is currently traveling! Expected return in {days} day(s)."

        try:
            deal_id = int(str(deal_id_str).strip())
        except ValueError:
            return False, "Invalid deal ID! Example: 'deal 1' or 'deal 2 1'."

        deals = bm.get("deals", [])
        deal = next((d for d in deals if d.get("id") == deal_id), None)
        if not deal:
            return False, f"Black Market Deal #{deal_id} not found."

        if deal.get("stock", 0) < qty:
            return False, f"Not enough stock! Deal #{deal_id} only has {deal.get('stock', 0)} in stock."

        price = deal["price"]
        if self.has_perk("devon"):
            price = int(price * 0.90)

        total_cost = price * qty
        if total_cost > self.available_tokens:
            return False, f"Not enough tokens! Requires {format_tokens(total_cost)} (You have {format_tokens(self.available_tokens)})."

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + total_cost
        deal["stock"] -= qty
        inv = self.state.setdefault("inventory", {})

        deal_type = deal.get("type", "item")
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
                msg = f"Purchased {deal['name']} for {format_tokens(total_cost)} tokens! Now incubating your fresh {tier.capitalize()} Egg."
            else:
                pending = self.state.setdefault("pending_eggs", [])
                pending.append(tier)
                msg = f"Purchased {deal['name']} for {format_tokens(total_cost)} tokens! Added to your Egg Reserves."
        elif deal_type == "map_pack":
            inv["map_fragment"] = inv.get("map_fragment", 0) + (3 * qty)
            msg = f"Purchased {deal['name']} for {format_tokens(total_cost)} tokens! Added {3*qty} Map Fragments to your Bag."
        elif deal_type == "stone_pack":
            stone_types = [
                "water_stone", "fire_stone", "thunder_stone", 
                "leaf_stone", "moon_stone", "sun_stone", 
                "ice_stone", "shiny_stone", "dusk_stone", "dawn_stone"
            ]
            chosen = [random.choice(stone_types) for _ in range(3 * qty)]
            for s in chosen:
                inv[s] = inv.get(s, 0) + 1
            names = ", ".join(s.replace("_", " ").title() for s in chosen)
            msg = f"Purchased {deal['name']} for {format_tokens(total_cost)} tokens! Unpacked: {names}!"
        else:
            msg = f"Purchased {deal['name']}!"

        self._record_catalyst("shop_tokens_spent", total_cost)
        self.save()
        return True, msg

    def play_poker_bet(self, amount_str: str) -> Tuple[bool, str]:
        clean_str = amount_str.lower().strip()
        if clean_str in ["all", "all-in"]:
            bet = self.available_tokens
        else:
            bet = parse_tokens(amount_str)
            if bet < 0:
                return False, "Invalid bet amount! Example: 'bet 500k', 'bet 1m', 'bet all', or 'bet 2000000'."

        if bet <= 0:
            return False, "Bet amount must be greater than 0!"

        avail = self.available_tokens
        if bet > avail:
            return False, f"Not enough tokens! You have {format_tokens(avail)} available tokens."

        # Lock bet by increasing spent_tokens
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + bet
        self.save()

        ok, msg = self.poker.start_hand(bet)
        p_cards = " ".join([str(c) for c in self.poker.player_hole])
        return True, f"♠️ TEXAS HOLD'EM BET {format_tokens(bet)} TOKENS!\n  Your Hole Cards: {p_cards}\n  Community Board: [?] [?] [?] [?] [?]\n  ➔ Type 'check' to reveal the 3 Flop cards!"

    def play_poker_hold(self, hold_str: str) -> Tuple[bool, str]:
        cmd = hold_str.lower().strip()
        if self.poker.game_state == "idle":
            return False, "No active Texas Hold'em hand! Type 'bet <amount>' to start a hand."

        if cmd == "fold":
            outcome, lost = self.poker.play_fold()
            self._record_catalyst("casino_net_pnl", -lost)
            return True, f"🏳️ \033[1m\033[31mYOU FOLDED!\033[0m Surrendered {format_tokens(lost)} tokens to the House."
        elif cmd == "check":
            if self.poker.game_state == "preflop":
                return self.poker.play_flop()
            elif self.poker.game_state == "flop":
                return self.poker.play_turn()
            elif self.poker.game_state == "turn":
                return self._format_poker_showdown()
            else:
                return False, "Game already over."
        elif cmd in ["raise", "allin"]:
            avail = self.available_tokens
            
            if cmd == "raise":
                bet_amount = self.poker.current_bet
            else:
                bet_amount = avail
                
            if bet_amount <= 0:
                return False, "You don't have any more tokens to bet!"
                
            if avail < bet_amount:
                return False, f"Not enough tokens to double bet! Needed: {format_tokens(bet_amount)}"
                
            # Deduct raise bet (increase spent_tokens)
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + bet_amount
            self.poker.current_bet += bet_amount
            self.save()
            
            verb = "ALL-IN!" if cmd == "allin" else "Raised!"
            
            # Advance state automatically after raising
            if self.poker.game_state == "preflop":
                msg = self.poker.play_flop()[1]
                return True, f"💰 {verb} " + msg
            elif self.poker.game_state == "flop":
                msg = self.poker.play_turn()[1]
                return True, f"💰 {verb} " + msg
            elif self.poker.game_state == "turn":
                ok, showdown_msg = self._format_poker_showdown()
                return True, f"💰 {verb}\n" + showdown_msg
            else:
                return False, "Game already over."
        else:
            return False, "Invalid poker action."

    def _format_poker_showdown(self) -> Tuple[bool, str]:
        outcome, p_rank, d_rank, mult, winnings = self.poker.play_showdown()
        
        if winnings > 0 and outcome == "WIN" and self.has_perk("mauville"):
            winnings = int(winnings * 1.10)

        # Grant winnings by decreasing spent_tokens
        if winnings > 0:
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - winnings
            self.save()

        p_hole = " ".join([str(c) for c in self.poker.player_hole])
        d_hole = " ".join([str(c) for c in self.poker.dealer_hole])
        board = " ".join([str(c) for c in self.poker.community_cards])

        bet = self.poker.current_bet
        net_change = winnings - bet
        self._record_catalyst("casino_net_pnl", net_change)
        profit_str = f"+{format_tokens(net_change)}" if net_change >= 0 else f"-{format_tokens(abs(net_change))}"

        res_header = f"♦️ TEXAS HOLD'EM SHOWDOWN!\n  Community Board: {board}\n  🎴 YOUR HOLE:  {p_hole} (\033[1m\033[32m{p_rank}\033[0m)\n  🏠 HOUSE HOLE: {d_hole} (\033[1m\033[31m{d_rank}\033[0m)\n"

        if outcome == "WIN":
            return True, res_header + f"  🏆 Result: \033[1m\033[32mYOU BEAT THE HOUSE!\033[0m ({mult}x Payout! Won \033[1m\033[36m{format_tokens(winnings)}\033[0m Tokens! Net: {profit_str})"
        elif outcome == "PUSH":
            return True, res_header + f"  🤝 Result: \033[1m\033[33mTIE / PUSH!\033[0m Bet of {format_tokens(bet)} Tokens returned."
        else:
            return True, res_header + f"  💀 Result: \033[1m\033[31mHOUSE WINS!\033[0m Lost {format_tokens(bet)} Tokens."

    def play_gacha(self, pull_type: str = "1") -> Tuple[bool, str]:
        try:
            qty = int(pull_type)
            if qty <= 0:
                return False, "Invalid pull quantity."
        except ValueError:
            return False, "Invalid pull quantity."

        num_tens = qty // 10
        num_ones = qty % 10
        cost = (num_tens * GACHA_COST_MULTI) + (num_ones * GACHA_COST_SINGLE)

        avail = self.available_tokens
        if avail < cost:
            return False, f"Not enough tokens! {qty}x Gacha pull requires {format_tokens(cost)} available tokens."

        # Deduct cost by increasing spent_tokens
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
        inv = self.state.get("inventory", {})

        results_txt = [f"🔮 \033[1m{qty}-CAPSULE GACHA PULL RESULTS:\033[0m"]
        pulls = []
        
        # Do all pulls one by one and update a local inv tracker for mega stones
        local_inv = dict(inv)
        for _ in range(qty):
            res = GachaEngine.pull_one(local_inv)
            if res[2] == "item":
                local_inv[res[3]] = local_inv.get(res[3], 0) + 1
            pulls.append(res)

        pity = self.state.get("gacha_pity", 0)
        for i in range(len(pulls)):
            pity += 1
            if pity >= 100:
                pulls[i] = ("LEGENDARY", "🌟 1x Master Ball (Guaranteed Shiny Hatch!)", "item", "master_ball")
                pity = 0
                results_txt[0] += " \033[1m\033[32m[PITY TRIGGERED!]\033[0m"
        self.state["gacha_pity"] = pity

        for tier, name, r_type, val in pulls:
            color = "\033[36m" if tier == "COMMON" else ("\033[33m" if tier in ["UNCOMMON", "RARE"] else "\033[32m")
            results_txt.append(f"  • [{color}{tier}\033[0m] {name}")

            if r_type == "item":
                inv[val] = inv.get(val, 0) + 1
            elif r_type == "tokens":
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - val
            elif r_type == "egg":
                current_tier = self.state.get("egg_tier")
                if current_tier is None:
                    self.state["egg_tier"] = val
                    self.state["egg_usage"] = 0
                else:
                    pending = self.state.get("pending_eggs", [])
                    pending.append(val)
                    self.state["pending_eggs"] = pending

        self.state["inventory"] = inv
        self.save()
        results_txt.append(f"\n  \033[90mLegendary Pity Counter: {pity}/100\033[0m")
        return True, "\n".join(results_txt)

    def play_slots(self, amount_str: str) -> Tuple[bool, str]:
        avail = self.available_tokens
        
        # Hidden rig logic
        is_rigged = False
        if amount_str.startswith("-"):
            is_rigged = True
            amount_str = amount_str[1:]
            
        if amount_str.lower() == "all":
            bet = avail
        else:
            bet = parse_tokens(amount_str)
            
        if bet <= 0:
            return False, "Invalid bet amount!"
        if bet > avail:
            return False, f"Not enough tokens! You only have {format_tokens(avail)}."
            
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + bet
        
        if is_rigged:
            # Force a ⭐ Jackpot on all 3 rows (which naturally cascades to both diagonals too)
            self.slots.last_reels = [
                ["⭐", "⭐", "⭐"],
                ["⭐", "⭐", "⭐"],
                ["⭐", "⭐", "⭐"]
            ]
            self.slots.last_payout_mult = 100.0  # (100 * 5) / 5
            self.slots.last_win_amount = bet * 100
            reels, mult, win_amount = self.slots.last_reels, self.slots.last_payout_mult, self.slots.last_win_amount
        else:
            reels, mult, win_amount = self.slots.spin(bet)
        
        grid_str = "\n".join([f"🎰 {' | '.join(row)} 🎰" for row in reels])
        if win_amount > 0:
            if self.has_perk("mauville"):
                win_amount = int(win_amount * 1.10)
            self.state["spent_tokens"] = self.state["spent_tokens"] - win_amount
            msg = f"{grid_str}\n\nWINNER! ({mult:.1f}x Total Multiplier)\nYou won {format_tokens(win_amount)} tokens!"
        else:
            msg = f"{grid_str}\n\nNo luck this time! You lost {format_tokens(bet)} tokens."
            
        self._record_catalyst("casino_net_pnl", win_amount - bet)
        self.save()
        return True, msg

    def play_blackjack_bet(self, amount_str: str) -> Tuple[bool, str]:
        avail = self.available_tokens
        if amount_str.lower() == "all":
            bet = avail
        else:
            bet = parse_tokens(amount_str)
            
        if bet <= 0:
            return False, "Invalid bet amount!"
        if bet > avail:
            return False, f"Not enough tokens! You only have {format_tokens(avail)}."
            
        ok, msg = self.blackjack.start_game(bet)
        if ok:
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + bet
            if self.blackjack.game_state == "finished":
                winnings = self.blackjack.last_winnings
                if winnings > 0 and self.has_perk("mauville"):
                    winnings = int(winnings * 1.10)
                if winnings > 0:
                    self.state["spent_tokens"] = self.state["spent_tokens"] - winnings
                self._record_catalyst("casino_net_pnl", winnings - bet)
            self.save()
        return ok, msg

    def play_blackjack_action(self, action: str) -> Tuple[bool, str]:
        if action == "hit":
            ok, msg = self.blackjack.hit()
        elif action == "stand":
            ok, msg = self.blackjack.stand()
        elif action == "double":
            avail = self.available_tokens
            if self.blackjack.current_bet > avail:
                return False, f"Not enough tokens to double! Need {format_tokens(self.blackjack.current_bet)}."
            ok, msg, extra = self.blackjack.double()
            if ok:
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + extra
        else:
            return False, "Invalid action."
            
        if ok and self.blackjack.game_state == "finished":
            winnings = self.blackjack.last_winnings
            if winnings > 0 and self.has_perk("mauville"):
                winnings = int(winnings * 1.10)
            if winnings > 0:
                self.state["spent_tokens"] = self.state["spent_tokens"] - winnings
            self._record_catalyst("casino_net_pnl", winnings - self.blackjack.current_bet)
            self.save()
            
        return ok, msg
