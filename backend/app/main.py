import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, SessionLocal, engine, get_db
from .models import AuthenticationEvent
from .schemas import EventOut, EventPage, HealthOut, StatsOut
from .services.events import EventTailer
from .services.ingestion import ingest
from .services.radius import radius_status

tailer = EventTailer(settings.radius_event_log)
worker_task: asyncio.Task | None = None
ingestion_state = "waiting"


async def ingestion_loop() -> None:
    global ingestion_state
    while True:
        try:
            with SessionLocal() as db:
                ingest(tailer, db)
            ingestion_state = "degraded" if tailer.last_error else ("ready" if settings.radius_event_log.exists() else "waiting")
        except Exception:
            ingestion_state = "degraded"
        await asyncio.sleep(settings.poll_interval_seconds)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global worker_task
    Base.metadata.create_all(engine)
    worker_task = asyncio.create_task(ingestion_loop())
    yield
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="CampusNet API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_methods=["GET"], allow_headers=["*"])


@app.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        database = "healthy"
    except Exception:
        database = "unhealthy"
    return {"status": "ok" if database == "healthy" else "degraded", "database": database, "ingestion": ingestion_state}


@app.get("/api/events", response_model=EventPage)
def events(db: Session = Depends(get_db), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), result: str | None = Query(None, pattern="^(accept|reject)$"), username: str | None = None, since: datetime | None = None, until: datetime | None = None):
    query = select(AuthenticationEvent)
    if result: query = query.where(AuthenticationEvent.result == result)
    if username: query = query.where(AuthenticationEvent.username.ilike(f"%{username.strip()}%"))
    if since: query = query.where(AuthenticationEvent.timestamp >= since)
    if until: query = query.where(AuthenticationEvent.timestamp <= until)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(AuthenticationEvent.timestamp.desc()).offset(offset).limit(limit)).all()
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@app.get("/api/events/{event_id}", response_model=EventOut)
def event(event_id: str, db: Session = Depends(get_db)):
    item = db.scalar(select(AuthenticationEvent).where(AuthenticationEvent.event_id == event_id))
    if not item: raise HTTPException(status_code=404, detail="Event not found")
    return item


@app.get("/api/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db), window_hours: int = Query(24, ge=1, le=720)):
    total = db.scalar(select(func.count()).select_from(AuthenticationEvent)) or 0
    accepted = db.scalar(select(func.count()).where(AuthenticationEvent.result == "accept")) or 0
    rejected = db.scalar(select(func.count()).where(AuthenticationEvent.result == "reject")) or 0
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    window_total = db.scalar(select(func.count()).where(AuthenticationEvent.timestamp >= cutoff)) or 0
    return {"total_attempts": total, "accepted_attempts": accepted, "rejected_attempts": rejected, "acceptance_rate": round(accepted / total * 100, 2) if total else 0, "window_hours": window_hours, "window_total": window_total}


@app.get("/api/radius/status")
def radius():
    return radius_status(settings.radius_service_name)


@app.get("/api/system/overview")
def overview(db: Session = Depends(get_db)):
    latest = db.scalar(select(AuthenticationEvent).order_by(AuthenticationEvent.timestamp.desc()).limit(1))
    return {"api": "healthy", "radius": radius_status(settings.radius_service_name), "ingestion": ingestion_state, "event_total": db.scalar(select(func.count()).select_from(AuthenticationEvent)) or 0, "latest_event_time": latest.timestamp if latest else None}


@app.get("/api/users")
def users(db: Session = Depends(get_db)):
    rows = db.execute(select(AuthenticationEvent.username, func.count(AuthenticationEvent.id).label("attempts"), func.max(AuthenticationEvent.timestamp).label("last_seen")).group_by(AuthenticationEvent.username).order_by(func.max(AuthenticationEvent.timestamp).desc())).all()
    return [{"username": row.username, "attempts": row.attempts, "last_seen": row.last_seen} for row in rows]

