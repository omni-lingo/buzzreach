# ATOM: BILL-002 — Subscription Plans & Management

**Layer:** L2
**Module:** billing
**Effort:** S
**Depends on:** BILL-001

## Inputs (what this atom reads/consumes)
- `src/backend/models/user.py` — User model
- `src/backend/services/stripe_service.py` — Stripe integration
- Pricing strategy from product requirements

## Outputs (what this atom produces)
- `src/backend/models/subscription.py` — Subscription model:
  - `id` (UUID PK), `user_id` (FK), `plan_id` (str: "free", "pro", "premium")
  - `stripe_subscription_id`, `status` (active/cancelled/past_due)
  - `current_period_start`, `current_period_end`
  - `auto_renew` (bool)
  - `created_at`, `updated_at`
- `contracts/billing/subscription.py` — SubscriptionData DTO
- `src/backend/services/subscription_service.py`:
  - `get_user_plan(user_id)` → returns active plan or "free"
  - `upgrade_plan(user_id, new_plan_id)` → triggers Stripe checkout
  - `downgrade_plan(user_id, new_plan_id)` → handles proration
  - `is_feature_available(user_id, feature)` → plan entitlements check
- Plan definitions (YAML or Python):
  ```
  free: $0, 5 opportunities/day, email delivery only
  pro: $49, 100 opportunities/day, email + Slack, advanced filters
  premium: $149, unlimited, all features, team members
  ```
- `tests/test_subscription_service.py` — plan switching, entitlements

## Acceptance criteria
- [ ] Free plan allows 5 opportunities/day
- [ ] Pro/Premium upgrade redirects to Stripe checkout
- [ ] Downgrade prorates correctly (Stripe API)
- [ ] `is_feature_available()` returns correct bool per plan
- [ ] Plan change reflected in User record within 30 seconds of Stripe webhook
- [ ] Expired subscriptions revert to free plan automatically
- [ ] Tests verify all plan transitions

## Cross-module contracts
- Uses `Subscription` model across modules
- Called by API-001 for plan checks
- Integrates with BILL-001 (Stripe) and BILL-004 (Customer portal)
