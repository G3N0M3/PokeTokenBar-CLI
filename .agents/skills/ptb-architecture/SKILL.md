---
name: ptb-architecture
description: >-
  Developer architecture guide for PokeTokenBar CLI & TUI codebase layout, state storage schema,
  tracker log parsers, sprite rendering, and game engine internals.
---

# 🏗️ PokeTokenBar Architecture Guide

PokeTokenBar is built with Python 3.8+ using standard libraries and zero heavy dependencies.

---

## 📁 Module Breakdown

Directory / File                      | Description
:----------------------------------- | :---------------------------------------------------------------------
`poketokenbar/cli.py`                 | CLI entry point (`ptb`, `ptb status`, `ptb watch`, `ptb card`)
`poketokenbar/tui.py`                 | Interactive 11-tab Linux CLI TUI event loop & orchestrator (72-col fixed width)
`poketokenbar/tui_tabs/`              | Modular tab renderers (`companion`, `pokedex`, `roster`, `shop`, `expeditions`, `red`, `quests`, `mega`, `game_corner`, `bank`, `settings`)
`poketokenbar/sprite_renderer.py`     | PNG to 24-bit TrueColor ANSI terminal sprite renderer
`poketokenbar/game/companion.py`      | Game engine (`CompanionEngine`), hatch, evolution, raids, expeditions
`poketokenbar/game/models.py`         | Data models (`MonState`, `Rarity`, `ItemKind`, `PokemonBalance`, `DifficultyMode`)
`poketokenbar/game/black_market.py`   | 100-item contraband pool, trove unpackers, crate drop tables, counterfeit fraud checks
`poketokenbar/game/stock_market.py`   | Corporate Stock Exchange engine (Silph, Devon, Aether, Mauville, Macro Cosmos)
`poketokenbar/game/red_battle.py`     | Turn-based RPG Mt. Silver Summit battle engine vs Trainer Red & Arceus
`poketokenbar/game/storage.py`        | Persistent JSON state manager (`~/.poketokenbar/state.json`)
`poketokenbar/game/pokeapi.py`        | PokéAPI local caching & sprite fetcher (`~/.poketokenbar/cache/`)
`poketokenbar/tracker/manager.py`     | Multi-source log tracker aggregator
`poketokenbar/tracker/antigravity.py` | Antigravity CLI SQLite DB parser (`~/.gemini/antigravity-cli/conversations/*.db`)
`poketokenbar/tracker/gemini.py`      | Gemini CLI JSON log parser (`~/.gemini/tmp/**/chats/*.json*`)
`poketokenbar/tracker/claude.py`      | Claude Code JSONL log parser (`~/.claude/projects/**/*.jsonl`)
`tests/test_companion.py`             | Comprehensive test suite for game mechanics, stock engine, and 72-col layout

---

## 💾 State Persistence Schema (`~/.poketokenbar/state.json`)

Key                   | Type            | Description
:-------------------- | :-------------- | :------------------------------------------------------------
`active_mon`          | `Dict / None`   | Serialized `MonState` dictionary of currently active mon
`dex`                 | `List[Dict]`    | List of registered Pokédex species entries
`incubating_eggs`     | `Dict`          | Tier to egg usage map (cleared on hatch)
`pending_eggs`        | `List[str]`     | Overflow egg queue awaiting incubation upon graduation
`inventory`           | `Dict[str,int]` | Bag inventory counts (`rare_candy`, held items, mega stones, fakes)
`spent_tokens`        | `int`           | Lifetime spent tokens (used to calculate spendable balance)
`used_since_install`  | `int`           | Lifetime total tokens indexed from log files
`streak_days`         | `int`           | Active daily coding streak in days
`happiness`           | `int` (0..100)  | Companion happiness percentage
`gym_badges`          | `List[str]`     | Earned gym badges list
`expeditions`         | `List[Dict]`    | Active background expeditions
`black_market`        | `Dict`          | `{"is_open": bool, "natural_open": bool, "deals": list, "deals_date": str}`
`stock_market`        | `Dict`          | Corporate exchange state (`prices`, `price_history`, `cost_basis`, `daily_catalysts`)
`investments`         | `Dict[str,int]` | Corporate shares owned (`silph`, `devon`, `aether`, etc.)
`cds`                 | `List[Dict]`    | Active Certificate of Deposit term contracts
`trainer_battles`     | `Dict`          | Auto-battle record `{"wins": int, "losses": int}`
`battle_logs`         | `List[str]`     | Recent auto-battle log strings (last 5 fights)
`golden_razz_active`  | `bool`          | Active shiny odds boost flag (1/24 on next hatch)

---

## 📐 Layout Constraints
- **Terminal Width**: The TUI is formatted to a strict **72-character fixed width** (`len(ansi_regex.sub("", line)) <= 72`).
- **Dividers**: Always use `"=" * 72` or `"-" * 72`.
- **Progress Bars**: Default width set to `12` or `14` columns to prevent text line wrapping.
- **Color Codes**: Use standard ANSI TrueColor or standard 16-color ANSI escapes with reset codes.
