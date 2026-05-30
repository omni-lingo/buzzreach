# ATOM: FEAT-004 — Search Profiles & Scheduling

**Layer:** L2/L3
**Module:** features
**Effort:** M
**Depends on:** DISC-003, FE-001

## Inputs (what this atom reads/consumes)
- `src/backend/services/discovery_service.py` — search orchestration
- `src/backend/models/user.py` — User model

## Outputs (what this atom produces)
- `src/backend/models/search_profile.py` — store multiple search configs:
  - `id`, `user_id`, `name` (e.g., "IRS Tax", "Parking Appeals")
  - `keywords` (list), `platforms` (list), `languages` (list)
  - `enabled` (bool)
  - `created_at`, `updated_at`
- `src/backend/services/search_scheduler.py`:
  - `schedule_search_profile(profile_id, times)` → set cron times (6am, 2pm, etc.)
  - `get_scheduled_searches()` → list all active scheduled searches
  - `run_scheduled_search(profile_id)` → trigger search for profile
- `src/frontend/pages/SearchProfilesPage.tsx` — UI:
  - List all search profiles
  - Create new profile (copy existing or from scratch)
  - Edit profile (keywords, platforms, language)
  - Schedule picker (hourly, daily @ times, etc.)
  - Enable/disable toggle
  - Delete button
- `src/backend/api/search.py` — routes:
  - GET `/api/v1/search-profiles` — list profiles
  - POST `/api/v1/search-profiles` — create
  - PUT `/api/v1/search-profiles/{id}` — update
  - DELETE `/api/v1/search-profiles/{id}` — delete
  - POST `/api/v1/search-profiles/{id}/schedule` — set schedule
- Job system (JOB-001 expansion):
  - Cron job reads all active profiles
  - Runs discovery for each at scheduled times
  - Results associated with profile_id
- `tests/test_search_profiles.py` — CRUD, scheduling

## Acceptance criteria
- [ ] Multiple profiles per user, each with own keywords
- [ ] Profile enable/disable works
- [ ] Schedule picker intuitive (e.g., "Every day at 6am, 2pm")
- [ ] Scheduled searches run at specified times
- [ ] Results tagged by profile (for filtering)
- [ ] Free plan: max 1 profile, pro: max 5, premium: unlimited
- [ ] Profile copy feature (duplicate + edit)
- [ ] Delete confirmation before removing profile
- [ ] Performance: schedule check <100ms

## Cross-module contracts
- Extends User model
- Integrates into discovery service (DISC-003)
- Called by job scheduler (JOB-001)
- UI in FE-001
