"""Cross-module contract for push notification data (MOBILE-002).

Consumed by:
- MOBILE-002 (push notification service)
- API push routes (register/unregister)
- JOB-001 (opportunity notification dispatch)
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class DevicePlatform(StrEnum):
    """Supported mobile platforms for push notifications."""

    IOS = "ios"
    ANDROID = "android"


class NotificationFrequency(StrEnum):
    """User preference for push notification frequency."""

    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    DISABLED = "disabled"


class PushSubscriptionData(BaseModel):
    """Public push subscription info for cross-module use."""

    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    device_token: str
    platform: DevicePlatform
    is_active: bool
    created_at: datetime


class PushNotificationPayload(BaseModel):
    """Payload for a push notification to be sent."""

    title: str
    body: str
    opportunity_id: UUID | None = None
    data: dict[str, str] | None = None
