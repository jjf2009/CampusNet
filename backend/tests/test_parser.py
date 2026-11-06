"""Parser unit tests: formats, sanitization, malformed handling."""

from __future__ import annotations

import json
from datetime import timezone

import pytest

from app.services.parser import parse_event_line, parse_timestamp


def test_parse_accept_line():
    line = json.dumps(
        {
            "timestamp": "2026-11-06T12:00:00Z",
            "username": "student01@gec.edu.in",
            "result": "Access-Accept",
            "nas_ip": "127.0.0.1",
            "nas_port": "0",
            "calling_station_id": "AA-BB-CC-DD-EE-FF",
            "source": "freeradius",
        }
    )
    payload = parse_event_line(line)
    assert payload is not None
    assert payload["result"] == "accept"
    assert payload["username"] == "student01@gec.edu.in"
    assert payload["nas_port"] == 0
    assert payload["timestamp"].tzinfo is not None


def test_access_reject_normalized():
    line = json.dumps(
        {"timestamp": "2026-11-06T12:00:00Z", "username": "x", "result": "Access-Reject"}
    )
    assert parse_event_line(line)["result"] == "reject"


@pytest.mark.parametrize(
    "value",
    [
        "2026-11-06T12:00:00Z",
        "2026-11-06T12:00:00+00:00",
        "Thu Nov  6 12:00:00 2026",      # ctime (%t), double space
        "Thu Nov 06 12:00:00 2026",      # ctime single-digit padded
        "2026-11-06-12.00.00.000000",    # %T dotted with micros
        "2026-11-06-12.00.00",           # %T dotted no micros
        "Nov 06 2026 12:00:00",
        1762430400,                       # epoch int
        "1762430400",                     # epoch string
    ],
)
def test_timestamp_formats(value):
    dt = parse_timestamp(value)
    assert dt.tzinfo == timezone.utc


def test_malformed_json_returns_none():
    assert parse_event_line("{not json") is None
    assert parse_event_line("") is None
    assert parse_event_line("   ") is None
    assert parse_event_line("[1,2,3]") is None  # not an object


def test_missing_required_fields_returns_none():
    assert parse_event_line(json.dumps({"result": "Access-Accept"})) is None  # no user
    assert parse_event_line(json.dumps({"username": "x"})) is None  # no result
    assert (
        parse_event_line(json.dumps({"username": "x", "result": "Access-Accept"}))
        is None
    )  # no timestamp


def test_unknown_result_returns_none():
    line = json.dumps(
        {"timestamp": "2026-11-06T12:00:00Z", "username": "x", "result": "Maybe"}
    )
    assert parse_event_line(line) is None


def test_bad_timestamp_returns_none():
    line = json.dumps(
        {"timestamp": "not-a-date", "username": "x", "result": "Access-Accept"}
    )
    assert parse_event_line(line) is None


def test_password_and_secret_fields_dropped():
    line = json.dumps(
        {
            "timestamp": "2026-11-06T12:00:00Z",
            "username": "x",
            "result": "Access-Accept",
            "User-Password": "hunter2",
            "secret": "testing123",
            "password": "hunter2",
        }
    )
    payload = parse_event_line(line)
    assert payload is not None
    assert "User-Password" not in payload
    assert "password" not in payload
    assert "secret" not in payload
    assert "hunter2" not in json.dumps(payload, default=str)


def test_event_id_hash_is_stable():
    line = json.dumps(
        {"timestamp": "2026-11-06T12:00:00Z", "username": "x", "result": "Access-Accept"}
    )
    assert parse_event_line(line)["event_id"] == parse_event_line(line)["event_id"]


def test_explicit_event_id_preferred():
    line = json.dumps(
        {
            "event_id": "abc-123",
            "timestamp": "2026-11-06T12:00:00Z",
            "username": "x",
            "result": "Access-Accept",
        }
    )
    assert parse_event_line(line)["event_id"] == "abc-123"
