"""Shared pytest fixtures for isolated database-backed tests.

The production application uses PostgreSQL. The test suite replaces the storage
session factories with a single in-memory SQLite database so tests cannot modify
a developer's local database.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from uuid import UUID

import pytest
from sqlalchemy import create_engine, delete, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# app.db.session requires DATABASE_URL at import time. This value is process-local
# and the production engine is not used by the test suite.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from app.db.models import Base, Event, Tenant  # noqa: E402
from app.storage import event_store, tenant_store  # noqa: E402


TEST_ENGINE = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=TEST_ENGINE,
    autoflush=False,
    autocommit=False,
)


@event.listens_for(TEST_ENGINE, "connect")
def register_sqlite_compatibility_functions(dbapi_connection, _connection_record) -> None:
    """Provide the PostgreSQL ``char_length`` function used by check constraints."""

    dbapi_connection.create_function("char_length", 1, len)


# Storage modules import SessionLocal directly, so replace those references with
# the isolated test session factory.
event_store.SessionLocal = TestingSessionLocal
tenant_store.SessionLocal = TestingSessionLocal


_original_get_event = event_store.get_event


def _sqlite_compatible_get_event(event_id: str | UUID):
    """Coerce valid UUID strings for SQLite's generic UUID bind processor.

    PostgreSQL accepts UUID text at the driver boundary. SQLite's SQLAlchemy UUID
    processor expects a UUID object, so this adapter preserves production-facing
    route behavior without changing application code.
    """

    if isinstance(event_id, str):
        try:
            event_id = UUID(event_id)
        except ValueError:
            pass

    return _original_get_event(event_id)


event_store.get_event = _sqlite_compatible_get_event


@pytest.fixture(scope="session", autouse=True)
def create_test_schema() -> Generator[None, None, None]:
    """Create the isolated schema once and remove it after the test session."""

    Base.metadata.create_all(TEST_ENGINE)
    yield
    Base.metadata.drop_all(TEST_ENGINE)


@pytest.fixture(autouse=True)
def clear_database(create_test_schema) -> Generator[None, None, None]:
    """Guarantee that every test starts and ends with an empty database."""

    _delete_all_rows()
    yield
    _delete_all_rows()


@pytest.fixture
def db_session(create_test_schema) -> Generator[Session, None, None]:
    """Yield a direct SQLAlchemy session for database-constraint tests."""

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def _delete_all_rows() -> None:
    """Delete rows in dependency-safe order without invoking application code."""

    with TestingSessionLocal() as db:
        db.execute(delete(Event))
        db.execute(delete(Tenant))
        db.commit()
