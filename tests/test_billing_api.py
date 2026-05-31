"""Tests for BILL-004: Billing portal API endpoints.

Covers: GET /current, GET /invoices, GET /plans,
        POST /upgrade, POST /downgrade, POST /cancel, POST /cancel/confirm.
"""

import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.db.base import Base
from tests.billing_helpers import (
    build_billing_client,
    make_stripe_customer,
    make_subscription,
    make_user,
)

_USER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture()
def db_session() -> Session:
    """In-memory SQLite session with buzzreach schema."""
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


class TestGetCurrentBilling:
    """GET /api/v1/billing/current returns plan + usage overview."""

    def test_returns_free_plan_default(
        self, db_session: Session
    ) -> None:
        make_user(db_session)
        client = build_billing_client(db_session)
        resp = client.get("/api/v1/billing/current")
        assert resp.status_code == 200
        body = resp.json()
        assert body["plan_id"] == "free"
        assert body["plan_name"] == "Free"
        assert body["price_cents"] == 0
        assert body["usage_limit"] == 5
        assert body["usage_percentage"] == 0.0
        assert body["card_last4"] is None

    def test_returns_pro_plan_with_subscription(
        self, db_session: Session
    ) -> None:
        user = make_user(db_session)
        make_subscription(db_session, user.id, plan_id="pro")
        client = build_billing_client(db_session)
        resp = client.get("/api/v1/billing/current")
        assert resp.status_code == 200
        body = resp.json()
        assert body["plan_id"] == "pro"
        assert body["plan_name"] == "Pro"
        assert body["price_cents"] == 4900
        assert body["usage_limit"] == 100
        assert body["auto_renew"] is True
        assert body["status"] == "active"

    def test_features_list_included(
        self, db_session: Session
    ) -> None:
        user = make_user(db_session)
        make_subscription(db_session, user.id, plan_id="pro")
        client = build_billing_client(db_session)
        resp = client.get("/api/v1/billing/current")
        body = resp.json()
        assert "email_delivery" in body["features"]
        assert "slack_delivery" in body["features"]

    def test_no_api_keys_in_response(
        self, db_session: Session
    ) -> None:
        make_user(db_session)
        client = build_billing_client(db_session)
        resp = client.get("/api/v1/billing/current")
        body_str = resp.text
        assert "sk_test" not in body_str
        assert "sk_live" not in body_str
        assert "api_key" not in body_str


class TestGetInvoices:
    """GET /api/v1/billing/invoices returns invoice list."""

    def test_returns_empty_no_customer(
        self, db_session: Session
    ) -> None:
        make_user(db_session)
        client = build_billing_client(db_session)
        resp = client.get("/api/v1/billing/invoices")
        assert resp.status_code == 200
        body = resp.json()
        assert body["invoices"] == []
        assert body["total"] == 0


class TestGetPlans:
    """GET /api/v1/billing/plans returns plan comparison."""

    def test_returns_all_plans(self, db_session: Session) -> None:
        make_user(db_session)
        client = build_billing_client(db_session)
        resp = client.get("/api/v1/billing/plans")
        assert resp.status_code == 200
        body = resp.json()
        plan_ids = [p["plan_id"] for p in body["plans"]]
        assert "free" in plan_ids
        assert "pro" in plan_ids
        assert "premium" in plan_ids

    def test_current_plan_highlighted(
        self, db_session: Session
    ) -> None:
        user = make_user(db_session)
        make_subscription(db_session, user.id, plan_id="pro")
        client = build_billing_client(db_session)
        resp = client.get("/api/v1/billing/plans")
        body = resp.json()
        current_plans = [
            p for p in body["plans"] if p["is_current"]
        ]
        assert len(current_plans) == 1
        assert current_plans[0]["plan_id"] == "pro"

    def test_free_user_sees_free_highlighted(
        self, db_session: Session
    ) -> None:
        make_user(db_session)
        client = build_billing_client(db_session)
        resp = client.get("/api/v1/billing/plans")
        body = resp.json()
        current = [p for p in body["plans"] if p["is_current"]]
        assert len(current) == 1
        assert current[0]["plan_id"] == "free"


class TestUpgrade:
    """POST /api/v1/billing/upgrade initiates Stripe checkout."""

    def test_upgrade_requires_stripe_customer(
        self, db_session: Session
    ) -> None:
        make_user(db_session)
        client = build_billing_client(db_session)
        resp = client.post(
            "/api/v1/billing/upgrade",
            json={"plan_id": "pro"},
        )
        assert resp.status_code == 400
        body = resp.json()
        assert body["detail"]["error_code"] == "CUSTOMER_NOT_FOUND"

    def test_upgrade_invalid_plan(
        self, db_session: Session
    ) -> None:
        user = make_user(db_session)
        make_stripe_customer(db_session, user.id)
        client = build_billing_client(db_session)
        resp = client.post(
            "/api/v1/billing/upgrade",
            json={"plan_id": "nonexistent"},
        )
        assert resp.status_code == 400
        body = resp.json()
        assert body["detail"]["error_code"] == "INVALID_PLAN"


class TestDowngrade:
    """POST /api/v1/billing/downgrade initiates plan downgrade."""

    def test_downgrade_no_subscription(
        self, db_session: Session
    ) -> None:
        make_user(db_session)
        client = build_billing_client(db_session)
        resp = client.post(
            "/api/v1/billing/downgrade",
            json={"plan_id": "free"},
        )
        assert resp.status_code == 400
        body = resp.json()
        assert body["detail"]["error_code"] == "NO_ACTIVE_SUBSCRIPTION"


class TestCancel:
    """POST /api/v1/billing/cancel handles cancellation."""

    def test_cancel_no_subscription(
        self, db_session: Session
    ) -> None:
        make_user(db_session)
        client = build_billing_client(db_session)
        resp = client.post(
            "/api/v1/billing/cancel",
            json={"reason": "too expensive"},
        )
        assert resp.status_code == 400

    def test_cancel_offers_retention_for_pro(
        self, db_session: Session
    ) -> None:
        user = make_user(db_session)
        make_subscription(db_session, user.id, plan_id="pro")
        make_stripe_customer(db_session, user.id, plan_id="pro")
        client = build_billing_client(db_session)
        resp = client.post(
            "/api/v1/billing/cancel",
            json={"reason": "too expensive"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["retention_offered"] is True
        assert "1 month free" in body["message"]


class TestCancelConfirm:
    """POST /api/v1/billing/cancel/confirm finalizes cancellation."""

    def test_confirm_cancel_no_subscription(
        self, db_session: Session
    ) -> None:
        make_user(db_session)
        client = build_billing_client(db_session)
        resp = client.post("/api/v1/billing/cancel/confirm")
        assert resp.status_code == 400
