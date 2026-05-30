"""Cross-module contract for subscription data (BILL-001, BILL-002).

Consumed by:
- BILL-002 (subscription plans & entitlements)
- API-001 (plan checks)
- BILL-004 (customer portal)
- OBSERV-001 (payment event notifications)
"""

from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class PlanEntitlements:
    """Feature limits and flags for a subscription plan."""

    plan_id: str
    display_name: str
    price_cents: int
    opportunities_per_day: int
    features: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class UserPlanInfo:
    """Resolved plan info for a user — returned by get_user_plan."""

    user_id: UUID
    plan_id: str
    status: SubscriptionStatus
    entitlements: PlanEntitlements
    current_period_end: datetime | None
    auto_renew: bool
