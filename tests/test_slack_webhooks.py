"""Tests for Slack webhook API endpoints (EXT-002).

Covers: event handling, slash commands (/buzzreach), and endpoint responses.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from contracts.opportunity.opportunity import OpportunityData


def _make_opportunity_data(**overrides: object) -> OpportunityData:
    """Build an OpportunityData DTO with sensible defaults."""
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "niche": "project-management",
        "url": "https://reddit.com/r/test/1",
        "title": "Best tool for managing projects?",
        "source": "reddit",
        "why_matched": "Mentions project management software",
        "relevance_score": 0.85,
        "draft_reply": "Check out BuzzReach for this.",
        "status": "new",
        "created_at": datetime.now(UTC),
        "delivered_at": None,
    }
    defaults.update(overrides)
    return OpportunityData(**defaults)


def _build_test_app() -> TestClient:
    """Build a TestClient with the Slack webhook router mounted."""
    from src.backend.api.slack_webhooks import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _slash_data(**overrides: str) -> dict[str, str]:
    """Build default slash command form data."""
    defaults = {
        "command": "/buzzreach",
        "text": "help",
        "user_id": "U123",
        "user_name": "testuser",
        "channel_id": "C123",
        "team_id": "T123",
        "response_url": "https://hooks.slack.com/resp",
        "trigger_id": "tr123",
    }
    defaults.update(overrides)
    return defaults


class TestSlackEventsEndpoint:
    """POST /api/v1/slack/events tests."""

    def test_url_verification_challenge(self) -> None:
        client = _build_test_app()
        resp = client.post(
            "/api/v1/slack/events",
            json={
                "type": "url_verification",
                "challenge": "abc123",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["challenge"] == "abc123"

    def test_event_callback_accepted(self) -> None:
        client = _build_test_app()
        resp = client.post(
            "/api/v1/slack/events",
            json={
                "type": "event_callback",
                "event": {
                    "type": "reaction_added",
                    "reaction": "thumbsup",
                },
                "team_id": "T123",
                "event_id": "Ev01",
            },
        )
        assert resp.status_code == 200


class TestSlashCommandHelp:
    """Slash command: /buzzreach help."""

    def test_help_returns_commands(self) -> None:
        client = _build_test_app()
        resp = client.post(
            "/api/v1/slack/slash",
            data=_slash_data(text="help"),
        )
        assert resp.status_code == 200
        assert "available commands" in resp.json()["text"].lower()

    def test_unknown_command_shows_help(self) -> None:
        client = _build_test_app()
        resp = client.post(
            "/api/v1/slack/slash",
            data=_slash_data(text="foobar"),
        )
        assert resp.status_code == 200
        assert "available commands" in resp.json()["text"].lower()


class TestSlashCommandLatest:
    """Slash command: /buzzreach latest."""

    def test_returns_opportunities(self) -> None:
        client = _build_test_app()
        with patch(
            "src.backend.api.slack_webhooks._fetch_latest_opportunities"
        ) as mock_fetch:
            mock_fetch.return_value = [
                _make_opportunity_data() for _ in range(5)
            ]
            resp = client.post(
                "/api/v1/slack/slash",
                data=_slash_data(text="latest"),
            )
        assert resp.status_code == 200
        assert len(resp.json().get("blocks", [])) > 0


class TestSlashCommandSearch:
    """Slash command: /buzzreach search [keyword]."""

    def test_returns_matching_results(self) -> None:
        client = _build_test_app()
        with patch(
            "src.backend.api.slack_webhooks._search_opportunities"
        ) as mock_search:
            mock_search.return_value = [
                _make_opportunity_data(title="CRM discussion"),
            ]
            resp = client.post(
                "/api/v1/slack/slash",
                data=_slash_data(text="search CRM"),
            )
        assert resp.status_code == 200
        assert "CRM" in str(resp.json())


class TestSlashCommandSubscribe:
    """Slash command: /buzzreach subscribe."""

    def test_subscribe_confirms(self) -> None:
        client = _build_test_app()
        resp = client.post(
            "/api/v1/slack/slash",
            data=_slash_data(text="subscribe"),
        )
        assert resp.status_code == 200
        assert "subscribed" in resp.json()["text"].lower()
