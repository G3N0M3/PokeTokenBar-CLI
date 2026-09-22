import datetime
from typing import Dict, List, Optional, Tuple, Any

from poketokenbar.game.models import MonState, Rarity, PokemonBalance, MEGA_STONES
from poketokenbar.game.storage import StorageManager


TIME_BASED_BRANCH_OVERRIDES: Dict[int, Dict[str, int]] = {
    790: {"day": 791, "night": 792},  # Cosmoem -> Solgaleo (Day) / Lunala (Night)
    133: {"day": 196, "night": 197},  # Eevee -> Espeon (Day) / Umbreon (Night)
}


def get_current_time_of_day(now: Optional[datetime.datetime] = None) -> str:
    """Returns 'day' (06:00 - 17:59) or 'night' (18:00 - 05:59)."""
    if now is None:
        now = datetime.datetime.now()
    return "day" if 6 <= now.hour < 18 else "night"


class EvolutionMixin:
    """Handles Pokémon level growth, evolutionary stages, time branches, stones, and Mega Evolution."""

    def get_current_time_of_day(self, now: Optional[datetime.datetime] = None) -> str:
        return get_current_time_of_day(now)

    def is_time_based_evolution(self, mon: MonState) -> bool:
        """Returns True if the Pokémon has a time-based branching or conditional evolution at current stage."""
        if not mon or mon.stage_index >= len(mon.path_ids) - 1:
            return False
        if mon.current_id in TIME_BASED_BRANCH_OVERRIDES:
            return True
        sp_data = self.api.get_pokemon_species(mon.current_id)
        if sp_data and "evolution_chain" in sp_data:
            try:
                chain_url = sp_data["evolution_chain"]["url"]
                chain_id = int(chain_url.rstrip("/").split("/")[-1])
                evo_data = self.api.get_evolution_chain(chain_id)
                if evo_data:
                    def check_chain_tod(node, target_id):
                        nid = int(node["species"]["url"].rstrip("/").split("/")[-1])
                        if nid == target_id:
                            for b in node.get("evolves_to", []):
                                for det in b.get("evolution_details", []):
                                    if det.get("time_of_day"):
                                        return True
                                return False
                        for b in node.get("evolves_to", []):
                            if check_chain_tod(b, target_id):
                                return True
                        return False
                    return check_chain_tod(evo_data["chain"], mon.current_id)
            except Exception:
                pass
        return False

    def _resolve_dynamic_evolution(self, mon: MonState, now: Optional[datetime.datetime] = None) -> Optional[int]:
        """Resolves target evolution ID based on current time of day ('day' or 'night')."""
        if not mon:
            return None
        tod = self.get_current_time_of_day(now)
        # 1. Canonical time branch overrides (e.g. Cosmoem -> Solgaleo/Lunala, Eevee -> Espeon/Umbreon)
        if mon.current_id in TIME_BASED_BRANCH_OVERRIDES:
            return TIME_BASED_BRANCH_OVERRIDES[mon.current_id].get(tod)

        # 2. Generic PokeAPI evolution chain time_of_day inspection
        sp_data = self.api.get_pokemon_species(mon.current_id)
        if sp_data and "evolution_chain" in sp_data:
            try:
                chain_url = sp_data["evolution_chain"]["url"]
                chain_id = int(chain_url.rstrip("/").split("/")[-1])
                evo_data = self.api.get_evolution_chain(chain_id)
                if evo_data:
                    def find_tod_target(node, target_id):
                        nid = int(node["species"]["url"].rstrip("/").split("/")[-1])
                        if nid == target_id:
                            for b in node.get("evolves_to", []):
                                for det in b.get("evolution_details", []):
                                    if det.get("time_of_day") == tod:
                                        return int(b["species"]["url"].rstrip("/").split("/")[-1])
                            return None
                        for b in node.get("evolves_to", []):
                            res = find_tod_target(b, target_id)
                            if res is not None:
                                return res
                        return None
                    return find_tod_target(evo_data["chain"], mon.current_id)
            except Exception:
                pass
        return None

    def get_next_evolution_id(self, mon: MonState, now: Optional[datetime.datetime] = None) -> Optional[int]:
        """Resolves the next evolution ID for mon, updating path_ids dynamically if time-based."""
        if not mon or mon.stage_index >= len(mon.path_ids) - 1:
            return None

        dynamic_target = self._resolve_dynamic_evolution(mon, now)
        if dynamic_target is not None:
            next_idx = mon.stage_index + 1
            if next_idx < len(mon.path_ids):
                mon.path_ids[next_idx] = dynamic_target
            else:
                mon.path_ids.append(dynamic_target)
            if hasattr(mon, "planned_path_ids") and isinstance(mon.planned_path_ids, list):
                if next_idx < len(mon.planned_path_ids):
                    mon.planned_path_ids[next_idx] = dynamic_target
                else:
                    mon.planned_path_ids.append(dynamic_target)
            return dynamic_target

        if mon.stage_index < len(mon.path_ids) - 1:
            return mon.path_ids[mon.stage_index + 1]
        return None

    def _parse_evo_tree(self, chain_node: Dict[str, Any], now: Optional[datetime.datetime] = None) -> List[int]:
        ids = []
        try:
            sp_url = chain_node["species"]["url"]
            sp_id = int(sp_url.rstrip("/").split("/")[-1])
            ids.append(sp_id)
            if chain_node.get("evolves_to"):
                tod = self.get_current_time_of_day(now)
                next_node = None
                # Check canonical time branch override first
                if sp_id in TIME_BASED_BRANCH_OVERRIDES:
                    target_id = TIME_BASED_BRANCH_OVERRIDES[sp_id].get(tod)
                    for b in chain_node["evolves_to"]:
                        b_id = int(b["species"]["url"].rstrip("/").split("/")[-1])
                        if b_id == target_id:
                            next_node = b
                            break

                # Check generic PokeAPI time_of_day if no override match
                if next_node is None:
                    for b in chain_node["evolves_to"]:
                        for det in b.get("evolution_details", []):
                            if det.get("time_of_day") == tod:
                                next_node = b
                                break
                        if next_node is not None:
                            break

                # Fallback to first branch
                if next_node is None:
                    next_node = chain_node["evolves_to"][0]

                ids.extend(self._parse_evo_tree(next_node, now))
        except Exception:
            pass
        return ids

    def _find_stone_evolution(self, current_id: int, api_item_name: str) -> Optional[int]:
        # Thematic stone overrides (e.g. Sun Stone -> Solgaleo, Moon Stone -> Lunala for Cosmoem)
        stone_overrides = {
            790: {
                "sun-stone": 791,
                "moon-stone": 792,
            }
        }
        if current_id in stone_overrides and api_item_name in stone_overrides[current_id]:
            return stone_overrides[current_id][api_item_name]

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

    def _check_growth(self, mon: MonState, is_active: bool = True, now: Optional[datetime.datetime] = None) -> List[str]:
        events = []
        diff = self.current_difficulty
        dex = self.state.get("dex", [])
        discovered_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))) for d in dex}

        target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, mon.stage_index, diff)

        # If holding Everstone, cap XP at threshold and halt evolution
        if mon.stage_index < len(mon.path_ids) - 1 and mon.held_item == "everstone":
            mon.used_at_stage = min(mon.used_at_stage, target_xp)
            if is_active:
                self.set_active_mon(mon)
            return events

        # If next evolution stage already exists in Pokédex, automatically halt evolution
        if mon.stage_index < len(mon.path_ids) - 1:
            next_sp_id = self.get_next_evolution_id(mon, now=now)
            if next_sp_id in discovered_sp_ids:
                mon.used_at_stage = min(mon.used_at_stage, target_xp)
                if is_active:
                    self.set_active_mon(mon)
                return events

        while mon.used_at_stage >= target_xp:
            if mon.stage_index < len(mon.path_ids) - 1:
                next_sp_id = self.get_next_evolution_id(mon, now=now)
                if next_sp_id in discovered_sp_ids:
                    mon.used_at_stage = min(mon.used_at_stage, target_xp)
                    if is_active:
                        self.set_active_mon(mon)
                    return events

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
                self.state["last_milestone"] = self.state["last_evolution"]
                events.extend(self._progress_quest_by_type("progression"))
                self._register_to_dex(mon, status="active" if is_active else "inactive")
                target_xp = PokemonBalance.phase_threshold(mon.rarity, mon.total_forms, mon.stage_index, diff)
            else:
                # Final form check
                is_already_grad = getattr(mon, "is_graduated", False) or \
                                  f"{mon.base_id}_{mon.current_id}" in self.state.get("collected_finals", [])
                if is_already_grad:
                    mon.is_graduated = True
                    mon.used_at_stage = min(mon.used_at_stage, target_xp)
                    if is_active:
                        self.set_active_mon(mon)
                    return events

                # Final form + reached graduation threshold for the first time!
                mon_name = self.api.get_species_name(mon.current_id)
                shiny_str = "✨ Shiny " if mon.is_shiny else ""
                grad_str = f"🎓 Graduation! {shiny_str}{mon_name} has graduated to your Pokédex!"
                events.append(grad_str)
                self.state["last_evolution"] = f"{shiny_str}{mon_name} graduated to Pokédex!"
                self.state["last_milestone"] = self.state["last_evolution"]

                # Add to Pokédex as graduated
                mon.is_graduated = True
                self._register_to_dex(mon, status="graduated")
                
                if is_active:
                    # Reset to new egg
                    self.set_active_mon(None)
                    pending = self.state.get("pending_eggs", [])
                    if pending:
                        next_egg = pending.pop(0)
                        self.state["egg_tier"] = next_egg
                        self.state["pending_eggs"] = pending
                        events.append(f"🥚 Next in queue: Now incubating your {next_egg.replace('_', ' ').title()} Egg!")
                    else:
                        self.state["egg_tier"] = None
                    self.state["egg_usage"] = 0
                    self.save()
                return events

        if is_active:
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
            is_form_grad = getattr(mon, "is_graduated", False) or (f"{mon.base_id}_{sp_id}" in self.state.get("collected_finals", []))
            if status == "graduated" or is_form_grad or idx < mon.stage_index:
                if status == "active" and idx == mon.stage_index:
                    sp_status = "active"
                else:
                    sp_status = "graduated" if (status == "graduated" or is_form_grad) else "evolved"
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
                happiness=mon.happiness,
                ditto_disguise=mon.ditto_disguise,
                ditto_revealed=mon.ditto_revealed,
                is_mega=mon.is_mega if idx == mon.stage_index else False,
                mega_form=mon.mega_form if idx == mon.stage_index else None,
                held_item=mon.held_item if idx == mon.stage_index else None,
                is_graduated=is_form_grad if idx == mon.stage_index else (idx < mon.stage_index)
            )
            sub_dict = StorageManager.mon_to_dict(sub_stage_mon)

            if sp_id in existing_sp_ids:
                entry = existing_sp_ids[sp_id]
                entry["status"] = sp_status
                entry["mon_state"] = sub_dict
                entry["happiness"] = mon.happiness
                if mon.is_shiny:
                    entry["is_shiny"] = True
            else:
                entry = {
                    "id": f"sp_{sp_id}",
                    "species_id": sp_id,
                    "base_id": mon.base_id,
                    "chain_order": mon.path_ids,
                    "rarity": mon.rarity.value,
                    "caught_at": datetime.datetime.now().isoformat(),
                    "is_shiny": mon.is_shiny,
                    "status": sp_status,
                    "mon_state": sub_dict,
                    "happiness": mon.happiness
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
