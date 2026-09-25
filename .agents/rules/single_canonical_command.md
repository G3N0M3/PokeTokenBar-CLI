# Rule: Single Canonical Command Policy

## Core Principle
Every system function, game mechanic, menu selection, or user action in PokeTokenBar MUST map to **exactly one canonical command**.

---

## Strict Guidelines

1. **Zero Redundant Command Aliases**:
   - Never implement multiple alternative keywords, synonyms, or abbreviations for the same underlying function.
   - Choose one clear, canonical keyword and reject all other alternative spellings or synonyms.
   - **Correct**: Only `dig` to start excavation.
   - **Incorrect**: Accepting both `dig` and `mine`.
   - **Correct**: Only `flip <r> <c>` to reveal cards.
   - **Incorrect**: Accepting both `flip` and `f`.
   - **Correct**: Only `pick <r> <c>` and `hammer <r> <c>`.
   - **Incorrect**: Accepting single-letter aliases `p` or `h`.
   - **Correct**: Only `use mist`, `use chrono`, and `use catalyst` in the Covert Armory.
   - **Incorrect**: Accepting numeric alternatives like `use 2`, `use 3`, or `use 5`, or verbose synonyms like `requisition catalyst`.
   - **Correct**: Only `race` to launch the stadium derby.
   - **Incorrect**: Accepting both `race` and `start`.
   - **Correct**: Only `giveup` to forfeit trivia.
   - **Incorrect**: Accepting both `giveup` and `pass`.
   - **Correct**: Only `fight` to enter tactical boss combat in Team Rocket Operations.
   - **Incorrect**: Accepting both `engage` and `fight`.

2. **Menu Selection**:
   - In submenus and Game Corner, each game or option has exactly one index/canonical name (e.g. `play 5` or `play voltorb`). Avoid registering long lists of informal aliases (`quiz`, `silhouette`, `mine`, `dig`, `stadium`).

3. **Documentation Consistency**:
   - All TUI in-tab hint lines, `--help` strings, and `README.md` command reference tables must teach and display only the canonical command.
   - Single canonical command enforcement keeps the CLI interface clean, unambiguous, predictable, and easy to maintain.
