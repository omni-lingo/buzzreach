"""SQLAlchemy declarative Base with schema-qualified metadata for BuzzReach.

Every model inheriting from ``Base`` lives in the ``buzzreach`` schema.
On SQLite the schema is resolved via ``schema_translate_map`` (see session.py).
On PostgreSQL the schema is used natively.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

SCHEMA_NAME = "buzzreach"


class Base(DeclarativeBase):
    """Base class for all BuzzReach ORM models.

    All models must declare:
        ``__table_args__ = {"schema": "buzzreach"}``
    to satisfy BUILD_RULES section 2 (schema-qualified tables).

    ``metadata.schema`` is set to ``buzzreach`` so Alembic autogenerate
    picks up the correct schema for every table.
    """

    metadata = MetaData(schema=SCHEMA_NAME)
