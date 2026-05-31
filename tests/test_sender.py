"""Tests for DELIV-002: Digest sender (email / Slack).

Covers: successful send marks opportunities delivered + sets delivered_at,
calls audit_service.log and metrics_recorder.record_delivery on success,
failure raises AppError(code="DELIVERY_FAILED") and records success=False
metric without marking delivered or calling audit.
All transports (SMTP / Slack) are mocked — no live network calls.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from contracts.delivery.digest import Digest
from src.backend.db.base import Base
from src.backend.errors import AppError
from src.backend.models.opportunity import Opportunity, OpportunityStatus
from src.backend.services.delivery.sender import send_digest

# -- fixtures ----------------------------------------------------------------

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


def _make_opportunity(**overrides: object) -> Opportunity:
    """Build an Opportunity row with sensible defaults."""
    defaults: dict[str, object] = {
        "niche": "tax",
        "url": "https://reddit.com/r/tax/comments/abc123",
        "title": "How do I reduce my IRS penalty?",
        "source": "reddit",
        "why_matched": "User asking about IRS penalty reduction",
        "relevance_score": 0.85,
        "draft_reply": "Check out the first-time abatement option.",
    }
    defaults.update(overrides)
    return Opportunity(**defaults)


def _make_digest(opportunity_ids: list[uuid.UUID]) -> Digest:
    """Build a Digest with the given opportunity IDs."""
    return Digest(
        subject="BuzzReach: 2 new opportunities",
        text_body="Opportunity details here.",
        html_body="<p>Opportunity details here.</p>",
        opportunity_ids=opportunity_ids,
    )


def _smtp_settings() -> MagicMock:
    """Return a Settings-like mock with SMTP configured."""
    settings = MagicMock()
    settings.smtp_host = "smtp.example.com"
    settings.smtp_port = 587
    settings.smtp_username = "user@example.com"
    settings.smtp_password = "secret"
    settings.smtp_from_email = "noreply@buzzreach.app"
    settings.slack_webhook_url = ""
    return settings


def _slack_settings() -> MagicMock:
    """Return a Settings-like mock with Slack configured."""
    settings = MagicMock()
    settings.smtp_host = ""
    settings.smtp_port = 587
    settings.smtp_username = ""
    settings.smtp_password = ""
    settings.smtp_from_email = ""
    settings.slack_webhook_url = "https://hooks.slack.com/services/T/B/X"
    return settings


def _both_settings() -> MagicMock:
    """Return a Settings-like mock with both SMTP and Slack configured."""
    settings = MagicMock()
    settings.smtp_host = "smtp.example.com"
    settings.smtp_port = 587
    settings.smtp_username = "user@example.com"
    settings.smtp_password = "secret"
    settings.smtp_from_email = "noreply@buzzreach.app"
    settings.slack_webhook_url = "https://hooks.slack.com/services/T/B/X"
    return settings


# -- successful email send ---------------------------------------------------

class TestSendDigestEmailSuccess:
    """Successful email send transitions opportunities and calls audit."""

    @patch("src.backend.services.delivery.sender._send_email")
    def test_marks_opportunities_delivered(
        self, mock_email: MagicMock, db_session: Session
    ) -> None:
        opp = _make_opportunity()
        db_session.add(opp)
        db_session.commit()
        digest = _make_digest([opp.id])
        audit = MagicMock()
        metrics = MagicMock()

        send_digest(digest, _smtp_settings(), audit, metrics, db_session)

        db_session.refresh(opp)
        assert opp.status == OpportunityStatus.DELIVERED

    @patch("src.backend.services.delivery.sender._send_email")
    def test_sets_delivered_at(
        self, mock_email: MagicMock, db_session: Session
    ) -> None:
        opp = _make_opportunity()
        db_session.add(opp)
        db_session.commit()
        digest = _make_digest([opp.id])
        audit = MagicMock()
        metrics = MagicMock()

        send_digest(digest, _smtp_settings(), audit, metrics, db_session)

        db_session.refresh(opp)
        assert opp.delivered_at is not None

    @patch("src.backend.services.delivery.sender._send_email")
    def test_calls_audit_log(
        self, mock_email: MagicMock, db_session: Session
    ) -> None:
        opp = _make_opportunity()
        db_session.add(opp)
        db_session.commit()
        digest = _make_digest([opp.id])
        audit = MagicMock()
        metrics = MagicMock()

        send_digest(digest, _smtp_settings(), audit, metrics, db_session)

        audit.log.assert_called_once_with(
            "digest_sent",
            "digest",
            change_summary="Sent 1 opportunities via email",
        )

    @patch("src.backend.services.delivery.sender._send_email")
    def test_records_success_metric(
        self, mock_email: MagicMock, db_session: Session
    ) -> None:
        opp = _make_opportunity(niche="tax")
        db_session.add(opp)
        db_session.commit()
        digest = _make_digest([opp.id])
        audit = MagicMock()
        metrics = MagicMock()

        send_digest(digest, _smtp_settings(), audit, metrics, db_session)

        metrics.record_delivery.assert_called_once_with(
            "tax", 1, success=True,
        )

    @patch("src.backend.services.delivery.sender._send_email")
    def test_calls_smtp_transport(
        self, mock_email: MagicMock, db_session: Session
    ) -> None:
        opp = _make_opportunity()
        db_session.add(opp)
        db_session.commit()
        digest = _make_digest([opp.id])
        audit = MagicMock()
        metrics = MagicMock()

        send_digest(digest, _smtp_settings(), audit, metrics, db_session)

        mock_email.assert_called_once()


# -- successful Slack send ---------------------------------------------------

class TestSendDigestSlackSuccess:
    """Successful Slack send transitions opportunities and calls audit."""

    @patch("src.backend.services.delivery.sender._send_slack")
    def test_marks_opportunities_delivered(
        self, mock_slack: MagicMock, db_session: Session
    ) -> None:
        opp = _make_opportunity()
        db_session.add(opp)
        db_session.commit()
        digest = _make_digest([opp.id])
        audit = MagicMock()
        metrics = MagicMock()

        send_digest(digest, _slack_settings(), audit, metrics, db_session)

        db_session.refresh(opp)
        assert opp.status == OpportunityStatus.DELIVERED

    @patch("src.backend.services.delivery.sender._send_slack")
    def test_calls_audit_with_slack_channel(
        self, mock_slack: MagicMock, db_session: Session
    ) -> None:
        opp = _make_opportunity()
        db_session.add(opp)
        db_session.commit()
        digest = _make_digest([opp.id])
        audit = MagicMock()
        metrics = MagicMock()

        send_digest(digest, _slack_settings(), audit, metrics, db_session)

        audit.log.assert_called_once_with(
            "digest_sent",
            "digest",
            change_summary="Sent 1 opportunities via slack",
        )

    @patch("src.backend.services.delivery.sender._send_slack")
    def test_calls_slack_transport(
        self, mock_slack: MagicMock, db_session: Session
    ) -> None:
        opp = _make_opportunity()
        db_session.add(opp)
        db_session.commit()
        digest = _make_digest([opp.id])
        audit = MagicMock()
        metrics = MagicMock()

        send_digest(digest, _slack_settings(), audit, metrics, db_session)

        mock_slack.assert_called_once()


# -- both channels configured -----------------------------------------------

class TestSendDigestBothChannels:
    """When both SMTP and Slack are configured, both are used."""

    @patch("src.backend.services.delivery.sender._send_slack")
    @patch("src.backend.services.delivery.sender._send_email")
    def test_sends_via_both(
        self,
        mock_email: MagicMock,
        mock_slack: MagicMock,
        db_session: Session,
    ) -> None:
        opp = _make_opportunity()
        db_session.add(opp)
        db_session.commit()
        digest = _make_digest([opp.id])
        audit = MagicMock()
        metrics = MagicMock()

        send_digest(digest, _both_settings(), audit, metrics, db_session)

        mock_email.assert_called_once()
        mock_slack.assert_called_once()


# -- send failure ------------------------------------------------------------

class TestSendDigestFailure:
    """Transport failure raises AppError and does not mark delivered."""

    @patch("src.backend.services.delivery.sender._send_email")
    def test_raises_app_error(
        self, mock_email: MagicMock, db_session: Session
    ) -> None:
        mock_email.side_effect = RuntimeError("SMTP connection refused")
        opp = _make_opportunity()
        db_session.add(opp)
        db_session.commit()
        digest = _make_digest([opp.id])
        audit = MagicMock()
        metrics = MagicMock()

        with pytest.raises(AppError) as exc_info:
            send_digest(
                digest, _smtp_settings(), audit, metrics, db_session,
            )

        assert exc_info.value.code == "DELIVERY_FAILED"

    @patch("src.backend.services.delivery.sender._send_email")
    def test_leaves_status_new(
        self, mock_email: MagicMock, db_session: Session
    ) -> None:
        mock_email.side_effect = RuntimeError("SMTP connection refused")
        opp = _make_opportunity()
        db_session.add(opp)
        db_session.commit()
        digest = _make_digest([opp.id])
        audit = MagicMock()
        metrics = MagicMock()

        with pytest.raises(AppError):
            send_digest(
                digest, _smtp_settings(), audit, metrics, db_session,
            )

        db_session.refresh(opp)
        assert opp.status == OpportunityStatus.NEW

    @patch("src.backend.services.delivery.sender._send_email")
    def test_does_not_set_delivered_at(
        self, mock_email: MagicMock, db_session: Session
    ) -> None:
        mock_email.side_effect = RuntimeError("SMTP connection refused")
        opp = _make_opportunity()
        db_session.add(opp)
        db_session.commit()
        digest = _make_digest([opp.id])
        audit = MagicMock()
        metrics = MagicMock()

        with pytest.raises(AppError):
            send_digest(
                digest, _smtp_settings(), audit, metrics, db_session,
            )

        db_session.refresh(opp)
        assert opp.delivered_at is None

    @patch("src.backend.services.delivery.sender._send_email")
    def test_does_not_call_audit(
        self, mock_email: MagicMock, db_session: Session
    ) -> None:
        mock_email.side_effect = RuntimeError("SMTP connection refused")
        opp = _make_opportunity()
        db_session.add(opp)
        db_session.commit()
        digest = _make_digest([opp.id])
        audit = MagicMock()
        metrics = MagicMock()

        with pytest.raises(AppError):
            send_digest(
                digest, _smtp_settings(), audit, metrics, db_session,
            )

        audit.log.assert_not_called()

    @patch("src.backend.services.delivery.sender._send_email")
    def test_records_failure_metric(
        self, mock_email: MagicMock, db_session: Session
    ) -> None:
        mock_email.side_effect = RuntimeError("SMTP connection refused")
        opp = _make_opportunity(niche="tax")
        db_session.add(opp)
        db_session.commit()
        digest = _make_digest([opp.id])
        audit = MagicMock()
        metrics = MagicMock()

        with pytest.raises(AppError):
            send_digest(
                digest, _smtp_settings(), audit, metrics, db_session,
            )

        metrics.record_delivery.assert_called_once_with(
            "tax", 1, success=False,
        )


# -- empty digest ------------------------------------------------------------

class TestSendDigestEmpty:
    """Empty digest (no opportunity_ids) is a no-op."""

    def test_no_error_on_empty_digest(self, db_session: Session) -> None:
        digest = _make_digest([])
        audit = MagicMock()
        metrics = MagicMock()

        send_digest(digest, _smtp_settings(), audit, metrics, db_session)

        audit.log.assert_not_called()
        metrics.record_delivery.assert_not_called()
