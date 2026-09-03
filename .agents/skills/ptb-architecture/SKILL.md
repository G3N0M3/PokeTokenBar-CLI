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
`poketokenbar/tui.py`                 | Interactive 11-tab Linux CLI TUI interface (72-character fixed width)
`poketokenbar/sprite_renderer.py`     | PNG to 24-bit TrueColor ANSI terminal sprite renderer
`poketokenbar/game/companion.py`      | Game engine (`CompanionEngine`), hatch, evolution, raids, expeditions
`poketokenbar/game/models.py`         | Data models (`MonState`, `Rarity`, `ItemKind`, `PokemonBalance`)
`poketokenbar/game/storage.py`        | Persistent JSON state manager (`~/.poketokenbar/state.json`)
`poketokenbar/game/pokemon_api.py`   | PokéAPI local caching & sprite fetcher (`~/.poketokenbar/cache/`)
`poketokenbar/tracker/manager.py`     | Multi-source log tracker aggregator
`poketokenbar/tracker/antigravity.py` | Antigravity CLI SQLite DB parser (`~/.gemini/antigravity-cli/conversations/*.db`)
`poketokenbar/tracker/gemini.py`      | Gemini CLI JSON log parser (`~/.gemini/tmp/**/chats/*.json*`)
`poketokenbar/tracker/claude.py`      | Claude Code JSONL log parser (`~/.claude/projects/**/*.jsonl`)
`tests/test_companion.py`             | Unittest test suite for game mechanics

---

## 💾 State Persistence Schema (`~/.poketokenbar/state.json`)

Key                   | Type            | Description
:-------------------- | :-------------- | :------------------------------------------------------------
`active_mon`          | `Dict / None`   | Serialized `MonState` dictionary of currently active mon
`dex`                 | `List[Dict]`    | List of registered Pokédex species entries
`incubating_eggs`     | `Dict`          | Tier to egg usage map (cleared on hatch)
`inventory`           | `Dict[str,int]` | Bag inventory counts (`rare_candy`, `berry_oran`, etc.)
`spent_tokens`        | `int`           | Lifetime spent tokens (used to calculate spendable balance)
`used_since_install`  | `int`           | Lifetime total tokens indexed from log files
`streak_days`         | `int`           | Active daily coding streak in days
`happiness`           | `int` (0..100)  | Companion happiness percentage
`gym_badges`          | `List[str]`     | Earned gym badges list
`expeditions`         | `List[Dict]`    | Active background expeditions
`trainer_battles`     | `Dict`          | Auto-battle record `{"wins": int, "losses": int}`
`battle_logs`         | `List[str]`     | Recent auto-battle log strings (last 5 fights)
`golden_razz_active`  | `bool`          | Active shiny odds boost flag (1/24 on next hatch)

---

## 📐 Layout Constraints
- **Terminal Width**: The TUI is formatted to a strict **72-character fixed width**.
- **Dividers**: Always use `"=" * 72` or `"-" * 72`.
- **Progress Bars**: Default width set to `12` or `14` columns to prevent text line wrapping.
