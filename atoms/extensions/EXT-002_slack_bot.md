# ATOM: EXT-002 — Slack Bot Integration

**Layer:** L3
**Module:** extensions
**Effort:** M
**Depends on:** API-001, DELIVERY-002

## Inputs (what this atom reads/consumes)
- Slack API (incoming webhooks, slash commands)
- `src/backend/models/opportunity.py` — opportunities

## Outputs (what this atom produces)
- `src/backend/services/slack_service.py`:
  - `send_opportunity_to_slack(user_id, opportunity_id)` → post formatted message
  - `send_digest_to_slack(user_id, opportunities)` → daily digest
  - Format: blocks with title, platform, score, copy button, link
- `src/backend/api/slack_webhooks.py` — webhook handlers:
  - POST `/api/v1/slack/events` — handle Slack events (message reactions, etc.)
  - POST `/api/v1/slack/slash` — handle `/buzzreach` slash command
- Slash commands:
  - `/buzzreach latest` — show 5 most recent opportunities
  - `/buzzreach search [keyword]` — find opportunities by keyword
  - `/buzzreach subscribe` — enable Slack digest delivery
  - `/buzzreach help` — show available commands
- User can configure:
  - Slack workspace in FE-001
  - Slack delivery preference (hourly/daily/weekly)
  - Disable/enable Slack notifications
- Slack message format:
  - Title (linked to thread)
  - Platform badge (reddit/quora/etc.)
  - Relevance score (5-star rating visual)
  - Draft reply (in text block)
  - Button: "Copy & Open" (links to web app, pre-selects opportunity)
  - Button: "Dismiss"
- Store `slack_workspace_id`, `slack_channel_id` per user
- `tests/test_slack_integration.py` — send message, handle slash command

## Acceptance criteria
- [ ] Slack workspace auth flow works (OAuth)
- [ ] Opportunities formatted nicely in Slack (readable, not text dump)
- [ ] `/buzzreach latest` returns 5 opportunities
- [ ] Buttons in Slack messages work (click → app action)
- [ ] Digest sent to configured channel at scheduled time
- [ ] User can unsubscribe from Slack notifications
- [ ] Rate limiting enforced (no spam)
- [ ] Slack API errors handled gracefully (retry + notify)
- [ ] No API keys exposed in Slack messages

## Cross-module contracts
- Uses Opportunity model (CORE-003)
- Integrated into delivery service (DELIV-002)
- User's Slack config stored in user settings (FE-001)
