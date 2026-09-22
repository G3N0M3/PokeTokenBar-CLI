import datetime
import random
from typing import Dict, List, Optional, Tuple, Any, Set

from poketokenbar.game.models import MonState, Rarity, PokemonBalance, ItemKind
from poketokenbar.game.storage import StorageManager
from poketokenbar.utils.formatting import format_tokens


class ProfileMixin:
    """Manages player profile, streaks, daily quests, gym bosses, achievements, and trainer battles."""

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
                    
                    if diff > 0:
                        days_to_apply = min(diff, 100)
                        
                        # Process banking day rollover (checking interest, CDs, loan interest, repossession)
                        self._apply_bank_day_rollover(days_to_apply, events)

                        # Process Corporate Stock Market Rollover & Dynamic Dividends
                        self._rollover_stock_market(days_to_apply, diff, current_streak, events)

                        # Process Black Market rotation (5% random chance per day)
                        bm = self.state.get("black_market")
                        if not bm:
                            bm = self.get_or_init_black_market()

                        if bm.get("natural_open", bm.get("is_open")):
                            dur = bm.get("duration_days", 1) - days_to_apply
                            if dur <= 0:
                                bm["natural_open"] = False
                                bm["is_open"] = False
                                events.append("🕶️ The Rocket Syndicate Black Market packed up and vanished.")
                            else:
                                bm["duration_days"] = dur

                        if not bm.get("natural_open"):
                            for _ in range(days_to_apply):
                                if random.random() < 0.05:
                                    self.get_or_init_black_market(force_open=True)
                                    events.append("🕶️ Rocket Syndicate dealers are operating in town! (Check Shop)")
                                    break

                        # Reroll daily grunt bribe on day advance
                        self.state["daily_grunt_bribe"] = random.choice([1_000_000, 2_000_000, 3_000_000, 4_000_000, 5_000_000])

                    if diff == 1:
                        if active:
                            bonus = 15 if active.held_item == "leftovers" else 10
                            if active.held_item == "soothe_bell":
                                bonus = 25
                            _, aether_bonus = self.get_aether_perks()
                            bonus += aether_bonus
                            active.happiness = min(100, active.happiness + bonus)
                            self.set_active_mon(active)
                    elif diff > 1:
                        if active and active.held_item in ["leftovers", "soothe_bell"]:
                            protect_item = ItemKind(active.held_item).name_en
                            events.append(f"🍎 Your companion missed {diff-1} day(s), but was protected by {protect_item}! Happiness preserved!")
                        else:
                            decay = (diff - 1) * 25
                            decay_shield, _ = self.get_aether_perks()
                            if decay_shield > 1.0:
                                decay = max(1, int(decay / decay_shield))
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
            ("q1", "Burn 1.0M tokens today", 1_000_000, "berry_oran", "burn_today"),
            ("q1", "Burn 2.5M tokens today", 2_500_000, "rare_candy", "burn_today"),
            ("q1", "Burn 5.0M tokens today", 5_000_000, "rare_candy", "burn_today"),
        ]
        comp_options = [
            ("q2", "Hatch an egg or evolve a companion", 1, "rare_candy", "progression"),
            ("q2", "Reach 100% Companion Happiness", 100, "rare_candy", "happiness"),
            ("q2", "Maintain a 2+ Day Coding Streak", 2, "berry_oran", "streak"),
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
                elif reward_type == "berry_oran":
                    inv["berry_oran"] = inv.get("berry_oran", 0) + 1
                    msgs.append(f"+1 Oran Berry 🫐 for [{q['text']}]")
                elif reward_type == "mint":
                    inv["rare_candy"] = inv.get("rare_candy", 0) + 1
                    msgs.append(f"+1 Rare Candy 🍬 for [{q['text']}]")
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

    def _update_boss_battle(self, delta: int) -> List[str]:
        events = []
        bosses = [
            {"id": "boss_1", "name": "Brock & Geodude", "sp_id": 74, "badge": "🪨 Boulder Badge", "threshold": 5_000_000, "hp": 2_000_000, "reward": "rare_candy"},
            {"id": "boss_2", "name": "Misty & Starmie", "sp_id": 121, "badge": "💧 Cascade Badge", "threshold": 15_000_000, "hp": 5_000_000, "reward": "rare_candy"},
            {"id": "boss_3", "name": "Lt. Surge & Raichu", "sp_id": 26, "badge": "⚡ Thunder Badge", "threshold": 30_000_000, "hp": 10_000_000, "reward": "tokens_10m"},
            {"id": "boss_4", "name": "Erika & Vileplume", "sp_id": 45, "badge": "🌸 Rainbow Badge", "threshold": 50_000_000, "hp": 18_000_000, "reward": "rare_candy"},
            {"id": "boss_5", "name": "Koga & Weezing", "sp_id": 110, "badge": "🟣 Soul Badge", "threshold": 75_000_000, "hp": 25_000_000, "reward": "rare_candy"},
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
            if active and active.held_item in ["choice_band", "choice_specs"]:
                damage = int(damage * 1.5)
            elif active and active.held_item == "metal_coat":
                damage = int(damage * 1.15)
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
                multiplier *= self.get_macro_multiplier()
                
                if r_type == "rare_candy" or r_type == "mint":
                    inv["rare_candy"] = inv.get("rare_candy", 0) + 1
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

    def get_red_battle_active_pokemon_ids(self) -> Set[int]:
        """Returns the set of Pokémon species IDs currently fighting Red on Mt. Silver."""
        st = self.state.get("red_battle_state", {})
        if not st:
            return set()
        if st.get("status") in ["win", "loss"]:
            return set()
        return set(st.get("player_team", []))

    def select_active_from_dex(self, selection_input: str) -> Tuple[bool, str]:
        # Handle 'select egg' or 'select 0'
        if selection_input.lower().startswith("egg") or selection_input == "0":
            if not self.state.get("egg_tier"):
                return False, "You don't own any Pokémon Eggs!"
                
            curr_active = self.active_mon
            if curr_active:
                prev_status = "graduated" if (getattr(curr_active, "is_graduated", False) or f"{curr_active.base_id}_{curr_active.current_id}" in self.state.get("collected_finals", [])) else "inactive"
                self._register_to_dex(curr_active, status=prev_status)
            
            self.set_active_mon(None)
            egg_usage = self.state.get("egg_usage", 0)
            threshold = self.current_difficulty.hatch_threshold
            pct = (egg_usage / threshold) * 100 if threshold > 0 else 0
            return True, f"Switched active companion to Incubating Egg! ({pct:.1f}% hatched)"

        dex = self.state.get("dex", [])
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

        # Prevent selecting a companion currently in battle with Red
        red_team_ids = self.get_red_battle_active_pokemon_ids()
        if sp_id in red_team_ids:
            return False, f"Cannot select {sp_name}! They are currently in battle with Red on Mt. Silver."

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

        # First, save current active mon into dex as inactive/graduated if exists
        curr_active = self.active_mon
        if curr_active:
            prev_status = "graduated" if (getattr(curr_active, "is_graduated", False) or f"{curr_active.base_id}_{curr_active.current_id}" in self.state.get("collected_finals", [])) else "inactive"
            self._register_to_dex(curr_active, status=prev_status)

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
                is_shiny=target_entry.get("is_shiny", False)
            )

        # Check if target companion is already graduated
        is_already_grad = (target_entry.get("status") == "graduated") or \
                          (f"{mon.base_id}_{mon.current_id}" in self.state.get("collected_finals", [])) or \
                          getattr(mon, "is_graduated", False)
        if is_already_grad:
            mon.is_graduated = True

        # Check if this species is an already-evolved pre-evolution stage
        target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, mon.stage_index, diff)
        discovered_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))) for d in dex}
        next_evo_id = self.get_next_evolution_id(mon)
        is_already_evolved = is_already_grad or (target_entry.get("status") in ["evolved", "graduated"]) or \
                            (next_evo_id is not None and next_evo_id in discovered_sp_ids)

        if is_already_evolved:
            mon.used_at_stage = target_xp

        # Set new active mon
        self.set_active_mon(mon)
        self._register_to_dex(mon, status="active")
        
        shiny_str = "✨ Shiny " if mon.is_shiny else ""
        return True, f"Switched active companion to {shiny_str}{sp_name} (#{sp_id})!"

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
                
                # Progress active Rocket Operation #2 ONLY if status is active
                ops = self.state.get("rocket_ops", {})
                if ops.get("op_2", {}).get("status") == "active" and not ops.get("op_2", {}).get("claimed", False):
                    ops["op_2"]["battle_wins"] = ops["op_2"].get("battle_wins", 0) + 1
                    win_count = ops["op_2"]["battle_wins"]
                    if win_count >= 2:
                        ops["op_2"]["objective_done"] = True
                        events.append("🎯 Rocket Operation Directive complete: 2 Trainer Battle wins secured!")
                    else:
                        events.append(f"🎯 Rocket Operation Directive: Trainer Battle win logged ({win_count}/2)!")

                if active and active.is_mega:
                    token_reward = 3_000_000
                    reward_str = "3.0M"
                    bonus_msg = " ✨ MEGA BONUS!"
                else:
                    token_reward = 2_000_000
                    reward_str = "2.0M"
                    bonus_msg = ""
                    
                if active and active.held_item == "amulet_coin":
                    token_reward = int(token_reward * 1.5)
                    reward_str = f"{token_reward / 1_000_000:.1f}M"
                    bonus_msg += " (🪙 Amulet Coin Bonus!)"
                macro_mult = self.get_macro_multiplier()
                if macro_mult > 1.0:
                    token_reward = int(token_reward * macro_mult)
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

            if "Team Rocket Grunt" in opp_name:
                events.append("   Grunt: \"You didn't see anything! And don't you dare go snooping behind the posters in the Game Corner!\"")

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
