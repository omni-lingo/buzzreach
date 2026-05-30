# ATOM: MOBILE-004 — One-Click Copy & URL Launcher

**Layer:** L4
**Module:** mobile
**Effort:** S
**Depends on:** MOBILE-003

## Inputs (what this atom reads/consumes)
- MOBILE-003 opportunity feed
- React Native linking API

## Outputs (what this atom produces)
- `src/mobile/src/components/OpportunityActions.tsx` — action buttons:
  - Large "Copy Draft" button (primary color, tap area 56x56dp)
  - Large "Open Thread" button (secondary color)
- Copy action (`src/mobile/src/utils/clipboard.ts`):
  - Tap "Copy Draft" → draft text copied to clipboard
  - Toast: "Copied to clipboard" (green, auto-dismiss in 2s)
  - Can immediately switch to Reddit app/browser and paste
  - Works in background (clipboard accessible while app is backgrounded)
- URL launcher (`src/mobile/src/utils/urlLauncher.ts`):
  - Tap "Open Thread" → opens URL in native browser
  - Or: opens Reddit app if user has it installed (intent/deeplink)
  - Preserves user's logged-in session
  - Returns to BuzzReach app on back button
- Clipboard content includes:
  - Draft text (primary)
  - Optional: "Posted via BuzzReach" footer (user can disable)
  - No metadata/logging in clipboard itself
- Clipboard management:
  - Clear clipboard on logout (privacy)
  - User can clear manually (settings)
- `tests/test_mobile_actions.tsx` — clipboard, URL launch

## Acceptance criteria
- [ ] Copy button adds draft to system clipboard
- [ ] Toast confirms copy action
- [ ] Paste works in Reddit/Quora/browser
- [ ] Open button launches URL in browser
- [ ] Reddit app launch works (if installed)
- [ ] Return to app on back button
- [ ] Clipboard cleared on logout
- [ ] Works in background (clipboard available after app backgrounded)
- [ ] No network calls needed (local clipboard)
- [ ] Accessible: tap area 56x56dp minimum

## Cross-module contracts
- Integrates into MOBILE-003 (opportunity detail)
- No backend calls (pure client)
- Logs action via FEAT-003 (post-action tracking)
