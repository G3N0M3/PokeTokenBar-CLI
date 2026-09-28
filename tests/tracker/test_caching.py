import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import urllib.error

from poketokenbar.tracker.antigravity import AntigravityUsageReader
from poketokenbar.tracker.gemini import GeminiUsageReader
from poketokenbar.tracker.claude import ClaudeUsageReader
from poketokenbar.game.pokeapi import PokeAPIClient


class TestTrackerDiskCaching(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.cache_dir = self.temp_path / "cache" / "tracker"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.orig_cache_env = os.environ.get("PTB_CACHE_DIR")
        os.environ["PTB_CACHE_DIR"] = str(self.cache_dir)

    def tearDown(self):
        if self.orig_cache_env is not None:
            os.environ["PTB_CACHE_DIR"] = self.orig_cache_env
        else:
            os.environ.pop("PTB_CACHE_DIR", None)
        self.temp_dir.cleanup()

    def test_gemini_disk_cache(self):
        root_dir = self.temp_path / "gemini" / "proj1" / "chats"
        root_dir.mkdir(parents=True, exist_ok=True)
        chat_file = root_dir / "chat1.json"
        chat_file.write_text(json.dumps([
            {
                "timestamp": "2026-09-28T00:00:00Z",
                "totalTokens": 150,
                "promptTokenCount": 100,
                "candidatesTokenCount": 50
            }
        ]), encoding="utf-8")

        reader1 = GeminiUsageReader(root_dir=str(self.temp_path / "gemini"))
        entries1 = reader1.get_entries()
        self.assertEqual(len(entries1), 1)
        self.assertEqual(entries1[0].input_tokens, 100)

        cache_file = self.cache_dir / "gemini.json"
        self.assertTrue(cache_file.exists())

        # Second reader should load from disk cache
        reader2 = GeminiUsageReader(root_dir=str(self.temp_path / "gemini"))
        self.assertIn(str(chat_file.resolve()), reader2._cache)
        entries2 = reader2.get_entries()
        self.assertEqual(len(entries2), 1)
        self.assertEqual(entries2[0].id, entries1[0].id)

    def test_claude_disk_cache(self):
        proj_dir = self.temp_path / "claude" / "project1"
        proj_dir.mkdir(parents=True, exist_ok=True)
        jsonl_file = proj_dir / "events.jsonl"
        jsonl_file.write_text(json.dumps({
            "timestamp": "2026-09-28T00:00:00Z",
            "model": "claude-3-7-sonnet",
            "usage": {
                "input_tokens": 200,
                "output_tokens": 80,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0
            }
        }) + "\n", encoding="utf-8")

        reader1 = ClaudeUsageReader(root_dir=str(self.temp_path / "claude"))
        entries1 = reader1.get_entries()
        self.assertEqual(len(entries1), 1)
        self.assertEqual(entries1[0].input_tokens, 200)

        cache_file = self.cache_dir / "claude.json"
        self.assertTrue(cache_file.exists())

        # Second reader should load from disk cache
        reader2 = ClaudeUsageReader(root_dir=str(self.temp_path / "claude"))
        self.assertIn(str(jsonl_file.resolve()), reader2._cache)
        entries2 = reader2.get_entries()
        self.assertEqual(len(entries2), 1)
        self.assertEqual(entries2[0].id, entries1[0].id)

    def test_pokeapi_negative_cache(self):
        from poketokenbar.game.pokeapi import SPRITE_DIR
        client = PokeAPIClient()

        missing_marker = SPRITE_DIR / "normal_front_8888.missing"
        missing_marker.touch()

        try:
            # Should immediately return None without attempting network call
            with patch("urllib.request.urlopen") as mock_url:
                res = client.download_sprite(8888, is_shiny=False, is_back=False)
                self.assertIsNone(res)
                mock_url.assert_not_called()
        finally:
            if missing_marker.exists():
                missing_marker.unlink()


if __name__ == "__main__":
    unittest.main()
