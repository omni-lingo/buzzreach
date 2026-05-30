"""Engine factory and session management for BuzzReach.

SQLite receives an ``ATTACH DATABASE`` so the ``buzzreach`` schema resolves.
A ``schema_translate_map`` is installed so the same schema-qualified models
run unchanged on PostgreSQL.
"""

import logging
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.backend.settings import Settings

log = logging.getLogger("buzzreach")

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None

SCHEMA_NAME = "buzzreach"


def _attach_schema(dbapi_conn: object, _rec: object) -> None:
    """Attach a SQLite database file as the 'buzzreach' schema."""
    cursor = dbapi_conn.cursor()  # type: ignore[union-attr]
    db_path = _resolve_sqlite_path()
    cursor.execute(f"ATTACH DATABASE '{db_path}' AS {SCHEMA_NAME}")
    cursor.close()


def _resolve_sqlite_path() -> str:
    """Return the absolute path to the SQLite database file."""
    settings = Settings()
    url = settings.database_url
    if url.startswith("sqlite:///"):
        raw = url.replace("sqlite:///", "", 1)
        return str(Path(raw).resolve())
    return ":memory:"


def get_engine(settings: Settings | None = None) -> Engine:
    """Create or return the singleton SQLAlchemy engine."""
    global _engine
    if _engine is not None:
        return _engine

    settings = settings or Settings()
    is_sqlite = settings.database_url.startswith("sqlite")

    connect_args: dict[str, object] = {}
    if is_sqlite:
        connect_args["check_same_thread"] = False

    engine = create_engine(
        settings.database_url,
        connect_args=connect_args,
        execution_options={"schema_translate_map": {SCHEMA_NAME: None}}
        if is_sqlite
        else {},
    )

    if is_sqlite:
        event.listen(engine, "connect", _attach_schema)

    _engine = engine
    log.info("Engine created", extra={"url": settings.database_url})
    return engine


def get_session_factory(
    engine: Engine | None = None,
) -> sessionmaker[Session]:
    """Create or return the singleton session factory."""
    global _SessionLocal
    if _SessionLocal is not None:
        return _SessionLocal

    engine = engine or get_engine()
    _SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return _SessionLocal


def get_session() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session, closing it when done."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


def reset_engine() -> None:
    """Dispose of the current engine and session factory (for testing)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
