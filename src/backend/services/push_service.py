"""Push notification service for MOBILE-002.

Pure business logic — no HTTP concerns. Sends push notifications via
the Expo Push API, manages device tokens, respects plan-based
frequency limits, and provides batch/scheduled sending.

Cross-module contracts:
- Reads PushSubscription model (MOBILE-002)
- Reads Subscription (BILL-002) for plan-based frequency
- Reads User (AUTH-001) to verify active status
- Integrates with UsageService (BILL-003) for push_sent tracking
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from contracts.push.push_subscription import NotificationFrequency
from src.backend.errors import AppError
from src.backend.models.push_subscription import PushSubscription
from src.backend.models.subscription import Subscription
from src.backend.models.user import User
from src.backend.services.push_expo import (
    build_messages,
    handle_expo_errors,
)
from src.backend.services.push_expo import (
    post_to_expo as _post_to_expo,
)

log = logging.getLogger("buzzreach.push")

_PLAN_FREQUENCY_MAP: dict[str, NotificationFrequency] = {
    "free": NotificationFrequency.DAILY,
    "pro": NotificationFrequency.REALTIME,
    "premium": NotificationFrequency.REALTIME,
}


def _resolve_plan_id(session: Session, user_id: UUID) -> str:
    """Look up the user's current plan, defaulting to free."""
    sub = (
        session.query(Subscription)
        .filter_by(user_id=user_id)
        .first()
    )
    if sub is None or sub.status != "active":
        return "free"
    return sub.plan_id


class PushService:
    """Sends push notifications and manages device tokens."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _get_active_tokens(
        self, user_id: UUID,
    ) -> list[PushSubscription]:
        """Return all active push subscriptions for a user."""
        return (
            self._session.query(PushSubscription)
            .filter_by(user_id=user_id, is_active=True)
            .all()
        )

    def _is_user_active(self, user_id: UUID) -> bool:
        """Check if the user account is active (verified)."""
        user = self._session.get(User, user_id)
        return user is not None and user.is_active

    def send_push_notification(
        self,
        user_id: UUID,
        title: str,
        body: str,
        opportunity_id: UUID | None = None,
    ) -> bool:
        """Send a push notification to all of a user's devices.

        Returns:
            True if at least one notification was sent.
        """
        if not self._is_user_active(user_id):
            log.info(
                "Push blocked for inactive user",
                extra={"user_id": str(user_id)},
            )
            return False

        tokens = self._get_active_tokens(user_id)
        if not tokens:
            return False

        messages = build_messages(tokens, title, body, opportunity_id)
        tickets = _post_to_expo(messages)
        handle_expo_errors(self._session, tokens, tickets)

        log.info(
            "Push sent",
            extra={
                "user_id": str(user_id),
                "device_count": len(tokens),
            },
        )
        return True

    def batch_send_notifications(
        self,
        user_ids: list[UUID],
        title: str,
        body: str,
        opportunity_id: UUID | None = None,
    ) -> int:
        """Send push notifications to multiple users.

        Returns the number of users who received a notification.
        """
        sent_count = 0
        for user_id in user_ids:
            if self.send_push_notification(
                user_id, title, body, opportunity_id,
            ):
                sent_count += 1
        return sent_count

    def schedule_notification(
        self,
        user_id: UUID,
        title: str,
        body: str,
        send_at: datetime,
        opportunity_id: UUID | None = None,
    ) -> dict[str, str] | None:
        """Schedule a notification for future delivery.

        Returns a receipt dict, or None if no active tokens.
        """
        tokens = self._get_active_tokens(user_id)
        if not tokens:
            return None

        log.info(
            "Notification scheduled",
            extra={
                "user_id": str(user_id),
                "send_at": send_at.isoformat(),
            },
        )
        return {
            "user_id": str(user_id),
            "title": title,
            "body": body,
            "send_at": send_at.isoformat(),
            "device_count": str(len(tokens)),
        }

    def get_user_notification_frequency(
        self, user_id: UUID,
    ) -> NotificationFrequency:
        """Return the notification frequency for the user's plan."""
        plan_id = _resolve_plan_id(self._session, user_id)
        return _PLAN_FREQUENCY_MAP.get(
            plan_id, NotificationFrequency.DAILY,
        )

    def register_token(
        self,
        user_id: UUID,
        device_token: str,
        platform: str,
    ) -> PushSubscription:
        """Register or reactivate a device push token."""
        existing = (
            self._session.query(PushSubscription)
            .filter_by(device_token=device_token)
            .first()
        )
        if existing is not None:
            existing.is_active = True
            existing.user_id = user_id
            existing.platform = platform
            self._session.commit()
            log.info(
                "Token reactivated",
                extra={"device_token": device_token[:20]},
            )
            return existing

        sub = PushSubscription(
            user_id=user_id,
            device_token=device_token,
            platform=platform,
        )
        self._session.add(sub)
        self._session.commit()
        log.info(
            "Token registered",
            extra={
                "user_id": str(user_id),
                "platform": platform,
            },
        )
        return sub

    def unregister_token(
        self, user_id: UUID, device_token: str,
    ) -> PushSubscription:
        """Mark a device token as inactive."""
        sub = (
            self._session.query(PushSubscription)
            .filter_by(user_id=user_id, device_token=device_token)
            .first()
        )
        if sub is None:
            raise AppError(
                code="TOKEN_NOT_FOUND",
                message="Device token not found",
            )
        sub.is_active = False
        self._session.commit()
        log.info(
            "Token unregistered",
            extra={"device_token": device_token[:20]},
        )
        return sub

    def deactivate_token(self, device_token: str) -> None:
        """Deactivate a token (e.g. from Expo feedback API)."""
        sub = (
            self._session.query(PushSubscription)
            .filter_by(device_token=device_token)
            .first()
        )
        if sub is not None:
            sub.is_active = False
            self._session.commit()
            log.info(
                "Stale token deactivated",
                extra={"device_token": device_token[:20]},
            )
