"""AuthenticationEvent ORM model.

One row per RADIUS authentication outcome. Only safe, non-secret fields
are persisted. Passwords and shared secrets are never stored.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuthenticationEvent(Base):
    __tablename__ = "authentication_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Stable identity for a single log line; used for idempotent ingestion.
    event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    username: Mapped[str] = mapped_column(String(255), index=True)
    result: Mapped[str] = mapped_column(String(16), index=True)  # accept | reject
    nas_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nas_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calling_station_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    called_station_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="freeradius")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    __table_args__ = (
        Index("ix_events_timestamp_result", "timestamp", "result"),
        Index("ix_events_username_timestamp", "username", "timestamp"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"<AuthenticationEvent {self.result} {self.username!r} "
            f"@ {self.timestamp.isoformat()}>"
        )
