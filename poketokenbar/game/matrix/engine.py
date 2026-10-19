"""Engine logic for the Quantum Singularity Matrix (QSM) Hack-Simulator & Cyberdeck."""

import random
from typing import Dict, List, Tuple, Optional, Any

from poketokenbar.utils.formatting import format_tokens
from poketokenbar.game.matrix.models import (
    ROOT_TRANSCENDENCE_COST,
    EXPLOIT_TOOLS,
    DECK_SUBSYSTEMS,
    QRAM_BLOCKS,
    MEMORY_NODES,
    SUBSTRATE_ENTITIES,
    TUTORIAL_QUESTS,
    TUTORIAL_COMPLETION,
    VIVIENNE_POST_TUTORIAL_QUOTES,
)
from poketokenbar.game.matrix.pentest import MatrixPentestMixin
from poketokenbar.game.matrix.combat import MatrixCombatMixin
from poketokenbar.game.matrix.tweaks import MatrixTweaksMixin
from poketokenbar.game.matrix.overclock import MatrixOverclockMixin


class MatrixEngine(
    MatrixPentestMixin,
    MatrixCombatMixin,
    MatrixTweaksMixin,
    MatrixOverclockMixin,
):
    """Manages the Cyberdeck terminal, memory node breaches, reality tweaks, and substrate combat."""

    def __init__(self, companion_engine):
        self.companion = companion_engine

    @property
    def state(self) -> Dict[str, Any]:
        st = self.companion.state.setdefault("matrix", {})
        st.setdefault("unlocked", False)
        st.setdefault("story_viewed", False)
        st.setdefault("ram_blocks", [])
        st.setdefault("hacked_nodes", [])
        st.setdefault("active_tweaks", {})
        st.setdefault("trace_level", 0)
        st.setdefault("deck_hardware", {
            "integrity": 100,
            "firewall": 500,
            "max_firewall": 500,
            "threads": 1,
        })
        st.setdefault("tools", ["overflow"])
        st.setdefault("tool_upgrades", [])
        st.setdefault("deck_upgrades", {
            "shield": 0,
            "stealth": 0,
            "nanites": 0,
            "clock": 0,
        })
        st.setdefault("active_breach", None)
        st.setdefault("active_threat", None)
        st.setdefault("defeated_daemons", [])
        st.setdefault("root_transcended", False)
        st.setdefault("total_tokens_consumed", 0)
        st.setdefault("patches", [])
        st.setdefault("sectors", [])
        st.setdefault("quantum_flux", 0)
        st.setdefault("overclock_levels", {"ram": 0, "amp": 0})
        st.setdefault("daemon_raid_tier", 1)
        st.setdefault("collider_state", None)
        st.setdefault("combat_state", None)
        st.setdefault("tutorial_step", 1)
        st.setdefault("tutorial_completed", False)
        st.setdefault("tutorial_active", True)
        return st

    @property
    def is_unlocked(self) -> bool:
        return bool(self.state.get("unlocked", False))

    @property
    def ram_blocks(self) -> List[int]:
        return self.state.setdefault("ram_blocks", [])

    @property
    def hacked_nodes(self) -> List[str]:
        return self.state.setdefault("hacked_nodes", [])

    @property
    def active_tweaks(self) -> Dict[str, Dict[str, str]]:
        return self.state.setdefault("active_tweaks", {})

    @property
    def trace_level(self) -> int:
        return int(self.state.setdefault("trace_level", 0))

    @property
    def max_threads(self) -> int:
        """Determines maximum concurrent exploit execution threads based on Q-RAM blocks & Sectors."""
        base = 8 if 5 in self.ram_blocks else max(1, len(self.ram_blocks))
        return base + self.get_sector_threads_bonus()

    @property
    def deck_hardware(self) -> Dict[str, Any]:
        hw = self.state.setdefault("deck_hardware", {})
        hw.setdefault("integrity", 100)
        shield_lvl = self.get_subsystem_level("shield")
        shield_bonus = DECK_SUBSYSTEMS["shield"]["levels"][shield_lvl]["bonus"] if shield_lvl > 0 else 0
        sec_fw_bonus = self.get_sector_firewall_bonus()
        max_fw = 500 + shield_bonus + sec_fw_bonus
        hw["max_firewall"] = max_fw
        hw.setdefault("firewall", max_fw)
        hw.setdefault("threads", 1)
        if hw["threads"] < 1:
            hw["threads"] = 1
        return hw

    @property
    def owned_tools(self) -> List[str]:
        tools = self.state.setdefault("tools", ["overflow"])
        if "overflow" not in tools:
            tools.insert(0, "overflow")
        return tools

    @property
    def tool_upgrades(self) -> List[str]:
        return self.state.setdefault("tool_upgrades", [])

    @property
    def deck_upgrades(self) -> Dict[str, int]:
        upgrades = self.state.setdefault("deck_upgrades", {})
        upgrades.setdefault("shield", 0)
        upgrades.setdefault("stealth", 0)
        upgrades.setdefault("nanites", 0)
        upgrades.setdefault("clock", 0)
        return upgrades

    def get_subsystem_level(self, sub_id: str) -> int:
        return int(self.deck_upgrades.get(sub_id, 0))

    @property
    def active_breach(self) -> Optional[Dict[str, Any]]:
        return self.state.get("active_breach")

    @property
    def active_threat(self) -> Optional[Dict[str, Any]]:
        return self.state.get("active_threat")

    @property
    def defeated_daemons(self) -> List[str]:
        return self.state.setdefault("defeated_daemons", [])

    @property
    def is_root_transcended(self) -> bool:
        return bool(self.state.get("root_transcended", False))

    # -------------------------------------------------------------------------
    # Tutorial Quest Progression (Madame Vivienne)
    # -------------------------------------------------------------------------

    @property
    def tutorial_step(self) -> int:
        return int(self.state.setdefault("tutorial_step", 1))

    @tutorial_step.setter
    def tutorial_step(self, val: int) -> None:
        self.state["tutorial_step"] = int(val)

    @property
    def tutorial_completed(self) -> bool:
        return bool(self.state.setdefault("tutorial_completed", False))

    @tutorial_completed.setter
    def tutorial_completed(self, val: bool) -> None:
        self.state["tutorial_completed"] = bool(val)

    @property
    def tutorial_active(self) -> bool:
        return bool(self.state.setdefault("tutorial_active", True)) and not self.tutorial_completed

    def get_current_tutorial_quest(self) -> Dict[str, Any]:
        """Returns current tutorial quest data, or completion metadata with random Vivienne quote."""
        if self.tutorial_completed or self.tutorial_step > max(TUTORIAL_QUESTS.keys()):
            quote = random.choice(VIVIENNE_POST_TUTORIAL_QUOTES)
            return {
                "step": 8,
                "title": "Root Shell Master",
                "tag": "ONLINE",
                "speaker": "Madame Vivienne",
                "speaker_role": "Grand Concierge & Substrate Architect",
                "dialogue": [quote],
                "summary": quote,
                "objective": "Sub-Level 0 is yours. Explore nodes, optimize tweaks, and dominate the substrate.",
                "hint": "Commands: 'scan', 'hack <node>', 'tweaks', 'sectors', 'hardware', 'combat'",
            }
        return TUTORIAL_QUESTS.get(self.tutorial_step, TUTORIAL_COMPLETION)

    def advance_tutorial(self, action: str) -> Optional[str]:
        """Advances tutorial step if the executed action matches the current or upcoming objective."""
        if self.tutorial_completed:
            return None

        # Synchronize if player jumps ahead
        if action == "hack" and self.tutorial_step < 3:
            self.tutorial_step = 3
        elif action == "run_exploit" and self.tutorial_step < 4:
            self.tutorial_step = 4
        elif action == "step" and self.tutorial_step < 5:
            self.tutorial_step = 5
        elif action == "crack" and self.tutorial_step < 6:
            self.tutorial_step = 6
        elif action == "tweak" and self.tutorial_step < 7:
            self.tutorial_step = 7

        quest = self.get_current_tutorial_quest()
        if not quest or quest.get("expected_action") != action:
            return None

        next_step = self.tutorial_step + 1
        max_step = max(TUTORIAL_QUESTS.keys())
        if next_step > max_step:
            self.tutorial_completed = True
            self.tutorial_step = next_step
            self.companion.save()
            return "🎉 TUTORIAL COMPLETED! Madame Vivienne: 'Magnificent work, Trainer! The root shell is yours!'"
        else:
            self.tutorial_step = next_step
            self.companion.save()
            nxt = TUTORIAL_QUESTS[next_step]
            return f"📡 [COM-LINK // MADAME VIVIENNE] Step {self.tutorial_step}/{max_step}: {nxt['title']} — {nxt['objective']}"

    def skip_tutorial(self) -> Tuple[bool, str]:
        """Bypasses introductory tutorial questline."""
        self.tutorial_completed = True
        self.tutorial_step = max(TUTORIAL_QUESTS.keys()) + 1
        self.companion.save()
        return True, "Madame Vivienne: 'Understood, Trainer. Cyberdeck tutorial bypassed. Root terminal in full manual control.'"

    def reset_tutorial(self) -> Tuple[bool, str]:
        """Resets the tutorial questline back to Step 1."""
        self.tutorial_completed = False
        self.tutorial_step = 1
        self.companion.save()
        return True, "Madame Vivienne: 'COM-LINK re-synchronized. Restarting Sub-Level 0 orientation protocol.'"

    def reset_matrix_process(self) -> Tuple[bool, str]:
        """Resets the entire Sub-Level 0 Singularity Matrix progress."""
        return self.companion.reset_matrix_process()

    # -------------------------------------------------------------------------
    # Hardware & Compute Properties
    # -------------------------------------------------------------------------

    @property
    def max_exaflops(self) -> float:
        """Calculates total Cyberdeck Exaflops based on Q-RAM blocks, Sectors, and Overclocking."""
        count = len(self.ram_blocks)
        base_ef = 16.0 if count == 0 else 16.0 * (2.0 ** count)
        sec_ef = self.get_sector_base_exaflops_bonus()
        oc_ram_ef = self.get_overclock_level("ram") * 64.0
        return base_ef + sec_ef + oc_ram_ef

    @property
    def used_exaflops(self) -> float:
        """Calculates current Exaflops allocated to active tweaks and exploit threads."""
        total = 0.0
        for node_id, tweaks in self.active_tweaks.items():
            if node_id not in MEMORY_NODES:
                continue
            for tweak_id, opt_key in tweaks.items():
                total += self.get_tweak_exaflop_cost(node_id, tweak_id, opt_key)
        breach = self.active_breach
        if breach and "threads" in breach:
            for th in breach["threads"]:
                total += float(th.get("cost_exaflops", 0.0))
        return total

    @property
    def available_exaflops(self) -> float:
        return max(0.0, self.max_exaflops - self.used_exaflops)

    @property
    def max_tweak_slots(self) -> int:
        """Determines maximum concurrent active tweaks."""
        base_slots = 99 if 5 in self.ram_blocks else (1 + len(self.ram_blocks))
        root_bonus = 2 if self.is_root_transcendence_tweak_active() else 0
        oc_bonus = self.get_overclock_level("ram") // 2
        return base_slots + root_bonus + oc_bonus

    @property
    def used_tweak_slots(self) -> int:
        count = 0
        for tweaks in self.active_tweaks.values():
            count += len(tweaks)
        return count

    # -------------------------------------------------------------------------
    # Q-RAM Hardware Allocation (500Q - 10,000Q)
    # -------------------------------------------------------------------------

    def allocate_ram(self, block_idx: int) -> Tuple[bool, str]:
        """Allocates a Quantum Virtual Memory block (1-5)."""
        if not self.is_unlocked:
            return False, "Quantum Singularity Matrix is not initialized! Descend from Luxury Suite."

        if block_idx not in QRAM_BLOCKS:
            return False, f"Invalid Q-RAM block index #{block_idx}! (Valid: 1 to 5)"

        if block_idx in self.ram_blocks:
            return False, f"{QRAM_BLOCKS[block_idx]['name']} is already allocated and online!"

        # Sequential prerequisite
        if block_idx > 1 and (block_idx - 1) not in self.ram_blocks:
            prev_name = QRAM_BLOCKS[block_idx - 1]["name"]
            return False, f"Prerequisite missing! You must allocate {prev_name} first."

        info = QRAM_BLOCKS[block_idx]
        cost = info["cost"]
        avail = self.companion.available_tokens
        if avail < cost:
            return False, f"Not enough spendable tokens! Allocating {info['name']} requires {format_tokens(cost)} tokens."

        self.companion.state["spent_tokens"] = self.companion.state.get("spent_tokens", 0) + cost
        self.ram_blocks.append(block_idx)
        self.state["total_tokens_consumed"] = self.state.get("total_tokens_consumed", 0) + cost
        self.companion.save()
        return True, f"💾 DECK UPGRADED! {info['name']} online! {info['perk']} (-{format_tokens(cost)} tokens)"

    # -------------------------------------------------------------------------
    # Software Exploit Purchasing & Overclocking (Tool v2.0)
    # -------------------------------------------------------------------------

    def buy_tool(self, tool_id: str) -> Tuple[bool, str]:
        """Purchases and compiles an exploit software tool using spendable tokens."""
        if not self.is_unlocked:
            return False, "Quantum Singularity Matrix is not initialized! Descend from Luxury Suite."

        tool_id = str(tool_id).lower().strip()
        for tid, spec in EXPLOIT_TOOLS.items():
            if tool_id in [tid, spec["name"].lower(), spec["name"].lower().split(".")[0]]:
                tool_id = tid
                break

        if tool_id not in EXPLOIT_TOOLS:
            valid_tools = ", ".join(EXPLOIT_TOOLS.keys())
            return False, f"Unknown exploit software '{tool_id}'! Available: {valid_tools}"

        if tool_id in self.owned_tools:
            return False, f"Software '{EXPLOIT_TOOLS[tool_id]['name']}' is already compiled and available in your Cyberdeck!"

        spec = EXPLOIT_TOOLS[tool_id]
        cost = spec.get("cost", 0)
        avail = self.companion.available_tokens
        if avail < cost:
            return False, f"Not enough spendable tokens! Compiling '{spec['name']}' requires {format_tokens(cost)} tokens."

        self.companion.state["spent_tokens"] = self.companion.state.get("spent_tokens", 0) + cost
        self.owned_tools.append(tool_id)
        self.state["total_tokens_consumed"] = self.state.get("total_tokens_consumed", 0) + cost
        self.companion.save()
        return True, f"💾 SOFTWARE COMPILED! '{spec['name']}' [{spec['protocol']}] is now installed and ready! (-{format_tokens(cost)} tokens)"

    def upgrade_tool(self, tool_id: str) -> Tuple[bool, str]:
        """Upgrades a compiled exploit tool to v2.0 Overclocked (-1 turn, -25% Exaflop cost)."""
        if not self.is_unlocked:
            return False, "Quantum Singularity Matrix is not initialized! Descend from Luxury Suite."

        tool_id = str(tool_id).lower().strip()
        for tid, spec in EXPLOIT_TOOLS.items():
            if tool_id in [tid, spec["name"].lower(), spec["name"].lower().split(".")[0]]:
                tool_id = tid
                break

        if tool_id not in EXPLOIT_TOOLS:
            valid_tools = ", ".join(EXPLOIT_TOOLS.keys())
            return False, f"Unknown exploit software '{tool_id}'! Available: {valid_tools}"

        if tool_id not in self.owned_tools:
            return False, f"You must compile base '{EXPLOIT_TOOLS[tool_id]['name']}' first! Type 'buy tool {tool_id}'."

        if tool_id in self.tool_upgrades:
            return False, f"Software '{EXPLOIT_TOOLS[tool_id]['name']}' is already upgraded to v2.0 Overclocked!"

        spec = EXPLOIT_TOOLS[tool_id]
        cost = spec.get("upgrade_cost", 500_000_000_000_000_000)
        avail = self.companion.available_tokens
        if avail < cost:
            return False, f"Not enough spendable tokens! Upgrading '{spec['name']}' to v2.0 requires {format_tokens(cost)} tokens."

        self.companion.state["spent_tokens"] = self.companion.state.get("spent_tokens", 0) + cost
        self.tool_upgrades.append(tool_id)
        self.state["total_tokens_consumed"] = self.state.get("total_tokens_consumed", 0) + cost
        self.companion.save()
        return True, f"⚡ SOFTWARE OVERCLOCKED! '{spec['name']}' upgraded to v2.0! (-1 turn execution time, -25% Exaflop cost) (-{format_tokens(cost)} tokens)"

    # -------------------------------------------------------------------------
    # Upgradable Cyberdeck Subsystems (Shield, Stealth, Nanites, Clock)
    # -------------------------------------------------------------------------

    def upgrade_subsystem(self, sub_id: str) -> Tuple[bool, str]:
        """Upgrades a Cyberdeck subsystem (shield, stealth, nanites, clock) by one tier."""
        if not self.is_unlocked:
            return False, "Quantum Singularity Matrix is not initialized! Descend from Luxury Suite."

        sub_id = str(sub_id).lower().strip()
        if sub_id not in DECK_SUBSYSTEMS:
            valid = ", ".join(DECK_SUBSYSTEMS.keys())
            return False, f"Unknown subsystem '{sub_id}'! Available: {valid}"

        sub_spec = DECK_SUBSYSTEMS[sub_id]
        curr_lvl = self.get_subsystem_level(sub_id)
        max_lvl = sub_spec["max_level"]
        if curr_lvl >= max_lvl:
            return False, f"{sub_spec['name']} is already at Maximum Level (Lv {max_lvl})!"

        next_lvl = curr_lvl + 1
        lvl_info = sub_spec["levels"][next_lvl]
        cost = lvl_info["cost"]
        avail = self.companion.available_tokens
        if avail < cost:
            return False, f"Not enough spendable tokens! Upgrading {sub_spec['name']} to Lv {next_lvl} requires {format_tokens(cost)} tokens."

        self.companion.state["spent_tokens"] = self.companion.state.get("spent_tokens", 0) + cost
        self.deck_upgrades[sub_id] = next_lvl
        self.state["total_tokens_consumed"] = self.state.get("total_tokens_consumed", 0) + cost

        if sub_id == "shield":
            bonus = lvl_info["bonus"]
            prev_bonus = sub_spec["levels"][curr_lvl]["bonus"] if curr_lvl > 0 else 0
            delta = bonus - prev_bonus
            hw = self.deck_hardware
            hw["max_firewall"] = 500 + bonus + self.get_sector_firewall_bonus()
            hw["firewall"] += delta

        self.companion.save()
        return True, f"🛡️ SUBSYSTEM UPGRADED! {sub_spec['name']} advanced to Lv {next_lvl}/{max_lvl}! ({lvl_info['desc']}) (-{format_tokens(cost)} tokens)"

    # -------------------------------------------------------------------------
    # Root Transcendence (Ultimate Endgame Climax: 10,000Q)
    # -------------------------------------------------------------------------

    def execute_root_transcendence(self) -> Tuple[bool, str]:
        """Claims ultimate Ring-0 sovereignty over the simulation universe."""
        if not self.is_unlocked:
            return False, "Sub-Level 0 is not online."

        if self.is_root_transcended:
            return False, "👑 You have already attained Root Transcendence! You are the Root Architect."

        # Check Q-RAM Block 5
        if 5 not in self.ram_blocks:
            return False, "Prerequisite missing! You must allocate all 5 Q-RAM blocks (Block 0x05 online)."

        # Check all 5 core nodes hacked
        core_nodes = ["nursery", "expeditions", "bank", "roster", "combat"]
        unhacked = [nid for nid in core_nodes if nid not in self.hacked_nodes]
        if unhacked:
            return False, f"Prerequisite missing! All 5 core memory nodes must be breached. Missing: {', '.join(unhacked)}"

        # Check all 3 Daemons neutralized
        undefeated = [
            d for d in SUBSTRATE_ENTITIES.values()
            if d["type"] == "daemon" and d["id"] not in self.defeated_daemons
        ]
        if undefeated:
            names = [d["name"] for d in undefeated]
            return False, f"Security threats remain! Must neutralize all Master Daemons: {', '.join(names)}"

        cost = ROOT_TRANSCENDENCE_COST
        if self.companion.available_tokens < cost:
            return False, f"Root Transcendence requires {format_tokens(cost)} spendable tokens!"

        self.companion.state["spent_tokens"] = self.companion.state.get("spent_tokens", 0) + cost
        self.state["root_transcended"] = True
        self.state["total_tokens_consumed"] = self.state.get("total_tokens_consumed", 0) + cost
        # Enable root transcendence tweak
        self.active_tweaks.setdefault("root", {})["transcendence"] = "active"
        self.companion.save()

        return True, (
            "👑 ROOT TRANSCENDENCE ATTAINED!\n"
            "Ring-0 execution sovereignty claimed. The barrier between coder and simulation is dissolved.\n"
            "You are the Sovereign Root Architect of the Matrix!"
        )

    # -------------------------------------------------------------------------
    # Legacy Support Methods (For Backward Compatibility & Unit Tests)
    # -------------------------------------------------------------------------

    def start_collider(self, patch_key: str) -> Tuple[bool, str]:
        """Legacy collider starter."""
        return True, "Collider chamber bypassed: Tweaks are now managed directly via Cyberdeck."

    def collider_pulse(self, freq: str = "alpha") -> Tuple[bool, str]:
        return True, "Pulse bypassed."

    def collider_contain(self) -> Tuple[bool, str]:
        return True, "Contain bypassed."

    def collider_vent(self) -> Tuple[bool, str]:
        return True, "Vent bypassed."
