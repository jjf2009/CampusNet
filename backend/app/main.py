"""CampusNet FastAPI application entrypoint.

Wires the database, the background ingestion worker and the API routers.
Bound to localhost by convention (see run command in README); CORS is
restricted to the configured frontend origin.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .config import settings
from .database import SessionLocal, init_db
from .workers import IngestionWorker

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    worker = IngestionWorker(
        log_path=settings.radius_event_log,
        session_factory=SessionLocal,
        poll_interval_seconds=settings.poll_interval_seconds,
        cursor_path=settings.ingestion_cursor_path,
    )
    app.state.worker = worker
    worker.start()
    try:
        yield
    finally:
        await worker.stop()


def create_app() -> FastAPI:
    app = FastAPI(title="CampusNet API", version="0.2.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    return app


app = create_app()
