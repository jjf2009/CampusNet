"""Pydantic response models. Request/response contracts only — never
include password or secret fields here.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Result = Literal["accept", "reject"]
IngestionState = Literal["waiting", "ready", "degraded"]
RadiusState = Literal["active", "inactive", "failed", "unknown"]


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    timestamp: datetime
    username: str
    result: Result
    nas_ip: str | None = None
    nas_port: int | None = None
    calling_station_id: str | None = None
    called_station_id: str | None = None
    auth_method: str | None = None
    source: str


class EventPage(BaseModel):
    items: list[EventOut]
    total: int
    limit: int
    offset: int


class StatsOut(BaseModel):
    total_attempts: int
    accepted_attempts: int
    rejected_attempts: int
    acceptance_rate: float
    window_hours: int
    window_total: int
    window_accepted: int
    window_rejected: int


class RadiusStatus(BaseModel):
    status: RadiusState
    service: str


class HealthOut(BaseModel):
    status: str
    database: str
    ingestion: IngestionState


class SystemOverview(BaseModel):
    api: str
    database: str
    radius: RadiusStatus
    ingestion: IngestionState
    event_total: int
    latest_event_time: datetime | None = None


class UserActivity(BaseModel):
    username: str
    attempts: int
    accepted: int
    rejected: int
    last_seen: datetime | None = None
