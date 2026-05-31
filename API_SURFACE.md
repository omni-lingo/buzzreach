# API Surface

## Endpoints

Auto-generated after L3 (routes).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/opportunities` | List opportunities with filters (platform, score_min, limit, offset) |
| POST | `/api/v1/opportunities/{id}/mark-posted` | Mark opportunity as posted (removes from feed) |
| POST | `/api/v1/opportunities/{id}/archive` | Archive opportunity (hides from feed) |
| POST | `/api/v1/opportunities/{id}/actions` | Log user action (viewed, copied, posted, archived) |
| GET | `/api/v1/opportunities/{id}/actions` | Get action history for an opportunity |
| POST | `/api/v1/scan` | Trigger immediate scan |
| GET | `/api/v1/settings` | Get user settings |
| POST | `/api/v1/settings` | Update user settings |
| POST | `/api/v1/settings/regenerate-key` | Regenerate API key |
| POST | `/api/v1/password/change` | Change user password |
| GET | `/api/v1/analytics/funnel` | Get conversion funnel analytics |
| GET | `/api/v1/dashboard` | Dashboard summary (today's stats) |
| GET | `/api/v1/dashboard/stats` | Per-niche metric aggregation |
| GET | `/api/v1/dashboard/errors` | Recent error audit log entries |
| GET | `/api/v1/templates` | List templates (global + user-owned, filter by category/search) |
| GET | `/api/v1/templates/{id}` | Get single template by ID |
| POST | `/api/v1/templates` | Create custom template (auth required) |
| PUT | `/api/v1/templates/{id}` | Update own template (auth required) |
| DELETE | `/api/v1/templates/{id}` | Delete own template (auth required) |

See `openapi.json` for full specification.
