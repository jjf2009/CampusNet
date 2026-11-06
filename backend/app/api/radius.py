"""RADIUS service status endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from ..config import settings
from ..schemas import RadiusStatus
from ..services.radius import radius_status

router = APIRouter(tags=["radius"])


@router.get("/radius/status", response_model=RadiusStatus)
def status() -> RadiusStatus:
    return RadiusStatus(**radius_status(settings.radius_service_name))
