import os
import tempfile
import unittest
from pathlib import Path

from poketokenbar.game.companion import CompanionEngine
from poketokenbar.game.storage import StorageManager
from poketokenbar.game.voltorb_flip import VoltorbFlipEngine
from poketokenbar.game.excavator import ExcavatorEngine
from poketokenbar.game.trivia import TriviaEngine
from poketokenbar.game.derby import DerbyEngine


class TestGameCornerMinigames(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._temp_dir = tempfile.TemporaryDirectory()
        cls._temp_state_file = Path(cls._temp_dir.name) / "test_minigame_state.json"
        cls._old_state_file = os.environ.get("PTB_STATE_FILE")
        os.environ["PTB_STATE_FILE"] = str(cls._temp_state_file)

    @classmethod
    def tearDownClass(cls):
        cls._temp_dir.cleanup()
        if cls._old_state_file is not None:
            os.environ["PTB_STATE_FILE"] = cls._old_state_file
        else:
            os.environ.pop("PTB_STATE_FILE", None)

    def setUp(self):
        StorageManager.save_state(StorageManager.default_state())
        self.engine = CompanionEngine()
        # Seed tokens for testing bets
        self.engine.state["used_since_install"] = 100_000_000
        self.engine.state["spent_tokens"] = 0
        self.engine.save()

    # -------------------------------------------------------------------------
    # 1. Voltorb Flip Tests
    # -------------------------------------------------------------------------
    def test_voltorb_engine_generation_and_clues(self):
        v = VoltorbFlipEngine()
        ok, msg = v.start_game(500_000, level=1)
        self.assertTrue(ok)
        self.assertEqual(len(v.board), 5)
        self.assertEqual(len(v.board[0]), 5)

        # Verify clues match card values
        for r in range(5):
            expected_pts = sum(v.board[r][c].value for c in range(5))
            expected_volts = sum(1 for c in range(5) if v.board[r][c].value == 0)
            self.assertEqual(v.row_points[r], expected_pts)
            self.assertEqual(v.row_voltorbs[r], expected_volts)

        for c in range(5):
            expected_pts = sum(v.board[r][c].value for r in range(5))
            expected_volts = sum(1 for r in range(5) if v.board[r][c].value == 0)
            self.assertEqual(v.col_points[c], expected_pts)
            self.assertEqual(v.col_voltorbs[c], expected_volts)

    def test_voltorb_memo_and_flip(self):
        v = VoltorbFlipEngine()
        v.start_game(200_000, level=1)

        # Test memo
        ok_m, msg_m = v.memo(1, 2, "v")
        self.assertTrue(ok_m)
        self.assertEqual(v.board[0][1].memo, "v")

        # Clear memo
        v.memo(1, 2, "")
        self.assertEqual(v.board[0][1].memo, "")

        # Flip card
        ok_f, msg_f = v.flip(1, 1)
        self.assertTrue(ok_f)
        self.assertTrue(v.board[0][0].revealed)

    def test_voltorb_explosion_reveals_board(self):
        v = VoltorbFlipEngine()
        v.start_game(100_000, level=1)

        # Force a voltorb at (1, 1)
        v.board[0][0].value = 0
        ok, msg = v.flip(1, 1)
        self.assertTrue(ok)
        self.assertEqual(v.game_state, "game_over")
        self.assertIn("KABOOM", msg)
        # All cards should be revealed after explosion
        for r in range(5):
            for c in range(5):
                self.assertTrue(v.board[r][c].revealed)

    def test_voltorb_cashout(self):
        v = VoltorbFlipEngine()
        v.start_game(100_000, level=1)
        # Force a 2 at (1, 1)
        v.board[0][0].value = 2
        v.flip(1, 1)
        self.assertEqual(v.current_multiplier, 2)

        ok_co, msg_co, winnings = v.cashout()
        self.assertTrue(ok_co)
        self.assertEqual(winnings, 200_000)
        self.assertEqual(v.game_state, "cashed_out")

    def test_voltorb_direct_level_selection_and_validation(self):
        v = VoltorbFlipEngine()
        # Direct valid level selection (e.g. level 5)
        ok, msg = v.start_game(100_000, level=5)
        self.assertTrue(ok)
        self.assertEqual(v.current_level, 5)
        v.game_state = "idle"

        # Invalid level selection rejected
        ok_high, msg_high = v.start_game(100_000, level=9)
        self.assertFalse(ok_high)
        self.assertIn("Invalid level '9'", msg_high)

        ok_low, msg_low = v.start_game(100_000, level=0)
        self.assertFalse(ok_low)
        self.assertIn("Invalid level '0'", msg_low)

    # -------------------------------------------------------------------------
    # 2. Excavator Tests
    # -------------------------------------------------------------------------
    def test_excavator_generation_and_pick(self):
        ex = ExcavatorEngine()
        ok, msg = ex.start_game(500_000)
        self.assertTrue(ok)
        self.assertEqual(len(ex.strata), 6)
        self.assertEqual(len(ex.strata[0]), 9)
        self.assertEqual(ex.integrity, 25)

        initial_depth = ex.strata[0][0]
        ok_p, msg_p, rewards = ex.pick(1, 1)
        self.assertTrue(ok_p)
        self.assertEqual(ex.integrity, 24)
        if not any((0, 0) in t.coords for t in ex.treasures if t.kind == "barrier"):
            self.assertEqual(ex.strata[0][0], max(0, initial_depth - 1))

    def test_excavator_hammer_and_collapse(self):
        ex = ExcavatorEngine()
        ex.start_game(500_000)

        # Hammer costs 3 integrity
        ok_h, msg_h, _ = ex.hammer(3, 3)
        self.assertTrue(ok_h)
        self.assertEqual(ex.integrity, 22)

        # Drain integrity to trigger collapse
        ex.integrity = 2
        ok_c, msg_c, rewards = ex.hammer(1, 1)
        self.assertTrue(ok_c)
        self.assertEqual(ex.game_state, "collapsed")
        self.assertIn("collapsed", msg_c)

    def test_excavator_fixed_default_cost(self):
        ex = ExcavatorEngine()
        ok, msg = ex.start_game()
        self.assertTrue(ok)
        self.assertEqual(ex.entry_cost, 500_000)

        # Custom cost argument is ignored and always uses 500_000
        ex.game_state = "idle"
        ok2, _ = ex.start_game(cost=1_000_000)
        self.assertTrue(ok2)
        self.assertEqual(ex.entry_cost, 500_000)

    # -------------------------------------------------------------------------
    # 3. Trivia Tests ("Who's That Pokémon?")
    # -------------------------------------------------------------------------
    def test_trivia_start_and_guess(self):
        tr = TriviaEngine()
        ok, msg = tr.start_game(500_000)
        self.assertTrue(ok)
        self.assertIsNotNone(tr.current_target)
        self.assertEqual(tr.current_multiplier, 5.0)
        self.assertEqual(tr.guesses_left, 3)

        # Test hints
        ok_h1, msg_h1 = tr.request_hint()
        self.assertTrue(ok_h1)
        self.assertEqual(tr.current_multiplier, 3.5)

        ok_h2, msg_h2 = tr.request_hint()
        self.assertTrue(ok_h2)
        self.assertEqual(tr.current_multiplier, 2.0)

        # Test wrong guess
        ok_wrong, msg_wrong, win0 = tr.guess("totally_not_a_pokemon")
        self.assertFalse(ok_wrong)
        self.assertEqual(tr.guesses_left, 2)

        # Test correct guess
        correct_name = tr.current_target["name"]
        ok_right, msg_right, winnings = tr.guess(correct_name)
        self.assertTrue(ok_right)
        self.assertEqual(tr.game_state, "won")
        self.assertEqual(tr.streak, 1)
        self.assertEqual(winnings, int(500_000 * 2.0))

    # -------------------------------------------------------------------------
    # 4. Derby Race Tests
    # -------------------------------------------------------------------------
    def test_derby_bet_and_simulation(self):
        db = DerbyEngine()
        self.assertEqual(len(db.racers), 4)

        ok_b, msg_b = db.place_bet(1, 500_000)
        self.assertTrue(ok_b)
        self.assertEqual(db.game_state, "bet_placed")
        self.assertIn("Type 'race' to drop the starting flag!", msg_b)
        self.assertNotIn("start", msg_b)

        frames = db.simulate_race()
        self.assertGreater(len(frames), 1)
        self.assertIsNotNone(db.winner)
        self.assertGreaterEqual(db.winner.position, db.TRACK_LENGTH)

        ok_r, msg_r, winnings = db.resolve_race()
        self.assertTrue(ok_r)
        self.assertEqual(db.game_state, "finished")
        if db.winner.lane == 1:
            self.assertEqual(winnings, int(500_000 * 2.0))
        else:
            self.assertEqual(winnings, 0)

    # -------------------------------------------------------------------------
    # 5. CompanionEngine Integration Tests
    # -------------------------------------------------------------------------
    def test_companion_casino_integration(self):
        avail_start = self.engine.available_tokens

        # Voltorb bet
        ok_v, _ = self.engine.play_voltorb_bet("200k")
        self.assertTrue(ok_v)
        self.assertEqual(self.engine.available_tokens, avail_start - 200_000)

        # Excavator start (fixed 500k cost)
        ok_ex, _ = self.engine.play_excavator_start()
        self.assertTrue(ok_ex)
        self.assertEqual(self.engine.available_tokens, avail_start - 700_000)

        # Trivia start
        ok_tr, _ = self.engine.play_trivia_start("100k")
        self.assertTrue(ok_tr)
        self.assertEqual(self.engine.available_tokens, avail_start - 800_000)

        # Derby bet
        ok_db, _ = self.engine.play_derby_bet("2", "400k")
        self.assertTrue(ok_db)
        self.assertEqual(self.engine.available_tokens, avail_start - 1_200_000)

    # -------------------------------------------------------------------------
    # 6. Grid TUI Alignment Verification Tests
    # -------------------------------------------------------------------------
    def test_grid_rendering_alignment(self):
        import io
        import sys
        import re
        from poketokenbar.tui_tabs.game_corner import render_voltorb_tab, render_excavator_tab

        # Mock app object
        class MockApp:
            def __init__(self, engine):
                self.engine = engine

        app = MockApp(self.engine)

        # 1. Voltorb Flip: all 25 cards revealed
        self.engine.voltorb.start_game(500_000, level=1)
        for r in range(5):
            for c in range(5):
                self.engine.voltorb.board[r][c].revealed = True
        self.engine.voltorb.game_state = "game_over"
        self.engine.voltorb.last_result = "KABOOM!"

        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            render_voltorb_tab(app)
        finally:
            sys.stdout = old_stdout

        output = buf.getvalue()
        # Find all 5 card row lines: "   <r> │...│"
        grid_rows = [line for line in output.splitlines() if re.match(r"^\s+[1-5]\s+│", line)]
        self.assertEqual(len(grid_rows), 5)
        # Strip ANSI codes and verify pipe positions
        clean_rows = [re.sub(r"\033\[[0-9;]*m", "", r) for r in grid_rows]
        pipe_positions = [r.rfind("│") for r in clean_rows]
        self.assertEqual(len(set(pipe_positions)), 1, f"Voltorb grid rows are misaligned: {pipe_positions}")

        # 2. Excavator: with uncovered treasures
        self.engine.excavator.start_game(500_000)
        # Force uncovered treasures and empty soil
        for t in self.engine.excavator.treasures:
            t.uncovered = True
            for r, c in t.coords:
                self.engine.excavator.strata[r][c] = 0

        buf2 = io.StringIO()
        try:
            sys.stdout = buf2
            render_excavator_tab(app)
        finally:
            sys.stdout = old_stdout

        output2 = buf2.getvalue()
        ex_rows = [line for line in output2.splitlines() if re.match(r"^\s+[1-6]\s+│", line)]
        self.assertEqual(len(ex_rows), 6)
        clean_ex = [re.sub(r"\033\[[0-9;]*m", "", r) for r in ex_rows]
        ex_pipe_positions = [r.rfind("│") for r in clean_ex]
        self.assertEqual(len(set(ex_pipe_positions)), 1, f"Excavator grid rows are misaligned: {ex_pipe_positions}")

    # -------------------------------------------------------------------------
    # 7. Single Canonical Command Policy Verification Tests
    # -------------------------------------------------------------------------
    def test_single_canonical_command_enforcement(self):
        # 1. Excavator error messages only suggest 'dig', never 'mine'
        ex = ExcavatorEngine()
        ok_p, msg_p, _ = ex.pick(1, 1)
        self.assertFalse(ok_p)
        self.assertIn("Type 'dig' to start.", msg_p)
        self.assertNotIn("mine", msg_p)

        ok_h, msg_h, _ = ex.hammer(1, 1)
        self.assertFalse(ok_h)
        self.assertIn("Type 'dig' to start.", msg_h)
        self.assertNotIn("mine", msg_h)

        # 2. TUI dispatch accepts only canonical commands
        from poketokenbar.tui import PokeTokenBarTUI
        from unittest.mock import patch, MagicMock
        import io

        tui = PokeTokenBarTUI()
        tui.engine = self.engine
        tui.current_tab = 9
        tui.minigame_state = "excavator"

        with patch("poketokenbar.tui.UsageManager") as mock_mgr:
            instance = MagicMock()
            instance.get_summary.return_value = {
                "total_tokens": 100_000_000, "today_tokens": 0, "week_tokens": 0,
                "month_tokens": 0, "antigravity_today": 0, "gemini_today": 0,
                "claude_today": 0, "burn_rate_tpm": 0, "active_days": []
            }
            mock_mgr.return_value = instance

            # 'mine' command should NOT trigger excavation
            commands_mine = "\n".join(["mine", "q"]) + "\n"
            with patch("sys.stdin", io.StringIO(commands_mine)), patch("sys.stdout"):
                tui.run()
            self.assertEqual(self.engine.excavator.game_state, "idle")

            # 'dig 100k' with cost parameter is rejected with fixed cost guidance
            commands_dig_cost = "\n".join(["dig 100k", "q"]) + "\n"
            self.engine.excavator.game_state = "idle"
            with patch("sys.stdin", io.StringIO(commands_dig_cost)), patch("sys.stdout"):
                tui.run()
            self.assertEqual(self.engine.excavator.game_state, "idle")
            self.assertIn("fixed cost of 500K", tui.message)

            # 'bet' on excavator is rejected with fixed cost guidance
            commands_bet = "\n".join(["bet 500k", "q"]) + "\n"
            self.engine.excavator.game_state = "idle"
            with patch("sys.stdin", io.StringIO(commands_bet)), patch("sys.stdout"):
                tui.run()
            self.assertEqual(self.engine.excavator.game_state, "idle")
            self.assertIn("fixed cost of 500K", tui.message)

            # Canonical 'dig' command DOES trigger excavation
            commands_dig = "\n".join(["dig", "q"]) + "\n"
            with patch("sys.stdin", io.StringIO(commands_dig)), patch("sys.stdout"):
                tui.run()
            self.assertEqual(self.engine.excavator.game_state, "digging")

            # 3. Derby canonical command enforcement
            # 'start' command should NOT launch race and should guide user to 'race'
            tui.minigame_state = "derby"
            self.engine.derby.place_bet(1, 500_000)
            commands_start = "\n".join(["start", "q"]) + "\n"
            with patch("sys.stdin", io.StringIO(commands_start)), patch("sys.stdout"):
                tui.run()
            self.assertEqual(self.engine.derby.game_state, "bet_placed")
            self.assertIn("Use 'race' to launch the derby race!", tui.message)

            # Canonical 'race' command DOES launch the race
            commands_race = "\n".join(["race", "q"]) + "\n"
            with patch("sys.stdin", io.StringIO(commands_race)), patch("sys.stdout"), patch.object(tui, "animate_derby_race"):
                tui.run()
            self.assertEqual(self.engine.derby.game_state, "finished")

    def test_game_corner_play_command_requires_index(self):
        from poketokenbar.tui import PokeTokenBarTUI
        from unittest.mock import patch, MagicMock
        import io

        tui = PokeTokenBarTUI()
        tui.engine = self.engine
        tui.current_tab = 9
        tui.minigame_state = "menu"

        with patch("poketokenbar.tui.UsageManager") as mock_mgr:
            instance = MagicMock()
            instance.get_summary.return_value = {
                "total_tokens": 100_000_000, "today_tokens": 0, "week_tokens": 0,
                "month_tokens": 0, "antigravity_today": 0, "gemini_today": 0,
                "claude_today": 0, "burn_rate_tpm": 0, "active_days": []
            }
            mock_mgr.return_value = instance

            # 1. Numbered indices 1-8 should succeed
            idx_map = {
                "1": "poker", "2": "gacha", "3": "slot", "4": "blackjack",
                "5": "voltorb", "6": "excavator", "7": "trivia", "8": "derby"
            }
            for idx, expected_state in idx_map.items():
                commands = f"play {idx}\nq\n"
                tui.minigame_state = "menu"
                with patch("sys.stdin", io.StringIO(commands)), patch("sys.stdout"):
                    tui.run()
                self.assertEqual(tui.minigame_state, expected_state)

            # 2. Game names must be rejected
            for name in ["poker", "voltorb", "slot", "blackjack", "excavator", "trivia", "derby"]:
                commands = f"play {name}\nq\n"
                tui.minigame_state = "menu"
                with patch("sys.stdin", io.StringIO(commands)), patch("sys.stdout"):
                    tui.run()
                self.assertEqual(tui.minigame_state, "menu")
                self.assertIn("Type 'play <1-8>'", tui.message)

            # 3. Direct name commands like 'slot' on tab 9 must not switch state
            commands_slot = "slot\nq\n"
            tui.minigame_state = "menu"
            with patch("sys.stdin", io.StringIO(commands_slot)), patch("sys.stdout"):
                tui.run()
            self.assertEqual(tui.minigame_state, "menu")

    def test_derby_tab_width_limit(self):
        import io
        import sys
        import re
        from poketokenbar.tui_tabs.game_corner import render_derby_tab

        class MockApp:
            def __init__(self, engine):
                self.engine = engine

        app = MockApp(self.engine)

        for state in ["idle", "bet_placed", "finished"]:
            if state == "idle":
                self.engine.derby._reset_racers()
                self.engine.derby.game_state = "idle"
            elif state == "bet_placed":
                self.engine.derby.place_bet(1, 500_000)
            elif state == "finished":
                self.engine.derby.place_bet(1, 500_000)
                self.engine.derby.resolve_race()

            buf = io.StringIO()
            old_stdout = sys.stdout
            try:
                sys.stdout = buf
                render_derby_tab(app)
            finally:
                sys.stdout = old_stdout

            output = buf.getvalue()
            for line in output.splitlines():
                clean_line = re.sub(r"\033\[[0-9;]*m", "", line)
                self.assertLessEqual(
                    len(clean_line), 72,
                    f"Derby line exceeds 72 cols in state '{state}': '{clean_line}' (len {len(clean_line)})"
                )

    def test_derby_animation_pacing(self):
        from poketokenbar.tui import PokeTokenBarTUI
        from unittest.mock import patch, MagicMock

        tui = PokeTokenBarTUI()
        tui.engine = self.engine

        mock_frames = [
            {"positions": {1: 0, 2: 0, 3: 0, 4: 0}, "events": ["Start!"]},
            {"positions": {1: 5, 2: 6, 3: 4, 4: 2}, "events": ["Mid 1"]},
            {"positions": {1: 15, 2: 12, 3: 16, 4: 2}, "events": ["Mid 2"]},
            {"positions": {1: 24, 2: 18, 3: 20, 4: 2}, "events": ["Finish!"]},
        ]

        with patch("time.sleep") as mock_sleep, patch("sys.stdout"), patch.object(tui, "render_header"), patch.object(tui, "render_tabs"), patch.object(tui, "render_footer"):
            tui.animate_derby_race(mock_frames)

            sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
            self.assertEqual(len(sleep_calls), 4)
            self.assertEqual(sleep_calls[0], 0.50)
            self.assertEqual(sleep_calls[1], 0.45)
            self.assertEqual(sleep_calls[2], 0.45)
            self.assertEqual(sleep_calls[3], 0.80)


if __name__ == "__main__":
    unittest.main()


