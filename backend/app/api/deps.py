"""Shared API dependencies."""

from __future__ import annotations

from fastapi import Request

from ..workers import IngestionWorker


def get_worker(request: Request) -> IngestionWorker:
    """Return the ingestion worker attached to the app at startup."""
    return request.app.state.worker
