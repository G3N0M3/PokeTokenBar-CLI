# 🐾 PokeTokenBar (Linux CLI Edition)

**Turn your AI coding tokens into a Pokémon companion directly inside your Linux CLI terminal.**

Designed specifically for **Linux CLI** environments, **Antigravity CLI** (`~/.gemini/antigravity-cli/conversations/*.db`), **Gemini CLI**, and **Claude Code** logs.

---

## ⚡ Key Features

- 🐾 **Terminal Pokémon Companion**: Incubate eggs, hatch Gen 1–5 Pokémon, evolve them, and archive them into your Pokédex as you write code!
- 🎨 **TrueColor ANSI Sprite Rendering**: Renders crisp, colored 24-bit ANSI Pokémon sprites directly inside your Linux CLI.
- 📡 **Active Token Usage Tracker**: Reads real-time token spend directly from Antigravity CLI SQLite DBs (`gen_metadata` protobuf step stats), Gemini CLI, and Claude Code log files.
- 📖 **Dedicated Pokédex Archive (Tab [2]) & Roster (Tab [3])**:
  - **Tab [2] Pokédex**: Historical archive of all discovered species with evolution & graduation milestones (`[EVOLVED]`, `[GRADUATED]`).
  - **Tab [3] Roster**: Active list of caught Pokémon partners available for switching and expeditions (`[ACTIVE]`, `[IN ROSTER]`, `[ON EXPEDITION]`).
  - Switch companions using `select <roster_idx>` (e.g. `select 2`) or species ID (e.g. `select #570` or `select 570`).
- 🎲 **Token Video Poker (Tab [9])**:
  - Bet your spendable tokens (`bet 500k`, `bet 1m`) and win payouts up to **250x** for a Royal Flush!
  - Draw unheld cards (`hold 1 3 5` or `hold none` / `hold all`).
- 🔮 **Pokémon Gacha Capsule Machine (Tab [10])**:
  - Spend tokens to pull rare capsule items and companions (`pull 1` for 5M or `pull 10` for 45M).
  - Rewards include **Shiny Charms**, **Rare Eggs**, **Mega Stones**, and **Legendary Shiny Partners**!
- 💖 **Individual Companion Happiness**:
  - Every Pokémon in your roster tracks its own Happiness (0-100%).
  - Maintaining **100% Happiness** grants a **+20% XP Boost**.
  - Restored via **Oran Berries 🫐** (+25%) and daily activity (+10%). Decays on missed coding days (-25%/day) and battle losses (-10%).
- 🛡️ **Safe Reset Confirmation Prompt**:
  - Prevents accidental data wipes with a two-step prompt requiring `RESET ALL` confirmation.
- ⚔️ **Mini-Trainer Auto-Battles & Gym Boss Raids (Tab [6])**:
  - Encounter AI Trainers (*Youngster Joey*, *Team Rocket Grunt*, *Rival Blue*) every 2.0M tokens burned to earn bonus spendable tokens and fight Gym Bosses (*Brock*, *Misty*, *Cynthia*)!
- 🗺️ **Pokédex Expeditions (Tab [5])**:
  - Dispatch companions on background expeditions (*Viridian Forest*, *Cerulean Cave*, *Mt. Silver*) to collect Rare Candies, Mints, and Berries.
- ✨ **Mega Evolution & Form Changes**:
  - Equip **Mega Stones** on eligible final forms (*Charizard*, *Lucario*, *Gengar*, *Mewtwo*, *Venusaur*, *Blastoise*) for glowing titles and a **+50% XP boost**!
- 📇 **Shareable Trainer Profile Card (`ptb card`)**:
  - Output a styled ASCII Trainer Profile Card featuring your active companion, rank, coding streak, and Gym Badges!

---

## 🗺️ Roadmap / Future Plans

- **Individualized Mega Stones**: Transition from the current "Universal Key Item" Mega Stone to species-specific Mega Stones (e.g., *Charizardite X*, *Venusaurite*, *Lucarionite*). This will require players to hunt or pull the exact Mega Stone corresponding to their Pokémon to achieve Mega Evolution, adding deeper collection mechanics!

---

## 🖥️ 11-Tab Interactive TUI Layout

```text
  [1] Companion   [2] Pokédex   [3] Roster      [4] Shop & Bag
  [5] Expeditions [6] Battles   [7] Quests      [8] Monitor
  [9] Poker       [10] Gacha    [11] Settings
```

---

## 🚀 Installation & Quick Start

### Prerequisites
- **OS**: Linux terminal / CLI environment (Ubuntu, Debian, Fedora, Arch, WSL2, or macOS Terminal)
- **Python**: Python 3.8+

### 1. Clone & Install

Clone the repository and install `poketokenbar` via `pip`:

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/PokeTokenBar.git
cd PokeTokenBar

# Install in editable mode
pip install -e .
```

### 2. Start Your Companion

Launch the interactive TUI from anywhere in your terminal:

```bash
ptb
```

---

## 💻 Usage & Commands

### Interactive TUI Commands:
- `1`..`11`: Switch directly between all 11 dedicated tabs.
- `select <roster_idx>` / `select #<species_id>` / `select egg`: Switch active partner companion or egg.
- `send <roster_idx> [viridian/cerulean/silver]`: Dispatch companion on expedition.
- `bet <amount>`: Start a Video Poker hand (e.g. `bet 500k`, `bet 1m`).
- `hold <1..5>`: Select held cards in Poker (or `hold none` / `hold all`).
- `pull [1/10]`: Pull 1x or 10x Gacha Capsules.
- `buy <number>`: Purchase shop items.
- `use <number>`: Feed berries or use items from Bag.
- `claim <id>`: Claim daily quest rewards.
- `card`: View ASCII Trainer Profile Card.
- `toggle`: Toggle automatic token tracking ON/OFF (in Settings).
- `reset`: Initiate two-step game progress reset prompt (in Settings).
- `interval <sec>`: Set auto-refresh interval in seconds.
- `r`: Force immediate log re-scan.
- `q`: Exit application.

### Command-Line Shortcuts:
```bash
ptb status       # 1-line status banner (perfect for prompt / tmux)
ptb watch        # Continuous live monitor loop with animated sprite
ptb card         # Display shareable ASCII Trainer Profile Card
ptb dex          # Quick Pokédex archive printout
ptb shop         # Quick Shop & Bag listing
```

---

## 📂 Data Sources & Privacy

- **Antigravity CLI**: Reads SQLite databases at `~/.gemini/antigravity-cli/conversations/*.db` using read-only mode (`mode=ro`).
- **Gemini CLI**: Reads session logs at `~/.gemini/tmp/**/chats/*.json*`.
- **Claude Code**: Reads project session logs at `~/.claude/projects/**/*.jsonl`.
- **Local Storage**: Game state saved at `~/.poketokenbar/state.json`, sprites cached at `~/.poketokenbar/cache/`.
- 100% on-device local tracking. No usage data or prompt content is ever uploaded anywhere.

---

## 🙏 Credits & Acknowledgments

- Based on the original concept and design from the [PokeTokenBar macOS Project](https://github.com/chattymin/PokeTokenBar).
- Sprite assets powered by [PokéAPI](https://pokeapi.co/).

---

## 📄 License & Disclaimer

MIT License. PokeTokenBar is an unofficial, non-commercial fan project and is not affiliated with Nintendo, Game Freak, or The Pokémon Company.
