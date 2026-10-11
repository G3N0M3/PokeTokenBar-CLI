"""Engine logic for the Quantum Singularity Matrix (QSM) Hack-Simulator & Cyberdeck."""

import random
from typing import Dict, List, Tuple, Optional, Any

from poketokenbar.utils.formatting import format_tokens
from poketokenbar.game.matrix.models import (
    MATRIX_ENTRY_COST,
    ROOT_TRANSCENDENCE_COST,
    HEX_BREACH_TOKENS,
    QRAM_BLOCKS,
    MEMORY_NODES,
    SUBSTRATE_ENTITIES,
    REALITY_PATCHES,
    MEMORY_SECTORS,
    KERNEL_DAEMONS,
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
        st.setdefault("active_breach", None)
        st.setdefault("active_threat", None)
        st.setdefault("defeated_daemons", [])
        st.setdefault("root_transcended", False)
        st.setdefault("total_tokens_consumed", 0)
        st.setdefault("patches", [])
        st.setdefault("sectors", [])
        st.setdefault("collider_state", None)
        st.setdefault("combat_state", None)
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
    def deck_hardware(self) -> Dict[str, Any]:
        hw = self.state.setdefault("deck_hardware", {})
        hw.setdefault("integrity", 100)
        hw.setdefault("firewall", 500)
        hw.setdefault("max_firewall", 500)
        hw.setdefault("threads", 1)
        return hw

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
        """Calculates current Exaflops allocated to active tweaks."""
        total = 0.0
        for node_id, tweaks in self.active_tweaks.items():
            if node_id not in MEMORY_NODES:
                continue
            for tweak_id, opt_key in tweaks.items():
                node_spec = MEMORY_NODES[node_id]["tweaks"].get(tweak_id)
                if node_spec and opt_key in node_spec["options"]:
                    total += float(node_spec["options"][opt_key]["cost_exaflops"])
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
                "desc": info["desc"],
                "hacked": is_hacked,
                "active_tweaks": active,
                "tweaks_available": info["tweaks"],
            }
        return results

    def start_breach(self, node_id: str) -> Tuple[bool, str]:
        """Initializes an interactive 4x4 Hex Memory Alignment puzzle for a node."""
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

        # Generate 4x4 Grid
        grid: List[List[str]] = []
        for _ in range(4):
            row = [random.choice(HEX_BREACH_TOKENS) for _ in range(4)]
            grid.append(row)

        # Generate solvable target sequence of length 3 (or 4 for high ICE)
        seq_len = 4 if node["ice_level"] >= 3 else 3
        seq_coords: List[Tuple[int, int]] = []
        # Alternate row / col selection (Cyberpunk netrunning style)
        curr_r = random.randint(0, 3)
        curr_c = random.randint(0, 3)
        seq_coords.append((curr_r, curr_c))
        is_row = True
        for _ in range(seq_len - 1):
            if is_row:
                curr_c = random.choice([c for c in range(4) if c != curr_c])
            else:
                curr_r = random.choice([r for r in range(4) if r != curr_r])
            seq_coords.append((curr_r, curr_c))
            is_row = not is_row

        target = [grid[r][c] for r, c in seq_coords]
        cycles = seq_len + 2

        self.state["active_breach"] = {
            "node_id": node_id,
            "grid": grid,
            "target": target,
            "buffer": [],
            "cycles": cycles,
            "max_cycles": cycles,
        }
        self.companion.save()
        return True, f"🔓 BREACH MATRIX ACTIVE: Target node {node['code']}. Align memory buffer to crack ICE."

    def breach_pick(self, row: int, col: int) -> Tuple[bool, str]:
        """Picks a coordinate in the 4x4 grid to align a hex byte."""
        breach = self.active_breach
        if not breach:
            return False, "No active breach session! Type 'hack <node>' to initiate."

        if not (0 <= row < 4 and 0 <= col < 4):
            return False, "Coordinate out of range! Use row (0-3) and col (0-3). Example: 'pick 1 2'"

        token = breach["grid"][row][col]
        breach["buffer"].append(token)
        breach["cycles"] -= 1

        buf = breach["buffer"]
        target = breach["target"]
        node_id = breach["node_id"]
        node_name = MEMORY_NODES[node_id]["name"]

        # Check match: does the buffer end with the target sequence?
        target_len = len(target)
        if len(buf) >= target_len and buf[-target_len:] == target:
            # Breach successful!
            self.hacked_nodes.append(node_id)
            self.state["active_breach"] = None
            self.companion.save()
            return True, f"🎉 ROOT ACCESS GRANTED! Node '{node_name}' compromised! Type 'tweak {node_id}' to customize."

        # Check out of cycles
        if breach["cycles"] <= 0:
            self.state["active_breach"] = None
            self.add_trace(20)
            self.companion.save()
            return False, f"⚠️ BREACH FAILED! Buffer cycles exhausted. Host intrusion alarm triggered (+20% Trace)!"

        self.companion.save()
        matched_so_far = 0
        for i in range(len(target), 0, -1):
            if buf[-i:] == target[:i]:
                matched_so_far = i
                break

        return True, f"Aligned [{token}]. Buffer: {' '.join(buf)} (Target matched: {matched_so_far}/{target_len}, {breach['cycles']} cycles left)"

    def abort_breach(self) -> Tuple[bool, str]:
        """Aborts the currently running breach session."""
        if not self.active_breach:
            return False, "No active breach session to abort."
        self.state["active_breach"] = None
        self.companion.save()
        return True, "Breach session terminated. Target node disconnected."

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

        heal = random.randint(25, 40)
        hw["integrity"] = min(100, hw["integrity"] + heal)
        threat["logs"].append(f"Reconstructed corrupted memory sectors (+{heal}% Integrity).")
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
