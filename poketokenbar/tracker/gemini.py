import json
import datetime
from pathlib import Path
from typing import List, Optional

from poketokenbar.tracker.base import UsageEntry

class GeminiUsageReader:
    def __init__(self, root_dir: Optional[str] = None):
        if root_dir:
            self.root_dir = Path(root_dir)
        else:
            self.root_dir = Path.home() / ".gemini" / "tmp"
        self._cache = {}  # chat_file -> (mtime, List[UsageEntry])

    def get_entries(self) -> List[UsageEntry]:
        if not self.root_dir.exists():
            return []

        entries: List[UsageEntry] = []
        for chat_file in self.root_dir.glob("**/chats/*.json*"):
            try:
                st = chat_file.stat()
                mtime = st.st_mtime
                size = st.st_size
                stat_key = (mtime, size)
                cached_key, cached_entries = self._cache.get(chat_file, (None, None))
                if cached_key == stat_key and cached_entries is not None:
                    entries.extend(cached_entries)
                    continue

                dt = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).astimezone()
                local_day = dt.strftime("%Y-%m-%d")

                with open(chat_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Supports single JSON or JSON Lines
                records = []
                if chat_file.suffix == ".jsonl":
                    for line in content.splitlines():
                        if line.strip():
                            records.append(json.loads(line))
                else:
                    data = json.loads(content)
                    records = data if isinstance(data, list) else [data]

                file_entries = []
                for idx, rec in enumerate(records):
                    tokens = rec.get("tokens", rec.get("totalTokens", 0))
                    if isinstance(tokens, int) and tokens > 0:
                        inp = rec.get("promptTokenCount", rec.get("inputTokens", tokens))
                        out = rec.get("candidatesTokenCount", rec.get("outputTokens", 0))
                        entry_id = f"gemini|{chat_file.stem}|{idx}"

                        ts_raw = rec.get("timestamp", rec.get("created_at", rec.get("time")))
                        rec_dt = dt
                        if ts_raw:
                            try:
                                if isinstance(ts_raw, (int, float)):
                                    rec_dt = datetime.datetime.fromtimestamp(ts_raw, tz=datetime.timezone.utc).astimezone()
                                elif isinstance(ts_raw, str):
                                    rec_dt = datetime.datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).astimezone()
                            except Exception:
                                pass

                        file_entries.append(UsageEntry(
                            id=entry_id,
                            date=rec_dt,
                            local_day=rec_dt.strftime("%Y-%m-%d"),
                            model="gemini-cli",
                            input_tokens=inp if isinstance(inp, int) else tokens,
                            output_tokens=out if isinstance(out, int) else 0,
                            cache_write_tokens=0,
                            cache_read_tokens=0
                        ))
                self._cache[chat_file] = (stat_key, file_entries)
                entries.extend(file_entries)
            except Exception:
                continue

        return entries
