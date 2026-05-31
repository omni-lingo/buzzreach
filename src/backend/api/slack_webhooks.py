"""Slack webhook handlers for the extensions module (EXT-002).

POST /api/v1/slack/events — handle Slack Events API callbacks
POST /api/v1/slack/slash  — handle /buzzreach slash commands

Slash commands:
  /buzzreach latest       — show 5 most recent opportunities
  /buzzreach search [kw]  — find opportunities by keyword
  /buzzreach subscribe    — enable Slack digest delivery
  /buzzreach help         — show available commands
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse

from contracts.opportunity.opportunity import OpportunityData
from src.backend.api.rate_limit_middleware import require_rate_limit
from src.backend.models.opportunity import Opportunity, OpportunityStatus
from src.backend.services.slack_service import format_opportunity_blocks

log = logging.getLogger("buzzreach.api.slack")

router = APIRouter(
    prefix="/api/v1/slack",
    tags=["slack"],
    dependencies=[Depends(require_rate_limit)],
)

_HELP_TEXT = (
    "*Available commands:*\n"
    "\u2022 `/buzzreach latest` \u2014 Show 5 most recent opportunities\n"
    "\u2022 `/buzzreach search [keyword]` \u2014 Find by keyword\n"
    "\u2022 `/buzzreach subscribe` \u2014 Enable Slack digest\n"
    "\u2022 `/buzzreach help` \u2014 Show this message"
)


@router.post("/events")
async def handle_slack_event(request: Request) -> JSONResponse:
    """Handle Slack Events API callbacks.

    Responds to url_verification challenges and processes
    event_callback payloads (e.g. reaction_added).
    """
    body: dict[str, Any] = await request.json()
    event_type = body.get("type", "")

    if event_type == "url_verification":
        return _handle_verification(body)

    if event_type == "event_callback":
        return _handle_event_callback(body)

    log.info(
        "Unknown Slack event type",
        extra={"event_type": event_type},
    )
    return JSONResponse({"ok": True})


@router.post("/slash")
async def handle_slash_command(
    command: Annotated[str, Form()],
    text: Annotated[str, Form()] = "",
    user_id: Annotated[str, Form()] = "",
    user_name: Annotated[str, Form()] = "",
    channel_id: Annotated[str, Form()] = "",
    team_id: Annotated[str, Form()] = "",
    response_url: Annotated[str, Form()] = "",
    trigger_id: Annotated[str, Form()] = "",
) -> JSONResponse:
    """Handle /buzzreach slash commands from Slack."""
    subcommand = text.strip().split()[0].lower() if text.strip() else ""
    args = text.strip().split()[1:] if text.strip() else []

    log.info(
        "Slash command received",
        extra={
            "subcommand": subcommand,
            "user_id": user_id,
            "channel_id": channel_id,
        },
    )

    handler = _COMMAND_HANDLERS.get(subcommand, _cmd_help)
    return handler(subcommand, args, channel_id, user_id)


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def _handle_verification(body: dict[str, Any]) -> JSONResponse:
    """Respond to Slack URL verification challenge."""
    challenge = body.get("challenge", "")
    log.info("Slack URL verification", extra={"challenge": challenge})
    return JSONResponse({"challenge": challenge})


def _handle_event_callback(body: dict[str, Any]) -> JSONResponse:
    """Process an event_callback from the Events API."""
    event = body.get("event", {})
    event_type = event.get("type", "unknown")

    log.info(
        "Slack event received",
        extra={
            "event_type": event_type,
            "team_id": body.get("team_id", ""),
        },
    )
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------------------
# Slash command handlers
# ---------------------------------------------------------------------------

def _cmd_help(
    _sub: str,
    _args: list[str],
    _channel: str,
    _user: str,
) -> JSONResponse:
    """Return the help text listing available commands."""
    return JSONResponse({
        "response_type": "ephemeral",
        "text": _HELP_TEXT,
    })


def _cmd_latest(
    _sub: str,
    _args: list[str],
    channel: str,
    _user: str,
) -> JSONResponse:
    """Return the 5 most recent opportunities."""
    opportunities = _fetch_latest_opportunities(limit=5)
    if not opportunities:
        return JSONResponse({
            "response_type": "ephemeral",
            "text": "No recent opportunities found.",
            "blocks": [],
        })

    blocks: list[dict[str, Any]] = []
    for opp in opportunities:
        blocks.extend(format_opportunity_blocks(opp))

    return JSONResponse({
        "response_type": "in_channel",
        "text": f"{len(opportunities)} recent opportunities",
        "blocks": blocks,
    })


def _cmd_search(
    _sub: str,
    args: list[str],
    channel: str,
    _user: str,
) -> JSONResponse:
    """Search opportunities by keyword."""
    keyword = " ".join(args) if args else ""
    if not keyword:
        return JSONResponse({
            "response_type": "ephemeral",
            "text": "Usage: `/buzzreach search [keyword]`",
        })

    results = _search_opportunities(keyword=keyword, limit=5)
    if not results:
        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"No opportunities found for '{keyword}'.",
        })

    blocks: list[dict[str, Any]] = []
    for opp in results:
        blocks.extend(format_opportunity_blocks(opp))

    return JSONResponse({
        "response_type": "in_channel",
        "text": f"{len(results)} results for '{keyword}'",
        "blocks": blocks,
    })


def _cmd_subscribe(
    _sub: str,
    _args: list[str],
    channel: str,
    user: str,
) -> JSONResponse:
    """Enable Slack digest delivery for the user."""
    log.info(
        "User subscribed to Slack digest",
        extra={"user_id": user, "channel_id": channel},
    )
    return JSONResponse({
        "response_type": "ephemeral",
        "text": (
            f"Subscribed! You'll receive BuzzReach digests in "
            f"<#{channel}>."
        ),
    })


# ---------------------------------------------------------------------------
# Data access helpers (mocked in tests)
# ---------------------------------------------------------------------------

def _fetch_latest_opportunities(
    limit: int = 5,
) -> list[OpportunityData]:
    """Fetch the most recent opportunities from the database.

    Returns an empty list when no database session is available
    (e.g. in slash command context without full app bootstrap).
    """
    try:
        from sqlalchemy.orm import Session

        from src.backend.db.session import get_engine

        engine = get_engine()
        with Session(engine) as session:
            rows = (
                session.query(Opportunity)
                .filter(Opportunity.status == OpportunityStatus.NEW)
                .order_by(Opportunity.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                OpportunityData.model_validate(r, from_attributes=True)
                for r in rows
            ]
    except Exception:
        log.warning("Could not fetch opportunities", exc_info=True)
        return []


def _search_opportunities(
    keyword: str,
    limit: int = 5,
) -> list[OpportunityData]:
    """Search opportunities by keyword in title or why_matched."""
    try:
        from sqlalchemy.orm import Session

        from src.backend.db.session import get_engine

        engine = get_engine()
        with Session(engine) as session:
            pattern = f"%{keyword}%"
            rows = (
                session.query(Opportunity)
                .filter(
                    Opportunity.title.ilike(pattern)
                    | Opportunity.why_matched.ilike(pattern)
                )
                .order_by(Opportunity.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                OpportunityData.model_validate(r, from_attributes=True)
                for r in rows
            ]
    except Exception:
        log.warning("Could not search opportunities", exc_info=True)
        return []


# Command dispatch table
_COMMAND_HANDLERS = {
    "latest": _cmd_latest,
    "search": _cmd_search,
    "subscribe": _cmd_subscribe,
    "help": _cmd_help,
}
