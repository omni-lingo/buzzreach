# ATOM: FEAT-003 — Post-Action Tracking & Conversion Analytics

**Layer:** L2/L3
**Module:** features
**Effort:** M
**Depends on:** CORE-005, AUDIT-002

## Inputs (what this atom reads/consumes)
- `src/backend/models/opportunity.py` — Opportunity model
- `src/backend/models/metrics.py` — Metrics model

## Outputs (what this atom produces)
- `src/backend/models/opportunity_action.py` — track user actions:
  - `id`, `opportunity_id`, `user_id`, `action_type` (viewed, copied, posted, archived)
  - `posted_url` (link to actual Reddit/forum reply, if available)
  - `created_at`
- `src/backend/services/action_tracker.py`:
  - `log_action(opportunity_id, action_type, posted_url=None)` → save to DB
  - `get_action_history(opportunity_id)` → list of all user actions
- `src/backend/api/opportunities.py` — new routes:
  - POST `/api/v1/opportunities/{id}/actions` — log action (viewed, copied, posted, archived)
  - GET `/api/v1/opportunities/{id}/actions` — retrieve action history
- `src/frontend/components/OpportunityCard.tsx` — enhancements:
  - "Paste & Open" button now pops up form for "paste URL of your reply" (optional)
  - Auto-logs "posted" action with optional reply URL
  - Shows action status ("Posted ✓", "Archived", etc.)
- `src/frontend/pages/AnalyticsPage.tsx` — basic analytics:
  - Conversion funnel: discovered → shown → copied → posted
  - Count breakdown (e.g., "100 discovered, 45 shown, 30 copied, 12 posted")
  - Filter by date range, platform, niche
- Metrics expansion (CORE-005):
  - Track: opportunities_posted, reply_urls_tracked, posting_rate
- `tests/test_action_tracking.py` — log and query actions

## Acceptance criteria
- [ ] Action logging is fast (<10ms per action)
- [ ] "Posted" action can store optional URL
- [ ] Analytics funnel shows correct counts (no double-counting)
- [ ] Conversion rate calculated: posted / shown
- [ ] Breakdown by platform available
- [ ] Date range filtering works (date picker)
- [ ] Data persists across sessions
- [ ] User can see their own actions only
- [ ] GDPR: user can delete action history
- [ ] Performance: analytics page loads in <500ms for 1 year of data

## Cross-module contracts
- Extends Opportunity model
- Uses audit log (AUDIT-002)
- Feeds metrics (CORE-005)
- Called from FE-002, MOBILE-003
