import time
import threading
from typing import Optional, Callable, List

from poketokenbar.tracker.manager import UsageManager
from poketokenbar.game.companion import CompanionEngine

class AutoTracker:
    """Background thread worker that automatically tracks AI token usage and updates Pokémon growth."""

    def __init__(self, callback: Optional[Callable[[List[str]], None]] = None):
        self.tracker = UsageManager()
        self.engine = CompanionEngine()
        self.callback = callback
        self.running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _run_loop(self):
        while self.running:
            settings = self.engine.state.get("settings", {})
            enabled = settings.get("auto_tracking_enabled", True)
            interval = float(settings.get("refresh_interval", 3.0))

            if enabled:
                try:
                    summary = self.tracker.get_summary()
                    events = self.engine.process_usage(summary["total_tokens"], summary.get("active_days"))
                    if events and self.callback:
                        self.callback(events)
                except Exception:
                    pass

            # Sleep in 0.5s chunks so stop() is responsive
            slept = 0.0
            while slept < interval and self.running:
                time.sleep(0.5)
                slept += 0.5
