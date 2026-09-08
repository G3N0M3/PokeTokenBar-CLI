# 🐾 PokeTokenBar (Linux CLI Edition)

[![Version](https://img.shields.io/badge/version-1.10.0-blue.svg)](https://github.com/G3N0M3/PokeTokenBar-CLI)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)

**Turn your AI coding token usage into an interactive Pokémon companion directly inside your Linux terminal.**

Designed specifically for **Linux CLI** environments, with automated, real-time tracking support for:
- **Antigravity CLI** (`~/.gemini/antigravity-cli/conversations/*.db`)
- **Gemini CLI** (`~/.gemini/tmp/**/chats/*.json*`)
- **Claude Code** (`~/.claude/projects/**/*.jsonl`)

---

## ⚡ Key Features

- 🐾 **Terminal Pokémon Companion (Tab [1])**:
  - Incubate eggs, hatch base Pokémon, level them up with your coding tokens, and evolve them as you write code!
  - **Evolution Safeguard**: Automatically halts evolution if the next evolutionary stage is already registered in your Pokédex, preventing unintended duplicates.
  - **Branch Evolutions via Evolution Stones**: Use elemental stones (Fire, Water, Thunder, Leaf, Moon, Sun, Shiny, Dusk, Dawn, Ice) to evolve species with branched evolutions (e.g. Eevee, Poliwhirl, Gloom).
  - **Legendary & Base Pool Expansion**: Includes all 68 Legendary and Mythical Pokémon across Gens 1–7 and over 150 base species.
  - **Guaranteed Duplicate-Free Hatching**: Egg hatching enforces strict exclusion logic against all species and evolutionary family lines in your Pokédex and roster.
  - **Interactive Egg Decision**: Seamlessly choose to swap or keep newly discovered eggs when your egg slot is full.
- 🎨 **TrueColor ANSI Sprite Rendering**:
  - Crisp, 24-bit TrueColor ANSI half-block sprites rendered directly in your terminal, with configurable sprite sizes (15–50 columns).
- 📡 **Real-Time Token Usage Tracking**:
  - Low-overhead log reader tracks active tokens and daily coding activity across multiple AI coding assistants with zero external telemetry.
- 📖 **Pokédex Archives (Tab [2]) & Roster Management (Tab [3])**:
  - **Tab [2] Pokédex**: Historical encyclopedia of all discovered species, showing evolutionary paths, forms, and graduation badges (`[GRADUATED]`, `[OWNED]`, `[EVOLVED]`).
  - **Tab [3] Roster**: Active roster of caught companions. Features **staged selection** with `[✓]` badges for batch expedition dispatching, and single-command switching (`sel <row>|#<id>|egg`).
- 🗺️ **Pokédex Expeditions & Multi-Select Dispatcher (Tab [5])**:
  - Dispatch companions on background token-burning expeditions across 5 areas:
    - **Viridian Forest** (5.0M tokens) ➔ 🌿 Mint + XP + 🪙
    - **Evolution Mine** (10.0M tokens) ➔ 💎 Random Evolution Stone
    - **Cerulean Cave** (15.0M tokens) ➔ 🍬 Rare Candy + Map fragment chance
    - **Mt. Silver** (30.0M tokens) ➔ 🍇 Golden Razz Berry + Map fragment chance
    - **Spear Pillar (Deep)** (100.0M tokens, requires 3x Maps & 100% Happiness) ➔ 🌟 Legendary Egg!
  - **Interactive Multi-Select Dispatcher**: Type `dispatch`, `send`, or `select` on Tab [5] or Tab [3] to enter a visual checklist UI (`[ ]` / `[✓]`), toggle companions by number/range, view available slots, and launch batches with one keystroke!
  - **Batch Command Syntax**: Dispatch immediately using `send 1,2,3 viridian`, `send 1-5 mine`, or `send all silver`.
  - **Expedition Passes (🎫)**: Instantly complete any active expedition with `pass <idx>`.
  - **Clean Recent Logs**: Shows a clean overview of your last 3 completed expeditions.
- 🏦 **Token Bank & Dynamic Stock Exchange (Tab [10])**:
  - **Checking Account**: Deposit tokens, earn interest, and take out collateralized loans (`deposit`, `withdraw`, `loan`, `payoff`).
  - **Certificates of Deposit (CDs)**: Lock tokens into fixed-term 1-day, 3-day, or 7-day CDs for high APY returns (`open`, `claim`, `break`).
  - **Dynamic Stock Market (`stocks`)**: Trade 5 corporate stocks (**Silph Co.** `SLPH`, **Devon Corp** `DEVN`, **Rocket Enterprises** `RCKT`, **Pokétch Co.** `PKTC`, **Aether Foundation** `AETH`) with live trade terminals, daily Lore News reports, and player-driven catalysts!
- 🎲 **Game Corner (Casino Hub) (Tab [9])**:
  - **Video Poker (`play 1`)**: 5-card draw poker with payouts up to **250x** for a Royal Flush (`bet <amount>`, `hold <cards>`).
  - **Gacha Capsule Machine (`play 2`)**: Single pulls (5M) and discounted 10-pull batches (45M) for Shiny Charms, Mega Stones, Rare Eggs, and Legendary Shiny partners (`pull <qty>`).
  - **Animated Slot Machine (`play 3`)**: 3-reel spinning slots with reel animation (`spin <amount>`).
  - **Blackjack 21 (`play 4`)**: Classic table blackjack against the dealer (`bet <amount>`, `hit`, `stand`, `double`).
- ⚔️ **Trainer Battles, Gym Raids & Mt. Silver Summit (Tab [6])**:
  - **Auto-Battles**: Encounter NPC trainers every 2.0M tokens burned to earn spendable tokens and battle badges.
  - **Gym Boss Raids**: Challenge all 8 Kanto Gym Leaders, Elite Four, and the Champion.
  - **Mt. Silver Summit (PKMN Trainer Red)**: Integrated 6v6 turn-based RPG battle against Trainer Red with an independent battle token economy, Hall of Fame logging, the Master of Masters badge, Mew, and a secret Arceus boss encounter.
- ✨ **Mega Evolution Chamber (Tab [8])**:
  - Equip Mega Stones on eligible final forms (Charizard, Lucario, Gengar, Mewtwo, Venusaur, Blastoise) for glowing ANSI titles, faster expeditions, and a **+50% XP boost**! Reversible anytime via `revert`.
- 💖 **Individual Companion Happiness & Coding Streaks**:
  - Every Pokémon maintains its own Happiness (0–100%).
  - **100% Happiness**: Grants a **+20% Bonus XP Boost** on all token gains.
  - **0% Happiness**: Exhausted companions refuse expeditions, miss battles, and gain no XP until fed **Oran Berries 🫐** (+25%).
  - Daily coding activity restores +10% Happiness and maintains your active coding streak!
- 📜 **Daily Quests (Tab [7])**:
  - Complete scaled daily token burning and companion interaction milestones for bonus token payouts and items (`claim <id>` or `claim all`).
- ⚙️ **Settings & Customization (Tab [11])**:
  - Customize pagination across all tables using `pagesize <dex|roster|exp|bag|mega> <number>`.
  - Adjust sprite resolution (15–50 columns).
  - Safe two-step data reset confirmation (`reset` ➔ `reset all`).
- 📇 **Shareable Trainer Card (`ptb card`)**:
  - Generates a terminal-formatted ASCII trainer card with your active Pokémon sprite, gym badges, streak, and rank.

---

## 🖥️ 11-Tab Interactive TUI Layout

```text
  [1] Companion   [2] Pokédex     [3] Roster      [4] Shop & Bag
  [5] Expeditions [6] Battles     [7] Quests      [8] Mega-Evo
  [9] Game Corner [10] Bank       [11] Settings
```

- **Strict 72-Column Width**: Hand-crafted terminal layouts strictly formatted to 72 characters wide, preventing wrapping artifacts across all terminal emulators.

---

## 🚀 Installation & Quick Start

### Prerequisites
- **OS**: Linux (Ubuntu, Debian, Fedora, Arch, WSL2) or macOS Terminal
- **Python**: Python 3.8+

### 1. Clone & Install
```bash
git clone https://github.com/G3N0M3/PokeTokenBar-CLI.git
cd PokeTokenBar-CLI

# Install in editable mode
pip install -e .
```

### 2. Start Your Companion
Launch the interactive TUI from anywhere in your terminal:
```bash
ptb
```

---

## 💻 Command Reference

### Interactive TUI Commands

| Command | Action |
| :--- | :--- |
| `1` .. `11` | Switch directly between tabs 1 through 11 |
| `sel <row> \| #<id> \| egg` | Switch active companion or incubating egg (in Tab 3) |
| `pick` | Open Interactive Multi-Select Expedition Dispatcher (in Tab 5) |
| `send <area>` | Dispatch all currently staged companions to `<area>` (e.g. `send mine`) |
| `send <row(s)> <area>` | Direct batch dispatch (e.g. `send 1,2,3 viridian`, `send 1-5 mine`, `send all silver`) |
| `clear` | Clear currently selected expedition companions |
| `pass <idx>` | Instantly finish an active expedition using an Expedition Pass (🎫) |
| `deposit` / `withdraw <amt>` | Bank checking account deposit/withdrawal (e.g. `deposit 10m`, `withdraw 5m`) |
| `loan` / `payoff <amt>` | Take out or repay token loans (e.g. `loan 2m`, `payoff all`) |
| `open <1d\|3d\|7d> <amt>` | Open a Certificate of Deposit (CD) with locked high APY |
| `claim <id>` / `break <id>` | Claim matured CD payout or break CD early with penalty |
| `b` / `c` / `s` | Switch Bank subtabs (Checking, Certificate of Deposit, Stocks) |
| `stock <idx\|sym>` | Open Trade Terminal for Silph (`1`/`SLPH`), Devon (`2`/`DEVN`), etc. |
| `buy <qty>` / `sell <qty>` | Buy or sell shares in active stock terminal |
| `black` | Open Black Market wandering merchant (in Tab 4) |
| `back` | Return from submodes (Dispatcher, Stock Terminal, Casino, Black Market) |
| `play <1..4>` | Open Game Corner minigames (1=Poker, 2=Gacha, 3=Slots, 4=Blackjack) |
| `bet <amount>` | Place a bet in Poker or Blackjack (e.g. `bet 500k`, `bet 1m`) |
| `hold <1..5>` / `all` / `none` | Choose cards to hold in Video Poker |
| `pull <qty>` | Pull Gacha capsules (e.g. `pull 1`, `pull 10`) |
| `spin <amount>` | Spin the Slot Machine (e.g. `spin 250k`) |
| `poster` | Inspect secret switch behind the Slot Machine poster (Tab 9) |
| `bribe` | Pay the daily Team Rocket Grunt toll (1M–5M) to unlock Black Market |
| `hit` / `stand` / `double` | Blackjack game actions |
| `buy <id>` / `sell <id>` | Buy or sell items in Mart / Bag |
| `use <id>` | Use an item or feed berries from your Bag |
| `claim <id>` / `claim all` | Claim daily quest rewards |
| `assemble <id1>..<id6>` | Assemble 6-Pokémon team for Mt. Silver Summit (in Tab 6) |
| `fight <1-4>` / `swap <1-6>` | Turn-based RPG battle actions against Trainer Red |
| `pagesize <tab> <num>` | Configure page size for `dex`, `roster`, `exp`, `bag`, or `mega` |
| `card` | Display ASCII Trainer Profile Card |
| `n` / `p` / `page <N>` | Navigate pages in tables |
| `r` | Force immediate log re-scan and usage refresh |
| `q` | Exit PokeTokenBar |

### Command-Line Shortcuts
```bash
ptb status       # 1-line status banner (ideal for tmux / prompt integration)
ptb watch        # Continuous live monitor loop with animated sprite
ptb card         # Shareable ASCII Trainer Profile Card
ptb dex          # Quick terminal Pokédex archive listing
ptb shop         # Quick Shop & Bag inventory listing
ptb settings     # View or update tracking settings
```

---

## 📂 Data Storage & Safety

- **Save Location**: `~/.poketokenbar/state.json`
- **Rolling Backup**: Every save automatically creates an atomic backup (`~/.poketokenbar/state.json.bak`).
- **Strict Test Isolation**: Test runners automatically sandbox state to `/tmp/ptb_test_*.json`, ensuring player progress is never modified during development or testing.
- **Privacy First**: 100% on-device local tracking. No prompt content or private code data is ever read or uploaded.

---

## 🗺️ Future Roadmap

- **Asynchronous Ghost PvP**: Export Hall of Fame teams as shareable codes for asynchronous player vs. player battles.
- **Poké Radar Shiny Chaining**: Consecutive daily coding streaks progressively boost wild Shiny encounter rates.
- **Daycare Breeding System**: Passively breed companions over token burn milestones with egg move and IV inheritance.

---

## 🙏 Credits & License

- Based on the original concept from the [PokeTokenBar macOS Project](https://github.com/chattymin/PokeTokenBar).
- Sprite assets powered by [PokéAPI](https://pokeapi.co/).
- Released under the [MIT License](LICENSE). PokeTokenBar is an unofficial fan project and is not affiliated with Nintendo, Game Freak, or The Pokémon Company.
