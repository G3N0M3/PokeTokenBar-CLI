# PokeTokenBar: Technical Architecture Guide

This document is intended for developers maintaining or extending the PokeTokenBar application. It outlines the core architecture, module responsibilities, state management, and the TUI rendering pipeline.

## 1. System Architecture Overview

PokeTokenBar follows a strict separation of concerns between the **View/Controller** (TUI) and the **Model/Logic** (Game Engine).

- **TUI (`tui.py`)**: Responsible entirely for standard input/output, clearing the terminal, rendering ANSI escape sequences, managing the current active tab, and parsing raw user input commands. It holds almost no game logic.
- **Engine (`game/companion.py`)**: The `CompanionEngine` acts as the central brain and state machine. It orchestrates sub-engines (like Poker, Slots, Bank) and manipulates the user's persistent save data based on inputs forwarded by the TUI.

## 2. Directory & Module Structure

```text
poketokenbar/
├── __init__.py           # Package version definition
├── cli.py                # Entry point script (sys.argv parsing, initialization)
├── tui.py                # `PokeTokenBarTUI`: The 72-column terminal renderer and input loop
├── sprite_renderer.py    # `SpriteRenderer`: 24-bit TrueColor ANSI half-block renderer & pure-Python PNG decoder
├── game/
│   ├── companion.py      # `CompanionEngine`: Core game logic, inventory, items, expeditions, growth
│   ├── storage.py        # `StorageManager`: Reads/writes ~/.poketokenbar/state.json atomically
│   ├── models.py         # Static data, dataclasses, and constants (e.g. MonState, ItemKind, MEGA_STONES)
│   ├── pokeapi.py        # `PokeAPIClient`: Handles HTTP requests to pokeapi.co and sprite caching
│   ├── red_battle.py     # `RedBattleHandler`: Mt. Silver turn-based RPG battle engine & Arceus secret fight
│   ├── gacha.py          # `GachaEngine`: Drop rate tables and capsule machine randomization
│   ├── poker.py          # `TexasHoldemEngine`: Deck management, hands, and dealer logic
│   ├── slots.py          # `SlotMachineEngine`: Weighted reel randomization logic
│   └── blackjack.py      # `BlackjackEngine`: Classic 21 logic and card value calculation
├── tracker/
│   ├── manager.py        # `UsageManager`: Thread-safe aggregator and period burn metrics
│   ├── antigravity.py    # `AntigravityUsageReader`: Protobuf wire decoder for Antigravity SQLite DBs
│   ├── gemini.py         # `GeminiUsageReader`: JSON session log parser
│   ├── claude.py         # `ClaudeUsageReader`: JSONL Claude Code log parser
│   └── base.py           # Base dataclasses (UsageEntry, DailyUsage)
├── tui_tabs/             # Dedicated renderer modules for each TUI tab
│   ├── companion.py      # Tab [1] Active companion HUD & stats
│   ├── pokedex.py        # Tab [2] Discovered species archive
│   ├── roster.py         # Tab [3] Caught Pokémon team & selection
│   ├── shop.py           # Tab [4] Shop & Bag inventory
│   ├── expeditions.py    # Tab [5] Background expeditions
│   ├── battles.py        # Tab [6] Auto-battles, Gym Raids & Mt. Silver Red Battle integration
│   ├── quests.py         # Tab [7] Daily coding quests
│   ├── mega_evo.py       # Tab [8] Mega Evolution chamber
│   ├── game_corner.py    # Tab [9] Poker, Slots, Blackjack, Gacha
│   ├── bank.py           # Tab [10] Token Bank deposits & loans
│   ├── settings.py       # Tab [11] Preferences, resolution, data reset
│   └── red.py            # Mt. Silver Summit battle interface (called from Tab [6])
└── utils/
    └── formatting.py     # ANSI color wrappers, progress bars, and token formatting helpers
```

## 3. State Management

All persistent player data is stored in a local JSON file managed by `StorageManager`.
- **Location**: `~/.poketokenbar/state.json`
- **Schema Highlights**:
  - `total_tokens`: Total all-time tokens tracked by the external daemon.
  - `spent_tokens`: The amount of tokens spent in the shop/casino. (Available = total - spent).
  - `bank_balance` / `bank_loan`: Deposited tokens earning interest and active token debt.
  - `dex`: List of unlocked Pokédex IDs and graduation entries.
  - `roster`: List of Pokémon dictionaries (ID, name, level, exp, nature, shiny status, happiness).
  - `inventory`: Dictionary mapping item IDs to quantities.
  - `active_mon`: Serialized dictionary of the currently active companion.
  - `red_battle_state`: State for the active Mt. Silver 6v6 battle against PKMN Trainer Red.

When adding new features, modify `self.state` directly within `CompanionEngine` and call `self.save()` to persist the data to disk.

## 4. TUI Rendering Loop (`tui.py`)

The TUI operates on an 11-tab fixed 72-character width layout using a synchronous blocking loop with `sys.stdin.readline()`:
1. **Clear Screen**: ANSI escape sequences (`\033[H\033[2J`) flush the terminal.
2. **Render Header & Tabs**: Displays the top navigation bar with 11 tabs (`[1] Companion` through `[11] Settings`).
3. **Render Active Tab**: Based on `self.current_tab` (1..11), delegates to specific render methods in `tui_tabs/`.
4. **Render Footer**: Displays `self.message`, which contains feedback from the last executed command or unread background alerts.
5. **Await Input**: Blocks and waits for the user to type a command or tab number (`1`..`11`).

*Note: Visual updates (like the Slot Machine spinning) are achieved by running this render loop inside a rapid `for` loop with `time.sleep()` delays, temporarily bypassing the `readline()` block.*

## 5. Battles & Mt. Silver Red Battle Integration (Tab [6])

Rather than occupying a standalone 12th tab, the **Mt. Silver Summit (Red Battle)** is architecturally integrated directly inside **Tab [6] Battles**:
- **Rendering Dispatch (`tui_tabs/battles.py`)**:
  - If a Red Battle is currently in progress (`status` in `["active", "win", "loss"]`), Tab [6] automatically delegates rendering directly to `tui_tabs/red.py` (`render_red_tab`).
  - If the player has defeated the Champion (or unlocked via dev flag) but is not in an active battle, the standard Gym Boss Raid and Trainer Auto-Battle logs render first, followed by the Mt. Silver challenge prompt at the bottom.
- **Command Routing (`tui.py`)**:
  - When `self.current_tab == 6`, Red Battle commands (`assemble <id1>..<id6>`, `fight <1-4>`, `swap <1-6>`, `run`, `restart`) are intercepted and forwarded to `tui_tabs/red.py` (`handle_red_command`).
  - If a user inputs `12` in the TUI, the interface smoothly redirects them to Tab [6] with a notification indicating that the Red Battle resides inside Battles.
- **Battle Engine (`game/red_battle.py`)**:
  - `RedBattleHandler` maintains an independent battle token pool starting at 20M tokens + tokens earned organically during combat.
  - Handles turn resolution, type effectiveness multipliers, Red's team AI, Hall of Fame logging, and the secret Arceus Easter egg encounter.

## 6. API & Sprite Caching (`pokeapi.py`)

To prevent rate-limiting and ensure fast terminal renders, all data from `pokeapi.co` is aggressively cached.
- **Cache Location**: `~/.poketokenbar/cache/`
- Sprites are fetched as PNGs and converted into ANSI block-character strings mapped to standard 24-bit TrueColor palettes via `SpriteRenderer`.
- The engine uses a default 30-column width for sprites, but this can be dynamically resized by the user in the Settings tab.

## 7. The Game Corner (Minigames)

Minigames reside in Tab 9 and follow a unified architectural pattern:
- The TUI routes commands starting with `play <idx>` to set a `self.minigame_state` (e.g., `"poker"`, `"slot"`).
- `tui.py` intercepts minigame-specific commands (like `spin` or `hit`) and forwards them to wrapper methods in `CompanionEngine` (like `play_slots` or `play_blackjack_action`).
- The `CompanionEngine` validates the player's available tokens and interacts with the standalone engines (`poker.py`, `slots.py`, `blackjack.py`).
- Standalone engines only manage the rules of their specific game (deck state, multipliers, win conditions) and do **not** interact with the file system or token economy directly.

## 8. Adding a New Feature (Workflow)

If you are adding a new mechanic (e.g., a Daycare):
1. Create a logic engine (if complex) in `poketokenbar/game/daycare.py`.
2. Instantiate the engine inside `CompanionEngine.__init__`.
3. Add a wrapper method in `CompanionEngine` (e.g., `handle_daycare(cmd)`) that updates `self.state` and calls `self.save()`.
4. Add a new tab rendering module in `poketokenbar/tui_tabs/daycare.py`.
5. Update `tui.py`'s `render_tabs()` and `run()` event loop to route inputs to your new method when the tab is active.
