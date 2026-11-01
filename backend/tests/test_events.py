from datetime import datetime, timezone
from app.services.events import parse_event_line


def test_parser_keeps_safe_fields_only():
    event = parse_event_line('{"timestamp":"2026-11-01T10:00:00Z","username":"student01@gec.edu.in","result":"accept","User-Password":"secret","secret":"testing123"}')
    assert event["username"] == "student01@gec.edu.in"
    assert "User-Password" not in event and "secret" not in event
    assert event["timestamp"] == datetime(2026, 11, 1, 10, tzinfo=timezone.utc)


def test_parser_rejects_malformed_or_unsafe_records():
    assert parse_event_line("not json") is None
    assert parse_event_line('{"username":"x","result":"maybe","timestamp":"2026-11-01T10:00:00Z"}') is None


def test_event_id_is_stable_when_missing():
    line = '{"timestamp":"2026-11-01T10:00:00Z","username":"x","result":"reject"}'
    assert parse_event_line(line)["event_id"] == parse_event_line(line)["event_id"]

