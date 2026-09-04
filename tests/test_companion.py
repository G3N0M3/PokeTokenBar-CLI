import os
import tempfile
import unittest
from pathlib import Path
from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.models import ItemKind, Rarity
from poketokenbar.game.storage import StorageManager

class TestCompanionEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._temp_dir = tempfile.TemporaryDirectory()
        cls._temp_state_file = Path(cls._temp_dir.name) / "test_state.json"
        os.environ["PTB_STATE_FILE"] = str(cls._temp_state_file)

    @classmethod
    def tearDownClass(cls):
        cls._temp_dir.cleanup()
        os.environ.pop("PTB_STATE_FILE", None)

    def setUp(self):
        StorageManager.save_state(StorageManager.default_state())
        self.engine = CompanionEngine()

    def test_item_prices(self):
        self.assertEqual(ItemKind.MINT.price, 1_000_000)
        self.assertEqual(ItemKind.SHINY_STONE.price, 50_000_000)

    def test_hatch(self):
        mon, events = self.engine.hatch_egg(0)
        self.assertIsNotNone(mon)
        self.assertTrue(len(events) > 0)
        self.assertIn("Hatched", events[0])

    def test_select_active_mon(self):
        mon, events = self.engine.hatch_egg(0)
        ok, msg = self.engine.select_active_from_dex("1")
        self.assertTrue(ok)
        self.assertIn("Switched active companion", msg)

    def test_duplicate_egg_restriction(self):
        # Hatch initial mon to clear baseline
        self.engine.hatch_egg(0)
        # Give enough tokens to buy eggs
        self.engine.state["used_since_install"] = 500_000_000
        ok1, msg1 = self.engine.buy_egg(None)
        self.assertTrue(ok1)
        # Second buy while holding egg should fail
        ok2, msg2 = self.engine.buy_egg(None)
        self.assertFalse(ok2)
        # After clearing egg (e.g. hatching), buying should succeed
        self.engine.state["egg_tier"] = None
        ok3, msg3 = self.engine.buy_egg(Rarity.UNCOMMON)
        self.assertTrue(ok3)

    def test_new_game_features(self):
        mon, events = self.engine.hatch_egg(0)
        
        # Test Oran Berry feeding
        self.engine.state["inventory"]["berry_oran"] = 1
        ok, msg = self.engine.use_item(ItemKind.BERRY_ORAN)
        self.assertTrue(ok)
        self.assertIn("Fed 1 Oran Berry", msg)

        # Test Trainer Card generation
        card_str = self.engine.generate_trainer_card()
        self.assertIn("TRAINER PROFILE CARD", card_str)

        # Test Expedition dispatching by index and species ID
        ok, msg = self.engine.dispatch_expedition("1", "viridian")
        self.assertTrue(ok)
        self.assertIn("Dispatched", msg)

    def test_streak_calculation(self):
        today_str = "2026-08-20"
        active_days = ["2026-08-19", "2026-08-20"]
        streak = self.engine._calculate_streak_from_active_days(active_days, today_str)
        self.assertEqual(streak, 2)

    def test_day_rollover_zero_delta(self):
        import datetime
        self.engine.state["last_active_date"] = "2026-08-19"
        self.engine.state["used_since_install"] = 100_000
        self.engine.state["install_baseline_set"] = True

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        active_days = ["2026-08-19", today_str]
        # Call process_usage with 0 delta
        self.engine.process_usage(100_000, active_days)
        self.assertEqual(self.engine.state["last_active_date"], today_str)

    def test_expedition_roster_restriction(self):
        # Register an evolved species entry (e.g. Dratini #147 with status evolved)
        self.engine.state["dex"] = [
            {"id": "sp_147", "species_id": 147, "base_id": 147, "chain_order": [147, 148, 149], "status": "evolved"},
            {"id": "sp_149", "species_id": 149, "base_id": 147, "chain_order": [147, 148, 149], "status": "inactive"}
        ]
        # Attempt to dispatch evolved Dratini (#147)
        ok, msg = self.engine.dispatch_expedition("#147", "viridian")
        self.assertFalse(ok)
        self.assertIn("not found in Roster", msg)

        # Attempt to dispatch active roster Dragonite (#149)
        ok2, msg2 = self.engine.dispatch_expedition("#149", "viridian")
        self.assertTrue(ok2)
        self.assertIn("Dispatched", msg2)

    def test_expedition_progress_advancement(self):
        self.engine.state["dex"] = [
            {"id": "sp_149", "species_id": 149, "base_id": 147, "chain_order": [147, 148, 149], "status": "inactive"}
        ]
        self.engine.dispatch_expedition("#149", "viridian")
        old_used = self.engine.state.get("used_since_install", 0)
        self.engine.process_usage(old_used + 1_000_000)
        expeditions = self.engine.state.get("expeditions", [])
        self.assertEqual(len(expeditions), 1)

    def test_active_pokemon_xp_and_evolution(self):
        mon, events = self.engine.hatch_egg(0)
        self.assertIsNotNone(self.engine.active_mon)
        self.engine.state["install_baseline_set"] = True
        
        initial_stage = self.engine.active_mon.stage_index
        initial_xp = self.engine.active_mon.used_at_stage
        
        # Burn 10,000,000 tokens
        old_used = self.engine.state.get("used_since_install", 0)
        events = self.engine.process_usage(old_used + 10_000_000)
        
        active = self.engine.active_mon
        if active:
            # XP should have increased
            self.assertGreater(active.used_at_stage, initial_xp)

if __name__ == "__main__":
    unittest.main()
