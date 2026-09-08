---
name: ptb-testing
description: >-
  Testing methodology, state isolation practices, layout regression verification, and pre-release runbook for PokeTokenBar.
---

# 🧪 PokeTokenBar Testing & Quality Verification Guide

This guide outlines the testing philosophy, automated test execution, layout compliance verification, and pre-release validation for PokeTokenBar.

---

## 1. Test Suite Execution & State Isolation

All unit tests must run with state isolation to prevent reading or mutating the user's real `~/.poketokenbar/state.json`.

```bash
# Recommended pytest execution:
/opt/anaconda3/bin/pytest tests/

# Standard unittest execution with isolated state file:
PTB_STATE_FILE=/tmp/ptb_test.json python3 -m unittest discover tests
```

### State Isolation Best Practices:
- In test classes, define `setUpClass` and `tearDownClass` using `tempfile.TemporaryDirectory()`.
- Set `os.environ["PTB_STATE_FILE"] = str(temp_state_path)` before initializing any engines.
- Clean up environment variables in `tearDownClass`.

---

## 2. Layout & Terminal Width Verification

PokeTokenBar enforces a strict **72-column terminal width** limit across all rendered output to avoid line-wrapping on standard terminal configurations.

### Verification Runbook:
- Automated regression test: `test_72_column_layout_compliance` in `tests/test_companion.py`.
- Strips ANSI escape sequences (`re.compile(r'\x1b\[[0-9;]*[mK]')`) and verifies `len(clean_line) <= 72` on every single line rendered across all 11 tabs and sub-views.
- When creating or modifying tab renderers, always verify that dynamic values (tokens, long species names, formatted badges) fit within 72 columns even at maximum width values.

---

## 3. Pre-Release Verification Runbook

Before committing a release or tagging a new version:
1. **Run Full Test Suite**: Verify zero failures or regressions (`pytest tests/`).
2. **CLI Smoke Test**: Verify CLI subcommands run without uncaught exceptions:
   ```bash
   ptb status
   ptb card
   ptb dex
   ptb shop
   ```
3. **Interactive TUI Smoke Test**: Launch `ptb`, cycle through tabs (1-11), test navigation (`n`/`p`), and exit cleanly (`q`).
4. **Git Tagging**: Follow the `ptb-git-workflow` skill for semantic version bumping and release tagging.
