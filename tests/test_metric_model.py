"""Tests for CORE-005: Metric model (product health tracking).

Covers: insert a metric row, query by name/niche/time range,
default timestamp, composite index, and schema qualification.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

from src.backend.db.base import Base
from src.backend.models.metric import Metric


@pytest.fixture()
def db_session() -> Session:
    """Create an in-memory SQLite session with the buzzreach schema attached."""
    engine = create_engine(
        "sqlite:///:memory:",
        execution_options={"schema_translate_map": {"buzzreach": None}},
    )

    @event.listens_for(engine, "connect")
    def _attach(dbapi_conn: object, _rec: object) -> None:
        cursor = dbapi_conn.cursor()  # type: ignore[union-attr]
        cursor.execute("ATTACH DATABASE ':memory:' AS buzzreach")
        cursor.close()

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    yield session
    session.close()
    engine.dispose()


def _make_metric(**overrides: object) -> Metric:
    """Build a Metric with sensible defaults; override any field."""
    defaults: dict[str, object] = {
        "metric_name": "opportunities_found",
        "niche": "tax",
        "value": 42.0,
    }
    defaults.update(overrides)
    return Metric(**defaults)


class TestMetricCreate:
    """Creating a Metric row persists all columns correctly."""

    def test_create_with_defaults(self, db_session: Session) -> None:
        row = _make_metric()
        db_session.add(row)
        db_session.commit()

        assert row.id is not None
        assert isinstance(row.id, uuid.UUID)
        assert row.metric_name == "opportunities_found"
        assert row.niche == "tax"
        assert row.value == 42.0
        assert row.timestamp is not None

    def test_stores_all_fields(self, db_session: Session) -> None:
        ts = datetime.now(UTC)
        row = _make_metric(
            metric_name="ai_tokens_used",
            niche="parking",
            value=1500.5,
            timestamp=ts,
        )
        db_session.add(row)
        db_session.commit()

        fetched = db_session.get(Metric, row.id)
        assert fetched is not None
        assert fetched.metric_name == "ai_tokens_used"
        assert fetched.niche == "parking"
        assert fetched.value == 1500.5

    def test_allows_duplicate_name_niche_timestamp(
        self, db_session: Session
    ) -> None:
        """No unique constraint — multiple values per name/niche allowed."""
        row1 = _make_metric(value=10.0)
        row2 = _make_metric(value=20.0)
        db_session.add_all([row1, row2])
        db_session.commit()

        assert row1.id != row2.id


class TestMetricQuery:
    """Querying metrics by name, niche, and time range."""

    def test_query_by_name(self, db_session: Session) -> None:
        db_session.add(_make_metric(metric_name="delivery_sent"))
        db_session.add(_make_metric(metric_name="ai_tokens_used"))
        db_session.commit()

        stmt = select(Metric).where(Metric.metric_name == "delivery_sent")
        results = db_session.execute(stmt).scalars().all()
        assert len(results) == 1
        assert results[0].metric_name == "delivery_sent"

    def test_query_by_niche(self, db_session: Session) -> None:
        db_session.add(_make_metric(niche="tax"))
        db_session.add(_make_metric(niche="parking"))
        db_session.commit()

        stmt = select(Metric).where(Metric.niche == "parking")
        results = db_session.execute(stmt).scalars().all()
        assert len(results) == 1
        assert results[0].niche == "parking"

    def test_query_by_time_range(self, db_session: Session) -> None:
        now = datetime.now(UTC)
        old = now - timedelta(days=7)
        recent = now - timedelta(hours=1)

        db_session.add(_make_metric(timestamp=old, value=1.0))
        db_session.add(_make_metric(timestamp=recent, value=2.0))
        db_session.commit()

        cutoff = now - timedelta(days=1)
        stmt = select(Metric).where(Metric.timestamp >= cutoff)
        results = db_session.execute(stmt).scalars().all()
        assert len(results) == 1
        assert results[0].value == 2.0

    def test_query_by_name_niche_time(self, db_session: Session) -> None:
        now = datetime.now(UTC)
        db_session.add(
            _make_metric(
                metric_name="delivery_sent",
                niche="tax",
                timestamp=now,
                value=5.0,
            )
        )
        db_session.add(
            _make_metric(
                metric_name="delivery_sent",
                niche="parking",
                timestamp=now,
                value=3.0,
            )
        )
        db_session.commit()

        stmt = select(Metric).where(
            Metric.metric_name == "delivery_sent",
            Metric.niche == "tax",
            Metric.timestamp >= now - timedelta(minutes=1),
        )
        results = db_session.execute(stmt).scalars().all()
        assert len(results) == 1
        assert results[0].value == 5.0


class TestMetricIndex:
    """Composite index on (metric_name, niche, timestamp) exists."""

    def test_composite_index_exists(self) -> None:
        index_names = {idx.name for idx in Metric.__table__.indexes}
        assert "ix_metrics_name_niche_timestamp" in index_names


class TestSchemaQualified:
    """Metric model is schema-qualified to 'buzzreach'."""

    def test_table_schema_is_buzzreach(self) -> None:
        args = Metric.__table_args__
        if isinstance(args, tuple):
            schema_dict = next(a for a in args if isinstance(a, dict))
        else:
            schema_dict = args
        assert schema_dict["schema"] == "buzzreach"

    def test_tablename_is_metrics(self) -> None:
        assert Metric.__tablename__ == "metrics"
