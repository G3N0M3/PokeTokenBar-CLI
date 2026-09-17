import datetime
import calendar
import threading
import time
from typing import Dict, List, Optional
from poketokenbar.tracker.base import UsageEntry, DailyUsage, ProviderSnapshot
from poketokenbar.tracker.antigravity import AntigravityUsageReader
from poketokenbar.tracker.gemini import GeminiUsageReader
from poketokenbar.tracker.claude import ClaudeUsageReader


def get_billing_cycle_start(now: datetime.datetime, billing_cycle_day: int = 1) -> datetime.datetime:
    """Calculates the start datetime of the monthly billing cycle for a given anchor day (1-31)."""
    billing_cycle_day = max(1, min(31, int(billing_cycle_day)))
    if billing_cycle_day == 1:
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    max_days_current = calendar.monthrange(now.year, now.month)[1]
    effective_day_current = min(billing_cycle_day, max_days_current)

    if now.day >= effective_day_current:
        return now.replace(day=effective_day_current, hour=0, minute=0, second=0, microsecond=0)
    else:
        prev_year = now.year if now.month > 1 else now.year - 1
        prev_month = now.month - 1 if now.month > 1 else 12
        max_days_prev = calendar.monthrange(prev_year, prev_month)[1]
        effective_day_prev = min(billing_cycle_day, max_days_prev)
        return now.replace(year=prev_year, month=prev_month, day=effective_day_prev, hour=0, minute=0, second=0, microsecond=0)


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

    def _compute_summary(
        self,
        entries: List[UsageEntry],
        billing_cycle_day: Optional[int] = None,
        baseline_total: Optional[int] = None
    ) -> Dict:
        from poketokenbar.game.storage import StorageManager
        try:
            state = StorageManager.load_state()
        except Exception:
            state = {}

        if billing_cycle_day is None:
            billing_cycle_day = state.get("billing_cycle_day", 1)
        if baseline_total is None:
            baseline_total = state.get("baseline_total_tokens", 0)

        now = datetime.datetime.now().astimezone()
        today_str = now.strftime("%Y-%m-%d")

        # 7-day start (beginning of 6 days ago at 00:00:00)
        week_start_dt = (now - datetime.timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        cycle_start_dt = get_billing_cycle_start(now, billing_cycle_day)

        today_tokens = 0
        week_tokens = 0
        month_tokens = 0
        raw_total_tokens = 0

        # Burn rate calculation (last 5 minutes)
        five_min_ago = now - datetime.timedelta(minutes=5)
        five_min_tokens = 0

        antigravity_today = 0
        gemini_today = 0
        claude_today = 0

        for entry in entries:
            t = entry.total_tokens
            raw_total_tokens += t

            if entry.local_day == today_str:
                today_tokens += t
                if entry.id.startswith("antigravity|"):
                    antigravity_today += t
                elif entry.id.startswith("gemini|"):
                    gemini_today += t
                elif entry.id.startswith("claude|"):
                    claude_today += t

            e_dt = entry.date
            if e_dt.tzinfo is None and now.tzinfo is not None:
                e_dt = e_dt.replace(tzinfo=now.tzinfo)
            elif e_dt.tzinfo is not None and now.tzinfo is None:
                e_dt = e_dt.replace(tzinfo=None)

            if e_dt >= week_start_dt:
                week_tokens += t

            if e_dt >= cycle_start_dt:
                month_tokens += t

            if e_dt >= five_min_ago:
                five_min_tokens += t

        tokens_per_min = five_min_tokens / 5.0
        active_days = sorted(list(set(e.local_day for e in entries)))
        displayed_total = max(0, raw_total_tokens - baseline_total)
        baseline_date = state.get("baseline_date") if baseline_total > 0 else None
        earliest_date = active_days[0] if active_days else today_str

        return {
            "today_tokens": today_tokens,
            "week_tokens": week_tokens,
            "month_tokens": month_tokens,
            "total_tokens": displayed_total,
            "raw_total_tokens": raw_total_tokens,
            "baseline_total_tokens": baseline_total,
            "baseline_date": baseline_date,
            "earliest_date": earliest_date,
            "billing_cycle_day": billing_cycle_day,
            "billing_cycle_start": cycle_start_dt.strftime("%Y-%m-%d"),
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

    def get_summary(
        self,
        force: bool = False,
        billing_cycle_day: Optional[int] = None,
        baseline_total: Optional[int] = None
    ) -> Dict:
        if force or billing_cycle_day is not None or baseline_total is not None:
            entries = self._fetch_all_entries_sync()
            summary = self._compute_summary(
                entries,
                billing_cycle_day=billing_cycle_day,
                baseline_total=baseline_total
            )
            with self._lock:
                self._cached_summary = summary
            return summary
            
        with self._lock:
            return self._cached_summary
