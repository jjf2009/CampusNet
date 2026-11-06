"""Tailer tests: cursor durability, partial lines, truncation, rotation."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.tailer import EventTailer


def _line(event_id: str, result: str = "Access-Accept") -> str:
    return json.dumps(
        {
            "event_id": event_id,
            "timestamp": "2026-11-06T12:00:00Z",
            "username": "student01@gec.edu.in",
            "result": result,
        }
    )


def test_missing_log_returns_empty(tmp_path: Path):
    tailer = EventTailer(tmp_path / "missing.jsonl")
    assert tailer.read_new() == []
    assert tailer.last_error is None


def test_reads_only_complete_lines(tmp_path: Path):
    log = tmp_path / "events.jsonl"
    log.write_text(_line("a") + "\n" + _line("b"))  # 'b' has no trailing newline
    tailer = EventTailer(log)
    first = tailer.read_new()
    assert [e["event_id"] for e in first] == ["a"]  # partial 'b' withheld

    # Complete the partial line; next read picks it up.
    with log.open("a") as fh:
        fh.write("\n")
    assert [e["event_id"] for e in tailer.read_new()] == ["b"]


def test_cursor_persists_across_instances(tmp_path: Path):
    log = tmp_path / "events.jsonl"
    log.write_text(_line("a") + "\n")
    assert len(EventTailer(log).read_new()) == 1

    with log.open("a") as fh:
        fh.write(_line("b") + "\n")
    # A fresh tailer reloads the cursor and only sees the new line.
    fresh = EventTailer(log)
    assert [e["event_id"] for e in fresh.read_new()] == ["b"]


def test_truncation_resets_offset(tmp_path: Path):
    log = tmp_path / "events.jsonl"
    log.write_text(_line("a") + "\n" + _line("b") + "\n")
    tailer = EventTailer(log)
    assert len(tailer.read_new()) == 2

    # Rotation-in-place: file shrinks below the saved offset.
    log.write_text(_line("c") + "\n")
    assert [e["event_id"] for e in tailer.read_new()] == ["c"]


def test_malformed_lines_skipped(tmp_path: Path):
    log = tmp_path / "events.jsonl"
    log.write_text("garbage\n" + _line("a") + "\n" + "{bad\n")
    tailer = EventTailer(log)
    assert [e["event_id"] for e in tailer.read_new()] == ["a"]
