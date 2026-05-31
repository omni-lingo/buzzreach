"""Shared test fixtures for BuzzReach test suite."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.backend.db.base import Base
from src.backend.models.subscription import Subscription
from src.backend.models.usage import DailyUsage
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


def make_user(**overrides: object) -> User:
    """Build a User with sensible defaults."""
    defaults: dict[str, object] = {
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "email": f"{uuid.uuid4().hex[:8]}@test.com",
        "password_hash": "hashed_pw_placeholder",
        "api_key": f"bz_{uuid.uuid4().hex[:24]}",
    }
    defaults.update(overrides)
    return User(**defaults)


def make_subscription(
    user_id: uuid.UUID, **overrides: object
) -> Subscription:
    """Build a Subscription with sensible defaults."""
    defaults: dict[str, object] = {
        "user_id": user_id,
        "plan_id": "free",
        "status": "active",
    }
    defaults.update(overrides)
    return Subscription(**defaults)


def make_usage(
    user_id: uuid.UUID, **overrides: object
) -> DailyUsage:
    """Build a DailyUsage with sensible defaults."""
    defaults: dict[str, object] = {
        "user_id": user_id,
        "usage_date": date.today(),
        "opportunities_found": 0,
        "api_calls": 0,
        "email_sent": 0,
        "push_sent": 0,
        "drafts_regenerated": 0,
        "stripe_cost": Decimal("0"),
        "ai_cost": Decimal("0"),
        "search_cost": Decimal("0"),
    }
    defaults.update(overrides)
    return DailyUsage(**defaults)


def setup_user_with_plan(
    db_session: Session,
    plan_id: str = "free",
) -> User:
    """Create a user with a subscription on the given plan."""
    user = make_user()
    db_session.add(user)
    db_session.commit()
    sub = make_subscription(user.id, plan_id=plan_id)
    db_session.add(sub)
    db_session.commit()
    return user
