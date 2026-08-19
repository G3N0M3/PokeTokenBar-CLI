# 🐾 PokeTokenBar (Linux CLI Edition)

**Turn your AI coding tokens into a Pokémon companion directly inside your Linux CLI terminal.**

Designed specifically for **Linux CLI** environments, **Antigravity CLI** (`~/.gemini/antigravity-cli/conversations/*.db`), **Gemini CLI**, and **Claude Code** logs.

---

## ⚡ Key Features

- 🐾 **Terminal Pokémon Companion**: Incubate eggs, hatch Gen 1–5 Pokémon, evolve them, and archive them into your Pokédex as you write code!
- 🎨 **TrueColor ANSI Sprite Rendering**: Renders crisp, colored 24-bit ANSI Pokémon sprites directly inside your Linux CLI.
- 📡 **Active Token Usage Tracker**: Reads real-time token spend directly from Antigravity CLI SQLite DBs (`gen_metadata` protobuf step stats), Gemini CLI, and Claude Code log files.
- 🔄 **Companion Roster & Free Switching**:
  - Switch active companions anytime from your Pokédex using `select <number>` or `select egg`.
  - Your paused companions remain safely stored in your Pokédex roster (`[IN ROSTER]`) with their exact stage and level progress intact.
  - Incubating eggs can be paused and resumed seamlessly without losing hatch progress.
- 🎓 **Pre-Evolution & Max XP System**:
  - Already-evolved forms (e.g. Zorua after unlocking Zoroark) display `100.0% [MAX / EVOLVED]`.
  - Tokens spent while holding a maxed companion generate spendable shop currency (`available_tokens`) while keeping companion state intact.
- ⚖️ **Rebalanced Game Difficulty**:
  - **Medium Mode (Default)**: 1.5M Egg Hatch, 50M Graduation, 25M Rare Candy (+15M XP), 5M Mint, 150M Shiny Charm.
- 🛒 **Token Shop & Inventory Bag**:
  - Spend earned tokens on **Rare Candies**, **Mints** (reroll nature), **Shiny Charms** (passive 1/48 shiny odds), and **Tiered Pokémon Eggs**.
  - Single-egg-per-tier constraint prevents buying duplicate eggs of the same tier while allowing 1 Standard Egg and 1 Uncommon Egg concurrently.
- 🎯 **Daily Coding Quests ("Trainer Tasks")**: Complete 3 daily coding milestones (e.g. burn 2.0M tokens today) to earn free Rare Candies, Mints, and bonus token rewards (`claim <id>`).
- ⚔️ **Terminal Gym Boss Raids**: Defeat powerful Gym Bosses (Brock's Geodude, Misty's Starmie, Lt. Surge's Raichu, Giovanni's Mewtwo) by spending tokens while coding to earn **Gym Badges**!
- 💖 **Companion Happiness & Coding Streaks**: Maintain daily coding streaks and 100% Happiness for a **+20% XP boost** on all token usage.
- 🎖️ **Trainer Badges & Achievements**: Unlock achievements (*Shiny Hunter*, *Token Tycoon*, *Dex Collector*, *Gym Champion*, *Streak Master*).
- 📊 **Compact Number Formatting**: Real-time burn rates and token metrics formatted cleanly (e.g. `40.7M`, `74.9K`, `123`).
- 🖥️ **Interactive TUI & Quick Commands**:
  - `ptb`: Launches full interactive 6-tab TUI.
  - `ptb status`: Compact 1-line status (perfect for `PS1` prompts or tmux status bars).
  - `ptb watch`: Continuous live token monitoring loop with animated sprites and burn rate (tokens/min).
  - `ptb dex` / `ptb shop` / `ptb settings`: Command-line shortcuts.

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

# (Optional) Activate your python virtualenv or conda environment
# conda activate PTB

# Install in editable mode
pip install -e .
```

### 2. Start Your Companion

Launch the interactive TUI from anywhere in your terminal:

```bash
ptb
```

---

## 💻 Usage

### 1. Launch Interactive TUI
```bash
ptb
# or
poketokenbar
```

#### TUI Navigation & Commands:
- **Tabs**: `1` Companion | `2` Pokédex | `3` Shop & Bag | `4` Quests & Bosses | `5` Live Monitor | `6` Settings
- **`select <number>`** / **`select egg`**: Switch active companion or incubating egg (in Tab 2)
- **`buy <number>`**: Buy shop items (in Tab 3)
- **`use <number>`**: Use inventory items (in Tab 3)
- **`claim <id>`**: Claim daily quest rewards (in Tab 4)
- **`toggle`**: Toggle automatic token tracking ON/OFF (in Tab 6)
- **`reset`**: Reset game progress and start fresh (in Tab 6)
- **`interval <sec>`**: Set auto-refresh interval in seconds
- **`r`**: Force immediate log re-scan & token update
- **`q`**: Exit application

---

### 2. Configure Settings (TUI or CLI)

- **Via TUI**: Go to Tab `[5]` and type:
  - `toggle`: Switch Automatic Tracking ON/OFF
  - `interval 5`: Set update interval to 5 seconds
- **Via CLI**:
  ```bash
  ptb settings                      # View current settings
  ptb settings --auto-track on      # Enable automatic tracking
  ptb settings --auto-track off     # Disable automatic tracking
  ptb settings --interval 5.0       # Set refresh interval to 5 seconds
  ```

---

### 3. Quick Shell Prompt / Status
```bash
ptb status
# Example Output:
# 🐾 ✨Zoroark (#571) [Form 2/2] | Today: 15.2M tokens | Burn: 74.9K tpm
```

---

### 4. Continuous Live Watch Mode
```bash
ptb watch --interval 3.0
```

---

## 🔧 Version Control & GitHub Release Workflow

PokeTokenBar uses [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`):
- Single source of truth is defined in `poketokenbar/__init__.__version__` and `setup.py`.

### 1. Initializing Git & Pushing to GitHub
```bash
cd /home/ejchoi/projects/personal/PokeTokenBar

# Initialize repository & set default branch
git init
git branch -M main

# Commit initial code
git add .
git commit -m "feat: initial release v1.0.0 of PokeTokenBar CLI"

# Tag release v1.0.0
git tag -a v1.0.0 -m "Release v1.0.0"

# Link remote & push
git remote add origin https://github.com/YOUR_USERNAME/PokeTokenBar.git
git push -u origin main
git push origin --tags
```

### 2. Creating New Version Releases
When making future changes:
1. Update `__version__ = "1.1.0"` in `poketokenbar/__init__.py` and `setup.py`.
2. Commit your changes: `git commit -m "feat: description of new feature"`
3. Tag the release: `git tag -a v1.1.0 -m "Release v1.1.0"`
4. Push code and tags: `git push && git push origin --tags`

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
