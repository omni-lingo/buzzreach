"""Tests for ADMIN-001: Team service logic and integration.

Covers: create team, invite/accept, single-use tokens, expiry,
and permission checks. Plan limits and role changes are in
test_team_limits.py.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.backend.db.base import Base
from src.backend.models.team_member import TeamMember, TeamRole
from src.backend.models.user import User
from src.backend.services.team_errors import (
    AlreadyMemberError,
    InvitationExpiredError,
    InvitationUsedError,
    PermissionDeniedError,
)
from src.backend.services.team_service import (
    accept_invitation,
    change_member_role,
    create_team,
    invite_member,
    list_team_members,
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
    """Patch _get_team_plan to return a specific plan."""
    return patch(
        "src.backend.services.team_helpers.get_team_plan",
        return_value=plan,
    )


class TestCreateTeam:
    """Owner can create a team and becomes its first member."""

    def test_create_team_success(self, db_session: Session) -> None:
        owner = _make_user(db_session)
        team = create_team(db_session, owner.id, "Acme Corp")

        assert team.id is not None
        assert team.name == "Acme Corp"
        assert team.owner_id == owner.id

    def test_owner_auto_added_as_member(
        self, db_session: Session
    ) -> None:
        owner = _make_user(db_session)
        team = create_team(db_session, owner.id, "Acme Corp")

        members = list_team_members(db_session, team.id)
        assert len(members) == 1
        assert members[0].user_id == owner.id
        assert members[0].role == TeamRole.OWNER

    def test_member_list_shows_all_users(
        self, db_session: Session
    ) -> None:
        owner = _make_user(db_session)
        user2 = _make_user(db_session)
        team = create_team(db_session, owner.id, "Team X")

        m2 = TeamMember(
            team_id=team.id,
            user_id=user2.id,
            role=TeamRole.MEMBER,
            joined_at=datetime.now(UTC),
        )
        db_session.add(m2)
        db_session.commit()

        members = list_team_members(db_session, team.id)
        assert len(members) == 2


class TestInviteMember:
    """Invitation flow: create, accept, single-use, expiry."""

    def test_invite_creates_token(self, db_session: Session) -> None:
        owner = _make_user(db_session)
        with _patch_plan("premium"):
            team = create_team(db_session, owner.id, "Acme")
            inv = invite_member(
                db_session, team.id, "new@x.com", "member", owner.id
            )

        assert inv.token is not None
        assert inv.email == "new@x.com"
        assert inv.is_used is False

    def test_accept_invitation(self, db_session: Session) -> None:
        owner = _make_user(db_session)
        joiner = _make_user(db_session)
        with _patch_plan("premium"):
            team = create_team(db_session, owner.id, "Acme")
            inv = invite_member(
                db_session, team.id, "j@x.com", "member", owner.id
            )
            member = accept_invitation(db_session, inv.token, joiner.id)

        assert member.team_id == team.id
        assert member.user_id == joiner.id
        assert member.role == TeamRole.MEMBER

    def test_token_single_use(self, db_session: Session) -> None:
        owner = _make_user(db_session)
        joiner = _make_user(db_session)
        joiner2 = _make_user(db_session)
        with _patch_plan("premium"):
            team = create_team(db_session, owner.id, "Acme")
            inv = invite_member(
                db_session, team.id, "j@x.com", "member", owner.id
            )
            accept_invitation(db_session, inv.token, joiner.id)

            with pytest.raises(InvitationUsedError):
                accept_invitation(db_session, inv.token, joiner2.id)

    def test_expired_token_rejected(
        self, db_session: Session
    ) -> None:
        owner = _make_user(db_session)
        joiner = _make_user(db_session)
        with _patch_plan("premium"):
            team = create_team(db_session, owner.id, "Acme")
            inv = invite_member(
                db_session, team.id, "j@x.com", "member", owner.id
            )

        inv.expires_at = datetime.now(UTC) - timedelta(hours=1)
        db_session.commit()

        with _patch_plan("premium"), pytest.raises(InvitationExpiredError):
            accept_invitation(db_session, inv.token, joiner.id)

    def test_already_member_rejected(
        self, db_session: Session
    ) -> None:
        owner = _make_user(db_session)
        with _patch_plan("premium"):
            team = create_team(db_session, owner.id, "Acme")
            inv = invite_member(
                db_session, team.id, "o@x.com", "member", owner.id
            )

            with pytest.raises(AlreadyMemberError):
                accept_invitation(db_session, inv.token, owner.id)


class TestPermissions:
    """Only owner/admin can invite, change roles, remove members."""

    def test_member_cannot_invite(self, db_session: Session) -> None:
        owner = _make_user(db_session)
        member_user = _make_user(db_session)
        with _patch_plan("premium"):
            team = create_team(db_session, owner.id, "Acme")

        m = TeamMember(
            team_id=team.id,
            user_id=member_user.id,
            role=TeamRole.MEMBER,
            joined_at=datetime.now(UTC),
        )
        db_session.add(m)
        db_session.commit()

        with _patch_plan("premium"), pytest.raises(PermissionDeniedError):
            invite_member(
                db_session,
                team.id,
                "x@x.com",
                "member",
                member_user.id,
            )

    def test_admin_can_invite(self, db_session: Session) -> None:
        owner = _make_user(db_session)
        admin_user = _make_user(db_session)
        with _patch_plan("premium"):
            team = create_team(db_session, owner.id, "Acme")

        m = TeamMember(
            team_id=team.id,
            user_id=admin_user.id,
            role=TeamRole.ADMIN,
            joined_at=datetime.now(UTC),
        )
        db_session.add(m)
        db_session.commit()

        with _patch_plan("premium"):
            inv = invite_member(
                db_session, team.id, "x@x.com", "member", admin_user.id
            )
        assert inv is not None

    def test_cannot_change_owner_role(
        self, db_session: Session
    ) -> None:
        owner = _make_user(db_session)
        admin_user = _make_user(db_session)
        with _patch_plan("premium"):
            team = create_team(db_session, owner.id, "Acme")

        m = TeamMember(
            team_id=team.id,
            user_id=admin_user.id,
            role=TeamRole.ADMIN,
            joined_at=datetime.now(UTC),
        )
        db_session.add(m)
        db_session.commit()

        with pytest.raises(PermissionDeniedError):
            change_member_role(
                db_session, team.id, owner.id, "member", admin_user.id
            )

    def test_admin_cannot_promote_to_owner(
        self, db_session: Session
    ) -> None:
        owner = _make_user(db_session)
        admin_user = _make_user(db_session)
        member_user = _make_user(db_session)
        with _patch_plan("premium"):
            team = create_team(db_session, owner.id, "Acme")

        db_session.add_all([
            TeamMember(
                team_id=team.id,
                user_id=admin_user.id,
                role=TeamRole.ADMIN,
                joined_at=datetime.now(UTC),
            ),
            TeamMember(
                team_id=team.id,
                user_id=member_user.id,
                role=TeamRole.MEMBER,
                joined_at=datetime.now(UTC),
            ),
        ])
        db_session.commit()

        with pytest.raises(PermissionDeniedError):
            change_member_role(
                db_session,
                team.id,
                member_user.id,
                "owner",
                admin_user.id,
            )


