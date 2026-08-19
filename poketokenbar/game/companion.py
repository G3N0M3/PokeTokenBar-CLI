import random
import datetime
from typing import Dict, List, Optional, Tuple, Any

from poketokenbar.game.models import (
    MonState, DexEntry, Rarity, PokemonNature, PokemonBalance, ItemKind, DifficultyMode
)
from poketokenbar.game.pokeapi import PokeAPIClient
from poketokenbar.game.storage import StorageManager

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

        if active is None:
            # We are incubating an egg
            curr_tier = self.state.get("current_egg_tier") or self.state.get("egg_tier") or "normal"
            incubating_eggs = self.state.get("incubating_eggs", {})
            egg_usage = incubating_eggs.get(curr_tier, self.state.get("egg_usage", 0)) + delta
            incubating_eggs[curr_tier] = egg_usage
            self.state["incubating_eggs"] = incubating_eggs
            self.state["egg_usage"] = egg_usage

            if egg_usage >= diff.hatch_threshold:
                # Hatch Egg!
                overflow = egg_usage - diff.hatch_threshold
                if curr_tier in incubating_eggs:
                    del incubating_eggs[curr_tier]
                self.state["incubating_eggs"] = incubating_eggs
                self.state["egg_usage"] = 0
                hatched_mon, hatch_events = self.hatch_egg(overflow)
                events.extend(hatch_events)
                self.set_active_mon(hatched_mon)
            else:
                self.save()
        else:
            # Active mon accumulates XP
            active.used_at_stage += delta
            # Check evolution / graduation
            evo_events = self._check_growth(active)
            events.extend(evo_events)

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

        self.state["dex"] = sorted(new_dex, key=lambda x: x.get("species_id", 0))
        if status == "graduated":
            collected = set(self.state.get("collected_finals", []))
            collected.add(f"{mon.base_id}_{mon.current_id}")
            self.state["collected_finals"] = list(collected)
        self.save()

    def select_active_from_dex(self, selection_input: str) -> Tuple[bool, str]:
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
        if not dex:
            return False, "Your Pokédex is empty!"

        target_entry = None
        # Try matching by 1-based index in dex list
        try:
            idx = int(selection_input)
            if 1 <= idx <= len(dex):
                target_entry = dex[idx - 1]
        except ValueError:
            pass

        if target_entry is None:
            # Try matching by species_id
            for d in dex:
                sp_id = str(d.get("species_id", d.get("base_id")))
                if selection_input == sp_id:
                    target_entry = d
                    break

        if target_entry is None:
            return False, f"Pokémon '{selection_input}' not found in Pokédex! Use index (1..{len(dex)}) or species ID."

        sp_id = target_entry.get("species_id", target_entry.get("base_id"))
        sp_name = self.api.get_species_name(sp_id)

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

        elif item_kind == ItemKind.SHINY_CHARM:
            return False, "Shiny Charm is a passive item and works automatically on all future egg hatches!"

        return False, "Unknown item action."

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
