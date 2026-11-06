"""Distinct-user activity endpoint.

Aggregates usernames observed in events. This is NOT a student directory;
it only reflects accounts that have appeared in authentication events.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuthenticationEvent
from ..schemas import UserActivity

router = APIRouter(tags=["users"])


@router.get("/users", response_model=list[UserActivity])
def users(db: Session = Depends(get_db)) -> list[UserActivity]:
    accepted = func.sum(case((AuthenticationEvent.result == "accept", 1), else_=0))
    rejected = func.sum(case((AuthenticationEvent.result == "reject", 1), else_=0))
    rows = db.execute(
        select(
            AuthenticationEvent.username,
            func.count(AuthenticationEvent.id).label("attempts"),
            accepted.label("accepted"),
            rejected.label("rejected"),
            func.max(AuthenticationEvent.timestamp).label("last_seen"),
        )
        .group_by(AuthenticationEvent.username)
        .order_by(func.max(AuthenticationEvent.timestamp).desc())
    ).all()
    return [
        UserActivity(
            username=row.username,
            attempts=row.attempts,
            accepted=int(row.accepted or 0),
            rejected=int(row.rejected or 0),
            last_seen=row.last_seen,
        )
        for row in rows
    ]
