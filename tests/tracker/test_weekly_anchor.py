import os
import json
import tempfile
import unittest
import datetime
from pathlib import Path
from unittest.mock import patch

from poketokenbar.tracker.base import UsageEntry
from poketokenbar.tracker.manager import UsageManager, get_week_start_datetime


class TestWeeklyAnchorAndUsageManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.state_file = self.temp_path / "state.json"
        self.token_file = self.temp_path / "token_usage.json"
        self.cache_dir = self.temp_path / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        os.environ["PTB_STATE_FILE"] = str(self.state_file)
        os.environ["PTB_TOKEN_FILE"] = str(self.token_file)
        os.environ["PTB_CACHE_DIR"] = str(self.cache_dir)

    def tearDown(self):
        os.environ.pop("PTB_STATE_FILE", None)
        os.environ.pop("PTB_TOKEN_FILE", None)
        os.environ.pop("PTB_CACHE_DIR", None)
        self.temp_dir.cleanup()

    def test_get_week_start_datetime_calculation(self):
        # Wednesday, 2026-09-30 15:30:00
        wednesday = datetime.datetime(2026, 9, 30, 15, 30, 0, tzinfo=datetime.timezone.utc)

        # 1. Monday anchor: should return Monday 2026-09-28 00:00:00
        start_mon, label_mon = get_week_start_datetime(wednesday, "monday")
        self.assertEqual(label_mon, "Monday")
        self.assertEqual(start_mon.year, 2026)
        self.assertEqual(start_mon.month, 9)
        self.assertEqual(start_mon.day, 28)
        self.assertEqual(start_mon.hour, 0)
        self.assertEqual(start_mon.minute, 0)

        # 2. Sunday anchor: should return Sunday 2026-09-27 00:00:00
        start_sun, label_sun = get_week_start_datetime(wednesday, "sunday")
        self.assertEqual(label_sun, "Sunday")
        self.assertEqual(start_sun.day, 27)

        # 3. Wednesday anchor (same day): should return today 2026-09-30 00:00:00
        start_wed, label_wed = get_week_start_datetime(wednesday, "wednesday")
        self.assertEqual(label_wed, "Wednesday")
        self.assertEqual(start_wed.day, 30)

        # 4. Rolling 7-day anchor: should return 6 days ago (2026-09-24 00:00:00)
        start_roll, label_roll = get_week_start_datetime(wednesday, "rolling")
        self.assertEqual(label_roll, "rolling")
        self.assertEqual(start_roll.day, 24)

    def test_usage_manager_includes_custom_entries(self):
        # Create custom entries in token file
        now = datetime.datetime.now().astimezone()
        today_str = now.strftime("%Y-%m-%d")
        data = [
            {"date": now.isoformat(), "tokens": 50000, "model": "gpt-4o"},
            {"date": (now - datetime.timedelta(days=2)).isoformat(), "tokens": 30000, "model": "claude"}
        ]
        self.token_file.write_text(json.dumps(data), encoding="utf-8")

        mgr = UsageManager()
        try:
            summary = mgr.get_summary(force=True, week_start_day="monday")
            self.assertGreaterEqual(summary["today_tokens"], 50000)
            self.assertGreaterEqual(summary["week_tokens"], 80000)
            self.assertEqual(summary["custom_today"], 50000)
            self.assertEqual(summary["week_start_day"], "monday")
            self.assertTrue(summary["custom_file_exists"])
        finally:
            mgr.stop()
