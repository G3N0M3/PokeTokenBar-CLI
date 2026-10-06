"""Unit tests for Resort Area Executive Penthouse, 100B invitation, and 500M VIP fee."""

import io
import os
import re
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.models import (
    PENTHOUSE_WEALTH_THRESHOLD,
    PENTHOUSE_VIP_FEE,
    PENTHOUSE_DEED_COST,
    PENTHOUSE_FACILITIES,
    PENTHOUSE_DECOR,
    PATTERN_BULL_RALLY
)
from poketokenbar.tui_tabs.bank import render_bank_tab, _render_stock_terminal
from poketokenbar.tui_tabs.penthouse import (
    _render_concierge_desk_view,
    _render_deed_inspection_view,
    _render_unlocked_penthouse_view,
    _render_facility_help_view
)


class TestResortPenthouse(unittest.TestCase):
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

    def test_initial_locked_state_under_100b(self):
        # Initial state has 0 tokens
        self.assertFalse(self.engine.is_penthouse_available())
        self.assertFalse(self.engine.is_penthouse_invitation_pending())
        self.assertFalse(self.engine.is_penthouse_vip_paid())
        self.assertFalse(self.engine.is_penthouse_unlocked())

        unlocked, msg = self.engine.check_penthouse_invitation()
        self.assertFalse(unlocked)

        # Cannot pay VIP fee or buy deed
        ok, err = self.engine.pay_penthouse_vip_fee()
        self.assertFalse(ok)
        self.assertIn("Not enough spendable tokens", err)

        ok, err = self.engine.purchase_penthouse_deed()
        self.assertFalse(ok)
        self.assertIn("VIP Concierge fee", err)

    def test_invitation_triggered_at_100b(self):
        # Set holding tokens to 60B and bank balance to 40B -> 100B total wealth
        self.engine.state["used_since_install"] = 60_000_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.state["bank_balance"] = 40_000_000_000
        self.engine.save()

        self.assertTrue(self.engine.is_penthouse_available())
        unlocked, msg = self.engine.check_penthouse_invitation()
        self.assertTrue(unlocked)
        self.assertIn("Resort Area Penthouse Invitation", msg)
        self.assertTrue(self.engine.is_penthouse_invitation_pending())

        # Postpone invitation
        self.engine.postpone_penthouse_invitation()
        self.assertFalse(self.engine.is_penthouse_invitation_pending())
        self.assertTrue(self.engine.is_penthouse_available())

    def test_pay_vip_fee_requires_500m(self):
        # Trigger invitation
        self.engine.state["used_since_install"] = 100_000_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.check_penthouse_invitation()

        # Cannot buy deed without VIP fee
        ok, err = self.engine.purchase_penthouse_deed()
        self.assertFalse(ok)
        self.assertIn("VIP Concierge fee", err)

        # Pay VIP fee (500M)
        ok, msg = self.engine.pay_penthouse_vip_fee()
        self.assertTrue(ok)
        self.assertIn("VIP CLEARANCE GRANTED", msg)
        self.assertTrue(self.engine.is_penthouse_vip_paid())
        self.assertEqual(self.engine.state.get("spent_tokens"), PENTHOUSE_VIP_FEE)

        # Cannot pay twice
        ok2, err2 = self.engine.pay_penthouse_vip_fee()
        self.assertFalse(ok2)
        self.assertIn("already been granted", err2)

    def test_purchase_penthouse_deed(self):
        # Setup qualified state with 10T tokens and VIP fee paid
        self.engine.state["used_since_install"] = 10_000_000_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.check_penthouse_invitation()
        self.engine.pay_penthouse_vip_fee()

        ok, msg = self.engine.purchase_penthouse_deed()
        self.assertTrue(ok)
        self.assertTrue(self.engine.is_penthouse_unlocked())
        self.assertGreaterEqual(self.engine.get_penthouse_total_value(), PENTHOUSE_DEED_COST)

        # Cannot purchase twice
        ok2, err2 = self.engine.purchase_penthouse_deed()
        self.assertFalse(ok2)
        self.assertIn("already own", err2)

    def test_facility_upgrades_and_decor(self):
        self.engine.state["used_since_install"] = 50_000_000_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.check_penthouse_invitation()
        self.engine.pay_penthouse_vip_fee()
        self.engine.purchase_penthouse_deed()

        # Upgrade Nursery to Lv 1
        ok, msg = self.engine.upgrade_penthouse_facility("1")
        self.assertTrue(ok)
        self.assertEqual(self.engine.get_penthouse_facility_level("nursery"), 1)

        # Furnish all 6 decor items
        for i in range(1, 6):
            ok, msg = self.engine.purchase_penthouse_decor(str(i))
            self.assertTrue(ok)
        self.assertNotIn("👑 Sovereign Tycoon", self.engine.state.get("gym_badges", []))

        # 6th decor grants title
        ok, msg = self.engine.purchase_penthouse_decor("6")
        self.assertTrue(ok)
        self.assertIn("👑 Sovereign Tycoon", self.engine.state.get("gym_badges", []))

    def test_tui_layout_compliance(self):
        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        app = MagicMock()
        app.engine = self.engine

        # 1. Bank tab when Penthouse unavailable (<100B wealth)
        app.bank_subtab = "checking"
        trap1 = io.StringIO()
        with patch("sys.stdout", trap1):
            render_bank_tab(app)
        clean_lines1 = [ansi_regex.sub("", l) for l in trap1.getvalue().split("\n")]
        for line in clean_lines1:
            self.assertLessEqual(len(line), 72, f"Bank tab line exceeds 72 cols: '{line}'")

        # 2. Bank tab when Penthouse available (>=100B wealth)
        self.engine.state["used_since_install"] = 100_000_000_000
        trap2 = io.StringIO()
        with patch("sys.stdout", trap2):
            render_bank_tab(app)
        clean_lines2 = [ansi_regex.sub("", l) for l in trap2.getvalue().split("\n")]
        for line in clean_lines2:
            self.assertLessEqual(len(line), 72, f"Bank tab (with P) line exceeds 72 cols: '{line}'")

        # 3. Concierge Desk view <= 72 cols
        trap3 = io.StringIO()
        with patch("sys.stdout", trap3):
            _render_concierge_desk_view(app, self.engine.available_tokens)
        clean_lines3 = [ansi_regex.sub("", l) for l in trap3.getvalue().split("\n")]
        for line in clean_lines3:
            self.assertLessEqual(len(line), 72, f"Concierge Desk line exceeds 72 cols: '{line}'")

        # 4. Deed Inspection view <= 72 cols
        trap4 = io.StringIO()
        with patch("sys.stdout", trap4):
            _render_deed_inspection_view(app, self.engine.available_tokens)
        clean_lines4 = [ansi_regex.sub("", l) for l in trap4.getvalue().split("\n")]
        for line in clean_lines4:
            self.assertLessEqual(len(line), 72, f"Deed Inspection line exceeds 72 cols: '{line}'")

        # 5. Unlocked Penthouse view <= 72 cols
        trap5 = io.StringIO()
        with patch("sys.stdout", trap5):
            _render_unlocked_penthouse_view(app, self.engine.available_tokens)
        clean_lines5 = [ansi_regex.sub("", l) for l in trap5.getvalue().split("\n")]
        for line in clean_lines5:
            self.assertLessEqual(len(line), 72, f"Unlocked Penthouse line exceeds 72 cols: '{line}'")

        # 6. Invitation modal with letter art <= 72 cols
        from poketokenbar.tui_tabs.penthouse import render_penthouse_invitation
        trap6 = io.StringIO()
        with patch("sys.stdout", trap6), patch("sys.stdin.readline", return_value="3\n"):
            render_penthouse_invitation(app)
        clean_lines6 = [ansi_regex.sub("", l) for l in trap6.getvalue().split("\n")]
        for line in clean_lines6:
            self.assertLessEqual(len(line), 72, f"Invitation modal line exceeds 72 cols: '{line}'")

        # 7. Wing Help view (all and single wings) <= 72 cols
        trap7 = io.StringIO()
        with patch("sys.stdout", trap7):
            _render_facility_help_view(app, self.engine.available_tokens)
        clean_lines7 = [ansi_regex.sub("", l) for l in trap7.getvalue().split("\n")]
        for line in clean_lines7:
            self.assertLessEqual(len(line), 72, f"Facility/Wing Help view line exceeds 72 cols: '{line}'")

        # 7b. Single Wing Help views <= 72 cols
        for w_idx in range(1, 5):
            app.penthouse_help_wing = w_idx
            trap_w = io.StringIO()
            with patch("sys.stdout", trap_w):
                _render_facility_help_view(app, self.engine.available_tokens)
            clean_lines_w = [ansi_regex.sub("", l) for l in trap_w.getvalue().split("\n")]
            for line in clean_lines_w:
                self.assertLessEqual(len(line), 72, f"Single Wing [{w_idx}] Help line exceeds 72 cols: '{line}'")
        app.penthouse_help_wing = None

        # 8. Assert that obsolete hot springs icon '♨' is NOT present in any output
        all_rendered_text = "".join([
            trap1.getvalue(), trap2.getvalue(), trap3.getvalue(),
            trap4.getvalue(), trap5.getvalue(), trap6.getvalue(), trap7.getvalue()
        ])
        self.assertNotIn("♨", all_rendered_text, "Found broken hot springs icon '♨' in rendered output!")

    def test_decor_interaction_and_perks(self):
        from poketokenbar.game.models import MonState, Rarity
        self.engine.state["used_since_install"] = 50_000_000_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.check_penthouse_invitation()
        self.engine.pay_penthouse_vip_fee()
        self.engine.purchase_penthouse_deed()

        # Cannot interact with unowned decor
        ok, msg = self.engine.interact_penthouse_decor("1")
        self.assertFalse(ok)
        self.assertIn("haven't installed", msg)

        # Mock active companion with 50 happiness
        mon = MonState(
            base_id=25,
            path_ids=[25, 26],
            planned_path_ids=[25, 26],
            stage_index=0,
            used_at_stage=0,
            rarity=Rarity.COMMON,
            total_forms=2,
            happiness=50
        )
        self.engine.set_active_mon(mon)

        # 1. Piano: purchase and play -> +10 happiness
        self.engine.purchase_penthouse_decor("1")
        self.assertTrue(self.engine.has_penthouse_decor("piano"))
        ok, msg = self.engine.interact_penthouse_decor("1")
        self.assertTrue(ok)
        self.assertIn("Piano", msg)
        self.assertEqual(self.engine.active_mon.happiness, 60)

        # 2. Chandelier: purchase -> +5% expedition tokens hook
        self.engine.purchase_penthouse_decor("2")
        self.assertTrue(self.engine.has_penthouse_decor("chandelier"))
        ok, msg = self.engine.interact_penthouse_decor("2")
        self.assertTrue(ok)
        self.assertIn("Chandelier", msg)

        # 3. Statue: purchase -> +10% macro multiplier for raids
        base_macro = self.engine.get_macro_multiplier()
        self.engine.purchase_penthouse_decor("3")
        self.assertTrue(self.engine.has_penthouse_decor("statue"))
        boosted_macro = self.engine.get_macro_multiplier()
        self.assertAlmostEqual(boosted_macro, base_macro + 0.10)
        ok, msg = self.engine.interact_penthouse_decor("3")
        self.assertTrue(ok)
        self.assertIn("Statue", msg)

        # 4. Hologram: purchase -> +5% mauville multiplier for casino
        base_mauv = self.engine.get_mauville_multiplier()
        self.engine.purchase_penthouse_decor("4")
        self.assertTrue(self.engine.has_penthouse_decor("hologram"))
        boosted_mauv = self.engine.get_mauville_multiplier()
        self.assertAlmostEqual(boosted_mauv, base_mauv + 0.05)
        ok, msg = self.engine.interact_penthouse_decor("4")
        self.assertTrue(ok)
        self.assertIn("Hologram", msg)

        # 5. Fountain: purchase -> restores happiness to 100
        self.engine.active_mon.happiness = 25
        self.engine.set_active_mon(self.engine.active_mon)
        self.engine.purchase_penthouse_decor("5")
        self.assertTrue(self.engine.has_penthouse_decor("fountain"))
        ok, msg = self.engine.interact_penthouse_decor("5")
        self.assertTrue(ok)
        self.assertIn("Fountain", msg)
        self.assertEqual(self.engine.active_mon.happiness, 100)

        # 6. Throne: purchase -> sovereign title and dividend bonus
        self.engine.purchase_penthouse_decor("6")
        self.assertTrue(self.engine.has_penthouse_decor("throne"))
        ok, msg = self.engine.interact_penthouse_decor("6")
        self.assertTrue(ok)
        self.assertIn("Throne", msg)

    def test_penthouse_router_and_help_subview(self):
        from poketokenbar.tui.router import CommandRouter
        app = MagicMock()
        app.engine = self.engine
        app.current_tab = 10
        app.bank_subtab = "penthouse"
        app.penthouse_subview = "main"
        app.penthouse_help_wing = None

        # 1. 'help' opens full wings guide
        CommandRouter.dispatch(app, "help")
        self.assertEqual(app.penthouse_subview, "help")
        self.assertIsNone(app.penthouse_help_wing)

        # 2. 'help wing 1' opens Wing 1 specific guide
        CommandRouter.dispatch(app, "help wing 1")
        self.assertEqual(app.penthouse_subview, "help")
        self.assertEqual(app.penthouse_help_wing, 1)

        # 3. 'help room 2' opens Wing 2 specific guide (alias support)
        CommandRouter.dispatch(app, "help room 2")
        self.assertEqual(app.penthouse_subview, "help")
        self.assertEqual(app.penthouse_help_wing, 2)

        # 4. 'help facility 3' opens Wing 3 specific guide (alias support)
        CommandRouter.dispatch(app, "help facility 3")
        self.assertEqual(app.penthouse_subview, "help")
        self.assertEqual(app.penthouse_help_wing, 3)

        # 5. 'help 4' opens Wing 4 specific guide
        CommandRouter.dispatch(app, "help 4")
        self.assertEqual(app.penthouse_subview, "help")
        self.assertEqual(app.penthouse_help_wing, 4)

        # 6. 'back' exits guide back to main penthouse overview
        CommandRouter.dispatch(app, "back")
        self.assertEqual(app.penthouse_subview, "main")
        self.assertIsNone(app.penthouse_help_wing)

        # 7. 'back' from main exits to checking
        CommandRouter.dispatch(app, "back")
        self.assertEqual(app.bank_subtab, "checking")

    def test_penthouse_p_navigation_from_all_bank_subtabs(self):
        from poketokenbar.tui.router import CommandRouter
        self.engine.state["used_since_install"] = 150_000_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.check_penthouse_invitation()

        app = MagicMock()
        app.engine = self.engine
        app.current_tab = 10

        # 1. From 'cd' (deposits menu), typing 'p' must switch to penthouse
        app.bank_subtab = "cd"
        CommandRouter.dispatch(app, "p")
        self.assertEqual(app.bank_subtab, "penthouse")

        # 2. From 'stocks' (stocks menu), typing 'p' must switch to penthouse
        app.bank_subtab = "stocks"
        CommandRouter.dispatch(app, "p")
        self.assertEqual(app.bank_subtab, "penthouse")

        # 3. From 'checking', typing 'p' must switch to penthouse
        app.bank_subtab = "checking"
        CommandRouter.dispatch(app, "p")
        self.assertEqual(app.bank_subtab, "penthouse")

        # 4. From stock terminal, typing 'p' clears terminal and switches to penthouse
        app.bank_subtab = "stocks"
        app.stock_terminal = "silph"
        CommandRouter.dispatch(app, "p")
        self.assertEqual(app.bank_subtab, "penthouse")
        self.assertIsNone(app.stock_terminal)

        # 5. Full word 'penthouse' also switches to penthouse
        app.bank_subtab = "cd"
        CommandRouter.dispatch(app, "penthouse")
        self.assertEqual(app.bank_subtab, "penthouse")


if __name__ == "__main__":
    unittest.main()
