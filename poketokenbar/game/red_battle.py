import random
from typing import Tuple, List, Dict

# Type Matchup Chart (Simplified)
# Format: "attacking_type": {"super": [defending_types], "weak": [defending_types], "immune": [defending_types]}
TYPE_MATCHUPS = {
    "normal": {"super": [], "weak": ["rock", "steel"], "immune": ["ghost"]},
    "fire": {"super": ["grass", "ice", "bug", "steel"], "weak": ["fire", "water", "rock", "dragon"], "immune": []},
    "water": {"super": ["fire", "ground", "rock"], "weak": ["water", "grass", "dragon"], "immune": []},
    "electric": {"super": ["water", "flying"], "weak": ["electric", "grass", "dragon"], "immune": ["ground"]},
    "grass": {"super": ["water", "ground", "rock"], "weak": ["fire", "grass", "poison", "flying", "bug", "dragon", "steel"], "immune": []},
    "ice": {"super": ["grass", "ground", "flying", "dragon"], "weak": ["fire", "water", "ice", "steel"], "immune": []},
    "fighting": {"super": ["normal", "ice", "rock", "dark", "steel"], "weak": ["poison", "flying", "psychic", "bug", "fairy"], "immune": ["ghost"]},
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
    "fairy": {"super": ["fighting", "dragon", "dark"], "weak": ["fire", "poison", "steel"], "immune": []}
}

RED_TEAM = [
    {"id": 25, "name": "Pikachu", "type": "electric", "max_hp": 150_000, "moves": ["Thunderbolt", "Iron Tail"]},
    {"id": 196, "name": "Espeon", "type": "psychic", "max_hp": 300_000, "moves": ["Psychic", "Shadow Ball"]},
    {"id": 143, "name": "Snorlax", "type": "normal", "max_hp": 800_000, "moves": ["Body Slam", "Crunch"]},
    {"id": 3, "name": "Venusaur", "type": "grass", "max_hp": 450_000, "moves": ["Frenzy Plant", "Sludge Bomb"]},
    {"id": 9, "name": "Blastoise", "type": "water", "max_hp": 500_000, "moves": ["Hydro Cannon", "Blizzard"]},
    {"id": 6, "name": "Charizard", "type": "fire", "max_hp": 400_000, "moves": ["Blast Burn", "Air Slash"]}
]

def get_effectiveness(attack_type: str, defend_type: str) -> float:
    if not attack_type or not defend_type: return 1.0
    attack_type = attack_type.lower()
    defend_type = defend_type.lower()
    if attack_type not in TYPE_MATCHUPS: return 1.0
    
    matchup = TYPE_MATCHUPS[attack_type]
    if defend_type in matchup["super"]: return 2.0
    if defend_type in matchup["weak"]: return 0.5
    if defend_type in matchup["immune"]: return 0.0
    return 1.0

def generate_player_moves(primary_type: str) -> List[Dict]:
    t = primary_type.lower() if primary_type else "normal"
    return [
        {"name": f"{primary_type.capitalize()} Strike", "type": t, "cost": 500_000, "power": 50, "desc": "Basic STAB attack"},
        {"name": f"{primary_type.capitalize()} Blast", "type": t, "cost": 2_000_000, "power": 120, "desc": "Heavy STAB attack"},
        {"name": "Recover", "type": "normal", "cost": 1_500_000, "power": 0, "desc": "Heal 30% HP"},
        {"name": "Hyper Beam", "type": "normal", "cost": 5_000_000, "power": 200, "desc": "Massive damage"}
    ]

class RedBattleHandler:
    def __init__(self, engine):
        self.engine = engine

    def _get_state(self):
        return self.engine.state.get("red_battle_state", {})
        
    def _save_state(self, st: dict):
        self.engine.state["red_battle_state"] = st
        self.engine.save()

    def get_red_tokens(self) -> int:
        st = self._get_state()
        if not st:
            return 0
        baseline = st.get("baseline_global_tokens", self.engine.state.get("used_since_install", 0))
        current = self.engine.state.get("used_since_install", 0)
        earned = max(0, current - baseline)
        return 20_000_000 + earned - st.get("red_spent_tokens", 0)

    def assemble_team(self, team_ids: List[int]) -> Tuple[bool, str]:
        if len(team_ids) != 6:
            return False, "You must provide exactly 6 Pokédex IDs."
        dex_list = self.engine.state.get("dex", [])
        dex_map = {d.get("species_id", d.get("final_id", d.get("base_id"))): d for d in dex_list}
        
        expeditions = self.engine.state.get("expeditions", [])
        exp_ids = {e["sp_id"] for e in expeditions}
        
        for pid in team_ids:
            if pid not in dex_map:
                return False, f"You don't own Pokémon #{pid}!"
            if pid in exp_ids:
                name = self.engine.api.get_species_name(pid)
                return False, f"Cannot assemble {name}! They are currently away on an expedition."
        
        # Calculate max HP for each member based on their XP (tokens)
        hps = []
        names = []
        types = []
        for pid in team_ids:
            data = dex_map[pid]
            mon_state = data.get("mon_state", {})
            xp = mon_state.get("used_at_stage", 0) if isinstance(mon_state, dict) else 0
            stage = mon_state.get("stage_index", 0) if isinstance(mon_state, dict) else 0
            
            # Level scaling: 50,000 base + 100,000 per stage + 1 HP per 100 XP. Max out at 1,000,000 HP.
            hp = min(1_000_000, 50_000 + (stage * 100_000) + (xp // 100))
            hps.append(hp)
            
            # Get species info from engine API
            sp = self.engine.api.get_pokemon_species(pid)
            names.append(sp.get("name", "Unknown").capitalize() if sp else f"#{pid}")
            # Primary type
            t = "normal"
            if sp and "types" in sp:
                # sp["types"] is usually a list or string depending on how it's stored. 
                # Let's just pull it dynamically. Wait, api might return types.
                # If not, fallback to normal. We can fix this in UI.
                pass
            
        st = {
            "player_team": team_ids,
            "player_hps": hps,
            "player_max_hps": hps,
            "player_active_index": 0,
            
            "red_team": [dict(r) for r in RED_TEAM],
            "red_hps": [r["max_hp"] for r in RED_TEAM],
            "red_max_hps": [r["max_hp"] for r in RED_TEAM],
            "red_active_index": 0,
            
            "turn_log": ["Battle started! Red sent out Pikachu!"],
            "baseline_global_tokens": self.engine.state.get("used_since_install", 0),
            "red_spent_tokens": 0
        }
        self._save_state(st)
        return True, "Team assembled! Let the battle on Mt. Silver begin!"

    def run_away(self) -> Tuple[bool, str]:
        st = self._get_state()
        if not st.get("player_team"):
            return False, "You are not in a battle."
        self._save_state({}) # Clear state
        return True, "You fled from Mt. Silver... Red's team has fully healed."

    def swap_pokemon(self, index: int) -> Tuple[bool, str]:
        st = self._get_state()
        if not st.get("player_team"):
            return False, "You must assemble your team first!"
        if index < 0 or index > 5:
            return False, "Invalid team index. Choose 1-6."
        if st["player_hps"][index] <= 0:
            return False, "That Pokémon has fainted!"
        if st["player_active_index"] == index:
            return False, "That Pokémon is already in battle!"
            
        st["player_active_index"] = index
        name = self.engine.api.get_species_name(st["player_team"][index])
        
        logs = [f"You sent out {name}!"]
        
        # Red Retaliates
        p_idx = index
        p_id = st["player_team"][p_idx]
        sp = self.engine.api.get_pokemon_info(p_id)
        p_type = sp["types"][0]["type"]["name"] if sp and "types" in sp else "normal"
        
        r_idx = st["red_active_index"]
        r_mon = st["red_team"][r_idx]
        
        r_move = random.choice(r_mon["moves"])
        eff = get_effectiveness(r_mon["type"], p_type)
        dmg = int(30_000 * eff)
        st["player_hps"][p_idx] = max(0, st["player_hps"][p_idx] - dmg)
        
        enemy_prefix = "Red's" if not st.get("arceus_phase") else "Godly"
        eff_str = " It's super effective!" if eff > 1.5 else (" It's not very effective..." if eff < 0.9 else "")
        logs.append(f"{enemy_prefix} {r_mon['name']} used {r_move}!{eff_str} (-{dmg} HP)")
        
        if st["player_hps"][p_idx] <= 0:
            logs.append(f"{name} fainted!")
            if all(hp <= 0 for hp in st["player_hps"]):
                logs.append("You blacked out! Red's team has healed. Try again...")
                st["status"] = "loss"
                existing_logs = st.get("turn_log", [])
                existing_logs.extend(logs)
                st["turn_log"] = existing_logs[-5:]
                self._save_state(st)
                return True, "\n".join(logs)
                
        existing_logs = st.get("turn_log", [])
        existing_logs.extend(logs)
        st["turn_log"] = existing_logs[-5:]
        
        self._save_state(st)
        return True, f"Swapped to {name}!"

    def execute_turn(self, move_index: int) -> Tuple[bool, str]:
        st = self._get_state()
        if not st.get("player_team"):
            return False, "Assemble a team first!"
            
        p_idx = st["player_active_index"]
        if st["player_hps"][p_idx] <= 0:
            return False, "Your active Pokémon has fainted! Swap to another one."
            
        r_idx = st["red_active_index"]
        if st["red_hps"][r_idx] <= 0:
            return False, "Red's Pokémon has fainted! (Wait, how did you get here?)"

        p_id = st["player_team"][p_idx]
        sp = self.engine.api.get_pokemon_info(p_id)
        if sp and "types" in sp:
            p_type = sp["types"][0]["type"]["name"]
        else:
            p_type = "normal"
            
        moves = generate_player_moves(p_type)
        
        if move_index < 0 or move_index >= len(moves):
            return False, "Invalid move index."
            
        move = moves[move_index]
        cost = move["cost"]
        
        spendable = self.get_red_tokens()
        
        if spendable < cost:
            return False, f"Not enough tokens! You need {cost:,} but have {spendable:,}."
            
        # Deduct cost
        st["red_spent_tokens"] = st.get("red_spent_tokens", 0) + cost
        
        p_name = self.engine.api.get_species_name(p_id)
        r_mon = st["red_team"][r_idx]
        
        logs = []
        
        # Player Turn
        if move["name"] == "Recover":
            heal = int(st["player_max_hps"][p_idx] * 0.3)
            st["player_hps"][p_idx] = min(st["player_max_hps"][p_idx], st["player_hps"][p_idx] + heal)
            logs.append(f"{p_name} used Recover! Healed {heal} HP.")
        else:
            eff = get_effectiveness(move["type"], r_mon["type"])
            dmg = int(move["power"] * 1500 * eff)
            st["red_hps"][r_idx] = max(0, st["red_hps"][r_idx] - dmg)
            
            eff_str = " It's super effective!" if eff > 1.5 else (" It's not very effective..." if eff < 0.9 else "")
            logs.append(f"{p_name} used {move['name']}!{eff_str} (-{dmg} HP)")
            
        # Check Red faint
        if st["red_hps"][r_idx] <= 0:
            logs.append(f"Red's {r_mon['name']} fainted!")
            if r_idx + 1 < len(st["red_team"]):
                st["red_active_index"] += 1
                next_mon = st["red_team"][st["red_active_index"]]
                logs.append(f"Red sent out {next_mon['name']}!")
            else:
                red_team_ids = {25, 196, 143, 3, 6, 9}
                if set(st["player_team"]) == red_team_ids and not st.get("arceus_phase"):
                    logs.append("You defeated PKMN Trainer Red!")
                    logs.append("Suddenly, the sky darkens... ARCEUS is pleased by your competence!")
                    logs.append("ARCEUS challenges you to a battle!")
                    
                    st["arceus_phase"] = True
                    # Initialize Arceus as the enemy
                    arceus = {
                        "id": 493,
                        "name": "Arceus",
                        "hp": 5_000_000,
                        "max_hp": 5_000_000,
                        "type": "normal",
                        "moves": ["Judgment", "Hyper Beam", "Earthquake", "Recover"]
                    }
                    st["red_team"] = [arceus]
                    st["red_active_index"] = 0
                    st["red_hps"] = [5_000_000]
                    st["red_max_hps"] = [5_000_000]
                    st["player_hps"] = list(st["player_max_hps"])
                    logs.append("Arceus fully restored your team's health!")
                    
                    st["turn_log"] = logs[-5:]
                    self._save_state(st)
                    return True, "\n".join(logs)
                else:
                    if st.get("arceus_phase"):
                        logs.append("You defeated Arceus! You are a Pokémon God!")
                        # Grant Arceus
                        from poketokenbar.game.models import MonState
                        arceus_mon = MonState(
                            base_id=493,
                            current_id=493,
                            rarity="legendary",
                            path_ids=[493],
                            stage_index=0,
                            is_shiny=False,
                            nickname="Arceus",
                            generation=1
                        )
                        self.engine._register_to_dex(arceus_mon, status="graduated")
                        logs.append("Arceus has acknowledged your strength and joined your roster!")
                    else:
                        logs.append("You defeated PKMN Trainer Red! You are a Pokémon Master!")
                        self.engine.state["egg_tier"] = "mysterious fetal form"
                        self.engine.state["egg_usage"] = 0
                        logs.append("You found a Mysterious Fetal Form of Mew!")
                        
                    st["status"] = "win"
                    wins = self.engine.state.get("red_wins", 0) + 1
                    self.engine.state["red_wins"] = wins
                    hof = self.engine.state.get("red_hof", [])
                    hof.append(st["player_team"])
                    self.engine.state["red_hof"] = hof
                    
                    # Grant badges & massive reward
                    badges = self.engine.state.get("gym_badges", [])
                    if "👑 Master of Masters" not in badges:
                        badges.append("👑 Master of Masters")
                    self.engine.state["gym_badges"] = badges
                    self.engine.state["spent_tokens"] -= 500_000_000
                    self.engine.save()
                    
                    st["turn_log"] = logs[-5:]
                    self._save_state(st)
                    return True, "\n".join(logs)
        else:
            # Red Retaliates
            r_move = random.choice(r_mon["moves"])
            eff = get_effectiveness(r_mon["type"], p_type)
            # Red deals heavy damage
            dmg = int(30_000 * eff)
            st["player_hps"][p_idx] = max(0, st["player_hps"][p_idx] - dmg)
            
            enemy_prefix = "Red's" if not st.get("arceus_phase") else "Godly"
            eff_str = " It's super effective!" if eff > 1.5 else (" It's not very effective..." if eff < 0.9 else "")
            logs.append(f"{enemy_prefix} {r_mon['name']} used {r_move}!{eff_str} (-{dmg} HP)")
            
            if st["player_hps"][p_idx] <= 0:
                logs.append(f"{p_name} fainted!")
                # Check black out
                if all(hp <= 0 for hp in st["player_hps"]):
                    logs.append("You blacked out! Red's team has healed. Try again...")
                    st["status"] = "loss"
                    st["turn_log"] = logs[-5:]
                    self._save_state(st)
                    return True, "\n".join(logs)
                
        # Trim logs
        st["turn_log"] = logs[-5:]
        self._save_state(st)
        
        return True, "Turn executed."
