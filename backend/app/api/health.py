"""Health endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import HealthOut
from ..workers import IngestionWorker
from .deps import get_worker

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health(
    db: Session = Depends(get_db),
    worker: IngestionWorker = Depends(get_worker),
) -> HealthOut:
    try:
        db.execute(text("SELECT 1"))
        database = "healthy"
    except Exception:  # noqa: BLE001
        database = "unhealthy"
    # Backend health reflects the API + DB only; RADIUS health is reported
    # separately and never inferred from API health.
    status = "ok" if database == "healthy" else "degraded"
    return HealthOut(status=status, database=database, ingestion=worker.state)
