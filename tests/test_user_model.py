"""Tests for AUTH-001: User model and UserData contract.

Covers: create user row, query by username/email/api_key,
is_active flag, unique constraints, and UserData contract safety.
"""

import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from contracts.auth.user import UserData
from src.backend.db.base import Base
from src.backend.models.user import User


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


def _make_user(**overrides: object) -> User:
    """Build a User with sensible defaults; override any field."""
    defaults: dict[str, object] = {
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": "hashed_pw_placeholder",
        "api_key": f"bz_{uuid.uuid4().hex[:24]}",
    }
    defaults.update(overrides)
    return User(**defaults)


class TestUserCreate:
    """Creating a User row persists all columns correctly."""

    def test_create_user_with_defaults(self, db_session: Session) -> None:
        user = _make_user()
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_id_is_uuid(self, db_session: Session) -> None:
        user = _make_user()
        db_session.add(user)
        db_session.commit()

        assert isinstance(user.id, uuid.UUID)

    def test_password_hash_stored_not_plain(self, db_session: Session) -> None:
        user = _make_user(password_hash="argon2$hashed_value")
        db_session.add(user)
        db_session.commit()

        fetched = db_session.get(User, user.id)
        assert fetched is not None
        assert fetched.password_hash == "argon2$hashed_value"
        assert not hasattr(fetched, "password")


class TestUserQueries:
    """Querying users by username, email, and api_key."""

    def test_query_by_username(self, db_session: Session) -> None:
        user = _make_user(username="alice")
        db_session.add(user)
        db_session.commit()

        found = db_session.query(User).filter_by(username="alice").first()
        assert found is not None
        assert found.id == user.id

    def test_query_by_email(self, db_session: Session) -> None:
        user = _make_user(email="alice@example.com")
        db_session.add(user)
        db_session.commit()

        found = db_session.query(User).filter_by(email="alice@example.com").first()
        assert found is not None
        assert found.id == user.id

    def test_query_by_api_key(self, db_session: Session) -> None:
        api_key = "bz_test_key_12345678"
        user = _make_user(api_key=api_key)
        db_session.add(user)
        db_session.commit()

        found = db_session.query(User).filter_by(api_key=api_key).first()
        assert found is not None
        assert found.id == user.id


class TestUserUniqueConstraints:
    """Unique constraints on username, email, and api_key."""

    def test_duplicate_username_raises(self, db_session: Session) -> None:
        db_session.add(_make_user(username="dup", email="a@x.com"))
        db_session.commit()

        db_session.add(_make_user(username="dup", email="b@x.com"))
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_duplicate_email_raises(self, db_session: Session) -> None:
        db_session.add(_make_user(username="u1", email="dup@x.com"))
        db_session.commit()

        db_session.add(_make_user(username="u2", email="dup@x.com"))
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_duplicate_api_key_raises(self, db_session: Session) -> None:
        key = "bz_duplicate_key_value"
        db_session.add(_make_user(username="u1", email="a@x.com", api_key=key))
        db_session.commit()

        db_session.add(_make_user(username="u2", email="b@x.com", api_key=key))
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestIsActiveFlag:
    """The is_active flag defaults to True and can be toggled."""

    def test_default_is_active(self, db_session: Session) -> None:
        user = _make_user()
        db_session.add(user)
        db_session.commit()

        assert user.is_active is True

    def test_set_inactive(self, db_session: Session) -> None:
        user = _make_user(is_active=False)
        db_session.add(user)
        db_session.commit()

        fetched = db_session.get(User, user.id)
        assert fetched is not None
        assert fetched.is_active is False

    def test_toggle_active(self, db_session: Session) -> None:
        user = _make_user()
        db_session.add(user)
        db_session.commit()

        user.is_active = False
        db_session.commit()

        fetched = db_session.get(User, user.id)
        assert fetched is not None
        assert fetched.is_active is False


class TestSchemaQualified:
    """User model is schema-qualified to 'buzzreach'."""

    def test_table_schema_is_buzzreach(self) -> None:
        args = User.__table_args__
        if isinstance(args, tuple):
            schema_dict = next(a for a in args if isinstance(a, dict))
        else:
            schema_dict = args
        assert schema_dict["schema"] == "buzzreach"

    def test_tablename_is_users(self) -> None:
        assert User.__tablename__ == "users"


class TestUserDataContract:
    """UserData contract never exposes password_hash or api_key."""

    def test_userdata_fields(self) -> None:
        data = UserData(
            id=uuid.uuid4(),
            username="alice",
            email="alice@example.com",
            is_active=True,
        )
        assert data.username == "alice"
        assert data.email == "alice@example.com"
        assert data.is_active is True

    def test_no_password_hash_field(self) -> None:
        fields = UserData.model_fields
        assert "password_hash" not in fields

    def test_no_api_key_field(self) -> None:
        fields = UserData.model_fields
        assert "api_key" not in fields

    def test_userdata_from_user_excludes_secrets(
        self, db_session: Session
    ) -> None:
        user = _make_user()
        db_session.add(user)
        db_session.commit()

        data = UserData(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
        )
        serialized = data.model_dump()
        assert "password_hash" not in serialized
        assert "api_key" not in serialized
        assert serialized["username"] == user.username
