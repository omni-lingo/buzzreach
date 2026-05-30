# ATOM: FE-001 — Settings & Configuration UI

**Layer:** L4
**Module:** frontend
**Effort:** M
**Depends on:** API-001, auth

## Inputs (what this atom reads/consumes)
- `src/backend/api/opportunities.py` — existing API routes
- `src/backend/models/` — User, Opportunity, Metrics models
- API authentication via JWT

## Outputs (what this atom produces)
- `src/frontend/pages/Settings.tsx` — React component for:
  - Product configuration (product URL, one-line pitch, keywords list)
  - Tone/persona settings (text input)
  - Delivery preferences (email address, Slack webhook URL, frequency: hourly/daily/weekly)
  - Search filters (platform preferences, exclude domains)
  - API key management (display masked key, regenerate)
  - Account info (email, created date, usage stats)
- `src/frontend/pages/AccountSettings.tsx` — user profile:
  - Email (read-only)
  - Password change form
  - API key visibility toggle + copy button
  - Delete account option
- `src/frontend/api/settingsClient.ts` — API client for:
  - GET `/api/v1/settings` — fetch user's current config
  - POST `/api/v1/settings` — save config changes
  - POST `/api/v1/settings/regenerate-key` — new API key
  - POST `/api/v1/password/change` — password change
- `src/frontend/components/SettingsForm.tsx` — reusable form with validation
- `tests/e2e/settings.spec.ts` — Playwright tests for settings flow

## Acceptance criteria
- [ ] Settings page loads current user config from API
- [ ] User can update keywords, tone, delivery settings and save
- [ ] API key regeneration works, old key immediately invalidated
- [ ] Password change requires current password validation
- [ ] Form validation prevents invalid emails, empty keywords
- [ ] Mobile responsive (at least 320px width)
- [ ] All API calls include JWT auth header
- [ ] E2E tests pass (load → edit → save → reload → verify)

## Cross-module contracts
- Imports `UserData` from `contracts/auth/user.py`
- Imports `OpportunityEvent` from `contracts/opportunities/opportunity_event.py`
- API calls go through JWT-authenticated routes (AUTH-002)
