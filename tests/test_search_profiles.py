"""Tests for SearchProfile model and plan limits (FEAT-004).

Covers: SearchProfile ORM CRUD, profile enable/disable,
plan limit enforcement, and contract type validation.
"""

import uuid

import pytest

from contracts.features.search_profile import (
    SEARCH_PROFILE_LIMITS,
    ScheduleConfig,
    ScheduledSearchInfo,
    SearchProfileData,
)
from src.backend.errors import AppError
from src.backend.models.search_profile import SearchProfile
from src.backend.services.search_scheduler import check_profile_limit
from tests.conftest import make_user


def _make_profile(user_id: uuid.UUID, **overrides: object) -> SearchProfile:
    """Build a SearchProfile with sensible defaults."""
    defaults: dict[str, object] = {
        "user_id": user_id,
        "name": "Test Profile",
        "keywords": ["saas", "crm"],
        "platforms": ["reddit", "quora"],
        "languages": ["en"],
        "enabled": True,
    }
    defaults.update(overrides)
    return SearchProfile(**defaults)


class TestSearchProfileModel:
    """Tests for SearchProfile ORM model persistence."""

    def test_create_profile(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        profile = _make_profile(user.id, name="IRS Tax")
        db_session.add(profile)
        db_session.commit()

        loaded = (
            db_session.query(SearchProfile)
            .filter_by(id=profile.id)
            .one()
        )
        assert loaded.name == "IRS Tax"
        assert loaded.keywords == ["saas", "crm"]
        assert loaded.enabled is True

    def test_multiple_profiles_per_user(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        p1 = _make_profile(user.id, name="Profile 1")
        p2 = _make_profile(user.id, name="Profile 2")
        db_session.add_all([p1, p2])
        db_session.commit()

        count = (
            db_session.query(SearchProfile)
            .filter_by(user_id=user.id)
            .count()
        )
        assert count == 2

    def test_disable_profile(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        profile = _make_profile(user.id, enabled=True)
        db_session.add(profile)
        db_session.commit()

        profile.enabled = False
        db_session.commit()

        loaded = (
            db_session.query(SearchProfile)
            .filter_by(id=profile.id)
            .one()
        )
        assert loaded.enabled is False

    def test_profile_with_schedule(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        profile = _make_profile(
            user.id,
            schedule_times=["06:00", "14:00"],
            schedule_frequency="daily",
        )
        db_session.add(profile)
        db_session.commit()

        loaded = (
            db_session.query(SearchProfile)
            .filter_by(id=profile.id)
            .one()
        )
        assert loaded.schedule_times == ["06:00", "14:00"]
        assert loaded.schedule_frequency == "daily"

    def test_delete_profile(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        profile = _make_profile(user.id)
        db_session.add(profile)
        db_session.commit()

        pid = profile.id
        db_session.delete(profile)
        db_session.commit()

        loaded = (
            db_session.query(SearchProfile)
            .filter_by(id=pid)
            .first()
        )
        assert loaded is None


class TestProfileLimits:
    """Tests for plan-based profile limit enforcement."""

    def test_free_plan_limit(self) -> None:
        assert SEARCH_PROFILE_LIMITS["free"] == 1

    def test_pro_plan_limit(self) -> None:
        assert SEARCH_PROFILE_LIMITS["pro"] == 5

    def test_premium_plan_limit(self) -> None:
        assert SEARCH_PROFILE_LIMITS["premium"] == 100

    def test_check_limit_allows(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()
        check_profile_limit(db_session, user.id, "free")

    def test_check_limit_blocks(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        profile = _make_profile(user.id)
        db_session.add(profile)
        db_session.commit()

        with pytest.raises(AppError, match="max 1 search profiles"):
            check_profile_limit(db_session, user.id, "free")

    def test_pro_allows_multiple(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        for i in range(4):
            db_session.add(
                _make_profile(user.id, name=f"Profile {i}")
            )
        db_session.commit()

        check_profile_limit(db_session, user.id, "pro")


class TestContracts:
    """Tests for cross-module contract types."""

    def test_search_profile_data(self) -> None:
        data = SearchProfileData(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Test",
            keywords=["saas"],
            platforms=["reddit"],
            languages=["en"],
            enabled=True,
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        assert data.name == "Test"

    def test_schedule_config_validation(self) -> None:
        cfg = ScheduleConfig(
            profile_id=uuid.uuid4(),
            times=["06:00", "14:00"],
            frequency="daily",
        )
        assert cfg.frequency == "daily"

    def test_scheduled_search_info(self) -> None:
        info = ScheduledSearchInfo(
            profile_id=uuid.uuid4(),
            profile_name="Test",
            times=["06:00"],
            frequency="daily",
            enabled=True,
        )
        assert info.profile_name == "Test"
