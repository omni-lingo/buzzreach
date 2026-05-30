"""Engine factory and session management for BuzzReach.

For SQLite a ``schema_translate_map`` remaps the ``buzzreach`` schema to
``None`` so schema-qualified models work without native schema support.
The same models run unchanged on PostgreSQL where the schema is real.
"""

import logging
from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.backend.settings import Settings

log = logging.getLogger("buzzreach")

SCHEMA_NAME = "buzzreach"

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _build_engine(
    database_url: str,
    db_schema: str = SCHEMA_NAME,
) -> Engine:
    """Create a new engine (non-singleton, useful for tests).

    Args:
        database_url: SQLAlchemy connection URL.
        db_schema: Logical schema name used by models.

    Returns:
        A configured ``Engine`` instance.
    """
    is_sqlite = database_url.startswith("sqlite")

    connect_args: dict[str, object] = {}
    if is_sqlite:
        connect_args["check_same_thread"] = False

    execution_options: dict[str, object] = {}
    if is_sqlite:
        execution_options["schema_translate_map"] = {db_schema: None}

    engine = create_engine(
        database_url,
        connect_args=connect_args,
        execution_options=execution_options,
    )

    log.info("Engine created", extra={"url": database_url})
    return engine


def get_engine(
    database_url: str | None = None,
    db_schema: str | None = None,
) -> Engine:
    """Return the singleton engine, creating it on first call.

    Args:
        database_url: Override the URL from Settings (first call only).
        db_schema: Override the schema name from Settings (first call only).

    Returns:
        The shared ``Engine`` instance.
    """
    global _engine  # noqa: PLW0603
    if _engine is not None:
        return _engine

    settings = Settings()
    url = database_url or settings.database_url
    schema = db_schema or settings.db_schema

    _engine = _build_engine(database_url=url, db_schema=schema)
    return _engine


def get_session_factory(
    engine: Engine | None = None,
) -> sessionmaker[Session]:
    """Return the singleton session factory, creating it on first call."""
    global _session_factory  # noqa: PLW0603
    if _session_factory is not None:
        return _session_factory

    engine = engine or get_engine()
    _session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return _session_factory


def get_session() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session (FastAPI ``Depends`` compatible)."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


def reset_engine() -> None:
    """Dispose engine and session factory singletons (for testing)."""
    global _engine, _session_factory  # noqa: PLW0603
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
