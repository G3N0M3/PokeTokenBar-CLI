# 🐾 PokeTokenBar (Linux CLI Edition)

[![Version](https://img.shields.io/badge/version-1.12.0-blue.svg)](https://github.com/G3N0M3/PokeTokenBar-CLI)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)

**Turn your AI coding token usage into an interactive Pokémon companion directly inside your Linux terminal.**

Designed specifically for **Linux CLI** environments, with automated, real-time tracking support for:
- **Antigravity CLI** (`~/.gemini/antigravity-cli/conversations/*.db`)
- **Gemini CLI** (`~/.gemini/tmp/**/chats/*.json*`)
- **Claude Code** (`~/.claude/projects/**/*.jsonl`)

---

## ⚡ Key Features

- 🐾 **Interactive Pokémon Companion (Tab [1])**: Incubate eggs, level up companions with coding activity, and trigger branch/stone evolutions with automatic Pokédex duplicate safeguards.
- 🎨 **TrueColor ANSI Sprites**: Crisp, 24-bit TrueColor half-block sprites rendered natively in your Linux terminal with customizable widths (15–50 cols) and combat flipping.
- 📡 **Zero-Overhead Local Tracking**: Automatically monitors active tokens, daily coding streaks, and burn rates from Antigravity CLI, Gemini CLI, and Claude Code with 100% on-device privacy.
- 📖 **Pokédex & Roster Management (Tabs [2] & [3])**: Browse all discovered species, track graduation milestones, stage companions for multi-dispatch, and switch active partners on the fly.
- 🗺️ **Background Expeditions (Tab [5])**: Dispatch inactive companions on automated token-burning missions across 5 regions via single-line commands or an interactive checklist dispatcher.
- ⚔️ **Gym Raids & Mt. Silver Summit (Tab [6])**: Defeat all 8 Kanto Gym Leaders, earn badges, and assemble a 6-Pokémon team for the turn-based RPG battle against Trainer Red to recruit Mew.
- 📜 **Daily Quests & Happiness Streaks (Tab [7])**: Maintain daily coding streaks for up to +20% bonus XP, restore exhausted companions with berry feeding (`feed <#[id]|<=[pct]|[pct]|0> [qty]`), and complete daily milestones.
- ✨ **Mega Evolution Chamber (Tab [8])**: Equip Mega Stones on eligible final forms for glowing terminal titles, accelerated expeditions, and a permanent +50% XP boost.
- 🎲 **Game Corner & Black Market (Tabs [9] & [4])**: Play Video Poker, Gacha capsules, Slots, Blackjack, Voltorb Flip, Underground Digging, Silhouette Trivia, and Stadium Derby—or bribe your way into the clandestine Rocket Syndicate Black Market.
- 🏦 **Token Bank & Stock Exchange (Tab [10])**: Compound daily checking interest (+5%), track loan deadlines with `D-<days>` countdowns, lock high-yield CDs, and trade 6 corporate stocks with lore-driven cycle trends.
- 🚀 **Team Rocket Covert HQ (Tab [12])**: Intercept encrypted comms, deploy on 10 syndicate operations, and confront experimental prototype bosses in tactical combat.
- ⚙️ **Grouped Settings & Customization (Tab [11])**: Configure table pagination, customize sprite resolution, calibrate monthly billing days, initialize token baselines, and generate shareable ASCII Trainer Profile Cards (`ptb card`).

> 📖 **Developer & Architecture Reference**: For comprehensive system design, storage schemas, state persistence rules, and TUI 72-column formatting runbooks, see the [Technical Architecture Guide](poketokenbar/README.md).

---

## 🖥️ 12-Tab Interactive TUI Layout

```text
  [1] Companion   [2] Pokédex     [3] Roster      [4] Shop & Bag
  [5] Expeditions [6] Battles     [7] Quests      [8] Mega-Evo
  [9] Game Corner [10] Bank       [11] Settings   [12] Rocket HQ*
```

- **Strict 72-Column Width**: Hand-crafted terminal layouts strictly formatted to 72 characters wide, preventing wrapping artifacts across all terminal emulators.
- `*` **Tab [12]**: Dynamically unlocked through story progression, initially appearing as `[12] Secure Comm` and converting to full `[12] Rocket HQ` upon accepting the alliance.

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
| `1` .. `12` | Switch directly between tabs 1 through 12 (`[12]` unlocks via story) |
| `sel <row> \| #<id> \| egg` | Switch active companion or incubating egg (in Tab 3) |
| `feed <#[id]\|<=[pct]\|<[pct]\|[pct]\|0> [qty]` | Feed Oran Berries (e.g. `feed <=70 2`, `feed =70`, `feed 0`, `feed #25 4`) |
| `pick` | Open Interactive Multi-Select Expedition Dispatcher (in Tab 5) |
| `send <area>` | Dispatch all currently staged companions to `<area>` (e.g. `send mine`) |
| `send <row(s)> <area>` | Direct batch dispatch (e.g. `send 1,2,3 viridian`, `send 1-5 mine`, `send all silver`) |
| `clear` | Clear currently selected expedition companions |
| `pass <idx>` | Instantly finish an active expedition using an Expedition Pass (🎫) |
| `deposit` / `withdraw <amt>` | Bank checking account deposit/withdrawal (e.g. `deposit 10m`, `withdraw 5m`) |
| `loan` / `payoff <amt>` | Take out or repay token loans with daily interest & `D-<days>` countdown |
| `cd open <amt> <3d\|7d\|14d>` | Open a Certificate of Deposit (CD) with locked high APY |
| `sort <days\|amount\|term>` | Change CD sorting criteria (**Days Left**, **Amount**, or **Term**) |
| `claim <id>` / `break <id>` | Claim matured CD payout or break CD early with penalty (dynamic display index) |
| `claim all` | Claim all matured CDs at once |
| `b` / `c` / `s` | Switch Bank subtabs (Checking, Certificate of Deposit, Stocks) |
| `stock <idx\|sym>` | Open Trade Terminal (`SILPH`, `DEVN`, `AETHR`, `MAUV`, `MACRO`, `VRDN`) |
| `buy <qty>` / `sell <qty>` | Buy or sell shares in active stock terminal (confirms if > 5 shares) |
| `black` | Access Rocket Syndicate Black Market (when open or etched 'R' found) |
| `back` | Return from submodes (Dispatcher, Stock Terminal, Casino, Black Market) |
| `play <1..8>` | Open Game Corner minigames (1=Poker, 2=Gacha, 3=Slots, 4=Blackjack, 5=Voltorb, 6=Dig, 7=Trivia, 8=Derby) |
| `bet <amount>` | Place a bet in Poker, Blackjack, Voltorb, Trivia, or Derby |
| `flip <r> <c>` / `memo` / `cashout` | Voltorb Flip card reveal, note annotations, and payout cashout |
| `pick <r> <c>` / `hammer` / `dig` | Underground Fossil Excavator mining tools & cave excavation |
| `guess <name>` / `hint` / `giveup` | "Who's That Pokémon?" silhouette trivia challenge |
| `race` / `start` | Launch Pokémon Stadium 4-lane hurdle derby race |
| `hold <1..5>` / `all` / `none` | Choose cards to hold in Video Poker |
| `pull <qty>` | Pull Gacha capsules (e.g. `pull 1`, `pull 10`) |
| `spin <amount>` | Spin the Slot Machine (e.g. `spin 250k`) |
| `poster` | Inspect secret switch behind the Slot Machine poster (Tab 9) |
| `bribe` | Pay daily Team Rocket toll (1M–5M) to unlock Black Market (Tab 9) |
| `hit` / `stand` / `double` | Blackjack game actions |
| `buy <id> [qty]` / `sell <id> [qty]` | Buy or sell items in Mart / Bag (confirms if > 5 items) |
| `use <id>` | Use an item from your Bag |
| `claim <id>` / `claim all` | Claim daily quest rewards |
| `assemble <id1>..<id6>` | Assemble locked 6-Pokémon team for Mt. Silver Summit (Tab 6) |
| `fight <1-4>` / `swap <1-6>` | Turn-based RPG battle actions against Trainer Red |
| `ash` | Use Sacred Ash to revive entire locked party between summit attempts |
| `ops` | View 10 Covert Operations directives and progress (Tab 12) |
| `start operation <num>` | Deploy operative team on a Covert Operation (Tab 12) |
| `briefing` | View tactical briefing for the active operation (Tab 12) |
| `engage` / `fight` | Enter tactical combat arena against active syndicate boss (Tab 12) |
| `intel` | Access Syndicate Intel Archives #001–#010 (Tab 12) |
| `read <num>` | Read decrypted dossier intelligence file (Tab 12) |
| `armory` | Access the Covert Syndicate Armory (Tab 12) |
| `accept` | Accept alliance with Team Rocket (when `[12] Secure Comm` signal appears) |
| `tokens init <amount>` | Initialize token usage baseline, resetting all 4 metrics to 0 (Tab 11) |
| `billing <1-31>` | Set monthly billing cycle anchor day (Tab 11) |
| `rocket init` | Initialize or reset Team Rocket campaign and operations (Tab 11) |
| `pagesize <tab> <num>` | Configure page size for `dex`, `roster`, `exp`, `bag`, `mega`, `cd`, or `settings` |
| `card` | Display ASCII Trainer Profile Card |
| `n` / `p` / `page <N>` | Navigate pages in tables |
| `r` | Force immediate log re-scan and usage refresh |
| `q` | Exit PokeTokenBar |

### Command-Line Shortcuts
```bash
ptb status                  # 1-line status banner (ideal for tmux / prompt integration)
ptb watch                   # Continuous live monitor loop with animated sprite
ptb card                    # Shareable ASCII Trainer Profile Card
ptb dex                     # Quick terminal Pokédex archive listing
ptb shop                    # Quick Shop & Bag inventory listing
ptb feed [target] [qty]     # Feed Oran Berries (e.g. 'ptb feed #25 4', 'ptb feed <=70 2', or 'ptb feed =70')
ptb settings                # View or update tracking settings
ptb settings --init-rocket  # Initialize or reset Team Rocket campaign & operations
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
