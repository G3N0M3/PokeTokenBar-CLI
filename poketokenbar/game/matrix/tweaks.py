"""Upper Reality Tweaker mixin for modifying PokeTokenBar's simulation rules."""

from typing import Tuple, Optional, Any

from poketokenbar.game.matrix.models import MEMORY_NODES


class MatrixTweaksMixin:
    """Manages active reality tweaks, Exaflop allocation costs, and upper-world hooks."""

    def is_root_transcendence_tweak_active(self) -> bool:
        """Returns True if the Root Transcendence tweak (0x00_ROOT_SUPERVISOR) is currently active."""
        if not self.is_unlocked:
            return False
        return self.active_tweaks.get("root", {}).get("transcendence") == "active"

    def get_tweak_exaflop_cost(self, node_id: str, tweak_id: str, option_key: str) -> float:
        """Returns the effective Exaflop cost of a tweak option, factoring in Root Transcendence (-50% EF)."""
        node_spec = MEMORY_NODES.get(node_id, {}).get("tweaks", {}).get(tweak_id)
        if not node_spec or option_key not in node_spec.get("options", {}):
            return 0.0
        base_cost = float(node_spec["options"][option_key]["cost_exaflops"])
        if node_id != "root" and self.is_root_transcendence_tweak_active():
            return base_cost * 0.5
        return base_cost

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

        if option_key in ("off", "none", "disable"):
            return self.remove_tweak(node_id, tweak_id)

        if node_id not in MEMORY_NODES:
            return False, f"Unknown memory node '{node_id}'! Available: {', '.join(MEMORY_NODES.keys())}"

        if node_id == "root" and not self.is_root_transcended:
            return False, "Node '0x00_ROOT_SUPERVISOR' is locked! Authorize Root Transcendence ('execute root') first."

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
        needed_flops = self.get_tweak_exaflop_cost(node_id, tweak_id, option_key)

        # Check existing allocation for this tweak to calculate delta
        curr_active_node = self.active_tweaks.get(node_id, {})
        old_key = curr_active_node.get(tweak_id)
        old_flops = 0.0
        if old_key and old_key in tweak_spec["options"]:
            old_flops = self.get_tweak_exaflop_cost(node_id, tweak_id, old_key)

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

        # Raise trace heat (+15%), unless Root Transcendence suppresses passive trace
        if not self.is_root_transcendence_tweak_active():
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
        """Retrieves active value of a tweak for upper game hooks, scaled by Reality Gain Amp if overclocked."""
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
        if not opt:
            return None

        val = opt.get("val")
        if val is None or isinstance(val, bool):
            return val

        if isinstance(val, (int, float)):
            amp_lvl = self.get_overclock_level("amp")
            if amp_lvl > 0:
                amp_mult = 1.0 + (0.10 * amp_lvl)
                if tweak_id == "smuggler_discount":
                    return max(0.05, round(float(val) / amp_mult, 4))
                scaled = round(float(val) * amp_mult, 4)
                if isinstance(val, int) and scaled.is_integer():
                    return int(scaled)
                return scaled
        return val

    def is_tweak_active(self, node_id: str, tweak_id: str) -> bool:
        return self.get_tweak_val(node_id, tweak_id) is not None

    def get_combat_damage_multiplier(self) -> float:
        """Returns active combat overdrive damage multiplier (default 1.0)."""
        val = self.get_tweak_val("combat", "overdrive")
        return float(val) if val else 1.0

    def is_instant_squad_active(self) -> bool:
        """Returns True if combat.instant_squad is active."""
        return bool(self.get_tweak_val("combat", "instant_squad"))

    def get_casino_luck_multiplier(self) -> float:
        """Returns active casino luck bias multiplier (default 1.0)."""
        val = self.get_tweak_val("casino", "luck_bias")
        return float(val) if val else 1.0

    def is_infinite_vip_active(self) -> bool:
        """Returns True if casino.infinite_vip is active."""
        return bool(self.get_tweak_val("casino", "infinite_vip"))

    def get_armory_charge_multiplier(self) -> float:
        """Returns active syndicate armory charge multiplier (default 1.0)."""
        val = self.get_tweak_val("syndicate", "armory_charge")
        return float(val) if val else 1.0

    def get_smuggler_price_multiplier(self) -> Optional[float]:
        """Returns active syndicate smuggler price multiplier (e.g. 0.5 or 0.2), or None if inactive."""
        val = self.get_tweak_val("syndicate", "smuggler_discount")
        return float(val) if val is not None else None

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
