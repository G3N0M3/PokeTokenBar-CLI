import io
import re
import unittest
from unittest.mock import patch, MagicMock

from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.minigames.poker import Card, Deck, TexasHoldemEngine
from poketokenbar.game.storage import StorageManager
from poketokenbar.tui.app import PokeTokenBarTUI
from poketokenbar.tui_tabs.game_corner import render_poker_tab

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[mK]')


class TestPokerGame(unittest.TestCase):
    def setUp(self):
        StorageManager.save_state(StorageManager.default_state())
        self.engine = CompanionEngine()

    def test_deck_and_card(self):
        deck = Deck()
        self.assertEqual(len(deck.cards), 52)
        drawn = deck.draw(5)
        self.assertEqual(len(drawn), 5)
        self.assertEqual(len(deck.cards), 47)

        c = Card("A", "♠")
        self.assertEqual(c.value, 14)
        self.assertIn("A♠", ANSI_REGEX.sub("", str(c)))

    def test_evaluate_5_cards(self):
        # Royal Flush
        rf = [Card("10", "♠"), Card("J", "♠"), Card("Q", "♠"), Card("K", "♠"), Card("A", "♠")]
        name, score = TexasHoldemEngine.evaluate_5_cards(rf)
        self.assertEqual(name, "Royal Flush")

        # Straight Flush (Wheel: A-2-3-4-5)
        sf_wheel = [Card("A", "♥"), Card("2", "♥"), Card("3", "♥"), Card("4", "♥"), Card("5", "♥")]
        name_sf, _ = TexasHoldemEngine.evaluate_5_cards(sf_wheel)
        self.assertEqual(name_sf, "Straight Flush")

        # Four of a Kind
        foak = [Card("9", "♠"), Card("9", "♥"), Card("9", "♦"), Card("9", "♣"), Card("K", "♠")]
        name_fk, _ = TexasHoldemEngine.evaluate_5_cards(foak)
        self.assertEqual(name_fk, "Four of a Kind")

        # Full House
        fh = [Card("J", "♠"), Card("J", "♥"), Card("J", "♦"), Card("4", "♣"), Card("4", "♠")]
        name_fh, _ = TexasHoldemEngine.evaluate_5_cards(fh)
        self.assertEqual(name_fh, "Full House")

        # Flush
        fl = [Card("2", "♦"), Card("5", "♦"), Card("8", "♦"), Card("J", "♦"), Card("A", "♦")]
        name_fl, _ = TexasHoldemEngine.evaluate_5_cards(fl)
        self.assertEqual(name_fl, "Flush")

        # Straight (Regular)
        st = [Card("5", "♠"), Card("6", "♥"), Card("7", "♦"), Card("8", "♣"), Card("9", "♠")]
        name_st, _ = TexasHoldemEngine.evaluate_5_cards(st)
        self.assertEqual(name_st, "Straight")

        # Straight (Wheel A-2-3-4-5)
        st_wheel = [Card("A", "♠"), Card("2", "♥"), Card("3", "♦"), Card("4", "♣"), Card("5", "♠")]
        name_stw, _ = TexasHoldemEngine.evaluate_5_cards(st_wheel)
        self.assertEqual(name_stw, "Straight")

        # Three of a Kind
        toak = [Card("8", "♠"), Card("8", "♥"), Card("8", "♦"), Card("K", "♣"), Card("2", "♠")]
        name_toak, _ = TexasHoldemEngine.evaluate_5_cards(toak)
        self.assertEqual(name_toak, "Three of a Kind")

        # Two Pair
        tp = [Card("Q", "♠"), Card("Q", "♥"), Card("7", "♦"), Card("7", "♣"), Card("A", "♠")]
        name_tp, _ = TexasHoldemEngine.evaluate_5_cards(tp)
        self.assertEqual(name_tp, "Two Pair")

        # One Pair
        op = [Card("10", "♠"), Card("10", "♥"), Card("3", "♦"), Card("6", "♣"), Card("K", "♠")]
        name_op, _ = TexasHoldemEngine.evaluate_5_cards(op)
        self.assertEqual(name_op, "One Pair")

        # High Card
        hc = [Card("2", "♠"), Card("4", "♥"), Card("7", "♦"), Card("10", "♣"), Card("A", "♠")]
        name_hc, _ = TexasHoldemEngine.evaluate_5_cards(hc)
        self.assertEqual(name_hc, "High Card")

    def test_get_hand_type(self):
        poker = TexasHoldemEngine()

        # Preflop: Pocket pair
        poker.player_hole = [Card("8", "♠"), Card("8", "♥")]
        poker.game_state = "preflop"
        poker.community_revealed = 0
        self.assertEqual(poker.get_hand_type(poker.player_hole), "One Pair")

        # Preflop: High card
        poker.player_hole = [Card("A", "♠"), Card("K", "♥")]
        self.assertEqual(poker.get_hand_type(poker.player_hole), "High Card")

        # Flop: 3 community cards (A♠ K♥ + A♦ 2♣ 7♠ -> One Pair)
        poker.game_state = "flop"
        poker.community_revealed = 3
        poker.community_cards = [Card("A", "♦"), Card("2", "♣"), Card("7", "♠"), Card("3", "♦"), Card("2", "♠")]
        self.assertEqual(poker.get_hand_type(poker.player_hole), "One Pair")

        # Turn: 4 community cards (A♠ K♥ + A♦ 2♣ 7♠ K♣ -> Two Pair)
        poker.game_state = "turn"
        poker.community_revealed = 4
        poker.community_cards[3] = Card("K", "♣")
        self.assertEqual(poker.get_hand_type(poker.player_hole), "Two Pair")

        # Showdown: 5 community cards (A♠ K♥ + A♦ 2♣ 7♠ K♣ A♣ -> Full House)
        poker.game_state = "idle"
        poker.community_revealed = 5
        poker.community_cards[4] = Card("A", "♣")
        self.assertEqual(poker.get_hand_type(poker.player_hole), "Full House")

        # Dealer hand alias property
        poker.dealer_hand = [Card("Q", "♠"), Card("Q", "♦")]
        self.assertEqual(poker.dealer_hole, poker.dealer_hand)
        self.assertEqual(poker.player_hole, poker.player_hand)

    def test_poker_engine_flow(self):
        poker = TexasHoldemEngine()
        self.assertEqual(poker.game_state, "idle")

        # Cannot advance before starting
        self.assertFalse(poker.play_flop()[0])
        self.assertFalse(poker.play_turn()[0])

        # Start hand
        ok, msg = poker.start_hand(100_000)
        self.assertTrue(ok)
        self.assertEqual(poker.game_state, "preflop")
        self.assertEqual(len(poker.player_hole), 2)
        self.assertEqual(len(poker.dealer_hole), 2)
        self.assertEqual(len(poker.community_cards), 5)

        # Cannot start another hand while in progress
        ok_dup, msg_dup = poker.start_hand(50_000)
        self.assertFalse(ok_dup)
        self.assertIn("already in progress", msg_dup)

        # Flop
        ok_f, msg_f = poker.play_flop()
        self.assertTrue(ok_f)
        self.assertEqual(poker.game_state, "flop")

        # Turn
        ok_t, msg_t = poker.play_turn()
        self.assertTrue(ok_t)
        self.assertEqual(poker.game_state, "turn")

        # Showdown
        outcome, p_rank, d_rank, mult, winnings = poker.play_showdown()
        self.assertIn(outcome, ["WIN", "LOSS", "PUSH"])
        self.assertEqual(poker.game_state, "idle")
        self.assertEqual(poker.last_outcome, outcome)

    def test_poker_fold(self):
        poker = TexasHoldemEngine()
        poker.start_hand(200_000)
        outcome, lost = poker.play_fold()
        self.assertEqual(outcome, "FOLD")
        self.assertEqual(lost, 200_000)
        self.assertEqual(poker.game_state, "idle")
        self.assertEqual(poker.last_outcome, "FOLD")

    def test_companion_casino_poker(self):
        self.engine.state["spent_tokens"] = 0
        self.engine.state["used_since_install"] = 10_000_000

        # Start bet
        ok, msg = self.engine.play_poker_bet("1m")
        self.assertTrue(ok)
        self.assertEqual(self.engine.poker.game_state, "preflop")
        self.assertEqual(self.engine.poker.current_bet, 1_000_000)

        # Check -> Flop
        ok_f, msg_f = self.engine.play_poker_action("check")
        self.assertTrue(ok_f)
        self.assertEqual(self.engine.poker.game_state, "flop")

        # Raise -> Turn (doubles bet)
        ok_r, msg_r = self.engine.play_poker_action("raise")
        self.assertTrue(ok_r)
        self.assertEqual(self.engine.poker.game_state, "turn")
        self.assertEqual(self.engine.poker.current_bet, 2_000_000)

        # Check -> Showdown
        ok_s, msg_s = self.engine.play_poker_action("check")
        self.assertTrue(ok_s)
        self.assertEqual(self.engine.poker.game_state, "idle")
        self.assertTrue(hasattr(self.engine.poker, "last_outcome"))

    def test_poker_layout_72_column_compliance(self):
        app = PokeTokenBarTUI()
        app.engine = self.engine
        self.engine.state["used_since_install"] = 10_000_000

        # 1. Idle state
        trap = io.StringIO()
        with patch("sys.stdout", trap):
            render_poker_tab(app)
        idle_out = trap.getvalue()
        self.assertNotIn("Hole", idle_out)
        for line in idle_out.splitlines():
            clean = ANSI_REGEX.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Line exceeds 72 cols: {clean}")

        # 2. Preflop state
        self.engine.play_poker_bet("500k")
        trap2 = io.StringIO()
        with patch("sys.stdout", trap2):
            render_poker_tab(app)
        preflop_out = trap2.getvalue()
        self.assertIn("Your Hand:", preflop_out)
        self.assertIn("House Hand:", preflop_out)
        self.assertNotIn("Your Hole", preflop_out)
        self.assertNotIn("House Hole", preflop_out)
        for line in preflop_out.splitlines():
            clean = ANSI_REGEX.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Line exceeds 72 cols: {clean}")

        # 3. Flop state
        self.engine.play_poker_action("check")
        trap3 = io.StringIO()
        with patch("sys.stdout", trap3):
            render_poker_tab(app)
        flop_out = trap3.getvalue()
        self.assertIn("Your Hand:", flop_out)
        self.assertIn("House Hand:", flop_out)
        self.assertNotIn("Your Hole", flop_out)
        self.assertNotIn("House Hole", flop_out)
        for line in flop_out.splitlines():
            clean = ANSI_REGEX.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Line exceeds 72 cols: {clean}")

        # 4. Turn state
        self.engine.play_poker_action("check")
        trap4 = io.StringIO()
        with patch("sys.stdout", trap4):
            render_poker_tab(app)
        turn_out = trap4.getvalue()
        self.assertIn("Your Hand:", turn_out)
        self.assertIn("House Hand:", turn_out)
        self.assertNotIn("Your Hole", turn_out)
        self.assertNotIn("House Hole", turn_out)
        for line in turn_out.splitlines():
            clean = ANSI_REGEX.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Line exceeds 72 cols: {clean}")

        # 5. Showdown completed state
        self.engine.play_poker_action("check")
        trap5 = io.StringIO()
        with patch("sys.stdout", trap5):
            render_poker_tab(app)
        showdown_out = trap5.getvalue()
        self.assertIn("Your Hand:", showdown_out)
        self.assertIn("House Hand:", showdown_out)
        self.assertNotIn("Your Hole", showdown_out)
        self.assertNotIn("House Hole", showdown_out)
        for line in showdown_out.splitlines():
            clean = ANSI_REGEX.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Line exceeds 72 cols: {clean}")

        # 6. Fold state
        self.engine.play_poker_bet("100k")
        self.engine.play_poker_action("fold")
        trap6 = io.StringIO()
        with patch("sys.stdout", trap6):
            render_poker_tab(app)
        fold_out = trap6.getvalue()
        self.assertIn("Your Hand:", fold_out)
        self.assertIn("House Hand:", fold_out)
        self.assertNotIn("Your Hole", fold_out)
        self.assertNotIn("House Hole", fold_out)
        for line in fold_out.splitlines():
            clean = ANSI_REGEX.sub("", line)
            self.assertLessEqual(len(clean), 72, f"Line exceeds 72 cols: {clean}")


if __name__ == "__main__":
    unittest.main()
