"""Application configuration loaded from environment / .env.

All values have safe localhost-only defaults so the API never binds or
talks to anything beyond the local machine unless explicitly configured.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Persistence
    database_url: str = "sqlite:///./campusnet.db"

    # FreeRADIUS event integration
    # Dev default is a project-local fixture path. For the live integration
    # point this at the host log, e.g. /var/log/campusnet/radius-events.jsonl
    radius_event_log: Path = Path("./data/radius-events.jsonl")
    radius_service_name: str = "radiusd"

    # Ingestion worker
    poll_interval_seconds: float = 2.0

    # CORS – restricted to the local frontend origin in development.
    frontend_origin: str = "http://127.0.0.1:3000"

    # Stats defaults
    default_window_hours: int = 24

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
