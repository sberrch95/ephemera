"""Tests for core/memory.py - the scoping and deduplication logic that
matters most for Ephemera's correctness."""

from sqlmodel import select

from ephemera.core.memory import (
    get_or_create_target,
    record_extracted_variables,
    record_request,
)
from ephemera.database.models import Endpoint, RequestLog, Target, TimelineEvent, Variable


def test_get_or_create_target_creates_new_target(session):
    target = get_or_create_target(session, "example.com")
    assert target.id is not None
    assert target.hostname == "example.com"

    events = session.exec(select(TimelineEvent)).all()
    assert len(events) == 1
    assert events[0].event_type == "TARGET_SEEN"


def test_get_or_create_target_returns_existing_target(session):
    first = get_or_create_target(session, "example.com")
    second = get_or_create_target(session, "example.com")
    assert first.id == second.id
    assert len(session.exec(select(Target)).all()) == 1


def test_get_or_create_target_only_logs_target_seen_once(session):
    for _ in range(3):
        get_or_create_target(session, "example.com")

    seen_events = session.exec(
        select(TimelineEvent).where(TimelineEvent.event_type == "TARGET_SEEN")
    ).all()
    assert len(seen_events) == 1


def test_different_hostnames_create_separate_targets(session):
    target_a = get_or_create_target(session, "example.com")
    target_b = get_or_create_target(session, "other.com")
    assert target_a.id != target_b.id
    assert len(session.exec(select(Target)).all()) == 2


def test_record_request_creates_endpoint(session):
    record_request(
        session, url="http://example.com/login", method="POST",
        status_code=200, response_bytes=100,
    )

    endpoints = session.exec(select(Endpoint)).all()
    assert len(endpoints) == 1
    assert endpoints[0].path == "/login"
    assert endpoints[0].times_seen == 1


def test_record_request_dedupes_repeated_endpoint(session):
    for _ in range(5):
        record_request(
            session, url="http://example.com/login", method="POST",
            status_code=200, response_bytes=100,
        )

    endpoints = session.exec(select(Endpoint)).all()
    assert len(endpoints) == 1
    assert endpoints[0].times_seen == 5

    # every hit should still be logged in RequestLog individually
    logs = session.exec(select(RequestLog)).all()
    assert len(logs) == 5


def test_record_request_only_fires_endpoint_discovered_once(session):
    for _ in range(5):
        record_request(
            session, url="http://example.com/login", method="POST",
            status_code=200, response_bytes=100,
        )

    discovered_events = session.exec(
        select(TimelineEvent).where(TimelineEvent.event_type == "ENDPOINT_DISCOVERED")
    ).all()
    assert len(discovered_events) == 1


def test_record_request_scopes_endpoints_per_target(session):
    record_request(
        session, url="http://a.com/login", method="POST",
        status_code=200, response_bytes=100,
    )
    record_request(
        session, url="http://b.com/login", method="POST",
        status_code=200, response_bytes=100,
    )

    # same path, different targets -> two separate Endpoint rows, not deduped
    endpoints = session.exec(select(Endpoint)).all()
    assert len(endpoints) == 2


def test_record_extracted_variables_stores_matched_key(session):
    record_request(
        session, url="http://example.com/login", method="POST",
        status_code=200, response_bytes=50,
    )
    body = b'{"authentication": {"token": "abc123"}}'
    record_extracted_variables(session, url="http://example.com/login", response_body=body)

    variables = session.exec(select(Variable)).all()
    assert len(variables) == 1
    assert variables[0].key == "token"
    assert variables[0].value == "abc123"
    assert variables[0].variable_type == "json_body_key"


def test_record_extracted_variables_ignores_non_allowlisted_keys(session):
    record_request(
        session, url="http://example.com/login", method="POST",
        status_code=200, response_bytes=50,
    )
    body = b'{"username": "admin", "bid": 1}'
    record_extracted_variables(session, url="http://example.com/login", response_body=body)

    assert len(session.exec(select(Variable)).all()) == 0


def test_record_extracted_variables_stores_cookie_without_response_body(session):
    record_request(
        session, url="http://example.com/login", method="POST",
        status_code=204, response_bytes=0,
    )
    record_extracted_variables(
        session,
        url="http://example.com/login",
        response_body=b"",
        response_headers={"Set-Cookie": "session=abc123; Path=/; HttpOnly"},
    )

    variables = session.exec(select(Variable)).all()
    assert len(variables) == 1
    assert variables[0].key == "session"
    assert variables[0].value == "abc123"
    assert variables[0].variable_type == "cookie"


def test_record_extracted_variables_does_nothing_if_target_missing(session):
    # no record_request() called first - target doesn't exist yet
    body = b'{"token": "abc123"}'
    record_extracted_variables(session, url="http://nowhere.com/x", response_body=body)

    assert len(session.exec(select(Variable)).all()) == 0
