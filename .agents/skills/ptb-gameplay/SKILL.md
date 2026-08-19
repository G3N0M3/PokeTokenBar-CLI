---
name: ptb-gameplay
description: >-
  Comprehensive guide for PokeTokenBar gameplay mechanics, difficulty scaling, item usage,
  companion growth, Mega Evolution, expeditions, Gym Boss raids, and Happiness/Streak systems.
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

### 3. ✨ Mega Evolution
- Eligible Species: Venusaur (#3), Charizard (#6), Blastoise (#9), Gengar (#94), Mewtwo (#150), Lucario (#448).
- **Item Required**: Mega Stone 🔮 from Shop (`buy 8`).
- **Effect**: Grants glowing ANSI title and a **+50% XP Boost** on token spend!

### 4. 🗺️ Pokédex Expeditions
- Send inactive Pokédex companions on background token-burning expeditions:
  - **Viridian Forest**: 5.0M tokens ➔ 🌿 Mint
  - **Cerulean Cave**: 15.0M tokens ➔ 🍬 Rare Candy
  - **Mt. Silver**: 30.0M tokens ➔ 🍇 Golden Razz Berry
- **Command**: `send <number/species_id> [viridian/cerulean/silver]` (e.g. `send 570 silver`).

### 5. ⚔️ Mini-Trainer Auto-Battles & Gym Boss Raids
- **Auto-Battles**: Encounter AI trainers (*Youngster Joey*, *Team Rocket Grunt*, *Rival Blue*) every **2.0M tokens**. Victory awards **+2.0M Spendable Tokens**.
- **Gym Boss Raids**: Attack Gym Bosses (*Brock*, *Misty*, *Lt. Surge*, ..., *Cynthia*) by spending tokens to earn **Gym Badges** (0/10).

---

## 🛒 Item Catalog & Shop Commands

Item                 | Cost (Medium) | Effect
:------------------- | :------------ | :-------------------------------------------------------
🍬 Rare Candy        | 25.0M tokens  | Grants +15.0M XP to active companion
🌿 Mint              | 5.0M tokens   | Rerolls companion Nature
✨ Shiny Charm       | 150.0M tokens | Passive boost to 1/48 shiny odds on future egg hatches
🥚 Standard Egg      | 30.0M tokens  | Incubates new Standard Egg
🥚 Uncommon Egg      | 75.0M tokens  | Guarantees Uncommon+ egg tier
🫐 Oran Berry        | 1.0M tokens   | Restores +25% Companion Happiness
🍇 Golden Razz Berry | 5.0M tokens   | Boosts shiny odds on NEXT egg hatch to 1/24!
🔮 Mega Stone        | 50.0M tokens  | Mega Evolves eligible final-form companions
