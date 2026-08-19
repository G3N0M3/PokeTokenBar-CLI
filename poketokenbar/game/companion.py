import random
import datetime
from typing import Dict, List, Optional, Tuple, Any

from poketokenbar.game.models import (
    MonState, DexEntry, Rarity, PokemonNature, PokemonBalance, ItemKind, DifficultyMode
)
from poketokenbar.game.pokeapi import PokeAPIClient
from poketokenbar.game.storage import StorageManager
from poketokenbar.utils.formatting import format_tokens

from poketokenbar.game.poker import PokerEngine
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
        self.poker = PokerEngine()

    def save(self):
        StorageManager.save_state(self.state)

    def get_settings(self) -> Dict[str, Any]:
        defaults = {"auto_tracking_enabled": True, "refresh_interval": 3.0}
        saved = self.state.get("settings", {})
        return {**defaults, **saved}

    def update_settings(self, auto_tracking_enabled: Optional[bool] = None, refresh_interval: Optional[float] = None) -> Tuple[bool, str]:
        settings = self.get_settings()
        if auto_tracking_enabled is not None:
            settings["auto_tracking_enabled"] = auto_tracking_enabled
        if refresh_interval is not None:
            if refresh_interval < 0.5:
                return False, "Interval must be at least 0.5 seconds."
            settings["refresh_interval"] = float(refresh_interval)

        self.state["settings"] = settings
        self.save()
        return True, "Settings updated successfully."

    def reset_game_state(self) -> Tuple[bool, str]:
        """Resets all game progress, inventory, companions, and Pokédex entries."""
        old_settings = self.get_settings()
        self.state = StorageManager.default_state()
        self.state["settings"] = old_settings
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
        self.state["active_mon"] = StorageManager.mon_to_dict(mon) if mon else None
        self.save()

    @property
    def current_difficulty(self) -> DifficultyMode:
        diff_str = self.state.get("settings", {}).get("difficulty", "medium")
        try:
            return DifficultyMode(diff_str)
        except Exception:
            return DifficultyMode.MEDIUM

    def process_usage(self, new_total_tokens: int) -> List[str]:
        """Call this with cumulative tokens used since install."""
        events = []
        old_used = self.state.get("used_since_install", 0)
        if not self.state.get("install_baseline_set", False):
            self.state["used_since_install"] = new_total_tokens
            self.state["install_baseline_set"] = True
            self.save()
            return events

        delta = max(0, new_total_tokens - old_used)
        if delta == 0:
            return events

        self.state["used_since_install"] = new_total_tokens
        active = self.active_mon
        diff = self.current_difficulty

        if active:
            active.happiness = min(100, active.happiness + int(delta / 100_000))
            self.set_active_mon(active)
            happiness = active.happiness
        else:
            happiness = 100

        # Happiness XP multiplier (+20% bonus if 100% happy)
        xp_multiplier = 1.20 if happiness >= 100 else 1.0
        if active and active.is_mega:
            xp_multiplier += 0.50  # Mega Evolution grants +50% XP boost!
        effective_xp = int(delta * xp_multiplier)

        # Update coding streak & daily quests
        self._update_streak_and_quests(delta, events)

        # Update boss battle damage if active
        boss_events = self._update_boss_battle(delta)
        events.extend(boss_events)

        # Update Pokédex expeditions progress
        self._update_expeditions(delta, events)

        # Check mini-trainer auto-battles
        self._check_trainer_battle(delta, events)

        if active is None:
            # We are incubating an egg
            curr_tier = self.state.get("current_egg_tier") or self.state.get("egg_tier") or "normal"
            incubating_eggs = self.state.get("incubating_eggs", {})
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

            if is_already_evolved:
                active.used_at_stage = min(active.used_at_stage, target_xp)

            self.set_active_mon(active)
            evo_events = self._check_growth(active)
            events.extend(evo_events)

        # Check achievements
        ach_events = self._check_achievements()
        events.extend(ach_events)

        return events

    def _update_streak_and_quests(self, delta: int, events: List[str]):
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        last_date = self.state.get("last_active_date", "")
        active = self.active_mon

        if last_date != today_str:
            if last_date:
                try:
                    last_dt = datetime.datetime.strptime(last_date, "%Y-%m-%d")
                    today_dt = datetime.datetime.strptime(today_str, "%Y-%m-%d")
                    diff = (today_dt - last_dt).days
                    if diff == 1:
                        self.state["streak_days"] = self.state.get("streak_days", 1) + 1
                        if active:
                            active.happiness = min(100, active.happiness + 10)
                            self.set_active_mon(active)
                    elif diff > 1:
                        self.state["streak_days"] = 1
                        decay = (diff - 1) * 25
                        if active:
                            active.happiness = max(0, active.happiness - decay)
                            self.set_active_mon(active)
                            hap_val = active.happiness
                        else:
                            hap_val = 0
                        events.append(f"💔 You missed {diff-1} day(s) of coding! Companion Happiness dropped to {hap_val}%. Feed Oran Berries 🫐 to cheer them up!")
                except Exception:
                    self.state["streak_days"] = 1
            else:
                self.state["streak_days"] = 1
            self.state["last_active_date"] = today_str

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
                elif q_type == "happiness" and self.state.get("happiness", 0) >= q["target"]:
                    q["progress"] = q["target"]
                    events.append(f"🎯 Quest Complete: [{q['text']}]! Type 'claim {q['id']}' to collect your reward!")

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
        target_q = None
        for q in quests:
            if q["id"] == q_id or q_id == "all":
                if q["progress"] >= q["target"] and not q["claimed"]:
                    target_q = q
                    break

        if not target_q:
            return False, "No completed unclaimed quest found!"

        reward_type = target_q["reward"]
        target_q["claimed"] = True
        self.state["daily_quests"] = qdata

        inv = self.state.get("inventory", {})
        if reward_type == "rare_candy":
            inv["rare_candy"] = inv.get("rare_candy", 0) + 1
            self.state["inventory"] = inv
            self.save()
            return True, f"Claimed Reward: +1 Rare Candy 🍬 for completing [{target_q['text']}]!"
        elif reward_type == "mint":
            inv["mint"] = inv.get("mint", 0) + 1
            self.state["inventory"] = inv
            self.save()
            return True, f"Claimed Reward: +1 Mint 🌿 for completing [{target_q['text']}]!"
        elif reward_type == "tokens_10m":
            self.state["spent_tokens"] = max(0, self.state.get("spent_tokens", 0) - 10_000_000)
            self.save()
            return True, f"Claimed Reward: +10.0M Spendable Tokens for completing [{target_q['text']}]!"
        elif reward_type == "tokens_20m":
            self.state["spent_tokens"] = max(0, self.state.get("spent_tokens", 0) - 20_000_000)
            self.save()
            return True, f"Claimed Reward: +20.0M Spendable Tokens for completing [{target_q['text']}]!"

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
            {"id": "boss_8", "name": "Giovanni & Mewtwo", "sp_id": 150, "badge": "👑 Earth Badge", "threshold": 180_000_000, "hp": 60_000_000, "reward": "shiny_charm"},
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
            active_boss["current_hp"] -= delta
            if active_boss["current_hp"] <= 0:
                active_boss["current_hp"] = 0
                badge = active_boss["badge"]
                b_name = active_boss["name"]
                gym_badges.add(badge)
                self.state["gym_badges"] = list(gym_badges)

                # Grant reward
                r_type = active_boss["reward"]
                inv = self.state.get("inventory", {})
                if r_type == "rare_candy":
                    inv["rare_candy"] = inv.get("rare_candy", 0) + 1
                    self.state["inventory"] = inv
                elif r_type == "mint":
                    inv["mint"] = inv.get("mint", 0) + 1
                    self.state["inventory"] = inv
                elif r_type == "shiny_charm":
                    inv["shiny_charm"] = inv.get("shiny_charm", 0) + 1
                    self.state["inventory"] = inv
                elif r_type == "tokens_10m":
                    self.state["spent_tokens"] = max(0, self.state.get("spent_tokens", 0) - 10_000_000)
                elif r_type == "tokens_15m":
                    self.state["spent_tokens"] = max(0, self.state.get("spent_tokens", 0) - 15_000_000)
                elif r_type == "tokens_20m":
                    self.state["spent_tokens"] = max(0, self.state.get("spent_tokens", 0) - 20_000_000)
                elif r_type == "tokens_50m":
                    self.state["spent_tokens"] = max(0, self.state.get("spent_tokens", 0) - 50_000_000)

                events.append(f"🏆 BOSS DEFEATED! You defeated Boss {b_name} and earned the {badge}!")
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
            if next_id in discovered_sp_ids:
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
                
                # Check Ditto reveal
                if mon.ditto_disguise and not mon.ditto_revealed:
                    mon.ditto_revealed = True
                    events.append(f"✨ Surprised! Your Pokémon was actually Ditto disguised as #{mon.base_id}!")

                shiny_str = "✨ Shiny " if mon.is_shiny else ""
                events.append(f"🎉 Evolution! Your companion evolved into {shiny_str}{mon_name} (#{new_id})!")
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
            target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, idx, diff)
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
                rarity=mon.rarity,
                total_forms=mon.total_forms,
                is_shiny=mon.is_shiny,
                nature=mon.nature,
                ditto_disguise=mon.ditto_disguise,
                ditto_revealed=mon.ditto_revealed
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
                    d["status"] = "evolved"

        self.state["dex"] = sorted(new_dex, key=lambda x: x.get("species_id", 0))
        if status == "graduated":
            collected = set(self.state.get("collected_finals", []))
            collected.add(f"{mon.base_id}_{mon.current_id}")
            self.state["collected_finals"] = list(collected)

        self.save()

    def select_active_from_dex(self, selection_input: str) -> Tuple[bool, str]:
        # Handle 'select egg' or 'select 0'
        if selection_input.lower() in ["egg", "0"]:
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
        roster = [d for d in dex if (d.get("status") != "evolved" or d.get("species_id", d.get("final_id", d.get("base_id"))) in exp_map)]
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
            if higher_forms or entry_status == "evolved":
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

    def hatch_egg(self, initial_xp: int = 0) -> Tuple[MonState, List[str]]:
        events = []
        tier_guarantee = self.state.get("egg_tier")
        
        # Select base species
        base_id, rarity, chain_ids, is_legendary = self._pick_species(tier_guarantee)

        # Roll Shiny odds (1/64 base or 1/48 if user has Shiny Charm)
        has_charm = self.state.get("inventory", {}).get(ItemKind.SHINY_CHARM.value, 0) > 0
        denom = 48 if has_charm else 64
        is_shiny = (random.randint(1, denom) == 1)

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

        self._register_to_dex(mon, status="active")

        events.append(f"🐣 Egg Hatched! You got a {shiny_str}{species_name} (#{base_id})! Nature: {nature_str}, Rarity: {rarity.value.upper()}")
        return mon, events

    def _pick_species(self, tier_guarantee: Optional[str] = None) -> Tuple[int, Rarity, List[int], bool]:
        # Filter candidate pool
        candidates = BASE_SPECIES_STARTERS
        if tier_guarantee:
            req_rank = Rarity(tier_guarantee).sort_rank
            candidates = [c for c in candidates if Rarity.from_capture_rate(c[2], c[3]).sort_rank >= req_rank]
            if not candidates:
                candidates = BASE_SPECIES_STARTERS

        chosen = random.choice(candidates)
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

    def buy_item(self, item_kind: ItemKind) -> Tuple[bool, str]:
        diff = self.current_difficulty
        cost = item_kind.price_for(diff)
        if self.available_tokens < cost:
            return False, f"Not enough tokens! Required: {format_tokens(cost)}, Available: {format_tokens(self.available_tokens)}"

        inv = self.state.get("inventory", {})
        if item_kind == ItemKind.SHINY_CHARM and inv.get(ItemKind.SHINY_CHARM.value, 0) > 0:
            return False, "You already own the Shiny Charm!"

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
        inv[item_kind.value] = inv.get(item_kind.value, 0) + 1
        self.state["inventory"] = inv
        self.save()
        return True, f"Successfully purchased {item_kind.name_en} ({item_kind.emoji})!"

    def use_item(self, item_kind: ItemKind) -> Tuple[bool, str]:
        inv = self.state.get("inventory", {})
        count = inv.get(item_kind.value, 0)
        if count <= 0:
            return False, f"You don't have any {item_kind.name_en} in your Bag!"

        active = self.active_mon
        if item_kind == ItemKind.RARE_CANDY:
            if active is None:
                return False, "You need an active Pokémon companion to give Rare Candy!"
            inv[item_kind.value] -= 1
            self.state["inventory"] = inv
            self.save()
            
            xp_grant = int(self.current_difficulty.shop_prices["rare_candy"] * 0.6)
            events = self.process_usage(self.state.get("used_since_install", 0) + xp_grant)
            msg = f"Gave 1 Rare Candy! (+{format_tokens(xp_grant)} XP)"
            if events:
                msg += "\n" + "\n".join(events)
            return True, msg

        elif item_kind == ItemKind.MINT:
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
            inv[item_kind.value] -= 1
            active.happiness = min(100, active.happiness + 25)
            self.set_active_mon(active)
            self.state["inventory"] = inv
            self.save()
            return True, f"Fed Oran Berry 🫐 to {self.api.get_species_name(active.current_id)}! (+25% Happiness! Current: {active.happiness}%)"

        elif item_kind == ItemKind.BERRY_GOLDEN:
            inv[item_kind.value] -= 1
            self.state["golden_razz_active"] = True
            self.state["inventory"] = inv
            self.save()
            return True, "Used Golden Razz Berry 🍇! Shiny odds on your NEXT egg hatch boosted to 1/24! ✨"

        elif item_kind == ItemKind.MEGA_STONE:
            return self.toggle_mega_evolution()

        elif item_kind == ItemKind.SHINY_CHARM:
            return False, "Shiny Charm is a passive item and works automatically on all future egg hatches!"

        return False, "Unknown item action."

    def toggle_mega_evolution(self) -> Tuple[bool, str]:
        active = self.active_mon
        if active is None:
            return False, "You need an active Pokémon companion to Mega Evolve!"

        mega_eligible = {3, 6, 9, 94, 150, 448}  # Venusaur, Charizard, Blastoise, Gengar, Mewtwo, Lucario
        if active.current_id not in mega_eligible:
            return False, f"Species #{active.current_id} ({self.api.get_species_name(active.current_id)}) is not eligible for Mega Evolution!"

        inv = self.state.get("inventory", {})
        if inv.get(ItemKind.MEGA_STONE.value, 0) <= 0 and not active.is_mega:
            return False, "You need a Mega Stone 🔮 from the Shop ([3]) to Mega Evolve!"

        active.is_mega = not active.is_mega
        self.set_active_mon(active)
        name = self.api.get_species_name(active.current_id)
        if active.is_mega:
            return True, f"✨ MEGA EVOLUTION! {name} has Mega Evolved! (+50% Bonus XP active!)"
        else:
            return True, f"{name} reverted back to standard form."

    def _update_expeditions(self, delta: int, events: List[str]):
        expeditions = self.state.get("expeditions", [])
        if not expeditions:
            return

        remaining = []
        for exp in expeditions:
            exp["progress"] += delta
            if exp["progress"] >= exp["target"]:
                sp_id = exp["sp_id"]
                sp_name = self.api.get_species_name(sp_id)
                area = exp["area"]
                reward = exp["reward"]

                # Grant reward
                inv = self.state.get("inventory", {})
                if reward == "rare_candy":
                    inv["rare_candy"] = inv.get("rare_candy", 0) + 1
                    reward_str = "+1 Rare Candy 🍬"
                elif reward == "mint":
                    inv["mint"] = inv.get("mint", 0) + 1
                    reward_str = "+1 Mint 🌿"
                else:
                    inv["berry_golden"] = inv.get("berry_golden", 0) + 1
                    reward_str = "+1 Golden Razz Berry 🍇"

                self.state["inventory"] = inv
                now_str = datetime.datetime.now().strftime("%H:%M:%S")
                logs = self.state.get("expedition_logs", [])
                logs.append(f"[{now_str}] 🗺️ {sp_name} returned from {area} with {reward_str}")
                self.state["expedition_logs"] = logs[-5:]
                events.append(f"🗺️ EXPEDITION COMPLETE! {sp_name} returned from {area} with {reward_str}!")
            else:
                remaining.append(exp)

        self.state["expeditions"] = remaining
        self.save()

    def dispatch_expedition(self, selection_input: str, area_name: str = "Viridian Forest") -> Tuple[bool, str]:
        dex = self.state.get("dex", [])
        if not dex:
            return False, "Your Pokédex is empty! Register companions before dispatching expeditions."

        target_entry = None
        try:
            idx = int(selection_input)
            if 1 <= idx <= len(dex):
                target_entry = dex[idx - 1]
        except ValueError:
            pass

        if target_entry is None:
            # Try matching by species_id or base_id
            for d in dex:
                sp_id = str(d.get("species_id", d.get("base_id")))
                if selection_input == sp_id:
                    target_entry = d
                    break

        if target_entry is None:
            return False, f"Companion '{selection_input}' not found in Pokédex! Use index (1..{len(dex)}) or species ID."

        sp_id = target_entry.get("species_id", target_entry.get("base_id"))
        sp_name = self.api.get_species_name(sp_id)

        # Check if already on expedition
        expeditions = self.state.get("expeditions", [])
        if any(e["sp_id"] == sp_id for e in expeditions):
            return False, f"{sp_name} is already on an expedition!"

        areas = {
            "viridian": ("Viridian Forest", 5_000_000, "mint"),
            "cerulean": ("Cerulean Cave", 15_000_000, "rare_candy"),
            "silver": ("Mt. Silver", 30_000_000, "golden_razz")
        }

        key = area_name.lower().split()[0]
        area_tuple = areas.get(key, ("Viridian Forest", 5_000_000, "mint"))
        area_title, target_xp, reward_type = area_tuple

        expeditions.append({
            "sp_id": sp_id,
            "area": area_title,
            "progress": 0,
            "target": target_xp,
            "reward": reward_type
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
                self.state["spent_tokens"] = max(0, self.state.get("spent_tokens", 0) - 2_000_000)
                msg = f"⚔️ TRAINER BATTLE! You defeated {opp_name} in an auto-battle! Earned +2.0M Spendable Tokens!"
                events.append(msg)
                logs.append(f"[{now_str}] 🏆 WIN vs {opp_name} (Earned +2.0M Tokens)")
            else:
                battles["losses"] += 1
                self.state["happiness"] = max(0, self.state.get("happiness", 100) - 10)
                msg = f"⚔️ TRAINER BATTLE! {opp_name} put up a tough fight! Companion Happiness dropped to {self.state['happiness']}%!"
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

        # Check duplicate egg ownership for same tier
        incubating_eggs = self.state.get("incubating_eggs", {})
        current_tier = self.state.get("current_egg_tier") or self.state.get("egg_tier") or "normal"
        has_legacy_egg = (self.active_mon is None) and (current_tier == tier_key or (tier is None and current_tier == "normal"))

        if tier_key in incubating_eggs or has_legacy_egg:
            tier_display = f"{tier.value.upper()}+" if tier else "Standard"
            return False, f"You already own a {tier_display} Pokémon Egg! You cannot buy duplicate eggs of the same tier."

        if self.available_tokens < cost:
            return False, f"Not enough tokens! Required: {format_tokens(cost)}, Available: {format_tokens(self.available_tokens)}"

        # Save current active mon into dex roster if exists
        curr_active = self.active_mon
        if curr_active:
            self._register_to_dex(curr_active, status="inactive")

        incubating_eggs[tier_key] = 0
        self.state["incubating_eggs"] = incubating_eggs
        self.state["current_egg_tier"] = tier_key
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
        self.set_active_mon(None)
        self.state["egg_usage"] = 0
        self.state["egg_tier"] = tier.value if tier else None
        self.save()
        tier_str = f"{tier.value.upper()}+" if tier else "Standard"
        return True, f"Obtained a fresh {tier_str} Pokémon Egg! Previous companion saved to Pokédex."

    def play_poker_bet(self, amount_str: str) -> Tuple[bool, str]:
        clean_str = amount_str.lower().strip()
        try:
            if clean_str.endswith("m"):
                bet = int(float(clean_str[:-1]) * 1_000_000)
            elif clean_str.endswith("k"):
                bet = int(float(clean_str[:-1]) * 1_000)
            else:
                bet = int(clean_str)
        except ValueError:
            return False, "Invalid bet amount! Example: 'bet 500k', 'bet 1m', or 'bet 2000000'."

        if bet <= 0:
            return False, "Bet amount must be greater than 0!"

        avail = self.available_tokens
        if bet > avail:
            return False, f"Not enough tokens! You have {format_tokens(avail)} available tokens."

        # Lock bet by deducting from spent_tokens
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - bet
        self.save()

        ok, msg = self.poker.start_hand(bet)
        hand_str = " ".join([str(c) for c in self.poker.hand])
        return True, f"🎲 Bet {format_tokens(bet)} Tokens!\n  Cards: {hand_str}\n  ➔ Type 'hold 1 3 5' (or 'hold none' / 'hold all') to draw!"

    def play_poker_hold(self, hold_str: str) -> Tuple[bool, str]:
        if self.poker.game_state != "holding":
            return False, "No active Poker hand! Type 'bet <amount>' to start a new hand."

        parts = hold_str.lower().split()
        indices = []
        if "all" in parts:
            indices = [1, 2, 3, 4, 5]
        elif "none" in parts or not parts or parts == ["hold"]:
            indices = []
        else:
            for p in parts:
                if p.isdigit() and 1 <= int(p) <= 5:
                    indices.append(int(p))

        rank_name, mult, winnings = self.poker.play_draw(indices)
        
        # Add winnings to spent_tokens
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + winnings
        self.save()

        hand_str = " ".join([str(c) for c in self.poker.hand])
        net_change = winnings - self.poker.current_bet
        profit_str = f"+{format_tokens(net_change)}" if net_change >= 0 else f"-{format_tokens(abs(net_change))}"

        if mult > 0:
            return True, f"🃏 Hand: {hand_str}\n  Result: \033[1m\033[32m{rank_name}\033[0m ({mult}x Payout!)\n  Won: \033[1m\033[36m{format_tokens(winnings)}\033[0m Tokens! (Net: {profit_str})"
        else:
            return True, f"🃏 Hand: {hand_str}\n  Result: \033[1m\033[31m{rank_name}\033[0m (No Payout)\n  Lost: {format_tokens(self.poker.current_bet)} Tokens."

    def play_gacha(self, pull_type: str = "1") -> Tuple[bool, str]:
        cost = GACHA_COST_MULTI if pull_type == "10" else GACHA_COST_SINGLE
        avail = self.available_tokens
        if avail < cost:
            return False, f"Not enough tokens! Gacha pull requires {format_tokens(cost)} available tokens."

        # Deduct cost from spent_tokens
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - cost
        inv = self.state.get("inventory", {})

        results_txt = []
        if pull_type == "10":
            pulls = GachaEngine.pull_ten()
            results_txt.append("🔮 \033[1m10-CAPSULE GACHA PULL RESULTS:\033[0m")
        else:
            pulls = [GachaEngine.pull_one()]
            results_txt.append("🔮 \033[1mGACHA CAPSULE PULL RESULT:\033[0m")

        for tier, name, r_type, val in pulls:
            color = "\033[36m" if tier == "COMMON" else ("\033[33m" if tier in ["UNCOMMON", "RARE"] else "\033[32m")
            results_txt.append(f"  • [{color}{tier}\033[0m] {name}")

            if r_type == "item":
                inv[val] = inv.get(val, 0) + 1
            elif r_type == "tokens":
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + val
            elif r_type == "egg":
                self.state["incubating_eggs"] = self.state.get("incubating_eggs", {})
                self.state["incubating_eggs"][val] = self.state["incubating_eggs"].get(val, 0)
            elif r_type == "legendary":
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + val
                self.state["golden_razz_active"] = True

        self.state["inventory"] = inv
        self.save()
        return True, "\n".join(results_txt)
