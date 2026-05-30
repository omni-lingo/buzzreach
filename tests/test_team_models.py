"""Tests for ADMIN-001: Team, TeamMember, TeamInvitation models.

Covers: model creation, constraints, schema qualification,
and contract DTOs.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from contracts.admin.team import (
    PLAN_MEMBER_LIMITS,
    TeamData,
    TeamInvitationData,
    TeamMemberData,
)
from src.backend.db.base import Base
from src.backend.models.team import Team
from src.backend.models.team_invitation import TeamInvitation
from src.backend.models.team_member import TeamMember, TeamRole
from src.backend.models.user import User


@pytest.fixture()
def db_session() -> Session:
    """In-memory SQLite session with buzzreach schema attached."""
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
        "email": f"{uuid.uuid4().hex[:8]}@example.com",
        "password_hash": "hashed_pw",
        "api_key": f"bz_{uuid.uuid4().hex[:24]}",
    }
    defaults.update(overrides)
    return User(**defaults)


class TestTeamModel:
    """Team model CRUD and constraints."""

    def test_create_team(self, db_session: Session) -> None:
        user = _make_user()
        db_session.add(user)
        db_session.flush()

        team = Team(owner_id=user.id, name="My Team")
        db_session.add(team)
        db_session.commit()

        assert team.id is not None
        assert isinstance(team.id, uuid.UUID)
        assert team.name == "My Team"
        assert team.owner_id == user.id
        assert team.created_at is not None

    def test_team_schema_is_buzzreach(self) -> None:
        args = Team.__table_args__
        if isinstance(args, tuple):
            schema_dict = next(a for a in args if isinstance(a, dict))
        else:
            schema_dict = args
        assert schema_dict["schema"] == "buzzreach"

    def test_tablename_is_teams(self) -> None:
        assert Team.__tablename__ == "teams"


class TestTeamMemberModel:
    """TeamMember model CRUD and unique constraint."""

    def test_create_member(self, db_session: Session) -> None:
        user = _make_user()
        db_session.add(user)
        db_session.flush()

        team = Team(owner_id=user.id, name="Test Team")
        db_session.add(team)
        db_session.flush()

        member = TeamMember(
            team_id=team.id,
            user_id=user.id,
            role=TeamRole.OWNER,
            joined_at=datetime.now(UTC),
        )
        db_session.add(member)
        db_session.commit()

        assert member.id is not None
        assert member.role == TeamRole.OWNER

    def test_duplicate_membership_raises(
        self, db_session: Session
    ) -> None:
        user = _make_user()
        db_session.add(user)
        db_session.flush()

        team = Team(owner_id=user.id, name="Test Team")
        db_session.add(team)
        db_session.flush()

        m1 = TeamMember(
            team_id=team.id, user_id=user.id, role=TeamRole.OWNER
        )
        db_session.add(m1)
        db_session.commit()

        m2 = TeamMember(
            team_id=team.id, user_id=user.id, role=TeamRole.MEMBER
        )
        db_session.add(m2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_role_enum_values(self) -> None:
        assert TeamRole.OWNER.value == "owner"
        assert TeamRole.ADMIN.value == "admin"
        assert TeamRole.MEMBER.value == "member"

    def test_member_schema_is_buzzreach(self) -> None:
        args = TeamMember.__table_args__
        if isinstance(args, tuple):
            schema_dict = next(a for a in args if isinstance(a, dict))
        else:
            schema_dict = args
        assert schema_dict["schema"] == "buzzreach"


class TestTeamInvitationModel:
    """TeamInvitation model CRUD and defaults."""

    def test_create_invitation(self, db_session: Session) -> None:
        user = _make_user()
        db_session.add(user)
        db_session.flush()

        team = Team(owner_id=user.id, name="Test Team")
        db_session.add(team)
        db_session.flush()

        inv = TeamInvitation(
            team_id=team.id,
            email="new@example.com",
            role="member",
        )
        db_session.add(inv)
        db_session.commit()

        assert inv.id is not None
        assert inv.token is not None
        assert len(inv.token) == 32
        assert inv.is_used is False
        assert inv.expires_at > inv.created_at

    def test_invitation_expires_in_24h(
        self, db_session: Session
    ) -> None:
        user = _make_user()
        db_session.add(user)
        db_session.flush()

        team = Team(owner_id=user.id, name="Test Team")
        db_session.add(team)
        db_session.flush()

        inv = TeamInvitation(
            team_id=team.id, email="x@example.com", role="member"
        )
        db_session.add(inv)
        db_session.commit()

        diff = inv.expires_at - inv.created_at
        assert timedelta(hours=23) < diff < timedelta(hours=25)

    def test_unique_token(self, db_session: Session) -> None:
        user = _make_user()
        db_session.add(user)
        db_session.flush()

        team = Team(owner_id=user.id, name="Test Team")
        db_session.add(team)
        db_session.flush()

        inv1 = TeamInvitation(
            team_id=team.id, email="a@x.com", role="member"
        )
        inv2 = TeamInvitation(
            team_id=team.id, email="b@x.com", role="member"
        )
        db_session.add_all([inv1, inv2])
        db_session.commit()

        assert inv1.token != inv2.token

    def test_invitation_schema_is_buzzreach(self) -> None:
        args = TeamInvitation.__table_args__
        if isinstance(args, tuple):
            schema_dict = next(a for a in args if isinstance(a, dict))
        else:
            schema_dict = args
        assert schema_dict["schema"] == "buzzreach"


class TestTeamContracts:
    """Contract DTOs serialize correctly."""

    def test_team_data(self) -> None:
        data = TeamData(
            id=uuid.uuid4(),
            owner_id=uuid.uuid4(),
            name="Acme",
            created_at=datetime.now(UTC),
        )
        assert data.name == "Acme"

    def test_team_member_data(self) -> None:
        data = TeamMemberData(
            id=uuid.uuid4(),
            team_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="admin",
            created_at=datetime.now(UTC),
        )
        assert data.role == "admin"

    def test_invitation_data_excludes_token(self) -> None:
        fields = TeamInvitationData.model_fields
        assert "token" not in fields

    def test_plan_limits_defined(self) -> None:
        assert PLAN_MEMBER_LIMITS["free"] == 1
        assert PLAN_MEMBER_LIMITS["pro"] == 3
        assert PLAN_MEMBER_LIMITS["premium"] == 999_999
