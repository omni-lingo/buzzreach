"""Tests for DASH-001: Dashboard errors endpoint.

Covers: GET /api/v1/dashboard/errors (recent failures from audit log).
No auth required for MVP.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.db.base import Base
from tests.dashboard_helpers import build_dashboard_client, seed_error_log


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


class TestDashboardErrors:
    """GET /api/v1/dashboard/errors lists recent failures."""

    def test_errors_empty(self, db_session: Session) -> None:
        client = build_dashboard_client(db_session)
        resp = client.get("/api/v1/dashboard/errors")
        assert resp.status_code == 200
        body = resp.json()
        assert body["errors"] == []

    def test_errors_returns_recent(self, db_session: Session) -> None:
        seed_error_log(db_session, action="pipeline_error")
        seed_error_log(db_session, action="search_error")

        client = build_dashboard_client(db_session)
        resp = client.get("/api/v1/dashboard/errors")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["errors"]) == 2

    def test_excludes_non_error_actions(
        self, db_session: Session,
    ) -> None:
        seed_error_log(db_session, action="pipeline_error")
        seed_error_log(db_session, action="opportunity_acted")

        client = build_dashboard_client(db_session)
        resp = client.get("/api/v1/dashboard/errors")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["errors"]) == 1
        assert body["errors"][0]["action"] == "pipeline_error"

    def test_respects_hours_param(
        self, db_session: Session,
    ) -> None:
        seed_error_log(db_session, action="pipeline_error")
        old_ts = datetime.now(UTC) - timedelta(hours=48)
        seed_error_log(
            db_session,
            action="search_error",
            created_at=old_ts,
        )

        client = build_dashboard_client(db_session)
        resp = client.get("/api/v1/dashboard/errors?hours=24")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["errors"]) == 1
        assert body["errors"][0]["action"] == "pipeline_error"

    def test_errors_include_details(
        self, db_session: Session,
    ) -> None:
        seed_error_log(
            db_session,
            action="pipeline_error",
            change_summary="Search API timed out",
        )

        client = build_dashboard_client(db_session)
        resp = client.get("/api/v1/dashboard/errors")
        assert resp.status_code == 200
        body = resp.json()
        err = body["errors"][0]
        assert err["action"] == "pipeline_error"
        assert err["resource_type"] == "pipeline"
        assert err["change_summary"] == "Search API timed out"
        assert "created_at" in err
