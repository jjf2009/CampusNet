"""Async ingestion worker.

Polls the RADIUS event log on a fixed interval and persists new events.
The blocking file read + SQLite write run in a worker thread via
``asyncio.to_thread`` so FastAPI's event loop is never blocked.

Exposed ``state`` is one of:
    waiting  – log file not present yet (nothing to ingest)
    ready    – log present and last poll succeeded
    degraded – last poll raised, or the tailer recorded an error
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Callable

from sqlalchemy.orm import Session

from ..services.ingestion import ingest
from ..services.tailer import EventTailer

logger = logging.getLogger("campusnet.ingestion")

IngestionState = str  # "waiting" | "ready" | "degraded"


class IngestionWorker:
    def __init__(
        self,
        log_path: Path,
        session_factory: Callable[[], Session],
        poll_interval_seconds: float,
    ) -> None:
        self.tailer = EventTailer(log_path)
        self._session_factory = session_factory
        self._interval = max(0.2, float(poll_interval_seconds))
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self.state: IngestionState = "waiting"
        self.last_ingested: int = 0

    def _poll_once(self) -> IngestionState:
        """Synchronous single poll; runs in a thread."""
        try:
            with self._session_factory() as db:
                self.last_ingested = ingest(self.tailer, db)
        except Exception:  # noqa: BLE001 - never let the worker die
            logger.exception("ingestion poll failed")
            return "degraded"
        if self.tailer.last_error:
            return "degraded"
        return "ready" if self.tailer.log_exists else "waiting"

    async def _run(self) -> None:
        logger.info("ingestion worker started (interval=%ss)", self._interval)
        while not self._stop.is_set():
            self.state = await asyncio.to_thread(self._poll_once)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self._interval)
            except asyncio.TimeoutError:
                pass
        logger.info("ingestion worker stopped")

    def start(self) -> None:
        if self._task is None:
            self._stop.clear()
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            await self._task
            self._task = None
