"""Quantum Flux synthesis, Tesseract Overclocking, and Kernel Sector Decryption mixin."""

from typing import Dict, List, Tuple, Optional, Any

from poketokenbar.utils.formatting import format_tokens, parse_tokens
from poketokenbar.game.matrix.models import (
    FLUX_SYNTHESIS_TOKENS_PER_QF,
    FLUX_SYNTHESIS_MIN_TOKENS,
    TESSERACT_OVERCLOCK_TRACKS,
    MEMORY_SECTORS,
)


class MatrixOverclockMixin:
    """Manages the Singularity Flux Collider, infinite Tesseract Overclocking, and Kernel Sectors."""

    @property
    def quantum_flux(self) -> int:
        """Current Quantum Flux (QF) balance."""
        return int(self.state.setdefault("quantum_flux", 0))

    @property
    def decrypted_sectors(self) -> List[int]:
        """List of decrypted Kernel Sector IDs (0-7)."""
        return self.state.setdefault("sectors", [])

    @property
    def overclock_levels(self) -> Dict[str, int]:
        """Current Tesseract Overclock levels for 'ram' and 'amp'."""
        levels = self.state.setdefault("overclock_levels", {"ram": 0, "amp": 0})
        levels.setdefault("ram", 0)
        levels.setdefault("amp", 0)
        return levels

    def get_overclock_level(self, track_id: str) -> int:
        """Returns the current overclock level for a track ('ram' or 'amp')."""
        return int(self.overclock_levels.get(str(track_id).lower().strip(), 0))

    def get_overclock_cost(self, track_id: str) -> Tuple[int, int]:
        """Returns (token_cost, flux_cost) for the next level of a Tesseract Overclock track."""
        track_id = str(track_id).lower().strip()
        spec = TESSERACT_OVERCLOCK_TRACKS.get(track_id)
        if not spec:
            return 0, 0
        next_lvl = self.get_overclock_level(track_id) + 1
        token_cost = int(spec["base_token_cost"] * (2 ** (next_lvl - 1)))
        flux_cost = int(spec["base_flux_cost"] * next_lvl)
        return token_cost, flux_cost

    # -------------------------------------------------------------------------
    # Sector Passive Bonus Helpers
    # -------------------------------------------------------------------------

    def get_sector_base_exaflops_bonus(self) -> float:
        """Returns total flat base Exaflops bonus from decrypted Kernel Sectors (0x00, 0x07)."""
        bonus = 0.0
        for sid in self.decrypted_sectors:
            sec = MEMORY_SECTORS.get(sid)
            if sec and sec.get("buff_key") in ("base_exaflops", "omega_core", "architect_core"):
                bonus += float(sec.get("buff_val", 0.0))
        return bonus

    def get_sector_firewall_bonus(self) -> int:
        """Returns total max Firewall HP bonus from decrypted Kernel Sectors (0x01)."""
        bonus = 0
        for sid in self.decrypted_sectors:
            sec = MEMORY_SECTORS.get(sid)
            if sec and sec.get("buff_key") == "max_firewall":
                bonus += int(sec.get("buff_val", 0))
        return bonus

    def get_sector_exploit_multiplier(self) -> float:
        """Returns multiplicative combat exploit damage multiplier from decrypted Sectors (0x02, 0x05)."""
        bonus = 0.0
        for sid in self.decrypted_sectors:
            sec = MEMORY_SECTORS.get(sid)
            if sec and sec.get("buff_key") in ("exploit_dmg", "exploit_dmg_pct"):
                val = float(sec.get("buff_val", 0.0))
                bonus += (val / 100.0) if val >= 1.0 else val
        return 1.0 + bonus

    def get_sector_trace_resistance(self) -> float:
        """Returns additive trace reduction fraction from decrypted Sectors (0x03)."""
        bonus = 0.0
        for sid in self.decrypted_sectors:
            sec = MEMORY_SECTORS.get(sid)
            if sec and sec.get("buff_key") in ("trace_resist", "trace_resist_pct"):
                val = float(sec.get("buff_val", 0.0))
                bonus += (val / 100.0) if val >= 1.0 else val
        return bonus

    def get_sector_clock_bonus(self) -> float:
        """Returns additive double-tick clock chance from decrypted Sectors (0x06)."""
        bonus = 0.0
        for sid in self.decrypted_sectors:
            sec = MEMORY_SECTORS.get(sid)
            if sec and sec.get("buff_key") in ("clock_chance", "clock_chance_pct"):
                val = float(sec.get("buff_val", 0.0))
                bonus += (val / 100.0) if val >= 1.0 else val
        return bonus

    def get_sector_threads_bonus(self) -> int:
        """Returns bonus execution threads from decrypted Sectors (0x07)."""
        return 1 if 7 in self.decrypted_sectors else 0

    def get_flux_yield_multiplier(self) -> float:
        """Returns Quantum Flux yield multiplier from Sector 0x04 (+15%) and Root Transcendence (+25%)."""
        mult = 1.0
        for sid in self.decrypted_sectors:
            sec = MEMORY_SECTORS.get(sid)
            if sec and sec.get("buff_key") in ("flux_yield", "flux_yield_pct"):
                val = float(sec.get("buff_val", 0.0))
                mult += (val / 100.0) if val >= 1.0 else val
        if self.is_root_transcendence_tweak_active():
            mult += 0.25
        return mult

    def get_flux_synthesis_rate(self) -> float:
        """Returns the effective QF per 1.0Q tokens synthesis rate."""
        return self.get_flux_yield_multiplier()

    # -------------------------------------------------------------------------
    # Singularity Flux Collider & Tesseract Overclocking
    # -------------------------------------------------------------------------

    def synthesize_flux(self, amount_str: str) -> Tuple[bool, str]:
        """Collides spendable tokens (>= 100Q) into Quantum Flux (QF) at 1.0Q Tokens = 1 QF base rate."""
        if not self.is_unlocked:
            return False, "Quantum Singularity Matrix is not initialized! Descend from Luxury Suite."

        clean = str(amount_str).lower().strip()
        avail = self.companion.available_tokens
        if clean in ("all", "max"):
            tokens = (avail // FLUX_SYNTHESIS_TOKENS_PER_QF) * FLUX_SYNTHESIS_TOKENS_PER_QF
        else:
            tokens = parse_tokens(clean)

        if tokens < FLUX_SYNTHESIS_MIN_TOKENS:
            return False, (
                f"Minimum synthesis batch is {format_tokens(FLUX_SYNTHESIS_MIN_TOKENS)} tokens "
                "(e.g. 'synthesize 100q' or 'synthesize 500q')!"
            )

        if avail < tokens:
            return False, (
                f"Not enough spendable tokens! Synthesizing {format_tokens(tokens)} requires "
                f"{format_tokens(tokens)} ({format_tokens(avail)} available)."
            )

        base_qf = tokens // FLUX_SYNTHESIS_TOKENS_PER_QF
        actual_tokens = base_qf * FLUX_SYNTHESIS_TOKENS_PER_QF
        flux_mult = self.get_flux_yield_multiplier()
        qf_gained = max(1, int(round(base_qf * flux_mult)))

        self.companion.state["spent_tokens"] = self.companion.state.get("spent_tokens", 0) + actual_tokens
        self.state["total_tokens_consumed"] = self.state.get("total_tokens_consumed", 0) + actual_tokens
        self.state["quantum_flux"] = self.quantum_flux + qf_gained
        self.companion.save()

        bonus_tag = f" ({flux_mult:.2f}x Yield)" if flux_mult > 1.0 else ""
        return (
            True,
            f"⚛️ FLUX SYNTHESIZED! Collided {format_tokens(actual_tokens)} tokens -> +{qf_gained:,} QF{bonus_tag}! "
            f"(Total: {self.quantum_flux:,} QF)"
        )

    def overclock_deck(self, track_id: str) -> Tuple[bool, str]:
        """Overclocks a Tesseract track ('ram' or 'amp') using spendable tokens and Quantum Flux."""
        if not self.is_unlocked:
            return False, "Quantum Singularity Matrix is not initialized! Descend from Luxury Suite."

        if 5 not in self.ram_blocks:
            return False, "Prerequisite missing! Allocate Q-RAM Block 0x05 [Tesseract Block] before overclocking."

        track_id = str(track_id).lower().strip()
        if track_id not in TESSERACT_OVERCLOCK_TRACKS:
            return False, "Unknown overclock track! Use 'overclock ram' or 'overclock amp'."

        spec = TESSERACT_OVERCLOCK_TRACKS[track_id]
        curr_lvl = self.get_overclock_level(track_id)
        next_lvl = curr_lvl + 1
        token_cost, flux_cost = self.get_overclock_cost(track_id)

        avail_tokens = self.companion.available_tokens
        if avail_tokens < token_cost:
            return False, (
                f"Not enough spendable tokens! {spec['name']} Lv {next_lvl} requires "
                f"{format_tokens(token_cost)} tokens + {flux_cost:,} QF."
            )

        if self.quantum_flux < flux_cost:
            return False, (
                f"Insufficient Quantum Flux! {spec['name']} Lv {next_lvl} requires "
                f"{flux_cost:,} QF ({self.quantum_flux:,} QF available). Use 'synthesize <amount>'."
            )

        self.companion.state["spent_tokens"] = self.companion.state.get("spent_tokens", 0) + token_cost
        self.state["total_tokens_consumed"] = self.state.get("total_tokens_consumed", 0) + token_cost
        self.state["quantum_flux"] = self.quantum_flux - flux_cost
        self.overclock_levels[track_id] = next_lvl
        self.companion.save()

        return (
            True,
            f"⚡ TESSERACT OVERCLOCKED! {spec['name']} advanced to Lv {next_lvl} ({spec['desc']})! "
            f"(-{format_tokens(token_cost)} tokens, -{flux_cost:,} QF)"
        )

    # -------------------------------------------------------------------------
    # Kernel Lore Sector Decryption (0x00 - 0x07)
    # -------------------------------------------------------------------------

    @staticmethod
    def resolve_sector_id(sector_arg: Any) -> Optional[int]:
        """Resolves a sector argument ('0', '0x00', 0, etc.) to a valid sector index 0-7."""
        if isinstance(sector_arg, int) and sector_arg in MEMORY_SECTORS:
            return sector_arg
        clean = str(sector_arg).lower().strip()
        if clean.startswith("0x0") and len(clean) == 4 and clean[3].isdigit():
            idx = int(clean[3])
            if idx in MEMORY_SECTORS:
                return idx
        if clean.startswith("0x") and clean[2:].isdigit():
            idx = int(clean[2:])
            if idx in MEMORY_SECTORS:
                return idx
        if clean.isdigit():
            idx = int(clean)
            if idx in MEMORY_SECTORS:
                return idx
        for sid, sec in MEMORY_SECTORS.items():
            if clean == sec.get("code", "").lower() or clean == sec["title"].lower():
                return sid
        return None

    def decrypt_sector(self, sector_arg: Any) -> Tuple[bool, str]:
        """Decrypts a Kernel Lore Sector (0x00-0x07) using spendable tokens and Quantum Flux."""
        if not self.is_unlocked:
            return False, "Quantum Singularity Matrix is not initialized! Descend from Luxury Suite."

        sector_id = self.resolve_sector_id(sector_arg)
        if sector_id is None:
            return False, f"Unknown Kernel Sector '{sector_arg}'! Valid sectors: 0x00 to 0x07."

        sec = MEMORY_SECTORS[sector_id]
        code = sec.get("code", f"0x0{sector_id}")
        if sector_id in self.decrypted_sectors:
            return False, f"Sector {code} [{sec['title']}] is already decrypted! ({sec['buff_desc']})"

        token_cost = int(sec["cost"])
        flux_cost = int(sec.get("flux_cost", 250))

        avail_tokens = self.companion.available_tokens
        if avail_tokens < token_cost:
            return False, (
                f"Not enough spendable tokens! Decrypting Sector {code} requires "
                f"{format_tokens(token_cost)} tokens + {flux_cost:,} QF."
            )

        if self.quantum_flux < flux_cost:
            return False, (
                f"Insufficient Quantum Flux! Decrypting Sector {code} requires "
                f"{flux_cost:,} QF ({self.quantum_flux:,} QF available). Use 'synthesize <amount>'."
            )

        self.companion.state["spent_tokens"] = self.companion.state.get("spent_tokens", 0) + token_cost
        self.state["total_tokens_consumed"] = self.state.get("total_tokens_consumed", 0) + token_cost
        self.state["quantum_flux"] = self.quantum_flux - flux_cost
        self.decrypted_sectors.append(sector_id)

        if sec.get("buff_key") == "max_firewall":
            hw = self.deck_hardware
            hw["firewall"] = min(hw["max_firewall"], hw["firewall"] + int(sec["buff_val"]))

        self.companion.save()
        return (
            True,
            f"🔓 SECTOR {code} DECRYPTED: [{sec['title']}]! Passive: {sec['buff_desc']} "
            f"(-{format_tokens(token_cost)} tokens, -{flux_cost:,} QF)"
        )

    def probe_sector(self, sector_id: int) -> Tuple[bool, str]:
        """Legacy sector probing method preserved for backward compatibility."""
        if sector_id not in MEMORY_SECTORS:
            return False, f"Invalid sector index #{sector_id}."
        if sector_id in self.decrypted_sectors:
            return True, f"Sector 0x0{sector_id} already decrypted."
        self.decrypted_sectors.append(sector_id)
        self.companion.save()
        return True, f"Sector 0x0{sector_id} decrypted."
