from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

# Optional dependency: watchdog (only required for --watch)
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class DebouncedRunner:
    """
    Coalesce rapid filesystem events into fewer rebuilds.

    Many editors trigger multiple events for one save; this keeps rebuilds sane.
    """

    def __init__(self, min_interval_s: float = 0.25) -> None:
        self.min_interval_s = min_interval_s
        self._last_run = 0.0

    def should_run(self) -> bool:
        now = time.time()
        if now - self._last_run < self.min_interval_s:
            return False
        self._last_run = now
        return True


class WatchHandler(FileSystemEventHandler):
    def __init__(self, on_change: Callable[[], None], debounce: DebouncedRunner) -> None:
        super().__init__()
        self.on_change = on_change
        self.debounce = debounce

    def on_modified(self, event):
        if event.is_directory:
            return
        p = str(event.src_path).lower()
        if not p.endswith(".md"):
            return
        if self.debounce.should_run():
            self.on_change()

    # Some editors trigger "created" rather than "modified"
    def on_created(self, event):
        self.on_modified(event)


def watch_md_dir(watch_dir: Path, on_change: Callable[[], None]) -> None:
    """
    Watch a directory for changes to *.md files and call `on_change()`.

    Raises RuntimeError if watchdog is not installed.
    """
    if not WATCHDOG_AVAILABLE:
        raise RuntimeError("watchdog is not installed. Install it with `pip install watchdog`.")

    print(f"[watch] Watching {watch_dir} for .md changes...")
    debounce = DebouncedRunner()
    handler = WatchHandler(on_change, debounce)

    observer = Observer()
    observer.schedule(handler, str(watch_dir), recursive=False)
    observer.start()

    try:
        while True:
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

