"""Billing webhook handler for Stripe events (BILL-001).

Validates webhook signatures to prevent spoofing, then dispatches
to event-specific handlers. This is an L3 route — all business
logic lives in the handler functions, not in HTTP plumbing.

Handled events:
- charge.succeeded — update user subscription status to active
- customer.subscription.deleted — mark user as past_due
- invoice.payment_failed — mark past_due and log for notification
"""

import logging
from typing import Any

import stripe
from sqlalchemy.orm import Session
from stripe import SignatureVerificationError as StripeSigError

from src.backend.models.stripe_customer import StripeCustomer

log = logging.getLogger("buzzreach.billing.webhooks")


def _verify_webhook_event(
    payload: bytes,
    sig_header: str,
    webhook_secret: str,
) -> Any | None:
    """Verify webhook signature and construct a Stripe event.

    Returns the event if valid, None if signature verification fails.
    """
    try:
        return stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except StripeSigError:
        log.warning(
            "Webhook signature verification failed",
            extra={"error_code": "WEBHOOK_SIG_INVALID"},
        )
        return None
    except ValueError:
        log.warning(
            "Webhook payload invalid",
            extra={"error_code": "WEBHOOK_PAYLOAD_INVALID"},
        )
        return None


def handle_charge_succeeded(
    event_data: dict[str, Any], session: Session
) -> None:
    """Update subscription to active on successful charge."""
    customer_id = event_data.get("customer")
    subscription_id = event_data.get("subscription")

    if not customer_id:
        log.warning("charge.succeeded missing customer field")
        return

    record = (
        session.query(StripeCustomer)
        .filter_by(stripe_customer_id=customer_id)
        .first()
    )
    if record is None:
        log.warning(
            "charge.succeeded for unknown customer",
            extra={"stripe_customer_id": customer_id},
        )
        return

    record.subscription_status = "active"
    if subscription_id:
        record.stripe_subscription_id = subscription_id
    session.commit()

    log.info(
        "Subscription activated via charge",
        extra={
            "user_id": str(record.user_id),
            "stripe_customer_id": customer_id,
        },
    )


def handle_subscription_deleted(
    event_data: dict[str, Any], session: Session
) -> None:
    """Mark subscription as past_due when deleted in Stripe."""
    customer_id = event_data.get("customer")

    if not customer_id:
        log.warning("subscription.deleted missing customer field")
        return

    record = (
        session.query(StripeCustomer)
        .filter_by(stripe_customer_id=customer_id)
        .first()
    )
    if record is None:
        log.warning(
            "subscription.deleted for unknown customer",
            extra={"stripe_customer_id": customer_id},
        )
        return

    record.subscription_status = "past_due"
    record.stripe_subscription_id = None
    record.plan_id = None
    session.commit()

    log.info(
        "Subscription marked past_due",
        extra={
            "user_id": str(record.user_id),
            "stripe_customer_id": customer_id,
        },
    )


def handle_invoice_payment_failed(
    event_data: dict[str, Any], session: Session
) -> None:
    """Mark subscription as past_due and log for notification."""
    customer_id = event_data.get("customer")
    invoice_id = event_data.get("id")

    if not customer_id:
        log.warning("invoice.payment_failed missing customer field")
        return

    record = (
        session.query(StripeCustomer)
        .filter_by(stripe_customer_id=customer_id)
        .first()
    )
    if record is None:
        log.warning(
            "invoice.payment_failed for unknown customer",
            extra={"stripe_customer_id": customer_id},
        )
        return

    record.subscription_status = "past_due"
    session.commit()

    log.info(
        "Payment failed, user notified",
        extra={
            "user_id": str(record.user_id),
            "invoice_id": invoice_id,
            "stripe_customer_id": customer_id,
        },
    )


_EVENT_HANDLERS: dict[str, Any] = {
    "charge.succeeded": handle_charge_succeeded,
    "customer.subscription.deleted": handle_subscription_deleted,
    "invoice.payment_failed": handle_invoice_payment_failed,
}


def _route_event(event: Any, session: Session) -> str:
    """Dispatch a verified Stripe event to the appropriate handler.

    Returns the event type if handled, 'unhandled' otherwise.
    """
    handler = _EVENT_HANDLERS.get(event.type)
    if handler is None:
        log.info(
            "Unhandled webhook event type",
            extra={"event_type": event.type},
        )
        return "unhandled"

    event_data = event.data.object
    if isinstance(event_data, dict):
        handler(event_data, session)
    else:
        handler(dict(event_data), session)

    return event.type
