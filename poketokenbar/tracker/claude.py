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
        self._cache = {}  # jsonl_file -> (mtime, List[UsageEntry])

    def get_entries(self) -> List[UsageEntry]:
        if not self.root_dir.exists():
            return []

        entries: List[UsageEntry] = []
        for jsonl_file in self.root_dir.glob("**/*.jsonl"):
            try:
                st = jsonl_file.stat()
                mtime = st.st_mtime
                size = st.st_size
                stat_key = (mtime, size)
                cached_key, cached_entries = self._cache.get(jsonl_file, (None, None))
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

                self._cache[jsonl_file] = (stat_key, file_entries)
                entries.extend(file_entries)
            except Exception:
                continue

        return entries
