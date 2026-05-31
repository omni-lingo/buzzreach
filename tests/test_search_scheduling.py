"""Tests for search scheduling service (FEAT-004).

Covers: schedule time validation, schedule_search_profile,
get_scheduled_searches, and run_scheduled_search functions.
"""

import uuid

import pytest

from src.backend.errors import AppError
from src.backend.models.search_profile import SearchProfile
from src.backend.services.search_scheduler import (
    get_scheduled_searches,
    run_scheduled_search,
    schedule_search_profile,
    validate_schedule_times,
)
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


class TestScheduleValidation:
    """Tests for schedule time validation."""

    def test_valid_times(self) -> None:
        errors = validate_schedule_times(["06:00", "14:00", "23:59"])
        assert errors == []

    def test_invalid_time_format(self) -> None:
        errors = validate_schedule_times(["6am", "2pm"])
        assert len(errors) == 2

    def test_invalid_hour(self) -> None:
        errors = validate_schedule_times(["25:00"])
        assert len(errors) == 1

    def test_invalid_minute(self) -> None:
        errors = validate_schedule_times(["12:60"])
        assert len(errors) == 1

    def test_empty_list(self) -> None:
        errors = validate_schedule_times([])
        assert errors == []

    def test_midnight(self) -> None:
        errors = validate_schedule_times(["00:00"])
        assert errors == []

    def test_boundary_2359(self) -> None:
        errors = validate_schedule_times(["23:59"])
        assert errors == []


class TestScheduleSearchProfile:
    """Tests for schedule_search_profile service function."""

    def test_set_schedule(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        profile = _make_profile(user.id)
        db_session.add(profile)
        db_session.commit()

        result = schedule_search_profile(
            db_session, profile.id, user.id, ["06:00", "14:00"]
        )
        assert result.schedule_times == ["06:00", "14:00"]
        assert result.schedule_frequency == "daily"

    def test_schedule_deduplicates_times(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        profile = _make_profile(user.id)
        db_session.add(profile)
        db_session.commit()

        result = schedule_search_profile(
            db_session,
            profile.id,
            user.id,
            ["14:00", "06:00", "14:00"],
        )
        assert result.schedule_times == ["06:00", "14:00"]

    def test_schedule_invalid_time_raises(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        profile = _make_profile(user.id)
        db_session.add(profile)
        db_session.commit()

        with pytest.raises(AppError, match="Invalid time format"):
            schedule_search_profile(
                db_session, profile.id, user.id, ["bad_time"]
            )

    def test_schedule_wrong_user_raises(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        profile = _make_profile(user.id)
        db_session.add(profile)
        db_session.commit()

        other_user_id = uuid.uuid4()
        with pytest.raises(AppError, match="Search profile not found"):
            schedule_search_profile(
                db_session, profile.id, other_user_id, ["06:00"]
            )

    def test_schedule_weekly(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        profile = _make_profile(user.id)
        db_session.add(profile)
        db_session.commit()

        result = schedule_search_profile(
            db_session,
            profile.id,
            user.id,
            ["09:00"],
            frequency="weekly",
        )
        assert result.schedule_frequency == "weekly"


class TestGetScheduledSearches:
    """Tests for get_scheduled_searches service function."""

    def test_returns_enabled_with_times(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        p1 = _make_profile(
            user.id,
            name="Active",
            schedule_times=["06:00"],
            enabled=True,
        )
        p2 = _make_profile(
            user.id,
            name="Disabled",
            schedule_times=["14:00"],
            enabled=False,
        )
        p3 = _make_profile(
            user.id,
            name="No schedule",
            schedule_times=[],
            enabled=True,
        )
        db_session.add_all([p1, p2, p3])
        db_session.commit()

        results = get_scheduled_searches(db_session)
        names = [r.profile_name for r in results]
        assert "Active" in names
        assert "Disabled" not in names
        assert "No schedule" not in names

    def test_empty_when_none_scheduled(self, db_session) -> None:  # type: ignore[no-untyped-def]
        results = get_scheduled_searches(db_session)
        assert results == []


class TestRunScheduledSearch:
    """Tests for run_scheduled_search service function."""

    def test_run_enabled_profile(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        profile = _make_profile(user.id, enabled=True)
        db_session.add(profile)
        db_session.commit()

        result = run_scheduled_search(db_session, profile.id)
        assert result["profile_id"] == str(profile.id)
        assert result["skipped"] is False

    def test_run_disabled_profile_skips(self, db_session) -> None:  # type: ignore[no-untyped-def]
        user = make_user()
        db_session.add(user)
        db_session.commit()

        profile = _make_profile(user.id, enabled=False)
        db_session.add(profile)
        db_session.commit()

        result = run_scheduled_search(db_session, profile.id)
        assert result["skipped"] is True

    def test_run_nonexistent_profile_raises(self, db_session) -> None:  # type: ignore[no-untyped-def]
        with pytest.raises(AppError, match="Search profile .* not found"):
            run_scheduled_search(db_session, uuid.uuid4())
