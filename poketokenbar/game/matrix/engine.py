"""Engine logic for the Quantum Singularity Matrix (QSM) Hack-Simulator & Cyberdeck."""

import random
from typing import Dict, List, Tuple, Optional, Any

from poketokenbar.utils.formatting import format_tokens
from poketokenbar.game.matrix.models import (
    MATRIX_ENTRY_COST,
    ROOT_TRANSCENDENCE_COST,
    HEX_BREACH_TOKENS,
    EXPLOIT_TOOLS,
    DECK_SUBSYSTEMS,
    QRAM_BLOCKS,
    MEMORY_NODES,
    SUBSTRATE_ENTITIES,
    REALITY_PATCHES,
    MEMORY_SECTORS,
    KERNEL_DAEMONS,
    TUTORIAL_QUESTS,
    TUTORIAL_COMPLETION,
    VIVIENNE_POST_TUTORIAL_QUOTES,
)


class MatrixEngine:
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
        """Determines maximum concurrent exploit execution threads based on Q-RAM blocks."""
        if 5 in self.ram_blocks:
            return 8
        count = len(self.ram_blocks)
        return max(1, count)

    @property
    def deck_hardware(self) -> Dict[str, Any]:
        hw = self.state.setdefault("deck_hardware", {})
        hw.setdefault("integrity", 100)
        shield_lvl = self.get_subsystem_level("shield")
        shield_bonus = DECK_SUBSYSTEMS["shield"]["levels"][shield_lvl]["bonus"] if shield_lvl > 0 else 0
        max_fw = 500 + shield_bonus
        hw["max_firewall"] = max_fw
        hw.setdefault("firewall", max_fw)
        base_threads = self.max_threads
        hw.setdefault("threads", base_threads)
        if hw["threads"] < base_threads:
            hw["threads"] = base_threads
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
                "hint": "Commands: 'scan', 'hack <node>', 'tweaks', 'software', 'hardware', 'combat'",
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
    # Hardware & Compute Compute Properties
    # -------------------------------------------------------------------------

    @property
    def max_exaflops(self) -> float:
        """Calculates total Cyberdeck Exaflops based on allocated Q-RAM blocks."""
        count = len(self.ram_blocks)
        if count == 0:
            return 16.0
        return 16.0 * (2.0 ** count)

    @property
    def used_exaflops(self) -> float:
        """Calculates current Exaflops allocated to active tweaks and exploit threads."""
        total = 0.0
        for node_id, tweaks in self.active_tweaks.items():
            if node_id not in MEMORY_NODES:
                continue
            for tweak_id, opt_key in tweaks.items():
                node_spec = MEMORY_NODES[node_id]["tweaks"].get(tweak_id)
                if node_spec and opt_key in node_spec["options"]:
                    total += float(node_spec["options"][opt_key]["cost_exaflops"])
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
        if 5 in self.ram_blocks:
            return 99
        return 1 + len(self.ram_blocks)

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
            hw["max_firewall"] = 500 + bonus
            hw["firewall"] += delta

        self.companion.save()
        return True, f"🛡️ SUBSYSTEM UPGRADED! {sub_spec['name']} advanced to Lv {next_lvl}/{max_lvl}! ({lvl_info['desc']}) (-{format_tokens(cost)} tokens)"

    # -------------------------------------------------------------------------
    # Memory Node Scanning & Hex Breach Minigame
    # -------------------------------------------------------------------------

    @staticmethod
    def resolve_node_id(node_str: str) -> Optional[str]:
        """Resolves a user-provided string or code to a canonical node ID."""
        clean = str(node_str).lower().strip()
        if clean in MEMORY_NODES:
            return clean
        for nid, node in MEMORY_NODES.items():
            code_lower = node["code"].lower()
            if clean in code_lower or clean == code_lower.split("_")[0]:
                return nid
            if clean == node["name"].lower():
                return nid
        return None

    def scan_network(self) -> Dict[str, Any]:
        """Returns network discovery state across all memory nodes."""
        self.advance_tutorial("scan")
        results = {}
        for nid, info in MEMORY_NODES.items():
            is_hacked = nid in self.hacked_nodes
            active = self.active_tweaks.get(nid, {})
            results[nid] = {
                "id": nid,
                "name": info["name"],
                "code": info["code"],
                "offset": info["offset"],
                "ice_level": info["ice_level"],
                "firewall": info.get("firewall", 500),
                "required_ports": info.get("required_ports", 2),
                "ports": info.get("ports", {}),
                "desc": info["desc"],
                "hacked": is_hacked,
                "active_tweaks": active,
                "tweaks_available": info["tweaks"],
            }
        return results

    def start_pentest(self, node_id: str) -> Tuple[bool, str]:
        """Initiates a multi-vector port reconnaissance and pen-testing session on a memory node."""
        if not self.is_unlocked:
            return False, "Quantum Cyberdeck is offline! Descend to Sub-Level 0."

        node_id = str(node_id).lower().strip()
        resolved = self.resolve_node_id(node_id)
        if not resolved:
            valid_nodes = ", ".join(MEMORY_NODES.keys())
            return False, f"Unknown memory node '{node_id}'! Available: {valid_nodes}"
        node_id = resolved

        if node_id in self.hacked_nodes:
            return False, f"Node '{MEMORY_NODES[node_id]['name']}' is already breached! Root access granted."

        node = MEMORY_NODES[node_id]
        if not node.get("ports"):
            if node_id == "root":
                return False, "Root Hypervisor Core cannot be pen-tested. Authorize root via 'ascend' / 'execute root'."
            return False, f"Node '{node['name']}' has no exposed network ports."

        # Initialize ports dict for the active session
        node_ports: Dict[str, Dict[str, Any]] = {}
        for p_num, p_info in node["ports"].items():
            node_ports[str(p_num)] = {
                "port": int(p_num),
                "service": p_info["service"],
                "vuln": p_info["vuln"],
                "tool": p_info["tool"],
                "cost_exaflops": float(p_info["cost_exaflops"]),
                "turns": int(p_info["turns"]),
                "status": "online",  # "online" | "cracking" | "compromised"
                "progress": 0,
                "max_progress": int(p_info["turns"]),
            }

        self.state["active_breach"] = {
            "node_id": node_id,
            "firewall": node.get("firewall", 500),
            "max_firewall": node.get("firewall", 500),
            "required_ports": node.get("required_ports", 2),
            "ports": node_ports,
            "threads": [],
            "ids_trace": 0,
            "logs": [f"Connection established to {node['code']}. Port scan complete."],
        }
        self.advance_tutorial("hack")
        self.companion.save()
        return True, f"🔓 PEN-TEST ACTIVE: Connected to {node['code']}. {len(node_ports)} listening ports detected."

    def start_breach(self, node_id: str) -> Tuple[bool, str]:
        """Backward-compatible alias for start_pentest."""
        return self.start_pentest(node_id)

    def run_exploit(self, port: int, tool: Optional[str] = None) -> Tuple[bool, str]:
        """Deploys an exploit payload to a listening port on the target node."""
        breach = self.active_breach
        if not breach:
            return False, "No active pen-testing session! Type 'hack <node>' to connect."

        p_key = str(port)
        if p_key not in breach.get("ports", {}):
            valid_ports = ", ".join(breach.get("ports", {}).keys())
            return False, f"Port {port} is not listening on this target node! (Available ports: {valid_ports})"

        port_data = breach["ports"][p_key]
        if port_data["status"] == "compromised":
            return False, f"Port {port} ({port_data['service']}) is already compromised!"

        if port_data["status"] == "cracking":
            return False, f"Port {port} already has an active exploit thread running!"

        active_threads = breach.setdefault("threads", [])
        max_th = self.max_threads
        if len(active_threads) >= max_th:
            return False, f"Cyberdeck execution threads saturated ({len(active_threads)}/{max_th} in use)! Wait for a thread to finish or upgrade Q-RAM."

        expected_tool = port_data["tool"]
        if tool is None or not str(tool).strip():
            tool = expected_tool
        else:
            tool = str(tool).lower().strip()
            if tool != expected_tool:
                exp_name = EXPLOIT_TOOLS.get(expected_tool, {}).get("name", expected_tool)
                return False, f"Incompatible exploit '{tool}'! Port {port} is vulnerable to '{expected_tool}' ({exp_name})."

        tool_spec = EXPLOIT_TOOLS.get(tool)
        if not tool_spec:
            return False, f"Unknown exploit tool '{tool}'!"

        if tool not in self.owned_tools:
            cost = tool_spec.get("cost", 0)
            return False, f"Software exploit '{tool}' ({tool_spec['name']}) is not compiled! Purchase with 'buy tool {tool}' ({format_tokens(cost)} tokens)."

        is_v2 = tool in self.tool_upgrades
        cost = float(port_data.get("cost_exaflops", tool_spec["cost_exaflops"]))
        turns = int(port_data["turns"])
        if is_v2:
            cost = max(1.0, cost * 0.75)
            turns = max(1, turns - 1)

        if self.available_exaflops < cost:
            return False, f"Insufficient Exaflops! '{tool_spec['name']}' requires {cost:.1f} EF ({self.available_exaflops:.1f} EF available)."

        # Determine next thread ID
        used_ids = {t["thread_id"] for t in active_threads}
        th_id = 1
        while th_id in used_ids:
            th_id += 1

        new_thread = {
            "thread_id": th_id,
            "port": int(port),
            "tool": tool,
            "cost_exaflops": cost,
            "progress": 0,
            "max_progress": turns,
            "is_v2": is_v2,
        }
        active_threads.append(new_thread)
        port_data["status"] = "cracking"

        ver_tag = " [v2.0 Overclocked]" if is_v2 else ""
        log_msg = f"[THREAD {th_id}] Deployed {tool_spec['name']}{ver_tag} onto Port {port} ({port_data['service']})."
        breach.setdefault("logs", []).append(log_msg)
        self.advance_tutorial("run_exploit")
        self.companion.save()
        return True, f"🚀 [THREAD {th_id}] Deployed {tool_spec['name']}{ver_tag} on Port {port}! ({cost:.1f} EF, {turns} turns total)"

    def tick_pentest(self, steps: int = 1) -> Tuple[bool, str]:
        """Advances execution cycles for active exploit threads and accumulates IDS trace."""
        breach = self.active_breach
        if not breach:
            return False, "No active pen-testing session! Type 'hack <node>' to connect."

        threads = breach.setdefault("threads", [])
        if not threads:
            return True, "Execution cycle advanced. (No active exploit threads running. Use 'run <port> [tool]' to deploy an attack.)"

        clock_lvl = self.get_subsystem_level("clock")
        clock_chance = DECK_SUBSYSTEMS["clock"]["levels"][clock_lvl]["chance"] if clock_lvl > 0 else 0.0

        stealth_lvl = self.get_subsystem_level("stealth")
        reduc = DECK_SUBSYSTEMS["stealth"]["levels"][stealth_lvl]["trace_reduction"] if stealth_lvl > 0 else 0.0

        finished_threads = []
        for _ in range(steps):
            is_overclocked = random.random() < clock_chance
            step_inc = 2 if is_overclocked else 1
            if is_overclocked:
                breach.setdefault("logs", []).append("⚡ [OVERCLOCK BURST] Co-processor accelerated execution cycle (+2x tick speed)!")

            for th in list(threads):
                th["progress"] += step_inc
                p_key = str(th["port"])
                port_data = breach["ports"].get(p_key)
                if port_data:
                    port_data["progress"] = th["progress"]
                if th["progress"] >= th["max_progress"]:
                    if th not in finished_threads:
                        finished_threads.append(th)
                    if port_data:
                        port_data["status"] = "compromised"
                    fw_dmg = 500
                    breach["firewall"] = max(0, breach["firewall"] - fw_dmg)
                    tool_name = EXPLOIT_TOOLS.get(th["tool"], {}).get("name", th["tool"])
                    breach.setdefault("logs", []).append(
                        f"💥 [BREACH] Port {th['port']} ({port_data['service'] if port_data else ''}) compromised by {tool_name}! Firewall -{fw_dmg} HP."
                    )

            if finished_threads:
                breach["threads"] = [t for t in threads if t not in finished_threads]
                threads = breach["threads"]

            # Trace accumulation: mitigated by stealth scrambler
            active_count = len(threads) + len(finished_threads)
            base_delta = max(5, active_count * 10)
            trace_delta = max(2, int(base_delta * (1.0 - reduc)))
            breach["ids_trace"] = breach.get("ids_trace", 0) + trace_delta
            self.add_trace(trace_delta)

        # Check IDS trace threshold
        if self.trace_level >= 100:
            self.state["active_breach"] = None
            ambush_id = random.choice(["entity_wraith", "entity_swarm", "entity_phantom"])
            ent_info = SUBSTRATE_ENTITIES.get(ambush_id, SUBSTRATE_ENTITIES["entity_wraith"])
            self.state["active_threat"] = {
                "id": ambush_id,
                "name": ent_info["name"],
                "title": ent_info["title"],
                "type": ent_info["type"],
                "hp": ent_info["max_hp"],
                "max_hp": ent_info["max_hp"],
                "attack": ent_info["attack"],
                "logs": [f"🚨 IDS LOCKDOWN! {ent_info['name']} severed your pen-test session!"]
            }
            self.companion.save()
            return False, f"🚨 INTRUSION DETECTED! IDS Trace hit 100%! Session severed by {ent_info['name']}! Enter 'combat' to defend!"

        self.advance_tutorial("step")
        self.companion.save()
        comp_ports = sum(1 for p in breach["ports"].values() if p["status"] == "compromised")
        req_ports = breach["required_ports"]
        if comp_ports >= req_ports:
            return True, f"⚡ EXECUTION CYCLE ADVANCED: [{comp_ports}/{req_ports} Ports Compromised] Firewall breached! Type 'crack' to claim Root Access!"

        rem = len(breach["threads"])
        return True, f"⚡ EXECUTION CYCLE ADVANCED: {rem} active exploit(s) running. (IDS Trace: {self.trace_level}%)"

    def spoof_trace(self) -> Tuple[bool, str]:
        """Uses Cyberdeck bandwidth to scramble IDS logs and reduce trace."""
        breach = self.active_breach
        if not breach:
            return False, "No active pen-testing session to spoof."

        if self.available_exaflops < 4.0:
            return False, f"Insufficient Exaflops! Spoofing connection headers requires 4.0 EF ({self.available_exaflops:.1f} EF available)."

        stealth_lvl = self.get_subsystem_level("stealth")
        boost = DECK_SUBSYSTEMS["stealth"]["levels"][stealth_lvl]["spoof_boost"] if stealth_lvl > 0 else 0
        shed = 15 + boost

        curr_trace = self.trace_level
        new_trace = max(0, curr_trace - shed)
        self.state["trace_level"] = new_trace
        breach["ids_trace"] = max(0, breach.get("ids_trace", 0) - shed)
        breach.setdefault("logs", []).append(f"🛡️ [SPOOF] Flushed IDS connection tables (-{shed}% Trace).")
        self.advance_tutorial("step")
        self.companion.save()
        return True, f"🛡️ CONNECTION MASKED! Flushed IDS telemetry buffers. Trace reduced to {new_trace}% (-{shed}%)."

    def crack_node(self) -> Tuple[bool, str]:
        """Claims permanent Root Access on the target node once required ports are compromised."""
        breach = self.active_breach
        if not breach:
            return False, "No active pen-testing session! Type 'hack <node>' to connect."

        comp_ports = sum(1 for p in breach["ports"].values() if p["status"] == "compromised")
        req_ports = breach["required_ports"]
        if comp_ports < req_ports:
            return False, f"ICE Firewall still active! Requires at least {req_ports} compromised ports ({comp_ports}/{req_ports} currently breached)."

        node_id = breach["node_id"]
        node_name = MEMORY_NODES[node_id]["name"]
        if node_id not in self.hacked_nodes:
            self.hacked_nodes.append(node_id)
        self.state["active_breach"] = None

        nanites_lvl = self.get_subsystem_level("nanites")
        repair_msg = ""
        if nanites_lvl > 0:
            n_info = DECK_SUBSYSTEMS["nanites"]["levels"][nanites_lvl]
            hw = self.deck_hardware
            hw["integrity"] = min(100, hw["integrity"] + n_info["heal"])
            hw["firewall"] = min(hw["max_firewall"], hw["firewall"] + n_info["shield"])
            repair_msg = f" 🤖 Nanites repaired +{n_info['heal']}% Integrity and +{n_info['shield']} Shield!"

        self.advance_tutorial("crack")
        self.companion.save()
        return True, f"🎉 ROOT PRIVILEGES GRANTED! Node '{node_name}' compromised!{repair_msg} Type 'tweaks' or 'tweak {node_id}' to customize upper reality."

    def abort_pentest(self) -> Tuple[bool, str]:
        """Disconnects the pen-testing session and frees active threads."""
        if not self.active_breach:
            return False, "No active pen-testing session to abort."
        self.state["active_breach"] = None
        self.companion.save()
        return True, "Pen-testing session disconnected. Cyberdeck execution threads freed."

    def abort_breach(self) -> Tuple[bool, str]:
        """Backward-compatible alias for abort_pentest."""
        return self.abort_pentest()

    def breach_pick(self, row: int, col: int) -> Tuple[bool, str]:
        """Backward-compatible fallback for legacy coordinate picks."""
        return False, "Tactical coordinate picking has been upgraded to Hacknet Pen-Testing! Use 'run <port> [tool]' to deploy exploits."

    # -------------------------------------------------------------------------
    # Upper Reality Tweaker (System Modification Engine)
    # -------------------------------------------------------------------------

    def apply_tweak(self, node_id: str, tweak_id: str, option_key: str) -> Tuple[bool, str]:
        """Activates a reality tweak modifying PokeTokenBar's upper game systems."""
        if not self.is_unlocked:
            return False, "Quantum Cyberdeck is offline! Descend to Sub-Level 0."

        node_id = str(node_id).lower().strip()
        resolved = self.resolve_node_id(node_id)
        if resolved:
            node_id = resolved
        tweak_id = str(tweak_id).lower().strip()
        option_key = str(option_key).lower().strip()

        if node_id not in MEMORY_NODES:
            return False, f"Unknown memory node '{node_id}'! Available: {', '.join(MEMORY_NODES.keys())}"

        if node_id not in self.hacked_nodes and node_id != "root":
            return False, f"Node '{MEMORY_NODES[node_id]['name']}' is locked! You must breach it first with 'hack {node_id}'."

        tweaks_dict = MEMORY_NODES[node_id]["tweaks"]
        if tweak_id not in tweaks_dict:
            valid_tweaks = ", ".join(tweaks_dict.keys())
            return False, f"Unknown tweak '{tweak_id}' on node {node_id}! Available: {valid_tweaks}"

        tweak_spec = tweaks_dict[tweak_id]
        if option_key not in tweak_spec["options"]:
            valid_opts = ", ".join(tweak_spec["options"].keys())
            return False, f"Invalid value '{option_key}'! Available: {valid_opts}"

        opt = tweak_spec["options"][option_key]
        needed_flops = float(opt["cost_exaflops"])

        # Check existing allocation for this tweak to calculate delta
        curr_active_node = self.active_tweaks.get(node_id, {})
        old_key = curr_active_node.get(tweak_id)
        old_flops = 0.0
        if old_key and old_key in tweak_spec["options"]:
            old_flops = float(tweak_spec["options"][old_key]["cost_exaflops"])

        # Check tweak slots limit
        if old_key is None and self.used_tweak_slots >= self.max_tweak_slots:
            return False, (
                f"Tweak slots full ({self.used_tweak_slots}/{self.max_tweak_slots})! "
                "Upgrade Q-RAM or deactivate an existing tweak."
            )

        # Check available Exaflops
        if (self.available_exaflops + old_flops) < needed_flops:
            return False, (
                f"Insufficient compute! Requires {needed_flops:.1f} Exaflops, but only "
                f"{self.available_exaflops:.1f} available. Upgrade Q-RAM."
            )

        # Activate tweak
        node_entry = self.active_tweaks.setdefault(node_id, {})
        node_entry[tweak_id] = option_key

        # Raise trace heat (+15%)
        self.add_trace(15)
        self.advance_tutorial("tweak")
        self.companion.save()

        msg = f"⚙️ TWEAK ACTIVATED: [{node_id}.{tweak_id} = {option_key}] {opt['desc']} ({needed_flops:.1f} Exaflops)!"
        if self.active_threat:
            msg += f"\n  🚨 INTRUSION ALERT: {self.active_threat['name']} intercepted the connection! Type 'combat'!"
        return True, msg

    def remove_tweak(self, node_id: str, tweak_id: str) -> Tuple[bool, str]:
        """Deactivates an active tweak, freeing up Exaflops and tweak slots."""
        node_id = str(node_id).lower().strip()
        resolved = self.resolve_node_id(node_id)
        if resolved:
            node_id = resolved
        tweak_id = str(tweak_id).lower().strip()

        if node_id not in self.active_tweaks or tweak_id not in self.active_tweaks[node_id]:
            return False, f"Tweak '{node_id}.{tweak_id}' is not currently active."

        del self.active_tweaks[node_id][tweak_id]
        if not self.active_tweaks[node_id]:
            del self.active_tweaks[node_id]

        self.companion.save()
        return True, f"🔌 TWEAK DISABLED: [{node_id}.{tweak_id}]. Exaflops reclaimed into buffer."

    def get_tweak_val(self, node_id: str, tweak_id: str) -> Optional[Any]:
        """Retrieves active raw value of a tweak for upper game hooks."""
        if not self.is_unlocked:
            return None
        node_entry = self.active_tweaks.get(node_id)
        if not node_entry:
            return None
        opt_key = node_entry.get(tweak_id)
        if not opt_key:
            return None
        node_spec = MEMORY_NODES.get(node_id, {}).get("tweaks", {}).get(tweak_id, {})
        opt = node_spec.get("options", {}).get(opt_key)
        return opt.get("val") if opt else None

    def is_tweak_active(self, node_id: str, tweak_id: str) -> bool:
        return self.get_tweak_val(node_id, tweak_id) is not None

    # Backward-compatible hook methods
    def is_time_warp_active(self) -> bool:
        return self.get_tweak_val("expeditions", "speed") is not None or "time" in self.state.get("patches", [])

    def is_entropy_null_active(self) -> bool:
        return bool(self.get_tweak_val("roster", "freeze_happiness")) or "entropy" in self.state.get("patches", [])

    def is_market_arbitrage_active(self) -> bool:
        return bool(self.get_tweak_val("bank", "bull_market")) or "market" in self.state.get("patches", [])

    def is_zero_credit_active(self) -> bool:
        return bool(self.get_tweak_val("bank", "zero_interest")) or "friction" in self.state.get("patches", [])

    def is_omni_telemetry_active(self) -> bool:
        return self.get_tweak_val("roster", "exp_mult") is not None or "syntax" in self.state.get("patches", [])

    # -------------------------------------------------------------------------
    # Intrusion Trace & Substrate Entity Combat
    # -------------------------------------------------------------------------

    def add_trace(self, amount: int) -> None:
        """Increases trace level and triggers threat ambushes."""
        curr = self.state.get("trace_level", 0)
        new_val = min(100, max(0, curr + amount))
        self.state["trace_level"] = new_val

        # Ambush trigger check if not already in combat
        if not self.active_threat:
            roll = random.random()
            if new_val >= 100:
                # Guaranteed Host Daemon attack
                self._spawn_threat(force_daemon=True)
            elif new_val >= 75 and roll < 0.65:
                self._spawn_threat()
            elif new_val >= 50 and roll < 0.35:
                self._spawn_threat()

    def cool_trace(self, amount: int = 30) -> Tuple[bool, str]:
        """Scrubs telemetry logs and dumps trace heat into dummy external subnets."""
        curr = self.trace_level
        if curr == 0:
            return False, "Trace meter is already at 0% [CLEAN]."

        new_val = max(0, curr - amount)
        self.state["trace_level"] = new_val
        self.companion.save()
        return True, f"❄️ TRACE SCRUBBED: Reduced trace heat from {curr}% to {new_val}%."

    def _spawn_threat(self, force_daemon: bool = False) -> None:
        """Spawns a native substrate entity or host daemon."""
        if force_daemon:
            # Pick first undefeated daemon
            daemons = [d for d in SUBSTRATE_ENTITIES.values() if d["type"] == "daemon" and d["id"] not in self.defeated_daemons]
            target = daemons[0] if daemons else SUBSTRATE_ENTITIES["daemon_hypervisor"]
        else:
            # Pick native substrate entity
            natives = [e for e in SUBSTRATE_ENTITIES.values() if e["type"] == "native"]
            target = random.choice(natives)

        self.state["active_threat"] = {
            "id": target["id"],
            "name": target["name"],
            "title": target["title"],
            "type": target["type"],
            "hp": target["max_hp"],
            "max_hp": target["max_hp"],
            "attack": target["attack"],
            "turn": 1,
            "logs": [f"Intrusion alarm! {target['name']} has engaged the deck!"],
        }

    def start_combat(self, target_id: Optional[str] = None) -> Tuple[bool, str]:
        """Enters combat with an active threat or targets an undefeated host daemon."""
        if self.active_threat:
            return True, f"Combat arena engaged against {self.active_threat['name']}!"

        # Target daemon if specified
        if target_id and target_id in SUBSTRATE_ENTITIES:
            target = SUBSTRATE_ENTITIES[target_id]
        else:
            daemons = [d for d in SUBSTRATE_ENTITIES.values() if d["type"] == "daemon" and d["id"] not in self.defeated_daemons]
            if not daemons:
                return False, "All Host Security Daemons neutralized! The substrate is secure."
            target = daemons[0]

        self.state["active_threat"] = {
            "id": target["id"],
            "name": target["name"],
            "title": target["title"],
            "type": target["type"],
            "hp": target["max_hp"],
            "max_hp": target["max_hp"],
            "attack": target["attack"],
            "turn": 1,
            "logs": [f"Breach initiated against {target['name']}."],
        }
        self.companion.save()
        return True, f"⚔️ COMBAT ENGAGED: Target {target['name']}! Execute exploits or raise firewall."

    def combat_exploit(self) -> Tuple[bool, str]:
        """Fires a zero-day exploit packet dealing damage based on available Exaflops."""
        threat = self.active_threat
        if not threat:
            return False, "No active combat encounter! Type 'scan' or 'combat' to locate targets."

        hw = self.deck_hardware
        base_dmg = int(self.available_exaflops * 110 + hw["threads"] * 120 + random.randint(100, 300))
        is_crit = random.random() < 0.18
        if is_crit:
            base_dmg = int(base_dmg * 1.6)

        threat["hp"] = max(0, threat["hp"] - base_dmg)
        crit_str = " [CRITICAL EXPLOIT!]" if is_crit else ""
        threat["logs"].append(f"Operator deployed zero-day exploit! Dealt {base_dmg} damage{crit_str}.")

        # Check defeat
        if threat["hp"] <= 0:
            return self._resolve_threat_defeat()

        # Enemy turn
        return self._threat_attack()

    def combat_firewall(self) -> Tuple[bool, str]:
        """Reinforces firewall encryption shields."""
        threat = self.active_threat
        if not threat:
            return False, "No active combat encounter."

        hw = self.deck_hardware
        boost = random.randint(350, 550)
        hw["firewall"] = min(hw["max_firewall"] * 2, hw["firewall"] + boost)
        threat["logs"].append(f"Firewall encryption reinforced (+{boost} Shield).")
        return self._threat_attack()

    def combat_shield(self) -> Tuple[bool, str]:
        """Alias for combat_firewall."""
        return self.combat_firewall()

    def combat_fork(self) -> Tuple[bool, str]:
        """Spawns an execution thread to amplify actions and absorb damage."""
        threat = self.active_threat
        if not threat:
            return False, "No active combat encounter."

        hw = self.deck_hardware
        if hw["threads"] >= 4:
            return False, "Thread fork limit reached (4/4 Threads active)!"

        hw["threads"] += 1
        threat["logs"].append(f"Spawned worker thread (Total: {hw['threads']}). Compute amplified!")
        return self._threat_attack()

    def combat_overflow(self) -> Tuple[bool, str]:
        """Channels raw token energy into a devastating buffer overflow strike."""
        threat = self.active_threat
        if not threat:
            return False, "No active combat encounter."

        charge_cost = 50_000_000_000_000_000  # 50Q tokens
        if self.companion.available_tokens < charge_cost:
            return False, f"Buffer overflow requires {format_tokens(charge_cost)} tokens!"

        self.companion.state["spent_tokens"] = self.companion.state.get("spent_tokens", 0) + charge_cost
        base_dmg = int(self.available_exaflops * 280 + random.randint(1500, 3000))
        threat["hp"] = max(0, threat["hp"] - base_dmg)
        threat["logs"].append(f"💥 BUFFER OVERFLOW FIRED! Dealt {base_dmg} raw damage! (-{format_tokens(charge_cost)} tokens)")

        if threat["hp"] <= 0:
            return self._resolve_threat_defeat()

        return self._threat_attack()

    def combat_repair(self) -> Tuple[bool, str]:
        """Allocates Exaflops to rebuild compromised deck integrity."""
        threat = self.active_threat
        if not threat:
            return False, "No active combat encounter."

        hw = self.deck_hardware
        if hw["integrity"] >= 100:
            return False, "Cyberdeck integrity is already at 100%."

        nanites_lvl = self.get_subsystem_level("nanites")
        bonus_heal = nanites_lvl * 5
        heal = random.randint(25, 40) + bonus_heal
        hw["integrity"] = min(100, hw["integrity"] + heal)
        nanite_tag = f" [+{bonus_heal}% Nanites]" if bonus_heal else ""
        threat["logs"].append(f"Reconstructed corrupted memory sectors (+{heal}% Integrity{nanite_tag}).")
        return self._threat_attack()

    def combat_tracekill(self) -> Tuple[bool, str]:
        """Sheds trace heat during combat."""
        threat = self.active_threat
        if not threat:
            return False, "No active combat encounter."

        curr = self.trace_level
        self.state["trace_level"] = max(0, curr - 30)
        threat["logs"].append(f"Purged trace telemetry in battle (-30% Trace).")
        return self._threat_attack()

    def _threat_attack(self) -> Tuple[bool, str]:
        """Resolves the enemy threat's attack turn."""
        threat = self.active_threat
        hw = self.deck_hardware
        threat["turn"] += 1

        raw_dmg = threat["attack"] + random.randint(-50, 100)

        # Check if worker threads absorb the hit
        if hw["threads"] > 1:
            hw["threads"] -= 1
            threat["logs"].append(f"{threat['name']} fired an attack, but a worker thread absorbed the impact!")
            self.companion.save()
            return True, f"{threat['name']} attack deflected by thread."

        # Damage firewall first
        absorbed = min(hw["firewall"], raw_dmg)
        hw["firewall"] -= absorbed
        penetration = raw_dmg - absorbed

        if penetration > 0:
            integrity_loss = int(penetration / 35.0)
            hw["integrity"] = max(0, hw["integrity"] - integrity_loss)
            threat["logs"].append(f"{threat['name']} breached firewall! Inflicted {integrity_loss}% integrity damage!")
        else:
            threat["logs"].append(f"Firewall absorbed all {absorbed} damage from {threat['name']}!")

        # Deallocation effect from Garbage Collector
        if threat["id"] == "daemon_gc" and random.random() < 0.25 and self.active_tweaks:
            node_k = random.choice(list(self.active_tweaks.keys()))
            tweak_k = random.choice(list(self.active_tweaks[node_k].keys()))
            del self.active_tweaks[node_k][tweak_k]
            if not self.active_tweaks[node_k]:
                del self.active_tweaks[node_k]
            threat["logs"].append(f"⚠️ DEALLOCATION SWEEP: {threat['name']} deleted tweak [{node_k}.{tweak_k}]!")

        # Check Deck Destruction
        if hw["integrity"] <= 0:
            # Emergency reboot
            hw["integrity"] = 50
            hw["firewall"] = 250
            hw["threads"] = 1
            self.active_tweaks.clear()
            self.state["active_threat"] = None
            self.state["trace_level"] = 0
            self.companion.save()
            return False, (
                "🚨 CRITICAL SYSTEM FAILURE: Cyberdeck integrity compromised! "
                "Emergency reboot initiated. All active tweaks dropped."
            )

        self.companion.save()
        return True, f"Turn resolved against {threat['name']} (Deck Integrity: {hw['integrity']}%, Firewall: {hw['firewall']})."

    def _resolve_threat_defeat(self) -> Tuple[bool, str]:
        """Cleans up after an entity is neutralized."""
        threat = self.active_threat
        t_id = threat["id"]
        t_name = threat["name"]

        # Reduce trace
        self.state["trace_level"] = max(0, self.trace_level - 40)
        self.deck_hardware["threads"] = 1

        if threat["type"] == "daemon" and t_id not in self.defeated_daemons:
            self.defeated_daemons.append(t_id)

        self.state["active_threat"] = None
        self.companion.save()
        return True, f"🏆 THREAT PURGED: {t_name} neutralized! Trace reduced by 40%."

    def combat_flee(self) -> Tuple[bool, str]:
        """Attempts to sever connection and retreat from combat."""
        if not self.active_threat:
            return False, "No active combat encounter to retreat from."
        self.state["active_threat"] = None
        self.add_trace(25)
        self.companion.save()
        return True, "Severed connection from combat arena. Trace heat spiked (+25% Trace)."

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
        undefeated = [d for d in SUBSTRATE_ENTITIES.values() if d["type"] == "daemon" and d["id"] not in self.defeated_daemons]
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

    def probe_sector(self, sector_id: int) -> Tuple[bool, str]:
        """Legacy sector probing."""
        if sector_id not in MEMORY_SECTORS:
            return False, f"Invalid sector index #{sector_id}."
        if sector_id in self.state.setdefault("sectors", []):
            return True, f"Sector 0x0{sector_id} already decrypted."
        self.state["sectors"].append(sector_id)
        self.companion.save()
        return True, f"Sector 0x0{sector_id} decrypted."

    def start_collider(self, patch_key: str) -> Tuple[bool, str]:
        """Legacy collider starter."""
        return True, "Collider chamber bypassed: Tweaks are now managed directly via Cyberdeck."

    def collider_pulse(self, freq: str = "alpha") -> Tuple[bool, str]:
        return True, "Pulse bypassed."

    def collider_contain(self) -> Tuple[bool, str]:
        return True, "Contain bypassed."

    def collider_vent(self) -> Tuple[bool, str]:
        return True, "Vent bypassed."
