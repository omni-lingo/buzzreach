"""Metric ORM model for the core module (CORE-005).

Product health tracking table. Stores timestamped metric values
per name and niche for aggregation (e.g. "opportunities_found",
"ai_tokens_used", "delivery_sent").

Composite index on (metric_name, niche, timestamp) for fast
time-range queries.
"""

import uuid as _uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.db.base import Base


class Metric(Base):
    """Timestamped product health metric."""

    __tablename__ = "metrics"
    __table_args__ = (
        Index(
            "ix_metrics_name_niche_timestamp",
            "metric_name",
            "niche",
            "timestamp",
        ),
        {"schema": "buzzreach"},
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        primary_key=True,
        default=_uuid.uuid4,
    )
    metric_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    niche: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
