import unittest
from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.models import ItemKind, Rarity

class TestCompanionEngine(unittest.TestCase):

    def setUp(self):
        self.engine = CompanionEngine()

    def test_item_prices(self):
        self.assertEqual(ItemKind.RARE_CANDY.price, 25_000_000)
        self.assertEqual(ItemKind.MINT.price, 5_000_000)
        self.assertEqual(ItemKind.SHINY_CHARM.price, 150_000_000)

    def test_hatch(self):
        mon, events = self.engine.hatch_egg(0)
        self.assertIsNotNone(mon)
        self.assertTrue(len(events) > 0)
        self.assertIn("Hatched", events[0])

    def test_settings(self):
        ok, msg = self.engine.update_settings(auto_tracking_enabled=False, refresh_interval=5.0)
        self.assertTrue(ok)
        s = self.engine.get_settings()
        self.assertFalse(s["auto_tracking_enabled"])
        self.assertEqual(s["refresh_interval"], 5.0)

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
        # Second buy of same tier should fail
        ok2, msg2 = self.engine.buy_egg(None)
        self.assertFalse(ok2)
        # Buying a different tier (Uncommon) should succeed
        ok3, msg3 = self.engine.buy_egg(Rarity.UNCOMMON)
        self.assertTrue(ok3)

    def test_reset_game_state(self):
        self.engine.hatch_egg(0)
        ok, msg = self.engine.reset_game_state()
        self.assertTrue(ok)
        self.assertIsNone(self.engine.active_mon)
        self.assertEqual(len(self.engine.state["dex"]), 0)

if __name__ == "__main__":
    unittest.main()
