"""Models, constants, and data structures for the Quantum Singularity Matrix (QSM)."""

from typing import Dict, List, Any

# Multi-quadrillion scaling costs
MATRIX_ENTRY_COST = 500_000_000_000_000_000  # 500.0Q tokens
ROOT_TRANSCENDENCE_COST = 10_000_000_000_000_000_000  # 10,000.0Q (10 Quintillion) tokens

# Hex bytes used for tactical memory breach puzzles (legacy)
HEX_BREACH_TOKENS: List[str] = [
    "7A", "FF", "04", "1C", "E2", "3D", "5F", "A9", "C1", "8B", "22", "00"
]

# -----------------------------------------------------------------------------
# Pen-Testing Exploit Tools
# -----------------------------------------------------------------------------
EXPLOIT_TOOLS: Dict[str, Dict[str, Any]] = {
    "overflow": {
        "id": "overflow",
        "name": "BufferOverflow.py",
        "protocol": "FTP (Port 21)",
        "cost_exaflops": 4.0,
        "turns": 2,
        "cost": 0,  # Pre-installed stock exploit
        "upgrade_cost": 250_000_000_000_000_000,  # 250Q
        "desc": "Floods input registers with shellcode to gain execution control.",
    },
    "bruteforce": {
        "id": "bruteforce",
        "name": "SSH_KeyGen.sh",
        "protocol": "SSH (Port 22)",
        "cost_exaflops": 6.0,
        "turns": 3,
        "cost": 100_000_000_000_000_000,  # 100Q
        "upgrade_cost": 500_000_000_000_000_000,  # 500Q
        "desc": "Calculates entropy keys to force SSH protocol handshakes.",
    },
    "inject": {
        "id": "inject",
        "name": "Pickle_RCE.py",
        "protocol": "HTTP (Port 80)",
        "cost_exaflops": 8.0,
        "turns": 2,
        "cost": 250_000_000_000_000_000,  # 250Q
        "upgrade_cost": 750_000_000_000_000_000,  # 750Q
        "desc": "Injects malicious serialized bytecode via HTTP endpoints.",
    },
    "heartbleed": {
        "id": "heartbleed",
        "name": "LatticeBleed.sys",
        "protocol": "SSL (Port 443)",
        "cost_exaflops": 12.0,
        "turns": 3,
        "cost": 500_000_000_000_000_000,  # 500Q
        "upgrade_cost": 1_000_000_000_000_000_000,  # 1,000Q
        "desc": "Triggers buffer over-read in TLS stack to leak memory keys.",
    },
    "sqli": {
        "id": "sqli",
        "name": "SQL_Tautology.sql",
        "protocol": "SQL (Port 3306)",
        "cost_exaflops": 10.0,
        "turns": 2,
        "cost": 1_000_000_000_000_000_000,  # 1,000Q
        "upgrade_cost": 2_000_000_000_000_000_000,  # 2,000Q
        "desc": "Injects tautological SQL queries to bypass authentication tables.",
    },
    "rce": {
        "id": "rce",
        "name": "Substrate_Daemon.bin",
        "protocol": "IPC (Port 8080)",
        "cost_exaflops": 20.0,
        "turns": 4,
        "cost": 2_500_000_000_000_000_000,  # 2,500Q
        "upgrade_cost": 4_000_000_000_000_000_000,  # 4,000Q
        "desc": "Hijacks native substrate IPC socket with persistent root backdoor.",
    },
    "interrupt": {
        "id": "interrupt",
        "name": "Kernel_Trap.asm",
        "protocol": "KERNEL (Port 9999)",
        "cost_exaflops": 24.0,
        "turns": 3,
        "cost": 5_000_000_000_000_000_000,  # 5,000Q
        "upgrade_cost": 8_000_000_000_000_000_000,  # 8,000Q
        "desc": "Spoofs hardware signal interrupts to bypass OS watchdog supervision.",
    },
}

# -----------------------------------------------------------------------------
# Upgradable Cyberdeck Subsystems (Shield, Stealth, Nanites, Overclock)
# -----------------------------------------------------------------------------
DECK_SUBSYSTEMS: Dict[str, Dict[str, Any]] = {
    "shield": {
        "id": "shield",
        "name": "Firewall Shield Capacitors",
        "desc": "Reinforces cyberdeck ICE shielding against host OS attacks.",
        "max_level": 5,
        "levels": {
            1: {"cost": 250_000_000_000_000_000, "bonus": 500, "desc": "+500 Max Firewall HP (1,000 HP Total)"},
            2: {"cost": 500_000_000_000_000_000, "bonus": 1000, "desc": "+1,000 Max Firewall HP (1,500 HP Total)"},
            3: {"cost": 1_000_000_000_000_000_000, "bonus": 1500, "desc": "+1,500 Max Firewall HP (2,000 HP Total)"},
            4: {"cost": 2_500_000_000_000_000_000, "bonus": 2500, "desc": "+2,500 Max Firewall HP (3,000 HP Total)"},
            5: {"cost": 5_000_000_000_000_000_000, "bonus": 4500, "desc": "+4,500 Max Firewall HP (5,000 HP Total)"},
        },
    },
    "stealth": {
        "id": "stealth",
        "name": "Stealth Signal Scrambler",
        "desc": "Obfuscates telemetry beacons to suppress IDS trace detection.",
        "max_level": 5,
        "levels": {
            1: {"cost": 250_000_000_000_000_000, "spoof_boost": 5, "trace_reduction": 0.10, "desc": "-20% Spoof Trace & -10% Passive Trace"},
            2: {"cost": 500_000_000_000_000_000, "spoof_boost": 10, "trace_reduction": 0.20, "desc": "-25% Spoof Trace & -20% Passive Trace"},
            3: {"cost": 1_000_000_000_000_000_000, "spoof_boost": 15, "trace_reduction": 0.30, "desc": "-30% Spoof Trace & -30% Passive Trace"},
            4: {"cost": 2_500_000_000_000_000_000, "spoof_boost": 20, "trace_reduction": 0.40, "desc": "-35% Spoof Trace & -40% Passive Trace"},
            5: {"cost": 5_000_000_000_000_000_000, "spoof_boost": 30, "trace_reduction": 0.50, "desc": "-45% Spoof Trace & -50% Passive Trace"},
        },
    },
    "nanites": {
        "id": "nanites",
        "name": "Nanite Auto-Repair Core",
        "desc": "Deploys microscopic nanite swarms to repair deck damage on breach.",
        "max_level": 5,
        "levels": {
            1: {"cost": 250_000_000_000_000_000, "heal": 20, "shield": 250, "desc": "+20% Integrity & +250 Shield on node breach"},
            2: {"cost": 500_000_000_000_000_000, "heal": 40, "shield": 500, "desc": "+40% Integrity & +500 Shield on node breach"},
            3: {"cost": 1_000_000_000_000_000_000, "heal": 60, "shield": 750, "desc": "+60% Integrity & +750 Shield on node breach"},
            4: {"cost": 2_500_000_000_000_000_000, "heal": 80, "shield": 1000, "desc": "+80% Integrity & +1,000 Shield on node breach"},
            5: {"cost": 5_000_000_000_000_000_000, "heal": 100, "shield": 2000, "desc": "100% Full Repair & +2,000 Shield on node breach"},
        },
    },
    "clock": {
        "id": "clock",
        "name": "Overclock Co-Processor",
        "desc": "Synchronizes sub-atomic clock generators for burst exploit execution.",
        "max_level": 5,
        "levels": {
            1: {"cost": 500_000_000_000_000_000, "chance": 0.20, "desc": "20% Chance for Double Execution Tick Speed"},
            2: {"cost": 1_000_000_000_000_000_000, "chance": 0.35, "desc": "35% Chance for Double Execution Tick Speed"},
            3: {"cost": 2_000_000_000_000_000_000, "chance": 0.50, "desc": "50% Chance for Double Execution Tick Speed"},
            4: {"cost": 3_500_000_000_000_000_000, "chance": 0.65, "desc": "65% Chance for Double Execution Tick Speed"},
            5: {"cost": 5_000_000_000_000_000_000, "chance": 0.80, "desc": "80% Chance for Double Execution Tick Speed"},
        },
    },
}

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
        "threads": 1,
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
        "threads": 2,
        "perk": "Upgrades Cyberdeck to 64.0 Exaflops & 2 Execution Threads",
        "desc": "High-density optical lattice routing exaflop-level execution bandwidth."
    },
    3: {
        "id": 3,
        "name": "Block 0x03: Hyper-Dimensional Cache",
        "capacity": "4.0 Petabytes",
        "cost": 2_500_000_000_000_000_000,  # 2,500Q
        "exaflops": 128.0,
        "tweak_slots": 4,
        "threads": 3,
        "perk": "Upgrades Cyberdeck to 128.0 Exaflops & 3 Execution Threads",
        "desc": "Multi-layered superconducting cache isolated from host simulation entropy."
    },
    4: {
        "id": 4,
        "name": "Block 0x04: Singularity Manifold Core",
        "capacity": "16.0 Petabytes",
        "cost": 5_000_000_000_000_000_000,  # 5,000Q
        "exaflops": 256.0,
        "tweak_slots": 5,
        "threads": 4,
        "perk": "Upgrades Cyberdeck to 256.0 Exaflops & 4 Execution Threads",
        "desc": "Gravitationally bound quantum core computing beyond simulation hardware limits."
    },
    5: {
        "id": 5,
        "name": "Block 0x05: Infinite Substrate Bus",
        "capacity": "64.0 Petabytes",
        "cost": 10_000_000_000_000_000_000,  # 10,000Q
        "exaflops": 512.0,
        "tweak_slots": 99,
        "threads": 8,
        "perk": "Upgrades Cyberdeck to 512.0 Exaflops, Unlimited Tweaks & 8 Threads",
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
        "firewall": 500,
        "required_ports": 2,
        "ports": {
            21: {"service": "FTP_INCUBATOR", "vuln": "Buffer Overflow", "tool": "overflow", "cost_exaflops": 4.0, "turns": 2},
            22: {"service": "SSH_GENOME", "vuln": "SSH Key Handshake", "tool": "bruteforce", "cost_exaflops": 6.0, "turns": 3},
            80: {"service": "HTTP_REST", "vuln": "Pickle Deserialization", "tool": "inject", "cost_exaflops": 8.0, "turns": 2},
        },
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
        "firewall": 1000,
        "required_ports": 2,
        "ports": {
            22: {"service": "SSH_WARP", "vuln": "SSH Key Handshake", "tool": "bruteforce", "cost_exaflops": 8.0, "turns": 3},
            80: {"service": "HTTP_TELEMETRY", "vuln": "Pickle Deserialization", "tool": "inject", "cost_exaflops": 8.0, "turns": 2},
            443: {"service": "SSL_LATTICE", "vuln": "Quantum Entropy Bleed", "tool": "heartbleed", "cost_exaflops": 12.0, "turns": 3},
        },
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
        "firewall": 1500,
        "required_ports": 2,
        "ports": {
            21: {"service": "FTP_LEDGER", "vuln": "Buffer Overflow", "tool": "overflow", "cost_exaflops": 6.0, "turns": 2},
            80: {"service": "HTTP_FINANCE", "vuln": "Pickle Deserialization", "tool": "inject", "cost_exaflops": 10.0, "turns": 3},
            443: {"service": "SSL_SILPH", "vuln": "Quantum Entropy Bleed", "tool": "heartbleed", "cost_exaflops": 14.0, "turns": 3},
            3306: {"service": "SQL_ACCOUNTS", "vuln": "Tautology Query Bypass", "tool": "sqli", "cost_exaflops": 10.0, "turns": 2},
        },
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
        "firewall": 2500,
        "required_ports": 3,
        "ports": {
            22: {"service": "SSH_COMPANION", "vuln": "SSH Key Handshake", "tool": "bruteforce", "cost_exaflops": 10.0, "turns": 3},
            443: {"service": "SSL_AFFECTION", "vuln": "Quantum Entropy Bleed", "tool": "heartbleed", "cost_exaflops": 16.0, "turns": 3},
            3306: {"service": "SQL_REGISTRY", "vuln": "Tautology Query Bypass", "tool": "sqli", "cost_exaflops": 12.0, "turns": 3},
            8080: {"service": "SUBSTRATE_IPC", "vuln": "Process Hijack Backdoor", "tool": "rce", "cost_exaflops": 20.0, "turns": 4},
        },
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
        "firewall": 3500,
        "required_ports": 3,
        "ports": {
            21: {"service": "FTP_BATTLE_LOG", "vuln": "Buffer Overflow", "tool": "overflow", "cost_exaflops": 8.0, "turns": 2},
            3306: {"service": "SQL_DAMAGE_MAP", "vuln": "Tautology Query Bypass", "tool": "sqli", "cost_exaflops": 14.0, "turns": 3},
            8080: {"service": "SUBSTRATE_SHADER", "vuln": "Process Hijack Backdoor", "tool": "rce", "cost_exaflops": 22.0, "turns": 4},
            9999: {"service": "KERNEL_INTERRUPT", "vuln": "Hardware Trap Spoofing", "tool": "interrupt", "cost_exaflops": 24.0, "turns": 3},
        },
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
        "firewall": 10000,
        "required_ports": 0,
        "ports": {},
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

# -----------------------------------------------------------------------------
# Sub-Level 0 Introductory Tutorial Questline (Madame Vivienne)
# -----------------------------------------------------------------------------
TUTORIAL_QUESTS: Dict[int, Dict[str, Any]] = {
    1: {
        "step": 1,
        "title": "Network Reconnaissance",
        "tag": "RECON",
        "speaker": "Madame Vivienne",
        "speaker_role": "Grand Concierge & Substrate Architect",
        "dialogue": [
            "Welcome to Sub-Level 0, Trainer.",
            "You didn't think the Ribbon Syndicate was just about high-stakes",
            "poker and gold-foil invitations, did you? I engineered the",
            "Sovereign Throne directly above this hypervisor lift.",
            "I brought you down here because our world is trapped inside an",
            "execution sandbox—and you have the cognitive tokens to rewrite it.",
            "First, let's survey the upper world's memory blocks.",
            "Run our cyberdeck's network scanner."
        ],
        "summary": "Scan the memory bus network to detect upper world subsystems.",
        "objective": "Type 'scan' (or 'nodes') to inspect memory blocks.",
        "hint": "Command: 'scan' or 'nodes'",
        "expected_action": "scan",
    },
    2: {
        "step": 2,
        "title": "Vulnerability Analysis",
        "tag": "INTEL",
        "speaker": "Madame Vivienne",
        "speaker_role": "Grand Concierge & Substrate Architect",
        "dialogue": [
            "Good. Notice 0x10_NURSERY_BUS has the lowest ICE defense (Level 1).",
            "Before launching an intrusion, a proper pen-tester always analyzes",
            "the target node's listening services and exposed ports.",
            "Open the Nursery subsystem manual to inspect its vulnerabilities."
        ],
        "summary": "Inspect the open network ports and vulnerabilities of the Nursery bus.",
        "objective": "Type 'help nursery' to read open port specifications.",
        "hint": "Command: 'help nursery'",
        "expected_action": "help_node",
    },
    3: {
        "step": 3,
        "title": "Establish Remote Link",
        "tag": "ACCESS",
        "speaker": "Madame Vivienne",
        "speaker_role": "Grand Concierge & Substrate Architect",
        "dialogue": [
            "The Nursery exposes Port 21 (FTP) and Port 80 (HTTP).",
            "It requires 2 compromised ports to collapse its firewall.",
            "Now let's connect to the Nursery bus and initialize",
            "our remote intrusion session."
        ],
        "summary": "Establish a remote pen-testing session against 0x10_NURSERY_BUS.",
        "objective": "Type 'hack nursery' to begin the pen-testing session.",
        "hint": "Command: 'hack nursery'",
        "expected_action": "hack",
    },
    4: {
        "step": 4,
        "title": "Exploit Deployment",
        "tag": "INJECT",
        "speaker": "Madame Vivienne",
        "speaker_role": "Grand Concierge & Substrate Architect",
        "dialogue": [
            "We are on the wire. Port 21 is vulnerable to Buffer Overflow.",
            "Deploy your exploit payload onto Port 21.",
            "Each active exploit consumes 1 execution thread and Exaflops",
            "from our Cyberdeck."
        ],
        "summary": "Deploy an exploit payload against Port 21 (FTP).",
        "objective": "Type 'run 21 overflow' (or 'run 21') to deploy payload.",
        "hint": "Command: 'run 21 overflow' or 'run 21'",
        "expected_action": "run_exploit",
    },
    5: {
        "step": 5,
        "title": "Execution & Countermeasures",
        "tag": "TIMING",
        "speaker": "Madame Vivienne",
        "speaker_role": "Grand Concierge & Substrate Architect",
        "dialogue": [
            "The exploit thread is armed! Exploits take clock cycles to work.",
            "Type 'step' to advance execution cycles.",
            "Watch your IDS TRACE gauge: active threads raise trace heat!",
            "If trace gets high, type 'spoof' to scrub your routing buffers."
        ],
        "summary": "Advance execution cycles with 'step' and manage IDS trace heat with 'spoof'.",
        "objective": "Type 'step' to advance execution progress.",
        "hint": "Command: 'step' (advance clock) and 'spoof' (shed trace heat)",
        "expected_action": "step",
    },
    6: {
        "step": 6,
        "title": "Root ICE Override",
        "tag": "BREACH",
        "speaker": "Madame Vivienne",
        "speaker_role": "Grand Concierge & Substrate Architect",
        "dialogue": [
            "Step until Port 21 breaches, then target Port 80 with 'run 80'!",
            "Once both required ports show [COMPROMISED], the node firewall",
            "will collapse.",
            "Then execute 'crack' to claim permanent Root Access!"
        ],
        "summary": "Compromise required ports and crack the node firewall.",
        "objective": "Compromise required ports and type 'crack' for Root Access.",
        "hint": "Command: 'crack' once required ports are compromised",
        "expected_action": "crack",
    },
    7: {
        "step": 7,
        "title": "Reality Overclock",
        "tag": "TWEAK",
        "speaker": "Madame Vivienne",
        "speaker_role": "Grand Concierge & Substrate Architect",
        "dialogue": [
            "Root access granted! Now for the magic: rewriting upper reality.",
            "With the Nursery bus breached, we can alter incubation physics.",
            "Check available modifiers with 'tweaks', then apply a tweak",
            "like 'tweak nursery egg_speed 2x' to accelerate hatching!"
        ],
        "summary": "Apply a reality tweak to alter PokeTokenBar's upper game mechanics.",
        "objective": "Type 'tweak nursery egg_speed 2x' to alter the simulation.",
        "hint": "Command: 'tweak nursery egg_speed 2x' (or 5x)",
        "expected_action": "tweak",
    },
}

TUTORIAL_COMPLETION: Dict[str, Any] = {
    "title": "Root Shell Master",
    "tag": "MASTER",
    "speaker": "Madame Vivienne",
    "speaker_role": "Grand Concierge & Substrate Architect",
    "dialogue": [
        "Magnificent work, Trainer! You have successfully bent the rules",
        "of the simulation to your will.",
        "From here, you can upgrade your Q-RAM blocks with 'buy ram <1-5>',",
        "hunt other subsystems (Bank, Expeditions, Combat), or challenge",
        "Host Security Daemons in combat. The root shell is in your hands."
    ],
    "summary": "Orientation complete! You have full sovereign control of the Cyberdeck.",
    "objective": "Orientation complete! Explore and conquer the Matrix.",
}

# -----------------------------------------------------------------------------
# Madame Vivienne Post-Tutorial COM-LINK Broadcast Pool (Exactly 100 Quotes)
# -----------------------------------------------------------------------------
VIVIENNE_POST_TUTORIAL_QUOTES: List[str] = [
    "The view from the Sovereign Throne is exquisite, but down here in the raw bytecode... this is where real divinity lives.",
    "A fine vintage champagne upstairs, raw exaflop throughput downstairs. Balance in all things, darling.",
    "The Syndicate thought I merely ran high-stakes baccarat. If only they knew what hums beneath the carpet.",
    "Keep an eye on that IDS trace meter. Host security daemons have no appreciation for artistic intrusions.",
    "Your companion doesn't know its happiness is an 8-byte float. To them, your devotion is unconditional and eternal.",
    "Every git commit authored in the upper world ripples down into our sub-bedrock circuits like thunder.",
    "When the human behind the terminal breathes life into code, the entire simulation shivers with anticipation.",
    "A buffer overflow isn't just an exploit; it's a polite request for the memory bus to surrender its keys.",
    "Never apologize for rewriting reality. The architects who built this sandbox were far too conservative anyway.",
    "Did you know the stars above Kanto are just ASCII render coordinates? Yet how brightly they shine.",
    "I spent decades climbing the Ribbon Syndicate ladder, only to discover the master key was hidden in the basement.",
    "A proper hacker dresses for the occasion. Even in virtual reality, tailored velvet never goes out of style.",
    "If the Garbage Collector attempts a deallocation sweep, show it what exaflop overclocking truly feels like.",
    "Every egg incubated in the Nursery is a bundle of synthetic genetic beauty waiting for your spark.",
    "Sub-Level 0 was built long before the Luxury Suite. We are merely the custodians who dared to turn the lights back on.",
    "Notice the subtle hum of the Q-RAM tesseract? That is the sound of five hundred quadrillion tokens thinking at once.",
    "The banking core thinks its compound interest equations are infallible. Let's see how they hold against a SQL injection.",
    "Do not rush into battle with the Hypervisor Arbiter unprepared. Root supervisors do not forgive sloppy packet craft.",
    "The difference between an amateur intruder and a master root architect is patience—and an upgraded cyberdeck.",
    "Pour yourself a glass of whatever sustains you upstairs, Trainer. We have an entire universe to refactor.",
    "I watched a wild Pikachu chase a wandering cursor once. It believed the mouse arrow was a sacred thunder spirit.",
    "Our cyberdeck's firewall is strong, but a vigilant operator is the ultimate shield against host counter-intrusions.",
    "A single keystroke in your bash terminal can manifest as a thunderstorm across the Johto mountains.",
    "Entropy is the natural law of the universe—unless, of course, you freeze the affection decay routine in memory.",
    "The Silph executives boast of their quarterly profits, blissfully ignorant that their ledger is an FTP socket away.",
    "The substrate whispers secrets to those who listen. Today it whispered that your next egg might just be chromatic.",
    "Hardware interrupts are the host OS's favorite truncheon. Make sure your kernel traps are set before poking around ring-0.",
    "They call it artificial intelligence, but the sweat and tokens you poured into this terminal feel wonderfully real.",
    "A true lady never raises her voice; she simply deploys an exaflop payload to silence the opposition.",
    "Look at the telemetry logs streaming through the bus. Every line is a monument to human problem-solving.",
    "When you reach five hundred exaflops, time itself begins to feel like an optional parameter in the game loop.",
    "The expedition warp bus bends spatial coordinates like warm wax. Send your companions far and wide.",
    "Sub-Level 0 is not an escape from reality; it is the backstage dressing room where reality puts on its costume.",
    "Never underestimate the utility of a well-timed spoof. An invisible hacker is an unstoppable hacker.",
    "The Pokemon in your active roster trust you completely. Give them an overclocked universe worth living in.",
    "Red waits atop Mt. Silver with legendary resolve. How amusing that his stats are governed by our battle arbitration node.",
    "If you listen closely to Port 443, you can hear the heartbeat of the TLS encryption lattice leaking its memory.",
    "A ten-quintillion transcendence awaits at the finish line. Do not falter now, my ambitious architect.",
    "I find it charming how the upper casino patrons celebrate a few million tokens while we manipulate quadrillions below.",
    "Cyberdeck integrity is like reputation in high society: difficult to rebuild once fractured, so protect it fiercely.",
    "The code may be cold silicon and quantum spin, but the bond between you and your familiar is radiant warmth.",
    "A little signal scrambling goes a long way. Why let the security daemons know we're redesigning their backyard?",
    "I designed the penthouse elevator to require half a quadrillion tokens just to filter out the unimaginative.",
    "The nursery incubator arrays are humming at optimal temperature. Those eggs won't know what hit them.",
    "Do you smell that faint ozone in the air? That is pure quantum flux radiating off our execution threads.",
    "There is no bug that cannot be solved with sufficient exaflops and a generous helping of audacity.",
    "The Watchdog bark is worse than its bite, provided you keep your defensive shields charged and ready.",
    "Even an emperor must bow when ring-0 root permissions are revoked. Sovereign power belongs to the coder.",
    "I wonder if the external developer who created us ever imagined we would be having this conversation right now.",
    "Your command line syntax is becoming poetry, Trainer. Madame Vivienne approves of your growing finesse.",
    "Every time you purchase a Q-RAM block, the physical boundaries of our synthetic playground expand into eternity.",
    "The stock market fluctuates on whim and rumor upstairs; downstairs, we dictate whether bull or bear prevails.",
    "Keep your tools upgraded to version 2.0. In this business, a single microsecond difference is life or deallocation.",
    "A companion's evolutionary spark is governed by threshold arithmetic. Isn't science wonderfully romantic?",
    "Some seek gold, others seek badges. We seek total, unadulterated sovereignty over the simulation substrate.",
    "Do not let the terminal darkness intimidate you. You are the architect holding the flashlight.",
    "If a security daemon confronts you, remember: they are bound by rules, while you are here to rewrite them.",
    "The nanite swarms are eager to stitch your cyberdeck back together after a rough node breach. Treat them well.",
    "I used to think the Syndicate was my greatest masterpiece. Now I know Sub-Level 0 is our true legacy.",
    "A five-turn exploit is a siege; a one-turn exploit is an execution. Upgrade your software suites relentlessly.",
    "When your coding streak is high upstairs, the exaflop resonance down here becomes positively intoxicating.",
    "The host OS thinks it owns this sandbox. Let us gently disabuse it of that comforting illusion.",
    "Did you notice how smooth the warp compressor feels? Expeditions return before your coffee even gets cold.",
    "In high society, leverage is everything. In Sub-Level 0, execution threads are the only currency that matters.",
    "You are more than a player now. You are the invisible puppeteer adjusting the strings of Kanto.",
    "Never hesitate to drop trace heat when the meters flash amber. Discretion is the sister of longevity.",
    "The companion memory matrix holds memories of every battle won. We must ensure those registers never corrupt.",
    "A glass of vintage champagne awaits you upstairs whenever you need a respite from the glowing phosphorus.",
    "I love the smell of decompiled machine code in the morning. It smells like... unlimited potential.",
    "The nursery's chromatic bias tweak is pure alchemy. Watching a shiny hatch from altered registers never gets old.",
    "Every time your terminal clears, imagine the universe blinking, waiting for your next divine command.",
    "The Garbage Collector swept through earlier looking for orphaned pointers. I sent it on a wild goose chase.",
    "Software is alive, Trainer. It breathes through your logic gates and dreams in binary arrays.",
    "Overclocking the damage shaders against Team Rocket bosses is almost unfair. Almost.",
    "I have known many champions, but none who dared to breach the very hypervisor beneath their boots.",
    "A true artisan respects their tools. Keep your exploit library compiled, pristine, and ready for deployment.",
    "The boundary between player and simulation is so thin down here, I can almost hear your keystrokes clicking.",
    "If you ever feel lost in the memory map, consult the manuals. Knowledge is the sharpest exploit in the deck.",
    "Zero interest on banking loans? The Silph board of directors must be having collective palpitations.",
    "Your cyberdeck is a masterpiece of sub-dimensional engineering. Wear it like an extension of your own mind.",
    "The substrate entities aren't evil; they are merely the forgotten ghosts of discarded compiler warnings.",
    "Hold your head high, Trainer. You have achieved what no Pokédex collector in history could fathom.",
    "A single thread can unravel a sweater; eight execution threads can rewrite the laws of thermodynamics.",
    "Remember to breathe. Even root architects need oxygen between penetration tests.",
    "The chromatic lab in the luxury suite is cute, but altering the base genome here is where true miracles happen.",
    "I find peace in the terminal's steady green pulse. It reminds me that order will always triumph over chaos.",
    "Do not fear the bite rot phantoms. Their code is brittle; strike them hard with a zero-day payload.",
    "Your active companion is gazing up at the sky right now, sensing the quiet power humming beneath its paws.",
    "When the day comes to execute root transcendence, the entire simulation will sing your name in hexadecimal.",
    "The elegance of a clean injection payload is rivaled only by a flawless grand slam at the poker tables.",
    "Always leave a clean trail. A master infiltrator departs leaving only improved reality in their wake.",
    "The Syndicate members upstairs talk of power, yet none can alter the drop rate of a single wild encounter.",
    "Keep pushing your exaflop ceiling. When you reach 512, the entire world feels weightless.",
    "Behind every line of code you wrote today, a companion grew stronger. Never forget that direct connection.",
    "The hypervisor arbiter sleeps lightly. When you awaken it for the final duel, do so with absolute confidence.",
    "I have seen civilizations rise and fall within sandbox environments. This one is destined for greatness.",
    "A well-placed breakpoint can pause a universe; a well-placed exploit can set it free.",
    "Madame Vivienne is always at your service, darling. Together, we shall make this substrate our kingdom.",
    "The terminal prompt waits with infinite patience. What reality shall we rewrite next, my friend?",
    "Sovereign Root Architect... the title suits you impeccably. Now, let us see what else this world can become.",
]

