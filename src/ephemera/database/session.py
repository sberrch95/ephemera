"""Database engine and session management.

Ephemera stores its SQLite file in ~/.ephemera/ephemera.db by default -
not in the project repo, since captured traffic data must never end up
in version control (see .gitignore's ephemera_data/ and *.db entries -
this is the same principle, just for the actual runtime location too).
"""

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

# Import models so their table definitions register with SQLModel.metadata
# before init_db() runs create_all(). This import looks "unused" to a linter
# but it's required for its side effect - don't remove it.
from ephemera.database import models  # noqa: F401

DATA_DIR = Path.home() / ".ephemera"
DB_PATH = DATA_DIR / "ephemera.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}")


def init_db() -> None:
    """Create all tables if they don't already exist."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Return a new database session. Caller is responsible for closing it
    (use as a context manager: `with get_session() as session:`)."""
    return Session(engine)
