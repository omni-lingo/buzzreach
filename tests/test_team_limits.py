"""Tests for ADMIN-001: Plan limits and error codes.

Covers: plan member limits (free=1, pro=3, premium=unlimited),
error code consistency, and role change edge cases.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.backend.db.base import Base
from src.backend.models.team_member import TeamMember, TeamRole
from src.backend.models.user import User
from src.backend.services.team_errors import (
    CannotRemoveOwnerError,
    MemberNotFoundError,
    PermissionDeniedError,
    PlanLimitError,
)
from src.backend.services.team_service import (
    accept_invitation,
    change_member_role,
    create_team,
    invite_member,
    list_team_members,
    remove_member,
)


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


def _make_user(session: Session, **overrides: object) -> User:
    """Create and persist a user with sensible defaults."""
    defaults: dict[str, object] = {
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "email": f"{uuid.uuid4().hex[:8]}@example.com",
        "password_hash": "hashed_pw",
        "api_key": f"bz_{uuid.uuid4().hex[:24]}",
    }
    defaults.update(overrides)
    user = User(**defaults)
    session.add(user)
    session.commit()
    return user


def _patch_plan(plan: str):
    """Patch get_team_plan to return a specific plan."""
    return patch(
        "src.backend.services.team_helpers.get_team_plan",
        return_value=plan,
    )


class TestPlanLimits:
    """Plan member limits enforced."""

    def test_free_plan_limit_1(self, db_session: Session) -> None:
        owner = _make_user(db_session)
        with _patch_plan("free"):
            team = create_team(db_session, owner.id, "Free Team")
            with pytest.raises(PlanLimitError):
                invite_member(
                    db_session,
                    team.id,
                    "x@x.com",
                    "member",
                    owner.id,
                )

    def test_pro_plan_limit_3(self, db_session: Session) -> None:
        owner = _make_user(db_session)
        u2 = _make_user(db_session)
        u3 = _make_user(db_session)
        with _patch_plan("pro"):
            team = create_team(db_session, owner.id, "Pro Team")

            inv1 = invite_member(
                db_session, team.id, "a@x.com", "member", owner.id
            )
            accept_invitation(db_session, inv1.token, u2.id)

            inv2 = invite_member(
                db_session, team.id, "b@x.com", "member", owner.id
            )
            accept_invitation(db_session, inv2.token, u3.id)

            with pytest.raises(PlanLimitError):
                invite_member(
                    db_session,
                    team.id,
                    "c@x.com",
                    "member",
                    owner.id,
                )

    def test_premium_plan_unlimited(
        self, db_session: Session
    ) -> None:
        owner = _make_user(db_session)
        with _patch_plan("premium"):
            team = create_team(db_session, owner.id, "Premium Team")
            inv = invite_member(
                db_session, team.id, "x@x.com", "member", owner.id
            )
        assert inv is not None


class TestRoleChanges:
    """Role change operations."""

    def test_owner_can_change_role(
        self, db_session: Session
    ) -> None:
        owner = _make_user(db_session)
        member_user = _make_user(db_session)
        team = create_team(db_session, owner.id, "Acme")

        m = TeamMember(
            team_id=team.id,
            user_id=member_user.id,
            role=TeamRole.MEMBER,
            joined_at=datetime.now(UTC),
        )
        db_session.add(m)
        db_session.commit()

        updated = change_member_role(
            db_session, team.id, member_user.id, "admin", owner.id
        )
        assert updated.role == TeamRole.ADMIN

    def test_change_nonexistent_member(
        self, db_session: Session
    ) -> None:
        owner = _make_user(db_session)
        team = create_team(db_session, owner.id, "Acme")
        fake_id = uuid.uuid4()

        with pytest.raises(MemberNotFoundError):
            change_member_role(
                db_session, team.id, fake_id, "admin", owner.id
            )


class TestRemoveMember:
    """Member removal operations."""

    def test_owner_can_remove_member(
        self, db_session: Session
    ) -> None:
        owner = _make_user(db_session)
        member_user = _make_user(db_session)
        team = create_team(db_session, owner.id, "Acme")

        m = TeamMember(
            team_id=team.id,
            user_id=member_user.id,
            role=TeamRole.MEMBER,
            joined_at=datetime.now(UTC),
        )
        db_session.add(m)
        db_session.commit()

        remove_member(db_session, team.id, member_user.id, owner.id)

        members = list_team_members(db_session, team.id)
        assert len(members) == 1
        assert members[0].user_id == owner.id

    def test_cannot_remove_owner(self, db_session: Session) -> None:
        owner = _make_user(db_session)
        admin_user = _make_user(db_session)
        team = create_team(db_session, owner.id, "Acme")

        m = TeamMember(
            team_id=team.id,
            user_id=admin_user.id,
            role=TeamRole.ADMIN,
            joined_at=datetime.now(UTC),
        )
        db_session.add(m)
        db_session.commit()

        with pytest.raises(CannotRemoveOwnerError):
            remove_member(
                db_session, team.id, owner.id, admin_user.id
            )

    def test_leaving_team_removes_access(
        self, db_session: Session
    ) -> None:
        owner = _make_user(db_session)
        member_user = _make_user(db_session)
        team = create_team(db_session, owner.id, "Acme")

        m = TeamMember(
            team_id=team.id,
            user_id=member_user.id,
            role=TeamRole.MEMBER,
            joined_at=datetime.now(UTC),
        )
        db_session.add(m)
        db_session.commit()

        remove_member(db_session, team.id, member_user.id, owner.id)

        remaining = list_team_members(db_session, team.id)
        user_ids = [r.user_id for r in remaining]
        assert member_user.id not in user_ids


class TestErrorCodes:
    """All errors have proper error codes."""

    def test_team_error_has_code(self) -> None:
        err = PermissionDeniedError("test")
        assert err.code == "PERMISSION_DENIED"

    def test_plan_limit_has_code(self) -> None:
        err = PlanLimitError(3)
        assert err.code == "PLAN_LIMIT_REACHED"

    def test_cannot_remove_owner_code(self) -> None:
        err = CannotRemoveOwnerError()
        assert err.code == "CANNOT_REMOVE_OWNER"
