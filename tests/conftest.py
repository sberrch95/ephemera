"""Shared pytest fixtures. conftest.py is auto-discovered by pytest -
anything defined here is available to every test file without importing.
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture
def session():
    """A fresh in-memory SQLite database for a single test.

    Using ':memory:' means each test gets its own isolated database that
    vanishes when the test ends - never touches ~/.ephemera/ephemera.db,
    and tests can't leak state into each other.
    """
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    engine.dispose()
