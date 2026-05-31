"""Tests for DASH-001: Dashboard summary and stats endpoints.

Covers: GET /api/v1/dashboard (summary), GET /api/v1/dashboard/stats
(per-niche aggregation). No auth required for MVP.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.db.base import Base
from src.backend.models.opportunity import OpportunityStatus
from tests.dashboard_helpers import (
    build_dashboard_client,
    seed_error_log,
    seed_metric,
    seed_opportunity,
)


@pytest.fixture()
def db_session() -> Session:
    """In-memory SQLite session with cross-thread access for TestClient."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        execution_options={"schema_translate_map": {"buzzreach": None}},
        poolclass=StaticPool,
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


class TestDashboardSummary:
    """GET /api/v1/dashboard returns today's summary."""

    def test_empty_dashboard(self, db_session: Session) -> None:
        client = build_dashboard_client(db_session)
        resp = client.get("/api/v1/dashboard")
        assert resp.status_code == 200
        body = resp.json()
        assert body["opportunities_found"] == 0
        assert body["acted_on"] == 0
        assert body["ai_tokens_used"] == 0
        assert body["cost_usd"] == 0.0
        assert body["error_count"] == 0

    def test_counts_today_opportunities(
        self, db_session: Session,
    ) -> None:
        seed_opportunity(db_session, status=OpportunityStatus.NEW)
        seed_opportunity(db_session, status=OpportunityStatus.ACTED)
        seed_opportunity(db_session, status=OpportunityStatus.SKIPPED)
        yesterday = datetime.now(UTC) - timedelta(days=1)
        seed_opportunity(
            db_session,
            status=OpportunityStatus.NEW,
            created_at=yesterday,
        )

        client = build_dashboard_client(db_session)
        resp = client.get("/api/v1/dashboard")
        assert resp.status_code == 200
        body = resp.json()
        assert body["opportunities_found"] == 3
        assert body["acted_on"] == 1

    def test_aggregates_ai_metrics(
        self, db_session: Session,
    ) -> None:
        seed_metric(
            db_session, "ai_input_tokens_haiku", 1000.0, "tax-help",
        )
        seed_metric(
            db_session, "ai_output_tokens_haiku", 500.0, "tax-help",
        )
        seed_metric(db_session, "ai_cost_usd", 0.05, "tax-help")
        seed_metric(db_session, "ai_cost_usd", 0.03, "parking")

        client = build_dashboard_client(db_session)
        resp = client.get("/api/v1/dashboard")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ai_tokens_used"] == 1500
        assert body["cost_usd"] == pytest.approx(0.08)

    def test_counts_errors(self, db_session: Session) -> None:
        seed_error_log(db_session, action="pipeline_error")
        seed_error_log(db_session, action="search_error")
        seed_error_log(db_session, action="opportunity_acted")

        client = build_dashboard_client(db_session)
        resp = client.get("/api/v1/dashboard")
        assert resp.status_code == 200
        body = resp.json()
        assert body["error_count"] == 2


class TestDashboardStats:
    """GET /api/v1/dashboard/stats aggregates by niche."""

    def test_stats_no_data(self, db_session: Session) -> None:
        client = build_dashboard_client(db_session)
        resp = client.get("/api/v1/dashboard/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["niches"] == []

    def test_stats_groups_by_niche(self, db_session: Session) -> None:
        seed_metric(db_session, "candidates_found", 5.0, "tax-help")
        seed_metric(db_session, "candidates_found", 3.0, "parking")

        client = build_dashboard_client(db_session)
        resp = client.get("/api/v1/dashboard/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["niches"]) == 2
        niches_by_name = {n["niche"]: n for n in body["niches"]}
        assert "tax-help" in niches_by_name
        assert "parking" in niches_by_name

    def test_stats_filters_by_niche(self, db_session: Session) -> None:
        seed_metric(db_session, "candidates_found", 5.0, "tax-help")
        seed_metric(db_session, "candidates_found", 3.0, "parking")

        client = build_dashboard_client(db_session)
        resp = client.get("/api/v1/dashboard/stats?niche=tax-help")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["niches"]) == 1
        assert body["niches"][0]["niche"] == "tax-help"

    def test_stats_respects_days_param(
        self, db_session: Session,
    ) -> None:
        seed_metric(db_session, "candidates_found", 5.0, "tax-help")
        old_ts = datetime.now(UTC) - timedelta(days=10)
        seed_metric(
            db_session, "candidates_found", 99.0, "tax-help", old_ts,
        )

        client = build_dashboard_client(db_session)
        resp = client.get("/api/v1/dashboard/stats?days=7")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["niches"]) == 1
        metrics = body["niches"][0]["metrics"]
        assert "candidates_found" in metrics
        assert metrics["candidates_found"]["sum"] == 5.0
