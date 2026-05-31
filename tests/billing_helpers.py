"""Shared test helpers for BILL-004 billing portal tests.

Provides factory functions for users, subscriptions, Stripe customers,
and a TestClient builder with auth override.
"""

import uuid
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from contracts.auth.user import UserData
from src.backend.models.stripe_customer import StripeCustomer
from src.backend.models.subscription import Subscription
from src.backend.models.user import User

_TEST_USER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def make_user(
    session: Session, **overrides: object
) -> User:
    """Create and persist a User with sensible defaults."""
    defaults: dict[str, object] = {
        "id": _TEST_USER_ID,
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "email": f"{uuid.uuid4().hex[:8]}@test.com",
        "password_hash": "hashed_pw_placeholder",
        "api_key": f"bz_{uuid.uuid4().hex[:24]}",
    }
    defaults.update(overrides)
    user = User(**defaults)
    session.add(user)
    session.commit()
    return user


def make_subscription(
    session: Session, user_id: uuid.UUID, **overrides: object
) -> Subscription:
    """Create and persist a Subscription with sensible defaults."""
    defaults: dict[str, object] = {
        "user_id": user_id,
        "plan_id": "pro",
        "status": "active",
        "current_period_start": datetime.utcnow(),
        "current_period_end": datetime.utcnow() + timedelta(days=30),
        "auto_renew": True,
    }
    defaults.update(overrides)
    sub = Subscription(**defaults)
    session.add(sub)
    session.commit()
    return sub


def make_stripe_customer(
    session: Session, user_id: uuid.UUID, **overrides: object
) -> StripeCustomer:
    """Create and persist a StripeCustomer record."""
    defaults: dict[str, object] = {
        "user_id": user_id,
        "stripe_customer_id": f"cus_{uuid.uuid4().hex[:14]}",
        "stripe_subscription_id": f"sub_{uuid.uuid4().hex[:14]}",
        "plan_id": "pro",
        "subscription_status": "active",
        "current_period_end": datetime.utcnow() + timedelta(days=30),
    }
    defaults.update(overrides)
    record = StripeCustomer(**defaults)
    session.add(record)
    session.commit()
    return record


def build_billing_client(
    db_session: Session,
    user_id: uuid.UUID | None = None,
) -> TestClient:
    """Build a TestClient with session and auth overrides."""
    from src.backend.api.auth_deps import get_current_user
    from src.backend.api.main import create_app
    from src.backend.db.session import get_session

    app = create_app()
    uid = user_id or _TEST_USER_ID

    def _override_session() -> Session:
        return db_session

    def _override_user() -> UserData:
        return UserData(
            id=uid,
            username="testuser",
            email="test@example.com",
            is_active=True,
        )

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_user] = _override_user
    return TestClient(app)
