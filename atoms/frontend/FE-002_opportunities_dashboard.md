# ATOM: FE-002 — Opportunities Dashboard (live feed)

**Layer:** L4
**Module:** frontend
**Effort:** M
**Depends on:** API-001, FE-001

## Inputs (what this atom reads/consumes)
- `src/backend/api/opportunities.py` — list/filter opportunities endpoint
- `src/backend/models/opportunity.py` — Opportunity schema
- API authentication via JWT

## Outputs (what this atom produces)
- `src/frontend/pages/Dashboard.tsx` — main feed view showing:
  - Card list of opportunities (URL title, platform, score, relevance reason)
  - Each card shows: draft reply preview, copy-to-clipboard button, "mark as posted" button
  - Filter sidebar (by platform, score range, date)
  - Pagination or infinite scroll
  - Empty state message when no opportunities
- `src/frontend/components/OpportunityCard.tsx` — reusable card component
- `src/frontend/components/OpportunityFilter.tsx` — filter controls
- `src/frontend/api/opportunitiesClient.ts` — API client:
  - GET `/api/v1/opportunities?platform=reddit&score_min=0.7&limit=50`
  - POST `/api/v1/opportunities/{id}/mark-posted` — record user action
  - POST `/api/v1/opportunities/{id}/archive` — hide from feed
- `src/frontend/hooks/useOpportunities.ts` — data fetching + polling (auto-refresh every 5 min)
- `tests/e2e/dashboard.spec.ts` — Playwright tests

## Acceptance criteria
- [ ] Dashboard loads and displays 20+ opportunities on first visit
- [ ] Filter by platform (Reddit, Quora, etc.) updates feed in real-time
- [ ] Score filter (0.5-1.0 range slider) works
- [ ] Copy-to-clipboard button copies the draft reply
- [ ] "Mark as posted" button removes opportunity from feed and logs action
- [ ] Archive button hides opportunity
- [ ] Opportunities auto-refresh every 5 minutes (optional polling)
- [ ] Mobile responsive
- [ ] Clicking URL opens thread in new tab
- [ ] E2E tests pass

## Cross-module contracts
- Imports `OpportunityEvent` from `contracts/opportunities/opportunity_event.py`
- Calls authenticated API routes (needs JWT token in header)
- Updates Opportunity status via API-001
