"""Combined system overview endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import AuthenticationEvent
from ..schemas import RadiusStatus, SystemOverview
from ..services.radius import radius_status
from ..workers import IngestionWorker
from .deps import get_worker

router = APIRouter(tags=["system"])


@router.get("/system/overview", response_model=SystemOverview)
def overview(
    db: Session = Depends(get_db),
    worker: IngestionWorker = Depends(get_worker),
) -> SystemOverview:
    try:
        db.execute(text("SELECT 1"))
        database = "healthy"
    except Exception:  # noqa: BLE001
        database = "unhealthy"

    total = db.scalar(select(func.count()).select_from(AuthenticationEvent)) or 0
    latest = db.scalar(
        select(AuthenticationEvent.timestamp)
        .order_by(AuthenticationEvent.timestamp.desc())
        .limit(1)
    )
    return SystemOverview(
        api="healthy",
        database=database,
        radius=RadiusStatus(**radius_status(settings.radius_service_name)),
        ingestion=worker.state,
        event_total=total,
        latest_event_time=latest,
    )
