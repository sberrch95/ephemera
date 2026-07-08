"""Memory layer: turns raw proxy traffic into stored Target/RequestLog/
Endpoint/TimelineEvent rows.

Design note: every function here takes `session` as a parameter rather
than creating its own via get_session(). This is deliberate - it means
these functions don't hardcode "always talk to the real database," which
makes them testable against an isolated in-memory database, and keeps
the decision of *which* session to use with the caller (the proxy addon
in production, a pytest fixture in tests).
"""

from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlmodel import Session, select

from ephemera.database.models import Endpoint, RequestLog, Target, TimelineEvent, Variable
from ephemera.extractor.builtin import extract_from_json_body


def get_or_create_target(session: Session, hostname: str) -> Target:
    """Find the Target row for this hostname, or create it if it's new."""
    existing = session.exec(select(Target).where(Target.hostname == hostname)).first()
    if existing:
        existing.last_seen = datetime.now(timezone.utc)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    target = Target(hostname=hostname)
    session.add(target)
    session.commit()
    session.refresh(target)

    session.add(TimelineEvent(
        target_id=target.id,
        event_type="TARGET_SEEN",
        description=f"First contact with {hostname}",
    ))
    session.commit()

    return target


def record_request(
    session: Session, url: str, method: str, status_code: int, response_bytes: int
) -> None:
    """Store a request/response pair. Caller provides the session."""
    hostname = urlparse(url).netloc
    path = urlparse(url).path or "/"

    target = get_or_create_target(session, hostname)

    session.add(RequestLog(
        target_id=target.id,
        method=method,
        url=url,
        status_code=status_code,
        response_bytes=response_bytes,
    ))

    existing_endpoint = session.exec(
        select(Endpoint).where(
            Endpoint.target_id == target.id,
            Endpoint.path == path,
            Endpoint.method == method,
        )
    ).first()

    if existing_endpoint:
        existing_endpoint.times_seen += 1
        session.add(existing_endpoint)
    else:
        session.add(Endpoint(target_id=target.id, path=path, method=method))
        session.add(TimelineEvent(
            target_id=target.id,
            event_type="ENDPOINT_DISCOVERED",
            description=f"New endpoint: {method} {path}",
        ))

    session.commit()


def record_extracted_variables(session: Session, url: str, response_body: bytes) -> None:
    """Run extraction against a response body and store matches. Caller
    provides the session, and must ensure record_request() has already
    run for this URL so the Target row exists."""
    hostname = urlparse(url).netloc
    candidates = extract_from_json_body(response_body)

    if not candidates:
        return

    target = session.exec(select(Target).where(Target.hostname == hostname)).first()
    if not target:
        return

    for candidate in candidates:
        session.add(Variable(
            target_id=target.id,
            variable_type=candidate.variable_type,
            key=candidate.key,
            value=candidate.value,
            source_url=url,
        ))
        session.add(TimelineEvent(
            target_id=target.id,
            event_type="VARIABLE_EXTRACTED",
            description=f"Extracted '{candidate.key}' from {url}",
        ))

    session.commit()
