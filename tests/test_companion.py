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

    def test_expedition_dispatch_unevolved_companion_with_higher_form_discovered(self):
        # User has Quilava (#156) and Typhlosion (#157) in dex
        self.engine.state["dex"] = [
            {"id": "sp_155", "species_id": 155, "base_id": 155, "chain_order": [155, 156, 157], "status": "evolved"},
            {"id": "sp_156", "species_id": 156, "base_id": 155, "chain_order": [155, 156, 157], "status": "inactive"},
            {"id": "sp_157", "species_id": 157, "base_id": 155, "chain_order": [155, 156, 157], "status": "inactive"}
        ]
        # In roster: row 1 is Quilava (156), row 2 is Typhlosion (157)
        # 1. Dispatch row 1 -> must dispatch Quilava (#156)
        ok1, msg1 = self.engine.dispatch_expedition("1", "viridian")
        self.assertTrue(ok1)
        self.assertIn("Quilava", msg1)
        self.assertEqual(self.engine.state["expeditions"][0]["sp_id"], 156)

        # Clear expeditions
        self.engine.state["expeditions"] = []

        # 2. Dispatch by name "quilava" -> must dispatch Quilava (#156)
        ok2, msg2 = self.engine.dispatch_expedition("quilava", "viridian")
        self.assertTrue(ok2)
        self.assertIn("Quilava", msg2)
        self.assertEqual(self.engine.state["expeditions"][0]["sp_id"], 156)

        # Clear expeditions
        self.engine.state["expeditions"] = []

        # 3. Dispatch by species ID "156" -> must dispatch Quilava (#156)
        ok3, msg3 = self.engine.dispatch_expedition("156", "viridian")
        self.assertTrue(ok3)
        self.assertIn("Quilava", msg3)
        self.assertEqual(self.engine.state["expeditions"][0]["sp_id"], 156)

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

    def test_expedition_missing_keys_defensive(self):
        # Expeditions with missing reward/target/progress should not raise KeyError
        self.engine.state["expeditions"] = [
            {"sp_id": 3, "area": "cerulean"}
        ]
        events = []
        self.engine._update_expeditions(500_000, events)
        exp = self.engine.state["expeditions"][0]
        self.assertEqual(exp.get("reward"), "rare_candy")
        self.assertGreater(exp.get("progress", 0), 0)
        self.assertEqual(exp.get("target"), 5_000_000)

    def test_dispatch_expedition_invalid_destination(self):
        mon, events = self.engine.hatch_egg(0)
        # Dispatch with mistyped destination 'ine'
        ok, msg = self.engine.dispatch_expedition("1", "ine")
        self.assertFalse(ok)
        self.assertIn("not one of the available options", msg)
        self.assertIn("ine", msg)
        # Active companion should NOT be cleared on failed dispatch
        self.assertIsNotNone(self.engine.active_mon)
        # Valid destination 'mine' should succeed
        ok_valid, msg_valid = self.engine.dispatch_expedition("1", "mine")
        self.assertTrue(ok_valid)
        self.assertIn("Evolution Mine", msg_valid)

    def test_roster_and_pokedex_rendering_defensive(self):
        from unittest.mock import MagicMock
        from poketokenbar.tui_tabs.roster import render as render_roster
        from poketokenbar.tui_tabs.pokedex import render as render_pokedex
        
        # Add a mon to dex
        self.engine.hatch_egg(0)
        # Set a malformed expedition entry missing keys
        self.engine.state["expeditions"] = [{"sp_id": 16}]
        
        app = MagicMock()
        app.engine = self.engine
        app.roster_page = 1
        app.pokedex_page = 1
        
        # Rendering shouldn't raise any KeyError
        try:
            render_roster(app)
            render_pokedex(app)
        except Exception as e:
            self.fail(f"Rendering raised unexpected exception: {e}")

    def test_red_battle_assembly_with_expeditions(self):
        from poketokenbar.game.red_battle import RedBattleHandler
        self.engine.state["dex"] = [
            {"species_id": pid, "base_id": pid, "status": "graduated"}
            for pid in [3, 6, 9, 25, 143, 149]
        ]
        self.engine.state["expeditions"] = [{"sp_id": 149}]
        handler = RedBattleHandler(self.engine)
        ok, msg = handler.assemble_team([3, 6, 9, 25, 143, 149])
        self.assertFalse(ok)
        self.assertIn("expedition", msg)

    def test_held_item_persistence_and_display(self):
        import io
        from unittest.mock import MagicMock
        from poketokenbar.tui_tabs.companion import render as render_companion

        mon, _ = self.engine.hatch_egg(0)
        self.engine.state["inventory"]["everstone"] = 1
        ok, msg = self.engine.use_item(ItemKind.EVERSTONE)
        self.assertTrue(ok)
        self.assertEqual(self.engine.active_mon.held_item, "everstone")

        # Verify StorageManager serialization preserves held_item
        mon_dict = StorageManager.mon_to_dict(self.engine.active_mon)
        self.assertEqual(mon_dict.get("held_item"), "everstone")
        loaded_mon = StorageManager.dict_to_mon(mon_dict)
        self.assertEqual(loaded_mon.held_item, "everstone")

        # Verify Trainer Card displays held item
        card = self.engine.generate_trainer_card()
        self.assertIn("Everstone", card)

        # Verify Companion TUI tab displays held item
        app = MagicMock()
        app.engine = self.engine
        app.active_mon = self.engine.active_mon
        app.current_difficulty = self.engine.current_difficulty
        app.tracker = MagicMock()
        app.tracker.get_daily_burn_profile.return_value = {}
        
        summary = {
            "today_tokens": 100_000,
            "antigravity_today": 100_000,
            "week_tokens": 500_000,
            "month_tokens": 1_000_000,
            "total_tokens": 5_000_000,
            "burn_rate_tpm": 10_000,
            "active_days": []
        }
        stdout_trap = io.StringIO()
        with unittest.mock.patch("sys.stdout", stdout_trap):
            render_companion(app, summary)
        output = stdout_trap.getvalue()
        self.assertIn("Everstone", output)
        self.assertIn("EVERSTONE", output)

        # Test unequip
        ok_unequip, msg_unequip = self.engine.unequip_item()
        self.assertTrue(ok_unequip)
        self.assertIsNone(self.engine.active_mon.held_item)
        self.assertEqual(self.engine.state["inventory"]["everstone"], 1)

    def test_term_deposits_system(self):
        self.engine.state["used_since_install"] = 100_000_000
        initial_tokens = self.engine.available_tokens

        # Open 3-day CD with 10M
        ok, msg = self.engine.open_cd("10m", 3)
        self.assertTrue(ok)
        self.assertEqual(self.engine.available_tokens, initial_tokens - 10_000_000)
        cds = self.engine.state.get("term_deposits", [])
        self.assertEqual(len(cds), 1)
        self.assertEqual(cds[0]["principal"], 10_000_000)
        self.assertEqual(cds[0]["term_days"], 3)
        self.assertFalse(cds[0]["matured"])

        # Premature claim should fail
        ok_claim, msg_claim = self.engine.claim_cd("1")
        self.assertFalse(ok_claim)
        self.assertIn("not matured", msg_claim)

        # Early break forfeits interest and incurs 10% penalty
        ok_break, msg_break = self.engine.break_cd("1")
        self.assertTrue(ok_break)
        self.assertEqual(len(self.engine.state.get("term_deposits", [])), 0)
        self.assertEqual(self.engine.available_tokens, initial_tokens - 1_000_000)

        # Open a 7-day CD and let it mature through day rollovers
        ok, msg = self.engine.open_cd("10m", 7)
        self.assertTrue(ok)
        self.engine.state["last_active_date"] = "2026-08-01"
        self.engine.state["install_baseline_set"] = True
        
        # Advance 7 days
        self.engine.process_usage(100_000_000, ["2026-08-01", "2026-08-08"])
        cds = self.engine.state.get("term_deposits", [])
        self.assertEqual(len(cds), 1)
        self.assertTrue(cds[0]["matured"])
        self.assertGreater(cds[0]["current_value"], 10_000_000)

        # Claim matured CD
        cur_val = cds[0]["current_value"]
        before_claim = self.engine.available_tokens
        ok_claim, msg_claim = self.engine.claim_cd("all")
        self.assertTrue(ok_claim)
        self.assertEqual(len(self.engine.state.get("term_deposits", [])), 0)
        self.assertEqual(self.engine.available_tokens, before_claim + cur_val)

    def test_corporate_investments_and_perks(self):
        self.engine.state["used_since_install"] = 200_000_000

        self.assertFalse(self.engine.has_perk("silph"))
        self.assertFalse(self.engine.has_perk("devon"))

        # Buy 2 shares of Silph and 1 share of Devon using stock codes (case-insensitive)
        ok_silph, msg_silph = self.engine.invest_corporate("SILPH", "2")
        self.assertTrue(ok_silph)
        ok_devon, msg_devon = self.engine.invest_corporate("DEVON", "1")
        self.assertTrue(ok_devon)
        # Also verify ticker alias DEVN works
        ok_devn_alias, _ = self.engine.invest_corporate("DEVN", "1")
        self.assertTrue(ok_devn_alias)

        self.assertTrue(self.engine.has_perk("silph"))
        self.assertTrue(self.engine.has_perk("devon"))
        self.assertFalse(self.engine.has_perk("macro"))

        # Test Devon perk: 10% discount on Shop Rare Candy
        rc_base = ItemKind.RARE_CANDY.price_for(self.engine.current_difficulty)
        expected_cost = int(rc_base * 0.90)
        tokens_before_rc = self.engine.available_tokens
        ok_buy, msg_buy = self.engine.buy_item(ItemKind.RARE_CANDY, 1)
        self.assertTrue(ok_buy)
        self.assertEqual(tokens_before_rc - self.engine.available_tokens, expected_cost)

        # Test Day rollover dividend payout with streak bonus
        self.engine.state["streak_days"] = 5
        self.engine.state["last_active_date"] = "2026-08-01"
        self.engine.state["install_baseline_set"] = True
        avail_before_div = self.engine.available_tokens
        self.engine.process_usage(200_000_000, ["2026-08-01", "2026-08-02"])
        self.assertGreater(self.engine.available_tokens, avail_before_div)

        # Divest 1 share of Silph using stock code (10M gross -> 9M net with 10% liquidation spread)
        avail_before_divest = self.engine.available_tokens
        ok_divest, msg_divest = self.engine.divest_corporate("SILPH", "1")
        self.assertTrue(ok_divest)
        self.assertEqual(self.engine.available_tokens, avail_before_divest + 9_000_000)
        self.assertEqual(self.engine.state["investments"]["silph"], 1)

    def test_black_market_and_held_items(self):
        self.engine.state["used_since_install"] = 500_000_000
        bm = self.engine.get_or_init_black_market(force_open=True)
        self.assertTrue(bm["is_open"])
        self.assertEqual(len(bm["deals"]), 4)

        # Test purchasing first deal
        deal = bm["deals"][0]
        initial_stock = deal["stock"]
        ok, msg = self.engine.buy_black_market_deal(str(deal["id"]), 1)
        self.assertTrue(ok)
        self.assertEqual(deal["stock"], initial_stock - 1)

        # Test equipping new held items
        mon, _ = self.engine.hatch_egg(0)
        self.engine.state["inventory"]["choice_band"] = 1
        ok_band, msg_band = self.engine.use_item(ItemKind.CHOICE_BAND)
        self.assertTrue(ok_band)
        self.assertEqual(self.engine.active_mon.held_item, "choice_band")

        # Test Choice Band damage boost in boss battle
        self.engine.state["active_boss"] = {
            "id": "boss_1",
            "name": "Brock & Geodude",
            "sp_id": 74,
            "badge": "🪨 Boulder Badge",
            "current_hp": 100_000,
            "hp": 100_000,
            "reward": "rare_candy"
        }
        self.engine._update_boss_battle(10_000)
        # Normal base damage = 10,000; with Choice Band (+50%) = 15,000 -> 85,000 HP remaining
        self.assertEqual(self.engine.state["active_boss"]["current_hp"], 85_000)

    def test_72_column_layout_compliance(self):
        import io
        import re
        from unittest.mock import MagicMock
        from poketokenbar.tui_tabs.bank import render_bank_tab
        from poketokenbar.tui_tabs.shop import render_shop_tab

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')

        app = MagicMock()
        app.engine = self.engine
        app.engine.state["used_since_install"] = 200_000_000
        app.engine.open_cd("10m", 3)
        app.engine.invest_corporate("SILPH", "2")
        app.engine.invest_corporate("MAUV", "1")

        # Test Bank Checking
        app.bank_subtab = "checking"
        trap = io.StringIO()
        with unittest.mock.patch("sys.stdout", trap):
            render_bank_tab(app)
        checking_output = trap.getvalue()
        self.assertNotIn("c' for Term Deposits", checking_output)
        for line in checking_output.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Bank Checking line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Test Bank CD
        app.bank_subtab = "cd"
        trap = io.StringIO()
        with unittest.mock.patch("sys.stdout", trap):
            render_bank_tab(app)
        cd_output = trap.getvalue()
        self.assertNotIn("b' for Checking", cd_output)
        for line in cd_output.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Bank CD line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Test Bank Stocks (Page 1)
        app.bank_subtab = "stocks"
        app.stock_page = 1
        trap = io.StringIO()
        with unittest.mock.patch("sys.stdout", trap):
            render_bank_tab(app)
        stocks_p1_output = trap.getvalue()
        self.assertNotIn("b' for Checking", stocks_p1_output)
        self.assertIn("Page 1/2", stocks_p1_output)
        for line in stocks_p1_output.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Bank Stocks P1 line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Test Bank Stocks (Page 2)
        app.stock_page = 2
        trap = io.StringIO()
        with unittest.mock.patch("sys.stdout", trap):
            render_bank_tab(app)
        stocks_p2_output = trap.getvalue()
        self.assertIn("Page 2/2", stocks_p2_output)
        for line in stocks_p2_output.split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Bank Stocks P2 line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Test Shop Normal
        app.shop_view = "normal"
        app.shop_page = 1
        trap = io.StringIO()
        with unittest.mock.patch("sys.stdout", trap):
            render_shop_tab(app)
        for line in trap.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Shop Normal line exceeds 72 cols: '{clean}' (len={len(clean)})")

        # Test Shop Black Market
        app.shop_view = "black_market"
        trap = io.StringIO()
        with unittest.mock.patch("sys.stdout", trap):
            render_shop_tab(app)
        for line in trap.getvalue().split("\n"):
            clean = ansi_regex.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Shop Black Market line exceeds 72 cols: '{clean}' (len={len(clean)})")

if __name__ == "__main__":
    unittest.main()

