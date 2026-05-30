# ATOM: BILL-003 — Usage Metering & Quotas

**Layer:** L2
**Module:** billing
**Effort:** M
**Depends on:** BILL-002, PIPE-001

## Inputs (what this atom reads/consumes)
- `src/backend/models/metrics.py` — metrics tracking
- `src/backend/models/subscription.py` — user's plan
- Pipeline orchestration (PIPE-001)

## Outputs (what this atom produces)
- `src/backend/models/usage.py` — track user usage:
  - `id`, `user_id`, `date`, `opportunities_found`, `api_calls`, `cost_estimate`
  - `email_sent`, `push_sent`, `drafts_regenerated`
  - Reset daily/monthly depending on plan billing cycle
- `src/backend/services/usage_service.py`:
  - `record_scan(user_id, opportunities_count)` → increment daily count
  - `record_api_call(user_id)` → track API usage
  - `is_quota_exceeded(user_id)` → check if user hit limit
  - `get_usage_today(user_id)` → current day's usage
  - `get_monthly_cost(user_id)` → estimated bill
- Plan quotas (daily):
  - Free: 5 opportunities/day
  - Pro: 100 opportunities/day
  - Premium: unlimited
- Rate limiting per plan:
  - Free: max 10 API calls/min
  - Pro: max 100 API calls/min
  - Premium: max 1000 API calls/min
- Cost tracking:
  - Track Stripe cost, AI cost, search cost
  - Estimate customer bill (for transparency)
- Frontend display (FE-001):
  - Show usage bar: "23/100 opportunities today"
  - Estimated monthly cost
  - Days until next billing cycle
- Pipeline integration:
  - Check quota before running scan (return early if exceeded)
  - Log usage after scan completes
- `tests/test_usage_metering.py` — record, query, quota checks

## Acceptance criteria
- [ ] Usage tracked per user per day
- [ ] Quota enforced (free max 5/day, pro max 100/day)
- [ ] API rate limiting works (per plan tier)
- [ ] Cost estimate accurate (within 5% of actual)
- [ ] Daily reset happens automatically at midnight (user's timezone)
- [ ] Usage display in settings shows accurate count
- [ ] Quota exceeded error message helpful ("Upgrade to Pro for 100/day")
- [ ] Historical usage queryable (last 30 days)
- [ ] Performance: quota check <10ms per request

## Cross-module contracts
- Reads Subscription (BILL-002)
- Reads pipeline metrics (PIPE-001)
- Checked by API rate limiting (RATE-001)
- Displayed in FE-001 (settings)
