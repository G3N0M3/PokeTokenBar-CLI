import os
import json
import datetime
from pathlib import Path
from typing import List, Optional

from poketokenbar.tracker.base import UsageEntry

class ClaudeUsageReader:
    def __init__(self, root_dir: Optional[str] = None):
        if root_dir:
            self.root_dir = Path(root_dir)
        else:
            self.root_dir = Path.home() / ".claude" / "projects"
        self._cache = {}  # str(path) -> (stat_key, List[UsageEntry])
        self._cache_dir = Path(os.environ.get("PTB_CACHE_DIR", Path.home() / ".poketokenbar" / "cache" / "tracker"))
        self._cache_file = self._cache_dir / "claude.json"
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
        
        # Optimize by avoiding recursive ** glob. Look specifically in root_dir/<project>/*.jsonl
        jsonl_files = []
        try:
            for proj_dir in self.root_dir.iterdir():
                if proj_dir.is_dir():
                    jsonl_files.extend(proj_dir.glob("*.jsonl"))
        except Exception:
            pass

        for jsonl_file in jsonl_files:
            path_key = str(jsonl_file.resolve())
            try:
                st = jsonl_file.stat()
                mtime = st.st_mtime
                size = st.st_size
                stat_key = (mtime, size)
                cached_key, cached_entries = self._cache.get(path_key, (None, None))
                if cached_key == stat_key and cached_entries is not None:
                    entries.extend(cached_entries)
                    continue

                file_entries = []
                with open(jsonl_file, "r", encoding="utf-8") as f:
                    for line_idx, line in enumerate(f):
                        line = line.strip()
                        if not line:
                            continue
                        data = json.loads(line)
                        usage = data.get("usage", {})
                        if not usage:
                            continue

                        inp = usage.get("input_tokens", 0)
                        out = usage.get("output_tokens", 0)
                        cache_w = usage.get("cache_creation_input_tokens", 0)
                        cache_r = usage.get("cache_read_input_tokens", 0)

                        if inp + out + cache_w + cache_r == 0:
                            continue

                        ts_str = data.get("timestamp", data.get("created_at"))
                        if ts_str:
                            try:
                                dt = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00")).astimezone()
                            except ValueError:
                                dt = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).astimezone()
                        else:
                            dt = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).astimezone()

                        msg_id = data.get("message_id", data.get("id", f"{jsonl_file.stem}_{line_idx}"))
                        file_entries.append(UsageEntry(
                            id=f"claude|{msg_id}",
                            date=dt,
                            local_day=dt.strftime("%Y-%m-%d"),
                            model=data.get("model", "claude-code"),
                            input_tokens=inp,
                            output_tokens=out,
                            cache_write_tokens=cache_w,
                            cache_read_tokens=cache_r
                        ))

                self._cache[path_key] = (stat_key, file_entries)
                cache_updated = True
                entries.extend(file_entries)
            except Exception:
                continue

        if cache_updated:
            self._save_cache()

        return entries
