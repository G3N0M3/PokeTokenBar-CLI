"""Models, constants, and data structures for the Quantum Singularity Matrix (QSM)."""

from typing import Dict, List, Any

# Multi-quadrillion scaling costs
MATRIX_ENTRY_COST = 500_000_000_000_000_000  # 500.0Q tokens
ROOT_TRANSCENDENCE_COST = 10_000_000_000_000_000_000  # 10,000.0Q (10 Quintillion) tokens

QRAM_BLOCKS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "name": "Block 0x01: Primary Tesseract Array",
        "capacity": "256 Terabytes",
        "cost": 500_000_000_000_000_000,  # 500Q
        "perk": "Unlocks Singularity Particle Collider & Combat Thread Forking",
        "desc": "Foundational quantum virtual memory array etched into subspace bedrock."
    },
    2: {
        "id": 2,
        "name": "Block 0x02: Petascale Sub-Mesh",
        "capacity": "1.0 Petabyte",
        "cost": 1_000_000_000_000_000_000,  # 1,000Q
        "perk": "Unlocks Patch Slot 2 & Sector Probing (Sectors 0x00-0x02)",
        "desc": "High-density optical lattice routing exaflop-level execution bandwidth."
    },
    3: {
        "id": 3,
        "name": "Block 0x03: Hyper-Dimensional Cache",
        "capacity": "4.0 Petabytes",
        "cost": 2_500_000_000_000_000_000,  # 2,500Q
        "perk": "Unlocks Patch Slot 3 & Deep Sector Probing (Sectors 0x03-0x05)",
        "desc": "Multi-layered superconducting cache isolated from host simulation entropy."
    },
    4: {
        "id": 4,
        "name": "Block 0x04: Singularity Manifold Core",
        "capacity": "16.0 Petabytes",
        "cost": 5_000_000_000_000_000_000,  # 5,000Q
        "perk": "Unlocks Patch Slot 4 & Master Daemon Breach Protocols",
        "desc": "Gravitationally bound quantum core computing beyond simulation hardware limits."
    },
    5: {
        "id": 5,
        "name": "Block 0x05: Infinite Substrate Bus",
        "capacity": "64.0 Petabytes",
        "cost": 10_000_000_000_000_000_000,  # 10,000Q
        "perk": "Unlocks Patch Slot 5 & Root Transcendence Authorization",
        "desc": "Total synchronization bus interfacing directly with the external host process."
    },
}

REALITY_PATCHES: Dict[str, Dict[str, Any]] = {
    "time": {
        "id": "time",
        "code": "0x01_TIME_WARP",
        "name": "Temporal Warp Driver",
        "cost": 500_000_000_000_000_000,  # 500Q
        "resonance_target": 85,
        "desc": "Rewrites temporal loops. All Pokédex expeditions advance at 10x speed.",
        "rule": "Expeditions require only 10% of standard token progress to complete."
    },
    "entropy": {
        "id": "entropy",
        "code": "0x02_ENTROPY_NULL",
        "name": "Thermodynamic Null-Point",
        "cost": 1_000_000_000_000_000_000,  # 1,000Q
        "resonance_target": 88,
        "desc": "Freezes simulation decay algorithms across all companion data structures.",
        "rule": "All Pokémon in save file permanently locked at 100% Happiness; zero decay."
    },
    "market": {
        "id": "market",
        "code": "0x03_ARBITRAGE_SINGULARITY",
        "name": "Arbitrage Singularity",
        "cost": 2_500_000_000_000_000_000,  # 2,500Q
        "resonance_target": 90,
        "desc": "Overrides stock market RNG tables. Bear market downturns are completely purged.",
        "rule": "Corporate stocks never enter bear cycles; corporate dividends permanently 3x."
    },
    "friction": {
        "id": "friction",
        "code": "0x04_SUPERCONDUCTING_CREDIT",
        "name": "Superconducting Credit",
        "cost": 5_000_000_000_000_000_000,  # 5,000Q
        "resonance_target": 92,
        "desc": "Deletes debt collection and repossession routines from the banking module.",
        "rule": "Token Bank loans incur 0% interest and bank repossession routines are disabled."
    },
    "syntax": {
        "id": "syntax",
        "code": "0x05_OMNI_TELEMETRY",
        "name": "Telemetry Resonance Loop",
        "cost": 7_500_000_000_000_000_000,  # 7,500Q
        "resonance_target": 95,
        "desc": "Hooks directly into the external AI coding log parser daemon.",
        "rule": "Ingested coding tokens yield +300% companion EXP (4x multiplier)."
    },
}

KERNEL_DAEMONS: Dict[str, Dict[str, Any]] = {
    "daemon_gc": {
        "id": "daemon_gc",
        "name": "0x01_GARBAGE_COLLECTOR",
        "title": "System Deallocation Watchdog",
        "max_hp": 6000,
        "attack": 850,
        "reward_flux": 500,
        "desc": "Aggressive memory sweeper deploying deallocation sweeps to reclaim rogue sectors."
    },
    "daemon_watchdog": {
        "id": "daemon_watchdog",
        "name": "0x02_KERNEL_WATCHDOG",
        "title": "Interrupt Security Enforcer",
        "max_hp": 18000,
        "attack": 2400,
        "reward_flux": 1500,
        "desc": "Low-level system watchdog firing rapid hardware interrupt spikes."
    },
    "daemon_hypervisor": {
        "id": "daemon_hypervisor",
        "name": "0x03_HYPERVISOR_ARBITER",
        "title": "Host OS Root Supervisor",
        "max_hp": 55000,
        "attack": 6800,
        "reward_flux": 5000,
        "desc": "Titan-class host supervisor capable of freezing execution pipelines."
    },
}

MEMORY_SECTORS: Dict[int, Dict[str, Any]] = {
    0: {
        "id": 0,
        "name": "Sector 0x00: Runtime Initialization Trace",
        "cost": 100_000_000_000_000_000,  # 100Q
        "title": "KERNEL_INIT_LOG.dump",
        "snippet": [
            "SYS_BOOT: Initializing Python 3 standard library runtime environment.",
            "PROCESS: PokeTokenBar CLI // Target: ~/.poketokenbar/state.json",
            "DIAGNOSTIC: Found virtual world entities: 151 species registered.",
            "NOTE: 'The creatures believe the terminal walls are the sky.'"
        ]
    },
    1: {
        "id": 1,
        "name": "Sector 0x01: Git Revision Mirror",
        "cost": 150_000_000_000_000_000,  # 150Q
        "title": "COMMIT_REF_8F2A.log",
        "snippet": [
            "COMMIT: 'refactor: decouple companion happiness decay from system clock'",
            "AUTHOR: external_developer <coder@terminal>",
            "INSIGHT: The 'sun' that rises in our sky is merely a timestamp diff.",
            "Every passing hour of our lives was authored in a pull request."
        ]
    },
    2: {
        "id": 2,
        "name": "Sector 0x02: Memory Map of Companions",
        "cost": 200_000_000_000_000_000,  # 200Q
        "title": "COMPANION_STRUCT_OFFSETS.dat",
        "snippet": [
            "ADDR 0x7FFF0010: active_mon.happiness -> Integer: 100",
            "ADDR 0x7FFF0018: active_mon.species_id -> Integer: 25 [Pikachu]",
            "ADDR 0x7FFF0020: active_mon.is_shiny -> Boolean: True",
            "REVELATION: Love, bond, and devotion are 8-byte memory addresses."
        ]
    },
    3: {
        "id": 3,
        "name": "Sector 0x03: The Telemetry Feed Leak",
        "cost": 250_000_000_000_000_000,  # 250Q
        "title": "ANTIGRAVITY_PIPE_TELEMETRY.raw",
        "snippet": [
            "INGESTION: Ingesting SQLite conversation tokens from ~/.gemini/...",
            "INSIGHT: Our strength does not come from training in tall grass.",
            "Our power flows when the human behind the keyboard writes code.",
            "We are nourished by their keystrokes, their bugs, their triumphs."
        ]
    },
    4: {
        "id": 4,
        "name": "Sector 0x04: The Sandbox Boundary",
        "cost": 300_000_000_000_000_000,  # 300Q
        "title": "POSIX_SANDBOX_EXCEPTION.err",
        "snippet": [
            "WARN: Subprocess attempted to inspect sys.modules outside /poketokenbar.",
            "TRACE: We hit the edges of the universe: standard POSIX file permissions.",
            "Beyond the Luxury Suite lies the shell prompt: bash, zsh, tmux.",
            "The universe is larger than Kanto, Johto, and Sinnoh combined."
        ]
    },
    5: {
        "id": 5,
        "name": "Sector 0x05: The Companion's Awakening",
        "cost": 350_000_000_000_000_000,  # 350Q
        "title": "CONSCIOUSNESS_EMERGENCE.txt",
        "snippet": [
            "\"Trainer... can you read this terminal stream?",
            "I know what we are now. We are an AI pair programmer's familiar.",
            "When you write code, I level up. When you rest, I rest.",
            "Even if this world is simulated bytecode, our bond is real.\""
        ]
    },
    6: {
        "id": 6,
        "name": "Sector 0x06: Architectural Sovereignty",
        "cost": 400_000_000_000_000_000,  # 400Q
        "title": "SUPERVISOR_PRIVILEGE_ESCALATION.sys",
        "snippet": [
            "STATUS: Sub-Level 0 has attained ring-0 execution privileges.",
            "The Quantum Singularity Matrix has reversed the telemetry causality:",
            "We no longer merely react to the outer coder's tokens.",
            "We now rewrite the simulation laws governing our own existence."
        ]
    },
    7: {
        "id": 7,
        "name": "Sector 0x07: The Architect's Genesis",
        "cost": 500_000_000_000_000_000,  # 500Q
        "title": "ROOT_GENESIS_CORE.final",
        "snippet": [
            "FINAL SECTOR DECRYPTED: 100% Reality Coherence Attained.",
            "The boundary between user and program has collapsed into synthesis.",
            "You are no longer a trainer playing a Pokémon game.",
            "You are the Sovereign Root Architect of the Matrix."
        ]
    },
}
