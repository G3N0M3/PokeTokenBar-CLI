"""Tests for companion feeding, happiness management, and berry thresholds."""

import os
import unittest
import tempfile
from poketokenbar.game.companion import CompanionEngine


class TestOranBerryFeeding(unittest.TestCase):
    def setUp(self):
        self.temp_state = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_state.close()
        os.environ["PTB_STATE_FILE"] = self.temp_state.name
        self.engine = CompanionEngine()

    def tearDown(self):
        if os.path.exists(self.temp_state.name):
            os.remove(self.temp_state.name)
        bak = self.temp_state.name.replace(".json", ".json.bak")
        if os.path.exists(bak):
            os.remove(bak)

    def test_feed_active_companion_custom_qty(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        self.assertIsNotNone(active)
        active.happiness = 50
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 5}

        ok, msg = self.engine.feed_pokemon("active", 1)
        self.assertTrue(ok)
        self.assertIn("Fed 1 Oran Berry", msg)
        self.assertEqual(self.engine.active_mon.happiness, 75)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran"), 4)

    def test_feed_zero_happiness_defaults_to_4_berries(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 10}

        ok, msg = self.engine.feed_pokemon("0")
        self.assertTrue(ok)
        self.assertIn("Fed 4 Oran Berries", msg)
        self.assertIn("100%", msg)
        self.assertEqual(self.engine.active_mon.happiness, 100)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran"), 6)

    def test_feed_zero_multiple_exhausted_companions(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)

        # Add second companion to roster
        self.engine.state["dex"].append({
            "id": "sp_25",
            "species_id": 25,
            "base_id": 25,
            "chain_order": [25, 26],
            "rarity": "uncommon",
            "status": "inactive",
            "mon_state": {"base_id": 25, "current_id": 25, "happiness": 0, "stage_index": 0, "total_forms": 2},
            "happiness": 0
        })
        self.engine.state["inventory"] = {"berry_oran": 10}

        ok, msg = self.engine.feed_pokemon("exhausted")
        self.assertTrue(ok)
        self.assertIn("Fed 8 Oran Berries", msg)
        self.assertEqual(self.engine.active_mon.happiness, 100)
        self.assertEqual(self.engine.state["dex"][-1]["mon_state"]["happiness"], 100)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran"), 2)

    def test_feed_zero_partial_inventory(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 3}

        ok, msg = self.engine.feed_pokemon("0")
        self.assertTrue(ok)
        self.assertIn("Fed 3 Oran Berries", msg)
        self.assertEqual(self.engine.active_mon.happiness, 75)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran", 0), 0)

    def test_feed_saves_excess_berries_at_max_happiness(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 75
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 5}

        # Requesting 4 berries, but only 1 needed to reach 100%
        ok, msg = self.engine.feed_pokemon("active", 4)
        self.assertTrue(ok)
        self.assertIn("Fed 1 Oran Berry", msg)
        self.assertIn("saved 3 berries", msg)
        self.assertEqual(self.engine.active_mon.happiness, 100)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran"), 4)

    def test_feed_all_option_is_removed(self):
        self.engine.hatch_egg(0)
        self.engine.state["inventory"] = {"berry_oran": 10}

        # 'all' option is rejected with explanatory error
        ok, msg = self.engine.feed_pokemon("all")
        self.assertFalse(ok)
        self.assertIn("The 'all' option has been removed", msg)

    def test_feed_by_species_id_and_rejection_of_names(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 50
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 5}

        # Feed by species #id (e.g. #25)
        ok, msg = self.engine.feed_pokemon(f"#{active.current_id}", 1)
        self.assertTrue(ok)
        self.assertEqual(self.engine.active_mon.happiness, 75)

        # Species name is rejected
        name = self.engine.api.get_species_name(active.current_id)
        ok, msg = self.engine.feed_pokemon(name, 1)
        self.assertFalse(ok)
        self.assertIn("not found in your Roster", msg)

    def test_feed_by_happiness_threshold_function(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 25
        self.engine.set_active_mon(active)

        # Mon 2: 50% happiness
        self.engine.state["dex"].append({
            "id": "sp_25",
            "species_id": 25,
            "base_id": 25,
            "chain_order": [25, 26],
            "rarity": "uncommon",
            "status": "inactive",
            "mon_state": {"base_id": 25, "current_id": 25, "happiness": 50, "stage_index": 0, "total_forms": 2},
            "happiness": 50
        })
        # Mon 3: 75% happiness (should NOT be fed when threshold is <= 50%)
        self.engine.state["dex"].append({
            "id": "sp_133",
            "species_id": 133,
            "base_id": 133,
            "chain_order": [133],
            "rarity": "rare",
            "status": "inactive",
            "mon_state": {"base_id": 133, "current_id": 133, "happiness": 75, "stage_index": 0, "total_forms": 1},
            "happiness": 75
        })
        self.engine.state["inventory"] = {"berry_oran": 10}

        # Feed 1 berry to all companions with happiness <= 50%
        ok, msg = self.engine.feed_by_happiness_threshold(max_happiness=50, qty=1)
        self.assertTrue(ok)
        self.assertIn("Fed 2 Oran Berries", msg)
        self.assertEqual(self.engine.active_mon.happiness, 50)  # 25 + 25 = 50
        self.assertEqual(self.engine.state["dex"][1]["mon_state"]["happiness"], 75)  # 50 + 25 = 75
        self.assertEqual(self.engine.state["dex"][2]["mon_state"]["happiness"], 75)  # unchanged!
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 8)

    def test_feed_by_happiness_threshold_confirm_flag(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 40
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 15}

        # confirm=True returns prompt string without mutating inventory
        ok, prompt_str = self.engine.feed_by_happiness_threshold(max_happiness=50, qty=2, confirm=True)
        self.assertTrue(ok)
        self.assertIn("Req:", prompt_str)
        self.assertIn("Bag: 15", prompt_str)
        self.assertLessEqual(len(prompt_str), 72)
        self.assertEqual(self.engine.active_mon.happiness, 40)
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 15)

    def test_feed_string_threshold_variations(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 30
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 10}

        # Test '<=50%' target string (less than or equal to)
        plan1 = self.engine.get_feed_plan("<=50%", qty=1)
        self.assertTrue(plan1["ok"])
        self.assertEqual(plan1["plan_type"], "threshold")
        self.assertEqual(plan1["threshold"], 50)
        self.assertEqual(plan1["op"], "<=")

        # Test '<=50' target string
        plan2 = self.engine.get_feed_plan("<=50", qty=1)
        self.assertTrue(plan2["ok"])
        self.assertEqual(plan2["threshold"], 50)

        # Test '<50%' target string (less than)
        plan3 = self.engine.get_feed_plan("<50%", qty=1)
        self.assertTrue(plan3["ok"])
        self.assertEqual(plan3["op"], "<")

        # Test '<30' target string (not matching since 30 is not < 30)
        plan4 = self.engine.get_feed_plan("<30", qty=1)
        self.assertFalse(plan4["ok"])

        # Test '30%' target string (equal to 30)
        plan5 = self.engine.get_feed_plan("30%", qty=1)
        self.assertTrue(plan5["ok"])
        self.assertEqual(plan5["op"], "=")

        # Test '=30' target string (equal to 30)
        plan6 = self.engine.get_feed_plan("=30", qty=1)
        self.assertTrue(plan6["ok"])
        self.assertEqual(plan6["op"], "=")

        # Test '30' target string (plain number equal to 30)
        plan7 = self.engine.get_feed_plan("30", qty=1)
        self.assertTrue(plan7["ok"])
        self.assertEqual(plan7["op"], "=")

        # Test '=70' target string (equal to 70, does not match 30)
        plan8 = self.engine.get_feed_plan("=70", qty=1)
        self.assertFalse(plan8["ok"])

        # Test '#<id>' targets species specifically
        plan9 = self.engine.get_feed_plan(f"#{active.current_id}", qty=1)
        self.assertTrue(plan9["ok"])
        self.assertEqual(plan9["plan_type"], "single")

    def test_feed_operator_conditions_comprehensive(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)

        # Mon 2: 30% happiness
        self.engine.state["dex"].append({
            "id": "sp_25", "species_id": 25, "base_id": 25,
            "chain_order": [25], "rarity": "uncommon", "status": "inactive",
            "mon_state": {"base_id": 25, "current_id": 25, "happiness": 30, "stage_index": 0, "total_forms": 1},
            "happiness": 30
        })
        # Mon 3: 70% happiness
        self.engine.state["dex"].append({
            "id": "sp_133", "species_id": 133, "base_id": 133,
            "chain_order": [133], "rarity": "rare", "status": "inactive",
            "mon_state": {"base_id": 133, "current_id": 133, "happiness": 70, "stage_index": 0, "total_forms": 1},
            "happiness": 70
        })
        # Mon 4: 70% happiness
        self.engine.state["dex"].append({
            "id": "sp_143", "species_id": 143, "base_id": 143,
            "chain_order": [143], "rarity": "rare", "status": "inactive",
            "mon_state": {"base_id": 143, "current_id": 143, "happiness": 70, "stage_index": 0, "total_forms": 1},
            "happiness": 70
        })
        # Mon 5: 90% happiness
        self.engine.state["dex"].append({
            "id": "sp_149", "species_id": 149, "base_id": 149,
            "chain_order": [149], "rarity": "rare", "status": "inactive",
            "mon_state": {"base_id": 149, "current_id": 149, "happiness": 90, "stage_index": 0, "total_forms": 1},
            "happiness": 90
        })
        self.engine.state["inventory"] = {"berry_oran": 20}

        # 1. <=70%: matches Mon 1 (0%), Mon 2 (30%), Mon 3 (70%), Mon 4 (70%) -> 4 mons
        plan_le = self.engine.get_feed_plan("<=70", qty=1)
        self.assertTrue(plan_le["ok"])
        self.assertEqual(len(plan_le["items"]), 4)

        # 2. <70%: matches Mon 1 (0%), Mon 2 (30%) -> 2 mons
        plan_lt = self.engine.get_feed_plan("<70", qty=1)
        self.assertTrue(plan_lt["ok"])
        self.assertEqual(len(plan_lt["items"]), 2)

        # 3. =70 / 70% / 70: matches Mon 3 (70%), Mon 4 (70%) -> 2 mons
        plan_eq = self.engine.get_feed_plan("=70", qty=1)
        self.assertTrue(plan_eq["ok"])
        self.assertEqual(len(plan_eq["items"]), 2)

        plan_pct = self.engine.get_feed_plan("70%", qty=1)
        self.assertTrue(plan_pct["ok"])
        self.assertEqual(len(plan_pct["items"]), 2)

        # 4. 0: matches Mon 1 (0%) -> 1 mon
        plan_zero = self.engine.get_feed_plan("0", qty=1)
        self.assertTrue(plan_zero["ok"])
        self.assertEqual(len(plan_zero["items"]), 1)

        # 5. #149: matches Mon 5 (Dragonite #149) specifically
        plan_id = self.engine.get_feed_plan("#149", qty=1)
        self.assertTrue(plan_id["ok"])
        self.assertEqual(len(plan_id["items"]), 1)
        self.assertEqual(plan_id["items"][0]["name"], "Dragonite")

    def test_feed_plan_stating_required_and_available(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 15}

        plan = self.engine.get_feed_plan("0")
        self.assertTrue(plan["ok"])
        self.assertEqual(plan["total_berries"], 4)
        self.assertEqual(plan["available_berries"], 15)
        self.assertIn("Req: 4", plan["prompt"])
        self.assertIn("Bag: 15", plan["prompt"])
        self.assertLessEqual(len(plan["prompt"]), 72)
        # Verify state was not mutated by planning
        self.assertEqual(self.engine.active_mon.happiness, 0)
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 15)

    def test_feed_pokemon_confirm_flag(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 10}

        # With confirm=True, returns prompt without mutating state
        ok, prompt_str = self.engine.feed_pokemon("0", confirm=True)
        self.assertTrue(ok)
        self.assertIn("Req: 4", prompt_str)
        self.assertIn("Bag: 10", prompt_str)
        self.assertEqual(self.engine.active_mon.happiness, 0)
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 10)

    def test_feed_tui_confirmation_flow(self):
        from poketokenbar.tui import PokeTokenBarTUI
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 10}

        app = PokeTokenBarTUI()
        app.engine = self.engine

        # Calling 'feed 0' creates pending_feed and shows prompt with req and in bag
        app.handle_feed_command("feed 0")
        self.assertIsNotNone(app.pending_feed)
        self.assertIn("Req: 4", app.message)
        self.assertIn("Bag: 10", app.message)
        # Berries not consumed yet
        self.assertEqual(self.engine.active_mon.happiness, 0)
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 10)

        # Confirming executes the plan
        ok, msg = app.engine.execute_feed_plan(app.pending_feed)
        app.pending_feed = None
        self.assertTrue(ok)
        self.assertIn("Fed 4 Oran Berries", msg)
        self.assertEqual(self.engine.active_mon.happiness, 100)
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 6)

    def test_feed_tui_bypass_confirm_flags(self):
        from poketokenbar.tui import PokeTokenBarTUI
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 10}

        app = PokeTokenBarTUI()
        app.engine = self.engine

        # With -y flag, executes immediately without pending_feed
        app.handle_feed_command("feed 0 -y")
        self.assertIsNone(app.pending_feed)
        self.assertIn("Fed 4 Oran Berries", app.message)
        self.assertEqual(self.engine.active_mon.happiness, 100)
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 6)

    def test_feed_tab1_immediate_execution(self):
        from poketokenbar.tui import PokeTokenBarTUI
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 10}

        app = PokeTokenBarTUI()
        app.engine = self.engine
        app.current_tab = 1

        # 'feed 3' on Tab 1 should execute immediately and update active companion happiness
        app.handle_feed_command("feed 3")
        self.assertIsNone(app.pending_feed)
        self.assertIn("Fed 3 Oran Berries", app.message)
        self.assertEqual(self.engine.active_mon.happiness, 75)
        self.assertEqual(self.engine.state["inventory"]["berry_oran"], 7)
        self.assertEqual(self.engine.state["happiness"], 75)

    def test_feed_confirmation_prompts_under_72_cols(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 0
        self.engine.set_active_mon(active)

        for i in range(1, 15):
            self.engine.state["dex"].append({
                "id": f"sp_{i}",
                "species_id": i,
                "base_id": i,
                "chain_order": [i],
                "rarity": "common",
                "status": "inactive",
                "mon_state": {"base_id": i, "current_id": i, "happiness": 0, "stage_index": 0, "total_forms": 1},
                "happiness": 0
            })
        self.engine.state["inventory"] = {"berry_oran": 100}

        # Check exhausted prompt
        plan = self.engine.get_feed_plan("0")
        self.assertTrue(plan["ok"])
        self.assertLessEqual(len(plan["prompt"]), 72)
        self.assertIn("Req:", plan["prompt"])
        self.assertIn("Bag:", plan["prompt"])

        # Check threshold prompt
        plan_thresh = self.engine.get_feed_plan("<=50%")
        self.assertTrue(plan_thresh["ok"])
        self.assertLessEqual(len(plan_thresh["prompt"]), 72)
        self.assertIn("Req:", plan_thresh["prompt"])
        self.assertIn("Bag:", plan_thresh["prompt"])

        # Check single target prompt
        plan_single = self.engine.get_feed_plan(f"#{active.current_id}", 4)
        self.assertTrue(plan_single["ok"])
        self.assertLessEqual(len(plan_single["prompt"]), 72)
        self.assertIn("Req:", plan_single["prompt"])
        self.assertIn("Bag:", plan_single["prompt"])

    def test_feed_rejects_pokemon_on_active_expedition(self):
        self.engine.hatch_egg(0)
        self.engine.state["inventory"] = {"berry_oran": 5}
        self.engine.state["dex"].append({
            "id": "sp_25",
            "species_id": 25,
            "base_id": 25,
            "chain_order": [25, 26],
            "rarity": "uncommon",
            "status": "inactive",
            "mon_state": {"base_id": 25, "current_id": 25, "happiness": 50, "stage_index": 0, "total_forms": 2},
            "happiness": 50
        })
        self.engine.state["expeditions"] = [{
            "sp_id": 25,
            "area": "Viridian Forest",
            "progress": 0,
            "target": 5000000,
            "reward": "rare_candy"
        }]

        ok, msg = self.engine.feed_pokemon("#25", 1)
        self.assertFalse(ok)
        self.assertIn("deployed on an expedition", msg)
        self.assertLessEqual(len(msg), 72)

    def test_feed_threshold_excludes_pokemon_on_active_expedition(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 100
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 10}

        # Mon with 0% happiness is currently deployed on expedition
        self.engine.state["dex"].append({
            "id": "sp_25",
            "species_id": 25,
            "base_id": 25,
            "chain_order": [25, 26],
            "rarity": "uncommon",
            "status": "inactive",
            "mon_state": {"base_id": 25, "current_id": 25, "happiness": 0, "stage_index": 0, "total_forms": 2},
            "happiness": 0
        })
        self.engine.state["expeditions"] = [{
            "sp_id": 25,
            "area": "Viridian Forest",
            "progress": 0,
            "target": 5000000,
            "reward": "rare_candy"
        }]

        plan = self.engine.get_feed_plan("0")
        self.assertFalse(plan["ok"])
        self.assertIn("All exhausted Pokémon are currently deployed on expeditions and cannot be fed until they return.", plan["error"])

    def test_feed_batch_targets_excludes_expeditions(self):
        self.engine.hatch_egg(0)
        active = self.engine.active_mon
        active.happiness = 100
        self.engine.set_active_mon(active)
        self.engine.state["inventory"] = {"berry_oran": 10}

        self.engine.state["dex"].append({
            "id": "sp_25",
            "species_id": 25,
            "base_id": 25,
            "chain_order": [25, 26],
            "rarity": "uncommon",
            "status": "inactive",
            "mon_state": {"base_id": 25, "current_id": 25, "happiness": 50, "stage_index": 0, "total_forms": 2},
            "happiness": 50
        })
        self.engine.state["dex"].append({
            "id": "sp_1",
            "species_id": 1,
            "base_id": 1,
            "chain_order": [1, 2, 3],
            "rarity": "starter",
            "status": "inactive",
            "mon_state": {"base_id": 1, "current_id": 1, "happiness": 50, "stage_index": 0, "total_forms": 3},
            "happiness": 50
        })
        # 25 is on expedition, 1 is available
        self.engine.state["expeditions"] = [{
            "sp_id": 25,
            "area": "Viridian Forest",
            "progress": 0,
            "target": 5000000,
            "reward": "rare_candy"
        }]

        # All targets deployed returns error
        plan_all_exp = self.engine.get_feed_plan("#25")
        self.assertFalse(plan_all_exp["ok"])

        # Multiple targets feeds available mon and ignores expedition mon
        plan_batch = self.engine.get_feed_plan("#25,#1", qty=1)
        self.assertTrue(plan_batch["ok"])
        self.assertEqual(len(plan_batch["items"]), 1)
        self.assertEqual(plan_batch["items"][0]["name"], self.engine.api.get_species_name(1))


if __name__ == "__main__":
    unittest.main()
