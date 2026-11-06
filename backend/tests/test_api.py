"""API endpoint tests via TestClient."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def test_health(client):
    body = client.get("/health").json()
    assert body["database"] == "healthy"
    assert body["ingestion"] in {"waiting", "ready", "degraded"}


def test_events_empty(client):
    body = client.get("/api/events").json()
    assert body == {"items": [], "total": 0, "limit": 50, "offset": 0}


def test_events_listing_and_filters(client, seed):
    now = datetime.now(timezone.utc)
    seed(event_id="a", result="accept", username="alice@gec.edu.in", timestamp=now)
    seed(
        event_id="b",
        result="reject",
        username="bob@gec.edu.in",
        timestamp=now - timedelta(minutes=5),
    )

    all_events = client.get("/api/events").json()
    assert all_events["total"] == 2
    # Newest first.
    assert all_events["items"][0]["event_id"] == "a"

    accepted = client.get("/api/events?result=accept").json()
    assert accepted["total"] == 1 and accepted["items"][0]["result"] == "accept"

    by_user = client.get("/api/events?username=bob").json()
    assert by_user["total"] == 1 and by_user["items"][0]["username"] == "bob@gec.edu.in"


def test_events_pagination(client, seed):
    for i in range(5):
        seed(event_id=f"e{i}", timestamp=datetime.now(timezone.utc))
    page = client.get("/api/events?limit=2&offset=0").json()
    assert len(page["items"]) == 2 and page["total"] == 5


def test_get_single_event(client, seed):
    seed(event_id="xyz")
    assert client.get("/api/events/xyz").json()["event_id"] == "xyz"
    assert client.get("/api/events/nope").status_code == 404


def test_stats_no_division_by_zero(client):
    body = client.get("/api/stats").json()
    assert body["total_attempts"] == 0
    assert body["acceptance_rate"] == 0.0


def test_stats_counts(client, seed):
    now = datetime.now(timezone.utc)
    seed(event_id="a", result="accept", timestamp=now)
    seed(event_id="b", result="accept", timestamp=now)
    seed(event_id="c", result="reject", timestamp=now)
    body = client.get("/api/stats").json()
    assert body["total_attempts"] == 3
    assert body["accepted_attempts"] == 2
    assert body["rejected_attempts"] == 1
    assert body["acceptance_rate"] == 66.67


def test_radius_status(client):
    body = client.get("/api/radius/status").json()
    assert body["status"] in {"active", "inactive", "failed", "unknown"}
    assert body["service"]


def test_system_overview(client, seed):
    seed(event_id="a")
    body = client.get("/api/system/overview").json()
    assert body["api"] == "healthy"
    assert body["event_total"] == 1
    assert body["latest_event_time"] is not None
    assert "status" in body["radius"]


def test_users_aggregate(client, seed):
    now = datetime.now(timezone.utc)
    seed(event_id="a", username="alice@gec.edu.in", result="accept", timestamp=now)
    seed(event_id="b", username="alice@gec.edu.in", result="reject", timestamp=now)
    body = client.get("/api/users").json()
    assert len(body) == 1
    assert body[0]["username"] == "alice@gec.edu.in"
    assert body[0]["attempts"] == 2
    assert body[0]["accepted"] == 1
    assert body[0]["rejected"] == 1


def test_cors_restricted(client):
    # Wildcard must never appear; only the configured origin is allowed.
    resp = client.get("/health", headers={"Origin": "http://evil.example"})
    assert resp.headers.get("access-control-allow-origin") != "*"
