# PokeTokenBar: Technical Architecture Guide

This document is intended for developers maintaining or extending the PokeTokenBar application. It outlines the core architecture, module responsibilities, state management, safety guarantees, and the TUI rendering pipeline as of **v1.11.0**.

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
                       │   - Rocket Covert HQ      │
                       └─────────────┬─────────────┘
                                     ▼
                       ┌───────────────────────────┐
                       │   PokeTokenBarTUI (View)  │
                       │   - 12 Fixed 72-Col Tabs  │
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
├── __init__.py           # Package version definition (v1.11.0)
├── cli.py                # CLI entry point (ptb, ptb status, ptb watch, ptb card, ptb settings)
├── tui.py                # PokeTokenBarTUI: 72-column terminal renderer and input dispatch loop
├── sprite_renderer.py    # SpriteRenderer: 24-bit TrueColor ANSI half-block renderer (with flip_h support)
├── game/
│   ├── companion.py      # CompanionEngine: Core progression, evolution, expeditions, bank, repossession
│   ├── stock_market.py   # StockMarketEngine: 5 pattern cycles, lore hints, shareholder perks
│   ├── black_market.py   # BlackMarketEngine: 100 contraband pool, sealed troves, counterfeit logic
│   ├── models.py         # Static data, dataclasses (MonState, ItemKind, Corporation, PokemonBalance)
│   ├── storage.py        # StorageManager: Atomic save, .bak rolling backup, sandbox redirect
│   ├── pokeapi.py        # PokeAPIClient: Local sprite & metadata caching (~/.poketokenbar/cache/)
│   ├── rocket_battle.py  # RocketBattleHandler: Tactical boss combat engine, stance cores & persistent HP
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
│   ├── companion.py      # Tab [1] Active companion HUD, stats & milestone celebrations
│   ├── pokedex.py        # Tab [2] Discovered species encyclopedia & graduation status
│   ├── roster.py         # Tab [3] Caught Pokémon team & staged multi-selection
│   ├── shop.py           # Tab [4] Mart shop purchases, Bag inventory, item usage, berry feeding
│   ├── expeditions.py    # Tab [5] Pokédex expeditions & Interactive Multi-Select Dispatcher
│   ├── battles.py        # Tab [6] Auto-battles, Gym Raids, Mt. Silver challenge & Hall of Fame
│   ├── quests.py         # Tab [7] Daily coding quests and scaled token goals
│   ├── mega_evo.py       # Tab [8] Mega Evolution chamber & form reversal
│   ├── game_corner.py    # Tab [9] Casino Hub (Poker, Gacha, Slots, Blackjack)
│   ├── bank.py           # Tab [10] Token Bank (Checking, CDs, and Dynamic Stock Market)
│   ├── settings.py       # Tab [11] Grouped preferences, sprite resolution, page sizes, tokens init
│   ├── rocket.py         # Tab [12] Team Rocket Covert HQ: Operations, Tactical Combat, Armory
│   └── red.py            # Mt. Silver Summit battle interface (called from Tab [6])
└── utils/
    └── formatting.py     # ANSI color constants, token abbreviation (format_tokens), progress bars
```

---

## 3. State Management & Data Safety

### Persistent Storage Schema (`~/.poketokenbar/state.json`)

Key                          | Type            | Description
:--------------------------- | :-------------- | :-----------------------------------------------------------------
`used_since_install`         | `int`           | Lifetime total tokens indexed from AI log sources.
`spent_tokens`               | `int`           | Lifetime tokens spent on items, casino, or bank. `available = used - spent`.
`baseline_total_tokens`      | `int`           | Baseline offset subtracted from lifetime total tokens when re-baselined.
`baseline_date`              | `str / None`    | Calendar date anchor when token metrics baseline was set.
`tokens_init_ts`             | `str / None`    | ISO timestamp when tokens were initialized to 0; filters earlier telemetry.
`billing_cycle_day`          | `int`           | Day of month (1-31) serving as monthly billing cycle anchor.
`active_mon`                 | `Dict / None`   | Serialized `MonState` dictionary of currently active companion.
`egg_tier`                   | `str / None`    | Tier of incubating egg (`"common"`, `"rare"`, `"legendary"`, etc.).
`egg_usage`                  | `int`           | Progress tokens accumulated toward current egg hatch threshold.
`pending_eggs`               | `List[str]`     | Queue of discovered eggs awaiting assignment/swap.
`dex`                        | `List[Dict]`    | List of all registered Pokédex entries with form chains and graduation flags.
`inventory`                  | `Dict[str,int]` | Bag inventory counts (`rare_candy`, `berry_oran`, `ice_stone`, etc.).
`expeditions`                | `List[Dict]`    | Active expeditions (`sp_id`, `area`, `progress`, `target`, `is_mega`).
`expedition_slots`           | `int`           | Maximum concurrent expedition capacity (default: 10).
`expedition_logs`            | `List[str]`     | Recent completed expedition event logs (retained to last 3 entries).
`bank_balance`               | `int`           | Tokens deposited in the Token Bank checking account.
`bank_loan`                  | `int`           | Active token loan debt.
`term_deposits`              | `List[Dict]`    | Active Certificates of Deposit (`id`, `principal`, `term_days`, `days_elapsed`, `current_value`, `matured`).
`cd_sort_criteria`           | `str`           | Active CD sort preference (`"days"`, `"amount"`, `"term"`).
`investments`                | `Dict[str,int]` | Stock share portfolio (`{"silph": int, "devon": int, ...}`).
`stock_market`               | `Dict`          | Dynamic stock exchange state: `prices`, `price_history`, `cost_basis`, `shareholder_tier`, `latest_news`.
`gym_badges`                 | `List[str]`     | Badges earned from Gym Bosses and Trainer Red.
`trainer_battles`            | `Dict`          | Auto-battle record `{"wins": int, "losses": int}`.
`battle_logs`                | `List[str]`     | Recent battle event strings (last 5 fights).
`red_battle_state`           | `Dict / None`   | Active Mt. Silver RPG battle state against PKMN Trainer Red.
`red_locked_team`            | `List[Dict] / None` | Locked 6-Pokémon team for active Mt. Silver summit attempt.
`hall_of_fame`               | `List[Dict]`    | Dual-record Hall of Fame entries (Trainer Red defeats & Arceus triumphs).
`last_milestone`             | `int / None`    | Highest lifetime token milestone reached & celebrated (e.g. 1M, 5M, 10M, 25M, 50M, 100M).
`last_evolution`             | `Dict / None`   | Transient banner metadata for evolution celebration screen.
`rocket_story_unlocked`      | `bool`          | Flag indicating whether Team Rocket Covert HQ (Tab 12) frequency is unlocked.
`rocket_alliance_accepted`   | `bool`          | Flag indicating whether the trainer accepted the Syndicate alliance (`accept`).
`rocket_rank`                | `str`           | Operative clearance rank (`Informant`, `Operative`, `Special Agent`, `Executive`, `Commander`).
`rocket_reputation`          | `int`           | Completed mission reputation progress toward rank promotions (0–10).
`rocket_ops`                 | `Dict[str,Dict]`| 10 Covert Operations status, multi-objective progress, boss HP remaining, and claim state.
`rocket_battle_state`        | `Dict / None`   | Active tactical combat arena state against Syndicate prototype bosses.
`rocket_intel_unlocked`      | `List[str]`     | Decrypted Syndicate Intel Dossier IDs (`"intel_001"` through `"intel_010"`).
`page_size_*`                | `int`           | Configurable table page sizes (`page_size_roster`, `page_size_expedition`, `page_size_cd`, etc.).

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

### 4.3 Token Bank, Stock Cycle Engine & Liquidation Waterfall
Tab [10] Bank provides three distinct financial services:
1. **Checking Account & Borrowing**: Standard deposit/withdrawal with daily interest accrual and collateralized borrowing up to 30% of checking deposits (max 500M tokens).
2. **Certificates of Deposit (CDs) & Dynamic Multi-Key Sorting**:
   - Fixed-term deposit contracts (3-Day at 8% APY, 7-Day at 12% APY, 14-Day at 20% APY compounding daily).
   - **Deterministic Multi-Key Sorting (`CompanionEngine.get_sorted_cds`)**: Supports criteria-based ordering with three modes:
     - `days` (Default): Matured claimable CDs first (`days_left <= 0`), followed by nearest maturity (`days_left` ascending), larger deposit values, and ID.
     - `amount`: Highest current value first (`current_value` descending), matured status, `days_left`, and ID.
     - `term`: Longest duration lockup first (`term_days` descending), matured status, `days_left`, and ID.
   - **Sequential 1-Based Display Indexing**: Active CD rows dynamically number `[1], [2], ...` based on current sort order. Commands (`claim 1`, `break 1`, `claim all`) resolve directly to the sorted index with internal slot fallback.
3. **Dynamic Stock Exchange & Shareholder Tiers (`stocks`)**:
   - **6 In-Universe Corporations**:
     - Silph Co. (`SILPH`): Saffron City tech giant (+15% expedition token yield & speed).
     - Devon Corp (`DEVN`): Rustboro industrial conglomerate (-5% Mart shop item discount).
     - Aether Foundation (`AETHR`): Alolan conservation sanctuary (+5 daily companion happiness recovery, halved decay).
     - Mauville Energy (`MAUV`): Hoenn power utility (+10% casino payout boost).
     - Macro Cosmos (`MACRO`): Galar conglomerate (+20% raid boss damage & token drops).
     - Viridian Dynamics (`VRDN`): Syndicate tech arm (+10% shiny encounter odds & token momentum).
   - **Tiered Shareholder Perks**: Holding larger share positions unlocks escalated corporate dividends and perks:
     - **Retail** (< 10 sh): Base perk unlocked.
     - **Preferred** (10+ sh): 1.5x perk multiplier.
     - **Corporate** (50+ sh): 2x perk multiplier.
     - **Board Member** (250+ sh): 3x perk multiplier.
     - **Controlling** (1000+ sh): 4x maximum perk multiplier.
   - **5 Pattern Cycles**: Stocks run on distinct pattern archetypes rather than random walks:
     - `bull_rally`: Consistent upward momentum, multi-day rallies, resistance testing.
     - `bear_decline`: Downward trends, short-seller pressure, oversold value bounce opportunities.
     - `cyclical_wave`: Predictable oscillating crests and troughs.
     - `speculative_bubble`: High volatility, parabolic spikes followed by sharp liquidation dumps.
     - `consolidation`: Low-volatility sideways trading around support floors.
   - **Predictive Lore Hints & Catalysts**: The trade terminal news ticker broadcasts company-specific narrative hints forecasting upcoming directional moves before market prices update. In-game actions (expeditions, shop purchases, casino PnL, boss fights) trigger corporate catalysts.
   - **Elastic Price Gravity**: Prevents runaway hyper-inflation or permanent corporate bankruptcy.
   - **6-Tier Repossession Waterfall (Overdue Loans)**: When a loan goes unpaid past the default threshold (7+ days), automated liquidation sequentially seizes assets:
     1. *Bank Checking Deposits* (`bank_balance`)
     2. *Spendable Token Balance* (`available_tokens`)
     3. *Term Deposits (CDs)* (matured first at 100%, then active CDs at 90% after early break penalty; excess refunded)
     4. *Corporate Stock Portfolios* (liquidated across all 6 corporations at 90% market bid value; excess refunded)
     5. *Bag Inventory Items* (liquidated at 80% market wholesale price; excess refunded)
     6. *Debt Discharge & Distress Penalty* (remaining unrecoverable debt is discharged, and all companions suffer a -50 Happiness penalty due to bank repossession stress)

### 4.4 Mt. Silver Summit & Red Battle (Tab [6])
The Mt. Silver Red Battle is architecturally integrated into Tab [6] Battles:
- Unlocked upon defeating the Champion or via dev flag.
- Uses an independent battle token pool (20M base + tokens earned during combat).
- Turn-based 6v6 RPG combat against PKMN Trainer Red's canonical team (Pikachu, Espeon, Snorlax, Venusaur, Charizard, Blastoise).
- **Party Lock**: Once assembled via `assemble <id1>..<id6>`, party members are locked from expeditions and roster swaps until Red is defeated or the team wipes.
- **Sacred Ash (`ash`)**: Fully revives all locked party Pokémon between attempts without losing summit progress.
- **Exclusive Mew Reward**: Defeating Red awards the **Master of Masters** badge and recruits **Mew** directly into your roster (Mew is excluded from all egg hatching pools).
- **Dual Hall of Fame**: Separate historical records for standard Red defeats and the secret Arceus encounter.
- **Arceus Easter Egg**: Assembling Red's exact canonical team triggers a secret battle against Arceus (5,000,000 HP).

### 4.5 Rocket Syndicate Underground Black Market (Tabs [4] & [9])
- **7 Daily Contraband Deals from a 100-Item Pool**: Features 7 rotating daily items selected without replacement from an illicit 100-item pool across 9 categories (evolution stones/troves, combat held items, black market consumables, mega stones, mystery crates, map packs, special eggs, syndicate evolution artifacts, and counterfeit items).
- **Sealed Troves & Mystery Crates**: High-tier packages (such as Evolution Stone Troves and Contraband Crates) remain mysteriously sealed until purchased; unpacked contents and jackpot bonuses are revealed in the purchase receipt.
- **Counterfeit & Fraud Items**: 12 shady counterfeit items (rock candy Rare Candies, cardboard Master Balls, painted stones) sold by grunts that scam unsuspecting trainers when inspected or used.
- **Decoupled Dual Entrances**:
  - **Natural Daily Open (5% chance)**: On daily rollover, Team Rocket operates in the Mart backroom. A discreet cipher appears beneath the Tab [4] counter (`🕶️ [A faint "R" is etched beneath the counter. Type 'black']`).
  - **Slot Machine Secret Passage**: Bribing the Grunt behind the Game Corner slot machine poster (`poster` -> `bribe`) opens a temporary backroom session. Returning via `back` returns directly to the slot machines without unlocking the Tab [4] Mart entrance.
- **Subtle Clues**: In-game rumors dynamically appear (~10% chance) in the Slot Machine room and Black Market status screens hinting at underground access.

### 4.6 Team Rocket Covert HQ (Tab [12])
- **Dynamic Frequency Signal**: Broadcasts on encrypted frequency `131.55` as `[12] Secure Comm` when milestone thresholds are reached. Accepting the alliance (`accept`) unlocks full `[12] Rocket HQ`.
- **10 Covert Operations (`ops`)**: Mission directives from Commander Petrel tracking multi-objective milestones (token burn, expeditions, battle wins, bank CDs, companion happiness, and syndicate boss battles). Deployed via `start operation <num>` with tactical briefings (`briefing`).
- **Tactical Boss Combat Arena (`rocket_battle.py`)**:
  - Enter the combat arena via `engage` or `fight` when an operation confrontation is active.
  - Battle experimental bosses (e.g. `Prototype Chimera-001`) with dynamic elemental stance cores (Fire, Ice, Electric, Water).
  - Boss health and remaining percentages persist across turns, battle retreats, and game restarts (`ops_st["boss_hp_remaining"]`).
  - Directional front-sprite horizontal flipping (`flip_h=True`) dynamically faces your companion toward the enemy when back sprites are missing.
- **10 Classified Intel Dossiers (`intel`)**: Decrypted archives #001 to #010 covering Syndicate origins, Silph Co. infiltration, Mewtwo cloning, and shadow energy. Features 5-item pagination (`n`, `p`, `page <num>`) and terminal reading (`read <num>`).
- **Covert Armory (`armory`)**: Illicit syndicate equipment (Shadow Elixirs, Overclock Chips, Rocket Master Balls) unlocked by clearance rank.
- **5 Clearance Ranks**: Ranks progress from `Informant` ➔ `Operative` ➔ `Special Agent` ➔ `Executive` ➔ `Commander` based on completed operations.

### 4.7 Lifetime Token Milestones & Compact Displays
- **Milestone Tracking**: Tracks cumulative coding milestones (1M, 5M, 10M, 25M, 50M, 100M+ tokens) with HUD celebration banners and item rewards.
- **Egg Hatch Celebrations**: Egg hatching triggers congratulatory milestone banners in Tab [1].
- **Compact Incubation Display**: Incubation progress line formatted strictly under 72 columns (`Incubating: [███░░░░░░░░░░░░░░░░░] 13.2% (197.6K / 1.5M)`), preventing terminal wrapping.

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
Always run tests using `pytest` or Python's `unittest` runner with state isolation:
```bash
PTB_STATE_FILE=/tmp/ptb_test.json pytest tests/
```
or with unittest:
```bash
PTB_STATE_FILE=/tmp/ptb_test.json python -m unittest discover tests
```

The test suite contains **110 passing unit and integration tests** verifying sprite rendering, economy calculations, repossession waterfall, stock cycle transitions, Red battle logic, tactical boss combat, CD criteria sorting, and TUI 72-column formatting constraints.

### Adding a New TUI Command
1. If the command belongs to an existing submode (e.g. Expeditions, Stocks, Minigames, Rocket HQ), handle it in the appropriate conditional block in `PokeTokenBarTUI.run()`.
2. Add necessary engine methods in `CompanionEngine` or specific sub-engines.
3. Ensure user-facing feedback messages (`self.message`) fit cleanly within 72 columns.
4. Add unit test coverage in `tests/test_companion.py`.
