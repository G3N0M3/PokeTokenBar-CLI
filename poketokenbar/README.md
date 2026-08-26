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
├── game/
│   ├── companion.py      # `CompanionEngine`: Core game logic, inventory, items, expeditions
│   ├── storage.py        # `StorageManager`: Reads/writes ~/.poketokenbar/state.json
│   ├── models.py         # Static data, dictionaries, and constants (e.g., MEGA_STONES, items)
│   ├── pokeapi.py        # `PokeAPIClient`: Handles HTTP requests to pokeapi.co and sprite caching
│   ├── gacha.py          # `GachaEngine`: Drop rate tables and randomization logic
│   ├── poker.py          # `TexasHoldemEngine`: Deck management, hands, and dealer logic
│   ├── slots.py          # `SlotMachineEngine`: Weighted reel randomization logic
│   └── blackjack.py      # `BlackjackEngine`: Classic 21 logic and card value calculation
└── utils/
    └── formatting.py     # ANSI color wrappers, progress bars, and `parse_tokens` helper
```

## 3. State Management

All persistent player data is stored in a local JSON file managed by `StorageManager`.
- **Location**: `~/.poketokenbar/state.json`
- **Schema Highlights**:
  - `total_tokens`: Total all-time tokens tracked by the external daemon.
  - `spent_tokens`: The amount of tokens spent in the shop/casino. (Available = total - spent).
  - `dex`: List of unlocked Pokédex IDs.
  - `roster`: List of Pokémon dictionaries (ID, name, level, exp, nature, shiny status, happiness).
  - `inventory`: Dictionary mapping item IDs to quantities.
  - `active_mon`: The array index of the currently active companion in the `roster`.

When adding new features, modify `self.state` directly within `CompanionEngine` and call `self.save()` to persist the data to disk.

## 4. TUI Rendering Loop (`tui.py`)

The TUI operates on a synchronous blocking loop using `sys.stdin.readline()`:
1. **Clear Screen**: ANSI escape sequences are used to flush the terminal.
2. **Render Header & Tabs**: Displays the top navigation layout.
3. **Render Active Tab**: Based on `self.current_tab`, delegates to specific render methods (e.g., `render_companion_tab`, `render_game_corner_tab`).
4. **Render Footer**: Displays the `self.message` property, which contains feedback from the last executed command.
5. **Await Input**: Blocks and waits for the user to type a command.

*Note: Visual updates (like the Slot Machine spinning) are achieved by running this render loop inside a rapid `for` loop with `time.sleep()` delays, temporarily bypassing the `readline()` block.*

## 5. API & Sprite Caching (`pokeapi.py`)

To prevent rate-limiting and ensure fast terminal renders, all data from `pokeapi.co` is aggressively cached.
- **Cache Location**: `~/.poketokenbar/cache/`
- Sprites are fetched as PNGs and converted into ANSI block-character strings mapped to standard 256-color palettes. 
- The engine uses a default 30-column width for sprites, but this can be dynamically resized by the user in the Settings tab.

## 6. The Game Corner (Minigames)

Minigames reside in Tab 9 and follow a unified architectural pattern:
- The TUI routes commands starting with `play <idx>` to set a `self.minigame_state` (e.g., `"poker"`, `"slot"`).
- `tui.py` intercepts minigame-specific commands (like `spin` or `hit`) and forwards them to wrapper methods in `CompanionEngine` (like `play_slots` or `play_blackjack_action`).
- The `CompanionEngine` validates the player's available tokens and interacts with the standalone engines (`poker.py`, `slots.py`, `blackjack.py`).
- Standalone engines only manage the rules of their specific game (deck state, multipliers, win conditions) and do **not** interact with the file system or token economy directly.

## 7. Adding a New Feature (Workflow)

If you are adding a new mechanic (e.g., a Daycare):
1. Create a logic engine (if complex) in `poketokenbar/game/daycare.py`.
2. Instantiate the engine inside `CompanionEngine.__init__`.
3. Add a wrapper method in `CompanionEngine` (e.g., `handle_daycare(cmd)`) that updates `self.state` and calls `self.save()`.
4. Add a new tab rendering method in `PokeTokenBarTUI` (e.g., `render_daycare_tab`).
5. Update the main `run()` loop in `tui.py` to route inputs to your new method when the tab is active.
