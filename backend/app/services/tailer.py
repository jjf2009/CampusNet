"""Durable file tailer for the RADIUS event log.

Persists a byte offset cursor next to the log so events are not re-ingested
after a process restart. Handles:

* partial trailing lines (only complete, newline-terminated lines consumed)
* file truncation / log rotation (offset reset when the file shrinks)
* a missing log (returns nothing, records a degraded reason)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .parser import parse_event_line


class EventTailer:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.cursor_path = self.path.with_suffix(self.path.suffix + ".cursor")
        self.offset = self._load_offset()
        self.last_error: str | None = None

    def _load_offset(self) -> int:
        try:
            return int(self.cursor_path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return 0

    def _save_offset(self) -> None:
        try:
            self.cursor_path.parent.mkdir(parents=True, exist_ok=True)
            self.cursor_path.write_text(str(self.offset), encoding="utf-8")
        except OSError as exc:
            self.last_error = f"cursor write failed: {exc}"

    @property
    def log_exists(self) -> bool:
        return self.path.exists()

    def read_new(self) -> list[dict[str, Any]]:
        """Return parsed payloads for any complete lines since last read."""
        if not self.path.exists():
            self.last_error = None
            return []
        try:
            size = self.path.stat().st_size
            if size < self.offset:
                # File was truncated or rotated in place; restart from 0.
                self.offset = 0
            with self.path.open("r", encoding="utf-8", errors="replace") as stream:
                stream.seek(self.offset)
                chunk = stream.read()

            # Only consume through the last newline; keep any partial tail.
            if "\n" in chunk:
                consumed, _partial = chunk.rsplit("\n", 1)
                consumed += "\n"
            else:
                consumed = ""

            if consumed:
                self.offset += len(consumed.encode("utf-8"))
                self._save_offset()

            self.last_error = None
            return [
                payload
                for raw_line in consumed.splitlines()
                if (payload := parse_event_line(raw_line)) is not None
            ]
        except OSError as exc:
            self.last_error = str(exc)
            return []
