"""Persist parsed events idempotently."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import AuthenticationEvent
from .tailer import EventTailer


def ingest(tailer: EventTailer, db: Session) -> int:
    """Read new lines from the tailer and insert unseen events.

    Returns the number of newly persisted events. Duplicate ``event_id``
    values are skipped so replaying the log never double-counts.
    """
    inserted = 0
    for payload in tailer.read_new():
        exists = db.scalar(
            select(AuthenticationEvent.id).where(
                AuthenticationEvent.event_id == payload["event_id"]
            )
        )
        if exists is not None:
            continue
        db.add(AuthenticationEvent(**payload))
        try:
            db.commit()
            inserted += 1
        except IntegrityError:
            # Lost a race on the unique event_id; safe to ignore.
            db.rollback()
    return inserted
