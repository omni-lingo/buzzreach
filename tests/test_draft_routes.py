"""Tests for FEAT-001 — Draft API routes (save, discard, regenerate).

Covers:
- PUT /api/v1/opportunities/{id}/draft — save edited draft
- DELETE /api/v1/opportunities/{id}/draft — discard edits
- POST /api/v1/opportunities/{id}/regenerate — AI re-draft
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from contracts.features.draft_edit import (
    DraftEditRequest,
    DraftRegenerateRequest,
    DraftTone,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_opportunity_row() -> MagicMock:
    """Create a mock Opportunity ORM object."""
    opp = MagicMock()
    opp.id = uuid.uuid4()
    opp.niche = "tax"
    opp.url = "https://reddit.com/r/tax/comments/abc123"
    opp.title = "Help with IRS CP14 notice"
    opp.source = "reddit"
    opp.why_matched = "Mentions IRS penalty"
    opp.relevance_score = 0.85
    opp.draft_reply = "Original AI-generated draft text."
    opp.edited_draft = None
    opp.status = MagicMock(value="new")
    opp.created_at = datetime.now(UTC)
    opp.delivered_at = None
    return opp


# ---------------------------------------------------------------------------
# Save draft
# ---------------------------------------------------------------------------

class TestSaveDraftEndpoint:
    """PUT /api/v1/opportunities/{id}/draft saves the edit."""

    def test_save_draft_updates_edited_field(self) -> None:
        opp = _make_opportunity_row()
        opp.edited_draft = None

        with (
            patch("src.backend.api.v1.draft_routes._audit_log") as mock_audit,
        ):
            from src.backend.api.v1.draft_routes import _save_draft_logic

            session = MagicMock()
            _save_draft_logic(
                opp=opp,
                body=DraftEditRequest(edited_text="My edited version"),
                session=session,
                user_id="user-123",
                ip_address="127.0.0.1",
            )

        assert opp.edited_draft == "My edited version"
        session.commit.assert_called_once()
        mock_audit.assert_called_once()

    def test_save_draft_returns_draft_response(self) -> None:
        opp = _make_opportunity_row()
        opp.draft_reply = "Original text"

        with patch("src.backend.api.v1.draft_routes._audit_log"):
            from src.backend.api.v1.draft_routes import _save_draft_logic

            session = MagicMock()
            result = _save_draft_logic(
                opp=opp,
                body=DraftEditRequest(edited_text="Edited text"),
                session=session,
                user_id="user-123",
                ip_address=None,
            )

        assert result.original_draft == "Original text"
        assert result.current_text == "Edited text"


# ---------------------------------------------------------------------------
# Discard edits
# ---------------------------------------------------------------------------

class TestDiscardDraft:
    """Discarding sets edited_draft back to None."""

    def test_discard_clears_edited_draft(self) -> None:
        opp = _make_opportunity_row()
        opp.draft_reply = "Original"
        opp.edited_draft = "Edited"

        with patch("src.backend.api.v1.draft_routes._audit_log"):
            from src.backend.api.v1.draft_routes import _discard_draft_logic

            session = MagicMock()
            result = _discard_draft_logic(
                opp=opp,
                session=session,
                user_id="user-123",
                ip_address=None,
            )

        assert opp.edited_draft is None
        assert result.current_text == "Original"


# ---------------------------------------------------------------------------
# Regenerate draft
# ---------------------------------------------------------------------------

class TestRegenerateDraftEndpoint:
    """POST /api/v1/opportunities/{id}/regenerate calls AI."""

    def test_regenerate_returns_new_draft(self) -> None:
        opp = _make_opportunity_row()
        opp.draft_reply = "Old draft"

        with (
            patch("src.backend.api.v1.draft_routes._audit_log"),
            patch(
                "src.backend.api.v1.draft_routes._build_regenerate_deps",
                return_value=(MagicMock(), MagicMock(), MagicMock()),
            ),
            patch(
                "src.backend.api.v1.draft_routes.regenerate_draft",
                return_value="Brand new AI draft",
            ),
        ):
            from src.backend.api.v1.draft_routes import (
                _regenerate_draft_logic,
            )

            session = MagicMock()
            result = _regenerate_draft_logic(
                opp=opp,
                body=DraftRegenerateRequest(tone=DraftTone.CASUAL),
                session=session,
                user_id="user-123",
                ip_address="127.0.0.1",
            )

        assert opp.draft_reply == "Brand new AI draft"
        assert opp.edited_draft is None
        assert result.current_text == "Brand new AI draft"

    def test_regenerate_clears_previous_edits(self) -> None:
        opp = _make_opportunity_row()
        opp.draft_reply = "Old draft"
        opp.edited_draft = "Previous edit"

        with (
            patch("src.backend.api.v1.draft_routes._audit_log"),
            patch(
                "src.backend.api.v1.draft_routes._build_regenerate_deps",
                return_value=(MagicMock(), MagicMock(), MagicMock()),
            ),
            patch(
                "src.backend.api.v1.draft_routes.regenerate_draft",
                return_value="Fresh AI draft",
            ),
        ):
            from src.backend.api.v1.draft_routes import (
                _regenerate_draft_logic,
            )

            session = MagicMock()
            result = _regenerate_draft_logic(
                opp=opp,
                body=DraftRegenerateRequest(tone=DraftTone.PROFESSIONAL),
                session=session,
                user_id="user-456",
                ip_address=None,
            )

        assert opp.edited_draft is None
        assert result.original_draft == "Fresh AI draft"
