"""Cross-module contract for subscription data (BILL-001).

Consumed by:
- BILL-002 (subscription plans)
- OBSERV-001 (payment event notifications)
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class SubscriptionStatus(StrEnum):
    """Possible states of a user's subscription."""

    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    NONE = "none"


class SubscriptionData(BaseModel):
    """Public subscription info — safe to expose to API consumers."""

    user_id: UUID
    stripe_customer_id: str
    stripe_subscription_id: str | None
    plan_id: str | None
    status: SubscriptionStatus
    current_period_end: datetime | None

    model_config = {"from_attributes": True}
