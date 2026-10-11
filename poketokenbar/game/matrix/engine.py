"""Engine logic for the Quantum Singularity Matrix (QSM)."""

import random
from typing import Dict, List, Tuple, Optional, Any

from poketokenbar.utils.formatting import format_tokens
from poketokenbar.game.matrix.models import (
    MATRIX_ENTRY_COST,
    ROOT_TRANSCENDENCE_COST,
    QRAM_BLOCKS,
    REALITY_PATCHES,
    KERNEL_DAEMONS,
    MEMORY_SECTORS,
)


class MatrixEngine:
    """Manages Q-RAM allocation, Particle Collider synthesis, Kernel Protocol Combat, and meta-story probing."""

    def __init__(self, companion_engine):
        self.companion = companion_engine

    @property
    def state(self) -> Dict[str, Any]:
        st = self.companion.state.setdefault("matrix", {})
        st.setdefault("unlocked", False)
        st.setdefault("ram_blocks", [])
        st.setdefault("patches", [])
        st.setdefault("sectors", [])
        st.setdefault("defeated_daemons", [])
        st.setdefault("root_transcended", False)
        st.setdefault("total_tokens_consumed", 0)
        st.setdefault("collider_state", None)
        st.setdefault("combat_state", None)
        st.setdefault("story_viewed", False)
        return st

    @property
    def is_unlocked(self) -> bool:
        return bool(self.state.get("unlocked", False))

    @property
    def ram_blocks(self) -> List[int]:
        return self.state.setdefault("ram_blocks", [])

    @property
    def patches(self) -> List[str]:
        return self.state.setdefault("patches", [])

    @property
    def sectors(self) -> List[int]:
        return self.state.setdefault("sectors", [])

    @property
    def defeated_daemons(self) -> List[str]:
        return self.state.setdefault("defeated_daemons", [])

    @property
    def is_root_transcended(self) -> bool:
        return bool(self.state.get("root_transcended", False))

    # -------------------------------------------------------------------------
    # Q-RAM Allocation (500Q - 10,000Q)
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
        return True, f"💾 Q-RAM ALLOCATED! {info['name']} ({info['capacity']}) is now ONLINE! (-{format_tokens(cost)} tokens)"

    # -------------------------------------------------------------------------
    # Particle Collider Minigame (Reality Patch Synthesis)
    # -------------------------------------------------------------------------

    def start_collider(self, patch_key: str) -> Tuple[bool, str]:
        """Initializes the Singularity Particle Collider to synthesize a Reality Patch."""
        if not self.is_unlocked:
            return False, "Quantum Singularity Matrix is not initialized!"

        if not self.ram_blocks:
            return False, "Singularity Particle Collider requires at least Q-RAM Block 0x01 allocated!"

        clean_key = str(patch_key).lower().strip()
        # Resolve by index or name
        if clean_key.isdigit():
            idx = int(clean_key) - 1
            keys = list(REALITY_PATCHES.keys())
            if 0 <= idx < len(keys):
                clean_key = keys[idx]
        
        if clean_key not in REALITY_PATCHES:
            return False, f"Unknown reality patch '{patch_key}'! (Valid: time, entropy, market, friction, syntax)"

        patch = REALITY_PATCHES[clean_key]
        if clean_key in self.patches:
            return False, f"{patch['name']} ({patch['code']}) is already compiled and active!"

        cost = patch["cost"]
        avail = self.companion.available_tokens
        if avail < cost:
            return False, f"Not enough tokens! Collider initialization for {patch['name']} requires {format_tokens(cost)} tokens."

        # Deduct cost
        self.companion.state["spent_tokens"] = self.companion.state.get("spent_tokens", 0) + cost
        self.state["total_tokens_consumed"] = self.state.get("total_tokens_consumed", 0) + cost

        self.state["collider_state"] = {
            "patch_id": clean_key,
            "patch_name": patch["name"],
            "patch_code": patch["code"],
            "resonance_target": patch["resonance_target"],
            "turns_left": 3,
            "resonance": 50,
            "containment": 100,
            "thermal_flux": 20,
            "active": True,
            "message": f"Collider chamber active! Target Resonance: {patch['resonance_target']}%. Tune pulse harmonics!"
        }
        self.companion.save()
        return True, f"⚛️ COLLIDER ENGAGED: Loaded {format_tokens(cost)} tokens into collision chamber for {patch['code']}!"

    def collider_pulse(self, freq: str = "alpha") -> Tuple[bool, str]:
        """Injects a harmonic frequency pulse into the particle chamber."""
        st = self.state.get("collider_state")
        if not st or not st.get("active"):
            return False, "Particle Collider is idle! Type 'synthesize <patch_id>' to load a patch."

        clean_freq = freq.lower().strip()
        if clean_freq in ["alpha", "a", "1"]:
            res_gain = random.randint(14, 18)
            cont_loss = random.randint(8, 12)
            heat_gain = random.randint(12, 16)
            mode_name = "ALPHA [14-18% Res]"
        elif clean_freq in ["beta", "b", "2"]:
            res_gain = random.randint(20, 26)
            cont_loss = random.randint(15, 20)
            heat_gain = random.randint(20, 28)
            mode_name = "BETA [20-26% Res]"
        elif clean_freq in ["gamma", "g", "3"]:
            res_gain = random.randint(28, 36)
            cont_loss = random.randint(24, 30)
            heat_gain = random.randint(30, 40)
            mode_name = "GAMMA [28-36% Res]"
        else:
            return False, "Invalid pulse frequency! Choose 'alpha', 'beta', or 'gamma'."

        st["resonance"] = min(100, st["resonance"] + res_gain)
        st["containment"] = max(0, st["containment"] - cont_loss)
        st["thermal_flux"] = min(100, st["thermal_flux"] + heat_gain)
        st["turns_left"] -= 1

        return self._evaluate_collider_step(f"Injected {mode_name} pulse: +{res_gain}% Res, -{cont_loss}% Cont, +{heat_gain}% Heat.")

    def collider_contain(self) -> Tuple[bool, str]:
        """Reinforces magnetic containment fields at the expense of a turn and slight resonance decay."""
        st = self.state.get("collider_state")
        if not st or not st.get("active"):
            return False, "Particle Collider is idle!"

        cont_gain = random.randint(28, 38)
        heat_loss = random.randint(8, 14)
        res_loss = random.randint(4, 7)

        st["containment"] = min(100, st["containment"] + cont_gain)
        st["thermal_flux"] = max(0, st["thermal_flux"] - heat_loss)
        st["resonance"] = max(0, st["resonance"] - res_loss)
        st["turns_left"] -= 1

        return self._evaluate_collider_step(f"Reinforced containment fields: +{cont_gain}% Cont, -{heat_loss}% Heat, -{res_loss}% Res.")

    def collider_vent(self) -> Tuple[bool, str]:
        """Purges chamber thermal flux at the expense of a turn and containment integrity."""
        st = self.state.get("collider_state")
        if not st or not st.get("active"):
            return False, "Particle Collider is idle!"

        heat_loss = random.randint(35, 48)
        cont_loss = random.randint(8, 14)
        res_loss = random.randint(6, 10)

        st["thermal_flux"] = max(0, st["thermal_flux"] - heat_loss)
        st["containment"] = max(0, st["containment"] - cont_loss)
        st["resonance"] = max(0, st["resonance"] - res_loss)
        st["turns_left"] -= 1

        return self._evaluate_collider_step(f"Vented cryogenic coolant: -{heat_loss}% Heat, -{cont_loss}% Cont, -{res_loss}% Res.")

    def _evaluate_collider_step(self, action_msg: str) -> Tuple[bool, str]:
        st = self.state["collider_state"]

        # Check breach conditions
        if st["containment"] <= 0:
            st["active"] = False
            self.companion.save()
            return False, f"💥 CONTAINMENT BREACH! Magnetic field collapsed. Synthesis failed! ({action_msg})"

        if st["thermal_flux"] >= 100:
            st["active"] = False
            self.companion.save()
            return False, f"🔥 THERMAL CRITICAL! Singularity chamber overheated. Synthesis failed! ({action_msg})"

        # Check turn completion
        if st["turns_left"] <= 0:
            st["active"] = False
            target = st["resonance_target"]
            actual = st["resonance"]
            if actual >= target:
                p_id = st["patch_id"]
                if p_id not in self.patches:
                    self.patches.append(p_id)
                self.companion.save()
                return True, f"✨ SYNTHESIS COMPLETE! Achieved {actual}% Resonance (Target: {target}%). Reality Patch {st['patch_code']} successfully compiled! 🎉"
            else:
                self.companion.save()
                return False, f"⚠️ SYNTHESIS FAILED: Final Resonance {actual}% fell short of {target}% threshold. Energy dissipated."

        self.companion.save()
        st["message"] = action_msg
        return True, action_msg

    # -------------------------------------------------------------------------
    # Tactical Kernel Protocol Combat (Host OS Security Defense)
    # -------------------------------------------------------------------------

    def start_combat(self, daemon_id: Optional[str] = None) -> Tuple[bool, str]:
        """Deploys system execution threads to combat active host security daemons."""
        if not self.is_unlocked:
            return False, "Quantum Singularity Matrix is not initialized!"

        # Pick daemon
        if not daemon_id:
            # Pick first undefeated daemon, or last
            for d_id in ["daemon_gc", "daemon_watchdog", "daemon_hypervisor"]:
                if d_id not in self.defeated_daemons:
                    daemon_id = d_id
                    break
            if not daemon_id:
                daemon_id = "daemon_hypervisor"

        clean_id = daemon_id.lower().strip()
        if clean_id not in KERNEL_DAEMONS:
            return False, f"Unknown daemon '{daemon_id}'! (Valid: daemon_gc, daemon_watchdog, daemon_hypervisor)"

        daemon = KERNEL_DAEMONS[clean_id]
        player_max = 12000 + (len(self.ram_blocks) * 4000)

        self.state["combat_state"] = {
            "daemon_id": clean_id,
            "daemon_name": daemon["name"],
            "daemon_title": daemon["title"],
            "daemon_hp": daemon["max_hp"],
            "daemon_max_hp": daemon["max_hp"],
            "daemon_attack": daemon["attack"],
            "player_hp": player_max,
            "player_max_hp": player_max,
            "player_shield": 1000,
            "fork_count": 1,
            "flux": 40,
            "active": True,
            "log": [f"🚨 ALERT: {daemon['name']} deployed by host OS to purge memory sectors!"]
        }
        self.companion.save()
        return True, f"⚔️ COMBAT ENGAGED: Infiltrating {daemon['name']} [{daemon['title']}]!"

    def combat_exploit(self) -> Tuple[bool, str]:
        """Executes a buffer exploit dealing direct damage scaled by thread fork count."""
        st = self.state.get("combat_state")
        if not st or not st.get("active"):
            return False, "No active combat engagement! Type 'combat' to engage security daemons."

        forks = st.get("fork_count", 1)
        dmg = random.randint(1400, 2100) * forks
        st["daemon_hp"] = max(0, st["daemon_hp"] - dmg)
        st["flux"] = min(100, st["flux"] + 15)
        st["log"].append(f"• Injected {forks}x memory exploit: {dmg} damage to {st['daemon_name']}!")

        if st["daemon_hp"] <= 0:
            return self._handle_combat_victory()

        self._daemon_counterattack()
        self.companion.save()
        return True, f"💥 Exploit struck for {dmg} damage!"

    def combat_shield(self) -> Tuple[bool, str]:
        """Deploys cryptographic firewall shielding and restores bandwidth."""
        st = self.state.get("combat_state")
        if not st or not st.get("active"):
            return False, "No active combat engagement!"

        shield_gain = random.randint(2200, 3200)
        hp_heal = random.randint(600, 1000)
        st["player_shield"] += shield_gain
        st["player_hp"] = min(st["player_max_hp"], st["player_hp"] + hp_heal)
        st["flux"] = min(100, st["flux"] + 10)
        st["log"].append(f"• Deployed firewall: +{shield_gain} Shield, +{hp_heal} Bandwidth.")

        self._daemon_counterattack()
        self.companion.save()
        return True, f"🛡️ Firewall raised! (+{shield_gain} Shield)"

    def combat_fork(self) -> Tuple[bool, str]:
        """Forks active execution threads to multiply attack output."""
        st = self.state.get("combat_state")
        if not st or not st.get("active"):
            return False, "No active combat engagement!"

        forks = st.get("fork_count", 1)
        if forks >= 4:
            return False, "Maximum thread concurrency reached (4x Fork Limit)!"

        if st["flux"] < 25:
            return False, f"Not enough Quantum Flux! Thread forking requires 25 Flux (Current: {st['flux']})."

        st["flux"] -= 25
        st["fork_count"] = forks + 1
        st["log"].append(f"• Forked execution thread! Concurrency increased to {st['fork_count']}x.")

        self._daemon_counterattack()
        self.companion.save()
        return True, f"⚡ Thread forked to {st['fork_count']}x concurrency!"

    def combat_overflow(self) -> Tuple[bool, str]:
        """Discharges 80 Quantum Flux for a massive critical segment fault burst."""
        st = self.state.get("combat_state")
        if not st or not st.get("active"):
            return False, "No active combat engagement!"

        if st["flux"] < 80:
            return False, f"Not enough Quantum Flux! Buffer Overflow requires 80 Flux (Current: {st['flux']})."

        st["flux"] -= 80
        forks = st.get("fork_count", 1)
        dmg = random.randint(5500, 7500) * forks
        st["daemon_hp"] = max(0, st["daemon_hp"] - dmg)
        st["log"].append(f"💥 CRITICAL BUFFER OVERFLOW: {dmg} devastating damage dealt!")

        if st["daemon_hp"] <= 0:
            return self._handle_combat_victory()

        self._daemon_counterattack()
        self.companion.save()
        return True, f"🔥 BUFFER OVERFLOW struck for {dmg} damage!"

    def _daemon_counterattack(self):
        st = self.state["combat_state"]
        base_atk = st["daemon_attack"]
        incoming = int(base_atk * random.uniform(0.85, 1.25))

        shield = st.get("player_shield", 0)
        if shield >= incoming:
            st["player_shield"] -= incoming
            absorbed = incoming
            penetrated = 0
        else:
            absorbed = shield
            penetrated = incoming - shield
            st["player_shield"] = 0
            st["player_hp"] = max(0, st["player_hp"] - penetrated)

        st["log"].append(f"⚠️ {st['daemon_name']} counterattacked: {incoming} dmg ({absorbed} absorbed, {penetrated} penetrated).")
        if len(st["log"]) > 5:
            st["log"] = st["log"][-5:]

        if st["player_hp"] <= 0:
            st["active"] = False
            st["log"].append("💀 CONNECTION TERMINATED: Execution thread purged by host OS.")

    def _handle_combat_victory(self) -> Tuple[bool, str]:
        st = self.state["combat_state"]
        st["active"] = False
        d_id = st["daemon_id"]
        d_name = st["daemon_name"]

        if d_id not in self.defeated_daemons:
            self.defeated_daemons.append(d_id)

        self.companion.save()
        return True, f"🎉 THREAT PURGED: {d_name} was deallocated! Rogue memory sector successfully secured!"

    # -------------------------------------------------------------------------
    # Substrate Sector Probing (Lore & Meta-Story Exploration)
    # -------------------------------------------------------------------------

    def probe_sector(self, sector_idx: int) -> Tuple[bool, str]:
        """Probes and decrypts a corrupted memory sector in the host substrate."""
        if not self.is_unlocked:
            return False, "Quantum Singularity Matrix is not initialized!"

        if sector_idx not in MEMORY_SECTORS:
            return False, f"Invalid memory sector #{sector_idx}! (Valid: 0 to 7)"

        sec = MEMORY_SECTORS[sector_idx]
        if sector_idx in self.sectors:
            return True, f"📂 SECTOR 0x0{sector_idx} ALREADY DECRYPTED:\n" + "\n".join(sec["snippet"])

        cost = sec["cost"]
        avail = self.companion.available_tokens
        if avail < cost:
            return False, f"Not enough spendable tokens! Decrypting Sector 0x0{sector_idx} requires {format_tokens(cost)} tokens."

        # Prerequisite: must have probed previous sector (sector 0 is free to probe if enough tokens)
        if sector_idx > 0 and (sector_idx - 1) not in self.sectors:
            return False, f"Sector 0x0{sector_idx} is locked behind sector 0x0{sector_idx - 1} encryption!"

        self.companion.state["spent_tokens"] = self.companion.state.get("spent_tokens", 0) + cost
        self.sectors.append(sector_idx)
        self.state["total_tokens_consumed"] = self.state.get("total_tokens_consumed", 0) + cost
        self.companion.save()

        msg = f"🔓 DECRYPTED {sec['name']} (-{format_tokens(cost)} tokens):\n" + "\n".join(sec["snippet"])
        return True, msg

    # -------------------------------------------------------------------------
    # Root Transcendence Climax (10,000Q Authorization)
    # -------------------------------------------------------------------------

    def execute_root_transcendence(self) -> Tuple[bool, str]:
        """Authorizes Root Transcendence at the climax of the Matrix expansion."""
        if not self.is_unlocked:
            return False, "Quantum Singularity Matrix is not initialized!"

        if self.is_root_transcended:
            return False, "Root Transcendence has already been executed! You are the Sovereign Root Architect."

        # Check all 5 RAM blocks
        if len(self.ram_blocks) < len(QRAM_BLOCKS):
            return False, f"Incomplete memory bank! You must allocate all 5 Q-RAM blocks (Current: {len(self.ram_blocks)}/5)."

        # Check all 5 Reality Patches
        if len(self.patches) < len(REALITY_PATCHES):
            return False, f"Incomplete patch array! You must synthesize all 5 Reality Patches (Current: {len(self.patches)}/5)."

        # Check all 3 daemons defeated
        if len(self.defeated_daemons) < len(KERNEL_DAEMONS):
            return False, f"Security threats remain active! You must defeat all 3 Kernel Daemons (Current: {len(self.defeated_daemons)}/3)."

        cost = ROOT_TRANSCENDENCE_COST
        avail = self.companion.available_tokens
        if avail < cost:
            return False, f"Not enough tokens! Root Transcendence requires {format_tokens(cost)} tokens (Current: {format_tokens(avail)})."

        self.companion.state["spent_tokens"] = self.companion.state.get("spent_tokens", 0) + cost
        self.state["root_transcended"] = True
        self.state["total_tokens_consumed"] = self.state.get("total_tokens_consumed", 0) + cost

        badges = self.companion.state.setdefault("gym_badges", [])
        title = "💠 Root Architect of the Matrix"
        if title not in badges:
            badges.append(title)

        self.companion.save()
        return True, "🌌 TRANSCENDENCE COMPLETE! You have achieved absolute Root Authorization over the Matrix and simulation! Title: '💠 Root Architect of the Matrix' awarded!"

    # -------------------------------------------------------------------------
    # System Hook Queries for the Upper World
    # -------------------------------------------------------------------------

    def is_time_warp_active(self) -> bool:
        return "time" in self.patches

    def is_entropy_null_active(self) -> bool:
        return "entropy" in self.patches

    def is_market_arbitrage_active(self) -> bool:
        return "market" in self.patches

    def is_zero_credit_active(self) -> bool:
        return "friction" in self.patches

    def is_omni_telemetry_active(self) -> bool:
        return "syntax" in self.patches
