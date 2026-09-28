"""Tests for TUI confirmations, stage flows, buy prompts, and modal alerts."""

import os
import io
import unittest
import tempfile
from unittest.mock import MagicMock, patch

from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.models import ItemKind, MonState, Rarity
from poketokenbar.game.storage import StorageManager
from poketokenbar.tui import PokeTokenBarTUI


class TestLargeQuantityPurchaseConfirmation(unittest.TestCase):
    def setUp(self):
        self.temp_state = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_state.close()
        os.environ["PTB_STATE_FILE"] = self.temp_state.name
        self.engine = CompanionEngine()
        self.engine.state["used_since_install"] = 100_000_000
        self.engine.state["spent_tokens"] = 0

    def tearDown(self):
        if os.path.exists(self.temp_state.name):
            os.remove(self.temp_state.name)
        bak = self.temp_state.name.replace(".json", ".json.bak")
        if os.path.exists(bak):
            os.remove(bak)

    def test_shop_buy_small_qty_executes_immediately(self):
        app = PokeTokenBarTUI()
        app.engine = self.engine

        # Buy 5 Oran Berries (<= 5)
        app.handle_shop_buy("buy 4 5")
        self.assertIsNone(app.pending_buy)
        self.assertIn("Successfully purchased 5x Oran Berry", app.message)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran"), 5)

    def test_shop_buy_large_qty_prompts_confirmation(self):
        app = PokeTokenBarTUI()
        app.engine = self.engine

        # Buy 10 Oran Berries (> 5)
        app.handle_shop_buy("buy 4 10")
        self.assertIsNotNone(app.pending_buy)
        self.assertIn("Buy 10x Oran Berry", app.message)
        self.assertIn("Type 'confirm'", app.message)
        self.assertEqual(self.engine.state.get("inventory", {}).get("berry_oran", 0), 0)

        # Confirm purchase
        ok, msg = app.execute_pending_buy(app.pending_buy)
        app.pending_buy = None
        self.assertTrue(ok)
        self.assertIn("Successfully purchased 10x Oran Berry", msg)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran"), 10)

    def test_shop_buy_large_qty_bypass_flag(self):
        app = PokeTokenBarTUI()
        app.engine = self.engine

        # Buy 10 Oran Berries with -y bypass
        app.handle_shop_buy("buy 4 10 -y")
        self.assertIsNone(app.pending_buy)
        self.assertIn("Successfully purchased 10x Oran Berry", app.message)
        self.assertEqual(self.engine.state["inventory"].get("berry_oran"), 10)

    def test_stock_large_shares_prompts_confirmation(self):
        app = PokeTokenBarTUI()
        app.engine = self.engine

        # Buy 10 shares of SILPH (> 5)
        app.handle_invest_command("invest SILPH 10")
        self.assertIsNotNone(app.pending_buy)
        self.assertIn("Buy 10 shares of SILPH", app.message)
        self.assertIn("Type 'confirm'", app.message)
        self.assertEqual(self.engine.state.get("investments", {}).get("silph", 0), 0)

        # Confirm stock purchase
        ok, msg = app.execute_pending_buy(app.pending_buy)
        app.pending_buy = None
        self.assertTrue(ok)
        self.assertIn("Invested in 10 share(s)", msg)
        self.assertEqual(self.engine.state["investments"]["silph"], 10)

    def test_stock_terminal_large_shares_prompts_confirmation(self):
        app = PokeTokenBarTUI()
        app.engine = self.engine
        app.stock_terminal = "silph"

        app.handle_stock_terminal_buy("buy 10")
        self.assertIsNotNone(app.pending_buy)
        self.assertIn("Buy 10 shares of SILPH", app.message)
        self.assertEqual(self.engine.state.get("investments", {}).get("silph", 0), 0)

        # Confirm purchase
        ok, msg = app.execute_pending_buy(app.pending_buy)
        app.pending_buy = None
        self.assertTrue(ok)
        self.assertEqual(self.engine.state["investments"]["silph"], 10)

    def test_buy_item_confirm_flag_programmatic(self):
        # Programmatic CompanionEngine.buy_item with confirm=True
        ok, prompt = self.engine.buy_item(ItemKind.BERRY_ORAN, 10, confirm=True)
        self.assertTrue(ok)
        self.assertIn("Buy 10x Oran Berry", prompt)
        self.assertLessEqual(len(prompt), 72)
        self.assertEqual(self.engine.state.get("inventory", {}).get("berry_oran", 0), 0)

    def test_large_buy_prompts_72_column_compliance(self):
        app = PokeTokenBarTUI()
        app.engine = self.engine

        # Test shop item prompts
        for item_id in ["1", "4", "5", "6", "7", "8", "9", "10", "11"]:
            app.handle_shop_buy(f"buy {item_id} 10")
            if app.pending_buy:
                self.assertLessEqual(len(app.pending_buy["prompt"]), 72, f"Item {item_id} prompt exceeds 72 cols: {app.pending_buy['prompt']}")

        # Test stock prompts
        for ticker in ["SILPH", "DEVON", "AETHER", "MAUV", "MACRO", "VIRIDIAN"]:
            app.handle_invest_command(f"invest {ticker} 10")
            if app.pending_buy:
                self.assertLessEqual(len(app.pending_buy["prompt"]), 72, f"Stock {ticker} prompt exceeds 72 cols: {app.pending_buy['prompt']}")

    def test_multiple_congratulation_alerts_render_distinct_sprites(self):
        """Verify each milestone alert dynamically renders its own Pokémon sprite and stats."""
        tui = PokeTokenBarTUI()
        tui.engine = self.engine
        tui.tracker.get_summary = MagicMock(return_value={"total_tokens": 0, "active_days": []})

        # Set active companion to Pikachu (#25)
        active_pika = MonState(
            base_id=25,
            path_ids=[172, 25, 26],
            planned_path_ids=[172, 25, 26],
            stage_index=1,
            used_at_stage=0,
            rarity=Rarity.UNCOMMON,
            total_forms=3,
        )
        self.engine.set_active_mon(active_pika)

        # Set up dex entries for other Pokémon involved in alerts
        charmeleon_mon = MonState(
            base_id=4,
            path_ids=[4, 5, 6],
            planned_path_ids=[4, 5, 6],
            stage_index=1,
            used_at_stage=0,
            rarity=Rarity.UNCOMMON,
            total_forms=3,
        )
        squirtle_mon = MonState(
            base_id=7,
            path_ids=[7],
            planned_path_ids=[7],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.COMMON,
            total_forms=1,
            is_graduated=True,
        )
        self.engine.state["dex"] = [
            {
                "species_id": 5,
                "base_id": 4,
                "rarity": "uncommon",
                "status": "inactive",
                "mon_state": StorageManager.mon_to_dict(charmeleon_mon),
            },
            {
                "species_id": 7,
                "base_id": 7,
                "rarity": "common",
                "status": "graduated",
                "mon_state": StorageManager.mon_to_dict(squirtle_mon),
            },
        ]

        # Queue 3 milestone alerts: Hatch, Evolution, Graduation
        self.engine.state["unread_alerts"] = [
            "🐣 Egg Hatched! You got a Bulbasaur (#1)! Rarity: COMMON",
            "🎉 Evolution! Charmander evolved into Charmeleon (#5)!",
            "🎓 Graduation! Squirtle (#7) has graduated to your Pokédex!",
        ]

        download_calls = []
        def mock_download(sp_id, is_shiny=False, is_back=False):
            download_calls.append((sp_id, is_shiny))
            return "/tmp/dummy.png"

        trap_out = io.StringIO()
        with patch.object(self.engine.api, "download_sprite", side_effect=mock_download), \
             patch("poketokenbar.sprite_renderer.SpriteRenderer.render_png_to_ansi", return_value="[SPRITE]"), \
             patch("sys.stdin", io.StringIO("\n\n\nq\n")), \
             patch("sys.stdout", trap_out):
            tui.run()

        # Verify that download_sprite was called for each alert's specific Pokémon ID, NOT Pikachu (#25)
        self.assertEqual(download_calls[:3], [(1, False), (5, False), (7, False)])

        # Verify all alerts were popped
        self.assertEqual(self.engine.state["unread_alerts"], [])

        # Verify shiny handling
        self.engine.state["unread_alerts"] = [
            "🐣 Egg Hatched! You got a ✨ Shiny Charmander (#4)! Rarity: COMMON"
        ]
        download_calls.clear()
        trap_shiny = io.StringIO()
        with patch.object(self.engine.api, "download_sprite", side_effect=mock_download), \
             patch("poketokenbar.sprite_renderer.SpriteRenderer.render_png_to_ansi", return_value="[SPRITE]"), \
             patch("sys.stdin", io.StringIO("\nq\n")), \
             patch("sys.stdout", trap_shiny):
            tui.run()

        self.assertEqual(download_calls[0], (4, True))

    def test_uncapped_stock_growth_and_trillion_scale_formatting(self):
        """Verify that stock price upper limits are expanded and prices can grow past 4.5x without artificial caps."""
        from poketokenbar.game.economy.stock_market import StockMarketEngine, BASE_PRICES
        from poketokenbar.utils.formatting import format_tokens, parse_tokens

        # 1. Verify trillion scale formatting and parsing
        self.assertEqual(format_tokens(1_500_000_000_000), "1.5T")
        self.assertEqual(parse_tokens("1.5t"), 1_500_000_000_000)
        self.assertEqual(parse_tokens("2.0q"), 2_000_000_000_000_000)

        # 2. Verify hard cap and ceiling are expanded to trillion scale
        for c_key in BASE_PRICES:
            self.assertGreaterEqual(StockMarketEngine.get_hard_cap(c_key), 10_000_000_000_000)
            self.assertGreaterEqual(StockMarketEngine.get_ceiling_price(c_key), 10_000_000_000_000)

        # 3. Verify stock prices can grow past previous 4.5x cap (e.g. Mauville base is 5M, old cap was 22.5M)
        sm = self.engine.get_or_init_stock_market()
        sm["prices"]["mauville"] = 50_000_000  # 10x base price
        sm["market_state"]["mauville"]["next_bias"] = 0.20  # +20% bull move
        sm["market_state"]["mauville"]["pattern"] = "bull_rally"

        changes = StockMarketEngine.step_day(
            sm_data=sm,
            days_to_apply=1,
            streak=5,
            burn_tokens=1_000_000,
            catalysts={},
            corp_boosts={"mauville": 0.05}
        )

        new_price = sm["prices"]["mauville"]
        # New price must not be clamped down to 22.5M! It should grow above 50M
        self.assertGreater(new_price, 50_000_000)
        self.assertGreaterEqual(changes["mauville"], 0.15)


if __name__ == "__main__":
    unittest.main()
