import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class UsageEntry:
    id: str
    date: datetime.datetime
    local_day: str  # YYYY-MM-DD
    model: str
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens + self.cache_write_tokens + self.cache_read_tokens

@dataclass
class DailyUsage:
    date: str  # YYYY-MM-DD
    input_tokens: int = 0
    output_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0

@dataclass
class ProviderSnapshot:
    provider_id: str
    display_name: str
    today_tokens: int
    week_tokens: int
    month_tokens: int
    total_tokens: int
    fetched_at: datetime.datetime
