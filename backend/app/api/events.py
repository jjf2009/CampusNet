"""Authentication event endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuthenticationEvent
from ..schemas import EventOut, EventPage

router = APIRouter(tags=["events"])


@router.get("/events", response_model=EventPage)
def list_events(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    result: str | None = Query(None, pattern="^(accept|reject)$"),
    username: str | None = Query(None, max_length=255),
    since: datetime | None = None,
    until: datetime | None = None,
) -> EventPage:
    query = select(AuthenticationEvent)
    if result:
        query = query.where(AuthenticationEvent.result == result)
    if username:
        query = query.where(AuthenticationEvent.username.ilike(f"%{username.strip()}%"))
    if since:
        query = query.where(AuthenticationEvent.timestamp >= since)
    if until:
        query = query.where(AuthenticationEvent.timestamp <= until)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(
        query.order_by(AuthenticationEvent.timestamp.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return EventPage(items=list(items), total=total, limit=limit, offset=offset)


@router.get("/events/{event_id}", response_model=EventOut)
def get_event(event_id: str, db: Session = Depends(get_db)) -> AuthenticationEvent:
    item = db.scalar(
        select(AuthenticationEvent).where(AuthenticationEvent.event_id == event_id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return item
