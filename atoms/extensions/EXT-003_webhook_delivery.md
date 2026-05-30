# ATOM: EXT-003 — Webhook Delivery Handler (Custom integrations)

**Layer:** L3
**Module:** extensions
**Effort:** S
**Depends on:** DELIV-002

## Inputs (what this atom reads/consumes)
- `src/backend/models/opportunity.py` — opportunities
- User webhook configuration

## Outputs (what this atom produces)
- `src/backend/models/webhook.py` — store webhooks per user:
  - `id`, `user_id`, `url` (HTTPS endpoint)
  - `event_type` (opportunity_created, daily_digest, etc.)
  - `secret` (for signature verification)
  - `active` (bool)
  - `created_at`, `updated_at`
- `src/backend/services/webhook_service.py`:
  - `send_webhook(user_id, event_type, payload)` — POST to URL
  - Retry logic: 3 attempts with exponential backoff
  - Signature verification: HMAC-SHA256
  - Timeout: 30 seconds
- `src/backend/api/webhooks.py` — routes:
  - GET `/api/v1/webhooks` — list user's webhooks
  - POST `/api/v1/webhooks` — create webhook
  - POST `/api/v1/webhooks/{id}/test` — send test event
  - PUT `/api/v1/webhooks/{id}` — update
  - DELETE `/api/v1/webhooks/{id}` — delete
- Webhook payload format (JSON):
  ```json
  {
    "event": "opportunity_created",
    "timestamp": "2025-05-31T12:00:00Z",
    "data": {
      "id": "opp-123",
      "url": "https://reddit.com/r/...",
      "title": "...",
      "draft": "..."
    },
    "signature": "sha256=..."
  }
  ```
- Delivery logs (for debugging):
  - Store last 100 webhook calls per webhook (URL, status, response)
- `src/frontend/pages/WebhooksPage.tsx` — UI:
  - List webhooks with test button
  - Create form (URL, event type)
  - View delivery history
- `tests/test_webhooks.py` — send, retry, signature

## Acceptance criteria
- [ ] Webhook POST request sent with correct signature
- [ ] Retry happens 3 times on failure
- [ ] 30-second timeout enforced
- [ ] HMAC-SHA256 signature verified by receiver
- [ ] Test endpoint available (send sample event)
- [ ] Delivery logs show last 100 events
- [ ] User can delete webhook
- [ ] Rate limiting: max 10 webhooks per user
- [ ] Webhook disabled after 10 consecutive failures

## Cross-module contracts
- Triggered by opportunity events (CORE-003, PIPE-001)
- Called by delivery service (DELIV-002)
- User config in FE-001
