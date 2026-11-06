"""Parse a single CampusNet RADIUS event log line into a safe payload.

The log is JSON-lines written by a FreeRADIUS ``linelog`` instance. Each
line is expected to look like::

    {"timestamp": "...", "username": "...", "result": "Access-Accept",
     "nas_ip": "...", "nas_port": "...", "calling_station_id": "...",
     "called_station_id": "...", "auth_method": "...", "source": "freeradius"}

FreeRADIUS timestamp expansions vary by version and configuration, so the
timestamp parser is deliberately tolerant: it accepts epoch seconds, ISO
8601, the ctime form produced by ``%t``, and the dotted form produced by
``%T``. Unparseable or incomplete records return ``None`` (treated as
malformed and skipped) rather than raising.

Only whitelisted, non-secret fields are ever emitted. Any ``User-Password``
or secret-looking key present in the raw line is dropped.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

# Fields we are willing to persist. Everything else in a raw line is dropped.
SAFE_FIELDS: frozenset[str] = frozenset(
    {
        "timestamp",
        "username",
        "result",
        "nas_ip",
        "nas_port",
        "calling_station_id",
        "called_station_id",
        "auth_method",
        "event_id",
        "source",
    }
)

_RESULT_ALIASES = {
    "access-accept": "accept",
    "accept": "accept",
    "access-reject": "reject",
    "reject": "reject",
}

# strptime patterns for the common non-ISO FreeRADIUS timestamp formats.
_TIME_PATTERNS = (
    "%a %b %d %H:%M:%S %Y",      # ctime  ->  "Thu Nov  6 12:00:00 2026"
    "%Y-%m-%d-%H.%M.%S.%f",      # %T dotted with micros -> 2026-11-06-12.00.00.000000
    "%Y-%m-%d-%H.%M.%S",         # %T dotted no micros
    "%b %d %Y %H:%M:%S",         # "Nov 06 2026 12:00:00"
    "%d %b %Y %H:%M:%S",         # "06 Nov 2026 12:00:00"
    "%Y-%m-%d %H:%M:%S",         # plain SQL-ish
)


def parse_timestamp(value: Any) -> datetime:
    """Return a timezone-aware UTC datetime, or raise ValueError.

    Naive inputs are assumed to already be local-ish wall clock and are
    treated as UTC to keep the demo deterministic; callers should prefer
    emitting explicit offsets.
    """
    if isinstance(value, bool):  # guard: bool is an int subclass
        raise ValueError("timestamp must not be a boolean")
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if not isinstance(value, str):
        raise ValueError("timestamp is required")

    text = value.strip()
    if not text:
        raise ValueError("empty timestamp")

    # Pure epoch string.
    if text.isdigit():
        return datetime.fromtimestamp(int(text), tz=timezone.utc)

    # ISO 8601 (handles trailing Z and explicit offsets).
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return _as_utc(parsed)
    except ValueError:
        pass

    # Collapse the double space ctime uses for single-digit days so a single
    # pattern matches both "Nov  6" and "Nov 06".
    collapsed = " ".join(text.split())
    for pattern in _TIME_PATTERNS:
        try:
            return _as_utc(datetime.strptime(collapsed, pattern))
        except ValueError:
            continue

    raise ValueError(f"unrecognized timestamp format: {value!r}")


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _clean_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clean_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def parse_event_line(line: str) -> dict[str, Any] | None:
    """Parse one JSONL line into a persistable payload, or None if invalid."""
    line = line.strip()
    if not line:
        return None
    try:
        raw = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None

    result = _RESULT_ALIASES.get(str(raw.get("result", "")).strip().lower())
    username = _clean_str(raw.get("username"))
    if result is None or username is None:
        return None

    try:
        timestamp = parse_timestamp(raw.get("timestamp"))
    except ValueError:
        return None

    payload: dict[str, Any] = {
        "timestamp": timestamp,
        "username": username,
        "result": result,
        "nas_ip": _clean_str(raw.get("nas_ip")),
        "nas_port": _clean_int(raw.get("nas_port")),
        "calling_station_id": _clean_str(raw.get("calling_station_id")),
        "called_station_id": _clean_str(raw.get("called_station_id")),
        "auth_method": _clean_str(raw.get("auth_method")),
        "source": _clean_str(raw.get("source")) or "freeradius",
    }

    # Stable id: prefer an explicit event_id, else hash the canonical line so
    # replaying the same log is idempotent.
    explicit = _clean_str(raw.get("event_id"))
    payload["event_id"] = explicit or hashlib.sha256(line.encode("utf-8")).hexdigest()
    return payload
