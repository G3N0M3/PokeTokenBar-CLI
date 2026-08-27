import datetime
import threading
import time
from typing import Dict, List, Optional
from poketokenbar.tracker.base import UsageEntry, DailyUsage, ProviderSnapshot
from poketokenbar.tracker.antigravity import AntigravityUsageReader
from poketokenbar.tracker.gemini import GeminiUsageReader
from poketokenbar.tracker.claude import ClaudeUsageReader

class UsageManager:
    """Aggregates usage entries from local log sources and computes period metrics."""

    def __init__(self):
        self.antigravity_reader = AntigravityUsageReader()
        self.gemini_reader = GeminiUsageReader()
        self.claude_reader = ClaudeUsageReader()
        
        self._lock = threading.Lock()
        # Initial synchronous fetch so TUI has data immediately
        self._cached_summary = self._compute_summary(self._fetch_all_entries_sync())
        
        self._stop_event = threading.Event()
        self._bg_thread = threading.Thread(target=self._background_fetch_loop, daemon=True)
        self._bg_thread.start()

    def stop(self):
        self._stop_event.set()

    def _background_fetch_loop(self):
        while not self._stop_event.is_set():
            time.sleep(2.0)
            try:
                entries = self._fetch_all_entries_sync()
                summary = self._compute_summary(entries)
                with self._lock:
                    self._cached_summary = summary
            except Exception:
                pass

    def _fetch_all_entries_sync(self) -> List[UsageEntry]:
        all_entries: List[UsageEntry] = []
        all_entries.extend(self.antigravity_reader.get_entries())
        all_entries.extend(self.gemini_reader.get_entries())
        all_entries.extend(self.claude_reader.get_entries())

        # Deduplicate across all readers by ID
        seen = {}
        for entry in all_entries:
            seen[entry.id] = entry

        return sorted(seen.values(), key=lambda e: e.date)

    def _compute_summary(self, entries: List[UsageEntry]) -> Dict:
        now = datetime.datetime.now().astimezone()
        today_str = now.strftime("%Y-%m-%d")

        # 7-day start (beginning of 6 days ago)
        week_start_dt = (now - datetime.timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        month_str = now.strftime("%Y-%m")

        today_tokens = 0
        week_tokens = 0
        month_tokens = 0
        total_tokens = 0

        # Burn rate calculation (last 5 minutes)
        five_min_ago = now - datetime.timedelta(minutes=5)
        five_min_tokens = 0

        antigravity_today = 0
        gemini_today = 0
        claude_today = 0

        for entry in entries:
            t = entry.total_tokens
            total_tokens += t

            if entry.local_day == today_str:
                today_tokens += t
                if entry.id.startswith("antigravity|"):
                    antigravity_today += t
                elif entry.id.startswith("gemini|"):
                    gemini_today += t
                elif entry.id.startswith("claude|"):
                    claude_today += t

            if entry.date >= week_start_dt:
                week_tokens += t

            if entry.local_day.startswith(month_str):
                month_tokens += t

            if entry.date >= five_min_ago:
                five_min_tokens += t

        tokens_per_min = five_min_tokens / 5.0
        active_days = sorted(list(set(e.local_day for e in entries)))

        return {
            "today_tokens": today_tokens,
            "week_tokens": week_tokens,
            "month_tokens": month_tokens,
            "total_tokens": total_tokens,
            "burn_rate_tpm": tokens_per_min,
            "antigravity_today": antigravity_today,
            "gemini_today": gemini_today,
            "claude_today": claude_today,
            "total_entries": len(entries),
            "active_days": active_days,
            "last_updated": now
        }

    def fetch_all_entries(self) -> List[UsageEntry]:
        return self._fetch_all_entries_sync()

    def get_summary(self, force: bool = False) -> Dict:
        if force:
            entries = self._fetch_all_entries_sync()
            summary = self._compute_summary(entries)
            with self._lock:
                self._cached_summary = summary
            return summary
            
        with self._lock:
            return self._cached_summary
