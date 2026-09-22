import json
import datetime
from typing import Dict, List, Optional, Tuple, Any, Union, Set

from poketokenbar.game.models import (
    MonState, DexEntry, Rarity, PokemonBalance, ItemKind,
)
from poketokenbar.game.pokeapi import PokeAPIClient
from poketokenbar.game.storage import StorageManager
from poketokenbar.game.poker import TexasHoldemEngine
from poketokenbar.game.slots import SlotMachineEngine
from poketokenbar.game.blackjack import BlackjackEngine

from poketokenbar.game.companion.hatching import HatchingMixin
from poketokenbar.game.companion.evolution import EvolutionMixin
from poketokenbar.game.companion.feeding import FeedingMixin
from poketokenbar.game.companion.items import ItemsMixin
from poketokenbar.game.companion.expeditions import ExpeditionsMixin
from poketokenbar.game.companion.profile import ProfileMixin
from poketokenbar.game.companion.markets import MarketsMixin
from poketokenbar.game.companion.casino import CasinoMixin
from poketokenbar.game.companion.rocket import RocketMixin
from poketokenbar.game.economy.banking import BankingMixin


class CompanionEngine(
    HatchingMixin,
    EvolutionMixin,
    FeedingMixin,
    ItemsMixin,
    ExpeditionsMixin,
    BankingMixin,
    MarketsMixin,
    CasinoMixin,
    ProfileMixin,
    RocketMixin,
):
    """Manages active Pokémon companion, hatching, evolution, Pokédex, and inventory."""

    def __init__(self):
        self.api = PokeAPIClient()
        self.state = StorageManager.load_state()

        # Migrate Earth Badge from crown to globe
        if "gym_badges" in self.state:
            self.state["gym_badges"] = [b.replace("👑 Earth Badge", "🌍 Earth Badge") for b in self.state["gym_badges"]]
        if "active_boss" in self.state and self.state["active_boss"] and "badge" in self.state["active_boss"]:
            self.state["active_boss"]["badge"] = self.state["active_boss"]["badge"].replace("👑 Earth Badge", "🌍 Earth Badge")

        # Prune obsolete mint from inventory and migrate active expeditions / bosses / quests
        inv = self.state.get("inventory", {})
        if "mint" in inv:
            del inv["mint"]
        if isinstance(inv.get("items"), dict) and "mint" in inv["items"]:
            del inv["items"]["mint"]
        for exp in self.state.get("expeditions", []):
            if exp.get("reward") == "mint":
                exp["reward"] = "rare_candy"
        if "active_boss" in self.state and self.state["active_boss"]:
            if self.state["active_boss"].get("reward") == "mint":
                self.state["active_boss"]["reward"] = "rare_candy"
        if "daily_quests" in self.state and isinstance(self.state["daily_quests"], dict):
            for q in self.state["daily_quests"].get("quests", []):
                if q.get("reward") == "mint":
                    q["reward"] = "rare_candy"

        self.poker = TexasHoldemEngine()
        self.blackjack = BlackjackEngine()
        self.slots = SlotMachineEngine()

        self._last_saved_state_str = json.dumps(self.state, sort_keys=True)

        if "install_date" not in self.state:
            dex = self.state.get("dex", [])
            caught_dates = [d.get("caught_at", "")[:10] for d in dex if d.get("caught_at")]
            self.state["install_date"] = min(caught_dates) if caught_dates else datetime.datetime.now().strftime("%Y-%m-%d")
            self.save()

        # Migrate Rocket expansion state
        ops_state = self.state.setdefault("rocket_ops", {})
        boss_hps = {3: 150_000, 6: 200_000, 9: 300_000, 10: 350_000}
        b_st = self.state.get("rocket_battle_state", {})
        for i in range(1, 11):
            key = f"op_{i}"
            expected_hp = boss_hps.get(i, 0)
            if key not in ops_state:
                ops_state[key] = {
                    "status": "available" if i == 1 else "locked",
                    "progress": 0,
                    "claimed": False,
                    "objective_done": False,
                    "boss_hp_remaining": expected_hp,
                    "briefing_viewed": False,
                    "expeditions_done": 0,
                    "battle_wins": 0,
                    "black_market_trades": 0
                }
            else:
                ops_state[key].setdefault("objective_done", False)
                ops_state[key].setdefault("expeditions_done", 0)
                ops_state[key].setdefault("battle_wins", 0)
                ops_state[key].setdefault("black_market_trades", 0)
                if ops_state[key].get("claimed", False):
                    ops_state[key].setdefault("briefing_viewed", True)
                    ops_state[key].setdefault("boss_hp_remaining", 0)
                else:
                    ops_state[key].setdefault("briefing_viewed", False)
                    if i in boss_hps:
                        has_won = (b_st.get("status") == "win" and str(b_st.get("op_code")) == str(i))
                        if not has_won:
                            ops_state[key]["objective_done"] = False
                            if ops_state[key].get("boss_hp_remaining", 0) <= 0:
                                ops_state[key]["boss_hp_remaining"] = expected_hp
                        else:
                            ops_state[key]["objective_done"] = True
                            ops_state[key]["boss_hp_remaining"] = 0
                    else:
                        ops_state[key].setdefault("boss_hp_remaining", 0)

        # Unlock ops sequentially if preceding is claimed
        for i in range(1, 10):
            if ops_state.get(f"op_{i}", {}).get("claimed", False):
                nxt = f"op_{i+1}"
                if nxt in ops_state and ops_state[nxt].get("status") == "locked":
                    ops_state[nxt]["status"] = "available"
                    nxt_num = i + 1
                    if nxt_num in boss_hps and not ops_state[nxt].get("claimed", False):
                        ops_state[nxt]["boss_hp_remaining"] = boss_hps[nxt_num]
                        ops_state[nxt]["objective_done"] = False

        rep = sum(1 for v in ops_state.values() if v.get("claimed", False))
        self.state["rocket_reputation"] = rep
        if "rocket_alliance_accepted" not in self.state:
            self.state["rocket_alliance_accepted"] = bool(self.state.get("rocket_story_viewed", False))

        if rep >= 10: rank = "Commander"
        elif rep >= 8: rank = "Executive"
        elif rep >= 5: rank = "Special Agent"
        elif rep >= 2: rank = "Operative"
        else: rank = "Informant"
        self.state["rocket_rank"] = rank

        # Auto-grant permanent clearance perks based on rank
        rank_order = {"Informant": 1, "Operative": 2, "Special Agent": 3, "Executive": 4, "Commander": 5}
        cur_lvl = rank_order.get(rank, 1)
        if cur_lvl >= 1 and self.state.get("rocket_alliance_accepted", False):
            self.state["permanent_black_market"] = True
        if cur_lvl >= 3:
            self.state["has_exp_splitter"] = True

        unlocked_intel = self.state.setdefault("rocket_intel_unlocked", [])
        if "intel_red_autopsy" in unlocked_intel and "intel_001" not in unlocked_intel:
            unlocked_intel.append("intel_001")
        if not unlocked_intel:
            unlocked_intel.append("intel_001")

        # Migrate graduation status for active mon and dex
        collected = set(self.state.get("collected_finals", []))
        active = self.active_mon
        if active and f"{active.base_id}_{active.current_id}" in collected:
            if not getattr(active, "is_graduated", False):
                active.is_graduated = True
                self.set_active_mon(active)

        for d in self.state.get("dex", []):
            sp_id = d.get("species_id", d.get("final_id", d.get("base_id")))
            base_id = d.get("base_id", sp_id)
            if f"{base_id}_{sp_id}" in collected:
                m_st = d.get("mon_state")
                if isinstance(m_st, dict):
                    m_st["is_graduated"] = True
                if d.get("status") not in ["active", "evolved"]:
                    d["status"] = "graduated"

            # Synchronize outer happiness key with mon_state happiness
            m_st = d.get("mon_state")
            if isinstance(m_st, dict) and "happiness" in m_st:
                d["happiness"] = m_st["happiness"]

        # Restore Charizard's happiness if it was zeroed by the Spear Pillar dispatch bug
        for d in self.state.get("dex", []):
            if d.get("species_id") == 6:
                m_st = d.get("mon_state")
                if isinstance(m_st, dict) and m_st.get("happiness") == 0:
                    recent_logs = " ".join(self.state.get("expedition_logs", []))
                    if "Charizard" in recent_logs and "LEGENDARY EGG" in recent_logs:
                        m_st["happiness"] = 90
                        d["happiness"] = 90
                        self.save()

        # Enforce maximum of 1 stone per Mega Stone in inventory
        inv = self.state.get("inventory", {})
        mega_clamped = False
        for k in list(inv.keys()):
            if k.startswith("mega_stone_") and inv[k] > 1:
                inv[k] = 1
                mega_clamped = True
        if mega_clamped:
            self.save()

        # Migrate last_milestone and sync desynced freshly hatched active companion
        if "last_milestone" not in self.state and self.state.get("last_evolution"):
            self.state["last_milestone"] = self.state["last_evolution"]

        act = self.active_mon
        if act and act.stage_index == 0:
            act_name = self.api.get_species_name(act.current_id)
            curr_last = self.state.get("last_evolution", "")
            if curr_last and act_name not in curr_last and "hatched" not in curr_last.lower():
                shiny_str = "✨ Shiny " if act.is_shiny else ""
                hatch_msg = f"Egg Hatched! You got a {shiny_str}{act_name} (#{act.base_id})!"
                self.state["last_evolution"] = hatch_msg
                self.state["last_milestone"] = hatch_msg
                self.save()

        # Purge legacy 'nature' fields from state if present
        cleaned_nature = False
        act_dict = self.state.get("active_mon")
        if isinstance(act_dict, dict) and "nature" in act_dict:
            act_dict.pop("nature", None)
            cleaned_nature = True
        for d in self.state.get("dex", []):
            if isinstance(d, dict):
                if "nature" in d:
                    d.pop("nature", None)
                    cleaned_nature = True
                m_st = d.get("mon_state")
                if isinstance(m_st, dict) and "nature" in m_st:
                    m_st.pop("nature", None)
                    cleaned_nature = True
        self.state.setdefault("cd_sort_criteria", "days")
        if cleaned_nature:
            self.save()

    def save(self):
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
    def current_difficulty(self):
        class DefaultBalanceConfig:
            hatch_threshold = 1_500_000
            shop_prices = {
                "rare_candy": 5_000_000,
                "egg_normal": 10_000_000,
                "egg_uncommon": 25_000_000,
                "egg_rare": 50_000_000,
            }
            graduation_totals = {
                Rarity.COMMON: 50_000_000,
                Rarity.UNCOMMON: 125_000_000,
                Rarity.RARE: 250_000_000,
                Rarity.LEGENDARY: 500_000_000,
                Rarity.MEGA: 1_000_000_000,
            }
        return DefaultBalanceConfig()

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
                decay_shield, _ = self.get_aether_perks()
                decay_rate = int(base_decay * decay_shield)
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
            if egg_tier is not None:
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
                                sub_evos = self._check_growth(sub_mon, is_active=False)
                                events.extend(sub_evos)
                                d["mon_state"] = StorageManager.mon_to_dict(sub_mon)

        # Check Corrupted EXP Splitter armory item
        if self.state.get("has_exp_splitter", False) and effective_xp > 0:
            splitter_xp = int(effective_xp * 0.25)
            active_base = active.base_id if active else None
            dex = self.state.get("dex", [])
            for d in dex:
                if d.get("status") not in ["graduated", "evolved"]:
                    m_data = d.get("mon_state")
                    if m_data:
                        sub_mon = StorageManager.dict_to_mon(m_data)
                        if sub_mon and (active_base is None or sub_mon.base_id != active_base):
                            sub_mon.used_at_stage += splitter_xp
                            sub_evos = self._check_growth(sub_mon, is_active=False)
                            events.extend(sub_evos)
                            d["mon_state"] = StorageManager.mon_to_dict(sub_mon)

        # Update active Rocket Operation progress (tracks raw coding tokens delta)
        if delta > 0 and self.state.get("rocket_story_unlocked", False):
            self._update_rocket_operations(delta, events)

        # Check for Rocket story unlock
        unlocked, alert_msg = self.check_rocket_story_unlock()
        if unlocked and alert_msg:
            events.append(alert_msg)

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
        elif delta > 0:
            self.save()

        return events

    def get_settings(self) -> dict:
        st = self.state.setdefault("settings", {})
        st.setdefault("auto_tracking_enabled", True)
        st.setdefault("refresh_interval", 3.0)
        return st

    def update_settings(self, auto_tracking_enabled: Optional[bool] = None, refresh_interval: Optional[float] = None) -> Tuple[bool, str]:
        st = self.get_settings()
        if auto_tracking_enabled is not None:
            st["auto_tracking_enabled"] = bool(auto_tracking_enabled)
        if refresh_interval is not None:
            try:
                val = float(refresh_interval)
                if val < 0.5:
                    return False, "Refresh interval must be at least 0.5 seconds."
                st["refresh_interval"] = val
            except (ValueError, TypeError):
                return False, "Invalid refresh interval number."
        self.save()
        return True, f"Refresh interval set to {st['refresh_interval']} seconds."

    def set_billing_cycle_day(self, day: int) -> Tuple[bool, str]:
        """Sets the day of the month (1-31) when the monthly token cycle starts."""
        try:
            val = int(day)
            if not (1 <= val <= 31):
                return False, "Billing cycle day must be between 1 and 31."
            self.state["billing_cycle_day"] = val
            self.save()
            return True, f"Monthly billing cycle anchor set to Day {val} of each month."
        except (ValueError, TypeError):
            return False, "Invalid day. Please specify a number between 1 and 31."

    def get_billing_cycle_day(self) -> int:
        return self.state.get("billing_cycle_day", 1)

    def initialize_total_tokens(self, raw_total: int, date_str: Optional[str] = None) -> Tuple[bool, str]:
        """Sets the baseline and initialization timestamp so all token metrics start from 0, preserving game progression."""
        now = datetime.datetime.now().astimezone()
        self.state["tokens_init_ts"] = now.isoformat()
        self.state["baseline_total_tokens"] = raw_total
        if date_str is None:
            date_str = now.strftime("%Y-%m-%d")
        self.state["baseline_date"] = date_str
        self.save()
        return True, "Token metrics initialized! All token usages (Today, 7-Day, Monthly, Total) reset to 0."

    def clear_total_tokens_baseline(self) -> Tuple[bool, str]:
        """Clears the baseline offset so displayed Total Tokens shows absolute lifetime tokens."""
        self.state["baseline_total_tokens"] = 0
        self.state.pop("baseline_date", None)
        self.state.pop("tokens_init_ts", None)
        self.save()
        return True, "Total tokens baseline cleared. Now displaying lifetime total tokens."
