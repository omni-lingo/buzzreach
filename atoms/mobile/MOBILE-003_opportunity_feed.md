# ATOM: MOBILE-003 — Mobile Opportunity Feed

**Layer:** L4
**Module:** mobile
**Effort:** M
**Depends on:** FE-002, MOBILE-002

## Inputs (what this atom reads/consumes)
- `src/backend/api/opportunities.py` — list opportunities
- FE-002 design (dashboard UI)

## Outputs (what this atom produces)
- `src/mobile/src/screens/FeedScreen.tsx` — opportunity feed:
  - Scrollable list of cards (platform, title, score, snippet)
  - Pull-to-refresh functionality
  - Swipe left to archive/dismiss
  - Swipe right to copy draft + open URL
  - Tap for full details modal
- `src/mobile/src/components/OpportunityCard.mobile.tsx` — optimized for touch:
  - Large hit targets (48dp minimum)
  - Condensed layout (mobile width)
  - Draft preview (first 100 chars)
- `src/mobile/src/screens/OpportunityDetail.tsx` — modal:
  - Full opportunity data (title, URL, platform, score reason)
  - Full draft reply text (scrollable)
  - "Copy to Clipboard" button (large)
  - "Open in Browser" button
  - "Mark as Posted" button
  - "Archive" button
  - "Regenerate Draft" button (if FEAT-005 available)
- `src/mobile/src/api/opportunities.ts` — fetch with pagination
- Pull-to-refresh triggers `/api/v1/opportunities?refresh=true`
- Swipe gestures via React Native Gesture Handler

## Acceptance criteria
- [ ] Feed loads and displays 20 opportunities on launch
- [ ] Scrolling is smooth (no jank at 60fps)
- [ ] Pull-to-refresh fetches new opportunities (visual spinner)
- [ ] Swipe left dismisses card (animated)
- [ ] Swipe right opens detail modal (not yet opening browser)
- [ ] Detail modal shows full draft text
- [ ] Copy button adds draft to clipboard
- [ ] Open button launches browser with URL
- [ ] Mark as Posted removes from feed + logs action
- [ ] Buttons accessible (tap area 48x48dp)
- [ ] No draft text exposed until user taps (privacy)

## Cross-module contracts
- Calls API-001 (`/opportunities` endpoint)
- Uses `OpportunityEvent` contract
- Integrates with MOBILE-004 (URL launcher)
