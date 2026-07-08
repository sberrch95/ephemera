"""Database engine and session management.

Ephemera stores its SQLite file in ~/.ephemera/ephemera.db by default -
not in the project repo, since captured traffic data must never end up
in version control.

The engine is created lazily via get_engine() rather than as a fixed
module-level constant, specifically so tests can swap in an in-memory
engine via override_engine() before any CLI command runs - without
that, every CLI test would read/write your real captured traffic data.
"""

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from ephemera.database import models  # noqa: F401  (registers tables with metadata)

DATA_DIR = Path.home() / ".ephemera"
DB_PATH = DATA_DIR / "ephemera.db"

_engine = None


def get_engine():
    """Return the current database engine, creating the default
    (real, on-disk) one on first use if nothing has overridden it."""
    global _engine
    if _engine is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{DB_PATH}")
    return _engine


def override_engine(engine) -> None:
    """Test-only hook: replace the active engine (e.g. with an in-memory
    one) before any CLI command or addon code runs."""
    global _engine
    _engine = engine


def init_db() -> None:
    """Create all tables if they don't already exist."""
    SQLModel.metadata.create_all(get_engine())


def get_session() -> Session:
    """Return a new database session against the current engine."""
    return Session(get_engine())
