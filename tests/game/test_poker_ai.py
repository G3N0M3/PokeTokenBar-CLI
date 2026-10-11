import io
import os
import re
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.minigames.poker import Card, TexasHoldemEngine
from poketokenbar.game.companion.casino import _format_poker_quote_block
from poketokenbar.game.minigames.poker_ai import (
    OPPONENT_PROFILES,
    OpponentProfile,
    get_opponent_profile,
    evaluate_opponent_street_action,
    evaluate_opponent_reaction_to_raise,
    evaluate_opponent_end_quote,
)
from poketokenbar.game.storage import StorageManager
from poketokenbar.tui_tabs.game_corner import render_poker_tab

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[mK]')


class TestPokerAIProfiles(unittest.TestCase):
    def test_all_named_profiles_exist(self):
        expected_opponents = [
            "Duchess Eleanor",
            "Gentleman Walter",
            "Madame Vivienne",
            "Financier Vance",
            "Viktor Rostov",
            "Countess Beverly",
            "Lord Sterling",
            "Oligarch Thorne",
            "Corinne Vane",
            "Baron Salvatore Croix",
        ]
        for name in expected_opponents:
            prof = get_opponent_profile(name)
            self.assertEqual(prof.name, name)
            self.assertGreater(prof.aggression, 0.0)
            self.assertGreater(prof.fold_resistance, 0.0)
            self.assertIn("check", prof.quotes)
            self.assertIn("bet", prof.quotes)
            self.assertIn("call", prof.quotes)
            self.assertIn("fold", prof.quotes)
            self.assertIn("raise", prof.quotes)

    def test_title_bracket_stripping(self):
        prof = get_opponent_profile("Viktor Rostov [Enforcer]")
        self.assertEqual(prof.name, "Viktor Rostov")
        self.assertEqual(prof.title, "Enforcer")

    def test_croix_chapter_tilt_profiles(self):
        base_prof = get_opponent_profile("Baron Salvatore Croix", chapter="8")
        self.assertEqual(base_prof.title, "Tycoon")
        self.assertEqual(base_prof.aggression, 0.80)

        ch9_prof = get_opponent_profile("Baron Salvatore Croix", chapter="9")
        self.assertEqual(ch9_prof.title, "Cornered Vulture")
        self.assertEqual(ch9_prof.aggression, 0.90)
        self.assertEqual(ch9_prof.bet_ratio, 1.25)

        ch10_prof = get_opponent_profile("Baron Salvatore Croix", chapter="10")
        self.assertEqual(ch10_prof.title, "Total Insolvency")
        self.assertEqual(ch10_prof.aggression, 0.95)
        self.assertEqual(ch10_prof.bet_ratio, 1.5)

    def test_fallback_profile(self):
        prof = get_opponent_profile("Mysterious Stranger")
        self.assertEqual(prof.name, "Mysterious Stranger")
        self.assertEqual(prof.title, "High-Roller")
        self.assertEqual(prof.aggression, 0.45)


class TestPokerStreetAction(unittest.TestCase):
    def setUp(self):
        self.prof = get_opponent_profile("Madame Vivienne")

    def test_monster_hand_aggressive_bet(self):
        with patch("random.random", return_value=0.1):
            action, amt, quote = evaluate_opponent_street_action(
                profile=self.prof,
                dealer_rank_name="Flush",
                dealer_score=5000000,
                current_bet=10_000_000_000_000,
                available_tokens=100_000_000_000_000,
            )
            self.assertEqual(action, "bet")
            self.assertGreater(amt, 0)
            self.assertIn("T", quote)

    def test_weak_hand_checks_when_roll_high(self):
        with patch("random.random", return_value=0.99):
            action, amt, quote = evaluate_opponent_street_action(
                profile=self.prof,
                dealer_rank_name="High Card",
                dealer_score=100,
                current_bet=10_000_000_000_000,
                available_tokens=100_000_000_000_000,
            )
            self.assertEqual(action, "check")
            self.assertEqual(amt, 0)
            self.assertIn("Check", quote)

    def test_weak_hand_bluffs_when_roll_low(self):
        with patch("random.random", return_value=0.01):
            action, amt, quote = evaluate_opponent_street_action(
                profile=self.prof,
                dealer_rank_name="High Card",
                dealer_score=100,
                current_bet=10_000_000_000_000,
                available_tokens=100_000_000_000_000,
            )
            self.assertEqual(action, "bet")
            self.assertGreater(amt, 0)


class TestPokerReactionToRaise(unittest.TestCase):
    def setUp(self):
        self.prof = get_opponent_profile("Financier Vance")  # low fold_resistance (0.20)

    def test_air_folds_to_raise(self):
        with patch("random.random", return_value=0.5):
            action, re_raise, quote = evaluate_opponent_reaction_to_raise(
                profile=self.prof,
                dealer_rank_name="High Card",
                dealer_score=50,
                current_bet=20_000_000_000_000,
                raise_amount=10_000_000_000_000,
                is_allin=False,
            )
            self.assertEqual(action, "fold")
            self.assertEqual(re_raise, 0)

    def test_monster_hand_calls_or_3bets(self):
        with patch("random.random", return_value=0.01):
            action, re_raise, quote = evaluate_opponent_reaction_to_raise(
                profile=self.prof,
                dealer_rank_name="Full House",
                dealer_score=6000000,
                current_bet=20_000_000_000_000,
                raise_amount=10_000_000_000_000,
                is_allin=False,
            )
            self.assertIn(action, ["call", "raise"])


class TestCompanionCasinoPokerActions(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_state_file = os.path.join(self.tmp_dir.name, "state.json")
        os.environ["PTB_STATE_FILE"] = self.tmp_state_file
        StorageManager.save_state(StorageManager.default_state())
        self.engine = CompanionEngine()
        self.engine.state["used_since_install"] = 1_000_000_000_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.state["poker_vip_unlocked"] = True
        self.engine.save()

    def tearDown(self):
        self.tmp_dir.cleanup()
        os.environ.pop("PTB_STATE_FILE", None)

    def test_standard_table_no_opponent_ai_bets(self):
        self.engine.poker.table_mode = "standard"
        self.engine.play_poker_bet("1m")
        # Advancing preflop to flop
        ok, msg = self.engine.play_poker_action("check")
        self.assertTrue(ok)
        self.assertEqual(self.engine.poker.opponent_pending_call, 0)
        self.assertEqual(self.engine.poker.game_state, "flop")

    def test_vip_check_rejected_when_facing_bet(self):
        self.engine.switch_poker_table("vip")
        self.engine.play_poker_bet("10t")
        self.engine.poker.opponent_pending_call = 10_000_000_000_000

        ok, msg = self.engine.play_poker_action("check")
        self.assertFalse(ok)
        self.assertIn("call", msg)

    def test_vip_call_advances_street(self):
        self.engine.switch_poker_table("vip")
        self.engine.play_poker_bet("10t")
        self.engine.poker.opponent_pending_call = 5_000_000_000_000
        initial_spent = self.engine.state["spent_tokens"]

        ok, msg = self.engine.play_poker_action("call")
        self.assertTrue(ok)
        self.assertEqual(self.engine.poker.game_state, "flop")
        self.assertEqual(self.engine.state["spent_tokens"], initial_spent + 5_000_000_000_000)
        self.assertEqual(self.engine.poker.current_bet, 15_000_000_000_000)

    def test_opponent_fold_awards_pot_and_credits_story(self):
        self.engine.state["velvet_sting"]["chapter"] = "2"
        self.engine.state["velvet_sting"]["recruited"] = True
        self.engine.switch_poker_table("vip")
        self.engine.play_poker_bet("20t")
        # Player is on flop
        self.engine.poker.game_state = "flop"

        # Force opponent to fold on player's raise
        with patch.object(self.engine.poker, "process_opponent_reaction", return_value=("fold", 0, "No way! I fold!")):
            ok, msg = self.engine.play_poker_action("raise")
            self.assertTrue(ok)
            self.assertIn("FOLDED", msg)
            self.assertIn("YOU WIN THE POT", msg)
            self.assertEqual(self.engine.poker.game_state, "idle")
            self.assertTrue(self.engine.poker.opponent_folded)
            # Pot was 20T base + 20T raise = 40T total bet, pot won = 80T
            self.assertGreaterEqual(self.engine.state["velvet_sting"]["chapter_pot"], 80_000_000_000_000)

    def test_player_fold_generates_opponent_end_quote(self):
        self.engine.switch_poker_table("vip")
        self.engine.play_poker_bet("10t")
        self.engine.poker.active_opponent = "Viktor Rostov"
        ok, msg = self.engine.play_poker_action("fold")
        self.assertTrue(ok)
        self.assertIn("YOU FOLDED", msg)
        self.assertNotIn("⚔️ Viktor Rostov:", msg)
        self.assertTrue(self.engine.poker.opponent_banner_quote)

    def test_showdown_generates_opponent_end_quote(self):
        self.engine.switch_poker_table("vip")
        self.engine.play_poker_bet("10t")
        self.engine.poker.active_opponent = "Duchess Eleanor"
        self.engine.poker.game_state = "turn"
        ok, msg = self.engine.play_poker_action("check")
        self.assertTrue(ok)
        self.assertNotIn("⚔️ Duchess Eleanor:", msg)
        self.assertTrue(self.engine.poker.opponent_banner_quote)


class TestPokerEndQuotes(unittest.TestCase):
    def test_all_opponents_have_end_quotes_for_all_situations(self):
        expected_opponents = [
            "Duchess Eleanor",
            "Gentleman Walter",
            "Madame Vivienne",
            "Financier Vance",
            "Viktor Rostov",
            "Countess Beverly",
            "Lord Sterling",
            "Oligarch Thorne",
            "Corinne Vane",
            "Baron Salvatore Croix",
        ]
        situations = ["showdown_win", "showdown_loss", "showdown_push", "player_fold", "bankrupt"]
        for name in expected_opponents:
            prof = get_opponent_profile(name)
            for sit in situations:
                quote = evaluate_opponent_end_quote(prof, sit)
                self.assertTrue(quote, f"Empty quote for {name} on {sit}")
                self.assertIsInstance(quote, str)

    def test_croix_chapter_tilt_end_quotes(self):
        for ch in ["8", "9", "10"]:
            prof = get_opponent_profile("Baron Salvatore Croix", chapter=ch)
            for sit in ["showdown_win", "showdown_loss", "showdown_push", "player_fold", "bankrupt"]:
                quote = evaluate_opponent_end_quote(prof, sit)
                self.assertTrue(quote, f"Empty quote for Croix ch{ch} on {sit}")

    def test_engine_process_opponent_end_quote(self):
        engine = TexasHoldemEngine()
        engine.table_mode = "vip"
        engine.active_opponent = "Madame Vivienne"

        quote = engine.process_opponent_end_quote("showdown_win")
        self.assertTrue(quote)
        self.assertEqual(engine.opponent_banner_quote, quote)

        # Standard table returns empty quote
        engine.table_mode = "standard"
        quote_std = engine.process_opponent_end_quote("showdown_win")
        self.assertEqual(quote_std, "")
        self.assertEqual(engine.opponent_banner_quote, "")

    def test_quote_block_formatting_and_width_compliance(self):
        opponents = [
            "Duchess Eleanor",
            "Gentleman Walter",
            "Madame Vivienne",
            "Financier Vance",
            "Viktor Rostov",
            "Countess Beverly",
            "Lord Sterling",
            "Oligarch Thorne",
            "Corinne Vane",
            "Baron Salvatore Croix",
            "Mysterious Stranger",
        ]
        situations = ["showdown_win", "showdown_loss", "showdown_push", "player_fold", "bankrupt"]
        for opp in opponents:
            prof = get_opponent_profile(opp)
            for sit in situations:
                quotes = prof.quotes.get(sit, [evaluate_opponent_end_quote(prof, sit)])
                for q in quotes:
                    block = _format_poker_quote_block(opp, q)
                    self.assertTrue(block.startswith("\n"))
                    for line in block.strip().split("\n"):
                        # render_footer prepends 2 spaces for indented lines
                        rendered_len = 2 + len(line)
                        self.assertLessEqual(
                            rendered_len, 72,
                            f"Quote line exceeded 72 cols for {opp} ({sit}): [{rendered_len}] '{line}'"
                        )


class TestPokerAILayoutCompliance(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_state_file = os.path.join(self.tmp_dir.name, "state.json")
        os.environ["PTB_STATE_FILE"] = self.tmp_state_file
        StorageManager.save_state(StorageManager.default_state())
        self.engine = CompanionEngine()
        self.engine.state["used_since_install"] = 1_000_000_000_000_000
        self.engine.state["poker_vip_unlocked"] = True
        self.engine.save()

    def tearDown(self):
        self.tmp_dir.cleanup()
        os.environ.pop("PTB_STATE_FILE", None)

    def test_render_poker_tab_72_column_with_active_opponent(self):
        app = MagicMock()
        app.engine = self.engine

        test_cases = [
            ("vip", "Financier Vance [Money Runner]", 0, "check", False),
            ("vip", "Oligarch Thorne [Consortium Partner]", 25_000_000_000_000, "The consortium buys this pot! Pay up or pack up! (+25.0T)", False),
            ("vip", "Viktor Rostov [Enforcer]", 0, "You think you're tough, kid?!", True),
            ("boss", "Baron Salvatore Croix [Tycoon]", 50_000_000_000_000, "I will strip your bankroll to atoms! RE-RAISE! (+50.0T)", False),
        ]

        for mode, opp, pending, quote, folded in test_cases:
            self.engine.poker.table_mode = mode
            self.engine.poker.active_opponent = opp
            self.engine.poker.opponent_pending_call = pending
            self.engine.poker.opponent_banner_quote = quote
            self.engine.poker.opponent_folded = folded
            if folded:
                self.engine.poker.game_state = "idle"
                self.engine.poker.last_outcome = "WIN"
            else:
                self.engine.poker.game_state = "flop"

            self.engine.poker.player_hole = [Card("A", "♠"), Card("K", "♠")]
            self.engine.poker.dealer_hole = [Card("Q", "♦"), Card("J", "♣")]
            self.engine.poker.community_cards = [
                Card("10", "♠"), Card("9", "♠"), Card("8", "♠"), Card("2", "♦"), Card("3", "♣")
            ]
            self.engine.poker.community_revealed = 3
            self.engine.poker.current_bet = 20_000_000_000_000

            captured = io.StringIO()
            with patch("sys.stdout", captured):
                render_poker_tab(app)

            lines = captured.getvalue().split("\n")
            for i, line in enumerate(lines):
                clean = ANSI_REGEX.sub("", line)
                self.assertLessEqual(
                    len(clean), 72,
                    f"Line {i} exceeded 72 cols with opp '{opp}': [{len(clean)}] '{clean}'"
                )


if __name__ == "__main__":
    unittest.main()
