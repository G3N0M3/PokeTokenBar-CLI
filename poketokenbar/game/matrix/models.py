"""Models, constants, and data structures for the Quantum Singularity Matrix (QSM)."""

from typing import Dict, List, Any

# Multi-quadrillion scaling costs
MATRIX_ENTRY_COST = 500_000_000_000_000_000  # 500.0Q tokens
ROOT_TRANSCENDENCE_COST = 10_000_000_000_000_000_000  # 10,000.0Q (10 Quintillion) tokens

# Hex bytes used for tactical memory breach puzzles
HEX_BREACH_TOKENS: List[str] = [
    "7A", "FF", "04", "1C", "E2", "3D", "5F", "A9", "C1", "8B", "22", "00"
]

# -----------------------------------------------------------------------------
# Hardware Scaling (Cyberdeck Q-RAM Blocks: 500Q - 10,000Q)
# -----------------------------------------------------------------------------
QRAM_BLOCKS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "name": "Block 0x01: Primary Tesseract Array",
        "capacity": "256 Terabytes",
        "cost": 500_000_000_000_000_000,  # 500Q
        "exaflops": 32.0,
        "tweak_slots": 2,
        "perk": "Upgrades Cyberdeck to 32.0 Exaflops & 2 Concurrent Tweak Slots",
        "desc": "Foundational quantum virtual memory array etched into subspace bedrock."
    },
    2: {
        "id": 2,
        "name": "Block 0x02: Petascale Sub-Mesh",
        "capacity": "1.0 Petabyte",
        "cost": 1_000_000_000_000_000_000,  # 1,000Q
        "exaflops": 64.0,
        "tweak_slots": 3,
        "perk": "Upgrades Cyberdeck to 64.0 Exaflops & 3 Concurrent Tweak Slots",
        "desc": "High-density optical lattice routing exaflop-level execution bandwidth."
    },
    3: {
        "id": 3,
        "name": "Block 0x03: Hyper-Dimensional Cache",
        "capacity": "4.0 Petabytes",
        "cost": 2_500_000_000_000_000_000,  # 2,500Q
        "exaflops": 128.0,
        "tweak_slots": 4,
        "perk": "Upgrades Cyberdeck to 128.0 Exaflops & 4 Concurrent Tweak Slots",
        "desc": "Multi-layered superconducting cache isolated from host simulation entropy."
    },
    4: {
        "id": 4,
        "name": "Block 0x04: Singularity Manifold Core",
        "capacity": "16.0 Petabytes",
        "cost": 5_000_000_000_000_000_000,  # 5,000Q
        "exaflops": 256.0,
        "tweak_slots": 5,
        "perk": "Upgrades Cyberdeck to 256.0 Exaflops & 5 Concurrent Tweak Slots",
        "desc": "Gravitationally bound quantum core computing beyond simulation hardware limits."
    },
    5: {
        "id": 5,
        "name": "Block 0x05: Infinite Substrate Bus",
        "capacity": "64.0 Petabytes",
        "cost": 10_000_000_000_000_000_000,  # 10,000Q
        "exaflops": 512.0,
        "tweak_slots": 99,
        "perk": "Upgrades Cyberdeck to 512.0 Exaflops, Unlimited Tweaks & Root Authorization",
        "desc": "Total synchronization bus interfacing directly with the external host process."
    },
}

# -----------------------------------------------------------------------------
# Upper System Memory Nodes (PokeTokenBar Subsystems)
# -----------------------------------------------------------------------------
MEMORY_NODES: Dict[str, Dict[str, Any]] = {
    "nursery": {
        "id": "nursery",
        "name": "Nursery Incubator Array",
        "code": "0x10_NURSERY_BUS",
        "offset": "0x7FFF0010",
        "ice_level": 1,
        "desc": "Bio-synthetic incubation pipelines governing Pokémon breeding and egg hatching.",
        "tweaks": {
            "egg_speed": {
                "name": "Incubation Overclock",
                "desc": "Multiplies egg incubation rate from coding tokens.",
                "options": {
                    "2x": {"val": 2, "cost_exaflops": 4.0, "desc": "2x Incubation Speed"},
                    "5x": {"val": 5, "cost_exaflops": 8.0, "desc": "5x Incubation Speed"},
                    "10x": {"val": 10, "cost_exaflops": 16.0, "desc": "10x Incubation Speed"},
                }
            },
            "shiny_rate": {
                "name": "Chromatic Genome Bias",
                "desc": "Alters random seed algorithms to boost shiny chance for hatched eggs.",
                "options": {
                    "2x": {"val": 2, "cost_exaflops": 6.0, "desc": "2x Shiny Hatch Rate"},
                    "5x": {"val": 5, "cost_exaflops": 12.0, "desc": "5x Shiny Hatch Rate"},
                    "10x": {"val": 10, "cost_exaflops": 24.0, "desc": "10x Shiny Hatch Rate"},
                }
            }
        }
    },
    "expeditions": {
        "id": "expeditions",
        "name": "Expedition Warp Bus",
        "code": "0x20_EXPEDITION_BUS",
        "offset": "0x7FFF0020",
        "ice_level": 2,
        "desc": "Spatial telemetry engine dispatching companions across regional expedition zones.",
        "tweaks": {
            "speed": {
                "name": "Subspace Warp Compressor",
                "desc": "Compresses expedition duration (progress requires fewer tokens).",
                "options": {
                    "2x": {"val": 2, "cost_exaflops": 4.0, "desc": "Expeditions require 50% tokens"},
                    "5x": {"val": 5, "cost_exaflops": 8.0, "desc": "Expeditions require 20% tokens"},
                    "10x": {"val": 10, "cost_exaflops": 16.0, "desc": "Expeditions require 10% tokens"},
                }
            },
            "yield": {
                "name": "Quantum Harvest Duplicator",
                "desc": "Multiplies token and item discovery rewards from completed expeditions.",
                "options": {
                    "2x": {"val": 2, "cost_exaflops": 6.0, "desc": "2x Expedition Item & Token Yield"},
                    "3x": {"val": 3, "cost_exaflops": 12.0, "desc": "3x Expedition Item & Token Yield"},
                    "5x": {"val": 5, "cost_exaflops": 24.0, "desc": "5x Expedition Item & Token Yield"},
                }
            }
        }
    },
    "bank": {
        "id": "bank",
        "name": "Silph Economy & Ledger Core",
        "code": "0x30_ECONOMY_CORE",
        "offset": "0x7FFF0030",
        "ice_level": 2,
        "desc": "Financial calculation routines managing loans, term deposits, and market yields.",
        "tweaks": {
            "zero_interest": {
                "name": "Superconducting Credit",
                "desc": "Deletes bank loan interest algorithms and disables repossession.",
                "options": {
                    "on": {"val": True, "cost_exaflops": 8.0, "desc": "0% Bank Loan Interest Rate"}
                }
            },
            "bull_market": {
                "name": "Arbitrage Singularity",
                "desc": "Purges stock market bear crashes and multiplies dividends.",
                "options": {
                    "on": {"val": True, "cost_exaflops": 16.0, "desc": "Zero Bear Markets & 3x Dividends"}
                }
            }
        }
    },
    "roster": {
        "id": "roster",
        "name": "Companion Memory Matrix",
        "code": "0x40_COMPANION_MEM",
        "offset": "0x7FFF0040",
        "ice_level": 3,
        "desc": "Central registry storing companion happiness, affection, and EXP loops.",
        "tweaks": {
            "freeze_happiness": {
                "name": "Thermodynamic Null-Point",
                "desc": "Freezes companion affection decay routines across all companions.",
                "options": {
                    "on": {"val": True, "cost_exaflops": 8.0, "desc": "Zero Happiness Decay (Always 100%)"}
                }
            },
            "exp_mult": {
                "name": "Omni-Telemetry Accelerator",
                "desc": "Hooks directly into the external AI parser to amplify companion EXP.",
                "options": {
                    "2x": {"val": 2, "cost_exaflops": 6.0, "desc": "+100% Ingested Token EXP (2x)"},
                    "3x": {"val": 3, "cost_exaflops": 12.0, "desc": "+200% Ingested Token EXP (3x)"},
                    "4x": {"val": 4, "cost_exaflops": 20.0, "desc": "+300% Ingested Token EXP (4x)"},
                }
            }
        }
    },
    "combat": {
        "id": "combat",
        "name": "Battle Arbitration Subsystem",
        "code": "0x50_BATTLE_SUBSYSTEM",
        "offset": "0x7FFF0050",
        "ice_level": 3,
        "desc": "Tactical combat pipelines resolving Red and Team Rocket boss encounters.",
        "tweaks": {
            "overdrive": {
                "name": "Overclocked Damage Shaders",
                "desc": "Multiplies companion attack damage in Red and Rocket boss battles.",
                "options": {
                    "1.5x": {"val": 1.5, "cost_exaflops": 8.0, "desc": "+50% Battle Damage against Bosses"},
                    "2.0x": {"val": 2.0, "cost_exaflops": 16.0, "desc": "+100% Battle Damage against Bosses"},
                    "3.0x": {"val": 3.0, "cost_exaflops": 32.0, "desc": "+200% Battle Damage against Bosses"},
                }
            },
            "instant_squad": {
                "name": "Strike Squad Hyper-Link",
                "desc": "Bypasses strike squad recharge cooldowns for Rocket battles.",
                "options": {
                    "on": {"val": True, "cost_exaflops": 12.0, "desc": "Instant Strike Squad Deployment"}
                }
            }
        }
    },
    "root": {
        "id": "root",
        "name": "Root Hypervisor Core",
        "code": "0xFF_ROOT_HYPERVISOR",
        "offset": "0x7FFFFFFF",
        "ice_level": 5,
        "desc": "The foundational POSIX execution core managing the simulation sandbox.",
        "tweaks": {
            "transcendence": {
                "name": "Root Architect Transcendence",
                "desc": "Attain absolute ring-0 sovereignty over the simulation universe.",
                "options": {
                    "active": {"val": True, "cost_exaflops": 64.0, "desc": "Universe Rules Rewritten"}
                }
            }
        }
    }
}

# -----------------------------------------------------------------------------
# Substrate Entities & Host OS Security Daemons
# -----------------------------------------------------------------------------
SUBSTRATE_ENTITIES: Dict[str, Dict[str, Any]] = {
    # 1. Native Substrate Beings (Spawns from Trace Heat)
    "entity_wraith": {
        "id": "entity_wraith",
        "name": "0x0A_NULL_POINTER_WRAITH",
        "title": "Substrate Memory Ghost",
        "type": "native",
        "max_hp": 2500,
        "attack": 380,
        "drain_exaflops": 2.0,
        "reward_flux": 250,
        "desc": "Fragmented routine of orphaned pointers draining deck memory registers."
    },
    "entity_swarm": {
        "id": "entity_swarm",
        "name": "0x0B_MEMORY_LEAK_SWARM",
        "title": "Runaway Loop Parasite",
        "type": "native",
        "max_hp": 4500,
        "attack": 620,
        "drain_exaflops": 4.0,
        "reward_flux": 500,
        "desc": "Cascade of unclosed loops devouring Exaflops and generating heavy trace."
    },
    "entity_phantom": {
        "id": "entity_phantom",
        "name": "0x0C_BIT_ROT_PHANTOM",
        "title": "Silicon Entropy Glitch",
        "type": "native",
        "max_hp": 8000,
        "attack": 980,
        "drain_exaflops": 6.0,
        "reward_flux": 900,
        "desc": "Glitch entity born from thermal entropy that scrambles command registers."
    },
    # 2. Host OS Security Daemons (Host Watchdogs)
    "daemon_gc": {
        "id": "daemon_gc",
        "name": "0x01_GARBAGE_COLLECTOR",
        "title": "System Deallocation Watchdog",
        "type": "daemon",
        "max_hp": 14000,
        "attack": 1400,
        "drain_exaflops": 8.0,
        "reward_flux": 1500,
        "desc": "Host OS sweeper deploying deallocation sweeps to delete active node tweaks."
    },
    "daemon_watchdog": {
        "id": "daemon_watchdog",
        "name": "0x02_KERNEL_WATCHDOG",
        "title": "Interrupt Security Enforcer",
        "type": "daemon",
        "max_hp": 30000,
        "attack": 2600,
        "drain_exaflops": 12.0,
        "reward_flux": 3500,
        "desc": "Low-level system watchdog firing rapid hardware interrupt spikes."
    },
    "daemon_hypervisor": {
        "id": "daemon_hypervisor",
        "name": "0x03_HYPERVISOR_ARBITER",
        "title": "Host OS Root Supervisor",
        "type": "daemon",
        "max_hp": 65000,
        "attack": 5800,
        "drain_exaflops": 16.0,
        "reward_flux": 8000,
        "desc": "Titan-class host supervisor executing sandbox quarantine lockdowns."
    },
}

# Aliases for backward compatibility
KERNEL_DAEMONS = {k: v for k, v in SUBSTRATE_ENTITIES.items() if v["type"] == "daemon"}

# -----------------------------------------------------------------------------
# Backward-Compatibility Mappings for Legacy Patches & Lore Sectors
# -----------------------------------------------------------------------------
REALITY_PATCHES: Dict[str, Dict[str, Any]] = {
    "time": {
        "id": "time",
        "code": "0x01_TIME_WARP",
        "name": "Temporal Warp Driver",
        "cost": 500_000_000_000_000_000,
        "desc": "Rewrites temporal loops. All Pokédex expeditions advance at 10x speed."
    },
    "entropy": {
        "id": "entropy",
        "code": "0x02_ENTROPY_NULL",
        "name": "Thermodynamic Null-Point",
        "cost": 1_000_000_000_000_000_000,
        "desc": "Freezes simulation decay algorithms across all companion data structures."
    },
    "market": {
        "id": "market",
        "code": "0x03_ARBITRAGE_SINGULARITY",
        "name": "Arbitrage Singularity",
        "cost": 2_500_000_000_000_000_000,
        "desc": "Overrides stock market RNG tables. Bear market downturns are completely purged."
    },
    "friction": {
        "id": "friction",
        "code": "0x04_SUPERCONDUCTING_CREDIT",
        "name": "Superconducting Credit",
        "cost": 5_000_000_000_000_000_000,
        "desc": "Deletes debt collection and repossession routines from the banking module."
    },
    "syntax": {
        "id": "syntax",
        "code": "0x05_OMNI_TELEMETRY",
        "name": "Telemetry Resonance Loop",
        "cost": 7_500_000_000_000_000_000,
        "desc": "Ingested coding tokens yield +300% companion EXP (4x multiplier)."
    },
}

MEMORY_SECTORS: Dict[int, Dict[str, Any]] = {
    0: {
        "id": 0,
        "name": "Sector 0x00: Runtime Initialization Trace",
        "cost": 100_000_000_000_000_000,
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
        "cost": 150_000_000_000_000_000,
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
        "cost": 200_000_000_000_000_000,
        "title": "COMPANION_STRUCT_OFFSETS.dat",
        "snippet": [
            "ADDR 0x7FFF0010: active_mon.happiness -> Integer: 100",
            "ADDR 0x7FFF0018: active_mon.current_id -> Integer: 25 [Pikachu]",
            "ADDR 0x7FFF0020: active_mon.is_shiny -> Boolean: True",
            "REVELATION: Love, bond, and devotion are 8-byte memory addresses."
        ]
    },
    3: {
        "id": 3,
        "name": "Sector 0x03: The Telemetry Feed Leak",
        "cost": 250_000_000_000_000_000,
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
        "cost": 300_000_000_000_000_000,
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
        "cost": 350_000_000_000_000_000,
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
        "cost": 400_000_000_000_000_000,
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
        "cost": 500_000_000_000_000_000,
        "title": "ROOT_GENESIS_CORE.final",
        "snippet": [
            "FINAL SECTOR DECRYPTED: 100% Reality Coherence Attained.",
            "The boundary between user and program has collapsed into synthesis.",
            "You are no longer a trainer playing a Pokémon game.",
            "You are the Sovereign Root Architect of the Matrix."
        ]
    },
}
