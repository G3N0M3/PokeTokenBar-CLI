import random
from typing import Dict, List, Optional, Tuple, Any, Union

from poketokenbar.game.models import ItemKind, Rarity, MEGA_STONES
from poketokenbar.utils.formatting import format_tokens
from poketokenbar.game.companion.evolution import TIME_BASED_BRANCH_OVERRIDES
from poketokenbar.game.economy.black_market import get_fake_item_fraud_message


class ItemsMixin:
    """Provides inventory management: purchasing, selling, equipping, and item usage."""

    def buy_item(self, item_kind: ItemKind, qty: int = 1, confirm: bool = False) -> Tuple[bool, str]:
        if qty <= 0:
            return False, "Quantity must be greater than 0!"
            
        diff = self.current_difficulty
        unit_cost = item_kind.price_for(diff)
        unit_cost = int(unit_cost * self.get_devon_multiplier())
        cost = unit_cost * qty
        
        if self.available_tokens < cost:
            return False, f"Not enough tokens! Required: {format_tokens(cost)}, Available: {format_tokens(self.available_tokens)}"

        if confirm:
            prompt = f"🛒 Buy {qty}x {item_kind.name_en} {item_kind.emoji} for {format_tokens(cost)} tokens? Type 'confirm' (or 'y')"
            if len(prompt) > 72:
                prompt = f"🛒 Buy {qty}x {item_kind.emoji} for {format_tokens(cost)} tokens? Type 'y'"
            if len(prompt) > 72:
                prompt = f"Buy {qty}x {item_kind.name_en} for {format_tokens(cost)}? [y/N]"
            if len(prompt) > 72:
                prompt = prompt[:69] + "..."
            return True, prompt

        inv = self.state.get("inventory", {})

        if item_kind == ItemKind.MEGA_STONE:
            available_stones = [s for s in MEGA_STONES.keys() if inv.get(f"mega_stone_{s}", 0) == 0]
            if not available_stones:
                return False, "You already own all available Mega Stones! (Only 1 per Mega Stone permitted)"
            if qty > 1:
                return False, "You can only purchase 1 Mega Stone at a time!"
            stone_id = random.choice(available_stones)
            stone_key = f"mega_stone_{stone_id}"
            stone_name = MEGA_STONES[stone_id]
            self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
            inv[stone_key] = 1
            self.state["inventory"] = inv
            self._record_catalyst("shop_tokens_spent", cost)
            self.save()
            return True, f"Successfully purchased 1x Mystery Mega Stone! You unboxed: 🔮 {stone_name}!"

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) + cost
        inv[item_kind.value] = inv.get(item_kind.value, 0) + qty
        self.state["inventory"] = inv
        self._record_catalyst("shop_tokens_spent", cost)
        self.save()
        return True, f"Successfully purchased {qty}x {item_kind.name_en} ({item_kind.emoji})!"

    def sell_item(self, item_kind: Union[ItemKind, str], qty: int = 1) -> Tuple[bool, str]:
        if qty <= 0:
            return False, "Quantity must be greater than 0."

        inv = self.state.get("inventory", {})

        if isinstance(item_kind, str):
            try: item_kind = ItemKind(item_kind)
            except ValueError: pass

        k = item_kind.value if isinstance(item_kind, ItemKind) else str(item_kind)
        inv = self.state.get("inventory", {})

        if k == "mega_stone" or (isinstance(item_kind, ItemKind) and item_kind == ItemKind.MEGA_STONE) or k.startswith("mega_stone_"):
            return False, "Mega Stones are unique key artifacts and cannot be sold!"

        count = inv.get(k, 0)
        if count < qty:
            return False, f"You don't have {qty}x in your Bag to sell!"

        if k.startswith("fake_"):
            sell_value = 1 * qty
            name_str = k.replace("fake_", "").replace("_", " ").title()
            emoji_str = "🪙"
        elif isinstance(item_kind, ItemKind):
            cost = item_kind.price_for(self.current_difficulty)
            sell_value = max(1, int(cost * 0.8)) * qty
            name_str = item_kind.name_en
            emoji_str = item_kind.emoji
        else:
            sell_value = 100_000 * qty
            name_str = k.replace("_", " ").title()
            emoji_str = "📦"

        inv[k] -= qty
        if inv[k] <= 0:
            del inv[k]

        self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - sell_value
        self.state["inventory"] = inv
        self.save()

        return True, f"Successfully sold {qty}x {name_str} ({emoji_str}) for +{format_tokens(sell_value)} Tokens!"

    def use_item(self, item_kind: Union[ItemKind, str], qty: int = 1) -> Tuple[bool, str]:
        if qty <= 0:
            return False, "Quantity must be greater than 0."

        if isinstance(item_kind, str):
            try: item_kind = ItemKind(item_kind)
            except ValueError: pass

        item_val = item_kind.value if isinstance(item_kind, ItemKind) else str(item_kind)
        item_name = item_kind.name_en if isinstance(item_kind, ItemKind) else item_val.replace("_", " ").title()
        item_emoji = item_kind.emoji if isinstance(item_kind, ItemKind) else "📦"

        inv = self.state.get("inventory", {})
        count = inv.get(item_val, 0)
        if count < qty:
            return False, f"You don't have enough {item_name} in your Bag!"

        active = self.active_mon

        # 1. Counterfeit / Fake items
        if item_val.startswith("fake_"):
            inv[item_val] -= 1
            if inv[item_val] <= 0: del inv[item_val]
            if item_val == "fake_soothe_bell" and active:
                active.happiness = max(0, active.happiness - 5)
                self.set_active_mon(active)
            elif item_val == "fake_gold_nugget":
                self.state["spent_tokens"] = self.state.get("spent_tokens", 0) - 1
            self.state["inventory"] = inv
            self.save()
            fraud_msg = get_fake_item_fraud_message(item_val)
            return True, f"⚠️ SCAM REVEALED! {fraud_msg}"

        # 2. Syndicate Evolution Artifacts
        elif item_val in [
            "metal_coat", "kings_rock", "dragon_scale", "upgrade",
            "dubious_disc", "protector", "electirizer", "magmarizer",
            "reaper_cloth", "prism_scale"
        ]:
            if qty > 1:
                return False, f"You can only use one {item_name} at a time!"
            if not active:
                return False, f"You need an active companion to use a {item_name}!"
            if active.held_item == "everstone":
                return False, "Your companion is holding an Everstone! It cannot evolve."

            artifact_compat = {
                "metal_coat": {95: 208, 123: 212},     # Onix -> Steelix, Scyther -> Scizor
                "kings_rock": {60: 186, 79: 199},      # Poliwhirl -> Politoed, Slowpoke -> Slowking
                "dragon_scale": {117: 230},            # Seadra -> Kingdra
                "upgrade": {137: 233},                 # Porygon -> Porygon2
                "dubious_disc": {233: 474},            # Porygon2 -> Porygon-Z
                "protector": {112: 464},               # Rhydon -> Rhyperior
                "electirizer": {125: 466},             # Electabuzz -> Electivire
                "magmarizer": {126: 467},              # Magmar -> Magmortar
                "reaper_cloth": {356: 477},            # Dusclops -> Dusknoir
                "prism_scale": {349: 350},             # Feebas -> Milotic
            }
            compat_map = artifact_compat.get(item_val, {})
            target_evo_id = compat_map.get(active.current_id)

            if not target_evo_id:
                if item_val == "metal_coat":
                    # Equip as held item
                    if active.held_item:
                        inv[active.held_item] = inv.get(active.held_item, 0) + 1
                    active.held_item = item_val
                    inv[item_val] -= 1
                    if inv[item_val] <= 0: del inv[item_val]
                    self.state["inventory"] = inv
                    self.set_active_mon(active)
                    self.save()
                    return True, f"Equipped Metal Coat ⚙️ to {self.api.get_species_name(active.current_id)}! (+15% Steel attack damage)"
                valid_species = ", ".join([self.api.get_species_name(sid) for sid in compat_map.keys()])
                return False, f"The {item_name} has no effect on {self.api.get_species_name(active.current_id)}! (Compatible with: {valid_species})"

            # Check if target evolved form already exists in Pokédex
            dex = self.state.get("dex", [])
            discovered_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))) for d in dex}
            if target_evo_id in discovered_sp_ids:
                next_name = self.api.get_species_name(target_evo_id)
                return False, f"Cannot evolve into {next_name}! {next_name} (#{target_evo_id}) already exists in your Pokédex."

            inv[item_val] -= 1
            if inv[item_val] <= 0: del inv[item_val]

            prev_name = self.api.get_species_name(active.current_id)
            active.stage_index += 1

            if active.stage_index >= len(active.path_ids):
                active.path_ids.append(target_evo_id)
            else:
                active.path_ids[active.stage_index] = target_evo_id
                active.path_ids = active.path_ids[:active.stage_index + 1]

            active.total_forms = len(active.path_ids)
            new_name = self.api.get_species_name(target_evo_id)

            sp_data = self.api.get_pokemon_species(target_evo_id)
            if sp_data:
                cap_rate = sp_data.get("capture_rate", 255)
                is_leg = sp_data.get("is_legendary", False) or sp_data.get("is_mythical", False)
                active.rarity = Rarity.from_capture_rate(cap_rate, is_leg)

            active.used_at_stage = 0
            self._register_to_dex(active, status="active")
            self.set_active_mon(active)
            self.state["inventory"] = inv
            self.save()

            shiny_str = "✨ Shiny " if active.is_shiny else ""
            quests_msg = "\n".join(self._progress_quest_by_type("progression"))
            msg = f"🎉 Amazing! {shiny_str}{prev_name} evolved into {shiny_str}{new_name} using the {item_name}!"
            if quests_msg:
                msg += f"\n{quests_msg}"
            return True, msg

        # Special Rocket Consumable: Dark Gene Catalyst
        elif item_val == "dark_gene_catalyst":
            ok, msg = self.apply_dark_gene_catalyst()
            if ok:
                inv[item_val] -= 1
                if inv[item_val] <= 0:
                    del inv[item_val]
                self.state["inventory"] = inv
                self.save()
                return True, f"🧬 Dark Gene Catalyst triggered cellular mutation!\n  {msg}"
            return False, msg

        # 3. Consumables (Tonics, Ash, Whistle, Radar, Insurance)
        elif item_val == "revitalizing_tonic":
            if not active:
                return False, "You need an active Pokémon companion to use Revitalizing Tonic!"
            inv[item_val] -= 1
            if inv[item_val] <= 0: del inv[item_val]
            active.happiness = 100
            self.set_active_mon(active)
            self.state["inventory"] = inv
            self.save()
            return True, f"⚗️ Revitalizing Tonic restored {self.api.get_species_name(active.current_id)}'s Happiness to 100%! Ready for expeditions again!"

        elif item_val == "sacred_ash":
            inv[item_val] -= 1
            if inv[item_val] <= 0: del inv[item_val]
            red_state = self.state.get("red_battle_state", {})
            if red_state and "player_hps" in red_state and "player_max_hps" in red_state:
                red_state["player_hps"] = list(red_state["player_max_hps"])
                self.state["red_battle_state"] = red_state
            self.state["inventory"] = inv
            self.save()
            return True, "🏺 Sacred Ash sprinkled! All Pokémon on your Mt. Silver roster have been fully restored and revived to peak strength!"

        elif item_val == "warp_whistle":
            expeditions = self.state.get("expeditions", [])
            if not expeditions:
                return False, "You have no active expeditions to complete!"
            inv[item_val] -= 1
            if inv[item_val] <= 0: del inv[item_val]
            count = len(expeditions)
            events = []
            while self.state.get("expeditions"):
                exp = self.state["expeditions"][0]
                remaining_xp = max(0, exp.get("target", 0) - exp.get("progress", 0))
                self._update_expeditions(remaining_xp, events)
            self.state["inventory"] = inv
            self.save()
            msg = f"🌬️ Blew the Smuggler's Warp Whistle! A mysterious whirlwind completed all {count} active expeditions!"
            if events:
                msg += "\n" + "\n".join(events)
            return True, msg

        elif item_val == "expedition_energy_tonic":
            inv[item_val] -= 1
            if inv[item_val] <= 0: del inv[item_val]
            if active:
                active.happiness = min(100, active.happiness + 50)
                self.set_active_mon(active)
            dex = self.state.get("dex", [])
            for d in dex:
                mon_st = d.get("mon_state")
                if isinstance(mon_st, dict) and "happiness" in mon_st:
                    mon_st["happiness"] = min(100, mon_st.get("happiness", 100) + 50)
            self.state["inventory"] = inv
            self.save()
            return True, "⚡ Expedition Energy Tonic invigorated all Pokémon in your party and roster (+50% Happiness)!"

        elif item_val == "expedition_insurance":
            inv[item_val] -= 1
            if inv[item_val] <= 0: del inv[item_val]
            self.state["expedition_insurance"] = self.state.get("expedition_insurance", 0) + 3
            self.state["inventory"] = inv
            self.save()
            charges = self.state["expedition_insurance"]
            return True, f"📜 Filed Expedition Insurance Policy! Your companions are protected from happiness decay for the next {charges} expeditions!"

        elif item_val == "rocket_radar":
            inv[item_val] -= 1
            if inv[item_val] <= 0: del inv[item_val]
            self.state["rocket_radar_charges"] = self.state.get("rocket_radar_charges", 0) + 3
            self.state["inventory"] = inv
            self.save()
            charges = self.state["rocket_radar_charges"]
            return True, f"📡 Activated Rocket Radar! Your next {charges} expeditions will gain +50% bonus token yields!"

        # 4. Rare Candy
        elif item_val == "rare_candy":
            if active is None:
                return False, "You need an active Pokémon companion to give Rare Candy!"
            inv[item_val] -= qty
            if inv[item_val] <= 0: del inv[item_val]
            self.state["inventory"] = inv

            xp_grant = int(self.current_difficulty.shop_prices["rare_candy"] * 0.6) * qty
            active.used_at_stage += xp_grant
            self.set_active_mon(active)

            events = self._check_growth(active)
            if events:
                alerts = self.state.get("unread_alerts", [])
                for e in events:
                    if e not in alerts:
                        alerts.append(e)
                self.state["unread_alerts"] = alerts
            self.save()
            active_name = self.api.get_species_name(active.current_id)
            msg = f"Fed {qty}x Rare Candy to {active_name}! (+{format_tokens(xp_grant)} XP)"
            if events:
                msg += "\n" + "\n".join(events)
            return True, msg

        # 5. Held items
        elif item_val in [
            "everstone", "lucky_egg", "amulet_coin", "leftovers",
            "choice_scarf", "exp_share", "soothe_bell", "scope_lens",
            "life_orb", "choice_band", "choice_specs", "focus_sash",
            "rocky_helmet", "assault_vest", "heavy_boots", "compass_of_deep"
        ]:
            if active is None:
                return False, f"You need an active Pokémon to equip a {item_name}!"
            if qty > 1:
                return False, f"You can only equip one {item_name} at a time."

            if active.held_item:
                inv[active.held_item] = inv.get(active.held_item, 0) + 1

            active.held_item = item_val
            inv[item_val] -= 1
            if inv[item_val] <= 0: del inv[item_val]
            self.state["inventory"] = inv
            self.set_active_mon(active)
            self.save()

            effect_text = {
                "everstone": "Its evolution is now halted.",
                "lucky_egg": "It will now gain +20% more XP!",
                "amulet_coin": "It will now find +50% more tokens in battles and expeditions!",
                "leftovers": "It will now be protected from daily happiness decay!",
                "choice_scarf": "It will now complete expeditions 20% faster, but drain happiness faster!",
                "exp_share": "It will now share 25% of earned XP with inactive companions in your roster!",
                "soothe_bell": "It will now double happiness gains and halt daily happiness decay!",
                "scope_lens": "It will now double shiny hatching and encounter chances!",
                "life_orb": "It will now channel +10% bonus token power from your coding!",
                "choice_band": "It will now deal +50% more damage in Boss and Trainer battles!",
                "choice_specs": "It will now deal +50% more special damage in Boss and Trainer battles!",
                "focus_sash": "It will endure a lethal blow with 1 HP remaining in Mt. Silver battles!",
                "rocky_helmet": "Bosses and foes take recoil damage when striking it!",
                "assault_vest": "It takes 30% reduced damage from enemy attacks in Mt. Silver!",
                "heavy_boots": "It is completely protected from environmental field hazards!",
                "compass_of_deep": "It speeds up all expeditions by +25%!"
            }.get(item_val, "")

            return True, f"Equipped {item_name} {item_emoji} to {self.api.get_species_name(active.current_id)}! {effect_text}"

        elif item_kind == ItemKind.BERRY_ORAN:
            if active is None:
                return False, "You need an active Pokémon companion to feed an Oran Berry!"
            return self.feed_pokemon("active", qty=qty)

        elif item_kind == ItemKind.BERRY_GOLDEN:
            if qty > 1:
                return False, "You can only use one Golden Razz Berry at a time!"
            inv[item_kind.value] -= 1
            self.state["golden_razz_active"] = True
            self.state["inventory"] = inv
            self.save()
            return True, "Used Golden Razz Berry 🍇! Shiny odds on your NEXT egg hatch boosted to 1/24! ✨"

        elif item_kind == ItemKind.MEGA_STONE or item_val.startswith("mega_stone_"):
            if qty > 1:
                return False, "You can only use one Mega Stone at a time!"
            return self.toggle_mega_evolution(target_stone_key=item_val if item_val.startswith("mega_stone_") else None)

        elif item_kind.value.endswith("_stone") and item_kind != ItemKind.MEGA_STONE:
            if qty > 1:
                return False, "You can only use one Evolution Stone at a time!"
            active = self.active_mon
            if not active:
                return False, "You need an active companion to use an Evolution Stone!"
            
            # Check for Everstone
            if active.held_item == "everstone":
                return False, "Your companion is holding an Everstone! It cannot evolve."
            
            api_item_name = item_kind.value.replace("_", "-")
            target_evo_id = self._find_stone_evolution(active.current_id, api_item_name)
            
            if not target_evo_id:
                return False, f"The {item_kind.name_en} has no effect on {self.api.get_species_name(active.current_id)}!"

            # Block stone evolution if target evolved form already exists in Pokédex
            dex = self.state.get("dex", [])
            discovered_sp_ids = {d.get("species_id", d.get("final_id", d.get("base_id"))) for d in dex}
            if target_evo_id in discovered_sp_ids:
                next_name = self.api.get_species_name(target_evo_id)
                return False, f"Cannot evolve into {next_name}! {next_name} (#{target_evo_id}) already exists in your Pokédex."
                
            inv[item_kind.value] -= 1
            if inv[item_kind.value] <= 0:
                del inv[item_kind.value]
                
            prev_name = self.api.get_species_name(active.current_id)
            active.stage_index += 1
            
            if active.stage_index >= len(active.path_ids):
                active.path_ids.append(target_evo_id)
            else:
                active.path_ids[active.stage_index] = target_evo_id
                active.path_ids = active.path_ids[:active.stage_index + 1]
                
            active.total_forms = len(active.path_ids)
            new_name = self.api.get_species_name(target_evo_id)
            
            sp_data = self.api.get_pokemon_species(target_evo_id)
            if sp_data:
                cap_rate = sp_data.get("capture_rate", 255)
                is_leg = sp_data.get("is_legendary", False) or sp_data.get("is_mythical", False)
                active.rarity = Rarity.from_capture_rate(cap_rate, is_leg)
                
            active.used_at_stage = 0 
            
            self._register_to_dex(active, status="active")
            self.set_active_mon(active)
            self.state["inventory"] = inv
            self.save()
            
            shiny_str = "✨ Shiny " if active.is_shiny else ""
            quests_msg = "\n".join(self._progress_quest_by_type("progression"))
            msg = f"🎉 Amazing! {shiny_str}{prev_name} evolved into {shiny_str}{new_name} using the {item_kind.name_en}!"
            if quests_msg:
                msg += f"\n{quests_msg}"
            return True, msg

        elif item_kind == ItemKind.EXPEDITION_PASS:
            if qty > 1:
                return False, "You can only use one Expedition Pass at a time!"
            expeditions = self.state.get("expeditions", [])
            if not expeditions:
                return False, "You have no active expeditions to complete!"
            inv[item_kind.value] -= 1
            # Complete the first expedition instantly
            exp = expeditions[0]
            remaining_xp = max(0, exp.get("target", 0) - exp.get("progress", 0))
            events = []
            self._update_expeditions(remaining_xp, events)
            self.state["inventory"] = inv
            self.save()
            return True, "\n".join(events)

        elif item_kind == ItemKind.POKE_FLUTE:
            if qty > 1:
                return False, "You can only use one Poké Flute at a time!"
            if self.state.get("active_boss"):
                return False, "A Gym Boss is already active! Defeat them first!"
            
            # Find an undefeated boss, or pick a random one if all defeated
            bosses = [
                {"id": "boss_1", "name": "Brock & Geodude", "sp_id": 74, "badge": "🪨 Boulder Badge", "hp": 2_000_000, "reward": "rare_candy"},
                {"id": "boss_2", "name": "Misty & Starmie", "sp_id": 121, "badge": "💧 Cascade Badge", "hp": 5_000_000, "reward": "rare_candy"},
                {"id": "boss_3", "name": "Lt. Surge & Raichu", "sp_id": 26, "badge": "⚡ Thunder Badge", "hp": 10_000_000, "reward": "tokens_10m"},
                {"id": "boss_4", "name": "Erika & Vileplume", "sp_id": 45, "badge": "🌸 Rainbow Badge", "hp": 18_000_000, "reward": "rare_candy"},
                {"id": "boss_5", "name": "Koga & Weezing", "sp_id": 110, "badge": "🟣 Soul Badge", "hp": 25_000_000, "reward": "rare_candy"},
                {"id": "boss_6", "name": "Sabrina & Alakazam", "sp_id": 65, "badge": "🔮 Marsh Badge", "hp": 35_000_000, "reward": "tokens_15m"},
                {"id": "boss_7", "name": "Blaine & Arcanine", "sp_id": 59, "badge": "🔥 Volcano Badge", "hp": 45_000_000, "reward": "rare_candy"},
                {"id": "boss_8", "name": "Giovanni & Mewtwo", "sp_id": 150, "badge": "🌍 Earth Badge", "hp": 60_000_000, "reward": "master_ball"},
                {"id": "boss_9", "name": "Lance & Dragonite", "sp_id": 149, "badge": "🐉 Dragon Badge", "hp": 80_000_000, "reward": "tokens_20m"},
                {"id": "boss_10", "name": "Cynthia & Garchomp", "sp_id": 445, "badge": "🏆 Champion Badge", "hp": 100_000_000, "reward": "tokens_50m"}
            ]
            gym_badges = set(self.state.get("gym_badges", []))
            available = [b for b in bosses if b["badge"] not in gym_badges]
            
            if not available:
                available = bosses  # All defeated, spawn any for fun
            
            b = random.choice(available)
            active_boss = {
                "id": b["id"],
                "name": b["name"],
                "sp_id": b["sp_id"],
                "badge": b["badge"],
                "total_hp": b["hp"],
                "current_hp": b["hp"],
                "reward": b["reward"]
            }
            self.state["active_boss"] = active_boss
            inv[item_kind.value] -= 1
            self.state["inventory"] = inv
            self.save()
            return True, f"🪈 You played the Poké Flute! A wild Gym Boss {b['name']} (#{b['sp_id']}) was summoned! (HP: {format_tokens(b['hp'])})"

        elif item_kind == ItemKind.MASTER_BALL:
            eggs = self.state.get("incubating_eggs", {})
            if not eggs:
                # If they have an active legacy egg
                if self.active_mon is None:
                    curr_tier = self.state.get("current_egg_tier") or self.state.get("egg_tier") or "normal"
                    eggs[curr_tier] = self.state.get("egg_usage", 0)
                else:
                    return False, "You need an incubating egg to use the Master Ball!"
            
            inv[item_kind.value] -= 1
            
            # Find the egg with the most progress to hatch
            best_tier = max(eggs.keys(), key=lambda t: eggs[t])
            events = []
            
            # Ensure the current active mon (if any) is archived first just in case
            if self.active_mon:
                self._register_to_dex(self.active_mon, status="inactive")
                
            mon, hatch_events = self.hatch_egg(initial_xp=0, force_tier=best_tier, force_shiny=True)
            events.extend(hatch_events)
            eggs.pop(best_tier, None)
            self.state["incubating_eggs"] = eggs
            self.state["inventory"] = inv
            self.save()
            return True, f"Threw a Master Ball 🌟! Guaranteed Shiny hatch!\n" + "\n".join(events)

        elif item_kind == ItemKind.EXPEDITION_LICENSE:
            inv[item_kind.value] -= 1
            self.state["expedition_slots"] = self.state.get("expedition_slots", 10) + 10
            self.state["inventory"] = inv
            self.save()
            return True, "📜 Used an Expedition License! You can now send 10 more Pokémon on expeditions simultaneously!"

        return False, f"{item_kind.name_en} is not usable directly from the Bag."

    def unequip_item(self) -> Tuple[bool, str]:
        active = self.active_mon
        if not active:
            return False, "You don't have an active Pokémon!"
        if not active.held_item:
            return False, "Your active companion is not holding any item."
        
        held = active.held_item
        active.held_item = None
        self.set_active_mon(active)
        
        inv = self.state.get("inventory", {})
        inv[held] = inv.get(held, 0) + 1
        self.state["inventory"] = inv
        
        events = self._check_growth(active)
        self.save()
        
        try:
            kind_name = ItemKind(held).name_en
        except ValueError:
            kind_name = held
            
        msg = f"Unequipped {kind_name} from your companion!"
        if events:
            msg += "\n" + "\n".join(events)
        return True, msg
