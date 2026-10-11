"""Unit tests for Resort Area Luxury Villa & Penthouse endgame token sink."""

import io
import os
import re
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.models import (
    VILLA_DEED_COST, VILLA_FACILITIES, VILLA_DECOR, PATTERN_BULL_RALLY
)
from poketokenbar.tui_tabs.bank import render_bank_tab, _render_stock_terminal


class TestResortVilla(unittest.TestCase):
    def setUp(self):
        self.temp_state = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_state.close()
        os.environ["PTB_STATE_FILE"] = self.temp_state.name
        self.engine = CompanionEngine()
        # Give generous spendable tokens for test setup
        self.engine.state["used_since_install"] = 100_000_000_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.check_penthouse_invitation()
        self.engine.pay_penthouse_vip_fee()
        self.engine.save()

    def tearDown(self):
        if os.path.exists(self.temp_state.name):
            os.remove(self.temp_state.name)
        bak = self.temp_state.name.replace(".json", ".json.bak")
        if os.path.exists(bak):
            os.remove(bak)

    def test_villa_initial_locked_state(self):
        self.engine.get_villa_state()["unlocked"] = False
        self.engine.get_villa_state()["vip_fee_paid"] = False
        self.assertFalse(self.engine.is_villa_unlocked())
        self.assertEqual(self.engine.get_villa_facility_level("nursery"), 0)

        # Cannot upgrade or furnish before deed
        ok, msg = self.engine.upgrade_villa_facility("1")
        self.assertFalse(ok)
        self.assertIn("acquire", msg.lower())

        ok, msg = self.engine.purchase_villa_decor("1")
        self.assertFalse(ok)
        self.assertIn("acquire", msg.lower())

    def test_purchase_villa_deed(self):
        self.engine.get_villa_state()["vip_fee_paid"] = True
        # Insufficient tokens check
        self.engine.state["spent_tokens"] = self.engine.state["used_since_install"] - (VILLA_DEED_COST - 1)
        ok, msg = self.engine.purchase_villa_deed()
        self.assertFalse(ok)
        self.assertIn("Not enough tokens", msg)

        # Sufficient tokens
        self.engine.state["spent_tokens"] = 0
        ok, msg = self.engine.purchase_villa_deed()
        self.assertTrue(ok)
        self.assertTrue(self.engine.is_villa_unlocked())
        self.assertGreaterEqual(self.engine.get_villa_total_value(), VILLA_DEED_COST)

        # Cannot purchase twice
        ok2, msg2 = self.engine.purchase_villa_deed()
        self.assertFalse(ok2)
        self.assertIn("already own", msg2)

    def test_facility_upgrades(self):
        self.engine.purchase_villa_deed()

        # Upgrade Nursery by index
        ok, msg = self.engine.upgrade_villa_facility("1")
        self.assertTrue(ok)
        self.assertEqual(self.engine.get_villa_facility_level("nursery"), 1)

        # Upgrade Springs by key
        ok, msg = self.engine.upgrade_villa_facility("springs")
        self.assertTrue(ok)
        self.assertEqual(self.engine.get_villa_facility_level("springs"), 1)

        # Max out Chromatic Resonator (only 1 level)
        ok, msg = self.engine.upgrade_villa_facility("4")
        self.assertTrue(ok)
        self.assertEqual(self.engine.get_villa_facility_level("chromatic_lab"), 1)

        # Trying to exceed max level
        ok, msg = self.engine.upgrade_villa_facility("4")
        self.assertFalse(ok)
        self.assertIn("already at maximum level", msg)

    def test_cryo_nursery_parallel_incubation(self):
        self.engine.purchase_villa_deed()
        # Upgrade Nursery to Lv 3 (all eggs incubate at 2x speed)
        self.engine.upgrade_villa_facility("nursery")
        self.engine.upgrade_villa_facility("nursery")
        self.engine.upgrade_villa_facility("nursery")
        self.assertEqual(self.engine.get_villa_facility_level("nursery"), 3)

        # Queue 2 eggs in pending_eggs
        self.engine.state["pending_eggs"] = [
            {"tier": "common", "progress": 0},
            {"tier": "uncommon", "progress": 0},
        ]
        self.engine.save()

        # Process delta = 500_000 -> with 2x speed, should add 1_000_000 to both
        events = []
        self.engine._process_villa_cryo_nursery(500_000, 3, events)
        pending = self.engine.state.get("pending_eggs", [])
        self.assertEqual(len(pending), 2)
        self.assertEqual(pending[0]["progress"], 1_000_000)
        self.assertEqual(pending[1]["progress"], 1_000_000)

        # Process another delta to hatch the common egg (1.5M threshold)
        self.engine._process_villa_cryo_nursery(300_000, 3, events)
        # 1_000_000 + 600_000 = 1_600_000 >= 1_500_000 -> Common egg hatches!
        pending_after = self.engine.state.get("pending_eggs", [])
        self.assertEqual(len(pending_after), 1)
        self.assertEqual(pending_after[0]["tier"], "uncommon")

    def test_hot_springs_decay_and_exp_perks(self):
        self.engine.purchase_villa_deed()
        # Upgrade springs to Lv 3
        self.engine.upgrade_villa_facility("springs")
        self.engine.upgrade_villa_facility("springs")
        self.engine.upgrade_villa_facility("springs")
        self.assertEqual(self.engine.get_villa_facility_level("springs"), 3)

        # Add active companion
        self.engine.state["active_mon"] = {
            "base_id": 25, "current_id": 25, "stage_index": 0, "path_ids": [25, 26],
            "rarity": "uncommon", "happiness": 100, "used_at_stage": 0, "is_mega": False,
            "held_item": None, "is_shiny": False, "is_graduated": False
        }
        self.engine.state["install_baseline_set"] = True
        self.engine.state["last_active_date"] = "2026-10-01"
        self.engine.save()

        # Missed 3 days rollover -> With Springs Lv 3, happiness should be fully preserved!
        events = []
        self.engine._update_streak_and_quests(100_000, events)
        active = self.engine.active_mon
        self.assertEqual(active.happiness, 100)

    def test_chromatic_shiny_transmutation(self):
        self.engine.purchase_villa_deed()
        self.engine.upgrade_villa_facility("chromatic_lab")

        # Set up a companion in dex/roster
        self.engine.state["dex"] = [{
            "species_id": 25,
            "base_id": 25,
            "status": "active",
            "is_shiny": False,
            "mon_state": {"species_id": 25, "base_id": 25, "is_shiny": False, "happiness": 100}
        }]
        self.engine.state["active_mon"] = {
            "base_id": 25, "current_id": 25, "stage_index": 0, "path_ids": [25, 26],
            "rarity": "uncommon", "happiness": 100, "used_at_stage": 0, "is_mega": False,
            "held_item": None, "is_shiny": False, "is_graduated": False
        }
        self.engine.save()

        ok, msg = self.engine.transmute_villa_shiny(1)
        self.assertTrue(ok)
        self.assertIn("CHROMATIC TRANSMUTATION", msg)
        self.assertTrue(self.engine.state["dex"][0]["is_shiny"])
        self.assertTrue(self.engine.active_mon.is_shiny)

        # Trying to transmute already shiny
        ok2, msg2 = self.engine.transmute_villa_shiny(1)
        self.assertFalse(ok2)
        self.assertIn("already Shiny", msg2)

    def test_decor_furnishings_and_tycoon_title(self):
        self.engine.purchase_villa_deed()
        self.assertEqual(len(self.engine.get_villa_state().get("decor", [])), 0)

        # Buy 5 decor items
        for i in range(1, 6):
            ok, msg = self.engine.purchase_villa_decor(str(i))
            self.assertTrue(ok)

        self.assertNotIn("👑 Sovereign Tycoon", self.engine.state.get("gym_badges", []))

        # Buy 6th decor item (Throne)
        ok, msg = self.engine.purchase_villa_decor("6")
        self.assertTrue(ok)
        self.assertIn("👑 Sovereign Tycoon", msg)
        self.assertIn("👑 Sovereign Tycoon", self.engine.state.get("gym_badges", []))

    def test_whale_catalyst_trigger(self):
        self.engine.purchase_villa_deed()
        # Upgrade trading desk to Lv 3
        self.engine.upgrade_villa_facility("trading_desk")
        self.engine.upgrade_villa_facility("trading_desk")
        self.engine.upgrade_villa_facility("trading_desk")
        self.assertEqual(self.engine.get_villa_facility_level("trading_desk"), 3)

        ok, msg = self.engine.trigger_villa_catalyst("silph")
        self.assertTrue(ok)
        self.assertIn("WHALE CATALYST DEPLOYED", msg)

        sm = self.engine.get_or_init_stock_market()
        st = sm.get("market_state", {}).get("silph", {})
        self.assertEqual(st.get("pattern"), PATTERN_BULL_RALLY)

    def test_tui_layout_compliance(self):
        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine
        app.bank_subtab = "villa"

        # 1. Test Locked Villa rendering <= 72 columns
        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_bank_tab(app)
        clean_lines = [ansi_regex.sub("", l) for l in trap.getvalue().split("\n")]
        for line in clean_lines:
            self.assertLessEqual(len(line), 72, f"Locked Villa line exceeds 72 cols ({len(line)}): '{line}'")

        # 2. Test Unlocked Villa rendering <= 72 columns
        self.engine.purchase_villa_deed()
        for i in range(1, 5):
            self.engine.upgrade_villa_facility(str(i))
        for i in range(1, 7):
            self.engine.purchase_villa_decor(str(i))

        trap2 = io.StringIO()
        with patch("sys.stdout", trap2):
            render_bank_tab(app)
        clean_lines2 = [ansi_regex.sub("", l) for l in trap2.getvalue().split("\n")]
        for line in clean_lines2:
            self.assertLessEqual(len(line), 72, f"Unlocked Villa line exceeds 72 cols ({len(line)}): '{line}'")

        # 3. Test Stock Terminal with Quantum Telemetry <= 72 columns
        trap3 = io.StringIO()
        with patch("sys.stdout", trap3):
            _render_stock_terminal(app, self.engine.available_tokens, "silph")
        clean_lines3 = [ansi_regex.sub("", l) for l in trap3.getvalue().split("\n")]
        for line in clean_lines3:
            self.assertLessEqual(len(line), 72, f"Stock Terminal line exceeds 72 cols ({len(line)}): '{line}'")


if __name__ == "__main__":
    unittest.main()
