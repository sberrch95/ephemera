"""SQLModel table definitions for Ephemera's memory layer.

Four tables: Target is the scoping root; RequestLog, Endpoint, and
TimelineEvent all hang off a Target via foreign key.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Target(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hostname: str = Field(index=True, unique=True)
    first_seen: datetime = Field(default_factory=utcnow)
    last_seen: datetime = Field(default_factory=utcnow)


class RequestLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    target_id: int = Field(foreign_key="target.id", index=True)
    method: str
    url: str
    status_code: Optional[int] = None
    response_bytes: Optional[int] = None
    timestamp: datetime = Field(default_factory=utcnow)


class Endpoint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    target_id: int = Field(foreign_key="target.id", index=True)
    path: str
    method: str
    times_seen: int = Field(default=1)
    first_seen: datetime = Field(default_factory=utcnow)


class TimelineEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    target_id: int = Field(foreign_key="target.id", index=True)
    event_type: str
    description: str
    timestamp: datetime = Field(default_factory=utcnow)
