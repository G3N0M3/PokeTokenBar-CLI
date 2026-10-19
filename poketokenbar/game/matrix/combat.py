"""Intrusion trace management and Substrate Entity / Daemon combat mixin."""

import random
from typing import Tuple, Optional

from poketokenbar.utils.formatting import format_tokens
from poketokenbar.game.matrix.models import SUBSTRATE_ENTITIES


class MatrixCombatMixin:
    """Handles IDS trace accumulation, substrate entity ambushes, and turn-based cyber-combat."""

    @property
    def daemon_raid_tier(self) -> int:
        """Current repeatable Overclocked Daemon Raid tier (starts at 1)."""
        return int(self.state.setdefault("daemon_raid_tier", 1))

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
            daemons = [
                d for d in SUBSTRATE_ENTITIES.values()
                if d["type"] == "daemon" and d["id"] not in self.defeated_daemons
            ]
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
            "drain_exaflops": float(target.get("drain_exaflops", 0.0)),
            "reward_flux": int(target.get("reward_flux", 50)),
            "throttled_ef": 0.0,
            "turn": 1,
            "logs": [f"Intrusion alarm! {target['name']} has engaged the deck!"],
        }

    def start_combat(self, target_id: Optional[str] = None) -> Tuple[bool, str]:
        """Enters combat with an active threat, undefeated daemon, or Overclocked Raid Daemon."""
        if self.active_threat:
            return True, f"Combat arena engaged against {self.active_threat['name']}!"

        # Target daemon if specified
        if target_id and target_id in SUBSTRATE_ENTITIES:
            target = SUBSTRATE_ENTITIES[target_id]
            if target["type"] == "daemon":
                daemon_order = ["daemon_gc", "daemon_watchdog", "daemon_hypervisor"]
                if target_id in daemon_order:
                    idx = daemon_order.index(target_id)
                    for prev_id in daemon_order[:idx]:
                        if prev_id not in self.defeated_daemons:
                            prev_name = SUBSTRATE_ENTITIES[prev_id]["name"]
                            return False, f"Cannot target {target['name']} yet! Neutralize {prev_name} first."
        else:
            daemons = [
                d for d in SUBSTRATE_ENTITIES.values()
                if d["type"] == "daemon" and d["id"] not in self.defeated_daemons
            ]
            if daemons:
                target = daemons[0]
            else:
                # All 3 story Daemons defeated -> spawn repeatable Overclocked Raid Daemon
                tier = self.daemon_raid_tier
                base = SUBSTRATE_ENTITIES["daemon_hypervisor"]
                max_hp = int(base["max_hp"] * (1.5 ** (tier - 1)))
                attack = int(base["attack"] * (1.25 ** (tier - 1)))
                reward_flux = int(base.get("reward_flux", 1000) * tier)
                drain_ef = float(base.get("drain_exaflops", 16.0)) + (tier - 1) * 4.0
                target = {
                    "id": f"daemon_raid_t{tier}",
                    "name": f"Overclocked Hypervisor [T{tier}]",
                    "title": f"Tier-{tier} Singularity Raid Daemon",
                    "type": "raid_daemon",
                    "raid_tier": tier,
                    "max_hp": max_hp,
                    "attack": attack,
                    "drain_exaflops": drain_ef,
                    "reward_flux": reward_flux,
                }

        self.state["active_threat"] = {
            "id": target["id"],
            "name": target["name"],
            "title": target["title"],
            "type": target["type"],
            "raid_tier": target.get("raid_tier"),
            "hp": target["max_hp"],
            "max_hp": target["max_hp"],
            "attack": target["attack"],
            "drain_exaflops": float(target.get("drain_exaflops", 0.0)),
            "reward_flux": int(target.get("reward_flux", 50)),
            "throttled_ef": 0.0,
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
        throttled = float(threat.get("throttled_ef", 0.0))
        eff_ef = max(1.0, self.available_exaflops - throttled)
        dmg_mult = self.get_sector_exploit_multiplier()
        base_dmg = int((eff_ef * 110 + hw["threads"] * 120 + random.randint(100, 300)) * dmg_mult)
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
        max_combat_threads = max(4, self.max_threads)
        if hw["threads"] >= max_combat_threads:
            return False, f"Thread fork limit reached ({hw['threads']}/{max_combat_threads} Threads active)!"

        hw["threads"] += 1
        new_th = hw["threads"]
        threat["logs"].append(f"Spawned worker thread (Total: {new_th}/{max_combat_threads}). Compute amplified!")
        ok, msg = self._threat_attack()
        return ok, f"Forked worker thread ({new_th}/{max_combat_threads}). {msg}"

    def combat_overflow(self) -> Tuple[bool, str]:
        """Channels raw token energy into a devastating buffer overflow strike."""
        threat = self.active_threat
        if not threat:
            return False, "No active combat encounter."

        charge_cost = 50_000_000_000_000_000  # 50Q tokens
        if self.companion.available_tokens < charge_cost:
            return False, f"Buffer overflow requires {format_tokens(charge_cost)} tokens!"

        self.companion.state["spent_tokens"] = self.companion.state.get("spent_tokens", 0) + charge_cost
        self.state["total_tokens_consumed"] = self.state.get("total_tokens_consumed", 0) + charge_cost
        throttled = float(threat.get("throttled_ef", 0.0))
        eff_ef = max(1.0, self.available_exaflops - throttled)
        dmg_mult = self.get_sector_exploit_multiplier()
        base_dmg = int((eff_ef * 280 + random.randint(1500, 3000)) * dmg_mult)
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
        """Sheds trace heat, clears compute throttling, and executes a stealth exploit strike."""
        threat = self.active_threat
        if not threat:
            return False, "No active combat encounter."

        curr = self.trace_level
        self.state["trace_level"] = max(0, curr - 40)
        threat["throttled_ef"] = 0.0

        hw = self.deck_hardware
        dmg_mult = self.get_sector_exploit_multiplier()
        stealth_dmg = int((self.available_exaflops * 55 + hw["threads"] * 60 + 150) * dmg_mult)
        threat["hp"] = max(0, threat["hp"] - stealth_dmg)
        threat["logs"].append(
            f"❄️ TRACEKILL: Purged -40% Trace, cleared EF throttle, & dealt {stealth_dmg} stealth damage!"
        )

        if threat["hp"] <= 0:
            return self._resolve_threat_defeat()

        ok, msg = self._threat_attack()
        if self.active_threat:
            self.active_threat["throttled_ef"] = 0.0
            self.companion.save()
        return ok, f"❄️ TRACEKILL EXECUTED (-40% Trace, {stealth_dmg} Stealth Dmg)! {msg}"

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

        # Entity Exaflop Drain / Compute Throttle
        drain_ef = float(threat.get("drain_exaflops", 0.0))
        if drain_ef > 0 and random.random() < 0.35:
            curr_throttle = float(threat.get("throttled_ef", 0.0))
            new_throttle = min(self.max_exaflops * 0.75, curr_throttle + drain_ef)
            threat["throttled_ef"] = new_throttle
            threat["logs"].append(
                f"⚡ COMPUTE THROTTLE: {threat['name']} drained {drain_ef:.1f} EF combat bandwidth!"
            )

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
        """Cleans up after an entity is neutralized and awards Quantum Flux & token bounties."""
        threat = self.active_threat
        t_id = threat["id"]
        t_name = threat["name"]
        t_type = threat.get("type", "native")

        # Reduce trace
        self.state["trace_level"] = max(0, self.trace_level - 40)
        self.deck_hardware["threads"] = 1

        if t_type == "daemon" and t_id not in self.defeated_daemons:
            self.defeated_daemons.append(t_id)
        elif t_type == "raid_daemon":
            self.state["daemon_raid_tier"] = int(self.state.get("daemon_raid_tier", 1)) + 1

        # Award Quantum Flux & Spendable Token Bounty
        base_flux = int(threat.get("reward_flux", SUBSTRATE_ENTITIES.get(t_id, {}).get("reward_flux", 50)))
        flux_gain = max(1, int(round(base_flux * self.get_flux_yield_multiplier())))
        self.state["quantum_flux"] = self.quantum_flux + flux_gain

        token_bounty = flux_gain * 100_000_000_000_000  # 100T per QF (e.g. 50 QF = 5.0Q, 1000 QF = 100.0Q)
        self.companion.state["spent_tokens"] = self.companion.state.get("spent_tokens", 0) - token_bounty

        self.state["active_threat"] = None
        self.companion.save()
        return (
            True,
            f"🏆 THREAT PURGED: {t_name} neutralized! (+{flux_gain:,} QF, +{format_tokens(token_bounty)} tokens, -40% Trace)"
        )

    def combat_flee(self) -> Tuple[bool, str]:
        """Attempts to sever connection and retreat from combat."""
        if not self.active_threat:
            return False, "No active combat encounter to retreat from."
        self.state["active_threat"] = None
        self.add_trace(25)
        self.companion.save()
        return True, "Severed connection from combat arena. Trace heat spiked (+25% Trace)."
