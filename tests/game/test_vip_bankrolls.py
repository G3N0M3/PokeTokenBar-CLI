import unittest
from unittest.mock import patch

from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.storage import StorageManager
from poketokenbar.game.models import (
    POKER_VIP_MIN_BET,
    VIP_PATRON_DAILY_BANKROLLS,
    VIP_CLEAN_SWEEP_BOUNTY,
)


class TestVIPBankrolls(unittest.TestCase):
    def setUp(self):
        StorageManager.save_state(StorageManager.default_state())
        self.engine = CompanionEngine()
        self.engine.state["poker_vip_unlocked"] = True
        self.engine.state["used_since_install"] = 100_000_000_000_000_000_000  # 100,000.0Q tokens
        self.engine.state["spent_tokens"] = 0
        self.engine.save()

    def test_vip_bankrolls_initialization(self):
        """Verify all VIP patrons are initialized with their default daily bankrolls."""
        bankrolls = self.engine.state.get("vip_bankrolls", {})
        for name, max_val in VIP_PATRON_DAILY_BANKROLLS.items():
            self.assertIn(name, bankrolls)
            self.assertEqual(bankrolls[name]["current"], max_val)
            self.assertEqual(bankrolls[name]["max"], max_val)
        self.assertFalse(self.engine.state.get("vip_clean_sweep_claimed", False))

    def test_vip_bankroll_win_deduction(self):
        """When player wins, chips won are deducted from active opponent's daily stack."""
        self.engine.poker.table_mode = "vip"
        self.engine.poker.active_opponent = "Duchess Eleanor"
        init_stack, _ = self.engine.get_vip_bankroll("Duchess Eleanor")
        self.assertEqual(init_stack, VIP_PATRON_DAILY_BANKROLLS["Duchess Eleanor"])

        # Start hand and simulate opponent fold
        ok, msg = self.engine.play_poker_bet("10t")
        self.assertTrue(ok)
        ok, fold_msg = self.engine._format_opponent_fold("A gracious concession.")
        self.assertTrue(ok)

        new_stack, _ = self.engine.get_vip_bankroll("Duchess Eleanor")
        self.assertLess(new_stack, init_stack)
        self.assertIn("Duchess Eleanor Chips: -", fold_msg)

    def test_vip_bankroll_loss_addition(self):
        """When player folds or loses showdown, chips are credited to opponent's daily stack."""
        self.engine.poker.table_mode = "vip"
        self.engine.poker.active_opponent = "Gentleman Walter"
        init_stack, _ = self.engine.get_vip_bankroll("Gentleman Walter")

        # Player bets and folds
        ok, _ = self.engine.play_poker_bet("10t")
        self.assertTrue(ok)
        ok, msg = self.engine.play_poker_action("fold")
        self.assertTrue(ok)

        new_stack, _ = self.engine.get_vip_bankroll("Gentleman Walter")
        self.assertEqual(new_stack, init_stack + 10_000_000_000_000)
        self.assertIn("Gentleman Walter Chips:", msg)

    def test_vip_patron_bust_and_auto_rotation(self):
        """When a patron's stack drops below minimum bet, they bust and next patron is seated."""
        self.engine.poker.table_mode = "vip"
        self.engine.poker.active_opponent = "Duchess Eleanor"
        # Set Duchess Eleanor to have only 10.0T left
        self.engine.state["vip_bankrolls"]["Duchess Eleanor"]["current"] = 10_000_000_000_000
        self.engine.save()

        # Win a hand against her
        ok, _ = self.engine.play_poker_bet("10t")
        self.assertTrue(ok)
        ok, fold_msg = self.engine._format_opponent_fold("Folded!")
        self.assertTrue(ok)

        # Eleanor stack should now be 0, and she should be busted
        cur_stack, _ = self.engine.get_vip_bankroll("Duchess Eleanor")
        self.assertEqual(cur_stack, 0)
        self.assertIn("DUCHESS ELEANOR HAS BUSTED FOR TODAY", fold_msg)
        # Next patron should be seated
        self.assertNotEqual(self.engine.poker.active_opponent, "Duchess Eleanor")

    def test_cycle_vip_opponent(self):
        """The 'next' command cycles between available patrons."""
        self.engine.poker.table_mode = "vip"
        self.engine.poker.active_opponent = "Duchess Eleanor"

        ok, msg = self.engine.cycle_vip_opponent()
        self.assertTrue(ok)
        self.assertNotEqual(self.engine.poker.active_opponent, "Duchess Eleanor")
        self.assertIn("Seated across from", msg)
        self.assertIn("tokens", msg)
        self.assertNotIn(" / ", msg)

    def test_table_stakes_bet_capping(self):
        """Bet is capped to what the active opponent can cover."""
        self.engine.poker.table_mode = "vip"
        self.engine.poker.active_opponent = "Madame Vivienne"
        # Set Vivienne stack to 20.0T
        self.engine.state["vip_bankrolls"]["Madame Vivienne"]["current"] = 20_000_000_000_000
        self.engine.save()

        # Try betting 100.0T
        ok, msg = self.engine.play_poker_bet("100t")
        self.assertTrue(ok)
        # Effective current bet should be capped at 20.0T
        self.assertEqual(self.engine.poker.current_bet, 20_000_000_000_000)

    def test_all_patrons_busted_and_clean_sweep_bounty(self):
        """Busting all patrons awards the Clean Sweep Bounty and closes VIP tables until midnight."""
        self.engine.poker.table_mode = "vip"

        # Deplete all patrons except one with 10.0T left
        for name in VIP_PATRON_DAILY_BANKROLLS.keys():
            self.engine.state["vip_bankrolls"][name]["current"] = 0
        last_patron = "Madame Vivienne"
        self.engine.state["vip_bankrolls"][last_patron]["current"] = 10_000_000_000_000
        self.engine.poker.active_opponent = last_patron
        self.engine.save()

        tokens_before = self.engine.available_tokens

        # Play last hand and bust Vivienne
        ok, _ = self.engine.play_poker_bet("10t")
        self.assertTrue(ok)
        ok, fold_msg = self.engine._format_opponent_fold("Fold!")
        self.assertTrue(ok)

        # Clean sweep should be awarded!
        self.assertIn("SALON CLEAN SWEEP", fold_msg)
        self.assertTrue(self.engine.state.get("vip_clean_sweep_claimed", False))
        self.assertEqual(self.engine.state.get("vip_clean_sweeps_count", 0), 1)

        # Further bets should be rejected
        ok_next, err_msg = self.engine.play_poker_bet("10t")
        self.assertFalse(ok_next)
        self.assertIn("All VIP patrons are busted for today", err_msg)
        self.assertIn("reset", err_msg.lower())
        self.assertNotIn("refill", err_msg.lower())

    def test_switch_vip_table_announcement_format(self):
        """Entering VIP table announces opponent with single current chips format without refill."""
        self.engine.poker.table_mode = "std"
        ok, msg = self.engine.switch_poker_table("vip")
        self.assertTrue(ok)
        self.assertIn("Chips:", msg)
        self.assertIn("tokens", msg)
        self.assertNotIn(" / ", msg)

    def test_daily_calendar_rollover_reset(self):
        """Advancing date resets all bankrolls and resets clean sweep flag."""
        # Deplete some patrons
        for name in VIP_PATRON_DAILY_BANKROLLS.keys():
            self.engine.state["vip_bankrolls"][name]["current"] = 0
        self.engine.state["vip_clean_sweep_claimed"] = True
        self.engine.save()

        # Simulate date rollover to next day via check_and_reset_vip_bankrolls
        reset_ok = self.engine.check_and_reset_vip_bankrolls("2026-10-13")
        self.assertTrue(reset_ok)
        self.assertEqual(self.engine.state["vip_bankrolls_date"], "2026-10-13")
        self.assertFalse(self.engine.state["vip_clean_sweep_claimed"])

        # Check all patrons are restored to full
        for name, max_val in VIP_PATRON_DAILY_BANKROLLS.items():
            self.assertEqual(self.engine.state["vip_bankrolls"][name]["current"], max_val)

        # Backward compatibility: verify check_and_refill_vip_bankrolls alias exists and points to same method
        self.assertEqual(self.engine.check_and_refill_vip_bankrolls, self.engine.check_and_reset_vip_bankrolls)


if __name__ == "__main__":
    unittest.main()
