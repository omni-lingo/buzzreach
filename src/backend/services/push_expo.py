"""Expo Push API helpers for MOBILE-002.

Handles HTTP communication with the Expo Push API, message building,
and error ticket processing. Extracted from push_service.py to keep
files under the 300-line limit (BUILD_RULES section 1).
"""

import json
import logging
from typing import Any
from urllib.request import Request, urlopen
from uuid import UUID

from sqlalchemy.orm import Session

from src.backend.models.push_subscription import PushSubscription

log = logging.getLogger("buzzreach.push")

_EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
_EXPO_TIMEOUT_SECONDS = 15


def post_to_expo(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """POST notification messages to the Expo Push API.

    Args:
        messages: List of Expo push message dicts.

    Returns:
        List of response ticket dicts from Expo.
    """
    body = json.dumps(messages).encode()
    req = Request(
        _EXPO_PUSH_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urlopen(req, timeout=_EXPO_TIMEOUT_SECONDS) as resp:  # noqa: S310
        result = json.loads(resp.read().decode())
    return result.get("data", [])


def build_messages(
    tokens: list[PushSubscription],
    title: str,
    body: str,
    opportunity_id: UUID | None,
) -> list[dict[str, Any]]:
    """Build Expo push message dicts for each device token."""
    data: dict[str, str] = {}
    if opportunity_id is not None:
        data["opportunity_id"] = str(opportunity_id)

    return [
        {
            "to": t.device_token,
            "title": title,
            "body": body,
            "data": data,
            "sound": "default",
            "priority": "high",
        }
        for t in tokens
    ]


def handle_expo_errors(
    session: Session,
    tokens: list[PushSubscription],
    tickets: list[dict[str, Any]],
) -> None:
    """Deactivate tokens that Expo reports as invalid."""
    for i, ticket in enumerate(tickets):
        if i >= len(tokens):
            break
        status = ticket.get("status", "")
        if status == "error":
            detail = ticket.get("details", {})
            error_type = detail.get("error", "")
            if error_type == "DeviceNotRegistered":
                tokens[i].is_active = False
                log.info(
                    "Token auto-deactivated",
                    extra={
                        "device_token": tokens[i].device_token[:20],
                        "error": error_type,
                    },
                )
    session.commit()
