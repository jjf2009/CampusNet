import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SAFE_FIELDS = {"timestamp", "username", "result", "nas_ip", "nas_port", "calling_station_id", "called_station_id", "auth_method", "event_id", "source"}


def _timestamp(value: Any) -> datetime:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc)
    if not isinstance(value, str):
        raise ValueError("timestamp is required")
    text = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def parse_event_line(line: str) -> dict[str, Any] | None:
    try:
        raw = json.loads(line)
        if not isinstance(raw, dict):
            return None
        result = str(raw.get("result", "")).strip().lower()
        result = {"access-accept": "accept", "access-reject": "reject"}.get(result, result)
        username = str(raw.get("username", "")).strip()
        if result not in {"accept", "reject"} or not username:
            return None
        timestamp = _timestamp(raw.get("timestamp"))
        safe = {key: raw.get(key) for key in SAFE_FIELDS}
        safe.update(timestamp=timestamp, username=username, result=result)
        safe["event_id"] = str(raw.get("event_id") or hashlib.sha256(line.strip().encode()).hexdigest())
        safe["source"] = str(raw.get("source") or "freeradius")
        if safe.get("nas_port") in (None, ""):
            safe["nas_port"] = None
        else:
            safe["nas_port"] = int(safe["nas_port"])
        return safe
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


class EventTailer:
    def __init__(self, path: Path):
        self.path = path
        self.cursor_path = path.with_suffix(path.suffix + ".cursor")
        try:
            self.offset = int(self.cursor_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.offset = 0
        self.last_error: str | None = None

    def read_new(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            size = self.path.stat().st_size
            if size < self.offset:
                self.offset = 0
            with self.path.open("r", encoding="utf-8") as stream:
                stream.seek(self.offset)
                content = stream.read()
                if content.endswith("\n"):
                    complete = content
                elif "\n" in content:
                    complete = content.rsplit("\n", 1)[0] + "\n"
                else:
                    complete = ""
                lines = complete.splitlines()
                self.offset += len(complete.encode("utf-8"))
                self.cursor_path.parent.mkdir(parents=True, exist_ok=True)
                self.cursor_path.write_text(str(self.offset), encoding="utf-8")
            self.last_error = None
            return [event for line in lines if (event := parse_event_line(line))]
        except OSError as exc:
            self.last_error = str(exc)
            return []
