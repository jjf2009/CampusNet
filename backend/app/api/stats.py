"""Aggregate statistics endpoint."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuthenticationEvent
from ..schemas import StatsOut

router = APIRouter(tags=["stats"])


def _count(db: Session, *conditions) -> int:
    query = select(func.count()).select_from(AuthenticationEvent)
    for condition in conditions:
        query = query.where(condition)
    return db.scalar(query) or 0


@router.get("/stats", response_model=StatsOut)
def stats(
    db: Session = Depends(get_db),
    window_hours: int = Query(24, ge=1, le=720),
) -> StatsOut:
    total = _count(db)
    accepted = _count(db, AuthenticationEvent.result == "accept")
    rejected = _count(db, AuthenticationEvent.result == "reject")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    window_total = _count(db, AuthenticationEvent.timestamp >= cutoff)
    window_accepted = _count(
        db,
        AuthenticationEvent.timestamp >= cutoff,
        AuthenticationEvent.result == "accept",
    )
    window_rejected = _count(
        db,
        AuthenticationEvent.timestamp >= cutoff,
        AuthenticationEvent.result == "reject",
    )

    acceptance_rate = round(accepted / total * 100, 2) if total else 0.0
    return StatsOut(
        total_attempts=total,
        accepted_attempts=accepted,
        rejected_attempts=rejected,
        acceptance_rate=acceptance_rate,
        window_hours=window_hours,
        window_total=window_total,
        window_accepted=window_accepted,
        window_rejected=window_rejected,
    )
