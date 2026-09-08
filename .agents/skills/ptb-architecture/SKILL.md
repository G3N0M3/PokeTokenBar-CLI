---
name: ptb-architecture
description: >-
  Developer architecture guide for PokeTokenBar: system layering, data flow, state persistence principles, and development workflow.
---

# 🏗️ PokeTokenBar Architecture & Development Process Guide

PokeTokenBar is built with Python 3.8+ using pure standard libraries and zero heavy dependencies (no curses, urwid, or heavy frameworks).

---

## 1. System Layering & Data Flow

```text
[Coding Activity / IDE Logs]
          │ (SQLite DBs & JSONL logs)
          ▼
┌──────────────────────────────────────┐
│ 1. Tracker Layer (poketokenbar/tracker)
│    Parses Antigravity, Gemini, Claude
└──────────────────┬───────────────────┘
                   │ Token deltas & active days
                   ▼
┌──────────────────────────────────────┐
│ 2. Game Engine Layer (poketokenbar/game)
│    CompanionEngine, models, storage,
│    sub-engines (stocks, casino, raids)
└──────────┬───────────────────┬───────┘
           │ State persistence │ Cache & sprites
           ▼                   ▼
    [~/.poketokenbar/    [~/.poketokenbar/
       state.json]            cache/]
           │
           ▼
┌──────────────────────────────────────┐
│ 3. Presentation Layer (poketokenbar/tui)
│    TUI orchestrator & modular tui_tabs/
│    72-column ANSI terminal rendering
└──────────────────────────────────────┘
```

### Layer Responsibilities:
1. **Tracker Layer (`tracker/`)**:
   - Discovers and parses local LLM usage logs without locking files.
   - Computes lifetime totals, daily active sessions, and burn rates.
2. **Game Engine Layer (`game/`)**:
   - `CompanionEngine`: Central state orchestrator for hatch, growth, happiness, quests, expeditions, and inventory.
   - Subsystem engines: Dedicated modules for discrete domains (`black_market.py`, `stock_market.py`, `red_battle.py`, casino engines).
   - `models.py`: Immutable enums, balance formulas, and data classes.
   - `storage.py`: Atomic read/write of game state with schema fallback.
   - `pokeapi.py`: Lazy HTTP client with local filesystem caching.
3. **Presentation Layer (`tui.py`, `tui_tabs/`, `cli.py`)**:
   - `tui.py`: Central event loop handling keyboard inputs and frame dispatching.
   - `tui_tabs/`: Isolated renderers for each of the 11 tabs, ensuring strict separation of rendering from business logic.
   - `sprite_renderer.py`: Converts PNGs to ANSI TrueColor half-blocks (`▀` / `▄`).

---

## 2. State Design & Persistence Principles

- **Single Source of Truth**: All game progress is stored in a single JSON document at `~/.poketokenbar/state.json`.
- **Schema Evolution & Backward Compatibility**:
  - Always provide sensible fallback defaults in `StorageManager.default_state()`.
  - When loading state, never assume keys exist; use `.get()` with safe defaults or run migration routines during `CompanionEngine.__init__`.
- **Test State Isolation**:
  - `StorageManager` checks the `PTB_STATE_FILE` environment variable.
  - Tests set this variable to temporary files, ensuring test runs never mutate player save data.

---

## 3. Feature Development Workflow

When adding or extending features:
1. **Model**: Define new items, enums, or balance curves in `models.py`.
2. **Logic**: Add state mutation methods in `companion.py` or a dedicated game sub-engine.
3. **Persistence**: Ensure state changes are recorded and saved through `self.save()`.
4. **UI**: Render new interface elements in the appropriate `tui_tabs/<tab>.py` module.
5. **Input**: Wire command parsing in `tui.py`.
6. **Constraints**: Verify strict $\le 72$-column formatting (`len(strip_ansi(line)) <= 72`).
7. **Test**: Write isolated unit tests in `tests/test_companion.py`.
