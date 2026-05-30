# ATOM: BILL-001 — Stripe Payment Integration

**Layer:** L2
**Module:** billing
**Effort:** M
**Depends on:** auth

## Inputs (what this atom reads/consumes)
- Stripe API documentation
- `src/backend/models/user.py` — User model
- Environment variables: `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`

## Outputs (what this atom produces)
- `src/backend/services/stripe_service.py` — wrapper for:
  - `create_checkout_session(user_id, plan_id)` → returns Stripe session URL
  - `create_customer(user_id, email)` → stores Stripe customer ID on user record
  - `cancel_subscription(user_id)` → triggers Stripe cancellation
  - `get_current_subscription(user_id)` → returns plan, next billing date, status
- `src/backend/models/stripe_customer.py` — new model to link User ↔ Stripe customer ID
- `src/backend/api/billing_webhooks.py` — webhook handler for:
  - `charge.succeeded` — update user subscription status
  - `customer.subscription.deleted` — mark user as past-due
  - `invoice.payment_failed` — notify user
- `migrations/versions/<rev>_add_stripe_customer.py` — Alembic migration
- `tests/test_stripe_service.py` — unit tests with mocked Stripe responses

## Acceptance criteria
- [ ] User record stores Stripe customer ID
- [ ] `create_checkout_session` returns valid Stripe session URL
- [ ] Webhook signature validation prevents spoofing (BILL-001 gate)
- [ ] `charge.succeeded` webhook marks user as subscriber
- [ ] Subscription status queries return correct plan metadata
- [ ] All Stripe calls include retry logic (exponential backoff)
- [ ] No API keys logged or exposed in error messages
- [ ] Tests mock Stripe API (no live API calls during CI)

## Cross-module contracts
- Extends `User` model (adds stripe_customer_id field)
- Called by BILL-002 (subscription plans)
- Notifies OBSERV-001 of payment events
