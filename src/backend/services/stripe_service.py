"""Stripe payment service for BILL-001.

Wraps Stripe SDK calls with retry logic and local subscription state.
Pure business logic — no HTTP concerns. Called by billing webhooks (L3)
and future BILL-002 (subscription plans).

Cross-module contracts:
- Extends User model via StripeCustomer FK
- Called by BILL-002 (subscription plans)
- Notifies OBSERV-001 of payment events
"""

import logging
import time
from uuid import UUID

import stripe
from sqlalchemy.orm import Session
from stripe import APIConnectionError as StripeConnectionError
from stripe import APIError as StripeAPIError
from stripe import AuthenticationError as StripeAuthError

from contracts.billing.subscription import SubscriptionData, SubscriptionStatus
from src.backend.errors import AppError
from src.backend.models.stripe_customer import StripeCustomer

log = logging.getLogger("buzzreach.billing")

_MAX_RETRIES = 3
_BASE_DELAY = 1.0


def _retry_stripe_call(func: object, *args: object, **kwargs: object) -> object:
    """Execute a Stripe API call with exponential backoff retry.

    Retries on transient connection errors up to _MAX_RETRIES times.
    Raises AppError on auth errors (no retry) or after exhausting retries.
    """
    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            return func(*args, **kwargs)  # type: ignore[operator]
        except StripeAuthError as exc:
            log.error(
                "Stripe auth failed",
                extra={"error_code": "STRIPE_AUTH_ERROR"},
            )
            raise AppError(
                code="STRIPE_AUTH_ERROR",
                message="Payment provider authentication failed",
            ) from exc
        except (StripeConnectionError, StripeAPIError) as exc:
            last_error = exc
            if attempt < _MAX_RETRIES - 1:
                delay = _BASE_DELAY * (2**attempt)
                log.warning(
                    "Stripe call failed, retrying",
                    extra={"attempt": attempt + 1, "delay": delay},
                )
                time.sleep(delay)

    log.error(
        "Stripe call failed after retries",
        extra={"error_code": "STRIPE_API_ERROR", "retries": _MAX_RETRIES},
    )
    raise AppError(
        code="STRIPE_API_ERROR",
        message="Payment provider temporarily unavailable",
    ) from last_error


class StripeService:
    """Wraps Stripe SDK operations with retry and local state."""

    def __init__(self, api_key: str, session: Session) -> None:
        stripe.api_key = api_key
        self._session = session

    def _get_customer_record(self, user_id: UUID) -> StripeCustomer | None:
        """Look up the local StripeCustomer row for a user."""
        return (
            self._session.query(StripeCustomer)
            .filter_by(user_id=user_id)
            .first()
        )

    def create_customer(self, user_id: UUID, email: str) -> str:
        """Create a Stripe customer for a user, or return existing ID.

        Returns the Stripe customer ID (cus_...).
        """
        existing = self._get_customer_record(user_id)
        if existing is not None:
            return existing.stripe_customer_id

        result = _retry_stripe_call(
            stripe.Customer.create,
            email=email,
            metadata={"buzzreach_user_id": str(user_id)},
        )
        stripe_id: str = result.id  # type: ignore[union-attr]

        record = StripeCustomer(
            user_id=user_id,
            stripe_customer_id=stripe_id,
        )
        self._session.add(record)
        self._session.commit()

        log.info(
            "Stripe customer created",
            extra={"user_id": str(user_id), "stripe_id": stripe_id},
        )
        return stripe_id

    def create_checkout_session(
        self, user_id: UUID, plan_id: str
    ) -> str:
        """Create a Stripe Checkout session for a subscription plan.

        Returns the checkout session URL.
        """
        record = self._get_customer_record(user_id)
        if record is None:
            raise AppError(
                code="CUSTOMER_NOT_FOUND",
                message="Create a customer before starting checkout",
            )

        session_obj = _retry_stripe_call(
            stripe.checkout.Session.create,
            customer=record.stripe_customer_id,
            mode="subscription",
            line_items=[{"price": plan_id, "quantity": 1}],
            success_url="https://app.buzzreach.com/billing?status=success",
            cancel_url="https://app.buzzreach.com/billing?status=cancel",
        )
        url: str = session_obj.url  # type: ignore[union-attr]

        log.info(
            "Checkout session created",
            extra={"user_id": str(user_id), "plan_id": plan_id},
        )
        return url

    def cancel_subscription(self, user_id: UUID) -> None:
        """Cancel the user's active Stripe subscription."""
        record = self._get_customer_record(user_id)
        if record is None or not record.stripe_subscription_id:
            raise AppError(
                code="NO_ACTIVE_SUBSCRIPTION",
                message="No active subscription to cancel",
            )

        _retry_stripe_call(
            stripe.Subscription.cancel,
            record.stripe_subscription_id,
        )

        log.info(
            "Subscription canceled",
            extra={
                "user_id": str(user_id),
                "sub_id": record.stripe_subscription_id,
            },
        )

    def get_current_subscription(self, user_id: UUID) -> SubscriptionData:
        """Return the user's current subscription metadata."""
        record = self._get_customer_record(user_id)
        if record is None:
            return SubscriptionData(
                user_id=user_id,
                stripe_customer_id="",
                stripe_subscription_id=None,
                plan_id=None,
                status=SubscriptionStatus.NONE,
                current_period_end=None,
            )

        return SubscriptionData(
            user_id=record.user_id,
            stripe_customer_id=record.stripe_customer_id,
            stripe_subscription_id=record.stripe_subscription_id,
            plan_id=record.plan_id,
            status=SubscriptionStatus(record.subscription_status),
            current_period_end=record.current_period_end,
        )
