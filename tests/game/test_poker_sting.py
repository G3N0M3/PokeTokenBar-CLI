import io
import re
import sys
import unittest
from unittest.mock import patch, MagicMock

from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.minigames.poker import Card, TexasHoldemEngine
from poketokenbar.game.storage import StorageManager
from poketokenbar.game.models import (
    POKER_VIP_TRIGGER_BET,
    POKER_VIP_MIN_BET,
    VELVET_STING_CHAPTERS,
    VELVET_PATRONS,
    VELVET_MARKS,
)
from poketokenbar.tui.app import PokeTokenBarTUI
from poketokenbar.tui_tabs.game_corner import (
    render_poker_tab,
    render_poker_vip_dialogue,
    render_velvet_sting_briefing,
)

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[mK]')


class TestPokerSting(unittest.TestCase):
    def setUp(self):
        StorageManager.save_state(StorageManager.default_state())
        self.engine = CompanionEngine()
        # Give ample tokens for testing high-roller bets
        self.engine.state["used_since_install"] = 1_000_000_000_000_000  # 1,000 Trillion
        self.engine.state["spent_tokens"] = 0
        self.engine.save()

    def test_card_standard_rendering_no_gold(self):
        c = Card("A", "♠")
        std_str = ANSI_REGEX.sub("", c.render(gold=False))
        gold_str = ANSI_REGEX.sub("", c.render(gold=True))
        self.assertIn("A♠", std_str)
        self.assertNotIn("24K", gold_str)
        self.assertIn("A♠", gold_str)

    def test_table_mode_switching(self):
        # Cannot enter VIP before unlock
        ok, msg = self.engine.switch_poker_table("vip")
        self.assertFalse(ok)
        self.assertIn("invitation", msg)

        # Unlock VIP
        self.engine.state["poker_vip_unlocked"] = True
        self.engine.save()

        # Now can enter VIP
        ok, msg = self.engine.switch_poker_table("vip")
        self.assertTrue(ok)
        self.assertEqual(self.engine.poker.table_mode, "vip")

        # Return to standard
        ok, msg = self.engine.switch_poker_table("std")
        self.assertTrue(ok)
        self.assertEqual(self.engine.poker.table_mode, "standard")

        # 'table boss' command is removed
        ok, msg = self.engine.switch_poker_table("boss")
        self.assertFalse(ok)
        self.assertIn("removed", msg)

        # In Chapter 3 (Viktor Rostov), entering VIP table automatically seats Viktor Rostov
        self.engine.state["velvet_sting"]["recruited"] = True
        self.engine.state["velvet_sting"]["chapter"] = "3"
        ok, msg = self.engine.switch_poker_table("vip")
        self.assertTrue(ok)
        self.assertEqual(self.engine.poker.table_mode, "vip")
        self.assertIn("Viktor Rostov", self.engine.poker.active_opponent)

    def test_vip_minimum_bet(self):
        self.engine.state["poker_vip_unlocked"] = True
        self.engine.switch_poker_table("vip")

        # Rejects bet below 10T
        ok, msg = self.engine.play_poker_bet("5t")
        self.assertFalse(ok)
        self.assertIn("Minimum bet", msg)

        # Accepts bet >= 10T
        ok, msg = self.engine.play_poker_bet("10t")
        self.assertTrue(ok)
        self.assertEqual(self.engine.poker.current_bet, 10_000_000_000_000)

    def test_vip_multipliers(self):
        self.engine.poker.table_mode = "vip"
        self.assertEqual(self.engine.poker._get_win_multiplier("Royal Flush"), 100)
        self.assertEqual(self.engine.poker._get_win_multiplier("Straight Flush"), 25)
        self.assertEqual(self.engine.poker._get_win_multiplier("Four of a Kind"), 12)
        self.assertEqual(self.engine.poker._get_win_multiplier("Full House"), 6)
        self.assertEqual(self.engine.poker._get_win_multiplier("Flush"), 5)
        self.assertEqual(self.engine.poker._get_win_multiplier("Straight"), 4)

    def test_sovereign_bad_beat_rebate(self):
        self.engine.state["poker_vip_unlocked"] = True
        self.engine.state["luxury"]["unlocked"] = True
        self.engine.switch_poker_table("vip")

        # Test fold rebate
        self.engine.play_poker_bet("10t")
        initial_spent = self.engine.state["spent_tokens"]
        ok, msg = self.engine.play_poker_action("fold")
        self.assertTrue(ok)
        self.assertIn("Sovereign Rebate", msg)
        # 10% of 10T = 1T refunded (spent_tokens reduced by 1T)
        self.assertEqual(self.engine.state["spent_tokens"], initial_spent - 1_000_000_000_000)

    def test_velvet_sting_10_chapter_progression(self):
        self.engine.state["poker_vip_unlocked"] = True
        sting = self.engine.state["velvet_sting"]

        # Chapter 1: Requires 10 syndicate wins AND 500T total VIP winnings to get recruited
        self.assertEqual(sting["chapter"], "1")
        self.assertFalse(sting.get("recruited", False))
        ready, _ = self.engine.check_velvet_sting_objective()
        self.assertFalse(ready)
        sting["syndicate_wins"] = 10
        ready, _ = self.engine.check_velvet_sting_objective()
        self.assertFalse(ready)  # Still needs 500T winnings
        sting["vip_winnings"] = 500_000_000_000_000
        ready, _ = self.engine.check_velvet_sting_objective()
        self.assertTrue(ready)
        sting["recruited"] = True
        ok, msg = self.engine.advance_velvet_sting()
        self.assertTrue(ok)
        self.assertEqual(sting["chapter"], "2")
        self.assertEqual(self.engine.poker.active_opponent, "Financier Vance [Money Runner]")

        # Chapter 2: Requires 25T pot against Vance
        self.assertEqual(sting.get("chapter_pot", 0), 0)
        ready, _ = self.engine.check_velvet_sting_objective()
        self.assertFalse(ready)
        sting["chapter_pot"] = 25_000_000_000_000
        ready, _ = self.engine.check_velvet_sting_objective()
        self.assertTrue(ready)
        ok, _ = self.engine.advance_velvet_sting()
        self.assertTrue(ok)
        self.assertEqual(sting["chapter"], "3")
        self.assertEqual(sting["boss_stack"], 50_000_000_000_000)

        # Chapter 3: Deplete Viktor Rostov stack at VIP table (no table boss needed)
        self.engine.switch_poker_table("vip")
        self.assertEqual(self.engine.poker.active_opponent, "Viktor Rostov [Enforcer]")
        ready, _ = self.engine.check_velvet_sting_objective()
        self.assertFalse(ready)
        sting["boss_stack"] = 0
        ready, _ = self.engine.check_velvet_sting_objective()
        self.assertTrue(ready)
        self.engine.advance_velvet_sting()
        self.assertEqual(sting["chapter"], "4")
        self.assertEqual(self.engine.poker.active_opponent, "Countess Beverly [Bondholder]")

        # Chapter 4: Requires 50T chapter VIP winnings against Countess Beverly
        self.assertEqual(sting.get("chapter_winnings", 0), 0)
        sting["chapter_winnings"] = 40_000_000_000_000
        ready, _ = self.engine.check_velvet_sting_objective()
        self.assertFalse(ready)
        sting["chapter_winnings"] = 50_000_000_000_000
        ready, _ = self.engine.check_velvet_sting_objective()
        self.assertTrue(ready)
        self.engine.advance_velvet_sting()
        self.assertEqual(sting["chapter"], "5")
        self.assertEqual(self.engine.poker.active_opponent, "Lord Sterling [Syndicator]")

        # Chapter 5: Requires 3 ranked wins (Two Pair+) against Lord Sterling
        self.assertEqual(sting.get("ranked_wins", 0), 0)
        ready, _ = self.engine.check_velvet_sting_objective()
        self.assertFalse(ready)
        sting["ranked_wins"] = 3
        ready, _ = self.engine.check_velvet_sting_objective()
        self.assertTrue(ready)
        self.engine.advance_velvet_sting()
        self.assertEqual(sting["chapter"], "6")
        self.assertEqual(self.engine.poker.active_opponent, "Oligarch Thorne [Consortium Partner]")

        # Chapter 6: Whale pot of 100T against Oligarch Thorne
        self.assertEqual(sting.get("chapter_pot", 0), 0)
        ready, _ = self.engine.check_velvet_sting_objective()
        self.assertFalse(ready)
        sting["chapter_pot"] = 100_000_000_000_000
        ready, _ = self.engine.check_velvet_sting_objective()
        self.assertTrue(ready)
        self.engine.advance_velvet_sting()
        self.assertEqual(sting["chapter"], "7")
        self.assertEqual(sting["boss_stack"], 100_000_000_000_000)
        self.assertEqual(self.engine.poker.active_opponent, "Corinne Vane [Chief Auditor]")

        # Chapter 7: Corinne Vane stack (100T)
        sting["boss_stack"] = 0
        self.engine.advance_velvet_sting()
        self.assertEqual(sting["chapter"], "8")
        self.assertEqual(sting["boss_stack"], 150_000_000_000_000)

        # Chapter 8: Baron Croix Round 1 (150T)
        sting["boss_stack"] = 0
        self.engine.advance_velvet_sting()
        self.assertEqual(sting["chapter"], "9")
        self.assertEqual(sting["boss_stack"], 250_000_000_000_000)

        # Chapter 9: Baron Croix Round 2 (250T)
        sting["boss_stack"] = 0
        self.engine.advance_velvet_sting()
        self.assertEqual(sting["chapter"], "10")
        self.assertEqual(sting["boss_stack"], 350_000_000_000_000)

        # Chapter 10: Climax Baron Croix Round 3 (350T)
        spent_before = self.engine.state["spent_tokens"]
        sting["boss_stack"] = 0
        ok, msg = self.engine.advance_velvet_sting()
        self.assertTrue(ok)
        self.assertEqual(sting["chapter"], "epilogue")
        self.assertTrue(sting["cleared"])

        # Check Epilogue rewards
        # 1. 100T bounty credited
        self.assertEqual(self.engine.state["spent_tokens"], spent_before - 100_000_000_000_000)
        # 2. Title unlocked
        self.assertIn("♠️ Master of the Velvet Sting", self.engine.state["achievements"])
        # 3. Baron's 24K watch in luxury decor
        self.assertIn("watch", self.engine.state["luxury"]["decor"])

    def test_layout_72_columns(self):
        app = MagicMock()
        app.engine = self.engine

        modes_to_test = [
            ("standard", False, ""),
            ("vip", True, ""),
            ("vip", True, "Baron Salvatore Croix [Tycoon]"),
        ]

        for mode, is_vip, boss_name in modes_to_test:
            self.engine.poker.table_mode = mode
            self.engine.poker.boss_name = boss_name
            self.engine.poker.active_opponent = boss_name or "Duchess Eleanor"
            self.engine.poker.boss_stack = 200_000_000_000_000 if boss_name else 0
            self.engine.poker.boss_max_stack = 350_000_000_000_000 if boss_name else 0
            self.engine.state["poker_vip_unlocked"] = is_vip
            self.engine.state["velvet_sting"]["recruited"] = True if boss_name else False

            # Deal a hand to render cards and board
            self.engine.poker.player_hole = [Card("A", "♠"), Card("K", "♠")]
            self.engine.poker.community_cards = [
                Card("Q", "♠"), Card("J", "♠"), Card("10", "♠"), Card("2", "♦"), Card("3", "♣")
            ]
            self.engine.poker.community_revealed = 5
            self.engine.poker.current_bet = 10_000_000_000_000
            self.engine.poker.game_state = "turn"

            captured = io.StringIO()
            with patch("sys.stdout", captured):
                render_poker_tab(app)

            lines = captured.getvalue().split("\n")
            for i, line in enumerate(lines):
                clean = ANSI_REGEX.sub("", line)
                self.assertLessEqual(
                    len(clean), 72,
                    f"Line {i} exceeded 72 cols in mode '{mode}' boss '{boss_name}': [{len(clean)}] '{clean}'"
                )

    def test_vip_dialogue_layout_and_no_cutoff(self):
        app = MagicMock()
        app.engine = self.engine

        captured = io.StringIO()
        with patch("sys.stdout", captured), patch("poketokenbar.tui_tabs.game_corner._read_input_safe", return_value="2"):
            render_poker_vip_dialogue(app)

        output = captured.getvalue()
        # Verify no truncation of phrases
        self.assertIn("tokens on this felt?!\"", output)
        self.assertIn("exceeds our", output)
        self.assertIn("standard table limits!", output)
        self.assertIn("I can introduce you", output)
        self.assertIn("The Velvet Salon", output)

        # Verify all lines <= 72 characters
        lines = output.split("\n")
        for i, line in enumerate(lines):
            clean = ANSI_REGEX.sub("", line)
            self.assertLessEqual(
                len(clean), 72,
                f"Line {i} exceeded 72 cols in VIP dialogue: [{len(clean)}] '{clean}'"
            )

    def test_recruitment_dialogue_layout_and_no_cutoff(self):
        from poketokenbar.tui_tabs.game_corner import render_velvet_recruitment_dialogue

        app = MagicMock()
        app.engine = self.engine

        captured = io.StringIO()
        with patch("sys.stdout", captured), patch("poketokenbar.tui_tabs.game_corner._read_input_safe", return_value=""):
            render_velvet_recruitment_dialogue(app)

        output = captured.getvalue()
        clean_text = " ".join(ANSI_REGEX.sub("", output).split())
        self.assertIn("RECRUITMENT INVITATION", clean_text)
        self.assertIn("Remarkable card play, Trainer", clean_text)
        self.assertIn("The Velvet Sting", clean_text)

        lines = output.split("\n")
        for i, line in enumerate(lines):
            clean = ANSI_REGEX.sub("", line)
            self.assertLessEqual(
                len(clean), 72,
                f"Line {i} exceeded 72 cols in recruitment dialogue: [{len(clean)}] '{clean}'"
            )

    def test_recruitment_flow_and_sting_locking(self):
        from poketokenbar.tui.router import CommandRouter

        app = MagicMock()
        app.engine = self.engine
        app.minigame_state = "poker"
        app.current_tab = 7

        # 1. Unlocked VIP room, but not recruited yet
        self.engine.state["poker_vip_unlocked"] = True
        self.engine.state["velvet_sting"]["recruited"] = False
        self.engine.state["velvet_sting"]["syndicate_wins"] = 3
        self.engine.state["velvet_sting"]["vip_winnings"] = 100_000_000_000_000
        self.engine.save()

        # Typing 'sting' when not recruited shows locked message
        CommandRouter.dispatch(app, "sting")
        self.assertIn("locked", app.message)
        self.assertIn("3/10 wins", app.message)

        # 2. Simulate crossing recruitment threshold on winning hand
        self.engine.state["velvet_sting"]["syndicate_wins"] = 9
        self.engine.state["velvet_sting"]["vip_winnings"] = 490_000_000_000_000
        self.engine.poker.table_mode = "vip"
        self.engine.poker.game_state = "turn"
        self.engine.poker.current_bet = 10_000_000_000_000
        # Mock a winning showdown
        with patch.object(self.engine.poker, "play_showdown", return_value=("WIN", "Two Pair", "One Pair", 2, 20_000_000_000_000)), \
             patch("poketokenbar.tui.router.render_velvet_recruitment_dialogue") as mock_modal:
            CommandRouter.dispatch(app, "check")
            self.assertTrue(self.engine.state["velvet_sting"]["recruited"])
            mock_modal.assert_called_once_with(app)

        # 3. Now recruited: typing 'sting' advances Chapter 1 to Chapter 2
        with patch("poketokenbar.tui.router.render_velvet_sting_briefing") as mock_briefing:
            CommandRouter.dispatch(app, "sting")
            self.assertEqual(self.engine.state["velvet_sting"]["chapter"], "2")
            mock_briefing.assert_called_once_with(app)

    def test_reset_velvet_sting_and_settings_routing(self):
        from poketokenbar.tui.router import CommandRouter

        app = MagicMock()
        app.engine = self.engine
        app.current_tab = 11

        # Progress campaign
        self.engine.state["poker_vip_unlocked"] = True
        self.engine.state["velvet_sting"]["chapter"] = "5"
        self.engine.state["velvet_sting"]["syndicate_wins"] = 10
        self.engine.poker.table_mode = "vip"
        self.engine.save()

        # Direct reset method
        ok, msg = self.engine.reset_velvet_sting()
        self.assertTrue(ok)
        self.assertFalse(self.engine.state["poker_vip_unlocked"])
        self.assertEqual(self.engine.state["velvet_sting"]["chapter"], "1")
        self.assertEqual(self.engine.poker.table_mode, "standard")

        # Unlock again for router test
        self.engine.state["poker_vip_unlocked"] = True
        self.engine.save()

        # Command router 'sting init' requires confirmation if unlocked and not --force
        CommandRouter.dispatch(app, "sting init")
        self.assertTrue(getattr(app, "pending_sting_init", False))
        self.assertIn("CONFIRM", app.message)

        # Confirm reset
        from poketokenbar.tui.modals.confirmations import handle_pending_confirmation
        handle_pending_confirmation(app, "CONFIRM")
        self.assertFalse(getattr(app, "pending_sting_init", False))
        self.assertFalse(self.engine.state["poker_vip_unlocked"])
        self.assertIn("reset", app.message)

        # Command router 'sting init --force'
        self.engine.state["poker_vip_unlocked"] = True
        self.engine.save()
        CommandRouter.dispatch(app, "sting init --force")
        self.assertFalse(self.engine.state["poker_vip_unlocked"])
        self.assertIn("reset", app.message)

    def test_salon_opponents_pre_and_post_recruitment(self):
        self.engine.state["poker_vip_unlocked"] = True

        # 1. Pre-recruitment (Chapter 1 Trial)
        self.engine.state["velvet_sting"]["recruited"] = False
        self.engine.state["velvet_sting"]["chapter"] = "1"
        self.engine.switch_poker_table("vip")
        self.assertIn(self.engine.poker.active_opponent, VELVET_PATRONS)
        self.assertNotIn(self.engine.poker.active_opponent, VELVET_MARKS)

        # 2. Post-recruitment: Operation Paper Trail (Chapter 2)
        self.engine.state["velvet_sting"]["recruited"] = True
        self.engine.state["velvet_sting"]["chapter"] = "2"
        self.engine.switch_poker_table("vip")
        # Should face Financier Vance, NOT Vivienne, Walter, or Eleanor
        self.assertEqual(self.engine.poker.active_opponent, "Financier Vance [Money Runner]")
        self.assertNotIn(self.engine.poker.active_opponent, VELVET_PATRONS)

        # 3. Post-recruitment: Operation Liquid Freeze (Chapter 4)
        self.engine.state["velvet_sting"]["chapter"] = "4"
        self.engine.switch_poker_table("vip")
        self.assertEqual(self.engine.poker.active_opponent, "Countess Beverly [Bondholder]")
        self.assertNotIn(self.engine.poker.active_opponent, VELVET_PATRONS)

        # 4. Post-recruitment: Operation Counter-Bluff (Chapter 5)
        self.engine.state["velvet_sting"]["chapter"] = "5"
        self.engine.switch_poker_table("vip")
        self.assertEqual(self.engine.poker.active_opponent, "Lord Sterling [Syndicator]")
        self.assertNotIn(self.engine.poker.active_opponent, VELVET_PATRONS)

        # 5. Post-recruitment: Operation Golden Lure (Chapter 6)
        self.engine.state["velvet_sting"]["chapter"] = "6"
        self.engine.switch_poker_table("vip")
        self.assertEqual(self.engine.poker.active_opponent, "Oligarch Thorne [Consortium Partner]")
        self.assertNotIn(self.engine.poker.active_opponent, VELVET_PATRONS)

    def test_post_campaign_opponent_rotation_and_no_tactical_message(self):
        self.engine.state["poker_vip_unlocked"] = True
        self.engine.state["velvet_sting"]["recruited"] = True
        self.engine.state["velvet_sting"]["cleared"] = True
        self.engine.state["velvet_sting"]["chapter"] = "epilogue"
        self.engine.save()

        # 1. Entering salon post-campaign seats from non-Croix pool
        ok, msg = self.engine.switch_poker_table("vip")
        self.assertTrue(ok)
        self.assertIn("Welcome back, Master of the Velvet Sting", msg)
        valid_pool = VELVET_PATRONS + VELVET_MARKS
        self.assertIn(self.engine.poker.active_opponent, valid_pool)
        self.assertNotIn("Croix", self.engine.poker.active_opponent)
        self.assertEqual(self.engine.poker.boss_name, "")
        self.assertEqual(self.engine.poker.boss_stack, 0)

        # 2. Opponents rotate across hands and Baron Croix never appears
        seen_opponents = set()
        for _ in range(15):
            ok, bet_msg = self.engine.play_poker_bet("10t")
            self.assertTrue(ok)
            opp = self.engine.poker.active_opponent
            self.assertIn(opp, valid_pool)
            self.assertNotIn("Croix", opp)
            seen_opponents.add(opp)

            # Fold hand and verify tactical objective message is NOT displayed
            ok_fold, fold_msg = self.engine.play_poker_action("fold")
            self.assertTrue(ok_fold)
            self.assertNotIn("Tactical objective achieved", fold_msg)
            self.assertNotIn("Type 'sting' to advance", fold_msg)

        # Verify rotation occurred (saw more than 1 distinct opponent)
        self.assertGreater(len(seen_opponents), 1)

        # 3. Winning showdown post-campaign does not display tactical objective message
        self.engine.play_poker_bet("10t")
        self.engine.poker.game_state = "turn"
        # Mock showdown as WIN
        with unittest.mock.patch.object(self.engine.poker, "play_showdown", return_value=("WIN", "Flush", "High Card", 5, 50_000_000_000_000)):
            ok_sd, sd_msg = self.engine.play_poker_action("check")
            self.assertTrue(ok_sd)
            self.assertNotIn("Tactical objective achieved", sd_msg)
            self.assertNotIn("Type 'sting' to advance", sd_msg)


if __name__ == "__main__":
    unittest.main()
