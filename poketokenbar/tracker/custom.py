import os
import json
import uuid
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from poketokenbar.tracker.base import UsageEntry
from poketokenbar.utils.formatting import parse_tokens, format_tokens


def get_custom_file_path() -> Path:
    """Returns the configured custom token file path, checking env, state, or default locations."""
    env_path = os.environ.get("PTB_TOKEN_FILE")
    if env_path:
        return Path(env_path)

    from poketokenbar.game.storage import StorageManager
    try:
        state = StorageManager.load_state()
        configured = state.get("custom_token_file")
        if configured:
            return Path(configured)
    except Exception:
        pass

    default_path = Path.home() / ".poketokenbar" / "token_usage.json"
    if not default_path.exists():
        for alt in ["custom_usage.json", "tokens.json"]:
            alt_path = Path.home() / ".poketokenbar" / alt
            if alt_path.exists():
                return alt_path
    return default_path


def parse_date_value(date_val: Any, default_dt: datetime.datetime) -> datetime.datetime:
    """Safely converts string/epoch date representations into a timezone-aware datetime."""
    if isinstance(date_val, (int, float)):
        if date_val > 1_000_000_000_000:
            date_val = date_val / 1000.0
        return datetime.datetime.fromtimestamp(date_val, tz=datetime.timezone.utc).astimezone()

    if isinstance(date_val, str):
        clean_str = date_val.strip()
        try:
            dt = datetime.datetime.fromisoformat(clean_str.replace("Z", "+00:00"))
            return dt.astimezone() if dt.tzinfo else dt
        except Exception:
            pass

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                dt = datetime.datetime.strptime(clean_str[:len(fmt)], fmt)
                return dt
            except Exception:
                continue

    return default_dt


def extract_token_counts(item: Any) -> Tuple[int, int, int, int, int]:
    """Extracts (total_tokens, input_tokens, output_tokens, cache_write, cache_read) from diverse payloads."""
    if isinstance(item, (int, float)):
        t = max(0, int(item))
        return t, t, 0, 0, 0

    if isinstance(item, str):
        t = parse_tokens(item)
        t = max(0, t)
        return t, t, 0, 0, 0

    if isinstance(item, dict):
        inp = int(item.get("input_tokens", 0) or 0)
        out = int(item.get("output_tokens", 0) or 0)
        cw = int(item.get("cache_write_tokens", 0) or 0)
        cr = int(item.get("cache_read_tokens", 0) or 0)

        tot = item.get("tokens")
        if tot is None:
            tot = item.get("total_tokens")

        if tot is not None:
            if isinstance(tot, str):
                parsed = parse_tokens(tot)
                tot = max(0, parsed)
            else:
                tot = max(0, int(tot))
        else:
            tot = inp + out + cw + cr

        if inp + out + cw + cr == 0 and tot > 0:
            inp = tot

        return tot, inp, out, cw, cr

    return 0, 0, 0, 0, 0


class CustomUsageReader:
    """Parses user-provided token usage files (JSON, JSONL) for custom/external LLM activity."""

    def __init__(self, file_path: Optional[str] = None):
        self._explicit_path = Path(file_path) if file_path else None
        self._cached_stat: Optional[Tuple[float, int]] = None
        self._cached_entries: List[UsageEntry] = []

    @property
    def target_file(self) -> Path:
        return self._explicit_path if self._explicit_path else get_custom_file_path()

    def get_entries(self) -> List[UsageEntry]:
        path = self.target_file
        if not path.exists() or not path.is_file():
            return []

        try:
            st = path.stat()
            current_stat = (st.st_mtime, st.st_size)
            if self._cached_stat == current_stat:
                return self._cached_entries

            content = path.read_text(encoding="utf-8").strip()
            if not content:
                self._cached_stat = current_stat
                self._cached_entries = []
                return []

            entries = self._parse_content(content, path, datetime.datetime.fromtimestamp(st.st_mtime, tz=datetime.timezone.utc).astimezone())
            self._cached_stat = current_stat
            self._cached_entries = entries
            return entries
        except Exception:
            return self._cached_entries

    def _parse_content(self, content: str, path: Path, file_dt: datetime.datetime) -> List[UsageEntry]:
        entries: List[UsageEntry] = []
        file_id = path.stem

        # Try parsing as standard JSON
        try:
            data = json.loads(content)
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    entry = self._item_to_entry(item, file_id, idx, file_dt)
                    if entry:
                        entries.append(entry)
                return entries
            elif isinstance(data, dict):
                # Format A: {"entries": [...]} or {"usage": [...]}
                list_key = next((k for k in ["entries", "usage", "tokens", "data"] if isinstance(data.get(k), list)), None)
                if list_key:
                    for idx, item in enumerate(data[list_key]):
                        entry = self._item_to_entry(item, file_id, idx, file_dt)
                        if entry:
                            entries.append(entry)
                    return entries

                # Format B: {"2026-09-28": 15000, "2026-09-27": {"tokens": 20000}}
                idx = 0
                for date_str, val in data.items():
                    tot, inp, out, cw, cr = extract_token_counts(val)
                    if tot <= 0:
                        continue
                    dt = parse_date_value(date_str, file_dt)
                    model_str = val.get("model", "custom") if isinstance(val, dict) else "custom"
                    entries.append(UsageEntry(
                        id=f"custom|{file_id}|{idx}|{date_str}",
                        date=dt,
                        local_day=dt.strftime("%Y-%m-%d"),
                        model=f"custom/{model_str}",
                        input_tokens=inp,
                        output_tokens=out,
                        cache_write_tokens=cw,
                        cache_read_tokens=cr
                    ))
                    idx += 1
                return entries
        except Exception:
            pass

        # Try parsing as JSONL (one JSON object per line)
        idx = 0
        for line in content.splitlines():
            clean_line = line.strip()
            if not clean_line:
                continue
            try:
                line_data = json.loads(clean_line)
                entry = self._item_to_entry(line_data, file_id, idx, file_dt)
                if entry:
                    entries.append(entry)
                    idx += 1
            except Exception:
                continue

        return entries

    def _item_to_entry(self, item: Any, file_id: str, idx: int, file_dt: datetime.datetime) -> Optional[UsageEntry]:
        tot, inp, out, cw, cr = extract_token_counts(item)
        if tot <= 0:
            return None

        date_val = None
        model_str = "custom"
        item_id = None
        if isinstance(item, dict):
            date_val = item.get("date") or item.get("timestamp") or item.get("time") or item.get("created_at")
            model_str = str(item.get("model", "custom"))
            item_id = item.get("id")

        dt = parse_date_value(date_val, file_dt)
        entry_id = f"custom|{file_id}|{item_id or idx}"
        return UsageEntry(
            id=entry_id,
            date=dt,
            local_day=dt.strftime("%Y-%m-%d"),
            model=f"custom/{model_str}",
            input_tokens=inp,
            output_tokens=out,
            cache_write_tokens=cw,
            cache_read_tokens=cr
        )

    @classmethod
    def log_entry(
        cls,
        tokens: int,
        model: str = "custom",
        date_dt: Optional[datetime.datetime] = None,
        file_path: Optional[Path] = None
    ) -> Tuple[bool, str]:
        """Appends a new token usage record directly to the custom token usage file."""
        if tokens <= 0:
            return False, "Token count must be a positive integer."

        target = file_path if file_path else get_custom_file_path()
        target.parent.mkdir(parents=True, exist_ok=True)

        if date_dt is None:
            date_dt = datetime.datetime.now().astimezone()

        new_record = {
            "id": uuid.uuid4().hex[:8],
            "date": date_dt.isoformat(),
            "tokens": tokens,
            "model": model
        }

        records = []
        if target.exists():
            try:
                content = target.read_text(encoding="utf-8").strip()
                if content:
                    existing = json.loads(content)
                    if isinstance(existing, list):
                        records = existing
                    elif isinstance(existing, dict) and isinstance(existing.get("entries"), list):
                        records = existing["entries"]
            except Exception:
                records = []

        records.append(new_record)

        try:
            tmp_target = target.with_name(f"{target.name}.{uuid.uuid4().hex[:6]}.tmp")
            with open(tmp_target, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            tmp_target.replace(target)
            return True, f"Logged {format_tokens(tokens)} tokens ({model}) to {target.name}."
        except Exception as e:
            return False, f"Failed to write to {target.name}: {e}"
