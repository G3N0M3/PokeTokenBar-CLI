# PokeTokenBar: Technical Architecture Guide

This document is intended for developers maintaining or extending the PokeTokenBar application. It outlines the core architecture, module responsibilities, state management, safety guarantees, and the TUI rendering pipeline as of **v1.10.0**.

---

## 1. System Architecture Overview

PokeTokenBar follows a clean separation of concerns between the **View/Controller** (TUI), the **Model/Logic** (Game Engine), and the **Telemetry Ingestion** (Tracker Daemon).

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        AI Coding Log Sources                            │
│  Antigravity CLI (SQLite) │ Gemini CLI (JSON) │ Claude Code (JSONL)     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     ▼
                       ┌───────────────────────────┐
                       │  UsageManager (Tracker)   │
                       └─────────────┬─────────────┘
                                     ▼
                       ┌───────────────────────────┐
                       │ CompanionEngine (Model)   │ ◄─── StorageManager
                       │   - Growth & Evolution    │      (~/.poketokenbar/
                       │   - Expeditions & Roster  │       state.json[.bak])
                       │   - Bank & Stock Market   │
                       │   - Red Battle & Raids    │
                       └─────────────┬─────────────┘
                                     ▼
                       ┌───────────────────────────┐
                       │   PokeTokenBarTUI (View)  │
                       │   - 11 Fixed 72-Col Tabs  │
                       │   - Interactive Dispatcher│
                       │   - ANSI Half-Block Sprites│
                       └───────────────────────────┘
```

- **TUI (`poketokenbar/tui.py`)**: Responsible for terminal lifecycle, ANSI escape sequences, screen refreshes, active tab navigation, interactive submodes (Stock Terminal, Minigames, Expedition Picker), and parsing raw user input.
- **Engine (`poketokenbar/game/companion.py`)**: The `CompanionEngine` acts as the central state machine and coordinator. It manages companion progression, inventory, banking, expeditions, stock trading, and calls `self.save()` to persist data.
- **Storage (`poketokenbar/game/storage.py`)**: Handles atomic JSON serialization, rolling backups (`state.json.bak`), and strict test runner sandboxing.
- **Tracker (`poketokenbar/tracker/manager.py`)**: Aggregates token usage across multiple local AI assistant logs without external network requests.

---

## 2. Directory & Module Structure

```text
poketokenbar/
├── __init__.py           # Package version definition (v1.10.0)
├── cli.py                # CLI entry point (ptb, ptb status, ptb watch, ptb card, ptb settings)
├── tui.py                # PokeTokenBarTUI: 72-column terminal renderer and input dispatch loop
├── sprite_renderer.py    # SpriteRenderer: 24-bit TrueColor ANSI half-block renderer
├── game/
│   ├── companion.py      # CompanionEngine: Core progression, evolution, expeditions, bank, stocks
│   ├── models.py         # Static data, dataclasses (MonState, ItemKind, Corporation, PokemonBalance)
│   ├── storage.py        # StorageManager: Atomic save, .bak rolling backup, sandbox redirect
│   ├── pokeapi.py        # PokeAPIClient: Local sprite & metadata caching (~/.poketokenbar/cache/)
│   ├── red_battle.py     # RedBattleHandler: Mt. Silver 6v6 turn-based RPG battle engine & Arceus fight
│   ├── gacha.py          # GachaEngine: Drop table probability and capsule pull logic
│   ├── poker.py          # TexasHoldemEngine: 5-card draw Video Poker engine
│   ├── slots.py          # SlotMachineEngine: 3-reel weighted slot machine with animation
│   └── blackjack.py      # BlackjackEngine: Classic 21 logic, card dealer, and double down
├── tracker/
│   ├── manager.py        # UsageManager: Aggregator of active tokens, daily streak, and burn rates
│   ├── antigravity.py    # AntigravityUsageReader: Protobuf reader for Antigravity SQLite DBs
│   ├── gemini.py         # GeminiUsageReader: Session JSON log reader
│   ├── claude.py         # ClaudeUsageReader: JSONL session log reader
│   └── base.py           # Usage dataclasses (UsageEntry, DailyUsage)
├── tui_tabs/             # Dedicated renderer modules for each TUI tab (72-col layout)
│   ├── companion.py      # Tab [1] Active companion HUD & stats
│   ├── pokedex.py        # Tab [2] Discovered species encyclopedia & graduation status
│   ├── roster.py         # Tab [3] Caught Pokémon team & staged multi-selection
│   ├── shop.py           # Tab [4] Mart shop purchases, Bag inventory, item usage, berry feeding
│   ├── expeditions.py    # Tab [5] Pokédex expeditions & Interactive Multi-Select Dispatcher
│   ├── battles.py        # Tab [6] Auto-battles, Gym Raids & Mt. Silver challenge prompt
│   ├── quests.py         # Tab [7] Daily coding quests and scaled token goals
│   ├── mega_evo.py       # Tab [8] Mega Evolution chamber & form reversal
│   ├── game_corner.py    # Tab [9] Casino Hub (Poker, Gacha, Slots, Blackjack)
│   ├── bank.py           # Tab [10] Token Bank (Checking, CDs, and Dynamic Stock Market)
│   ├── settings.py       # Tab [11] Preferences, sprite resolution, page sizes, safe reset
│   └── red.py            # Mt. Silver Summit battle interface (called from Tab [6])
└── utils/
    └── formatting.py     # ANSI color constants, token abbreviation (format_tokens), progress bars
```

---

## 3. State Management & Data Safety

### Persistent Storage Schema (`~/.poketokenbar/state.json`)

Key                     | Type            | Description
:---------------------- | :-------------- | :-----------------------------------------------------------------
`used_since_install`    | `int`           | Lifetime total tokens indexed from AI log sources.
`spent_tokens`          | `int`           | Lifetime tokens spent on items, casino, or bank. `available = used - spent`.
`active_mon`            | `Dict / None`   | Serialized `MonState` dictionary of currently active companion.
`egg_tier`              | `str / None`    | Tier of incubating egg (`"common"`, `"rare"`, `"legendary"`, etc.).
`egg_usage`             | `int`           | Progress tokens accumulated toward current egg hatch threshold.
`pending_eggs`          | `List[str]`     | Queue of discovered eggs awaiting assignment/swap.
`dex`                   | `List[Dict]`    | List of all registered Pokédex entries with form chains and graduation flags.
`inventory`             | `Dict[str,int]` | Bag inventory counts (`rare_candy`, `berry_oran`, `ice_stone`, etc.).
`expeditions`           | `List[Dict]`    | Active expeditions (`sp_id`, `area`, `progress`, `target`, `is_mega`).
`expedition_slots`      | `int`           | Maximum concurrent expedition capacity (default: 10).
`expedition_logs`       | `List[str]`     | Recent completed expedition event logs (retained to last 3 entries).
`bank_balance`          | `int`           | Tokens deposited in the Token Bank checking account.
`bank_loan`             | `int`           | Active token loan debt.
`cds`                   | `List[Dict]`    | Active Certificates of Deposit (`id`, `tier`, `principal`, `apy`, `matures_at`).
`investments`           | `Dict[str,int]` | Stock share portfolio (`{"silph": int, "devon": int, ...}`).
`corporate_catalysts`   | `Dict[str,int]` | Player action counts influencing stock market movement.
`market_news`           | `List[Dict]`    | Generated Lore News reports with sentiment and ticker effects.
`gym_badges`            | `List[str]`     | Badges earned from Gym Bosses and Trainer Red.
`trainer_battles`       | `Dict`          | Auto-battle record `{"wins": int, "losses": int}`.
`battle_logs`           | `List[str]`     | Recent battle event strings (last 5 fights).
`red_battle_state`      | `Dict / None`   | Active Mt. Silver RPG battle state against PKMN Trainer Red.
`page_size_*`           | `int`           | Configurable table page sizes (`page_size_roster`, `page_size_expedition`, etc.).

### Automatic Rolling Backup (`state.json.bak`)
To prevent accidental save corruption or loss during unexpected process termination, `StorageManager.save_state()` creates an atomic rolling backup copy (`~/.poketokenbar/state.json.bak`) before flushing new state data to disk.

### Strict Test Runner Sandboxing
To protect the player's live save data during automated testing and CI runs:
- `StorageManager.get_state_path()` checks the `PTB_STATE_FILE` environment variable.
- If unset, it inspects `sys.modules` and `sys.argv` for active test runners (`pytest`, `unittest`). If detected, it automatically redirects the save path to `/tmp/ptb_test_sandbox.json`.
- Unit tests run completely isolated from the user's live progress.

---

## 4. Key Subsystem Implementations

### 4.1 Pokédex Expeditions & Multi-Select Dispatcher
Expeditions allow players to send inactive roster Pokémon on background token missions across 5 destinations (*Viridian Forest*, *Evolution Mine*, *Cerulean Cave*, *Mt. Silver*, *Spear Pillar*).

The system supports **three dispatch mechanisms**:
1. **Interactive Multi-Select Dispatcher (`render_expedition_picker`)**:
   - Activated via `dispatch`, `send`, or `select` on Tab [5] or Tab [3].
   - Displays a 72-column table with `[ ]` (available), `[✓]` (selected), `[-]` (deployed), and `[x]` (exhausted) checkboxes.
   - Users toggle companions by entering row numbers or ranges (e.g. `1 2 3`, `1-5`, `all`, `clear`).
   - Entering a destination (`viridian`, `mine`, `cerulean`, `silver`, `spear`, or `to 1`..`to 5`) dispatches the entire batch simultaneously.
2. **Staged Roster Selection**:
   - In Tab [3] Roster, typing `select 1 2 3` or `pick 1-4` stages companions with green `[✓]` badges.
   - Typing `send <area>` (e.g. `send mine`) dispatches the staged companions and clears the stage.
3. **Batch CLI Command**:
   - Single-line syntax: `send 1,2,3 viridian`, `send 1-5 mine`, `send all silver`.

### 4.2 Evolution Intelligence & Duplicate Prevention
- **Automatic Evolution Safeguard (`CompanionEngine._check_growth()`)**:
  When a companion accumulates enough XP to evolve, the engine queries the Pokédex for the next evolutionary stage. If the next stage is already registered (`status != "evolved"`), evolution is automatically halted and the companion is marked `[OWNED]`, preserving the lower-stage companion and preventing duplicate final forms.
- **Strict Duplicate-Free Hatching (`CompanionEngine._pick_species()`)**:
  Hatching an egg checks the player's complete Pokédex and roster against all species in the candidate's evolutionary chain. The player is guaranteed to hatch a species they do not already own.
- **Elemental Evolution Stones**:
  Branch evolutions (e.g. Eevee ➔ Vaporeon, Jolteon, Flareon, Espeon, Umbreon, Glaceon, Leafeon, Sylveon; Poliwhirl ➔ Poliwrath / Politoed) are triggered by purchasing and using elemental stones from the Shop or mining them in Evolution Mine.

### 4.3 Token Bank & Dynamic Stock Market
Tab [10] Bank provides three distinct financial services:
1. **Checking Account**: Standard deposit/withdrawal with interest accrual and collateralized borrowing up to 30% of deposits (max 500M).
2. **Certificates of Deposit (CDs)**: Fixed-term deposit contracts (1-Day at 5% APY, 3-Day at 12% APY, 7-Day at 25% APY) with early withdrawal penalties.
3. **Dynamic Stock Exchange (`stocks`)**:
   - 5 in-universe corporations: Silph Co. (`SLPH`), Devon Corp (`DEVN`), Rocket Enterprises (`RCKT`), Pokétch Co. (`PKTC`), and Aether Foundation (`AETH`).
   - Modeled using Geometric Brownian Motion with drift, volatility, and mean-reversion.
   - **Player Catalysts (`_record_catalyst()`)**: In-game actions trigger market momentum (e.g. completing expeditions drives Silph Co.; winning battles drives Devon Corp; high token burns drive Rocket Enterprises).
   - **Daily Lore News**: Procedurally generated news bulletins hint at sector performance.
   - **Corporate Perks**: Owning significant shareholdings unlocks permanent passive perks (+15% expedition tokens, +20% battle tokens, +10% shiny odds).

### 4.4 Mt. Silver Summit & Red Battle (Tab [6])
The Mt. Silver Red Battle is architecturally integrated into Tab [6] Battles:
- Unlocked upon defeating the Champion or via dev flag.
- Uses an independent battle token pool (20M base + tokens earned during combat).
- Turn-based 6v6 RPG combat against PKMN Trainer Red's canonical team (Pikachu, Espeon, Snorlax, Venusaur, Charizard, Blastoise).
- Winning records the team into the **Hall of Fame**, awards the **Master of Masters** badge and a **Mysterious Fetal Form (Mew)**.
- **Arceus Easter Egg**: Challenging Red with his exact iconic team triggers a secret battle against Arceus (5,000,000 HP).

---

## 5. TUI Rendering Pipeline & Layout Constraints

All TUI views adhere to strict formatting standards:
1. **72-Column Fixed Width**:
   Every rendered line (headers, tables, progress bars, logs) is capped at 72 characters to prevent horizontal wrapping across all standard Linux terminal windows.
2. **Dividers**:
   Standardized section dividers use `sys.stdout.write(f"{HEADER}{'='*72}{RESET}\n")` or `"-" * 72`.
3. **Progress Bars (`format_progress_bar`)**:
   Bounded to 12–14 character bar widths to leave ample space for numeric values and labels.
4. **ANSI Half-Block Sprites (`SpriteRenderer`)**:
   Converts 2 vertical pixels into single terminal characters (`▀` / `▄`) with 24-bit TrueColor foreground and background escape sequences (`\033[38;2;R;G;Bm\033[48;2;R;G;Bm`).

---

## 6. Development & Testing Runbook

### Running the Test Suite
Always run tests using Python's unittest runner with state isolation:
```bash
PTB_STATE_FILE=/tmp/ptb_test.json python -m unittest discover tests
```

### Adding a New TUI Command
1. If the command belongs to an existing submode (e.g. Expeditions, Stocks, Minigames), handle it in the appropriate conditional block in `PokeTokenBarTUI.run()`.
2. Add necessary engine methods in `CompanionEngine` or specific sub-engines.
3. Ensure user-facing feedback messages (`self.message`) fit cleanly within 72 columns.
4. Add unit test coverage in `tests/test_companion.py`.
