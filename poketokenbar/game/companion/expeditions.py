import random
import datetime
from typing import Dict, List, Optional, Tuple, Any, Union

from poketokenbar.game.models import Rarity, PokemonBalance, MonState
from poketokenbar.game.storage import StorageManager
from poketokenbar.utils.formatting import format_tokens


class ExpeditionsMixin:
    """Manages companion expedition dispatching, progression, rewards, and passes."""

    def _update_expeditions(self, effective_xp: int, events: List[str]):
        expeditions = self.state.get("expeditions", [])
        if not expeditions:
            return

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
                    reward = "berry_oran"
                elif "silver" in area_l:
                    reward = "berry_golden"
                elif "spear" in area_l:
                    reward = "legendary_egg"
                elif "mine" in area_l:
                    reward = "evo_stone"
                else:
                    reward = "rare_candy"
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
            if active and active.held_item == "compass_of_deep":
                mult *= 1.25
            silph_speed_mult, silph_token_mult = self.get_silph_multipliers()
            mult *= silph_speed_mult

            exp["progress"] += int(effective_xp * mult)
            
            if exp["progress"] >= exp["target"]:
                # Grant reward
                inv = self.state.get("inventory", {})
                if reward == "rare_candy":
                    inv["rare_candy"] = inv.get("rare_candy", 0) + 1
                    reward_str = "+1 Rare Candy 🍬"
                elif reward == "berry_oran":
                    inv["berry_oran"] = inv.get("berry_oran", 0) + 1
                    reward_str = "+1 Oran Berry 🫐"
                    if random.random() < 0.10:
                        inv["map_fragment"] = inv.get("map_fragment", 0) + 1
                        reward_str += " & +1 Map 📜!"
                elif reward == "mint":
                    inv["rare_candy"] = inv.get("rare_candy", 0) + 1
                    reward_str = "+1 Rare Candy 🍬"
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
                tokens_gain = int(tokens_gain * silph_token_mult)
                if self.state.get("rocket_radar_charges", 0) > 0:
                    tokens_gain = int(tokens_gain * 1.5)
                    self.state["rocket_radar_charges"] -= 1

                # Grant tokens by refunding spent_tokens
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - tokens_gain
                
                for d in dex:
                    sp_id_dex = d.get("species_id", d.get("base_id"))
                    if sp_id_dex == sp_id:
                        if "mon_state" in d and isinstance(d["mon_state"], dict):
                            mon = StorageManager.dict_to_mon(d["mon_state"])
                        else:
                            mon = StorageManager.dict_to_mon(d)
                            
                        if self.state.get("expedition_insurance", 0) > 0:
                            self.state["expedition_insurance"] -= 1
                        else:
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

                # Progress active Rocket Operation #1 ONLY if status is active
                ops = self.state.get("rocket_ops", {})
                if ops.get("op_1", {}).get("status") == "active" and not ops.get("op_1", {}).get("claimed", False):
                    ops["op_1"]["expeditions_done"] = ops["op_1"].get("expeditions_done", 0) + 1
                    done_count = ops["op_1"]["expeditions_done"]
                    if done_count >= 2:
                        ops["op_1"]["objective_done"] = True
                        events.append("🎯 Rocket Operation Directive complete: 2 scout expeditions logged!")
                    else:
                        events.append(f"🎯 Rocket Operation Directive: Scout expedition logged ({done_count}/2)!")

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

        areas = {
            "viridian": ("Viridian Forest", PokemonBalance.EXPEDITION_VIRIDIAN, "rare_candy"),
            "cerulean": ("Cerulean Cave", PokemonBalance.EXPEDITION_CERULEAN, "berry_oran"),
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

            red_team_ids = self.get_red_battle_active_pokemon_ids()
            if sp_id in red_team_ids:
                return False, f"Cannot dispatch {sp_name}! They are currently in battle with Red on Mt. Silver."

            mon_state_dict = target_entry.get("mon_state", {})
            if isinstance(mon_state_dict, dict) and "happiness" in mon_state_dict:
                current_hap = mon_state_dict["happiness"]
            else:
                current_hap = target_entry.get("happiness", 100)

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

            red_team_ids = self.get_red_battle_active_pokemon_ids()
            if sp_id in red_team_ids:
                skipped_notes.append(f"{sp_name} (in Red battle)")
                continue

            mon_state_dict = entry.get("mon_state", {})
            if isinstance(mon_state_dict, dict) and "happiness" in mon_state_dict:
                hap = mon_state_dict["happiness"]
            else:
                hap = entry.get("happiness", 100)

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
