"""Test fixtures. Env is set BEFORE importing the app so settings pick up
isolated temp paths instead of the real project database / RADIUS log.
"""

from __future__ import annotations

import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="campusnet-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["RADIUS_EVENT_LOG"] = f"{_TMP}/events.jsonl"
os.environ["POLL_INTERVAL_SECONDS"] = "0.2"
os.environ["FRONTEND_ORIGIN"] = "http://127.0.0.1:3000"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import AuthenticationEvent  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seed(db):
    def _seed(**overrides):
        from datetime import datetime, timezone

        defaults = dict(
            event_id=overrides.get("event_id", "evt-1"),
            timestamp=overrides.get("timestamp", datetime.now(timezone.utc)),
            username=overrides.get("username", "student01@gec.edu.in"),
            result=overrides.get("result", "accept"),
            source="freeradius",
        )
        defaults.update(
            {k: v for k, v in overrides.items() if k in defaults or k in {
                "nas_ip", "nas_port", "calling_station_id",
                "called_station_id", "auth_method",
            }}
        )
        event = AuthenticationEvent(**defaults)
        db.add(event)
        db.commit()
        return event

    return _seed


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
