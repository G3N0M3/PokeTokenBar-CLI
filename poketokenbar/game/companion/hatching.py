import random
from typing import Dict, List, Optional, Tuple, Any, Set

from poketokenbar.game.models import MonState, Rarity, PokemonBalance
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


ALL_STRAIN_SPECIES_IDS = frozenset([
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    25, 26, 27, 28, 37, 38, 41, 42, 43, 44, 45, 54, 55, 58, 59, 60, 61, 62,
    63, 64, 65, 66, 67, 68, 69, 70, 71, 74, 75, 76, 77, 78, 79, 80, 81, 82,
    92, 93, 94, 95, 123, 127, 129, 130, 131, 133, 134, 135, 136, 137, 138, 139,
    140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155,
    156, 157, 158, 159, 160, 169, 172, 175, 176, 179, 180, 181, 182, 183, 184, 186,
    194, 195, 196, 197, 199, 208, 212, 214, 227, 228, 229, 231, 232, 233, 243, 244,
    245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260,
    280, 281, 282, 285, 286, 287, 288, 289, 298, 304, 305, 306, 307, 308, 309, 310,
    328, 329, 330, 333, 334, 345, 346, 347, 348, 349, 350, 359, 371, 372, 373, 374,
    375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390,
    391, 392, 393, 394, 395, 403, 404, 405, 408, 409, 410, 411, 427, 428, 442, 443,
    444, 445, 446, 447, 448, 453, 454, 459, 460, 462, 468, 470, 471, 474, 475, 479,
    480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495,
    496, 497, 498, 499, 500, 501, 502, 503, 540, 541, 542, 543, 544, 545, 551, 552,
    553, 559, 560, 564, 565, 566, 567, 570, 571, 607, 608, 609, 610, 611, 612, 624,
    625, 633, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647,
    648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 661, 662, 663, 674, 675,
    679, 680, 681, 686, 687, 696, 697, 698, 699, 700, 704, 705, 706, 716, 717, 718,
    719, 720, 721, 722, 723, 724, 725, 726, 727, 728, 729, 730, 736, 737, 738, 744,
    745, 747, 748, 759, 760, 778, 782, 783, 784, 785, 786, 787, 788, 789, 790, 791,
    792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 805, 806, 807,
    900, 980, 983
])

EGG_TOKEN_VALUES: Dict[str, int] = {
    "common": 30_000_000,
    "normal": 30_000_000,
    "starter": 35_000_000,
    "uncommon": 45_000_000,
    "rare": 60_000_000,
    "fossil": 50_000_000,
    "dragon": 75_000_000,
    "paradox": 80_000_000,
    "smuggler_mystery": 40_000_000,
    "shadow_fetal": 100_000_000,
    "mysterious fetal form": 100_000_000,
    "legendary": 100_000_000,
}

class HatchingMixin:
    """Manages egg hatching, starter species selection, and egg purchases."""

    def get_roster_species_ids(self) -> Set[int]:
        """Returns the set of species IDs currently present in the player's active roster.

        The active roster includes:
        1. The active companion (if present).
        2. Any Pokémon in the dex whose status != 'evolved' (active, inactive, graduated).
        3. Any Pokémon currently dispatched on expeditions.
        """
        roster_ids = set()

        # 1. Active companion
        active = self.active_mon
        if active:
            try:
                roster_ids.add(int(active.current_id))
            except (ValueError, TypeError):
                pass
        elif isinstance(self.state.get("active_mon"), dict):
            cur = self.state["active_mon"].get("current_id") or self.state["active_mon"].get("base_id")
            if cur is not None:
                try:
                    roster_ids.add(int(cur))
                except (ValueError, TypeError):
                    pass

        # 2. Dex entries where status != "evolved"
        dex = self.state.get("dex", [])
        for d in dex:
            if d.get("status") != "evolved":
                sp_id = d.get("species_id", d.get("final_id", d.get("base_id")))
                if sp_id is not None:
                    try:
                        roster_ids.add(int(sp_id))
                    except (ValueError, TypeError):
                        pass
                m_st = d.get("mon_state")
                if isinstance(m_st, dict):
                    cur = m_st.get("current_id") or (
                        m_st.get("path_ids")[m_st["stage_index"]]
                        if m_st.get("path_ids") and 0 <= m_st.get("stage_index", 0) < len(m_st["path_ids"])
                        else None
                    )
                    if cur is not None:
                        try:
                            roster_ids.add(int(cur))
                        except (ValueError, TypeError):
                            pass

        # 3. Expeditions
        for exp in self.state.get("expeditions", []):
            p_id = exp.get("sp_id") or exp.get("pokemon_id") or exp.get("species_id") or exp.get("base_id")
            if p_id is not None:
                try:
                    roster_ids.add(int(p_id))
                except (ValueError, TypeError):
                    pass

        return roster_ids

    def is_roster_full(self) -> bool:
        """Returns True if the player has every species across all evolutionary strains in their Roster."""
        return ALL_STRAIN_SPECIES_IDS.issubset(self.get_roster_species_ids())

    @staticmethod
    def parse_egg_entry(entry: Any) -> Tuple[str, int]:
        """Extracts (tier, progress) from an egg reserve entry (supports string, dict, or nested dict)."""
        prog = 0
        cur = entry
        while isinstance(cur, dict):
            if "progress" in cur and cur["progress"] is not None:
                try:
                    prog = max(prog, int(cur["progress"]))
                except (ValueError, TypeError):
                    pass
            cur = cur.get("tier", "normal")
        tier_str = str(cur or "normal").strip().lower()
        if not tier_str or tier_str == "none":
            tier_str = "normal"
        return tier_str, int(prog)

    def get_egg_hatch_threshold(self, tier: Optional[str] = None) -> int:
        """Returns the token usage required to hatch an egg (fixed 1.5M for all tiers)."""
        return getattr(self.current_difficulty, "hatch_threshold", PokemonBalance.EGG_HATCH_THRESHOLD)

    def get_egg_token_value(self, tier: str) -> int:
        """Returns the token conversion value for an egg tier."""
        clean_tier, _ = self.parse_egg_entry(tier)
        clean_tier = clean_tier.replace(" ", "_")
        return EGG_TOKEN_VALUES.get(clean_tier, EGG_TOKEN_VALUES.get(clean_tier, 30_000_000))

    def set_nursery_sort_criteria(self, criteria: str) -> Tuple[bool, str]:
        """Sets the active sort criteria for the Egg Nursery reserves."""
        crit = criteria.strip().lower()
        valid = {
            "tier": ("tier", "Tier / Rarity (Highest First)"),
            "progress": ("progress", "Incubation Progress (Highest First)"),
            "value": ("value", "Token Value (Highest First)"),
            "default": ("default", "Default (Active First, Order Obtained)"),
        }
        if crit not in valid:
            return False, "Invalid sort criteria! Options: 'tier', 'progress', 'value', 'default'."

        norm_key, label = valid[crit]
        self.state["nursery_sort_criteria"] = norm_key
        self.save()
        return True, f"🐾 Nursery sort criteria updated: {label}."

    def get_all_nursery_eggs(self) -> List[Dict[str, Any]]:
        """Returns a unified list of all eggs currently owned (active + nursery reserves).

        Each item is a dict:
        {
            'index': int,            # 1-based display index (respects active sort criteria)
            'tier': str,             # tier string (e.g. 'common', 'rare')
            'progress': int,         # current incubation tokens
            'threshold': int,        # hatch requirement (1.5M)
            'is_active': bool,       # True if actively incubating as current companion
            'source': str,           # 'active' or 'pending'
            'pending_index': Optional[int]
        }
        """
        # Migrate any stray egg_tier if player already has an active Pokémon
        if self.active_mon is not None and self.state.get("egg_tier"):
            curr_t, curr_p = self.parse_egg_entry(self.state.pop("egg_tier"))
            curr_p = max(curr_p, int(self.state.pop("egg_usage", 0) or 0))
            pending = self.state.setdefault("pending_eggs", [])
            pending.insert(0, {"tier": curr_t, "progress": curr_p})
            self.save()

        eggs = []
        thresh = self.get_egg_hatch_threshold()

        # 1. Active incubating egg (when active_mon is None)
        if self.active_mon is None and self.state.get("egg_tier"):
            curr_t, curr_p = self.parse_egg_entry(self.state["egg_tier"])
            curr_p = max(curr_p, int(self.state.get("egg_usage", 0) or 0))
            self.state["egg_tier"] = curr_t
            self.state["egg_usage"] = curr_p
            eggs.append({
                "tier": curr_t,
                "progress": curr_p,
                "threshold": thresh,
                "is_active": True,
                "source": "active",
                "pending_index": None,
                "orig_order": 0,
            })

        # 2. Eggs in Nursery reserves
        pending = self.state.get("pending_eggs", [])
        cleaned_pending = []
        pending_changed = False
        for p_idx, entry in enumerate(pending):
            t_name, prog = self.parse_egg_entry(entry)
            cleaned_pending.append({"tier": t_name, "progress": prog})
            if entry != {"tier": t_name, "progress": prog}:
                pending_changed = True
            eggs.append({
                "tier": t_name,
                "progress": prog,
                "threshold": thresh,
                "is_active": False,
                "source": "pending",
                "pending_index": p_idx,
                "orig_order": p_idx + 1,
            })

        if pending_changed:
            self.state["pending_eggs"] = cleaned_pending
            self.save()

        sort_crit = self.state.get("nursery_sort_criteria", "default")
        if sort_crit == "tier":
            eggs.sort(key=lambda e: (self.get_egg_token_value(e["tier"]), e["progress"], -e["orig_order"]), reverse=True)
        elif sort_crit == "progress":
            eggs.sort(key=lambda e: (e["progress"], self.get_egg_token_value(e["tier"]), -e["orig_order"]), reverse=True)
        elif sort_crit == "value":
            eggs.sort(key=lambda e: (self.get_egg_token_value(e["tier"]), e["progress"], -e["orig_order"]), reverse=True)
        else:
            eggs.sort(key=lambda e: (0 if e["is_active"] else 1, e["orig_order"]))

        for i, egg in enumerate(eggs, 1):
            egg["index"] = i

        return eggs

    def select_nursery_egg(self, target: str) -> Tuple[bool, str]:
        """Switches active companion to the chosen egg from the Nursery, preserving progress."""
        all_eggs = self.get_all_nursery_eggs()
        if not all_eggs:
            return False, "You don't own any Pokémon Eggs in the Nursery!"

        target_str = target.strip().lower()
        chosen = None

        # 1. Try 1-based index (e.g. 'sel 2' or 'incubate 2')
        try:
            idx = int(target_str)
            for egg in all_eggs:
                if egg["index"] == idx:
                    chosen = egg
                    break
        except ValueError:
            pass

        # 2. Try matching by tier name (e.g. 'incubate rare')
        if chosen is None:
            for egg in all_eggs:
                if target_str in egg["tier"].lower():
                    chosen = egg
                    break

        # 3. Default to first egg if target is empty, 'egg', or '0'
        if chosen is None and (target_str in ("", "egg", "0") or target_str.startswith("egg")):
            chosen = all_eggs[0]

        if chosen is None:
            return False, f"Could not find egg '{target}' in Nursery reserves."

        tier_title = chosen["tier"].replace("_", " ").title()

        if chosen["is_active"]:
            thresh = chosen["threshold"]
            pct = (chosen["progress"] / thresh) * 100 if thresh > 0 else 0
            return True, f"{tier_title} Egg is already your active incubating companion! ({pct:.1f}% hatched)"

        # Save current active Pokémon back to dex if present
        curr_active = self.active_mon
        if curr_active:
            prev_status = "graduated" if (getattr(curr_active, "is_graduated", False) or f"{curr_active.base_id}_{curr_active.current_id}" in self.state.get("collected_finals", [])) else "inactive"
            self._register_to_dex(curr_active, status=prev_status)
            self.set_active_mon(None)

        # Stash previously active egg back to Nursery reserves if present
        curr_tier = self.state.get("egg_tier")
        pending = self.state.setdefault("pending_eggs", [])
        if curr_tier:
            curr_t, curr_p = self.parse_egg_entry(curr_tier)
            curr_p = max(curr_p, int(self.state.get("egg_usage", 0) or 0))
            pending.append({"tier": curr_t, "progress": curr_p})

        # Remove chosen egg from pending_eggs
        if chosen["source"] == "pending" and chosen["pending_index"] is not None:
            pending.pop(chosen["pending_index"])

        self.state["egg_tier"] = chosen["tier"]
        self.state["egg_usage"] = chosen["progress"]
        self.state["pending_eggs"] = pending
        self.save()

        thresh = chosen["threshold"]
        pct = (chosen["progress"] / thresh) * 100 if thresh > 0 else 0
        return True, f"Switched active companion to Incubating {tier_title} Egg! ({pct:.1f}% hatched)"

    def load_incubator_egg(self, target: str) -> Tuple[bool, str]:
        """Alias for select_nursery_egg."""
        return self.select_nursery_egg(target)

    def sell_nursery_egg(self, target: str) -> Tuple[bool, str, Optional[int]]:
        """Sells an egg from the Nursery (or active incubator) for tokens."""
        all_eggs = self.get_all_nursery_eggs()
        if not all_eggs:
            return False, "You don't have any eggs in the Nursery to sell!", None

        target_str = target.strip().lower()

        # Handle 'sell all' or 'sell all <tier>'
        if target_str.startswith("all"):
            sub_tier = target_str.split()[1] if len(target_str.split()) > 1 else None
            pending = self.state.get("pending_eggs", [])
            new_pending = []
            sold_count = 0
            total_cash = 0

            for p in pending:
                t_name, _ = self.parse_egg_entry(p)
                if sub_tier is None or sub_tier in t_name.lower():
                    val = self.get_egg_token_value(t_name)
                    total_cash += val
                    sold_count += 1
                else:
                    new_pending.append(p)

            if sold_count == 0:
                filter_desc = f" matching '{sub_tier}'" if sub_tier else ""
                return False, f"No reserve eggs{filter_desc} found to sell in Nursery.", None

            self.state["pending_eggs"] = new_pending
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - total_cash
            self.save()
            return True, f"Sold {sold_count} reserve Egg(s) for {format_tokens(total_cash)} tokens!", total_cash

        # Try matching by 1-based index in all_eggs
        chosen = None
        try:
            idx = int(target_str)
            for egg in all_eggs:
                if egg["index"] == idx:
                    chosen = egg
                    break
        except ValueError:
            pass

        # Try matching by tier name
        if chosen is None:
            for egg in all_eggs:
                if target_str in egg["tier"].lower() or (target_str in ("incubator", "active") and egg["is_active"]):
                    chosen = egg
                    break

        if chosen is None:
            return False, f"Could not find egg '{target}' in Nursery.", None

        tier_title = chosen["tier"].replace("_", " ").title()
        cash = self.get_egg_token_value(chosen["tier"])

        if chosen["source"] == "active":
            self.state["egg_tier"] = None
            self.state["egg_usage"] = 0
        elif chosen["source"] == "pending" and chosen["pending_index"] is not None:
            pending = self.state.get("pending_eggs", [])
            if 0 <= chosen["pending_index"] < len(pending):
                pending.pop(chosen["pending_index"])
                self.state["pending_eggs"] = pending

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - cash
        self.save()
        return True, f"Sold 1x {tier_title} Egg from Nursery for {format_tokens(cash)} tokens!", cash

    def sell_egg(self, target: str) -> Tuple[bool, str, Optional[int]]:
        """Alias for sell_nursery_egg."""
        return self.sell_nursery_egg(target)

    def obtain_egg(self, tier: str) -> Tuple[bool, str, Optional[int]]:
        """Obtains an egg of the specified tier, or converts it to tokens if the Roster is full."""
        tier_str = str(tier or "common").replace("_", " ").title()
        if self.is_roster_full():
            cash_val = self.get_egg_token_value(tier)
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - cash_val
            self.save()
            return True, f"🌟 Living Roster Full! Your obtained {tier_str} Egg was automatically converted into {format_tokens(cash_val)} tokens!", cash_val

        current_tier = self.state.get("egg_tier")
        if self.active_mon is None and current_tier is None:
            self.state["egg_tier"] = str(tier).lower()
            self.state["egg_usage"] = 0
            self.save()
            return True, f"Obtained a fresh {tier_str} Egg! Now loaded as your active companion.", None
        else:
            pending = self.state.setdefault("pending_eggs", [])
            pending.append({"tier": str(tier).lower(), "progress": 0})
            self.save()
            return True, f"Obtained a {tier_str} Egg! Added to your Egg Nursery.", None

    def hatch_egg(self, initial_xp: int = 0, force_tier: Optional[str] = None, force_shiny: bool = False, preserve_active: bool = False) -> Tuple[MonState, List[str]]:
        events = []
        used_tier = force_tier or self.state.get("egg_tier") or "common"
        if used_tier == "normal":
            used_tier = "common"
        
        # Clean up active egg keys completely
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

        if preserve_active and self.active_mon is not None:
            self._register_to_dex(mon, status="inactive")
            hatch_milestone = f"Egg Hatched! You got a {shiny_str}{species_name} (#{base_id})! (Sent to Roster)"
            self.state["last_evolution"] = hatch_milestone
            self.state["last_milestone"] = hatch_milestone
            events.append(f"🐣 Oh? Your Egg Hatched! You got a {shiny_str}{species_name} (#{base_id})! Joined your Roster. Rarity: {rarity.value.upper()}")
        else:
            self.set_active_mon(mon)
            self._register_to_dex(mon, status="active")
            hatch_milestone = f"Egg Hatched! You got a {shiny_str}{species_name} (#{base_id})!"
            self.state["last_evolution"] = hatch_milestone
            self.state["last_milestone"] = hatch_milestone
            events.append(f"🐣 Egg Hatched! You got a {shiny_str}{species_name} (#{base_id})! Rarity: {rarity.value.upper()}")

        events.extend(self._progress_quest_by_type("progression"))
        return mon, events

    def _pick_species(self, tier_guarantee: Optional[str] = None) -> Tuple[int, Rarity, List[int], bool]:
        # 1. Collect all species IDs present in the active Roster
        roster_ids = self.get_roster_species_ids()

        # 2. Select candidate pool based on tier guarantee
        if tier_guarantee == "mysterious fetal form":
            if 151 not in roster_ids:
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

        # 3. Strict No-Duplicate Filter: exclude any species that is already in active Roster
        filtered_candidates = [c for c in candidates if c[0] not in roster_ids]

        # 4. Fallback if requested tier is exhausted: search unowned species from broader pool
        if not filtered_candidates:
            if tier_guarantee in ("legendary", "mysterious fetal form", "shadow_fetal"):
                # If requested legendary/mythical pool is exhausted, search any unowned legendary
                filtered_candidates = [c for c in BASE_SPECIES_STARTERS if c[3] and c[0] not in roster_ids]
                # If all legendaries are in roster, find any unowned species
                if not filtered_candidates:
                    filtered_candidates = [c for c in BASE_SPECIES_STARTERS if c[0] not in roster_ids]
            else:
                # If tier pool is exhausted, search any unowned non-legendary species
                filtered_candidates = [c for c in BASE_SPECIES_STARTERS if not c[3] and c[0] not in roster_ids]
                # If all non-legendaries are in roster, search any unowned species (including legendaries)
                if not filtered_candidates:
                    filtered_candidates = [c for c in BASE_SPECIES_STARTERS if c[0] not in roster_ids]

        # 5. True 100% full-game completion fallback (only occurs if player literally owns all base species in roster)
        if not filtered_candidates:
            filtered_candidates = candidates

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

    def buy_egg(self, tier: Optional[Rarity] = None) -> Tuple[bool, str]:
        if self.is_roster_full():
            return False, "Your Roster is completely full! You already own every Pokémon across all evolutionary stages."

        diff = self.current_difficulty
        costs = diff.shop_prices
        tier_key = tier.value if tier else "normal"
        cost = costs.get("egg_rare" if tier == Rarity.RARE else ("egg_uncommon" if tier == Rarity.UNCOMMON else "egg_normal"), 30_000_000)
        cost = int(cost * self.get_devon_multiplier())

        if self.available_tokens < cost:
            return False, f"Not enough tokens! Required: {format_tokens(cost)}, Available: {format_tokens(self.available_tokens)}"

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
        self._record_catalyst("shop_tokens_spent", cost)

        # Clean up legacy keys
        self.state.pop("incubating_eggs", None)
        self.state.pop("current_egg_tier", None)

        tier_str = f"{tier.value.upper()}+" if tier else "Standard"
        if self.active_mon is None and not self.state.get("egg_tier"):
            self.state["egg_usage"] = 0
            self.state["egg_tier"] = tier_key
            self.save()
            return True, f"Obtained a fresh {tier_str} Pokémon Egg! Now loaded as your active companion."
        else:
            pending = self.state.setdefault("pending_eggs", [])
            pending.append({"tier": tier_key, "progress": 0})
            self.save()
            return True, f"Obtained a fresh {tier_str} Pokémon Egg! Added to your Egg Nursery."
