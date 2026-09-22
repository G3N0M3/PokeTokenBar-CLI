import random
from typing import Dict, List, Optional, Tuple, Any

from poketokenbar.game.models import MonState, Rarity
from poketokenbar.utils.formatting import format_tokens


# Expanded pool of starters, base species, and all legendary/mythical Pokémon (Gens 1-7)
BASE_SPECIES_STARTERS = [
    # === LEGENDARY & MYTHICAL POKÉMON (Generations 1 - 7) ===
    # Gen 1
    (144, "Articuno", 3, True), (145, "Zapdos", 3, True), (146, "Moltres", 3, True),
    (150, "Mewtwo", 3, True),
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
    (345, "Lileep", 45, False), (347, "Anorith", 45, False), (408, "Cranidos", 45, False),
    (410, "Shieldon", 45, False), (564, "Tirtouga", 45, False), (566, "Archen", 45, False),
    (696, "Tyrunt", 45, False), (698, "Amaura", 45, False),
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


class HatchingMixin:
    """Manages egg hatching, starter species selection, and egg purchases."""

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
        
        # Select base species
        base_id, rarity, chain_ids, is_legendary = self._pick_species(used_tier)

        # Roll Shiny odds (1/64 base, 1/32 for paradox, or 1/24 with Golden Razz Berry)
        denom = 32 if used_tier == "paradox" else 64
        if self.state.get("golden_razz_active", False):
            denom = min(denom, 24)
        if self.active_mon and self.active_mon.held_item == "scope_lens":
            denom = max(2, denom // 2)
            
        is_shiny = force_shiny or (random.randint(1, denom) == 1)
        self.state["golden_razz_active"] = False

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
            ditto_disguise=ditto_disguise
        )

        species_name = self.api.get_species_name(base_id)
        shiny_str = "✨ Shiny " if is_shiny else ""

        self.state["egg_usage"] = 0
        self.set_active_mon(mon)
        self._register_to_dex(mon, status="active")

        hatch_milestone = f"Egg Hatched! You got a {shiny_str}{species_name} (#{base_id})!"
        self.state["last_evolution"] = hatch_milestone
        self.state["last_milestone"] = hatch_milestone

        events.append(f"🐣 Egg Hatched! You got a {shiny_str}{species_name} (#{base_id})! Rarity: {rarity.value.upper()}")
        events.extend(self._progress_quest_by_type("progression"))
        return mon, events

    def _pick_species(self, tier_guarantee: Optional[str] = None) -> Tuple[int, Rarity, List[int], bool]:
        # 1. Collect all owned species IDs, base IDs, and chain IDs across Pokédex, Active Companion, and Roster
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
                for pl_id in mon_st.get("planned_path_ids", []):
                    try: owned_ids.add(int(pl_id))
                    except (ValueError, TypeError): pass

        active = self.active_mon
        if active:
            try: owned_ids.add(int(active.base_id))
            except (ValueError, TypeError): pass
            try: owned_ids.add(int(active.current_id))
            except (ValueError, TypeError): pass
            for p_id in getattr(active, "path_ids", []):
                try: owned_ids.add(int(p_id))
                except (ValueError, TypeError): pass
            for pl_id in getattr(active, "planned_path_ids", []):
                try: owned_ids.add(int(pl_id))
                except (ValueError, TypeError): pass

        act_st = self.state.get("active_mon")
        if isinstance(act_st, dict):
            if act_st.get("base_id"):
                try: owned_ids.add(int(act_st["base_id"]))
                except (ValueError, TypeError): pass
            if act_st.get("current_id"):
                try: owned_ids.add(int(act_st["current_id"]))
                except (ValueError, TypeError): pass
            for p_id in act_st.get("path_ids", []):
                try: owned_ids.add(int(p_id))
                except (ValueError, TypeError): pass
            for pl_id in act_st.get("planned_path_ids", []):
                try: owned_ids.add(int(pl_id))
                except (ValueError, TypeError): pass

        for item in self.state.get("collected_finals", []):
            if isinstance(item, str) and "_" in item:
                parts = item.split("_")
                for p in parts:
                    try: owned_ids.add(int(p))
                    except (ValueError, TypeError): pass

        for exp in self.state.get("expeditions", []):
            p_id = exp.get("pokemon_id") or exp.get("species_id") or exp.get("base_id")
            if p_id:
                try: owned_ids.add(int(p_id))
                except (ValueError, TypeError): pass

        # 2. Select candidate pool based on tier guarantee
        if tier_guarantee == "mysterious fetal form":
            if 151 not in owned_ids:
                return 151, Rarity.LEGENDARY, [151], True
            candidates = [c for c in BASE_SPECIES_STARTERS if c[3]]
        elif tier_guarantee == "legendary":
            candidates = [c for c in BASE_SPECIES_STARTERS if c[3]]
        elif tier_guarantee == "fossil":
            fossil_ids = {138, 140, 142, 345, 347, 408, 410, 564, 566, 696, 698}
            candidates = [c for c in BASE_SPECIES_STARTERS if c[0] in fossil_ids]
        elif tier_guarantee == "dragon":
            dragon_ids = {147, 371, 443, 610, 633, 704, 782}
            candidates = [c for c in BASE_SPECIES_STARTERS if c[0] in dragon_ids]
        elif tier_guarantee == "shadow_fetal":
            candidates = [c for c in BASE_SPECIES_STARTERS if c[0] == 251]
        elif tier_guarantee == "starter":
            starter_ids = {1, 4, 7, 152, 155, 158, 252, 255, 258, 387, 390, 393, 495, 498, 501, 650, 653, 656, 722, 725, 728}
            candidates = [c for c in BASE_SPECIES_STARTERS if c[0] in starter_ids]
        elif tier_guarantee == "paradox":
            paradox_ids = {147, 246, 371, 374, 443, 633, 704, 782, 131, 143, 447, 570, 636, 679, 778}
            candidates = [c for c in BASE_SPECIES_STARTERS if c[0] in paradox_ids]
        elif tier_guarantee == "smuggler_mystery":
            if random.random() < 0.50:
                candidates = [c for c in BASE_SPECIES_STARTERS if c[3]]
            else:
                candidates = [c for c in BASE_SPECIES_STARTERS if c[0] == 129]  # Magikarp
        else:
            candidates = [c for c in BASE_SPECIES_STARTERS if not c[3]]
            if tier_guarantee:
                try:
                    req_rank = Rarity(tier_guarantee).sort_rank
                    candidates = [c for c in candidates if Rarity.from_capture_rate(c[2], c[3]).sort_rank >= req_rank]
                except (ValueError, KeyError):
                    pass
                if not candidates:
                    candidates = [c for c in BASE_SPECIES_STARTERS if not c[3]]

        # 3. Strict No-Duplicate Filter: exclude any species that is already owned in any form
        filtered_candidates = [c for c in candidates if c[0] not in owned_ids]

        # 4. Fallback if requested tier is exhausted: search unowned species from broader pool
        if not filtered_candidates:
            if tier_guarantee in ("legendary", "mysterious fetal form", "shadow_fetal"):
                # If requested legendary/mythical pool is exhausted, search any unowned legendary
                filtered_candidates = [c for c in BASE_SPECIES_STARTERS if c[3] and c[0] not in owned_ids]
                # If all legendaries are owned, find any unowned species
                if not filtered_candidates:
                    filtered_candidates = [c for c in BASE_SPECIES_STARTERS if c[0] not in owned_ids]
            else:
                # If tier pool is exhausted, search any unowned non-legendary species
                filtered_candidates = [c for c in BASE_SPECIES_STARTERS if not c[3] and c[0] not in owned_ids]
                # If all non-legendaries are owned, search any unowned species (including legendaries)
                if not filtered_candidates:
                    filtered_candidates = [c for c in BASE_SPECIES_STARTERS if c[0] not in owned_ids]

        # 5. True 100% full-game completion fallback (only occurs if player literally owns all 150+ species)
        if not filtered_candidates:
            filtered_candidates = candidates

        # Select species and verify evolutionary family has no overlap with owned_ids
        while filtered_candidates:
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

            # If there's any overlap with owned_ids and we have alternative candidates, skip this candidate
            if any(cid in owned_ids for cid in chain_ids) and len(filtered_candidates) > 1:
                filtered_candidates.remove(chosen)
                continue

            return sp_id, rarity, chain_ids, is_leg

        return chosen[0], rarity, chain_ids, chosen[3]

    def buy_egg(self, tier: Optional[Rarity] = None) -> Tuple[bool, str]:
        diff = self.current_difficulty
        costs = diff.shop_prices
        tier_key = tier.value if tier else "normal"
        cost = costs.get("egg_rare" if tier == Rarity.RARE else ("egg_uncommon" if tier == Rarity.UNCOMMON else "egg_normal"), 30_000_000)
        cost = int(cost * self.get_devon_multiplier())

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
