import os
import re
import io
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from poketokenbar.game.companion.engine import CompanionEngine
from poketokenbar.tui.app import PokeTokenBarTUI
from poketokenbar.tui.router import CommandRouter
from poketokenbar.tui_tabs.companion import render as render_companion
from poketokenbar.tui_tabs.settings import render_settings_tab


def strip_ansi(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*[mK]', '', text)


class TestCompanionWeeklyAndCustomTokens(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.state_file = self.temp_path / "state.json"
        self.token_file = self.temp_path / "token_usage.json"
        self.cache_dir = self.temp_path / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        real_pokeapi = Path.home() / ".poketokenbar" / "cache" / "pokeapi"
        if real_pokeapi.exists():
            try:
                os.symlink(real_pokeapi, self.cache_dir / "pokeapi")
            except Exception:
                pass

        os.environ["PTB_STATE_FILE"] = str(self.state_file)
        os.environ["PTB_TOKEN_FILE"] = str(self.token_file)
        os.environ["PTB_CACHE_DIR"] = str(self.cache_dir)

        self.engine = CompanionEngine()

    def tearDown(self):
        os.environ.pop("PTB_STATE_FILE", None)
        os.environ.pop("PTB_TOKEN_FILE", None)
        os.environ.pop("PTB_CACHE_DIR", None)
        self.temp_dir.cleanup()

    def test_engine_week_start_day(self):
        # Default is monday
        self.assertEqual(self.engine.get_week_start_day(), "monday")

        # Set to sunday
        ok, msg = self.engine.set_week_start_day("sunday")
        self.assertTrue(ok)
        self.assertIn("Sunday", msg)
        self.assertEqual(self.engine.get_week_start_day(), "sunday")

        # Set to rolling
        ok, msg = self.engine.set_week_start_day("rolling")
        self.assertTrue(ok)
        self.assertEqual(self.engine.get_week_start_day(), "rolling")

        # Invalid day
        ok, msg = self.engine.set_week_start_day("invalid_day")
        self.assertFalse(ok)
        self.assertIn("Invalid", msg)

    def test_engine_custom_token_file(self):
        custom_target = self.temp_path / "my_custom.json"
        ok, msg = self.engine.set_custom_token_file(str(custom_target))
        self.assertTrue(ok)
        self.assertEqual(self.engine.state.get("custom_token_file"), str(custom_target.resolve()))

        # Reset to default
        ok, msg = self.engine.set_custom_token_file("default")
        self.assertTrue(ok)
        self.assertIsNone(self.engine.state.get("custom_token_file"))

    def test_engine_log_custom_tokens(self):
        ok, msg = self.engine.log_custom_tokens(50000, model="gpt-4o")
        self.assertTrue(ok)
        self.assertIn("50.0K", msg)
        self.assertTrue(self.token_file.exists())

        # Verify contents
        data = json.loads(self.token_file.read_text(encoding="utf-8"))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["tokens"], 50000)
        self.assertEqual(data[0]["model"], "gpt-4o")

    def test_tui_commands_week_and_token(self):
        app = PokeTokenBarTUI()
        try:
            # Test 'week start sunday'
            CommandRouter.dispatch(app, "week start sunday")
            self.assertEqual(app.engine.get_week_start_day(), "sunday")
            self.assertIn("Sunday", app.message)

            # Test 'token add 25k o1'
            CommandRouter.dispatch(app, "token add 25k o1")
            self.assertIn("25.0K", app.message)

            # Test 'token file'
            custom_p = str(self.temp_path / "another.json")
            CommandRouter.dispatch(app, f"token file {custom_p}")
            self.assertEqual(app.engine.state.get("custom_token_file"), str(Path(custom_p).resolve()))
        finally:
            app.tracker.stop()

    def test_72_column_layout_compliance(self):
        """Verifies strictly that Companion Tab and Settings Tab render within 72 columns."""
        app = PokeTokenBarTUI()
        try:
            # 1. Test Companion Tab rendering with custom tokens & weekly info
            summary = {
                "today_tokens": 125000,
                "antigravity_today": 75000,
                "custom_today": 50000,
                "week_tokens": 450000,
                "week_mode_label": "Monday",
                "week_start_date": "2026-09-28",
                "month_tokens": 1200000,
                "total_tokens": 5000000,
                "burn_rate_tpm": 1200,
                "billing_cycle_day": 1,
                "billing_cycle_start": "2026-09-01",
            }
            captured = io.StringIO()
            with patch.object(sys, 'stdout', captured):
                render_companion(app, summary)

            for idx, line in enumerate(captured.getvalue().splitlines()):
                clean = strip_ansi(line)
                self.assertLessEqual(
                    len(clean), 72,
                    f"Companion Tab line {idx+1} exceeded 72 columns ({len(clean)} chars): '{clean}'"
                )

            # 2. Test Settings Tab rendering
            captured_settings = io.StringIO()
            with patch.object(sys, 'stdout', captured_settings):
                render_settings_tab(app)

            for idx, line in enumerate(captured_settings.getvalue().splitlines()):
                clean = strip_ansi(line)
                self.assertLessEqual(
                    len(clean), 72,
                    f"Settings Tab line {idx+1} exceeded 72 columns ({len(clean)} chars): '{clean}'"
                )
        finally:
            app.tracker.stop()
