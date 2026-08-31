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

### 3. 🎲 Token Video Poker (Tab [9])
- Bet spendable tokens (`bet 500k`, `bet 1m`) to win high multiplier token payouts!
- Paytable:
  - Royal Flush: 250x | Straight Flush: 50x | Four of a Kind: 25x
  - Full House: 12x | Flush: 8x | Straight: 5x
  - Three of a Kind: 3x | Two Pair: 2x | Jacks or Better: 1x
- Command: `bet <amount>`, then `hold 1 3 5` (or `hold none` / `hold all`).

### 4. 🔮 Gacha Capsule Machine (Tab [10])
- Pull capsules for 5.0M tokens (`pull 1`) or 45.0M tokens (`pull 10` - 10% discount!).
- Drop Table:
  - 🌟 Legendary (2%): Guaranteed Shiny Companion / +50M Tokens
  - ✨ Epic (8%): Shiny Charm ✨, Rare Egg 🥚 Tier
  - 🔮 Rare (15%): Standard/Uncommon Eggs 🥚, Mega Stone 🔮
  - 🍬 Uncommon (30%): Rare Candy 🍬, Golden Razz Berry 🍇, +3M Tokens
  - 🫐 Common (45%): Oran Berry 🫐, Mint 🌿, +1M Tokens

### 5. ✨ Mega Evolution
- Eligible Species: Venusaur (#3), Charizard (#6), Blastoise (#9), Gengar (#94), Mewtwo (#150), Lucario (#448).
- **Item Required**: Mega Stone 🔮 from Shop (`buy 8`).
- **Effect**: Grants glowing ANSI title and a **+50% XP Boost** on token spend!

### 6. 🗺️ Pokédex Expeditions (Tab [5])
- Send inactive Pokédex companions on background token-burning expeditions:
  - **Viridian Forest**: 5.0M tokens ➔ 🌿 Mint
  - **Cerulean Cave**: 15.0M tokens ➔ 🍬 Rare Candy
  - **Mt. Silver**: 30.0M tokens ➔ 🍇 Golden Razz Berry
- **Command**: `send <number/species_id> [viridian/cerulean/silver]`.

### 7. 🏔️ Mt. Silver Summit (Tab [12])
- **Unlock Condition**: Automatically unlocks and teased after defeating the Champion in Tab [6].
- **Independent Token Economy**: Unlike regular gameplay, the Red Battle uses an isolated token system. The player starts with 20,000,000 tokens, and any global tokens earned *during* the battle are added 1:1. Attacks cost Red tokens (e.g., 500K, 1.5M, etc.), protecting the player's global bank balance.
- **Battle Mechanics**:
  - Full 6v6 RPG-style turn-based battle against PKMN Trainer Red.
  - Assemble team using `assemble <id1> <id2> ... <id6>`.
  - Perform actions using `fight 1-4`, `swap 1-6`, or `run`. Red will automatically retaliate upon attacking or swapping.
- **Rewards & Hall of Fame**:
  - Defeating Red securely logs the victory and winning team into the **Hall of Fame**.
  - Awards the **Master of Masters** badge and a **Mysterious Fetal Form (Mew)**.
- **Arceus Easter Egg**:
  - If the player challenges Red using his exact iconic team (`25`, `196`, `143`, `3`, `6`, `9` in any order) and wins, they trigger a secret battle against **Arceus** (5,000,000 HP).
  - Winning this secret battle grants Arceus directly into the roster. Losing forces the player to start the Red gauntlet over.
