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

Execute the unittest suite across all game modules:

```bash
python3 -m unittest discover tests
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

Launch the full interactive 8-tab TUI:

```bash
ptb
```

### Verification Criteria:
1. **Width**: Ensure all headers, tab bars, progress bars, and footer messages fit within **72 character columns** without line wrapping.
2. **Tab Alignment**: Verify Tab `[7] Live Monitor` is vertically aligned with Tab `[3] Shop & Bag` at column index 34.
3. **Expeditions & Selection**: Verify `send 570 silver` dispatches species #570 on expedition, and that dispatched companions cannot be selected as active until returned.

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
