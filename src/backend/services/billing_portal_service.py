"""Billing portal service for BILL-004.

Pure business logic — no HTTP concerns. Aggregates subscription, usage,
and Stripe data for the customer portal frontend.

Cross-module contracts:
- Reads Subscription (BILL-002) via SubscriptionService
- Reads Usage (BILL-003) via UsageService
- Calls Stripe API via StripeService (BILL-001)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import stripe
from sqlalchemy.orm import Session

from contracts.billing.subscription import SubscriptionStatus
from src.backend.errors import AppError
from src.backend.models.stripe_customer import StripeCustomer
from src.backend.models.subscription import Subscription
from src.backend.services.plan_definitions import PLANS
from src.backend.services.subscription_service import SubscriptionService
from src.backend.services.usage_service import UsageService

log = logging.getLogger("buzzreach.billing")


@dataclass(frozen=True)
class BillingOverview:
    """Current plan, usage, and billing cycle for the portal."""

    plan_id: str
    plan_name: str
    price_cents: int
    status: str
    usage_current: int
    usage_limit: int
    usage_percentage: float
    period_start: datetime | None
    period_end: datetime | None
    auto_renew: bool
    card_last4: str | None
    card_brand: str | None
    features: list[str]


@dataclass(frozen=True)
class InvoiceItem:
    """Single invoice record from Stripe."""

    invoice_id: str
    date: datetime
    amount_cents: int
    currency: str
    status: str
    pdf_url: str | None
    description: str | None


@dataclass(frozen=True)
class PlanOption:
    """Plan details for the comparison page."""

    plan_id: str
    display_name: str
    price_cents: int
    opportunities_per_day: int
    features: list[str]
    is_current: bool


@dataclass(frozen=True)
class ProrationPreview:
    """Proration amount preview for plan changes."""

    amount_cents: int
    currency: str
    description: str


class BillingPortalService:
    """Aggregates billing data for the customer portal."""

    def __init__(
        self, session: Session, stripe_api_key: str
    ) -> None:
        self._session = session
        self._sub_svc = SubscriptionService(session, stripe_api_key)
        self._usage_svc = UsageService(session)
        stripe.api_key = stripe_api_key

    def get_overview(self, user_id: UUID) -> BillingOverview:
        """Return current plan, usage, and payment info."""
        plan_info = self._sub_svc.get_user_plan(user_id)
        quota = self._usage_svc.is_quota_exceeded(user_id)
        card = self._get_payment_method(user_id)
        pct = _usage_percentage(quota.current, quota.limit)

        return BillingOverview(
            plan_id=plan_info.plan_id,
            plan_name=plan_info.entitlements.display_name,
            price_cents=plan_info.entitlements.price_cents,
            status=plan_info.status.value,
            usage_current=quota.current,
            usage_limit=quota.limit,
            usage_percentage=pct,
            period_start=_get_period_start(self._session, user_id),
            period_end=plan_info.current_period_end,
            auto_renew=plan_info.auto_renew,
            card_last4=card[0],
            card_brand=card[1],
            features=sorted(plan_info.entitlements.features),
        )

    def get_invoices(
        self, user_id: UUID, limit: int = 20
    ) -> list[InvoiceItem]:
        """Return invoice history from Stripe."""
        customer = self._get_stripe_customer(user_id)
        if customer is None:
            return []

        try:
            invoices = stripe.Invoice.list(
                customer=customer.stripe_customer_id,
                limit=limit,
            )
        except stripe.StripeError:
            log.warning(
                "Failed to fetch invoices",
                extra={"user_id": str(user_id)},
            )
            return []

        return [_map_invoice(inv) for inv in invoices.data]

    def get_plan_options(self, user_id: UUID) -> list[PlanOption]:
        """Return all plans with current plan highlighted."""
        plan_info = self._sub_svc.get_user_plan(user_id)
        return [
            PlanOption(
                plan_id=p.plan_id,
                display_name=p.display_name,
                price_cents=p.price_cents,
                opportunities_per_day=p.opportunities_per_day,
                features=sorted(p.features),
                is_current=(p.plan_id == plan_info.plan_id),
            )
            for p in PLANS.values()
        ]

    def initiate_upgrade(self, user_id: UUID, plan_id: str) -> str:
        """Start Stripe checkout for upgrading. Returns checkout URL."""
        return self._sub_svc.upgrade_plan(user_id, plan_id)

    def initiate_downgrade(
        self, user_id: UUID, plan_id: str
    ) -> None:
        """Downgrade to a lower plan with proration."""
        self._sub_svc.downgrade_plan(user_id, plan_id)
        log.info(
            "Plan downgraded via portal",
            extra={"user_id": str(user_id), "new_plan": plan_id},
        )

    def cancel_subscription(
        self, user_id: UUID, reason: str
    ) -> bool:
        """Cancel subscription. Returns True if retention offered."""
        plan_info = self._sub_svc.get_user_plan(user_id)
        if plan_info.status not in (
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.PAST_DUE,
        ):
            raise AppError(
                code="NO_ACTIVE_SUBSCRIPTION",
                message="No active subscription to cancel",
            )

        offer_retention = plan_info.plan_id in ("pro", "premium")
        if not offer_retention:
            self._sub_svc.downgrade_plan(user_id, "free")

        log.info(
            "Cancel requested via portal",
            extra={
                "user_id": str(user_id),
                "reason": reason,
                "retention_offered": offer_retention,
            },
        )
        return offer_retention

    def confirm_cancel(self, user_id: UUID) -> None:
        """Confirm cancellation after retention offer declined."""
        self._sub_svc.downgrade_plan(user_id, "free")
        log.info(
            "Cancel confirmed via portal",
            extra={"user_id": str(user_id)},
        )

    def _get_stripe_customer(
        self, user_id: UUID
    ) -> StripeCustomer | None:
        """Look up local Stripe customer record."""
        return (
            self._session.query(StripeCustomer)
            .filter_by(user_id=user_id)
            .first()
        )

    def _get_payment_method(
        self, user_id: UUID
    ) -> tuple[str | None, str | None]:
        """Return (last4, brand) from Stripe, or (None, None)."""
        customer = self._get_stripe_customer(user_id)
        if customer is None:
            return (None, None)

        try:
            methods = stripe.PaymentMethod.list(
                customer=customer.stripe_customer_id,
                type="card",
                limit=1,
            )
            if methods.data:
                card = methods.data[0].card
                return (card.last4, card.brand)
        except stripe.StripeError:
            log.warning(
                "Failed to fetch payment method",
                extra={"user_id": str(user_id)},
            )
        return (None, None)


def _usage_percentage(current: int, limit: int) -> float:
    """Calculate usage as a percentage, capped at 100."""
    if limit <= 0:
        return 0.0
    return min((current / limit) * 100, 100.0)


def _get_period_start(
    session: Session, user_id: UUID
) -> datetime | None:
    """Fetch the current billing period start from the subscription."""
    sub = (
        session.query(Subscription)
        .filter_by(user_id=user_id)
        .first()
    )
    return sub.current_period_start if sub else None


def _map_invoice(inv: object) -> InvoiceItem:
    """Map a Stripe Invoice object to our InvoiceItem."""
    return InvoiceItem(
        invoice_id=inv.id,
        date=datetime.fromtimestamp(inv.created),
        amount_cents=inv.amount_paid,
        currency=inv.currency,
        status=inv.status,
        pdf_url=inv.invoice_pdf,
        description=inv.description,
    )
