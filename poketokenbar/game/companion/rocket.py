import datetime
import random
from typing import Dict, List, Optional, Tuple, Any

from poketokenbar.game.models import CORPORATIONS, MonState, Rarity, SPECIAL_SPECIES
from poketokenbar.utils.formatting import format_tokens


ROCKET_OPERATION_DIALOGUES: Dict[str, Dict[str, Any]] = {
    "1": {
        "title": "Operation Genesis: Subterranean Pallet Wiretap",
        "location": "Route 1 Subterranean Relay // Pallet Outskirts",
        "speaker": "Commander Petrel",
        "dialogue": [
            "\"Welcome to the real fight, Operative. You're looking at Pallet Town—the peaceful, idyllic hometown of Pokémon researchers. That's the public facade.",
            "",
            "Buried eight meters beneath the Route 1 dirt track lies a high-speed fiber-optic data trunk. It connects Oak's laboratory directly to the Indigo League mainframe and clandestine bio-silos.",
            "",
            "Every time an innocent rookie trainer logs a wild encounter, Oak siphons that telemetry down this wire. Our field teams need you to tap into that trunk.",
            "",
            "Deploy expeditions to locate the surface junction boxes, and channel your coding power to decrypt his encrypted carrier wave. Once that line is open, our underground Black Market frequencies and syndicate transmissions go live. Move out!\""
        ],
        "tactical_orders": [
            "• Complete 2+ completed expeditions to scout the physical junction boxes.",
            "• Accumulate 5.0M coding tokens to decrypt the encrypted trunk carrier wave."
        ]
    },
    "2": {
        "title": "Operation Chimera: Celadon Reagent & Chrono Intercept",
        "location": "Celadon Transit Tunnels // West Kanto Corridor",
        "speaker": "Commander Petrel",
        "dialogue": [
            "\"Intercept confirmed, Operative. Oak's automated logistics convoy has just departed Celadon City under heavy armored escort.",
            "",
            "Our scouts report two critical cargo consignments: pressurized canisters of 'Morale Mist'—a chemical reagent Oak synthesized to induce artificial obedience—and Silph Co's experimental Chrono Accelerator prototypes, which compress developmental timelines.",
            "",
            "Oak is using these chronometers to accelerate his clone maturation cycles. If those prototypes reach Pallet Deep Lab, his bio-vats will double their production.",
            "",
            "Prove your combat supremacy by dominating the Trainer Battle arena, and intercept that convoy. Seize those canisters and chronometers for our Skunkworks Armory. Successful recovery will approve your promotion to Operative rank. Petrel out!\""
        ],
        "tactical_orders": [
            "• Win 2+ Trainer Battles in Tab [6] Arena to establish combat dominance.",
            "• Generate 10.0M coding tokens to breach the armored transport convoy."
        ]
    },
    "3": {
        "title": "[BOSS 1] Silph Sub-Vault: Prototype Chimera-001",
        "location": "Silph Co. Sub-Basement B4 // Saffron City Core",
        "speaker": "Commander Petrel",
        "dialogue": [
            "\"Red alert, Operative! When Team Rocket stormed Silph Co years ago, the media claimed we wanted Master Balls. A total fabrication. We were trying to breach Sub-Basement 4.",
            "",
            "Deep below the corporate executive suites lies Oak's first biological abomination: Prototype Chimera-001. Synthesized by fusing multi-elemental gene drives, it proved too volatile even for Oak, so he sealed it behind automated cryo-containment.",
            "",
            "With Red's defeat, the lockdown failsafes have deactivated. Chimera-001 is awake, drawing power from Silph's auxiliary reactors.",
            "",
            "Take your vanguard companion into the sub-vault. It's a bio-weapon with no empathy, no restraint. Unleash standard strikes or burn coding tokens for burst discharges. Terminate the prototype!\""
        ],
        "tactical_orders": [
            "• Infiltrate Sub-Basement B4 and engage Prototype Chimera-001.",
            "• Defeat Prototype Chimera-001 (150,000 HP) using 'attack' or 'burst'."
        ]
    },
    "4": {
        "title": "Operation Blackout: Cerulean Power Disruption",
        "location": "Cerulean Cape Sub-Aquatic Pipeline // North Kanto",
        "speaker": "Commander Petrel",
        "dialogue": [
            "\"Congratulations on crushing Chimera-001, Operative. But Oak's network is vast. Our telemetry has pinpointed the primary power source keeping his subterranean cloning vats alive.",
            "",
            "Massive liquid nitrogen conduits run sub-aquatically from Cerulean Cape, pumping heavy water directly into Pallet's bio-chambers. Oak conceals the staggering power draw under municipal grid allocations.",
            "",
            "To freeze those conduits, we need to deploy high-frequency Chrono disruptors. Those devices require immense financial backing—you must anchor capital in high-yield Bank term CDs (Tab [10]) to fund the temporal pulse emitter.",
            "",
            "Synchronize your coding output with the grid's resonance frequency. Cut Cerulean's flow, and Oak's incubators will stall. Execute!\""
        ],
        "tactical_orders": [
            "• Hold at least 1 active Bank Term CD deposit in Tab [10] to fund disruptors.",
            "• Accumulate 15.0M coding tokens to synchronize grid overload frequencies."
        ]
    },
    "5": {
        "title": "Operation Leviathan: Telemetry Cargo & Neural Tap",
        "location": "Vermilion Deep Anchorage // Bay Berth 09",
        "speaker": "Commander Petrel",
        "dialogue": [
            "\"Operative, look out across the harbor. The automated freight vessel S.S. Dreadnought has just docked at Vermilion Deep Anchorage under an encrypted League transponder.",
            "",
            "Its cargo hold isn't carrying consumer goods. It is laden with neural broadcast antennas and quantum telemetry splitters designed to siphon combat battle data from every trainer across Kanto.",
            "",
            "Oak is using this global tap to feed training XP directly into his slumbering battle-constructs. We are going to hijack that network.",
            "",
            "Deploy covert expeditions to infiltrate the docks, and make contact with our Black Market operatives in the shadows. We will reverse-engineer Oak's neural tap into our Corrupted EXP Splitter, allowing you to mirror XP across your entire roster. Pull this off, and you earn Special Agent clearance!\""
        ],
        "tactical_orders": [
            "• Deploy 2+ active expeditions simultaneously to flank the harbor docks.",
            "• Complete a transaction on the Black Market to secure covert extraction gear."
        ]
    },
    "6": {
        "title": "[BOSS 2] Power Plant: Cyber-Enforcer Core",
        "location": "Abandoned Power Plant Core // Route 10 Sub-Station",
        "speaker": "Commander Petrel",
        "dialogue": [
            "\"Special Agent, emergency transmission! The abandoned Power Plant on Route 10 just spiked off the charts.",
            "",
            "Oak's automated contingency enforcer has boots on the ground. It's a cybernetic titan—a mechanized skeletal construct grafted with regenerative cellular tissue, designed to defend the grid against resistance strikes.",
            "",
            "It has locked itself into the plant's main transformer core, feeding hundreds of thousands of volts into Oak's regional defense shield.",
            "",
            "If we don't sever its core, our comms and satellite links will be completely fried. Breach the facility, Agent. Strike with precision or burn token bursts. Shut down the Cyber-Enforcer!\""
        ],
        "tactical_orders": [
            "• Infiltrate high-voltage reactor chamber of Route 10 Power Plant.",
            "• Defeat Cyber-Zapdos Core (200,000 HP) using 'attack' or 'burst'."
        ]
    },
    "7": {
        "title": "Operation Squad Harmony: Lavender Crypt Decryption",
        "location": "Pokémon Tower Crypt Basement // Lavender Sub-Levels",
        "speaker": "Commander Petrel",
        "dialogue": [
            "\"You took down the Cyber-Enforcer, Agent. Now comes an operation that requires more than brute force.",
            "",
            "Beneath the somber tombstones of Lavender Tower lies an ancient crypt where Oak conducted his earliest neural frequency experiments. He was trying to decode how Pokémon spirits resonate with organic trainers.",
            "",
            "The cipher is locked behind a biocentric resonance lock. It will only open if approached by a trainer and Pokémon whose bond is unbroken—your companion must be at absolute peak morale (100% Happiness). Use the Syndicate Morale Mist we seized in Celadon if you need to synchronize cellular affinity instantly.",
            "",
            "Generate the required cryptographic tokens and attune your companion's frequency to the crypt. Recover the neural cipher—we need it to crack Oak's personal command codes!\""
        ],
        "tactical_orders": [
            "• Bring your active companion to 100% Happiness (via interaction or Morale Mist).",
            "• Accumulate 20.0M coding tokens to solve the biomorphic frequency cipher."
        ]
    },
    "8": {
        "title": "Operation Gene-Lock: Fuchsia Mutagen Vault Extraction",
        "location": "Safari Zone Subterranean Vault // Fuchsia Bio-Sanctuary",
        "speaker": "Commander Petrel",
        "dialogue": [
            "\"Agent, this is the turning point of our war. Before Giovanni walked away from Oak in 1982, Oak synthesized a terrifying compound: the Dark Gene Catalyst.",
            "",
            "It bypasses natural evolution completely, forcing instantaneous cellular metamorphosis. Giovanni locked the formula in a deep vault beneath Fuchsia's Safari Zone, refusing to corrupt organic biology.",
            "",
            "Oak's automated drones have begun drilling into the vault to reclaim it. We must strike first and extract the master drive.",
            "",
            "Deploying such mutagenic power requires proven command—you must demonstrate mastery by fielding at least 2 evolved Pokémon in your roster. Secure that formula, Agent. It will unlock Executive clearance and place instant cellular evolution in your hands!\""
        ],
        "tactical_orders": [
            "• Command 2+ evolved Pokémon in your roster (or hold 10+ VRDN shares).",
            "• Accumulate 25.0M coding tokens to breach the heavy vault locks."
        ]
    },
    "9": {
        "title": "[BOSS 3] Cinnabar Caldera: Apex Vanguard Mon-Omega",
        "location": "Volcanic Caldera Bio-Foundry // Deep Cinnabar Sub-Level 7",
        "speaker": "Commander Petrel",
        "dialogue": [
            "\"Executive, all satellite channels are clear. The path to Oak's inner sanctum is almost open—save for one final guardian.",
            "",
            "Deep within the volcanic caldera of Cinnabar Island, Oak's subterranean bio-foundry has awakened Mon-Omega. It is his apex bodyguard construct: a bio-synthetic apex combatant calibrated to withstand multi-elemental bombardment.",
            "",
            "Mon-Omega is fitted with a telepathic override matrix. It doesn't flinch, it doesn't tire, and it wields devastating psionic and physical destruction.",
            "",
            "This is the supreme test of your battle companion's resolve. Breach the caldera facility. Pour every ounce of tactical discipline and token energy into this assault. Break Mon-Omega, and the doors to Oak's Citadel will swing wide open!\""
        ],
        "tactical_orders": [
            "• Breach the volcanic sub-foundry on Cinnabar Island.",
            "• Defeat Apex Vanguard: Mon-Omega (300,000 HP) with 'attack' or 'burst'."
        ]
    },
    "10": {
        "title": "[FINAL BOSS] The Oak Citadel: Arch-Director Samuel Oak",
        "location": "Himalayan Mountain Citadel // Fortress Inner Sanctum",
        "speaker": "Commander Petrel",
        "dialogue": [
            "\"Executive... no, Comrade. This is it. The culmination of everything Giovanni started, everything we sacrificed for.",
            "",
            "Our full Rocket fleet has breached the Himalayan airspace. Ahead of us looms The Citadel—Oak's central command fortress, concealed above the snowline for thirty years.",
            "",
            "Inside, Arch-Director Samuel Oak awaits you. He has shed his grandfatherly persona. Flanking him is the Augmented Legion: Venusaur, Charizard, Blastoise, Tauros, Dragonite, Alakazam—all fitted with neural cybernetic collars and synthetic stimulants.",
            "",
            "He believes artificial subjugation is the only path to peace. Show him that the authentic bond between trainer and Pokémon is unbreakable. Conquer the Augmented Legion, shatter his throne, and take supreme Commander Authority over Team Rocket! For the truth!\""
        ],
        "tactical_orders": [
            "• Storm the inner sanctum of the Himalayan Citadel.",
            "• Defeat Arch-Director Samuel Oak & Master Core (350,000 HP)."
        ]
    }
}


class RocketMixin:
    """Provides Team Rocket syndicate storyline, operations, tactical boss battles, intel dossiers, and covert armory."""

    def check_rocket_story_unlock(self) -> Tuple[bool, Optional[str]]:
        """Checks if the player qualifies for the Team Rocket story unlock."""
        if self.state.get("rocket_story_unlocked", False):
            return False, None

        badges = self.state.get("gym_badges", [])
        if "👑 Master of Masters" not in badges:
            return False, None

        invs = self.state.get("investments", {})
        vrdn_shares = invs.get("viridian", 0)
        sm = self.get_or_init_stock_market()
        vrdn_price = sm.get("prices", {}).get("viridian", CORPORATIONS["viridian"].share_price)
        holding_value = vrdn_shares * vrdn_price

        if holding_value < 500_000_000:
            return False, None

        self.state["rocket_story_unlocked"] = True
        self.state["rocket_story_viewed"] = False

        alert_msg = "🚨 [ENCRYPTED TRANSMISSION] Frequency intercepted from Commander Petrel! Press '12' to view!"
        alerts = self.state.get("unread_alerts", [])
        if alert_msg not in alerts:
            alerts.append(alert_msg)
        self.state["unread_alerts"] = alerts
        self.save()
        return True, alert_msg

    def initialize_rocket_process(self) -> Tuple[bool, str]:
        """Initializes or resets the Team Rocket campaign, unlocking Tab 12 and resetting operations."""
        self.state["rocket_story_unlocked"] = True
        self.state["rocket_story_viewed"] = False
        self.state["rocket_alliance_accepted"] = False
        self.state["rocket_transmission_state"] = "intro"
        self.state["rocket_rank"] = "Informant"
        self.state["rocket_reputation"] = 0
        boss_hps = {3: 150_000, 6: 200_000, 9: 300_000, 10: 350_000}
        self.state["rocket_ops"] = {
            f"op_{i}": {
                "status": "available" if i == 1 else "locked",
                "progress": 0,
                "claimed": False,
                "objective_done": False,
                "boss_hp_remaining": boss_hps.get(i, 0),
                "briefing_viewed": False,
                "expeditions_done": 0,
                "battle_wins": 0,
                "black_market_trades": 0
            }
            for i in range(1, 11)
        }
        self.state["rocket_intel_unlocked"] = ["intel_001"]
        # Auto-grant Informant rank permanent clearance perk (Syndicate Black Pass)
        self.state["permanent_black_market"] = True
        self.state["has_exp_splitter"] = self.state.get("has_exp_splitter", False)
        self.state["last_authority_date"] = None
        self.state["pending_authority_delivery"] = None
        self.state["rocket_battle_state"] = {}
        self.state["daily_grunt_bribe"] = 2_000_000

        alert_msg = "🚨 [ENCRYPTED TRANSMISSION] Team Rocket frequency initialized! Press '12' to connect with Commander Petrel."
        alerts = self.state.get("unread_alerts", [])
        if alert_msg not in alerts:
            alerts.append(alert_msg)
        self.state["unread_alerts"] = alerts
        self.save()
        return True, "Team Rocket process initialized! Tab [12] unlocked with fresh Operation #1."

    def _update_rocket_operations(self, delta_tokens: int, events: List[str]):
        """Accumulates progress toward the active or available Rocket Operation."""
        self._update_armory_charges(delta_tokens, events)
        ops_state = self.state.setdefault("rocket_ops", {})
        for op_id, op_info in ops_state.items():
            if op_info.get("status") in ["active", "available"] and not op_info.get("claimed", False):
                # Auto-activate if currently available
                if op_info.get("status") == "available":
                    op_info["status"] = "active"
                    for op_def in self.get_rocket_operations():
                        if op_def["id"] == op_id and op_def["is_boss"]:
                            b_st = self.state.get("rocket_battle_state", {})
                            has_won = (b_st.get("status") == "win" and str(b_st.get("op_code")) == str(op_def["code"]))
                            if not has_won:
                                op_info["objective_done"] = False
                                if op_info.get("boss_hp_remaining", 0) <= 0:
                                    op_info["boss_hp_remaining"] = op_def["boss_hp"]

                for op_def in self.get_rocket_operations():
                    if op_def["id"] == op_id and op_def["target"] > 0:
                        old_prog = op_info.get("progress", 0)
                        new_prog = old_prog + delta_tokens
                        op_info["progress"] = new_prog
                        if old_prog < op_def["target"] <= new_prog:
                            events.append(f"🚀 Rocket Operation Ready! Coding target reached for {op_id.upper()}. Type '12' to inspect!")
                break

    def get_rocket_operations(self) -> List[Dict[str, Any]]:
        """Returns the list of 10 Rocket operations with current state."""
        ops_state = self.state.setdefault("rocket_ops", {})
        
        op_defs = [
            {
                "id": "op_1",
                "code": "1",
                "name": "Operation Genesis: Subterranean Pallet Wiretap",
                "briefing": "Oak's high-speed fiber relay runs secretly under Route 1. Decrypt his data line to access syndicate transmissions & Black Market networks.",
                "target": 5_000_000,
                "target_desc": "5.0M coding tokens & 2+ completed expeditions",
                "reward_tokens": 15_000_000,
                "reward_rank": "Informant",
                "intel_id": "intel_001",
                "is_boss": False,
                "boss_name": None,
                "boss_hp": 0
            },
            {
                "id": "op_2",
                "code": "2",
                "name": "Operation Chimera: Celadon Reagent & Chrono Intercept",
                "briefing": "Hijack Oak's automated convoy smuggling Morale Mist chemical canisters and Silph Chrono Accelerator prototypes through Celadon.",
                "target": 10_000_000,
                "target_desc": "10.0M coding tokens & 2+ Trainer Battle arena wins",
                "reward_tokens": 25_000_000,
                "reward_rank": "Operative",
                "intel_id": "intel_002",
                "is_boss": False,
                "boss_name": None,
                "boss_hp": 0
            },
            {
                "id": "op_3",
                "code": "3",
                "name": "[BOSS 1] Silph Sub-Vault: Prototype Chimera-001",
                "briefing": "Infiltrate Silph Co's sealed sub-basement and neutralize Oak's early bio-weapon prototype.",
                "target": 0,
                "target_desc": "Neutralize Sub-Vault bio-aberrations in tactical combat ('fight')",
                "reward_tokens": 40_000_000,
                "reward_rank": "Operative",
                "intel_id": "intel_003",
                "is_boss": True,
                "boss_name": "Prototype Chimera-001",
                "boss_hp": 150_000
            },
            {
                "id": "op_4",
                "code": "4",
                "name": "Operation Blackout: Cerulean Power Disruption",
                "briefing": "Disrupt the cooling conduits supplying Oak's subterranean bio-vats. Bank CD reserves required to power high-frequency Chrono disruptors.",
                "target": 15_000_000,
                "target_desc": "15.0M coding tokens & hold at least 1 Bank CD deposit",
                "reward_tokens": 50_000_000,
                "reward_rank": "Operative",
                "intel_id": "intel_004",
                "is_boss": False,
                "boss_name": None,
                "boss_hp": 0
            },
            {
                "id": "op_5",
                "code": "5",
                "name": "Operation Leviathan: Telemetry Cargo & Neural Tap",
                "briefing": "Sabotage freighter S.S. Dreadnought in Vermilion to seize Oak's neural telemetry splitters and reverse-engineer the Corrupted EXP Splitter.",
                "target": 0,
                "target_desc": "Deploy 2+ simultaneous expeditions & trade on the Black Market",
                "reward_tokens": 65_000_000,
                "reward_rank": "Special Agent",
                "intel_id": "intel_005",
                "is_boss": False,
                "boss_name": None,
                "boss_hp": 0
            },
            {
                "id": "op_6",
                "code": "6",
                "name": "[BOSS 2] Power Plant: Cyber-Enforcer Core",
                "briefing": "Oak's automated enforcer construct has occupied the abandoned Power Plant to supercharge the grid.",
                "target": 0,
                "target_desc": "Neutralize Cyber-Enforcer Unit in tactical combat ('fight')",
                "reward_tokens": 80_000_000,
                "reward_rank": "Special Agent",
                "intel_id": "intel_006",
                "is_boss": True,
                "boss_name": "Cyber-Zapdos Core",
                "boss_hp": 200_000
            },
            {
                "id": "op_7",
                "code": "7",
                "name": "Operation Squad Harmony: Lavender Crypt Decryption",
                "briefing": "Attune to the biological frequency cipher in Lavender Crypt. Requires maximum squad morale (100% Happiness via Syndicate Morale Mist).",
                "target": 20_000_000,
                "target_desc": "20.0M coding tokens & companion at 100% Happiness",
                "reward_tokens": 100_000_000,
                "reward_rank": "Special Agent",
                "intel_id": "intel_007",
                "is_boss": False,
                "boss_name": None,
                "boss_hp": 0
            },
            {
                "id": "op_8",
                "code": "8",
                "name": "Operation Gene-Lock: Fuchsia Mutagen Vault Extraction",
                "briefing": "Infiltrate the deep genetics lab beneath Fuchsia to extract Oak's master formula for the Dark Gene Catalyst.",
                "target": 25_000_000,
                "target_desc": "25.0M coding tokens & command 2+ evolved Pokémon in Roster",
                "reward_tokens": 120_000_000,
                "reward_rank": "Executive",
                "intel_id": "intel_008",
                "is_boss": False,
                "boss_name": None,
                "boss_hp": 0
            },
            {
                "id": "op_9",
                "code": "9",
                "name": "[BOSS 3] Cinnabar Caldera: Apex Vanguard Mon-Omega",
                "briefing": "Storm the volcanic caldera facility where Oak's supreme tactical combat unit is being awakened.",
                "target": 0,
                "target_desc": "Neutralize Apex Vanguard: Mon-Omega in tactical combat ('fight')",
                "reward_tokens": 150_000_000,
                "reward_rank": "Executive",
                "intel_id": "intel_009",
                "is_boss": True,
                "boss_name": "Apex Vanguard Mon-Omega",
                "boss_hp": 300_000
            },
            {
                "id": "op_10",
                "code": "10",
                "name": "[FINAL BOSS] The Oak Citadel: Arch-Director Samuel Oak",
                "briefing": "Full assault on Oak's Himalayan Citadel. Neutralize Oak to claim supreme Commander Authority and global courier control!",
                "target": 0,
                "target_desc": "Conquer Arch-Director Oak & The Augmented Legion in final combat ('fight')",
                "reward_tokens": 200_000_000,
                "reward_rank": "Commander",
                "intel_id": "intel_010",
                "is_boss": True,
                "boss_name": "Arch-Director Samuel Oak & Master Core",
                "boss_hp": 350_000
            }
        ]

        result = []
        for d in op_defs:
            op_st = ops_state.get(d["id"], {"status": "locked", "progress": 0, "claimed": False, "objective_done": False, "boss_hp_remaining": d["boss_hp"] if d["is_boss"] else 0, "briefing_viewed": False})
            cur_prog = op_st.get("progress", 0)
            if d["target"] > 0:
                cur_prog = min(cur_prog, d["target"])
            result.append({
                **d,
                "status": op_st.get("status", "locked"),
                "progress": cur_prog,
                "claimed": op_st.get("claimed", False),
                "objective_done": op_st.get("objective_done", False),
                "boss_hp_remaining": op_st.get("boss_hp_remaining", d["boss_hp"]),
                "briefing_viewed": op_st.get("briefing_viewed", False)
            })
        return result

    def get_operation_dialogue(self, op_code: str) -> Optional[Dict[str, Any]]:
        """Returns the immersive story dialogue and tactical orders for an operation."""
        clean_code = str(op_code).replace("op_", "").strip()
        return ROCKET_OPERATION_DIALOGUES.get(clean_code)

    def get_operation_requirements(self, op_code: str) -> List[Dict[str, Any]]:
        """Returns a list of tracked requirements for an operation with live progress."""
        clean_code = str(op_code).replace("op_", "").strip()
        op_id = f"op_{clean_code}"
        ops_list = self.get_rocket_operations()
        op_def = next((op for op in ops_list if op["id"] == op_id), None)
        if not op_def:
            return []

        ops_state = self.state.setdefault("rocket_ops", {})
        st = ops_state.setdefault(op_id, {})
        obj_done = st.get("objective_done", False)

        reqs = []

        # 1. Coding Tokens Requirement (if target > 0)
        target = op_def.get("target", 0)
        if target > 0:
            prog = min(st.get("progress", 0), target)
            is_met = prog >= target
            pct = 100 if is_met else ((prog * 100) // target if target > 0 else 100)
            reqs.append({
                "name": "Coding Tokens",
                "current": prog,
                "target": target,
                "current_str": f"{format_tokens(prog)}/{format_tokens(target)}",
                "target_str": format_tokens(target),
                "pct": pct,
                "is_met": is_met
            })

        # 2. Objective Requirement
        if op_def.get("is_boss", False):
            max_hp = op_def.get("boss_hp", 1000)
            hp_rem = max(0, st.get("boss_hp_remaining", max_hp))
            dmg_dealt = max_hp - hp_rem
            is_met = (hp_rem <= 0 or obj_done)
            pct = 100 if is_met else ((dmg_dealt * 100) // max_hp if max_hp > 0 else 0)
            b_name = op_def.get("boss_name", "Boss")
            short_bname = "Defeat " + b_name.split(":")[0].replace("Arch-Director ", "").strip()
            if len(short_bname) > 19:
                short_bname = short_bname[:19]
            reqs.append({
                "name": short_bname,
                "current": dmg_dealt,
                "target": max_hp,
                "current_str": f"{hp_rem:,} HP" if not is_met else "Defeated",
                "target_str": f"{max_hp:,} HP",
                "pct": pct,
                "is_met": is_met
            })
        elif op_id == "op_1":
            cur_exp = min(st.get("expeditions_done", 0), 2)
            is_met = (cur_exp >= 2) or st.get("objective_done", False) or st.get("claimed", False)
            pct = 100 if is_met else (cur_exp * 100) // 2
            reqs.append({
                "name": "Scout Expeditions",
                "current": cur_exp,
                "target": 2,
                "current_str": f"{cur_exp}/2",
                "target_str": "2",
                "pct": pct,
                "is_met": is_met
            })
        elif op_id == "op_2":
            cur_wins = min(st.get("battle_wins", 0), 2)
            is_met = (cur_wins >= 2) or st.get("claimed", False)
            if is_met:
                cur_wins = 2
            pct = 100 if is_met else (cur_wins * 100) // 2
            reqs.append({
                "name": "Battle Arena Wins",
                "current": cur_wins,
                "target": 2,
                "current_str": f"{cur_wins}/2",
                "target_str": "2",
                "pct": pct,
                "is_met": is_met
            })
        elif op_id == "op_4":
            cds = len(self.state.get("term_deposits", []))
            is_met = (cds >= 1) or st.get("claimed", False)
            cur_cds = 1 if is_met else min(cds, 1)
            pct = 100 if is_met else 0
            reqs.append({
                "name": "Active Bank CD",
                "current": cur_cds,
                "target": 1,
                "current_str": f"{cur_cds}/1 CD",
                "target_str": "1 CD",
                "pct": pct,
                "is_met": is_met
            })
        elif op_id == "op_5":
            exp_active = len(self.state.get("expeditions", []))
            cur_trade = min(st.get("black_market_trades", 0), 1)
            is_met_exp = (exp_active >= 2) or st.get("claimed", False)
            is_met_trade = (cur_trade >= 1) or st.get("claimed", False)
            cur_exp = 2 if is_met_exp else min(exp_active, 2)
            reqs.append({
                "name": "Active Expeditions",
                "current": cur_exp,
                "target": 2,
                "current_str": f"{cur_exp}/2",
                "target_str": "2",
                "pct": 100 if is_met_exp else (cur_exp * 100) // 2,
                "is_met": is_met_exp
            })
            reqs.append({
                "name": "Black Market Trade",
                "current": cur_trade,
                "target": 1,
                "current_str": f"{cur_trade}/1",
                "target_str": "1",
                "pct": 100 if is_met_trade else 0,
                "is_met": is_met_trade
            })
        elif op_id == "op_7":
            hap = self.active_mon.happiness if self.active_mon else self.state.get("happiness", 0)
            is_met = (hap >= 100) or st.get("claimed", False)
            cur_hap = 100 if is_met else min(hap, 100)
            pct = 100 if is_met else cur_hap
            reqs.append({
                "name": "Companion Happiness",
                "current": cur_hap,
                "target": 100,
                "current_str": f"{cur_hap}%/100%",
                "target_str": "100%",
                "pct": pct,
                "is_met": is_met
            })
        elif op_id == "op_8":
            dex = self.state.get("dex", [])
            roster = [d for d in dex if d.get("status") != "evolved"]
            evolved_count = 0
            if self.active_mon and getattr(self.active_mon, "stage_index", 0) > 0:
                evolved_count += 1
            for d in roster:
                if d.get("status") == "active":
                    continue
                stage = d.get("stage_index") or d.get("mon_state", {}).get("stage_index", 0)
                if stage > 0:
                    evolved_count += 1
            shares = self.state.get("investments", {}).get("viridian", 0)
            is_met = (evolved_count >= 2 or shares >= 10) or st.get("claimed", False)
            cur_ev = 2 if is_met else min(evolved_count, 2)
            pct = 100 if is_met else (cur_ev * 100) // 2
            reqs.append({
                "name": "Evolved Pokémon",
                "current": cur_ev,
                "target": 2,
                "current_str": f"{cur_ev}/2",
                "target_str": "2",
                "pct": pct,
                "is_met": is_met
            })

        return reqs

    def check_operation_objective(self, op_id: str) -> Tuple[bool, str]:
        """Checks whether active objective for an operation is met."""
        ops_state = self.state.setdefault("rocket_ops", {})
        st = ops_state.setdefault(op_id, {})
        if st.get("claimed", False):
            return True, "Objective verified!"

        old_done = st.get("objective_done", False)
        ok = False
        msg = ""

        if op_id == "op_1":
            cur_exp = st.get("expeditions_done", 0)
            if cur_exp >= 2 or st.get("objective_done", False):
                ok = True
                msg = "Completed 2+ scout expeditions!"
            else:
                ok = False
                msg = f"Need 2 scout expeditions (Completed: {cur_exp}/2)."

        elif op_id == "op_2":
            cur_wins = st.get("battle_wins", 0)
            if cur_wins >= 2:
                ok = True
                msg = "Won 2+ Trainer Battles!"
            else:
                ok = False
                msg = f"Need 2 Trainer Battle wins in Tab [6] (Current: {cur_wins}/2)."

        elif op_id == "op_3":
            hp_rem = st.get("boss_hp_remaining", 150_000)
            b_st = self.state.get("rocket_battle_state", {})
            has_won = (b_st.get("status") == "win" and str(b_st.get("op_code")) == "3")
            if hp_rem <= 0 and has_won:
                ok = True
                msg = "Prototype Chimera-001 neutralized!"
            else:
                ok = False
                if not has_won and hp_rem <= 0:
                    hp_rem = 150_000
                    st["boss_hp_remaining"] = hp_rem
                msg = f"Boss remaining HP: {hp_rem:,}. Type 'fight'!"

        elif op_id == "op_4":
            cds = len(self.state.get("term_deposits", []))
            if cds >= 1:
                ok = True
                msg = "Active Bank CD verified!"
            else:
                ok = False
                msg = "Requires at least 1 active Bank CD in Tab [10]."

        elif op_id == "op_5":
            exp_active = len(self.state.get("expeditions", []))
            trades = st.get("black_market_trades", 0)
            if exp_active >= 2 and trades >= 1:
                ok = True
                msg = "2 expeditions deployed & Black Market transaction verified!"
            else:
                ok = False
                msg = f"Requires 2 active expeditions ({exp_active}/2) and trading on Black Market ({trades}/1)."

        elif op_id == "op_6":
            hp_rem = st.get("boss_hp_remaining", 200_000)
            b_st = self.state.get("rocket_battle_state", {})
            has_won = (b_st.get("status") == "win" and str(b_st.get("op_code")) == "6")
            if hp_rem <= 0 and has_won:
                ok = True
                msg = "Cyber-Zapdos Core neutralized!"
            else:
                ok = False
                if not has_won and hp_rem <= 0:
                    hp_rem = 200_000
                    st["boss_hp_remaining"] = hp_rem
                msg = f"Boss remaining HP: {hp_rem:,}. Type 'fight'!"

        elif op_id == "op_7":
            hap = self.active_mon.happiness if self.active_mon else self.state.get("happiness", 0)
            if hap >= 100:
                ok = True
                msg = "Companion at 100% Happiness!"
            else:
                ok = False
                msg = f"Companion Happiness must be 100% (Current: {hap}%)."

        elif op_id == "op_8":
            dex = self.state.get("dex", [])
            roster = [d for d in dex if d.get("status") != "evolved"]
            evolved_count = 0
            if self.active_mon and getattr(self.active_mon, "stage_index", 0) > 0:
                evolved_count += 1
            for d in roster:
                if d.get("status") == "active":
                    continue
                stage = d.get("stage_index") or d.get("mon_state", {}).get("stage_index", 0)
                if stage > 0:
                    evolved_count += 1
            shares = self.state.get("investments", {}).get("viridian", 0)
            if evolved_count >= 2 or shares >= 10:
                ok = True
                msg = "Evolved Pokémon command clearance verified!"
            else:
                ok = False
                msg = f"Requires 2+ evolved Pokémon in roster (Current: {evolved_count}/2) or 10 VRDN shares."

        elif op_id == "op_9":
            hp_rem = st.get("boss_hp_remaining", 300_000)
            b_st = self.state.get("rocket_battle_state", {})
            has_won = (b_st.get("status") == "win" and str(b_st.get("op_code")) == "9")
            if hp_rem <= 0 and has_won:
                ok = True
                msg = "Apex Vanguard Mon-Omega neutralized!"
            else:
                ok = False
                if not has_won and hp_rem <= 0:
                    hp_rem = 300_000
                    st["boss_hp_remaining"] = hp_rem
                msg = f"Boss remaining HP: {hp_rem:,}. Type 'fight'!"

        elif op_id == "op_10":
            hp_rem = st.get("boss_hp_remaining", 350_000)
            b_st = self.state.get("rocket_battle_state", {})
            has_won = (b_st.get("status") == "win" and str(b_st.get("op_code")) == "10")
            if hp_rem <= 0 and has_won:
                ok = True
                msg = "Arch-Director Samuel Oak & The Augmented Legion conquered!"
            else:
                ok = False
                if not has_won and hp_rem <= 0:
                    hp_rem = 350_000
                    st["boss_hp_remaining"] = hp_rem
                msg = f"Boss remaining HP: {hp_rem:,}. Type 'fight'!"

        else:
            ok = True
            msg = "Objective verified!"

        st["objective_done"] = ok
        if ok != old_done:
            self.save()
        return ok, msg

    def start_rocket_operation(self, op_code: str) -> Tuple[bool, str]:
        """Activates a specific Rocket operation."""
        if op_code == "operation":
            ops_list = self.get_rocket_operations()
            selected = next((op for op in ops_list if op["status"] == "available" and not op["claimed"]), None)
            if not selected:
                return False, "No available operation to start."
            op_id = selected["id"]
        else:
            op_id = f"op_{op_code}" if not op_code.startswith("op_") else op_code
            ops_list = self.get_rocket_operations()
            selected = next((op for op in ops_list if op["id"] == op_id), None)

        if not selected:
            return False, f"Unknown operation '{op_code}'! Valid codes are 1 through 10."

        ops_state = self.state.setdefault("rocket_ops", {})
        st = ops_state.setdefault(op_id, {"status": "locked", "progress": 0, "claimed": False, "objective_done": False, "boss_hp_remaining": 0})

        if st.get("claimed", False):
            return False, f"Operation {op_code} is already completed and claimed!"
        if st.get("status") == "locked":
            return False, f"Operation {op_code} is locked! Complete preceding operations first."
        if st.get("status") == "active":
            return True, f"🚀 Operation {op_code} ({selected['name']}) is already active and underway!"

        for k, v in ops_state.items():
            if v.get("status") == "active" and not v.get("claimed", False):
                v["status"] = "available"

        st["status"] = "active"
        st.setdefault("expeditions_done", 0)
        st.setdefault("battle_wins", 0)
        st.setdefault("black_market_trades", 0)
        if selected["is_boss"]:
            b_st = self.state.get("rocket_battle_state", {})
            has_won = (b_st.get("status") == "win" and str(b_st.get("op_code")) == str(selected["code"]))
            if not has_won:
                st["objective_done"] = False
                if st.get("boss_hp_remaining", 0) <= 0:
                    st["boss_hp_remaining"] = selected["boss_hp"]

        self.save()
        msg = f"🚀 Operation {selected['code']} activated: {selected['name']}!"
        if selected["is_boss"]:
            msg += f" Target: {selected['boss_name']}. Type 'fight' to enter the Vault Arena!"
        return True, msg

    def attack_rocket_boss(self, burst: bool = False) -> Tuple[bool, str]:
        """Attacks the syndicate boss of the currently active Rocket operation."""
        ops_list = self.get_rocket_operations()
        active_op = next((op for op in ops_list if op["status"] == "active"), None)
        if not active_op or not active_op["is_boss"]:
            return False, "No active Syndicate Boss encounter! Select an active boss operation first (Op 3, 6, 9, 10)."

        from poketokenbar.game.rocket_battle import RocketBattleHandler
        handler = RocketBattleHandler(self)
        b_st = handler._get_state()
        if not b_st.get("player_team") or b_st.get("status") in ["win", "loss"] or b_st.get("op_code") != active_op["code"]:
            ok, msg = handler.start_boss_battle(active_op["code"])
            if not ok:
                return False, msg

        move_idx = 3 if burst else 0
        return handler.execute_turn(move_idx)

    def _recruit_rocket_companion(self, species_id: int):
        """Helper to recruit unique rocket rewards into dex roster."""
        spec_info = SPECIAL_SPECIES.get(species_id, {})
        rarity = spec_info.get("rarity", Rarity.RARE)
        mon = MonState(
            base_id=species_id,
            path_ids=[species_id],
            planned_path_ids=[species_id],
            stage_index=0,
            used_at_stage=0,
            rarity=rarity,
            total_forms=1,
            is_shiny=False,
            happiness=100
        )
        self._register_to_dex(mon, status="inactive")

    def claim_rocket_operation(self, op_code: str) -> Tuple[bool, str]:
        """Claims rewards for a completed operation, promoting rank and unlocking intel."""
        op_id = f"op_{op_code}" if not op_code.startswith("op_") else op_code
        ops_list = self.get_rocket_operations()
        selected = next((op for op in ops_list if op["id"] == op_id), None)

        if not selected:
            return False, f"Unknown operation '{op_code}'!"

        ops_state = self.state.setdefault("rocket_ops", {})
        st = ops_state.setdefault(op_id, {"status": "locked", "progress": 0, "claimed": False, "objective_done": False, "boss_hp_remaining": 0})

        if st.get("claimed", False):
            return False, f"Operation {op_code} reward has already been claimed!"

        if selected["target"] > 0 and st.get("progress", 0) < selected["target"]:
            rem = selected["target"] - st.get("progress", 0)
            return False, f"Operation {op_code} incomplete! Need {format_tokens(rem)} more coding tokens."

        ok_obj, msg_obj = self.check_operation_objective(op_id)
        if not ok_obj:
            return False, f"Operation {op_code} objective not fulfilled: {msg_obj}"

        st["claimed"] = True
        st["status"] = "completed"
        st["objective_done"] = True

        # Award tokens
        reward = selected["reward_tokens"]
        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - reward

        # Update Reputation & Rank
        old_rank = self.state.get("rocket_rank", "Informant")
        rep = sum(1 for v in ops_state.values() if v.get("claimed", False))
        self.state["rocket_reputation"] = rep
        if rep >= 10: new_rank = "Commander"
        elif rep >= 8: new_rank = "Executive"
        elif rep >= 5: new_rank = "Special Agent"
        elif rep >= 2: new_rank = "Operative"
        else: new_rank = "Informant"
        self.state["rocket_rank"] = new_rank

        # Auto-grant permanent clearance perks based on rank
        rank_order = {"Informant": 1, "Operative": 2, "Special Agent": 3, "Executive": 4, "Commander": 5}
        cur_lvl = rank_order.get(new_rank, 1)
        if cur_lvl >= 1 and self.state.get("rocket_alliance_accepted", False):
            self.state["permanent_black_market"] = True
        if cur_lvl >= 3:
            self.state["has_exp_splitter"] = True
        if cur_lvl >= 2:
            charges_st = self.state.setdefault("rocket_armory_charges", {})
            for tech in ["spray", "chrono"]:
                t_st = charges_st.setdefault(tech, {"charges": 0, "progress": 0, "target": 2_500_000})
                if t_st.get("charges", 0) == 0:
                    t_st["charges"] = 3
        if cur_lvl >= 4:
            charges_st = self.state.setdefault("rocket_armory_charges", {})
            t_st = charges_st.setdefault("catalyst", {"charges": 0, "progress": 0, "target": 2_500_000})
            if t_st.get("charges", 0) == 0:
                t_st["charges"] = 3

        perk_msg = ""
        if rank_order.get(new_rank, 1) > rank_order.get(old_rank, 1):
            if new_rank == "Operative":
                perk_msg = "\n  🎖️ PROMOTED TO OPERATIVE! Unlocked Syndicate Morale Mist & Chrono Accelerator in Covert Armory."
            elif new_rank == "Special Agent":
                perk_msg = "\n  🎖️ PROMOTED TO SPECIAL AGENT! Auto-activated Corrupted EXP Splitter (25% passive XP mirroring)!"
            elif new_rank == "Executive":
                perk_msg = "\n  🎖️ PROMOTED TO EXECUTIVE! Unlocked Dark Gene Catalyst in Covert Armory."
            elif new_rank == "Commander":
                perk_msg = "\n  👑 PROMOTED TO COMMANDER! Unlocked Team Rocket Authority daily requisition in Covert Armory."

        # Unlock dossier
        intel_id = selected["intel_id"]
        unlocked_intel = self.state.setdefault("rocket_intel_unlocked", [])
        if intel_id not in unlocked_intel:
            unlocked_intel.append(intel_id)

        # Unlock next op sequentially
        try:
            curr_num = int(selected["code"])
            if curr_num < 10:
                next_key = f"op_{curr_num + 1}"
                if next_key in ops_state and not ops_state[next_key].get("claimed", False):
                    ops_state[next_key]["status"] = "available"
                    ops_state[next_key]["briefing_viewed"] = False
                    next_num = curr_num + 1
                    boss_hps = {3: 150_000, 6: 200_000, 9: 300_000, 10: 350_000}
                    if next_num in boss_hps:
                        ops_state[next_key]["boss_hp_remaining"] = boss_hps[next_num]
                        ops_state[next_key]["objective_done"] = False
        except ValueError:
            pass

        climax_msg = ""
        # Final Operation 10 Climax Unlocks!
        if op_id == "op_10":
            badges = self.state.setdefault("gym_badges", [])
            truth_badge = "👑 Seeker of Truth"
            if truth_badge not in badges:
                badges.append(truth_badge)

            # Recruit Armored Mewtwo & Porygon-Zero
            self._recruit_rocket_companion(2001)  # Armored Mewtwo
            self._recruit_rocket_companion(2002)  # Porygon-Zero

            # Recruit Oak's Augmented Team
            for aug_id in [2003, 2004, 2005, 2006, 2007, 2008]:
                self._recruit_rocket_companion(aug_id)

            # Permanent Black Market access
            self.state["permanent_black_market"] = True
            climax_msg = "\n  👑 EARNED TITLE: 'Seeker of Truth'!\n  🎁 RECRUITED: Armored Mewtwo, Porygon-Zero, & Oak's Augmented Team into Roster!\n  🔓 UNLOCKED: Permanent 24/7 Black Market Access!"

        self.save()
        return True, f"🎉 Operation {selected['code']} Completed! Claimed {format_tokens(reward)} tokens! Rank: {new_rank} (Rep: {rep}/10)!{perk_msg}{climax_msg}"

    def get_rocket_dossier(self) -> List[Dict[str, Any]]:
        """Returns the 10 classified dossier entries."""
        unlocked_set = set(self.state.get("rocket_intel_unlocked", ["intel_001"]))
        return [
            {
                "id": 1,
                "key": "intel_001",
                "title": "Dossier #001: Red's Biological Blueprint",
                "date": "1996-02-27",
                "unlocked": "intel_001" in unlocked_set,
                "content": [
                    "LOG DATE: 1996-02-27 | FACILITY: Cinnabar Deep Lab Sub-Level 4",
                    "SUBJECT: Specimen-001 (Designation: RED)",
                    "",
                    "Neural pathways successfully synthesized using purified DNA strands.",
                    "Emotional response matrices eliminated to optimize pure battle instinct.",
                    "Growth acceleration reached physical maturity in 48 months.",
                    "Subject dispatched to Pallet Town for field trial under the guise",
                    "of an ordinary youth. Pokédex telemetry uplink confirmed active.",
                    "",
                    "Commander Petrel note: 'We found this blueprint buried in Oak's",
                    "private mainframe. Red wasn't an ordinary champion—he was engineered",
                    "to enforce total compliance across the Pokémon League.'"
                ]
            },
            {
                "id": 2,
                "key": "intel_002",
                "title": "Dossier #002: Celadon Convoy & Chrono R&D",
                "date": "1999-11-21",
                "unlocked": "intel_002" in unlocked_set,
                "content": [
                    "LOG DATE: 1999-11-21 | INTERCEPTED SUPPLY MANIFEST",
                    "ORIGIN: Celadon Dept. Synthesis Wing -> Pallet Deep Lab",
                    "",
                    "Convoy cargo seized: pressurized Morale Mist chemical canisters",
                    "and Silph Co quantum Chrono Accelerator prototypes. Oak utilized",
                    "these chronometers to compress developmental cycle times.",
                    "",
                    "Commander Petrel note: 'Our Skunkworks has reverse-engineered",
                    "both prototypes. Operatives may now requisition Morale Mist and",
                    "Chrono Accelerators directly from the Covert Armory.'"
                ]
            },
            {
                "id": 3,
                "key": "intel_003",
                "title": "Dossier #003: Project Chimera: The Silph Vault",
                "date": "2000-05-14",
                "unlocked": "intel_003" in unlocked_set,
                "content": [
                    "LOG DATE: 2000-05-14 | RECOVERED SILPH R&D LOGS",
                    "PROJECT: Chimera Synthesis",
                    "",
                    "Prototypes synthesized by combining multi-elemental gene drives.",
                    "Initial trials yielded extreme volatility. Specimen-001 was quarantined",
                    "in Silph sub-basement with automated containment shielding.",
                    "",
                    "Commander Petrel note: 'Oak used Silph Co to fund his monstrous tests.",
                    "When we raided Silph in Saffron, we were trying to seize this data.'"
                ]
            },
            {
                "id": 4,
                "key": "intel_004",
                "title": "Dossier #004: The Cerulean Cooling Conduit",
                "date": "2001-08-30",
                "unlocked": "intel_004" in unlocked_set,
                "content": [
                    "LOG DATE: 2001-08-30 | INFRASTRUCTURE TELEMETRY",
                    "TARGET: Subterranean Liquid Nitrogen Conduit",
                    "",
                    "Massive sub-aquatic conduits route chilled heavy water from Cerulean",
                    "Cape directly into the Pallet underground bio-vats. Power draw",
                    "disguised under municipal grid allocations.",
                    "",
                    "Commander Petrel note: 'Diverting Cerulean power destabilized Oak's",
                    "cloning vats, buying us crucial time to organize the counterstrike.'"
                ]
            },
            {
                "id": 5,
                "key": "intel_005",
                "title": "Dossier #005: S.S. Dreadnought Telemetry Manifest",
                "date": "2002-02-18",
                "unlocked": "intel_005" in unlocked_set,
                "content": [
                    "LOG DATE: 2002-02-18 | FREIGHT CARGO MANIFEST: S.S. DREADNOUGHT",
                    "SHIPPED TO: Vermilion Deep Anchorage // Oak Syndicate Logistics",
                    "",
                    "Consignment seized: Neural telemetry splitters and quantum broadcast",
                    "relays designed to siphon trainer battle experience across Kanto.",
                    "",
                    "Commander Petrel note: 'We reverse-engineered Oak's broadcast tap",
                    "into our Corrupted EXP Splitter. Special Agents can now mirror",
                    "combat data passively across reserve roster Pokémon.'"
                ]
            },
            {
                "id": 6,
                "key": "intel_006",
                "title": "Dossier #006: Cybernetic DNA Schematics",
                "date": "2002-11-15",
                "unlocked": "intel_006" in unlocked_set,
                "content": [
                    "LOG DATE: 2002-11-15 | RECOVERED SCHEMATICS: Power Plant Core",
                    "PROTOTYPE: Cyber-Enforcer Bio-Construct",
                    "",
                    "Mechanized skeletal frame grafted with regenerative cellular tissue.",
                    "Power cell powered by condensed token resonance. In the event of",
                    "Specimen-001 deactivation, automated defenses engage immediately.",
                    "",
                    "Commander Petrel note: 'Oak anticipated Red's defeat. He had automated",
                    "cyber-constructs sleeping in reinforced mountain silos.'"
                ]
            },
            {
                "id": 7,
                "key": "intel_007",
                "title": "Dossier #007: Celadon Institute (1975)",
                "date": "1975-06-12",
                "unlocked": "intel_007" in unlocked_set,
                "content": [
                    "LOG DATE: 1975-06-12 | ARCHIVE: Celadon Institute of Biology",
                    "FELLOW RESEARCHERS: Samuel Oak & Giovanni",
                    "",
                    "Before the badges, before the syndicate, Samuel Oak and Giovanni were",
                    "inseparable research partners. Together they mapped the first genetic",
                    "sequences of wild Pokémon in the Viridian basin.",
                    "",
                    "Commander Petrel note: 'They weren't always enemies. In fact, they were",
                    "best friends. But brilliance without restraint breeds monstrous ambition.'"
                ]
            },
            {
                "id": 8,
                "key": "intel_008",
                "title": "Dossier #008: Fuchsia Vault & Mutagen Protocol",
                "date": "1982-04-09",
                "unlocked": "intel_008" in unlocked_set,
                "content": [
                    "LOG DATE: 1982-04-09 | SAFARI ZONE DEEP ARCHIVE",
                    "RESEARCH PROJECT: Forced Cellular Metamorphosis",
                    "",
                    "Oak perfected a synthetic catalyst forcing instant cellular evolution.",
                    "Giovanni locked the formula away, refusing to corrupt organic biology.",
                    "Oak later buried the master drive inside the Fuchsia gene-vault.",
                    "",
                    "Commander Petrel note: 'With the formula secured, Executives are",
                    "cleared to deploy the Dark Gene Catalyst to instantly evolve team",
                    "members at will.'"
                ]
            },
            {
                "id": 9,
                "key": "intel_009",
                "title": "Dossier #009: Mon-Omega Vanguard Directive",
                "date": "2003-09-01",
                "unlocked": "intel_009" in unlocked_set,
                "content": [
                    "LOG DATE: 2003-09-01 | CINNABAR CALDERA VAULT REPORT",
                    "DESIGNATION: Mon-Omega (Syndicate Vanguard)",
                    "",
                    "Peak bio-synthetic apex combatant completed. Telepathic override",
                    "matrix active. Calibrated to withstand multi-elemental assaults.",
                    "",
                    "Commander Petrel note: 'Mon-Omega was Oak's supreme bodyguard.",
                    "With this construct broken, the path to the Citadel is wide open.'"
                ]
            },
            {
                "id": 10,
                "key": "intel_010",
                "title": "Dossier #010: Fall of Oak & Supreme Authority",
                "date": "CURRENT",
                "unlocked": "intel_010" in unlocked_set,
                "content": [
                    "LOG DATE: CURRENT | DECLASSIFIED AFTER ACTION REPORT",
                    "OPERATION FINALITY: CITADEL NEUTRALIZATION",
                    "",
                    "The Himalayan Citadel has fallen. Arch-Director Samuel Oak's secret",
                    "syndicate operations across Kanto and Johto are completely offline.",
                    "",
                    "Commander Petrel note: 'By unanimous decree of the Executive Council,",
                    "supreme command of Team Rocket is conferred upon you. Your Team Rocket",
                    "Authority grants daily courier requisitions across all regional outposts.'"
                ]
            }
        ]

    def get_armory_charge_info(self, tech_code: str) -> Dict[str, Any]:
        """Returns charging status and available uses (up to 3) for armory devices."""
        tech_code = tech_code.lower().strip()
        if tech_code in ["mist", "morale", "morale mist"]:
            tech_code = "spray"
        elif tech_code in ["accelerator", "chrono accelerator"]:
            tech_code = "chrono"
        elif tech_code in ["catalyst", "gene", "dark gene", "dark gene catalyst"]:
            tech_code = "catalyst"

        charges_st = self.state.setdefault("rocket_armory_charges", {})
        rank_order = {"Informant": 1, "Operative": 2, "Special Agent": 3, "Executive": 4, "Commander": 5}
        user_rank = self.state.get("rocket_rank", "Informant")
        user_lvl = rank_order.get(user_rank, 1)

        req_lvl = 4 if tech_code == "catalyst" else 2
        is_unlocked = user_lvl >= req_lvl
        default_c = 3 if is_unlocked else 0

        if tech_code not in charges_st or not isinstance(charges_st[tech_code], dict):
            charges_st[tech_code] = {
                "charges": default_c,
                "progress": 0,
                "target": 2_500_000
            }
        t_info = charges_st[tech_code]
        t_info.setdefault("charges", default_c)
        t_info.setdefault("progress", 0)
        t_info.setdefault("target", 2_500_000)

        c = min(3, max(0, t_info["charges"]))
        p = max(0, t_info["progress"])
        t = max(1, t_info["target"])
        pct = 100 if c >= 3 else min(99, int((p / t) * 100))
        return {
            "charges": c,
            "max_charges": 3,
            "progress": p,
            "target": t,
            "pct": pct
        }

    def _update_armory_charges(self, delta_tokens: int, events: List[str]):
        """Charges experimental Armory devices based on coding tokens used."""
        rank_order = {"Informant": 1, "Operative": 2, "Special Agent": 3, "Executive": 4, "Commander": 5}
        user_rank = self.state.get("rocket_rank", "Informant")
        user_lvl = rank_order.get(user_rank, 1)
        if user_lvl < 2:
            return

        charges_st = self.state.setdefault("rocket_armory_charges", {})
        tech_list = ["spray", "chrono"]
        if user_lvl >= 4:
            tech_list.append("catalyst")

        for tech in tech_list:
            info = self.get_armory_charge_info(tech)
            c = info["charges"]
            if c >= 3:
                charges_st[tech]["progress"] = 0
                continue

            target = info["target"]
            p = info["progress"] + delta_tokens
            recharged = 0
            while p >= target and c < 3:
                c += 1
                p -= target
                recharged += 1

            if c >= 3:
                p = 0

            charges_st[tech]["charges"] = c
            charges_st[tech]["progress"] = p

            if recharged > 0:
                if tech == "spray":
                    name, icon = "Syndicate Morale Mist", "💨"
                elif tech == "chrono":
                    name, icon = "Chrono Accelerator", "⌛"
                else:
                    name, icon = "Dark Gene Catalyst", "🧬"
                events.append(f"{icon} Covert Armory: {name} recharged! ({c}/3 charges)")

    def use_rocket_armory_item(self, tech_code: str) -> Tuple[bool, str]:
        """Consumes a stored charge (up to 3) to deploy Morale Mist or Chrono Accelerator."""
        tech_code = tech_code.lower().strip()
        if tech_code in ["mist", "spray", "morale", "morale mist"]:
            tech_code = "spray"
        elif tech_code in ["chrono", "accelerator", "chrono accelerator"]:
            tech_code = "chrono"
        elif tech_code in ["catalyst", "gene", "dark gene", "dark gene catalyst"]:
            tech_code = "catalyst"

        if tech_code not in ["spray", "chrono", "catalyst"]:
            return False, f"Unknown chargeable tech '{tech_code}'. Valid: 'use mist', 'use chrono', 'use catalyst'."

        rank_order = {"Informant": 1, "Operative": 2, "Special Agent": 3, "Executive": 4, "Commander": 5}
        user_rank = self.state.get("rocket_rank", "Informant")
        user_lvl = rank_order.get(user_rank, 1)

        req_lvl = 4 if tech_code == "catalyst" else 2
        req_rank = "Executive" if tech_code == "catalyst" else "Operative"
        if user_lvl < req_lvl:
            name = (
                "Dark Gene Catalyst" if tech_code == "catalyst"
                else ("Syndicate Morale Mist" if tech_code == "spray" else "Chrono Accelerator")
            )
            return False, f"Clearance Denied! {name} requires rank '{req_rank}' (Your Rank: {user_rank})."

        info = self.get_armory_charge_info(tech_code)
        if info["charges"] <= 0:
            if tech_code == "spray":
                name = "Syndicate Morale Mist"
            elif tech_code == "chrono":
                name = "Chrono Accelerator"
            else:
                name = "Dark Gene Catalyst"
            p_str = format_tokens(info["progress"])
            t_str = format_tokens(info["target"])
            return False, f"⚠️ {name} has 0/3 charges! Coding: {p_str}/{t_str} ({info['pct']}%)."

        if tech_code == "catalyst":
            ok, evo_msg = self.apply_dark_gene_catalyst()
            if not ok:
                return False, evo_msg

            charges_st = self.state.setdefault("rocket_armory_charges", {})
            charges_st["catalyst"]["charges"] = info["charges"] - 1
            rem = charges_st["catalyst"]["charges"]
            if "dark_gene_catalyst" in self.state.get("inventory", {}):
                self.state["inventory"].pop("dark_gene_catalyst", None)
            self.save()
            return True, f"🧬 Dark Gene Catalyst deployed! [Charges: {rem}/3]\n  {evo_msg}"

        # Consume 1 charge
        charges_st = self.state.setdefault("rocket_armory_charges", {})
        charges_st[tech_code]["charges"] = info["charges"] - 1
        rem = charges_st[tech_code]["charges"]

        if tech_code == "spray":
            if self.active_mon:
                m = self.active_mon
                m.happiness = 100
                self.set_active_mon(m)
            self.state["happiness"] = 100
            for d in self.state.get("dex", []):
                if d.get("status") != "evolved":
                    d["happiness"] = 100
                    m_st = d.get("mon_state")
                    if isinstance(m_st, dict):
                        m_st["happiness"] = 100
            self.save()
            return True, f"💨 Deployed Syndicate Morale Mist! Squad at 100%! [Charges: {rem}/3]"

        elif tech_code == "chrono":
            cds = self.state.get("term_deposits", [])
            active_cds = [c for c in cds if not c.get("matured")]
            matured_count = 0
            for cd in active_cds:
                rate = cd.get("daily_rate", 0.08)
                cd["current_value"] = int(cd["current_value"] * (1 + rate))
                cd["days_elapsed"] = cd.get("days_elapsed", 0) + 1
                if cd["days_elapsed"] >= cd["term_days"]:
                    cd["matured"] = True
                    matured_count += 1
            self.state["term_deposits"] = cds
            self.save()
            if active_cds:
                mat_str = f" ({matured_count} matured)" if matured_count > 0 else ""
                return True, f"⌛ Chrono Accelerator: Advanced {len(active_cds)} CD(s) +1d{mat_str}! [Charges: {rem}/3]"
            else:
                return True, f"⌛ Chrono Accelerator warped (+1 day). No active CDs! [Charges: {rem}/3]"

    def buy_rocket_armory_item(self, item_code: str) -> Tuple[bool, str]:
        """Requisitions covert tech from the Rocket Armory with rank clearance checks (Free of charge)."""
        item_code = item_code.lower().strip()
        if item_code in ["spray", "chrono", "mist", "accelerator"]:
            return self.use_rocket_armory_item(item_code)

        catalog = {
            "pass": ("Syndicate Black Pass", 0, "Informant"),
            "spray": ("Syndicate Morale Mist", 0, "Operative"),
            "chrono": ("Chrono Accelerator", 0, "Operative"),
            "splitter": ("Corrupted EXP Splitter", 0, "Special Agent"),
            "catalyst": ("Dark Gene Catalyst", 0, "Executive"),
            "authority": ("Team Rocket Authority", 0, "Commander"),
        }

        if item_code not in catalog:
            valid_codes = ", ".join(f"'{k}'" for k in catalog.keys())
            return False, f"Unknown tech code '{item_code}'! Valid codes: {valid_codes}."

        name, cost, min_rank = catalog[item_code]
        rank_order = {"Informant": 1, "Operative": 2, "Special Agent": 3, "Executive": 4, "Commander": 5}
        user_rank = self.state.get("rocket_rank", "Informant")
        if rank_order.get(user_rank, 1) < rank_order.get(min_rank, 1):
            return False, f"Clearance Denied! {name} requires rank '{min_rank}' (Your Rank: {user_rank})."

        # Clearance and prerequisite validations
        if item_code == "pass":
            if self.state.get("permanent_black_market", False):
                return False, "You already possess the Syndicate Black Pass!"
        elif item_code == "splitter":
            if self.state.get("has_exp_splitter", False):
                return False, "You already possess the Corrupted EXP Splitter!"
        elif item_code == "authority":
            if self.state.get("pending_authority_delivery"):
                return False, "A courier delivery is already waiting at HQ! Type 'keep' or 'dismiss' first."
            today_str = datetime.date.today().isoformat()
            if self.state.get("last_authority_date") == today_str:
                return False, "Authority requisition already dispatched today! Field logistics reset tomorrow."
            # Check available non-duplicate candidates
            roster_ids = set()
            if self.active_mon:
                roster_ids.add(self.active_mon.current_id)
                roster_ids.add(self.active_mon.base_id)
            for d in self.state.get("dex", []):
                if d.get("status") != "evolved":
                    sp_id = d.get("species_id", d.get("base_id"))
                    if sp_id:
                        roster_ids.add(int(sp_id))
                    base_id = d.get("base_id")
                    if base_id:
                        roster_ids.add(int(base_id))
                    m_st = d.get("mon_state")
                    if isinstance(m_st, dict):
                        if m_st.get("base_id"):
                            roster_ids.add(int(m_st["base_id"]))
                        if m_st.get("current_id"):
                            roster_ids.add(int(m_st["current_id"]))
            candidates = [i for i in range(1, 152) if i not in roster_ids]
            if not candidates:
                return False, "Your Roster already commands every Gen 1 Pokémon species in the region!"

        # Requisition granted for 0 tokens (free of charge)
        if item_code == "pass":
            self.state["permanent_black_market"] = True
            bm = self.get_or_init_black_market(force_open=True)
            bm["is_open"] = True
            bm["natural_open"] = True
            self.state["black_market"] = bm
            msg = "📯 Clearance Authorized: Syndicate Black Pass active! 24/7 Black Market unlocked & all Grunt tolls waived!"

        elif item_code == "splitter":
            self.state["has_exp_splitter"] = True
            msg = "⚡ Clearance Authorized: Corrupted EXP Splitter active! 25% of coding XP is now mirrored to all inactive roster Pokémon!"

        elif item_code == "catalyst":
            return self.use_rocket_armory_item("catalyst")

        elif item_code == "authority":
            chosen_id = random.choice(candidates)
            species_name = self.api.get_species_name(chosen_id)
            self.state["last_authority_date"] = datetime.date.today().isoformat()
            self.state["pending_authority_delivery"] = chosen_id
            msg = (
                f"👑 Clearance Authorized: Team Rocket Authority requisition dispatched! Field agents intercepted a wild {species_name} (#{chosen_id})!\n"
                f"  📦 Courier delivery pending at HQ. Type 'keep' to register into Roster, or 'dismiss' to release."
            )

        self.save()
        return True, msg

    def handle_authority_delivery(self, choice: str) -> Tuple[bool, str]:
        """Handles user choice ('keep' or 'dismiss') for pending Rocket Authority delivery."""
        pending = self.state.get("pending_authority_delivery")
        if not pending:
            return False, "No syndicate delivery pending at HQ."

        choice = choice.lower().strip()
        if choice not in ["keep", "dismiss"]:
            return False, "Invalid command. Type 'keep' to register into Roster, or 'dismiss' to release."

        sp_id = pending if isinstance(pending, int) else pending.get("species_id")
        sp_name = self.api.get_species_name(sp_id)
        self.state["pending_authority_delivery"] = None

        if choice == "dismiss":
            self.save()
            return True, f"📦 Requisitioned {sp_name} (#{sp_id}) was dismissed back into the wild."

        # choice == "keep"
        chain_ids = [sp_id]
        rarity = Rarity.RARE
        sp_data = self.api.get_pokemon_species(sp_id)
        if sp_data:
            cap_rate = sp_data.get("capture_rate", 255)
            is_leg = sp_data.get("is_legendary", False) or sp_data.get("is_mythical", False)
            rarity = Rarity.from_capture_rate(cap_rate, is_leg)
            if "evolution_chain" in sp_data:
                try:
                    chain_url = sp_data["evolution_chain"]["url"]
                    chain_id = int(chain_url.rstrip("/").split("/")[-1])
                    evo_data = self.api.get_evolution_chain(chain_id)
                    if evo_data:
                        chain_ids = self._parse_evo_tree(evo_data["chain"])
                except Exception:
                    pass

        if not chain_ids:
            chain_ids = [sp_id]

        if sp_id in chain_ids:
            stage_idx = chain_ids.index(sp_id)
            base_id = chain_ids[0]
        else:
            base_id = sp_id
            chain_ids = [sp_id]
            stage_idx = 0

        mon = MonState(
            base_id=base_id,
            path_ids=chain_ids,
            planned_path_ids=chain_ids,
            stage_index=stage_idx,
            used_at_stage=0,
            rarity=rarity,
            total_forms=len(chain_ids),
            is_shiny=False,
            happiness=100
        )
        self._register_to_dex(mon, status="inactive")
        self.save()
        return True, f"👑 Registered {sp_name} (#{sp_id}) into your Roster! Mon is rested at 100% Happiness."
