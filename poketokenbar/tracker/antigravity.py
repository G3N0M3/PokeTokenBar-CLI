import os
import glob
import sqlite3
import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from poketokenbar.tracker.base import UsageEntry

TOKEN_CEILING = 1_000_000_000

class AntigravityProtoDecoder:
    """Pure Python Protobuf wire-format parser tailored for Antigravity's Cascade step metadata."""

    @staticmethod
    def decode_varint(buffer: bytes, start_idx: int) -> Optional[Tuple[int, int]]:
        value = 0
        shift = 0
        idx = start_idx
        while idx < len(buffer):
            byte = buffer[idx]
            idx += 1
            value |= (byte & 0x7F) << shift
            if (byte & 0x80) == 0:
                return value, idx
            shift += 7
            if shift > 63:
                return None
        return None

    @classmethod
    def walk_fields(cls, buffer: bytes):
        idx = 0
        length = len(buffer)
        while idx < length:
            varint_res = cls.decode_varint(buffer, idx)
            if not varint_res:
                break
            key, idx = varint_res
            field_number = key >> 3
            wire_type = key & 0x7
            if field_number == 0:
                break

            if wire_type == 0:  # Varint
                val_res = cls.decode_varint(buffer, idx)
                if not val_res:
                    break
                val, idx = val_res
                yield field_number, val, None
            elif wire_type == 1:  # 64-bit fixed
                if idx + 8 > length:
                    break
                idx += 8
            elif wire_type == 2:  # Length-delimited (message / string / bytes)
                len_res = cls.decode_varint(buffer, idx)
                if not len_res:
                    break
                sub_len, idx = len_res
                if idx + sub_len > length:
                    break
                payload = buffer[idx:idx + sub_len]
                idx += sub_len
                yield field_number, 0, payload
            elif wire_type == 5:  # 32-bit fixed
                if idx + 4 > length:
                    break
                idx += 4
            else:
                break

    @classmethod
    def get_message(cls, buffer: bytes, field_num: int) -> Optional[bytes]:
        for fn, _, payload in cls.walk_fields(buffer):
            if fn == field_num and payload is not None:
                return payload
        return None

    @classmethod
    def get_varint(cls, buffer: bytes, field_num: int) -> Optional[int]:
        for fn, val, payload in cls.walk_fields(buffer):
            if fn == field_num and payload is None:
                return val
        return None

    @classmethod
    def get_string(cls, buffer: bytes, field_num: int) -> Optional[str]:
        payload = cls.get_message(buffer, field_num)
        if payload:
            try:
                return payload.decode('utf-8')
            except UnicodeDecodeError:
                return None
        return None

def parse_created_at(chat_model_bytes: bytes) -> Optional[datetime.datetime]:
    start_meta = AntigravityProtoDecoder.get_message(chat_model_bytes, 9)
    if not start_meta:
        return None
    created_at_msg = AntigravityProtoDecoder.get_message(start_meta, 4)
    if not created_at_msg:
        return None
    seconds = AntigravityProtoDecoder.get_varint(created_at_msg, 1)
    if seconds is None or seconds < 1_000_000_000 or seconds > 4_102_444_800:
        return None
    nanos = AntigravityProtoDecoder.get_varint(created_at_msg, 2) or 0
    if nanos >= 1_000_000_000:
        nanos = 0
    return datetime.datetime.fromtimestamp(seconds + nanos / 1e9, tz=datetime.timezone.utc)

def parse_generation_metadata(blob: bytes, conversation_id: str, row_idx: int, mtime: Optional[float] = None) -> Optional[UsageEntry]:
    chat_model = AntigravityProtoDecoder.get_message(blob, 1)
    if not chat_model:
        return None
    
    usage_msg = AntigravityProtoDecoder.get_message(chat_model, 4)
    if not usage_msg:
        return None
    
    dt = parse_created_at(chat_model)

    response_id = AntigravityProtoDecoder.get_string(usage_msg, 11)
    entry_id = f"antigravity|{response_id}" if response_id else f"antigravity|{conversation_id}|{row_idx}"

    model = AntigravityProtoDecoder.get_string(chat_model, 19) or "unknown"

    inp = AntigravityProtoDecoder.get_varint(usage_msg, 2) or 0
    out = AntigravityProtoDecoder.get_varint(usage_msg, 3) or 0
    cache_w = AntigravityProtoDecoder.get_varint(usage_msg, 4) or 0
    cache_r = AntigravityProtoDecoder.get_varint(usage_msg, 5) or 0

    if inp > TOKEN_CEILING or out > TOKEN_CEILING or cache_w > TOKEN_CEILING or cache_r > TOKEN_CEILING:
        return None

    if inp + out + cache_w + cache_r == 0:
        return None

    if dt:
        local_dt = dt.astimezone()
    elif mtime:
        local_dt = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).astimezone()
    else:
        local_dt = datetime.datetime.now().astimezone()

    local_day = local_dt.strftime("%Y-%m-%d")

    return UsageEntry(
        id=entry_id,
        date=local_dt,
        local_day=local_day,
        model=f"antigravity/{model}",
        input_tokens=inp,
        output_tokens=out,
        cache_write_tokens=cache_w,
        cache_read_tokens=cache_r
    )

class AntigravityUsageReader:
    def __init__(self, root_dir: Optional[str] = None):
        if root_dir:
            self.root_dir = Path(root_dir)
        else:
            self.root_dir = Path.home() / ".gemini" / "antigravity-cli" / "conversations"
        self._cache = {}  # db_path -> (mtime, List[UsageEntry])

    def get_entries(self, modified_since: Optional[datetime.datetime] = None) -> List[UsageEntry]:
        if not self.root_dir.exists() or not self.root_dir.is_dir():
            return []

        entries: List[UsageEntry] = []
        db_files = list(self.root_dir.glob("*.db"))

        for db_path in db_files:
            try:
                # Stat main file + WAL file
                mtime = db_path.stat().st_mtime
                wal_path = db_path.with_name(db_path.name + "-wal")
                if wal_path.exists():
                    mtime = max(mtime, wal_path.stat().st_mtime)

                if modified_since:
                    cutoff = modified_since.timestamp()
                    if mtime < cutoff:
                        continue

                cached_mtime, cached_entries = self._cache.get(db_path, (None, None))
                if cached_mtime == mtime and cached_entries is not None:
                    entries.extend(cached_entries)
                    continue

                conv_id = db_path.stem
                conn_uri = f"file:{db_path.resolve()}?mode=ro"
                try:
                    conn = sqlite3.connect(conn_uri, uri=True, timeout=10.0)
                except sqlite3.OperationalError:
                    # Fallback for immutable
                    conn = sqlite3.connect(f"file:{db_path.resolve()}?immutable=1", uri=True, timeout=10.0)

                try:
                    conn.execute("PRAGMA busy_timeout = 5000")
                except Exception:
                    pass

                cursor = conn.cursor()
                cursor.execute("SELECT idx, data FROM gen_metadata WHERE data IS NOT NULL")
                rows = cursor.fetchall()
                conn.close()

                db_entries = []
                for row_idx, blob in rows:
                    if blob:
                        entry = parse_generation_metadata(blob, conv_id, row_idx, mtime)
                        if entry:
                            db_entries.append(entry)

                self._cache[db_path] = (mtime, db_entries)
                entries.extend(db_entries)

            except Exception:
                # If reading DB fails (e.g. file lock during active write), reuse last valid cached entries
                cached_mtime, cached_entries = self._cache.get(db_path, (None, None))
                if cached_entries:
                    entries.extend(cached_entries)
                continue

        # Deduplicate by entry ID
        seen = {}
        for entry in entries:
            seen[entry.id] = entry
        
        sorted_entries = sorted(seen.values(), key=lambda e: e.date)
        return sorted_entries
