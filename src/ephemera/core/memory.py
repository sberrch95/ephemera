"""Memory layer: turns raw proxy traffic into stored Target/RequestLog/
Endpoint/TimelineEvent rows. The proxy addon calls into this; this module
is the only thing that talks to the database session directly.
"""

from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlmodel import select

from ephemera.database.models import Endpoint, RequestLog, Target, TimelineEvent
from ephemera.database.session import get_session


def get_or_create_target(session, hostname: str) -> Target:
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


def record_request(url: str, method: str, status_code: int, response_bytes: int) -> None:
    """Called by the proxy addon after each request/response pair completes."""
    hostname = urlparse(url).netloc
    path = urlparse(url).path or "/"

    with get_session() as session:
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
