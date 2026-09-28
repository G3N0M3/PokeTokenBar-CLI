import os
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
        self._cache = {}  # str(chat_file) -> (stat_key, List[UsageEntry])
        self._cache_dir = Path(os.environ.get("PTB_CACHE_DIR", Path.home() / ".poketokenbar" / "cache" / "tracker"))
        self._cache_file = self._cache_dir / "gemini.json"
        self._load_cache()

    def _load_cache(self):
        if not self._cache_file.exists():
            return
        try:
            with open(self._cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("version") != 1:
                return
            for path_str, item in data.get("files", {}).items():
                stat_key = tuple(item["stat"])
                entries = []
                for r in item["entries"]:
                    try:
                        entries.append(UsageEntry(
                            id=r[0],
                            date=datetime.datetime.fromisoformat(r[1]),
                            local_day=r[2],
                            model=r[3],
                            input_tokens=r[4],
                            output_tokens=r[5],
                            cache_write_tokens=r[6],
                            cache_read_tokens=r[7],
                        ))
                    except Exception:
                        continue
                self._cache[path_str] = (stat_key, entries)
        except Exception:
            self._cache.clear()

    def _save_cache(self):
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            files_data = {}
            for path_str, (stat_key, entries) in self._cache.items():
                try:
                    if not Path(path_str).exists():
                        continue
                except Exception:
                    continue
                files_data[path_str] = {
                    "stat": list(stat_key),
                    "entries": [
                        [
                            e.id,
                            e.date.isoformat(),
                            e.local_day,
                            e.model,
                            e.input_tokens,
                            e.output_tokens,
                            e.cache_write_tokens,
                            e.cache_read_tokens,
                        ]
                        for e in entries
                    ]
                }
            tmp_file = self._cache_file.with_name(self._cache_file.name + ".tmp")
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump({"version": 1, "files": files_data}, f)
            tmp_file.replace(self._cache_file)
        except Exception:
            pass

    def get_entries(self) -> List[UsageEntry]:
        if not self.root_dir.exists():
            return []

        entries: List[UsageEntry] = []
        cache_updated = False
        
        # Optimize by avoiding recursive ** glob. Look specifically in root_dir/<project>/chats/
        chat_files = []
        try:
            for proj_dir in self.root_dir.iterdir():
                if proj_dir.is_dir():
                    chats_dir = proj_dir / "chats"
                    if chats_dir.exists() and chats_dir.is_dir():
                        chat_files.extend(chats_dir.glob("*.json*"))
        except Exception:
            pass

        for chat_file in chat_files:
            path_key = str(chat_file.resolve())
            try:
                st = chat_file.stat()
                mtime = st.st_mtime
                size = st.st_size
                stat_key = (mtime, size)
                cached_key, cached_entries = self._cache.get(path_key, (None, None))
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
                self._cache[path_key] = (stat_key, file_entries)
                cache_updated = True
                entries.extend(file_entries)
            except Exception:
                continue

        if cache_updated:
            self._save_cache()

        return entries
