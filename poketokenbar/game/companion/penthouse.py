"""Resort Area Executive Penthouse engine mixin and progression hooks."""

from typing import Tuple, List, Optional, Any, Dict
from poketokenbar.utils.formatting import format_tokens
from poketokenbar.game.models import (
    PENTHOUSE_WEALTH_THRESHOLD,
    PENTHOUSE_VIP_FEE,
    PENTHOUSE_DEED_COST,
    PENTHOUSE_FACILITIES,
    PENTHOUSE_DECOR,
    CORPORATIONS,
)
from poketokenbar.game.economy.stock_market import StockMarketEngine, BASE_PRICES, PATTERN_BULL_RALLY


class PenthouseMixin:
    """Provides Resort Area Executive Penthouse state management, upgrades, and hooks."""

    def get_penthouse_state(self) -> Dict[str, Any]:
        # Migrate legacy 'villa' key if present
        if "villa" in self.state and "penthouse" not in self.state:
            self.state["penthouse"] = self.state.pop("villa")

        p = self.state.setdefault("penthouse", {})
        p.setdefault("invitation_sent", False)
        p.setdefault("invitation_pending", False)
        p.setdefault("vip_fee_paid", False)
        p.setdefault("unlocked", False)
        p.setdefault("facilities", {
            "nursery": 0,
            "springs": 0,
            "trading_desk": 0,
            "chromatic_lab": 0
        })
        p.setdefault("decor", [])
        p.setdefault("last_shiny_transmute", None)

        # Legacy fallback if deed was already bought
        if p.get("unlocked"):
            p["vip_fee_paid"] = True
            p["invitation_sent"] = True

        return p

    def get_villa_state(self) -> Dict[str, Any]:
        """Backward-compatible alias for get_penthouse_state."""
        return self.get_penthouse_state()

    def is_penthouse_available(self) -> bool:
        """Checks if player meets the 100B wealth requirement or has received the invitation."""
        st = self.get_penthouse_state()
        if st.get("invitation_sent", False) or st.get("vip_fee_paid", False) or st.get("unlocked", False):
            return True
        total_wealth = self.available_tokens + self.state.get("bank_balance", 0)
        return total_wealth >= PENTHOUSE_WEALTH_THRESHOLD

    def is_penthouse_invitation_pending(self) -> bool:
        """Returns True if the luxury invitation modal should be presented."""
        return self.get_penthouse_state().get("invitation_pending", False)

    def is_penthouse_vip_paid(self) -> bool:
        """Returns True if the 500M VIP concierge clearance fee has been paid."""
        st = self.get_penthouse_state()
        return bool(st.get("vip_fee_paid", False) or st.get("unlocked", False))

    def is_penthouse_unlocked(self) -> bool:
        """Returns True if the Penthouse deed has been acquired."""
        return bool(self.get_penthouse_state().get("unlocked", False))

    def is_villa_unlocked(self) -> bool:
        """Backward-compatible alias for is_penthouse_unlocked."""
        return self.is_penthouse_unlocked()

    def get_penthouse_facility_level(self, facility_key_or_idx: Any) -> int:
        st = self.get_penthouse_state()
        facs = st.setdefault("facilities", {})
        fac_keys = list(PENTHOUSE_FACILITIES.keys())
        try:
            idx = int(facility_key_or_idx) - 1
            if 0 <= idx < len(fac_keys):
                f_key = fac_keys[idx]
            else:
                return 0
        except (ValueError, TypeError):
            f_key = str(facility_key_or_idx).lower().strip()
        return facs.get(f_key, 0)

    def get_villa_facility_level(self, facility_key_or_idx: Any) -> int:
        """Backward-compatible alias for get_penthouse_facility_level."""
        return self.get_penthouse_facility_level(facility_key_or_idx)

    def get_penthouse_wing_level(self, wing_key_or_idx: Any) -> int:
        """Alias for get_penthouse_facility_level."""
        return self.get_penthouse_facility_level(wing_key_or_idx)

    def get_penthouse_total_value(self) -> int:
        st = self.get_penthouse_state()
        total = 0
        if st.get("vip_fee_paid"):
            total += PENTHOUSE_VIP_FEE
        if st.get("unlocked"):
            total += PENTHOUSE_DEED_COST

        facs = st.get("facilities", {})
        for f_key, lvl in facs.items():
            if f_key in PENTHOUSE_FACILITIES:
                levels = PENTHOUSE_FACILITIES[f_key]["levels"]
                for l in range(1, lvl + 1):
                    total += levels.get(l, {}).get("cost", 0)

        for d_key in st.get("decor", []):
            if d_key in PENTHOUSE_DECOR:
                total += PENTHOUSE_DECOR[d_key]["cost"]

        return total

    def get_villa_total_value(self) -> int:
        """Backward-compatible alias for get_penthouse_total_value."""
        return self.get_penthouse_total_value()

    def check_penthouse_invitation(self) -> Tuple[bool, Optional[str]]:
        """Checks if total wealth (bank + holding tokens) exceeds 100B to dispatch the invitation."""
        st = self.get_penthouse_state()
        if st.get("invitation_sent"):
            return False, None

        total_wealth = self.available_tokens + self.state.get("bank_balance", 0)
        if total_wealth >= PENTHOUSE_WEALTH_THRESHOLD:
            st["invitation_sent"] = True
            st["invitation_pending"] = True
            self.save()
            return True, "⚜️ An ornate, wax-sealed gold envelope has arrived for you! (Resort Area Penthouse Invitation)"
        return False, None

    def pay_penthouse_vip_fee(self) -> Tuple[bool, str]:
        """Pays the 500M token fee to the Ribbon Syndicate concierge to view/buy the Penthouse."""
        st = self.get_penthouse_state()
        if self.is_penthouse_vip_paid():
            return False, "VIP broker clearance has already been granted!"

        avail = self.available_tokens
        if avail < PENTHOUSE_VIP_FEE:
            return False, f"Not enough spendable tokens! VIP Concierge fee requires {format_tokens(PENTHOUSE_VIP_FEE)} tokens."

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + PENTHOUSE_VIP_FEE
        st["vip_fee_paid"] = True
        st["invitation_pending"] = False
        self.save()
        return True, f"⚜️ VIP CLEARANCE GRANTED! Paid {format_tokens(PENTHOUSE_VIP_FEE)} tokens to Madame Vivienne. You may now inspect the deed and purchase the Penthouse!"

    def postpone_penthouse_invitation(self) -> Tuple[bool, str]:
        """Dismisses the active modal invitation to be reviewed later."""
        st = self.get_penthouse_state()
        st["invitation_pending"] = False
        self.save()
        return True, "Penthouse invitation postponed. You can review it anytime in Bank Tab [10]."

    def purchase_penthouse_deed(self) -> Tuple[bool, str]:
        """Acquires the Executive Penthouse Deed for 1.0T tokens."""
        if not self.is_penthouse_vip_paid():
            return False, f"You must pay the {format_tokens(PENTHOUSE_VIP_FEE)} VIP Concierge fee to gain clearance before purchasing the Penthouse deed!"

        if self.is_penthouse_unlocked():
            return False, "You already own the Resort Area Executive Penthouse!"

        avail = self.available_tokens
        if avail < PENTHOUSE_DEED_COST:
            return False, f"Not enough tokens! The Penthouse Deed costs {format_tokens(PENTHOUSE_DEED_COST)} tokens."

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + PENTHOUSE_DEED_COST
        st = self.get_penthouse_state()
        st["unlocked"] = True
        self.save()
        return True, "🏰 CONGRATULATIONS! You acquired the Resort Area Executive Penthouse Deed! All 4 luxury wings are now unlocked."

    def purchase_villa_deed(self) -> Tuple[bool, str]:
        """Backward-compatible alias for purchase_penthouse_deed."""
        return self.purchase_penthouse_deed()

    def upgrade_penthouse_facility(self, facility_key_or_idx: Any) -> Tuple[bool, str]:
        if not self.is_penthouse_unlocked():
            return False, "You must acquire the Executive Penthouse deed first! Type 'acquire'."

        fac_keys = list(PENTHOUSE_FACILITIES.keys())
        try:
            idx = int(facility_key_or_idx) - 1
            if 0 <= idx < len(fac_keys):
                f_key = fac_keys[idx]
            else:
                return False, f"Invalid facility index #{facility_key_or_idx}! (Valid: 1 to {len(fac_keys)})"
        except (ValueError, TypeError):
            f_key = str(facility_key_or_idx).lower().strip()
            if f_key not in PENTHOUSE_FACILITIES:
                return False, f"Unknown facility '{facility_key_or_idx}'!"

        fac_info = PENTHOUSE_FACILITIES[f_key]
        st = self.get_penthouse_state()
        facs = st.setdefault("facilities", {})
        cur_lvl = facs.get(f_key, 0)
        max_lvl = len(fac_info["levels"])

        if cur_lvl >= max_lvl:
            return False, f"{fac_info['name']} is already at maximum level (Lv {max_lvl})!"

        next_lvl = cur_lvl + 1
        cost = fac_info["levels"][next_lvl]["cost"]
        avail = self.available_tokens
        if avail < cost:
            return False, f"Not enough tokens! Upgrading {fac_info['name']} to Lv {next_lvl} costs {format_tokens(cost)} tokens."

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
        facs[f_key] = next_lvl
        self.save()

        lvl_name = fac_info["levels"][next_lvl]["name"]
        return True, f"✨ UPGRADED {fac_info['name']} to Lv {next_lvl} ({lvl_name})! Spent {format_tokens(cost)} tokens."

    def upgrade_villa_facility(self, facility_key_or_idx: Any) -> Tuple[bool, str]:
        """Backward-compatible alias for upgrade_penthouse_facility."""
        return self.upgrade_penthouse_facility(facility_key_or_idx)

    def upgrade_penthouse_wing(self, wing_key_or_idx: Any) -> Tuple[bool, str]:
        """Alias for upgrade_penthouse_facility."""
        return self.upgrade_penthouse_facility(wing_key_or_idx)

    def purchase_penthouse_decor(self, decor_key_or_idx: Any) -> Tuple[bool, str]:
        if not self.is_penthouse_unlocked():
            return False, "You must acquire the Executive Penthouse deed first! Type 'acquire'."

        decor_keys = list(PENTHOUSE_DECOR.keys())
        try:
            idx = int(decor_key_or_idx) - 1
            if 0 <= idx < len(decor_keys):
                d_key = decor_keys[idx]
            else:
                return False, f"Invalid decor index #{decor_key_or_idx}! (Valid: 1 to {len(decor_keys)})"
        except (ValueError, TypeError):
            d_key = str(decor_key_or_idx).lower().strip()
            if d_key not in PENTHOUSE_DECOR:
                return False, f"Unknown decor item '{decor_key_or_idx}'!"

        decor_info = PENTHOUSE_DECOR[d_key]
        st = self.get_penthouse_state()
        owned_decor = st.setdefault("decor", [])
        if d_key in owned_decor:
            return False, f"{decor_info['name']} is already installed in your Penthouse!"

        cost = decor_info["cost"]
        avail = self.available_tokens
        if avail < cost:
            return False, f"Not enough tokens! {decor_info['name']} costs {format_tokens(cost)} tokens."

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
        owned_decor.append(d_key)

        title_msg = ""
        if len(owned_decor) == len(PENTHOUSE_DECOR):
            badges = self.state.setdefault("gym_badges", [])
            title = "👑 Sovereign Tycoon"
            if title not in badges:
                badges.append(title)
                title_msg = f" 🏆 Title unlocked: '{title}'!"

        self.save()
        return True, f"🛋️ Installed {decor_info['name']}! ({format_tokens(cost)} tokens).{title_msg}"

    def purchase_villa_decor(self, decor_key_or_idx: Any) -> Tuple[bool, str]:
        """Backward-compatible alias for purchase_penthouse_decor."""
        return self.purchase_penthouse_decor(decor_key_or_idx)

    def has_penthouse_decor(self, decor_key: str) -> bool:
        """Returns True if the specified decor item is installed in the Penthouse."""
        return decor_key in self.get_penthouse_state().get("decor", [])

    def has_villa_decor(self, decor_key: str) -> bool:
        """Backward-compatible alias for has_penthouse_decor."""
        return self.has_penthouse_decor(decor_key)

    def interact_penthouse_decor(self, decor_key_or_idx: Any) -> Tuple[bool, str]:
        """Interacts with an installed luxury furnishing in the Penthouse."""
        if not self.is_penthouse_unlocked():
            return False, "You must acquire the Executive Penthouse deed first!"

        decor_keys = list(PENTHOUSE_DECOR.keys())
        try:
            idx = int(decor_key_or_idx) - 1
            if 0 <= idx < len(decor_keys):
                d_key = decor_keys[idx]
            else:
                return False, f"Invalid decor index #{decor_key_or_idx}! (Valid: 1 to {len(decor_keys)})"
        except (ValueError, TypeError):
            d_key = str(decor_key_or_idx).lower().strip()
            if d_key not in PENTHOUSE_DECOR:
                return False, f"Unknown decor item '{decor_key_or_idx}'!"

        if not self.has_penthouse_decor(d_key):
            d_info = PENTHOUSE_DECOR[d_key]
            return False, f"You haven't installed {d_info['name']} yet! Use 'furnish <idx>' to purchase."

        if d_key == "piano":
            active = self.active_mon
            if active:
                active.happiness = min(100, active.happiness + 10)
                self.set_active_mon(active)
                self.save()
                return True, "🎹 You play a soothing sonata on the Grand Piano (+10 Happiness)!"
            return True, "🎹 You play a brilliant classical piece on the Grand Concert Piano!"

        elif d_key == "chandelier":
            return True, "💎 Diamond Chandelier sparkles with brilliance (+5% expedition tokens)!"

        elif d_key == "statue":
            return True, "🗽 The Golden Arceus Statue radiates divine power (+10% raid tokens)!"

        elif d_key == "hologram":
            return True, "🔮 Master Core Hologram projects Mon-Omega matrix (+5% casino bonus)!"

        elif d_key == "fountain":
            active = self.active_mon
            if active:
                active.happiness = 100
                self.set_active_mon(active)
                self.save()
                return True, "⛲ Your companion bathes in Prism Spring Fountain! Happiness is 100%!"
            return True, "⛲ The Prism Spring Fountain murmurs gently with pure mineral waters."

        elif d_key == "throne":
            return True, "👑 You recline on the Sovereign Tycoon Throne (+10% stock dividends)!"

        return False, "Nothing happened."

    def interact_villa_decor(self, decor_key_or_idx: Any) -> Tuple[bool, str]:
        """Backward-compatible alias for interact_penthouse_decor."""
        return self.interact_penthouse_decor(decor_key_or_idx)

    def transmute_penthouse_shiny(self, target_idx: int) -> Tuple[bool, str]:
        if self.get_penthouse_facility_level("chromatic_lab") < 1:
            return False, "Chromatic Resonator is not built! Construct it in the Executive Penthouse."

        dex = self.state.get("dex", [])
        roster = [d for d in dex if d.get("status") != "evolved"]
        if not roster:
            return False, "Your Roster is currently empty!"
        if target_idx < 1 or target_idx > len(roster):
            return False, f"Invalid index #{target_idx}! Must be between 1 and {len(roster)}."

        entry = roster[target_idx - 1]
        sp_id = entry.get("species_id", entry.get("base_id"))
        species_name = self.api.get_species_name(sp_id)
        if entry.get("is_shiny", False):
            return False, f"{species_name} (#{sp_id}) is already Shiny!"

        entry["is_shiny"] = True
        if isinstance(entry.get("mon_state"), dict):
            entry["mon_state"]["is_shiny"] = True
        if self.active_mon and self.active_mon.current_id == sp_id:
            self.active_mon.is_shiny = True
            self.set_active_mon(self.active_mon)
        self.save()
        return True, f"✨ CHROMATIC TRANSMUTATION! {species_name} (#{sp_id}) is now a brilliant SHINY Pokémon!"

    def transmute_villa_shiny(self, target_idx: int) -> Tuple[bool, str]:
        """Backward-compatible alias for transmute_penthouse_shiny."""
        return self.transmute_penthouse_shiny(target_idx)

    def trigger_penthouse_catalyst(self, corp_key: str) -> Tuple[bool, str]:
        key = self._resolve_corp_key(corp_key)
        if not key or key not in BASE_PRICES:
            return False, f"Unknown corporation '{corp_key}'!"
        if self.get_penthouse_facility_level("trading_desk") < 3:
            return False, "Quantum Trading Terminal Lv 3 required to trigger market catalysts!"

        cost = 1_000_000_000_000
        avail = self.available_tokens
        if avail < cost:
            return False, f"Not enough tokens! Whale Catalyst costs {format_tokens(cost)} tokens."

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
        sm = self.get_or_init_stock_market()
        st = sm.setdefault("market_state", {}).setdefault(key, {})
        phases = StockMarketEngine.get_pattern_phases(key, PATTERN_BULL_RALLY)
        st["pattern"] = PATTERN_BULL_RALLY
        st["phase"] = 0
        st["duration"] = len(phases)
        st["next_bias"] = phases[0][0]
        st["next_hint"] = phases[0][1]
        sm.setdefault("latest_news", {})[key] = phases[0][1]
        self.save()
        corp_name = CORPORATIONS[key].name
        return True, f"🚀 WHALE CATALYST DEPLOYED! 1.0T tokens pumped into {corp_name}! Bull Rally initiated!"

    def trigger_villa_catalyst(self, corp_key: str) -> Tuple[bool, str]:
        """Backward-compatible alias for trigger_penthouse_catalyst."""
        return self.trigger_penthouse_catalyst(corp_key)

    def _process_penthouse_cryo_nursery(self, delta: int, level: int, events: List[str]):
        pending = self.state.get("pending_eggs", [])
        if not pending or level < 1:
            return

        count = 1 if level == 1 else (3 if level == 2 else len(pending))
        eff_delta = delta * 2 if level >= 3 else delta

        hatched_indices = []
        for i in range(min(count, len(pending))):
            egg = pending[i]
            tier = egg.get("tier", "common")
            prog = egg.get("progress", 0) + eff_delta
            egg["progress"] = prog
            threshold = self.get_egg_hatch_threshold(tier)
            if prog >= threshold:
                hatched_indices.append((i, tier, prog - threshold))

        for i, tier, overflow in reversed(hatched_indices):
            pending.pop(i)
            mon, hatch_events = self.hatch_egg(
                initial_xp=overflow,
                force_tier=tier,
                preserve_active=True
            )
            events.extend(hatch_events)
            if mon:
                evo_events = self._check_growth(mon, is_active=False)
                events.extend(evo_events)

    def _process_villa_cryo_nursery(self, delta: int, level: int, events: List[str]):
        """Backward-compatible alias for _process_penthouse_cryo_nursery."""
        return self._process_penthouse_cryo_nursery(delta, level, events)


# Backward-compatible alias
VillaMixin = PenthouseMixin
