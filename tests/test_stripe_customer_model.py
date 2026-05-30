"""Tests for BILL-001: StripeCustomer model and SubscriptionData contract.

Covers: StripeCustomer CRUD, schema qualification, default values,
and SubscriptionData contract validation.
"""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from contracts.billing.subscription import SubscriptionData, SubscriptionStatus
from src.backend.db.base import Base
from src.backend.models.stripe_customer import StripeCustomer
from src.backend.models.user import User


@pytest.fixture()
def db_session() -> Session:
    """In-memory SQLite session with the buzzreach schema attached."""
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


def _make_user(**overrides: object) -> User:
    """Build a User with sensible defaults."""
    defaults: dict[str, object] = {
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "email": f"{uuid.uuid4().hex[:8]}@test.com",
        "password_hash": "hashed_pw_placeholder",
        "api_key": f"bz_{uuid.uuid4().hex[:24]}",
    }
    defaults.update(overrides)
    return User(**defaults)


class TestStripeCustomerModel:
    """StripeCustomer model persists Stripe-to-User link."""

    def test_create_stripe_customer(self, db_session: Session) -> None:
        user = _make_user()
        db_session.add(user)
        db_session.commit()

        sc = StripeCustomer(
            user_id=user.id,
            stripe_customer_id="cus_test_123",
        )
        db_session.add(sc)
        db_session.commit()

        assert sc.id is not None
        assert sc.stripe_customer_id == "cus_test_123"
        assert sc.user_id == user.id

    def test_subscription_fields_default_none(self, db_session: Session) -> None:
        user = _make_user()
        db_session.add(user)
        db_session.commit()

        sc = StripeCustomer(user_id=user.id, stripe_customer_id="cus_456")
        db_session.add(sc)
        db_session.commit()

        assert sc.stripe_subscription_id is None
        assert sc.plan_id is None
        assert sc.subscription_status == "none"

    def test_schema_is_buzzreach(self) -> None:
        args = StripeCustomer.__table_args__
        if isinstance(args, tuple):
            schema_dict = next(a for a in args if isinstance(a, dict))
        else:
            schema_dict = args
        assert schema_dict["schema"] == "buzzreach"

    def test_tablename(self) -> None:
        assert StripeCustomer.__tablename__ == "stripe_customers"


class TestSubscriptionDataContract:
    """SubscriptionData contract validates correctly."""

    def test_contract_from_model(self, db_session: Session) -> None:
        user = _make_user()
        db_session.add(user)
        db_session.commit()

        now = datetime.now(UTC)
        sc = StripeCustomer(
            user_id=user.id,
            stripe_customer_id="cus_contract",
            stripe_subscription_id="sub_test",
            plan_id="price_basic",
            subscription_status="active",
            current_period_end=now,
        )
        db_session.add(sc)
        db_session.commit()

        data = SubscriptionData(
            user_id=sc.user_id,
            stripe_customer_id=sc.stripe_customer_id,
            stripe_subscription_id=sc.stripe_subscription_id,
            plan_id=sc.plan_id,
            status=SubscriptionStatus(sc.subscription_status),
            current_period_end=sc.current_period_end,
        )
        dumped = data.model_dump()
        assert dumped["status"] == "active"
        assert dumped["plan_id"] == "price_basic"
        assert "stripe_customer_id" in dumped

    def test_contract_fields(self) -> None:
        fields = SubscriptionData.model_fields
        assert "user_id" in fields
        assert "stripe_customer_id" in fields
        assert "status" in fields

    def test_status_enum_values(self) -> None:
        assert SubscriptionStatus.ACTIVE == "active"
        assert SubscriptionStatus.PAST_DUE == "past_due"
        assert SubscriptionStatus.CANCELED == "canceled"
        assert SubscriptionStatus.NONE == "none"
