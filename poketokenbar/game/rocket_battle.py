import random
from typing import Tuple, List, Dict, Any, Optional

# Type Matchup Chart (Expanded with Glitch typing)
TYPE_MATCHUPS: Dict[str, Dict[str, List[str]]] = {
    "normal": {"super": [], "weak": ["rock", "steel"], "immune": ["ghost"]},
    "fire": {"super": ["grass", "ice", "bug", "steel"], "weak": ["fire", "water", "rock", "dragon"], "immune": []},
    "water": {"super": ["fire", "ground", "rock"], "weak": ["water", "grass", "dragon"], "immune": []},
    "electric": {"super": ["water", "flying"], "weak": ["electric", "grass", "dragon"], "immune": ["ground"]},
    "grass": {"super": ["water", "ground", "rock"], "weak": ["fire", "grass", "poison", "flying", "bug", "dragon", "steel"], "immune": []},
    "ice": {"super": ["grass", "ground", "flying", "dragon"], "weak": ["fire", "water", "ice", "steel"], "immune": []},
    "fighting": {"super": ["normal", "ice", "rock", "dark", "steel"], "weak": ["poison", "flying", "psychic", "bug", "fairy"], "immune": ["ghost", "glitch"]},
    "poison": {"super": ["grass", "fairy"], "weak": ["poison", "ground", "rock", "ghost"], "immune": ["steel"]},
    "ground": {"super": ["fire", "electric", "poison", "rock", "steel"], "weak": ["grass", "bug"], "immune": ["flying"]},
    "flying": {"super": ["grass", "fighting", "bug"], "weak": ["electric", "rock", "steel"], "immune": []},
    "psychic": {"super": ["fighting", "poison"], "weak": ["psychic", "steel"], "immune": ["dark"]},
    "bug": {"super": ["grass", "psychic", "dark"], "weak": ["fire", "fighting", "poison", "flying", "ghost", "steel", "fairy"], "immune": []},
    "rock": {"super": ["fire", "ice", "flying", "bug"], "weak": ["fighting", "ground", "steel"], "immune": []},
    "ghost": {"super": ["psychic", "ghost"], "weak": ["dark"], "immune": ["normal", "fighting"]},
    "dragon": {"super": ["dragon"], "weak": ["steel"], "immune": ["fairy"]},
    "dark": {"super": ["psychic", "ghost"], "weak": ["fighting", "dark", "fairy"], "immune": []},
    "steel": {"super": ["ice", "rock", "fairy"], "weak": ["fire", "water", "electric", "steel"], "immune": []},
    "fairy": {"super": ["fighting", "dragon", "dark"], "weak": ["fire", "poison", "steel"], "immune": []},
    "glitch": {"super": ["psychic", "ghost", "normal"], "weak": ["electric", "rock", "bug"], "immune": ["fighting"]}
}

def get_effectiveness(attack_type: str, defend_type: str) -> float:
    """Calculates type effectiveness multiplier (2.0, 1.0, 0.5, 0.0)."""
    if not attack_type or not defend_type:
        return 1.0
    attack_type = attack_type.lower()
    defend_type = defend_type.lower()
    if attack_type not in TYPE_MATCHUPS:
        return 1.0

    matchup = TYPE_MATCHUPS[attack_type]
    if defend_type in matchup["super"]:
        return 2.0
    if defend_type in matchup["weak"]:
        return 0.5
    if defend_type in matchup["immune"]:
        return 0.0
    return 1.0

def generate_player_moves(primary_type: str) -> List[Dict[str, Any]]:
    """Generates 4 tactical combat moves based on companion type."""
    t = primary_type.lower() if primary_type else "normal"
    t_name = t.capitalize()
    return [
        {"name": f"{t_name} Strike", "type": t, "cost": 500_000, "power": 55, "desc": "Light STAB strike"},
        {"name": f"{t_name} Blast", "type": t, "cost": 2_000_000, "power": 125, "desc": "Heavy STAB attack"},
        {"name": "Nanite Recover", "type": "normal", "cost": 1_500_000, "power": 0, "desc": "Heal 30% Max HP"},
        {"name": "Rocket Overclock", "type": "steel", "cost": 5_000_000, "power": 230, "desc": "Massive syndicate strike"}
    ]

# Boss Team Definitions for Syndicate Boss Operations
ROCKET_BOSS_TEAMS: Dict[str, Dict[str, Any]] = {
    "3": {
        "title": "Silph Sub-Vault 4: Prototype Chimera-001",
        "location": "Silph Co. Sealed Sub-Basement // Saffron City",
        "team": [
            {
                "id": 2012,
                "name": "Prototype Chimera-001",
                "title": "Vault Sovereign: Tri-Elemental Bio-Weapon",
                "type": "fire",
                "stances": ["fire", "ice", "electric", "dragon"],
                "stance_idx": 0,
                "max_hp": 150_000,
                "moves": ["Tri-Overclock", "Mutagen Breath", "Titanium Shell", "Stance Shift"]
            }
        ]
    },
    "6": {
        "title": "Abandoned Power Plant: Cyber-Enforcer Core",
        "location": "Route 10 Power Plant Reactor // Kanto Coast",
        "team": [
            {
                "id": 2013,
                "name": "Cyber-Zapdos Core",
                "title": "Oak's Mechanized Reactor Boss",
                "type": "steel",
                "max_hp": 200_000,
                "moves": ["Railgun Blast", "EMP Pulse", "Nanite Repair", "Drill Peck"]
            }
        ]
    },
    "9": {
        "title": "Cinnabar Caldera Laboratory: Apex Vanguard",
        "location": "Volcanic Magma Chamber // Cinnabar Island",
        "team": [
            {
                "id": 2014,
                "name": "Apex Vanguard Mon-Omega",
                "title": "Oak's Supreme Genetic Construct",
                "type": "psychic",
                "max_hp": 300_000,
                "moves": ["Psionic Cataclysm", "Cosmic Core", "Dimension Warp", "Omega Beam"]
            }
        ]
    },
    "10": {
        "title": "The Himalayan Citadel: Arch-Director Samuel Oak",
        "location": "Mountaintop Fortress // Himalayan Range",
        "team": [
            {
                "id": 2001,
                "name": "Arch-Director Samuel Oak & Master Core",
                "title": "Supreme Syndicate Commander",
                "type": "steel",
                "max_hp": 350_000,
                "moves": ["Syndicate Override", "Omega Judgment", "Bio-Convergence", "Hyper Beam"]
            }
        ]
    }
}

class RocketBattleHandler:
    """Manages dynamic, turn-based combat against Syndicate Bosses in Rocket HQ."""

    def __init__(self, engine):
        self.engine = engine

    def _get_state(self) -> Dict[str, Any]:
        return self.engine.state.get("rocket_battle_state", {})

    def _save_state(self, st: Dict[str, Any]):
        self.engine.state["rocket_battle_state"] = st
        self.engine.save()

    def get_rocket_tokens(self) -> int:
        """Returns spendable combat token budget for tactical moves."""
        st = self._get_state()
        if not st:
            return 25_000_000
        baseline = st.get("baseline_global_tokens", self.engine.state.get("used_since_install", 0))
        current = self.engine.state.get("used_since_install", 0)
        earned = max(0, current - baseline)
        return 25_000_000 + earned - st.get("rocket_spent_tokens", 0)

    def auto_assemble_squad(self) -> List[int]:
        """Automatically builds a 6-member Strike Squad starting with active companion."""
        squad_ids = []
        active = self.engine.active_mon
        if active:
            squad_ids.append(active.current_id)

        dex_list = self.engine.state.get("dex", [])
        def get_xp(entry):
            ms = entry.get("mon_state", {})
            return ms.get("used_at_stage", 0) if isinstance(ms, dict) else 0

        sorted_dex = sorted(dex_list, key=get_xp, reverse=True)
        for d in sorted_dex:
            pid = d.get("species_id", d.get("final_id", d.get("base_id")))
            if pid and pid not in squad_ids:
                squad_ids.append(pid)
                if len(squad_ids) >= 6:
                    break

        if not squad_ids:
            squad_ids = [4, 1, 7, 25, 143, 149] # Safe fallback
        return squad_ids

    def start_boss_battle(self, op_code: str, custom_squad: Optional[List[int]] = None) -> Tuple[bool, str]:
        """Initializes a tactical boss encounter for a given operation code."""
        clean_code = str(op_code).replace("op_", "").strip()
        if clean_code not in ROCKET_BOSS_TEAMS:
            return False, f"Operation {clean_code} is not a Syndicate Boss encounter."

        boss_def = ROCKET_BOSS_TEAMS[clean_code]
        team_ids = custom_squad if custom_squad else self.auto_assemble_squad()

        dex_list = self.engine.state.get("dex", [])
        dex_map = {d.get("species_id", d.get("final_id", d.get("base_id"))): d for d in dex_list}

        # Calculate HP for each squad member
        hps = []
        for pid in team_ids:
            if pid in dex_map:
                ms = dex_map[pid].get("mon_state", {})
                xp = ms.get("used_at_stage", 0) if isinstance(ms, dict) else 0
                stage = ms.get("stage_index", 0) if isinstance(ms, dict) else 0
                hp = min(1_000_000, 50_000 + (stage * 100_000) + (xp // 100))
            else:
                hp = 100_000
            hps.append(hp)

        import copy
        boss_team = copy.deepcopy(boss_def["team"])
        boss_hps = [b["max_hp"] for b in boss_team]
        boss_max_hps = list(boss_hps)

        op_id = f"op_{clean_code}"
        ops_st = self.engine.state.setdefault("rocket_ops", {}).setdefault(op_id, {})
        current_rem = ops_st.get("boss_hp_remaining")
        if current_rem and 0 < current_rem < boss_hps[0]:
            boss_hps[0] = current_rem

        first_boss = boss_team[0]
        st = {
            "op_code": clean_code,
            "title": boss_def["title"],
            "location": boss_def["location"],
            "player_team": team_ids,
            "player_hps": list(hps),
            "player_max_hps": list(hps),
            "player_active_index": 0,
            "boss_team": boss_team,
            "boss_hps": boss_hps,
            "boss_max_hps": boss_max_hps,
            "boss_active_index": 0,
            "turn_count": 0,
            "turn_log": [
                f"🚨 Breach initiated into {boss_def['location']}!",
                f"⚠️ Security breach detected! {first_boss['name']} emerges from the bio-vat!"
            ],
            "baseline_global_tokens": self.engine.state.get("used_since_install", 0),
            "rocket_spent_tokens": 0,
            "status": "in_combat"
        }
        self._save_state(st)
        ops_st["boss_hp_remaining"] = boss_hps[0]
        ops_st["objective_done"] = False
        self.engine.save()
        return True, f"🚀 Deployed into {boss_def['title']}! Engage {first_boss['name']}!"

    def execute_turn(self, move_index: int) -> Tuple[bool, str]:
        """Executes a combat turn where player attacks and boss retaliates."""
        st = self._get_state()
        if not st.get("player_team") or st.get("status") in ["win", "loss"]:
            return False, "No active boss encounter. Type 'engage' or 'start operation' to deploy."

        p_idx = st["player_active_index"]
        if st["player_hps"][p_idx] <= 0:
            return False, "Active Pokémon has fainted! Use 'swap 1-6' to send in another squad member."

        r_idx = st["boss_active_index"]
        if st["boss_hps"][r_idx] <= 0:
            return False, "Opponent is already neutralized!"

        p_id = st["player_team"][p_idx]
        sp = self.engine.api.get_pokemon_info(p_id)
        p_type = sp["types"][0]["type"]["name"] if sp and "types" in sp else "normal"

        moves = generate_player_moves(p_type)
        if move_index < 0 or move_index >= len(moves):
            return False, "Invalid move selection. Choose 1, 2, 3, or 4."

        move = moves[move_index]
        cost = move["cost"]
        spendable = self.get_rocket_tokens()
        if spendable < cost:
            return False, f"Insufficient tactical tokens! Need {cost:,} (Available: {spendable:,})."

        st["rocket_spent_tokens"] = st.get("rocket_spent_tokens", 0) + cost
        st["turn_count"] = st.get("turn_count", 0) + 1

        p_name = self.engine.api.get_species_name(p_id)
        r_mon = st["boss_team"][r_idx]
        logs = []

        # --- 1. PLAYER TURN ---
        if move["name"] == "Nanite Recover":
            heal = int(st["player_max_hps"][p_idx] * 0.30)
            st["player_hps"][p_idx] = min(st["player_max_hps"][p_idx], st["player_hps"][p_idx] + heal)
            logs.append(f"🛡️ {p_name} deployed Nanite Recover! (+{heal:,} HP)")
        else:
            eff = get_effectiveness(move["type"], r_mon["type"])
            dmg = int(move["power"] * 480 * eff)
            active = self.engine.active_mon
            if active and active.current_id == p_id:
                if getattr(active, "is_mega", False):
                    dmg = int(dmg * 1.5)
                if active.held_item in ["choice_band", "choice_specs"]:
                    dmg = int(dmg * 1.5)
                elif active.held_item == "life_orb":
                    dmg = int(dmg * 1.2)

            dmg = max(1000, dmg + random.randint(-500, 500))
            st["boss_hps"][r_idx] = max(0, st["boss_hps"][r_idx] - dmg)
            eff_str = " (Super Effective! 💥)" if eff > 1.5 else (" (Not very effective...)" if eff < 0.9 else "")
            logs.append(f"⚔️ {p_name} used {move['name']}!{eff_str} (-{dmg:,} HP)")

        # Update rocket_ops boss_hp_remaining for telemetry display
        op_id = f"op_{st['op_code']}"
        ops_st = self.engine.state.setdefault("rocket_ops", {}).setdefault(op_id, {})
        ops_st["boss_hp_remaining"] = st["boss_hps"][r_idx]

        # --- 2. CHECK BOSS FAINT / PROGRESSION ---
        if st["boss_hps"][r_idx] <= 0:
            logs.append(f"💥 {r_mon['name']} was defeated and collapsed!")
            if r_idx + 1 < len(st["boss_team"]):
                st["boss_active_index"] += 1
                next_mon = st["boss_team"][st["boss_active_index"]]
                logs.append(f"🚨 ALARM: Containment failure! {next_mon['name']} enters the arena!")
                if next_mon.get("name") == "Prototype Chimera-001":
                    logs.append("⚠️ PROTOTYPE CHIMERA-001 has awakened! Multi-elemental cores online!")
                ops_st["boss_hp_remaining"] = next_mon["max_hp"]
                existing_logs = st.get("turn_log", [])
                existing_logs.extend(logs)
                st["turn_log"] = existing_logs[-5:]
                self._save_state(st)
                return True, "\n".join(logs)
            else:
                # ALL BOSSES DEFEATED -> VICTORY!
                st["status"] = "win"
                ops_st["objective_done"] = True
                ops_st["boss_hp_remaining"] = 0
                logs.append("🏆 VICTORY! All syndicate bio-aberrations neutralized!")
                logs.append(f"➔ Type 'claim {st['op_code']}' or 'claim' to finalize and collect rewards!")
                existing_logs = st.get("turn_log", [])
                existing_logs.extend(logs)
                st["turn_log"] = existing_logs[-5:]
                self._save_state(st)
                return True, "\n".join(logs)

        # --- 3. BOSS RETALIATION ---
        r_move = random.choice(r_mon["moves"])

        # Special Boss Gimmicks
        if r_move == "Stance Shift" or (r_mon.get("stances") and st["turn_count"] % 2 == 0):
            stances = r_mon.get("stances", ["fire", "ice", "electric", "dragon"])
            cur_idx = r_mon.get("stance_idx", 0)
            new_idx = (cur_idx + 1) % len(stances)
            r_mon["stance_idx"] = new_idx
            r_mon["type"] = stances[new_idx]
            core_name = r_mon["type"].upper() + " CORE"
            logs.append(f"🔄 Chimera-001 shifted elemental matrix to {core_name}!")

        elif r_move == "Buffer Overflow":
            logs.append("👾 MissingNo. injected BUFFER OVERFLOW! Glitched memory packets scrambled the arena!")

        elif r_move in ["Shell Spore", "Leech Seed"]:
            boss_heal = min(15_000, r_mon["max_hp"] - st["boss_hps"][r_idx])
            st["boss_hps"][r_idx] += boss_heal
            logs.append(f"🌿 Venustoise absorbed organic nutrients with {r_move}! (+{boss_heal:,} HP)")

        # Determine Boss Damage
        b_eff = get_effectiveness(r_mon["type"], p_type)
        base_boss_dmg = random.randint(18_000, 26_000)
        boss_dmg = int(base_boss_dmg * b_eff)

        active = self.engine.active_mon
        if active and active.current_id == p_id and active.held_item == "assault_vest":
            boss_dmg = int(boss_dmg * 0.8)

        st["player_hps"][p_idx] = max(0, st["player_hps"][p_idx] - boss_dmg)
        b_eff_str = " (Super Effective! ⚠️)" if b_eff > 1.5 else (" (Not very effective...)" if b_eff < 0.9 else "")
        logs.append(f"💥 {r_mon['name']} struck with {r_move}!{b_eff_str} (-{boss_dmg:,} HP)")

        # --- 4. CHECK PLAYER FAINT ---
        if st["player_hps"][p_idx] <= 0:
            logs.append(f"💀 {p_name} fainted!")
            if all(hp <= 0 for hp in st["player_hps"]):
                st["status"] = "loss"
                logs.append("🚨 Strike Squad blacked out! Sub-vault security expelled your team.")
                logs.append("➔ Type 'restart' or 'engage' to regroup and deploy again!")
            else:
                logs.append("➔ Swap to an active squad member with 'swap 1-6'!")

        existing_logs = st.get("turn_log", [])
        existing_logs.extend(logs)
        st["turn_log"] = existing_logs[-5:]
        self._save_state(st)
        return True, "\n".join(logs)

    def swap_pokemon(self, slot_index: int) -> Tuple[bool, str]:
        """Swaps active squad member and triggers Boss retaliation against incoming Pokémon."""
        st = self._get_state()
        if not st.get("player_team") or st.get("status") in ["win", "loss"]:
            return False, "No active encounter to swap Pokémon."

        if slot_index < 0 or slot_index >= len(st["player_team"]):
            return False, f"Invalid squad slot. Choose 1 through {len(st['player_team'])}."

        if st["player_hps"][slot_index] <= 0:
            return False, "That Pokémon has fainted!"

        if st["player_active_index"] == slot_index:
            return False, "That Pokémon is already in battle!"

        st["player_active_index"] = slot_index
        p_id = st["player_team"][slot_index]
        p_name = self.engine.api.get_species_name(p_id)
        logs = [f"🔄 Sent out {p_name}!"]

        # Boss Retaliates against incoming swap
        r_idx = st["boss_active_index"]
        r_mon = st["boss_team"][r_idx]
        sp = self.engine.api.get_pokemon_info(p_id)
        p_type = sp["types"][0]["type"]["name"] if sp and "types" in sp else "normal"

        r_move = random.choice(r_mon["moves"])
        eff = get_effectiveness(r_mon["type"], p_type)
        dmg = int(random.randint(15_000, 24_000) * eff)
        st["player_hps"][slot_index] = max(0, st["player_hps"][slot_index] - dmg)
        eff_str = " (Super Effective!)" if eff > 1.5 else ""
        logs.append(f"⚡ {r_mon['name']} caught the incoming swap with {r_move}!{eff_str} (-{dmg:,} HP)")

        if st["player_hps"][slot_index] <= 0:
            logs.append(f"💀 {p_name} fainted!")
            if all(hp <= 0 for hp in st["player_hps"]):
                st["status"] = "loss"
                logs.append("🚨 Strike Squad blacked out! Type 'engage' to try again.")

        existing_logs = st.get("turn_log", [])
        existing_logs.extend(logs)
        st["turn_log"] = existing_logs[-5:]
        self._save_state(st)
        return True, "\n".join(logs)

    def run_away(self) -> Tuple[bool, str]:
        """Disengages from combat and clears combat state."""
        st = self._get_state()
        if not st.get("player_team"):
            return False, "You are not in combat."
        self._save_state({})
        return True, "Tactical retreat executed. Returned to Rocket Operations command."
