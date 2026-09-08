---
name: ptb-testing
description: >-
  Runbook for executing unit tests, validating CLI commands, testing TUI 72-column layout rendering,
  and performing release verification for PokeTokenBar.
---

# 🧪 PokeTokenBar Testing & Release Verification Guide

This skill provides step-by-step instructions for running test suites, verifying CLI commands, testing layout width, and releasing updates.

---

## 1. Running Unit Tests

Execute the test suite with state isolation:

```bash
# Recommended pytest runner:
/opt/anaconda3/bin/pytest tests/

# Or standard unittest runner with temp state file:
PTB_STATE_FILE=/tmp/ptb_test.json python3 -m unittest discover tests
```

---

## 2. CLI Commands Testing Checklist

Test each CLI subcommand to verify expected output format:

```bash
# 1. Check compact 1-line status banner (includes Happiness & Streak)
ptb status

# 2. Check Trainer Card ASCII generation
ptb card

# 3. Check Pokédex archive listing
ptb dex

# 4. Check Shop & Bag listing
ptb shop

# 5. Check live monitor execution (CTRL+C to stop)
ptb watch --interval 2.0
```

---

## 3. TUI Layout & Fixed-Width Verification

Launch the full interactive 11-tab TUI:

```bash
ptb
```

### Verification Criteria:
1. **Strict 72-Column Width Compliance**:
   - Automated via `test_72_column_layout_compliance` in `tests/test_companion.py`.
   - Every rendered line across all tabs (Companion, Pokédex, Roster, Mart, Black Market across all 100 items, Expeditions, Battles, Quests, Mega, Game Corner, Bank & Stocks, Settings) must satisfy `len(ansi_regex.sub("", line)) <= 72`.
2. **Dual Black Market Entrances**:
   - Verify Mart Tab [4] shows discreet cipher `🕶️ [A faint "R" is etched beneath the counter. Type 'black']` only when `natural_open == True`.
   - Verify Game Corner Tab [9] poster bribe session decouples cleanly from Mart alley door.
3. **Stock Market & Pagination**:
   - Verify Bank Tab [10] Exchange paginates stocks (Page 1/2) with `next`/`prev`.
4. **Expeditions & Selection**:
   - Verify `send <id> <dest>` or `pick` dispatches companions without allowing active selection until returned.

---

## 4. Release Checklist (Version Bump)

When releasing a new version (e.g. `v1.1.0`):

1. **Update Version Strings**:
   - `setup.py`: `version="1.1.0"`
   - `pyproject.toml`: `version = "1.1.0"`
   - `poketokenbar/__init__.py`: `__version__ = "1.1.0"`

2. **Commit & Tag**:
   ```bash
   git add setup.py pyproject.toml poketokenbar/ README.md
   git commit -m "chore(release): bump version to 1.1.0"
   git tag -a v1.1.0 -m "PokeTokenBar v1.1.0 Release"
   git push && git push --tags
   ```
