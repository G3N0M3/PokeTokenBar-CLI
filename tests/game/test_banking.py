"""Tests for banking system, deposit/loan interest, and economic transactions."""

import os
import unittest
import tempfile
from poketokenbar.game.companion import CompanionEngine


class TestBankDailyInterest(unittest.TestCase):
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

    def test_bank_checking_view_displays_daily_interest(self):
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.bank import render_bank_tab

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        self.engine.state["bank_balance"] = 10_000_000
        self.engine.state["bank_loan"] = 5_000_000

        app = MagicMock()
        app.engine = self.engine
        app.bank_subtab = "checking"

        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_bank_tab(app)

        output = trap.getvalue()
        clean_lines = [ansi_regex.sub("", l) for l in output.split("\n")]

        # Check daily deposit interest (+500.0K/day interest)
        self.assertIn("+500.0K/day interest", output)
        self.assertIn("+5% daily interest (+500.0K tokens/day)", output)

        # Check daily loan interest (+500.0K/day interest)
        self.assertIn("+500.0K/day interest", output)
        self.assertIn("+10% daily interest (+500.0K debt/day", output)

        # 72-col compliance check
        for line in clean_lines:
            self.assertLessEqual(len(line), 72, f"Line exceeds 72 cols: '{line}'")

    def test_bank_checking_view_zero_balances(self):
        import io
        import re
        from unittest.mock import MagicMock, patch
        from poketokenbar.tui_tabs.bank import render_bank_tab

        ansi_regex = re.compile(r'\x1b\[[0-9;]*[mK]')
        self.engine.state["bank_balance"] = 0
        self.engine.state["bank_loan"] = 0

        app = MagicMock()
        app.engine = self.engine
        app.bank_subtab = "checking"

        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_bank_tab(app)

        output = trap.getvalue()
        clean_lines = [ansi_regex.sub("", l) for l in output.split("\n")]

        self.assertIn("+0/day interest", output)
        self.assertIn("No active debt", output)
        self.assertIn("+5% daily interest (+0 tokens/day)", output)
        self.assertIn("+10% daily interest (+0 debt/day", output)

        for line in clean_lines:
            self.assertLessEqual(len(line), 72, f"Line exceeds 72 cols: '{line}'")

    def test_bank_transactions_feedback_daily_interest(self):
        self.engine.state["used_since_install"] = 50_000_000
        self.engine.state["spent_tokens"] = 0

        # Deposit 10M -> balance 10M -> daily interest +500K/day
        ok, msg = self.engine.handle_bank_transaction("deposit", "10m")
        self.assertTrue(ok)
        self.assertIn("Deposited 10.0M tokens", msg)
        self.assertIn("+500.0K/day interest", msg)

        # Withdraw 2M -> balance 8M -> daily interest +400K/day
        ok, msg = self.engine.handle_bank_transaction("withdraw", "2m")
        self.assertTrue(ok)
        self.assertIn("Withdrew 2.0M tokens", msg)
        self.assertIn("+400.0K/day interest", msg)

        # Loan 5M -> debt 5M -> daily debt interest +500K/day
        ok, msg = self.engine.handle_bank_transaction("loan", "5m")
        self.assertTrue(ok)
        self.assertIn("Took loan of 5.0M tokens", msg)
        self.assertIn("+500.0K/day interest", msg)

        # Payoff 3M -> debt 2M -> daily debt interest +200K/day
        ok, msg = self.engine.handle_bank_transaction("payoff", "3m")
        self.assertTrue(ok)
        self.assertIn("Paid off 3.0M tokens", msg)
        self.assertIn("+200.0K/day interest", msg)

        # Payoff remaining 2M -> debt 0 -> debt fully cleared
        ok, msg = self.engine.handle_bank_transaction("payoff", "2m")
        self.assertTrue(ok)
        self.assertIn("debt fully cleared", msg)


if __name__ == "__main__":
    unittest.main()
