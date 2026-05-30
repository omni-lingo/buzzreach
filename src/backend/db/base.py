"""SQLAlchemy declarative Base with schema-qualified metadata for BuzzReach."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all BuzzReach ORM models.

    All models must declare ``__table_args__ = {"schema": "buzzreach"}``
    to ensure schema-qualified table names (BUILD_RULES section 2).
    """
