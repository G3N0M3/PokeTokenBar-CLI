import random
import datetime
from typing import Dict, List, Optional, Tuple, Any

from poketokenbar.game.models import (
    MonState, DexEntry, Rarity, PokemonNature, PokemonBalance, ItemKind, DifficultyMode
)
from poketokenbar.game.pokeapi import PokeAPIClient
from poketokenbar.game.storage import StorageManager
from poketokenbar.utils.formatting import format_tokens, parse_tokens

from poketokenbar.game.poker import TexasHoldemEngine
from poketokenbar.game.slots import SlotMachineEngine
from poketokenbar.game.blackjack import BlackjackEngine
from poketokenbar.game.gacha import GachaEngine, GACHA_COST_SINGLE, GACHA_COST_MULTI

# Gen 1-5 starters/base species sampling fallback table if offline
BASE_SPECIES_STARTERS = [
    # Gen 1
    (1, "Bulbasaur", 45, False), (4, "Charmander", 45, False), (7, "Squirtle", 45, False),
    (10, "Caterpie", 255, False), (13, "Weedle", 255, False), (16, "Pidgey", 255, False),
    (19, "Rattata", 255, False), (25, "Pikachu", 190, False), (37, "Vulpix", 190, False),
    (43, "Oddish", 255, False), (54, "Psyduck", 190, False), (58, "Growlithe", 190, False),
    (60, "Poliwag", 255, False), (63, "Abra", 200, False), (66, "Machop", 180, False),
    (92, "Gastly", 190, False), (129, "Magikarp", 255, False), (133, "Eevee", 45, False),
    (147, "Dratini", 45, False), (144, "Articuno", 3, True), (150, "Mewtwo", 3, True),
    # Gen 2
    (152, "Chikorita", 45, False), (155, "Cyndaquil", 45, False), (158, "Totodile", 45, False),
    (172, "Pichu", 190, False), (179, "Mareep", 235, False), (246, "Larvitar", 45, False),
    (249, "Lugia", 3, True), (250, "Ho-Oh", 3, True),
    # Gen 3
    (252, "Treecko", 45, False), (255, "Torchic", 45, False), (258, "Mudkip", 45, False),
    (280, "Ralts", 235, False), (371, "Bagon", 45, False), (384, "Rayquaza", 3, True),
    # Gen 4
    (387, "Turtwig", 45, False), (390, "Chimchar", 45, False), (393, "Piplup", 45, False),
    (443, "Gible", 45, False), (483, "Dialga", 3, True), (484, "Palkia", 3, True),
    # Gen 5
    (495, "Snivy", 45, False), (498, "Tepig", 45, False), (501, "Oshawott", 45, False),
    (570, "Zorua", 75, False), (633, "Deino", 45, False), (643, "Reshiram", 3, True)
]

class CompanionEngine:
    """Manages active Pokémon companion, hatching, evolution, Pokédex, and inventory."""

    def __init__(self):
        self.api = PokeAPIClient()
        self.state = StorageManager.load_state()
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
            decay_rate = 800_000 if active.held_item == "choice_scarf" else 1_000_000
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
            self.save()
        else:
            active.used_at_stage += effective_xp

            # Check evolution / graduation threshold
            target_xp = PokemonBalance.phase_threshold(active.rarity, active.total_forms, active.stage_index, self.current_difficulty)
            
            # Check if this stage has already evolved into next stage
            dex = self.state.get("dex", [])
            discovered_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))) for d in dex}
            is_already_evolved = (active.stage_index < len(active.path_ids) - 1) and (active.path_ids[active.stage_index + 1] in discovered_sp_ids)
            self.set_active_mon(active)
            evo_events = self._check_growth(active)
            events.extend(evo_events)

        # Check achievements
        ach_events = self._check_achievements()
        events.extend(ach_events)

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

                        if bank_loan > 0:
                            new_loan = bank_loan
                            for _ in range(days_to_apply):
                                new_loan = int(new_loan * 1.10)
                            events.append(f"🏦 Your Token Bank loan accumulated {format_tokens(new_loan - bank_loan)} tokens in interest!")
                            self.state["bank_loan"] = new_loan
                            
                            loan_days = self.state.get("loan_days_active", 0) + days_to_apply
                            self.state["loan_days_active"] = loan_days
                            
                            if loan_days >= 8:
                                remaining_loan = new_loan
                                
                                # 1. Confiscate from Bank Balance
                                bank_bal = self.state.get("bank_balance", 0)
                                take_from_bank = min(bank_bal, remaining_loan)
                                self.state["bank_balance"] -= take_from_bank
                                remaining_loan -= take_from_bank
                                
                                # 2. Confiscate from Available Tokens
                                avail_tokens = self.state.get("used_since_install", 0) - self.state.get("spent_tokens", 0)
                                take_from_avail = min(avail_tokens, remaining_loan)
                                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + take_from_avail
                                remaining_loan -= take_from_avail
                                
                                # 3. Liquidate Bag
                                if remaining_loan > 0:
                                    inv = self.state.get("inventory", {})
                                    items_to_sell = list(inv.keys())
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
                                    
                                events.append("🚨 BANK REPOSSESSION! 8 days have passed! The bank seized tokens and liquidated items to cover your debt, reducing ALL roster companions' happiness by 50%!")

                    if diff == 1:
                        if active:
                            bonus = 15 if active.held_item == "leftovers" else 10
                            active.happiness = min(100, active.happiness + bonus)
                            self.set_active_mon(active)
                    elif diff > 1:
                        if active and active.held_item == "leftovers":
                            events.append(f"🍎 Your companion missed {diff-1} day(s), but was snacking on Leftovers! Happiness preserved!")
                        else:
                            decay = (diff - 1) * 25
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
            self.save()

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
            {"id": "boss_8", "name": "Giovanni & Mewtwo", "sp_id": 150, "badge": "👑 Earth Badge", "threshold": 180_000_000, "hp": 60_000_000, "reward": "master_ball"},
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
            active_boss["current_hp"] -= damage
            if active_boss["current_hp"] <= 0:
                active_boss["current_hp"] = 0
                badge = active_boss["badge"]
                b_name = active_boss["name"]
                gym_badges.add(badge)
                self.state["gym_badges"] = list(gym_badges)

                # Grant reward
                r_type = active_boss["reward"]
                inv = self.state.get("inventory", {})
                is_mega = active and active.is_mega
                multiplier = 1.5 if is_mega else 1.0
                
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

        # If this stage has ALREADY evolved into the next stage, cap XP at 100% max and do not re-trigger evolution
        if mon.stage_index < len(mon.path_ids) - 1:
            next_id = mon.path_ids[mon.stage_index + 1]
            if next_id in discovered_sp_ids or mon.held_item == "everstone":
                mon.used_at_stage = target_xp
                self.set_active_mon(mon)
                return events

        while mon.used_at_stage >= target_xp:
            if mon.stage_index < len(mon.path_ids) - 1:
                # Evolve to next stage!
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
                events.append(f"🎉 Evolution! Your companion evolved into {shiny_str}{mon_name} (#{new_id})!")
                events.extend(self._progress_quest_by_type("progression"))
                self._register_to_dex(mon, status="active")
                target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, mon.stage_index, diff)
            else:
                # Final form + reached graduation threshold!
                mon_name = self.api.get_species_name(mon.current_id)
                shiny_str = "✨ Shiny " if mon.is_shiny else ""
                events.append(f"🎓 Graduation! {shiny_str}{mon_name} has graduated to your Pokédex!")

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
        exp_map = {e["sp_id"]: e for e in expeditions}
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

        if target_entry is None:
            return False, f"Pokémon '{selection_input}' not found in Roster or Pokédex! Use roster index (1..{len(roster)}) or species ID (e.g. #570)."

        sp_id = target_entry.get("species_id", target_entry.get("base_id"))
        sp_name = self.api.get_species_name(sp_id)

        # Prevent selecting a companion currently on an expedition
        expeditions = self.state.get("expeditions", [])
        if any(e["sp_id"] == sp_id for e in expeditions):
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
        if tier_guarantee == "legendary":
            candidates = [c for c in BASE_SPECIES_STARTERS if c[3]]
        else:
            candidates = [c for c in BASE_SPECIES_STARTERS if not c[3]]
            if tier_guarantee:
                req_rank = Rarity(tier_guarantee).sort_rank
                candidates = [c for c in candidates if Rarity.from_capture_rate(c[2], c[3]).sort_rank >= req_rank]
                if not candidates:
                    candidates = [c for c in BASE_SPECIES_STARTERS if not c[3]]

        # Block spawning of Pokemon already in the roster (active or inactive)
        dex = self.state.get("dex", [])
        roster_base_ids = {d.get("base_id") for d in dex if d.get("status") in ["active", "inactive"]}
        filtered_candidates = [c for c in candidates if c[0] not in roster_base_ids]
        
        # Fallback if somehow they have all possible Pokemon in the roster
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
            self.save()
            return True, f"Successfully purchased {qty}x Mystery Mega Stone! You unboxed: 🔮 {stone_name}!"

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
        inv[item_kind.value] = inv.get(item_kind.value, 0) + qty
        self.state["inventory"] = inv
        self.save()
        return True, f"Successfully purchased {qty}x {item_kind.name_en} ({item_kind.emoji})!"

    def sell_item(self, item_kind: ItemKind, qty: int = 1) -> Tuple[bool, str]:
        if qty <= 0:
            return False, "Quantity must be greater than 0!"
            
        inv = self.state.get("inventory", {})
        
        if item_kind == ItemKind.MEGA_STONE:
            target_key = "mega_stone"
            target_name = "Universal Mega Stone"
            if inv.get("mega_stone", 0) < qty:
                target_key = None
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
            self.save()
            active_name = self.api.get_species_name(active.current_id)
            return True, f"Fed {qty}x Rare Candy to {active_name}! (+{format_tokens(xp_grant)} XP)"
            
        elif item_kind in [ItemKind.EVERSTONE, ItemKind.LUCKY_EGG, ItemKind.AMULET_COIN, ItemKind.LEFTOVERS, ItemKind.CHOICE_SCARF]:
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
                ItemKind.CHOICE_SCARF: "It will now complete expeditions 20% faster, but drain happiness faster!"
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
            remaining_xp = exp["target"] - exp["progress"]
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
                {"id": "boss_8", "name": "Giovanni & Mewtwo", "sp_id": 150, "badge": "👑 Earth Badge", "hp": 60_000_000, "reward": "master_ball"},
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
        has_universal = inv.get("mega_stone", 0) > 0
        
        if f"{sp_id}_X" in MEGA_STONES and (inv.get(f"mega_stone_{sp_id}_X", 0) > 0 or has_universal):
            owned_forms.append("X")
        if f"{sp_id}_Y" in MEGA_STONES and (inv.get(f"mega_stone_{sp_id}_Y", 0) > 0 or has_universal):
            owned_forms.append("Y")
        if sp_id in MEGA_STONES and (inv.get(f"mega_stone_{sp_id}", 0) > 0 or has_universal):
            owned_forms.append("Normal")
            
        if not owned_forms:
            return False, f"You need a corresponding Mega Stone 🔮 to Mega Evolve {self.api.get_species_name(active.current_id)}!"
            
        if target_stone_key and target_stone_key != "mega_stone":
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
            sp_id = exp["sp_id"]
            sp_name = self.api.get_species_name(sp_id)
            area = exp["area"]
            reward = exp["reward"]

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
                logs.append(f"[{now_str}] 🗺️ {sp_name}: {reward_str} | +{format_tokens(tokens_gain)} 🪙 | +{format_tokens(xp_gain)} XP")
                self.state["expedition_logs"] = logs[-5:]
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
        exp["progress"] = exp["target"]
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

    def dispatch_expedition(self, selection_input: str, area_name: str = "Viridian Forest") -> Tuple[bool, str]:
        dex = self.state.get("dex", [])
        if not dex:
            return False, "Your Pokédex is empty! Register companions before dispatching expeditions."

        expeditions = self.state.get("expeditions", [])
        exp_map = {e["sp_id"]: e for e in expeditions}
        all_discovered_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))) for d in dex}
        roster = []
        for d in dex:
            if d.get("status") == "evolved":
                continue
            sp_id = d.get("species_id", d.get("final_id", d.get("base_id")))
            chain = d.get("chain_order", [])
            if chain and sp_id in chain:
                idx_in_chain = chain.index(sp_id)
                higher_forms = [h for h in chain[idx_in_chain + 1:] if h in all_discovered_sp_ids]
                if higher_forms:
                    continue
            roster.append(d)

        s_input = selection_input.strip()
        target_entry = None

        # 1. If starts with '#', match strictly by species_id within ROSTER
        if s_input.startswith("#"):
            target_sp = s_input[1:]
            for d in roster:
                sp_id = str(d.get("species_id", d.get("base_id")))
                if target_sp == sp_id:
                    target_entry = d
                    break
        else:
            # 2. Try matching by 1-based index in ROSTER (matching Tab 3)
            try:
                idx = int(s_input)
                if 1 <= idx <= len(roster):
                    target_entry = roster[idx - 1]
            except ValueError:
                pass

            # 3. Fallback to species_id match within ROSTER
            if target_entry is None:
                for d in roster:
                    sp_id = str(d.get("species_id", d.get("base_id")))
                    if s_input == sp_id:
                        target_entry = d
                        break

        if target_entry is None:
            return False, f"Companion '{selection_input}' not found in Roster! Only active companions in your Roster can be dispatched on expeditions (use roster index 1..{len(roster)} or species ID)."

        sp_id = target_entry.get("species_id", target_entry.get("base_id"))
        sp_name = self.api.get_species_name(sp_id)

        # Check if active companion (comparing base_id)
        active = self.active_mon
        is_mega_dispatch = False
        if active and active.base_id == target_entry.get("base_id"):
            is_mega_dispatch = active.is_mega
            self._register_to_dex(active, status="inactive")
            self.set_active_mon(None)

        # Check if already on expedition
        if any(e["sp_id"] == sp_id for e in expeditions):
            return False, f"{sp_name} is already on an expedition!"

        mon_state_dict = target_entry.get("mon_state", {})
        current_hap = mon_state_dict.get("happiness", target_entry.get("happiness", 100)) if isinstance(mon_state_dict, dict) else target_entry.get("happiness", 100)
        
        if current_hap <= 0:
            return False, f"{sp_name} is completely exhausted (0% Happiness) and refuses to go on an expedition! Please feed it Oran Berries 🫐 first."
            
        slot_limit = self.state.get("expedition_slots", 10)
        if len(expeditions) >= slot_limit:
            return False, f"You have reached the maximum limit of {slot_limit} active expeditions! You must wait for them to finish or use an Expedition License (📜) to expand your slots."

        from poketokenbar.game.models import PokemonBalance
        areas = {
            "viridian": ("Viridian Forest", PokemonBalance.EXPEDITION_VIRIDIAN, "mint"),
            "cerulean": ("Cerulean Cave", PokemonBalance.EXPEDITION_CERULEAN, "rare_candy"),
            "silver": ("Mt. Silver", PokemonBalance.EXPEDITION_SILVER, "berry_golden"),
            "spear": ("Spear Pillar (Deep)", PokemonBalance.EXPEDITION_SPEAR_PILLAR, "legendary_egg")
        }

        key = area_name.lower().split()[0]
        if key == "spear":
            inv = self.state.get("inventory", {})
            if inv.get("map_fragment", 0) < 3:
                return False, "You need 3x Maps to dispatch a Deep Expedition to Spear Pillar!"
            
            mon_state_dict = target_entry.get("mon_state", {})
            hap = mon_state_dict.get("happiness", target_entry.get("happiness", 100)) if isinstance(mon_state_dict, dict) else target_entry.get("happiness", 100)
            if hap < 100:
                return False, "Only a companion with 100% Happiness can brave a Deep Expedition to Spear Pillar!"
            inv["map_fragment"] -= 3
            self.state["inventory"] = inv

        area_tuple = areas.get(key, ("Viridian Forest", 5_000_000, "mint"))
        area_title, target_xp, reward_type = area_tuple

        target_entry["happiness"] = max(0, target_entry.get("happiness", 100) - 10)

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
        mon_str = f"{self.api.get_species_name(active.current_id)} (#{active.current_id})" if active else "Incubating Egg"

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
        
        # Grant winnings by decreasing spent_tokens
        if winnings > 0:
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - winnings
            self.save()

        p_hole = " ".join([str(c) for c in self.poker.player_hole])
        d_hole = " ".join([str(c) for c in self.poker.dealer_hole])
        board = " ".join([str(c) for c in self.poker.community_cards])

        bet = self.poker.current_bet
        net_change = winnings - bet
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
            self.state["spent_tokens"] = self.state["spent_tokens"] - win_amount
            msg = f"{grid_str}\n\nWINNER! ({mult:.1f}x Total Multiplier)\nYou won {format_tokens(win_amount)} tokens!"
        else:
            msg = f"{grid_str}\n\nNo luck this time! You lost {format_tokens(bet)} tokens."
            
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
            if self.blackjack.game_state == "finished" and self.blackjack.last_winnings > 0:
                self.state["spent_tokens"] = self.state["spent_tokens"] - self.blackjack.last_winnings
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
            if self.blackjack.last_winnings > 0:
                self.state["spent_tokens"] = self.state["spent_tokens"] - self.blackjack.last_winnings
            self.save()
            
        return ok, msg
