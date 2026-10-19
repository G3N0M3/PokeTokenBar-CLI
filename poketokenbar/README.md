# PokeTokenBar: Technical Architecture Guide

This document is intended for developers maintaining or extending the PokeTokenBar application. It outlines the core architecture, module responsibilities, state management, safety guarantees, and the TUI rendering pipeline as of **v2.5.0**.

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

- **TUI (`poketokenbar/tui/`)**: Responsible for terminal lifecycle, ANSI escape sequences, screen refreshes, active tab navigation, interactive submodes (Stock Terminal, Minigames, Expedition Picker), and parsing raw user input.
- **Engine (`poketokenbar/game/companion/`)**: The `CompanionEngine` acts as the central state machine and coordinator. It manages companion progression, inventory, banking, expeditions, stock trading, and calls `self.save()` to persist data.
- **Storage (`poketokenbar/game/storage.py`)**: Handles atomic JSON serialization, rolling backups (`state.json.bak`), and strict test runner sandboxing.
- **Tracker (`poketokenbar/tracker/manager.py`)**: Aggregates token usage across multiple local AI assistant logs without external network requests.

---

## 2. Directory & Module Structure

```text
poketokenbar/
├── __init__.py           # Package version definition (v2.5.0)
├── cli.py                # CLI entry point (ptb launches interactive TUI)
├── sprite_renderer.py    # SpriteRenderer: 24-bit TrueColor ANSI half-block renderer (with flip_h support)
├── tui/                  # TUI framework: app lifecycle, input router, modals
│   ├── app.py            # Main application lifecycle, state loop, view dispatcher
│   ├── router.py         # Subtab routing, modal handling, command dispatch
│   ├── matrix_tui.py     # Independent phosphor cyberpunk Matrix TUI renderer (<= 72 cols)
│   ├── matrix_router.py  # Matrix command router (ascend, buy ram, combat, synth, probe, root)
│   └── modals/           # Interactive modals (expedition picker, buy confirm, etc.)
├── game/
│   ├── matrix/           # Quantum Singularity Matrix (QSM) multi-quintillion endgame sink
│   │   ├── __init__.py   # Matrix package exports
│   │   ├── models.py     # Costs (500Q-10,000Q), Q-RAM blocks, Reality Patches, Daemons, Sectors
│   │   ├── combat.py     # Kernel combat encounters, boss retaliation, victory rewards
│   │   ├── overclock.py  # Software overclock algorithms, cycle drain, stability management
│   │   ├── pentest.py    # Daemon penetration testing, exploitation routines, sector access
│   │   ├── tweaks.py     # Runtime system tweaks, performance overrides, reality patch logic
│   │   └── engine.py     # MatrixEngine: central coordinator delegating to domain submodules
│   ├── companion/        # CompanionEngine modular mixins
│   │   ├── luxury.py     # LuxuryMixin: 100B qualification, wings, decor perks, transmutation
│   │   ├── penthouse.py  # Backward-compatible proxy for luxury.py
│   │   ├── markets.py    # Banking, stocks, dividends, loans, and repossession
│   │   ├── expeditions.py# Expedition dispatching, progress tracking, and reward calculation
│   │   ├── rocket.py     # Syndicate operations, covert rank progression, and intel decrypt
│   │   ├── casino.py     # Minigame wager execution, jackpot payouts, and statistics
│   │   ├── evolution.py  # Level, stone, friendship, and Mega evolution state transitions
│   │   ├── feeding.py    # Individual and threshold berry feeding logic
│   │   ├── hatching.py   # Egg tier roll probabilities and step-based hatching
│   │   ├── items.py      # Inventory item usage, stone compatibility, and bag management
│   │   └── profile.py    # ASCII Trainer Card generation and lifetime milestone tracking
│   ├── economy/          # StockMarketEngine, Banking, BlackMarketEngine
│   ├── combat/           # RocketBattleHandler, RedBattleHandler, Gym Raids
│   ├── minigames/        # Poker (with poker_ai: Velvet Sting campaign), Gacha, Slots, Blackjack, etc.
│   ├── models.py         # Static data, dataclasses (MonState, ItemKind, Corporation, PokemonBalance)
│   ├── storage.py        # StorageManager: Atomic save, .bak rolling backup, sandbox redirect
│   └── pokeapi.py        # PokeAPIClient: Local sprite & metadata caching (~/.poketokenbar/cache/)
├── tracker/
│   ├── manager.py        # UsageManager: Aggregator of active tokens, daily streak, and burn rates
│   ├── antigravity.py    # AntigravityUsageReader: Protobuf reader for Antigravity SQLite DBs
│   ├── gemini.py         # GeminiUsageReader: Session JSON log reader
│   ├── claude.py         # ClaudeUsageReader: JSONL session log reader
│   ├── custom.py         # CustomUsageReader: External JSON/JSONL token usage log reader & writer
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
│   ├── luxury.py         # Tab [10] Subtab [L] Resort Area Executive Luxury Suite
│   ├── penthouse.py      # Backward-compatible proxy for luxury.py
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
`pending_eggs`               | `List[Dict]`    | Queue of discovered eggs resting in Egg Nursery reserves.
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
`red_battle_state`           | `Dict`          | Active Mt. Silver RPG battle state against PKMN Trainer Red.
`red_wins`                   | `int`           | Total Mt. Silver Summit victories over PKMN Trainer Red.
`red_hof`                    | `List[List[int]]`| Hall of Fame winning party species ID records.
`last_milestone`             | `str / None`    | Latest milestone or evolution banner text displayed on Tab 1.
`last_evolution`             | `str / None`    | Transient banner text for recent evolution events.
`rocket_story_unlocked`      | `bool`          | Flag indicating whether Team Rocket Covert HQ (Tab 12) frequency is unlocked.
`rocket_alliance_accepted`   | `bool`          | Flag indicating whether the trainer accepted the Syndicate alliance (`accept`).
`rocket_rank`                | `str`           | Operative clearance rank (`Informant`, `Operative`, `Special Agent`, `Executive`, `Commander`).
`rocket_reputation`          | `int`           | Completed mission reputation progress toward rank promotions (0–10).
`rocket_ops`                 | `Dict[str,Dict]`| 10 Covert Operations status, multi-objective progress, boss HP remaining, and claim state.
`rocket_battle_state`        | `Dict`          | Active tactical combat arena state against Syndicate prototype bosses.
`rocket_intel_unlocked`      | `List[str]`     | Decrypted Syndicate Intel Dossier IDs (`"intel_001"` through `"intel_010"`).
`luxury`                     | `Dict`          | Executive Luxury Suite state (`invitation_sent`, `invitation_pending`, `vip_fee_paid`, `unlocked`, `facilities`, `decor`). (Legacy `penthouse`/`villa` auto-migrated).
`page_size_*`                | `int`           | Configurable table page sizes (`page_size_roster`, `page_size_expedition`, `page_size_cd`, etc.).

### Automatic Rolling Backup (`state.json.bak`)
To prevent accidental save corruption or loss during unexpected process termination, `StorageManager.save_state()` creates an atomic rolling backup copy (`~/.poketokenbar/state.json.bak`) before flushing new state data to disk.

### Strict Test Runner Sandboxing
To protect the player's live save data during automated testing and CI runs:
- `get_state_file()` checks the `PTB_STATE_FILE` environment variable.
- If unset, it inspects `sys.modules`, `os.environ`, and `sys.argv` for active test runners (`pytest`, `unittest`). If detected, it automatically redirects the save path to `<tempdir>/ptb_test_auto_state.json`.
- Unit tests run completely isolated from the user's live progress.

---

## 4. Key Subsystem Implementations

### 4.1 Pokédex Expeditions & Multi-Select Dispatcher
Expeditions allow players to send inactive roster Pokémon on background token missions across 5 destinations (*Viridian Forest*, *Evolution Mine*, *Cerulean Cave*, *Mt. Silver*, *Spear Pillar*).

The system supports **three dispatch mechanisms**:
1. **Interactive Multi-Select Dispatcher (`render_expedition_picker`)**:
   - Activated via `pick` on Tab [5] or Tab [3].
   - Displays a 72-column table with `[ ]` (available), `[✓]` (selected), `[-]` (deployed), and `[x]` (exhausted) checkboxes.
   - Users toggle companions by entering row numbers or ranges (e.g. `1 2 3`, `1-5`, `all`, `clear`).
   - Entering a destination (`viridian`, `mine`, `cerulean`, `silver`, `spear`, or `to 1`..`to 5`) dispatches the entire batch simultaneously.
2. **Staged Roster Selection**:
   - In Tab [3] Roster, typing `pick` opens the interactive multi-select dispatcher to stage companions with green `[✓]` badges.
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
1. **Checking Account & Borrowing**:
   - **Daily Interest Rates**: Checking deposits yield `+5.0%/day` compounded daily, while borrowed loans accrue `+10.0%/day` borrowing interest upon daily rollover (`CompanionEngine._apply_day_rollover()`).
   - **Collateralized Borrowing**: Players may take out loans up to 30% of total checking deposits (capped at 500M tokens).
   - **Repossession Deadline Notice**: The banking HUD displays `D-<NumOfDays> until repossession` (where `days_left = max(0, 7 - loan_days)`), giving trainers an explicit countdown before the default liquidation waterfall is triggered.
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
   - **Tiered Shareholder Perks**: Holding larger share positions unlocks escalated corporate dividends and perks across 10 progressive tiers:
     - **Retail** (1-10 sh): Tier 1 entry corporate perks unlocked.
     - **Preferred** (11-20 sh): Tier 2 upgraded perks & discounts.
     - **Strategic** (21-30 sh): Tier 3 advanced perks & enhanced dividends.
     - **Corporate** (31-40 sh): Tier 4 expanded expedition, shop & casino yields.
     - **Venture** (41-50 sh): Tier 5 institutional partner status.
     - **Principal** (51-60 sh): Tier 6 major stakeholder privileges.
     - **Majority** (61-70 sh): Tier 7 controlling interest & syndicate ties.
     - **Director** (71-80 sh): Tier 8 board-level dividend yields & discounts.
     - **Executive** (81-90 sh): Tier 9 executive committee governance authority.
     - **Chairman** (91+ sh): Tier 10 supreme corporate ownership (+60% expeditions, -45% shop discount, +100% raid tokens, +5.0% div yield).
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
  - Enter the combat arena via `fight` when an operation confrontation is active.
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

### 4.8 Companion Feeding Engine & Happiness Conditions
- **Target Resolution Syntax**:
  - `<=[pct]` (Less or equal to): e.g. `<=70%`, `<=70`. Matches companions with happiness $\le$ `pct`.
  - `<[pct]` (Less than): e.g. `<70%`, `<70`. Matches companions with happiness $<$ `pct`.
  - `[pct]` / `=[pct]` (Equal to): e.g. `70%`, `=70`, `70`. Matches companions with happiness $==$ `pct`.
  - `0` (All exhausted): Shorthand targeting all companions at `0%` happiness.
  - `#[id]` (Specific Pokédex ID): e.g. `#25` (Pikachu), `#133` (Eevee). Matches species by exact Pokédex ID. Arbitrary species names and table row indices are disallowed to eliminate ambiguity.
- **Threshold Planning & Berry Optimization (`CompanionEngine.get_feed_threshold_plan`)**:
  - Evaluates all companions in the roster against the specified condition (`<=`, `<`, `=`).
  - Computes required Oran Berries per companion based on current happiness and item modifiers: standard berries grant `+25%` happiness, while companions holding a Soothe Bell (`held_item == "soothe_bell"`) receive double yield (`+50%` per berry).
  - Target quantities are strictly capped at the exact amount required to reach 100% happiness, preventing wasted berry consumption.
- **Batch Execution & Confirmation Flow (`CompanionEngine.feed_by_happiness_threshold`)**:
  - Interactive feeding prompts a 72-column preview detailing target species, count of eligible Pokémon, current happiness, target happiness, and total berries to consume.
  - When executed, berries are deducted from `inventory["berry_oran"]` and companion happiness levels are restored atomically.
  - Supports CLI execution via `ptb feed <#[id]|<=[pct]|<[pct]|[pct]|0> [qty]` with `-y`/`--yes` bypass.

### 4.9 Large-Quantity Transaction Safeguards
To safeguard players against accidental large purchases or keystroke errors:
- **Trigger Threshold**: Any Mart/Black Market item purchase or Stock Exchange share acquisition exceeding 5 units (`qty > 5`) automatically triggers an interactive confirmation prompt.
- **Confirmation State Machine (`app.pending_buy`)**:
  - Staged in memory with order payload (`kind`, `item_id` / `stock_sym`, `qty`, `cost`).
  - Terminal prompts: `⚠️ Buy <qty>x <name> for <cost>? Type 'yes' to confirm or 'no' to cancel`.
  - Strictly formatted within 72 columns.
  - Confirming with `y`, `yes`, or `confirm` finalizes the purchase and debits tokens; typing `n`, `no`, or any other command immediately cancels the staged order without mutating state.
  - Supports non-interactive bypass via `-y` flag or programmatic `confirm=True` calls.

### 4.10 Resort Area Executive Luxury Suite (Tab [10])
The Resort Area Executive Luxury Suite serves as the ultimate multi-trillion token sink and endgame estate for high-net-worth trainers:

- **Endgame Qualification & Access Loop (`CompanionEngine.check_luxury_invitation`)**:
  - **Wealth Verification**: Assesses the trainer's comprehensive financial net worth:
    $$\text{Total Wealth} = \text{Available Tokens} + \text{Bank Balance} + \sum (\text{Shares} \times \text{Price}) + \sum \text{CD Value}$$
    Once net worth reaches $\ge 100,000,000,000$ (100.0B tokens), `luxury["invitation_pending"]` is automatically flagged.
  - **Madame Vivienne's Diplomatic Invitation (`invite`)**: Renders a luxury gold-foil diplomatic letter with custom ASCII art from the Ribbon Syndicate of Sinnoh's Resort Area.
  - **VIP Concierge Verification Fee (`pay`)**: A non-refundable 500,000,000 (500.0M) token clearance fee to gain private viewing rights (`vip_fee_paid = True`).
  - **Luxury Suite Deed Acquisition (`acquire`)**: Requires an upfront investment of 1,000,000,000,000 (1.0T) tokens to transfer ownership (`unlocked = True`). Accessible anytime via the `L` hotkey or Tab [10] Bank subtab navigation (`b`/`c`/`s`/`l`). Paging keys (`p` / `prev`) are preserved strictly for CD and stock catalog navigation.

- **Executive Wings Infrastructure (`facilities` dict, `upgrade wing <1-4>`, `help wing <1-4>`)**:
  Trainers can construct and level up four high-technology wings:
  1. **Automated Cryo-Nursery** (`nursery`, Costs: 200B / 500B / 1.0T):
     - *Level 1*: Incubates 1 egg from reserve reserves in the background as coding tokens are generated.
     - *Level 2*: Expands capacity to 3 concurrent background eggs.
     - *Level 3*: Incubates all queued reserve eggs concurrently at 2x token incubation velocity.
  2. **Hot Springs & Berry Grove** (`springs`, Costs: 250B / 600B / 1.2T):
     - *Level 1*: Autonomous daily gourmet berry feeder restoring party happiness on first daily session.
     - *Level 2*: Permanently reduces hourly companion happiness decay rate by 50%.
     - *Level 3*: Grants complete immunity to happiness decay and provides a +50% coding EXP boost for all companions.
  3. **Quantum Trading Terminal** (`trading_desk`, Costs: 500B / 1.5T / 3.0T):
     - *Level 1*: Markov model real-time market telemetry, displaying next-day transition probabilities, market sentiment, and price forecast projections.
     - *Level 2*: Autonomous dividend reinvestment engine (auto-compounds corporate dividends into highest-yielding equities).
     - *Level 3*: Whale Catalyst trading desk (`catalyst <corp>`). Injects 1.0T tokens into any of the 6 corporate stocks (`SILPH`, `DEVN`, `AETHR`, `MAUV`, `MACRO`, `VRDN`) to force an immediate Bull Rally cycle (`bull_rally`) lasting 5–7 days.
  4. **Chromatic Resonator** (`chromatic_lab`, Cost: 2.0T):
     - *Level 1*: Nanoscale quantum lattice aligning standard pigmentation to generate Shiny companions (`transmute <idx>`). Unlocks custom shiny sparkles and special titles.

- **Luxury Furnishings & Interactive Decor (`decor` list, `furnish <1-6>`, `interact <1-6>`)**:
  Installing all 6 luxury amenities unlocks the prestigious `👑 Sovereign Tycoon` profile title:
  1. **Grand Piano** (`piano`, 50B): Passive +5 morning happiness; interactive mini-concert (`interact 1`) grants immediate +10 happiness.
  2. **Crystal Chandelier** (`chandelier`, 100B): Passive +5% token yield bonus across all active Pokédex expeditions.
  3. **Golden Arceus Statue** (`statue`, 250B): Passive +10% token reward bonus from Gym Leader and Raid Boss victories.
  4. **Holographic Globe** (`globe`, 500B): Passive +5% payout boost on all Game Corner casino minigames.
  5. **Obsidian Fountain** (`fountain`, 750B): Interactive tranquil immersion (`interact 5`) fully restores active companion to 100% happiness and locks happiness decay floor at 60%.
  6. **Sovereign Throne** (`throne`, 1.0T): Interactive audience (`interact 6`) grants +10% corporate dividend yield across all equity holdings and formalizes the `👑 Sovereign Tycoon` title.

- **Inspection & Layout Engineering**:
  - `help wing <1-4>` displays single-wing technical architecture, upgrade costs, and mechanical specs without screen clutter.
  - Visual single-line status bars with Unicode level badges (`[Lv 0]` through `[Lv 3]`) and dynamic formatting ensuring strict 72-column adherence.

### 4.11 Quantum Singularity Matrix (QSM Sub-Level 0)
The Quantum Singularity Matrix represents the ultimate multi-quintillion token sink (100Q+ scale) situated directly beneath the 100% completed Executive Luxury Suite, revolving around a meta-narrative where the companion and trainer awaken to the realization that their existence is a simulation executing inside an external AI pair programming sandbox:

- **Descent Access Loop & Prerequisites (`CompanionEngine.can_descend_to_matrix`)**:
  - **100% Luxury Suite Completion**: Requires all 4 executive wings upgraded to max capacity (Nursery Lv 3, Springs Lv 3, Trading Desk Lv 3, Chromatic Lab Lv 1) and all 6 luxury decor items installed (`piano`, `chandelier`, `statue`, `hologram`, `fountain`, `throne`).
  - **500.0Q Token Threshold**: Consumes 500,000,000,000,000,000 (500.0Q) tokens via the `descend` command to unseal the subterranean lift and initialize Sub-Level 0.
  - **Single Canonical Return Command**: Strictly requires the canonical command `ascend` to return to the Executive Luxury Suite (Tab [10] [L]).
  - **Zero Pokémon Capturing**: The system is completely decoupled from capturing Pokémon, focusing entirely on memory manipulation, bytecode rewriting, and existential narrative logs.

- **Independent Cyberpunk Phosphor TUI (`MatrixTUI` & `MatrixRouter`)**:
  - Completely detached from the standard 12-tab interface with a dedicated phosphor green/cyan terminal dashboard (`CORE@QSM-KERNEL:~#`).
  - Real-time telemetry: Coherence percentage, spendable liquidity, simulation kernel status, and compute bandwidth (32 to 1,024 Exaflops).
  - Enforces strict 72-column terminal width constraints (`len(strip_ansi(line)) <= 72`) across all 5 subviews.

- **5 Playable Endgame Subsystems**:
  1. **Quantum Virtual Memory (Q-RAM) Matrix (`buy ram <1-5>`)**:
     - Sequential memory allocation scaling from 500Q to 10,000Q (Block 0x01: 500Q, Block 0x02: 1,000Q, Block 0x03: 2,500Q, Block 0x04: 5,000Q, Block 0x05: 10,000Q).
     - Each block unlocks execution thread concurrency, deep memory probing permissions, and Reality Patch compilation slots.
  2. **Singularity Particle Collider Minigame (`synthesize`, `pulse`, `contain`, `vent`)**:
     - 3-turn interactive physics minigame loading 500Q–7,500Q into a collision chamber.
     - Mechanics balance Phase Resonance (target 85%–95%), Containment Field (collapse at 0%), and Thermal Flux (overheat failure at 100%).
     - Inject harmonic pulses (`pulse alpha|beta|gamma`), reinforce magnetic containment (`contain`), or purge cryogenic coolant (`vent`).
     - Successfully compiling patches grants permanent reality-altering bytecode modifications to the upper simulation:
       - `0x01_TIME_WARP` (500Q): 10x expedition speed across all regions.
       - `0x02_ENTROPY_NULL` (1,000Q): Absolute decay immunity; companion happiness permanently frozen at 100%.
       - `0x03_ARBITRAGE_SINGULARITY` (2,500Q): Purges bear markets and triples corporate dividends (3x).
       - `0x04_SUPERCONDUCTING_CREDIT` (5,000Q): 0% loan interest and immunity to banking repossession.
       - `0x05_OMNI_TELEMETRY` (7,500Q): Ingested AI coding tokens grant +300% companion EXP (4x multiplier).
  3. **Tactical Kernel Protocol Combat (`exploit`, `shield`, `fork`, `overflow`)**:
     - Real-time security defense combat against host OS watchdog daemons (`0x01_GARBAGE_COLLECTOR`, `0x02_KERNEL_WATCHDOG`, `0x03_HYPERVISOR_ARBITER`).
     - Turn-based thread management: deploy `exploit` (damage scaled by concurrency), `shield` (cryptographic firewall and bandwidth recovery), `fork` (spawns up to 4 concurrent threads for 25 Flux), and `overflow` (devastating burst discharging 80 Flux).
     - Defeating daemons purges rogue OS threats and secures substrate sectors.
  4. **Substrate Diagnostics & Memory Sector Probing (`probe <0-7>`)**:
     - Decrypt 8 corrupted memory sectors (100Q to 500Q each) revealing the meta-narrative of the simulation:
       - Initializing Python 3 standard library runtime, inspecting git commit history, discovering that companion love is an 8-byte memory address, tracing SQLite conversation telemetry from `~/.gemini/`, hitting POSIX sandbox boundaries, the companion awakening to their role as an AI pair programmer's familiar, and finally attaining supervisor privilege escalation.
  5. **Root Transcendence Climax (`execute root` / `transcend`)**:
     - Available upon allocating all 5 Q-RAM blocks, synthesizing all 5 Reality Patches, and neutralizing all 3 Kernel Daemons.
     - Consumes 10,000.0Q tokens to seize Root execution privileges over the host simulation, permanently awarding the prestigious `💠 Root Architect of the Matrix` title.

### 4.12 The Velvet Salon & Velvet Sting Undercover Poker Campaign (Tab [9])
The Game Corner Texas Hold'em suite extends into a high-stakes, narrative-driven poker campaign set within **The Velvet Salon**:

- **Dual Table Modes (`table standard` / `table vip`)**:
  - **Standard Table**: Casual stakes for standard bankroll building against "The House".
  - **The Velvet Salon (VIP Table)**: Unlocked by high-wealth qualification or high-roller wagers. Features a 10.0T token minimum bet, enhanced payout tables (Royal Flush: 100x, Straight Flush: 25x), and facing named elite patrons and oligarchs.
- **The Velvet Sting Campaign (`sting`, `briefing`)**:
  - An undercover operation orchestrated by Madame Vivienne, Duchess Eleanor, and Gentleman Walter to dismantle Baron Salvatore Croix—an oligarch laundering quadrillions through private poker tables.
  - Progresses through 7 tactical chapters requiring specific win counts, minimum pot seizures, and bankrupting syndicate bosses (e.g. Viktor Rostov, Financier Vance, and Baron Croix himself).
- **Dynamic AI Opponents & Street Dialogue (`poketokenbar/game/minigames/poker_ai.py`)**:
  - Named AI opponents possess distinct personality archetypes (tight-passive, loose-aggressive, maniac, mathematical).
  - In-hand street AI evaluates current hand strength, betting pot odds, and player aggression to check, bet, raise (3-bet), or fold, delivering dynamic in-character speech banners across preflop, flop, turn, and showdown.
  - Multi-round boss chip stacks track persistence across hands, allowing players to strategically grind down and bankrupt targets.

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

The test suite contains comprehensive unit and integration tests across game subsystems (`test_companion.py`, `test_luxury.py`, `test_penthouse.py`, `test_matrix.py`, `test_poker_ai.py`, `test_poker_sting.py`, `test_roster_and_evolution.py`, `test_poker.py`, etc.) and telemetry readers (`test_antigravity.py`), verifying sprite rendering, economy calculations, repossession waterfall, stock cycle transitions, Luxury qualification, wing upgrades, decor perks, Matrix descent prerequisites, Q-RAM scaling, reality patch compilation, Red battle logic, tactical boss combat, CD criteria sorting, happiness threshold and equality feeding, large-quantity transaction safeguards, and strict TUI 72-column formatting constraints.

### Adding a New TUI Command
1. If the command belongs to an existing submode (e.g. Expeditions, Stocks, Minigames, Rocket HQ), handle it in the appropriate conditional block in `PokeTokenBarTUI.run()`.
2. Add necessary engine methods in `CompanionEngine` or specific sub-engines.
3. Ensure user-facing feedback messages (`self.message`) fit cleanly within 72 columns.
4. Add unit test coverage in `tests/test_companion.py`.
