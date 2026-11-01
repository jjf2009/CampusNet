from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..models import AuthenticationEvent
from .events import EventTailer


def ingest(tailer: EventTailer, db: Session) -> int:
    count = 0
    for payload in tailer.read_new():
        if db.query(AuthenticationEvent).filter_by(event_id=payload["event_id"]).first():
            continue
        db.add(AuthenticationEvent(**payload))
        try:
            db.commit()
            count += 1
        except IntegrityError:
            db.rollback()
    return count

