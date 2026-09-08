---
name: ptb-gameplay
description: >-
  Developmental process, design philosophy, and core progression systems for PokeTokenBar gameplay.
---

# 🐾 PokeTokenBar Gameplay Design & Developmental Guide

This guide describes the core game design philosophy, progression loop, and conventions for developing gameplay features in PokeTokenBar.

---

## 1. Core Progression Loop

PokeTokenBar translates developer coding activity into a Pokémon companion RPG through a two-stage loop:

1. **Passive Token Harvesting**:
   - Coding token usage is continuously read from local LLM log files (Antigravity, Gemini, Claude).
   - Accrued tokens drive passive milestones: Egg incubation, companion growth stages, happiness scaling, and graduation to the Pokédex.
2. **Active Gameplay & Token Economy**:
   - Graduated companions and coding milestones unlock spendable token currency.
   - Players reinvest tokens into Shop items, Gym raids, expeditions, bank investments, or Game Corner minigames.

---

## 2. Gameplay Subsystems Architecture

When designing or extending gameplay features, follow the patterns established across the core subsystems:

### A. Companion Growth & Life Cycle
- **Incubation & Evolution**: Companions progress through multi-stage evolutionary lines based on difficulty thresholds.
- **Happiness & Streaks**: Daily coding activity maintains happiness, granting bonus multipliers. Missed days or battle losses cause gradual decay.
- **Roster & Graduation**: Max-tier companions graduate to the Pokédex archive, freeing active slots while contributing to lifetime progression.

### B. Economy & Token Sinks
- **Difficulty Scaling**: Balance all prices and thresholds across difficulty tiers (`SPEED`, `EASY`, `MEDIUM`, `HARD`, `ORIGINAL`).
- **Spendable vs Lifetime Balance**: Lifetime tokens measure career progress; spendable tokens serve as liquid in-game currency.
- **Risk & Reward**: Minigames (Game Corner, Stock Exchange, Black Market) offer high-stakes token sinks with proportional rewards.

### C. Combat & Encounters
- **Gym Boss Raids**: Cooperative token-burning damage checks that unlock regional badges.
- **RPG Battle Gauntlets (Mt. Silver)**: Turn-based battles utilizing isolated combat economies to prevent draining global bank balances.
- **Special Encounters**: Secret battle triggers (e.g. iconic team combinations) reward rare legendary companions.

### D. Expeditions & Passive Yields
- **Background Dispatches**: Inactive roster companions can be deployed on timed expeditions to gather rare items, eggs, and tokens.
- **State Guarding**: Dispatched companions are locked from active selection until recalled or completed.

---

## 3. Gameplay Feature Development Guidelines

When implementing new gameplay mechanics:
- **Simple Command Model**: Keep input commands terse and natural (e.g., `<verb> <target> [qty]`).
- **Immediate Feedback**: Every player action must return a clear boolean status and user-facing feedback message.
- **Non-blocking Execution**: Gameplay logic must never block the main TUI render loop with long synchronous operations.
- **Theme Consistency**: Maintain the retro Pokémon aesthetic paired with subtle developer/coding humor.
