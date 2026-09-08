---
name: ptb-gameplay
description: >-
  Comprehensive guide for PokeTokenBar gameplay mechanics, difficulty scaling, item usage,
  companion growth, Mega Evolution, expeditions, Gym Boss raids, Token Poker, Gacha Capsules, and Happiness/Streak systems.
---

# 🐾 PokeTokenBar Gameplay System Guide

PokeTokenBar turns your AI coding token usage into a Pokémon companion game inside your Linux CLI terminal.

---

## 🎮 Core Game Systems

### 1. Companion Growth & Evolution
- **Incubation Threshold**: 1.5M tokens (Medium mode default).
- **Evolution Stages**: Form 1 ➔ Form 2 ➔ Final Form.
- **Graduation**: Max form companions graduate to the Pokédex (`[GRADUATED]`). Spent tokens on maxed companions generate spendable shop currency (`available_tokens`).

### 2. Happiness & Coding Streaks
- **100% Happiness Bonus**: Grants a **+20% Bonus XP Boost** on all token usage.
- **Happiness Decay**:
  - Missed coding days: **-25% Happiness** per missed day.
  - Battle loss: **-10% Happiness**.
- **Restoring Happiness**:
  - Daily coding activity: **+10% Happiness**.
  - **Oran Berry 🫐**: Restores **+25% Happiness**.

### 3. 🎰 Celadon Game Corner (Tab [9])
- **Video Poker (`play 1`)**:
  - Bet spendable tokens (`bet 500k`, `bet 1m`) to win high multiplier token payouts.
  - Paytable: Royal Flush (250x), Straight Flush (50x), 4 of a Kind (25x), Full House (12x), Flush (8x), Straight (5x), 3 of a Kind (3x), Two Pair (2x), Jacks or Better (1x).
  - Commands: `hold 1 3 5`, `hold none`, `hold all`.
- **Gacha Capsule Machine (`play 2`)**:
  - Pull capsules for 5.0M tokens (`pull 1`) or 45.0M tokens (`pull 10` - 10% discount).
  - Drop Table: 🌟 Legendary (2%), ✨ Epic (8%), 🔮 Rare (15%), 🍬 Uncommon (30%), 🫐 Common (45%).
- **Token Slot Machines (`play 3`)**:
  - Spin reels (`spin 250k`, `spin 500k`) with 20-frame ANSI animation.
  - Matching symbols: 🍒 2x, 🍋 5x, 🍇 10x, 🍉 20x, 🔔 50x, 💎 100x, ⭐ 250x (Triple 7s).
- **Blackjack 21 (`play 4`)**:
  - Classic casino dealer vs player blackjack: `bet <amount>`, `hit`, `stand`, `double`.
- **Secret Poster Switch**:
  - Typing `poster` while playing Slots reveals a suspicious switch guarded by a Team Rocket Grunt.
  - Bribing the Grunt (`bribe`) pays a daily toll (1M–5M) to enter the Black Market backroom session.

### 4. 🕶️ Rocket Syndicate Underground Black Market (Tabs [4] & [9])
- **7 Daily Contraband Deals from 100-Item Pool**:
  - Drawn without replacement each day from a curated 100-item contraband pool across 9 categories.
- **Sealed Troves & Contraband Crates**:
  - Troves (e.g. `Evolution Stone Trove (3x) [SEALED]`) and Mystery Crates (`Rocket Black Box`, `Smuggler's Safe`) keep contents concealed in listings; drop tables unpack upon purchase.
- **Counterfeit & Fraud Items**:
  - 12 scam items (e.g. rock candy Rare Candies, cardboard Master Balls, chalk stones). Inspecting or using reveals a humorous scam message and consumes the item.
- **Decoupled Dual Entrances**:
  - **Natural 5% Daily Chance**: Opens Tab [4] Mart alley door with discreet cipher: `🕶️ [A faint "R" is etched beneath the counter. Type 'black']`.
  - **Slot Machine Grunt Bribe**: Backroom session accessible via Tab [9] (`bribe`). Typing `back` returns to the slot machines without unlocking Tab [4].
- **Exclusive Gear & Consumables**:
  - Combat items: `choice_specs`, `focus_sash`, `rocky_helmet`, `assault_vest`, `heavy_boots`, `compass_of_deep`.
  - Consumables: `revitalizing_tonic` (100% hap), `sacred_ash` (Mt. Silver roster revive), `warp_whistle` (finishes active expeditions), `expedition_insurance`, `rocket_radar`.
  - Syndicate evolution artifacts: `metal_coat`, `kings_rock`, `dragon_scale`, `upgrade`, `dubious_disc`, `protector`, `electirizer`, `magmarizer`, `reaper_cloth`, `prism_scale`.
  - Special eggs: Fossil base species, Dragon, Starter, Paradox (1/32 shiny odds), Shadow Fetal.

### 5. 🏦 Bank of Kanto & Corporate Exchange (Tab [10])
- **Subtab `b` — Checking Account**:
  - View lifetime tokens, spendable balance, and deposit history.
- **Subtab `c` — Certificates of Deposit (CD)**:
  - Lock tokens for 3, 7, or 14 days (`cd open <amount> <days>`) to earn guaranteed interest yields.
  - Early termination (`cd break <id>`) incurs penalty forfeiture.
- **Subtab `s` — Dynamic Stock Exchange**:
  - Trade shares of 5 Pokémon megacorporations:
    - **SILPH** (Silph Co. — Tech & Master Balls)
    - **DEVN** (Devon Corp. — Mining & Automation, grants -10% mart discount at 1+ shares)
    - **ATHR** (Aether Foundation — Biotech & Preservation)
    - **MAUV** (Greater Mauville Holdings — Energy & Infrastructure)
    - **MCRO** (Macro Cosmos — Heavy Industry & Dynamax)
  - Mechanics: Dynamic daily catalyst headlines, real-time prices, 10% spread, cost basis tracking, and realized P&L.
  - Commands: `stock <idx|sym>`, `buy <qty>`, `sell <qty>`, `divest <code> <shares|all>`.

### 6. ✨ Mega Evolution & Primal Reversion (Tab [8])
- Eligible Species: Venusaur (#3), Charizard (#6 X/Y), Blastoise (#9), Gengar (#94), Mewtwo (#150 X/Y), Lucario (#448), Rayquaza (#384), Kyogre (#382), Groudon (#383).
- **Activation**: Equip corresponding Mega Stone or Primal Orb; use `toggle` or `use mega_stone_<id>`.
- **Effect**: Custom TrueColor glowing ANSI title and **+50% XP Boost** on all coding tokens.

### 7. 🗺️ Pokédex Expeditions (Tab [5])
- Dispatch inactive Pokédex companions on background token-burning expeditions:
  - **Viridian Forest**: 5.0M tokens ➔ 🌿 Mint
  - **Cerulean Cave**: 15.0M tokens ➔ 🍬 Rare Candy
  - **Mt. Silver**: 30.0M tokens ➔ 🍇 Golden Razz Berry
  - **Spear Pillar**: 100.0M tokens + 3x Map Fragments ➔ Legendary Egg
- Commands: `send <id> <dest>`, `pass <id>` (Expedition Pass instant completion), or interactive picker `pick`.

### 8. 🏔️ Mt. Silver Summit (Tab [6] Battles)
- **Unlock Condition**: Automatically unlocks after defeating the 10 Gym Bosses.
- **Independent Token Economy**: Starts with 20M Red battle tokens; real-time coding adds tokens 1:1. Attacks consume battle tokens, leaving global bank balances intact.
- **Turn-Based RPG Mechanics**:
  - Full 6v6 battle against PKMN Trainer Red. Commands: `fight 1-4`, `swap 1-6`, `run`, `restart`.
  - Victory grants **Hall of Fame** induction, **Master of Masters** badge, and a **Mysterious Fetal Form (Mew)**.
  - **Arceus Easter Egg**: Defeating Red using his exact iconic team (`25`, `196`, `143`, `3`, `6`, `9`) triggers the secret 5,000,000 HP **Arceus Raid**.
