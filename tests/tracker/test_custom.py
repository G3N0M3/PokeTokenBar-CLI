import os
import json
import tempfile
import unittest
from pathlib import Path
import datetime

from poketokenbar.tracker.custom import CustomUsageReader, extract_token_counts, parse_date_value


class TestCustomUsageReader(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.token_file = self.temp_path / "token_usage.json"
        self.orig_env = os.environ.get("PTB_TOKEN_FILE")
        os.environ["PTB_TOKEN_FILE"] = str(self.token_file)

    def tearDown(self):
        if self.orig_env is not None:
            os.environ["PTB_TOKEN_FILE"] = self.orig_env
        else:
            os.environ.pop("PTB_TOKEN_FILE", None)
        self.temp_dir.cleanup()

    def test_nonexistent_file_returns_empty(self):
        reader = CustomUsageReader(file_path=str(self.temp_path / "does_not_exist.json"))
        entries = reader.get_entries()
        self.assertEqual(entries, [])

    def test_parse_json_list_format(self):
        data = [
            {
                "date": "2026-09-28T10:15:00+00:00",
                "tokens": 5000,
                "model": "gpt-4o"
            },
            {
                "date": "2026-09-28T12:30:00+00:00",
                "input_tokens": 3000,
                "output_tokens": 1500,
                "model": "claude-3-5-sonnet"
            },
            {
                "date": "2026-09-27T08:00:00+00:00",
                "tokens": "25k",
                "model": "gemini-1.5-pro"
            }
        ]
        self.token_file.write_text(json.dumps(data), encoding="utf-8")

        reader = CustomUsageReader(file_path=str(self.token_file))
        entries = reader.get_entries()
        self.assertEqual(len(entries), 3)

        self.assertEqual(entries[0].total_tokens, 5000)
        self.assertEqual(entries[0].model, "custom/gpt-4o")

        self.assertEqual(entries[1].input_tokens, 3000)
        self.assertEqual(entries[1].output_tokens, 1500)
        self.assertEqual(entries[1].total_tokens, 4500)

        self.assertEqual(entries[2].total_tokens, 25000)

    def test_parse_json_dict_dates(self):
        data = {
            "2026-09-28": 15000,
            "2026-09-27": {
                "tokens": 30000,
                "model": "o1-mini"
            }
        }
        self.token_file.write_text(json.dumps(data), encoding="utf-8")

        reader = CustomUsageReader(file_path=str(self.token_file))
        entries = reader.get_entries()
        self.assertEqual(len(entries), 2)
        total_toks = sum(e.total_tokens for e in entries)
        self.assertEqual(total_toks, 45000)

    def test_parse_jsonl_format(self):
        lines = [
            json.dumps({"date": "2026-09-28T09:00:00Z", "tokens": 1200, "model": "mistral"}),
            json.dumps({"date": "2026-09-28T10:00:00Z", "tokens": 2800, "model": "llama3"})
        ]
        self.token_file.write_text("\n".join(lines), encoding="utf-8")

        reader = CustomUsageReader(file_path=str(self.token_file))
        entries = reader.get_entries()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].total_tokens, 1200)
        self.assertEqual(entries[1].total_tokens, 2800)

    def test_caching_behavior(self):
        self.token_file.write_text(json.dumps([{"date": "2026-09-28", "tokens": 100}]), encoding="utf-8")
        reader = CustomUsageReader(file_path=str(self.token_file))
        entries1 = reader.get_entries()
        self.assertEqual(len(entries1), 1)

        # Calling again should use cached stat
        entries2 = reader.get_entries()
        self.assertIs(entries1, entries2)

    def test_log_entry_appends_and_creates(self):
        log_file = self.temp_path / "logged_usage.json"
        self.assertFalse(log_file.exists())

        ok, msg = CustomUsageReader.log_entry(25000, model="gpt-4o", file_path=log_file)
        self.assertTrue(ok)
        self.assertTrue(log_file.exists())

        # Check content
        content = json.loads(log_file.read_text(encoding="utf-8"))
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]["tokens"], 25000)
        self.assertEqual(content[0]["model"], "gpt-4o")

        # Second append
        ok2, msg2 = CustomUsageReader.log_entry(15000, model="claude-3-5", file_path=log_file)
        self.assertTrue(ok2)
        content2 = json.loads(log_file.read_text(encoding="utf-8"))
        self.assertEqual(len(content2), 2)
        self.assertEqual(content2[1]["tokens"], 15000)

        # Reader parses both
        reader = CustomUsageReader(file_path=str(log_file))
        entries = reader.get_entries()
        self.assertEqual(len(entries), 2)
