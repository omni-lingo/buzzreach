"""Tests for post-action tracking and conversion analytics (FEAT-003).

Covers: OpportunityAction model, action_tracker service (log_action,
get_action_history, get_funnel_counts, delete_user_actions), and
API routes (POST/GET /api/v1/opportunities/{id}/actions, DELETE actions,
GET /api/v1/analytics/funnel).
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from contracts.features.opportunity_action import ActionType
from src.backend.errors import AppError
from src.backend.models.opportunity import Opportunity
from src.backend.models.opportunity_action import OpportunityAction
from src.backend.services.action_tracker import (
    delete_user_actions,
    get_action_history,
    get_funnel_counts,
    log_action,
)


def _make_opp(session: Session, **overrides: object) -> Opportunity:
    """Persist an opportunity with sensible defaults."""
    defaults: dict[str, object] = {
        "niche": "saas",
        "url": f"https://reddit.com/r/saas/{uuid.uuid4().hex[:8]}",
        "title": "Looking for a tool",
        "source": "reddit",
        "why_matched": "mentions tools",
        "relevance_score": 0.8,
        "draft_reply": "Try our tool...",
    }
    defaults.update(overrides)
    opp = Opportunity(**defaults)
    session.add(opp)
    session.commit()
    return opp


def _stub_user_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


# ── Model tests ──────────────────────────────────────────────────────


class TestOpportunityActionModel:
    """Tests for the OpportunityAction ORM model."""

    def test_create_action(self, db_session: Session) -> None:
        opp = _make_opp(db_session)
        action = OpportunityAction(
            opportunity_id=opp.id,
            user_id=_stub_user_id(),
            action_type=ActionType.VIEWED,
        )
        db_session.add(action)
        db_session.commit()

        loaded = (
            db_session.query(OpportunityAction)
            .filter_by(id=action.id)
            .one()
        )
        assert loaded.action_type == "viewed"
        assert loaded.posted_url is None
        assert loaded.created_at is not None

    def test_create_posted_action_with_url(
        self, db_session: Session
    ) -> None:
        opp = _make_opp(db_session)
        action = OpportunityAction(
            opportunity_id=opp.id,
            user_id=_stub_user_id(),
            action_type=ActionType.POSTED,
            posted_url="https://reddit.com/r/saas/comment/abc",
        )
        db_session.add(action)
        db_session.commit()

        loaded = (
            db_session.query(OpportunityAction)
            .filter_by(id=action.id)
            .one()
        )
        assert loaded.action_type == "posted"
        assert loaded.posted_url == "https://reddit.com/r/saas/comment/abc"

    def test_action_type_values(self) -> None:
        assert ActionType.VIEWED == "viewed"
        assert ActionType.COPIED == "copied"
        assert ActionType.POSTED == "posted"
        assert ActionType.ARCHIVED == "archived"


# ── Service tests ────────────────────────────────────────────────────


class TestLogAction:
    """Tests for log_action service function."""

    def test_log_viewed(self, db_session: Session) -> None:
        opp = _make_opp(db_session)
        user_id = _stub_user_id()
        action = log_action(
            db_session, opp.id, user_id, ActionType.VIEWED
        )
        assert action.action_type == "viewed"
        assert action.opportunity_id == opp.id

    def test_log_posted_with_url(self, db_session: Session) -> None:
        opp = _make_opp(db_session)
        user_id = _stub_user_id()
        url = "https://reddit.com/r/saas/reply/xyz"
        action = log_action(
            db_session, opp.id, user_id, ActionType.POSTED, posted_url=url
        )
        assert action.action_type == "posted"
        assert action.posted_url == url

    def test_log_invalid_opportunity_raises(
        self, db_session: Session
    ) -> None:
        fake_id = uuid.uuid4()
        with pytest.raises(AppError) as exc_info:
            log_action(
                db_session, fake_id, _stub_user_id(), ActionType.VIEWED
            )
        assert exc_info.value.code == "OPPORTUNITY_NOT_FOUND"


class TestGetActionHistory:
    """Tests for get_action_history service function."""

    def test_returns_actions_for_opportunity(
        self, db_session: Session
    ) -> None:
        opp = _make_opp(db_session)
        user_id = _stub_user_id()
        log_action(db_session, opp.id, user_id, ActionType.VIEWED)
        log_action(db_session, opp.id, user_id, ActionType.COPIED)

        history = get_action_history(db_session, opp.id, user_id)
        assert len(history) == 2

    def test_user_isolation(self, db_session: Session) -> None:
        opp = _make_opp(db_session)
        user_a = _stub_user_id()
        user_b = uuid.UUID("00000000-0000-0000-0000-000000000002")
        log_action(db_session, opp.id, user_a, ActionType.VIEWED)
        log_action(db_session, opp.id, user_b, ActionType.COPIED)

        history_a = get_action_history(db_session, opp.id, user_a)
        assert len(history_a) == 1
        assert history_a[0].action_type == "viewed"

    def test_ordered_by_created_at(self, db_session: Session) -> None:
        opp = _make_opp(db_session)
        user_id = _stub_user_id()
        log_action(db_session, opp.id, user_id, ActionType.VIEWED)
        log_action(db_session, opp.id, user_id, ActionType.COPIED)
        log_action(db_session, opp.id, user_id, ActionType.POSTED)

        history = get_action_history(db_session, opp.id, user_id)
        assert [a.action_type for a in history] == [
            "viewed",
            "copied",
            "posted",
        ]


class TestGetFunnelCounts:
    """Tests for get_funnel_counts (analytics)."""

    def test_basic_funnel(self, db_session: Session) -> None:
        user_id = _stub_user_id()
        opp1 = _make_opp(db_session, source="reddit")
        opp2 = _make_opp(db_session, source="reddit")
        opp3 = _make_opp(db_session, source="reddit")

        log_action(db_session, opp1.id, user_id, ActionType.VIEWED)
        log_action(db_session, opp2.id, user_id, ActionType.VIEWED)
        log_action(db_session, opp3.id, user_id, ActionType.VIEWED)
        log_action(db_session, opp1.id, user_id, ActionType.COPIED)
        log_action(db_session, opp2.id, user_id, ActionType.COPIED)
        log_action(db_session, opp1.id, user_id, ActionType.POSTED)

        funnel = get_funnel_counts(db_session, user_id)
        assert funnel["viewed"] == 3
        assert funnel["copied"] == 2
        assert funnel["posted"] == 1

    def test_no_double_counting(self, db_session: Session) -> None:
        user_id = _stub_user_id()
        opp = _make_opp(db_session)
        log_action(db_session, opp.id, user_id, ActionType.VIEWED)
        log_action(db_session, opp.id, user_id, ActionType.VIEWED)

        funnel = get_funnel_counts(db_session, user_id)
        assert funnel["viewed"] == 1

    def test_filter_by_platform(self, db_session: Session) -> None:
        user_id = _stub_user_id()
        opp_r = _make_opp(db_session, source="reddit")
        opp_q = _make_opp(db_session, source="quora")
        log_action(db_session, opp_r.id, user_id, ActionType.VIEWED)
        log_action(db_session, opp_q.id, user_id, ActionType.VIEWED)

        funnel = get_funnel_counts(
            db_session, user_id, platform="reddit"
        )
        assert funnel["viewed"] == 1

    def test_filter_by_date_range(self, db_session: Session) -> None:
        user_id = _stub_user_id()
        opp = _make_opp(db_session)
        action = log_action(
            db_session, opp.id, user_id, ActionType.VIEWED
        )
        action.created_at = datetime.now(UTC) - timedelta(days=10)
        db_session.commit()

        now = datetime.now(UTC)
        funnel = get_funnel_counts(
            db_session,
            user_id,
            date_from=now - timedelta(days=5),
            date_to=now,
        )
        assert funnel["viewed"] == 0

    def test_conversion_rate(self, db_session: Session) -> None:
        user_id = _stub_user_id()
        for _ in range(4):
            opp = _make_opp(db_session)
            log_action(db_session, opp.id, user_id, ActionType.VIEWED)
        opp_posted = _make_opp(db_session)
        log_action(
            db_session, opp_posted.id, user_id, ActionType.VIEWED
        )
        log_action(
            db_session, opp_posted.id, user_id, ActionType.POSTED
        )

        funnel = get_funnel_counts(db_session, user_id)
        assert funnel["viewed"] == 5
        assert funnel["posted"] == 1
        expected_rate = 1 / 5
        assert abs(funnel["conversion_rate"] - expected_rate) < 0.001


class TestDeleteUserActions:
    """Tests for GDPR delete_user_actions."""

    def test_deletes_all_user_actions(self, db_session: Session) -> None:
        user_id = _stub_user_id()
        opp = _make_opp(db_session)
        log_action(db_session, opp.id, user_id, ActionType.VIEWED)
        log_action(db_session, opp.id, user_id, ActionType.COPIED)

        count = delete_user_actions(db_session, user_id)
        assert count == 2

        remaining = (
            db_session.query(OpportunityAction)
            .filter_by(user_id=user_id)
            .count()
        )
        assert remaining == 0

    def test_does_not_delete_other_users(
        self, db_session: Session
    ) -> None:
        user_a = _stub_user_id()
        user_b = uuid.UUID("00000000-0000-0000-0000-000000000002")
        opp = _make_opp(db_session)
        log_action(db_session, opp.id, user_a, ActionType.VIEWED)
        log_action(db_session, opp.id, user_b, ActionType.VIEWED)

        delete_user_actions(db_session, user_a)
        remaining = (
            db_session.query(OpportunityAction)
            .filter_by(user_id=user_b)
            .count()
        )
        assert remaining == 1
