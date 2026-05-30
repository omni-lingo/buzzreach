"""Subscription management service for BILL-002.

Pure business logic — no HTTP concerns. Manages plan lookups, upgrades,
downgrades, feature entitlements, and expiration of past-due subscriptions.

Cross-module contracts:
- Uses StripeCustomer model from BILL-001
- Produces UserPlanInfo consumed by API-001
- Integrates with BILL-004 (customer portal)
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

import stripe
from sqlalchemy.orm import Session

from contracts.billing.subscription import (
    PlanEntitlements,
    SubscriptionStatus,
    UserPlanInfo,
)
from src.backend.errors import AppError
from src.backend.models.stripe_customer import StripeCustomer
from src.backend.models.subscription import Subscription
from src.backend.services.plan_definitions import FREE_PLAN, PLANS

log = logging.getLogger("buzzreach.billing")

# Stripe price IDs mapped to internal plan IDs.
# In production these come from Stripe Dashboard config.
_STRIPE_PRICE_MAP: dict[str, str] = {
    "pro": "price_pro_monthly",
    "premium": "price_premium_monthly",
}


def _resolve_entitlements(plan_id: str, status: str) -> PlanEntitlements:
    """Return entitlements for a plan, falling back to free if inactive."""
    if status not in (SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE):
        return FREE_PLAN
    return PLANS.get(plan_id, FREE_PLAN)


class SubscriptionService:
    """Manages subscription plans, upgrades, and entitlements."""

    def __init__(self, session: Session, stripe_api_key: str) -> None:
        self._session = session
        stripe.api_key = stripe_api_key

    def _get_subscription(self, user_id: UUID) -> Subscription | None:
        """Look up the user's subscription row."""
        return (
            self._session.query(Subscription)
            .filter_by(user_id=user_id)
            .first()
        )

    def _get_stripe_customer(self, user_id: UUID) -> StripeCustomer | None:
        """Look up the user's Stripe customer record."""
        return (
            self._session.query(StripeCustomer)
            .filter_by(user_id=user_id)
            .first()
        )

    def _require_stripe_customer(self, user_id: UUID) -> StripeCustomer:
        """Return the StripeCustomer or raise CUSTOMER_NOT_FOUND."""
        record = self._get_stripe_customer(user_id)
        if record is None:
            raise AppError(
                code="CUSTOMER_NOT_FOUND",
                message="Create a Stripe customer before managing plans",
            )
        return record

    def get_user_plan(self, user_id: UUID) -> UserPlanInfo:
        """Return the user's active plan info, defaulting to free."""
        sub = self._get_subscription(user_id)
        if sub is None:
            return UserPlanInfo(
                user_id=user_id,
                plan_id="free",
                status=SubscriptionStatus.NONE,
                entitlements=FREE_PLAN,
                current_period_end=None,
                auto_renew=False,
            )

        entitlements = _resolve_entitlements(sub.plan_id, sub.status)
        return UserPlanInfo(
            user_id=user_id,
            plan_id=sub.plan_id,
            status=SubscriptionStatus(sub.status),
            entitlements=entitlements,
            current_period_end=sub.current_period_end,
            auto_renew=sub.auto_renew,
        )

    def upgrade_plan(self, user_id: UUID, new_plan_id: str) -> str:
        """Start a Stripe checkout for upgrading to a paid plan.

        Returns the Stripe checkout session URL.
        """
        if new_plan_id not in PLANS:
            raise AppError(
                code="INVALID_PLAN",
                message=f"Unknown plan: {new_plan_id}",
            )

        sub = self._get_subscription(user_id)
        if sub is not None and sub.plan_id == new_plan_id:
            raise AppError(
                code="ALREADY_ON_PLAN",
                message=f"Already subscribed to {new_plan_id}",
            )

        customer = self._require_stripe_customer(user_id)
        price_id = _STRIPE_PRICE_MAP.get(new_plan_id)
        if price_id is None:
            raise AppError(
                code="INVALID_PLAN",
                message=f"No Stripe price for plan: {new_plan_id}",
            )

        session_obj = stripe.checkout.Session.create(
            customer=customer.stripe_customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url="https://app.buzzreach.com/billing?status=success",
            cancel_url="https://app.buzzreach.com/billing?status=cancel",
        )

        log.info(
            "Upgrade checkout created",
            extra={
                "user_id": str(user_id),
                "new_plan": new_plan_id,
            },
        )
        return session_obj.url  # type: ignore[return-value]

    def downgrade_plan(self, user_id: UUID, new_plan_id: str) -> None:
        """Downgrade to a lower plan with Stripe proration."""
        if new_plan_id not in PLANS:
            raise AppError(
                code="INVALID_PLAN",
                message=f"Unknown plan: {new_plan_id}",
            )

        sub = self._get_subscription(user_id)
        if sub is None or sub.status != SubscriptionStatus.ACTIVE:
            raise AppError(
                code="NO_ACTIVE_SUBSCRIPTION",
                message="No active subscription to downgrade",
            )

        if new_plan_id == "free":
            self._cancel_to_free(sub)
            return

        self._modify_subscription(sub, new_plan_id)

    def _cancel_to_free(self, sub: Subscription) -> None:
        """Cancel the Stripe subscription and revert to free."""
        if sub.stripe_subscription_id:
            stripe.Subscription.cancel(sub.stripe_subscription_id)

        sub.plan_id = "free"
        sub.status = SubscriptionStatus.CANCELED
        sub.stripe_subscription_id = None
        sub.auto_renew = False
        self._session.commit()

        log.info(
            "Subscription canceled to free",
            extra={"user_id": str(sub.user_id)},
        )

    def _modify_subscription(
        self, sub: Subscription, new_plan_id: str
    ) -> None:
        """Modify an existing Stripe subscription with proration."""
        if not sub.stripe_subscription_id:
            raise AppError(
                code="NO_ACTIVE_SUBSCRIPTION",
                message="No Stripe subscription to modify",
            )

        price_id = _STRIPE_PRICE_MAP.get(new_plan_id)
        if price_id is None:
            raise AppError(
                code="INVALID_PLAN",
                message=f"No Stripe price for plan: {new_plan_id}",
            )

        stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
        item_id: str = stripe_sub.items.data[0].id

        stripe.Subscription.modify(
            sub.stripe_subscription_id,
            items=[{"id": item_id, "price": price_id}],
            proration_behavior="create_prorations",
        )

        log.info(
            "Subscription downgraded",
            extra={
                "user_id": str(sub.user_id),
                "new_plan": new_plan_id,
            },
        )

    def is_feature_available(
        self, user_id: UUID, feature: str
    ) -> bool:
        """Check whether a feature is available on the user's plan."""
        plan_info = self.get_user_plan(user_id)
        return feature in plan_info.entitlements.features

    def expire_past_due_subscriptions(self) -> int:
        """Revert past-due subscriptions whose period has ended.

        Returns the number of subscriptions expired.
        """
        now = datetime.now(UTC)
        expired = (
            self._session.query(Subscription)
            .filter(
                Subscription.status == SubscriptionStatus.PAST_DUE,
                Subscription.current_period_end < now,
            )
            .all()
        )

        for sub in expired:
            sub.plan_id = "free"
            sub.status = SubscriptionStatus.CANCELED
            sub.auto_renew = False
            log.info(
                "Subscription expired to free",
                extra={"user_id": str(sub.user_id)},
            )

        if expired:
            self._session.commit()

        return len(expired)
