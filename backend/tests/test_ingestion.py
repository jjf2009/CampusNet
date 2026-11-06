"""Ingestion tests: persistence and idempotent de-duplication."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select

from app.models import AuthenticationEvent
from app.services.ingestion import ingest
from app.services.tailer import EventTailer


def _write(log: Path, *event_ids: str) -> None:
    lines = [
        json.dumps(
            {
                "event_id": eid,
                "timestamp": "2026-11-06T12:00:00Z",
                "username": "student01@gec.edu.in",
                "result": "Access-Accept",
            }
        )
        for eid in event_ids
    ]
    with log.open("a") as fh:
        fh.write("\n".join(lines) + "\n")


def test_ingest_persists_new_events(tmp_path: Path, db):
    log = tmp_path / "events.jsonl"
    _write(log, "a", "b")
    inserted = ingest(EventTailer(log), db)
    assert inserted == 2
    assert db.scalar(select(func.count()).select_from(AuthenticationEvent)) == 2


def test_replay_does_not_duplicate(tmp_path: Path, db):
    log = tmp_path / "events.jsonl"
    _write(log, "a", "b")

    tailer = EventTailer(log)
    assert ingest(tailer, db) == 2

    # Simulate restart: brand-new tailer with a reset cursor re-reads the file.
    replay = EventTailer(log)
    replay.offset = 0
    assert ingest(replay, db) == 0  # all event_ids already present
    assert db.scalar(select(func.count()).select_from(AuthenticationEvent)) == 2
