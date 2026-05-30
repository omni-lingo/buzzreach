# ATOM: EXT-001 — Browser Extension (Chrome/Firefox/Edge)

**Layer:** L4
**Module:** extensions
**Effort:** M
**Depends on:** API-001, FE-002

## Inputs (what this atom reads/consumes)
- Manifest V3 specification
- API endpoints from API-001
- User's API key from settings

## Outputs (what this atom produces)
- `extensions/browser-extension/` — Chrome/Firefox extension:
  - `manifest.json` (V3, minimal permissions)
  - `src/popup.tsx` — extension popup:
    - Logged-in users see "Check for opportunities on this page"
    - Shows 3 most recent opportunities (if on Reddit/Quora)
    - Direct "Copy Draft & Reply" button
  - `src/background.ts` — service worker:
    - Listen for page navigation to Reddit/Quora/etc.
    - Fetch opportunity metadata for current page (URL match)
    - Show badge with count ("2 opportunities on this thread")
  - `src/content.ts` — content script (optional):
    - Highlight BuzzReach-matched threads inline
    - Context menu: "View BuzzReach opportunities for this thread"
  - `public/icons/` — icons for toolbar
  - `public/style.css` — popup styling
- API endpoint: GET `/api/v1/extension/opportunities?current_url={url}` → matching opportunities
- Installation: user inputs API key in extension options page
- Chrome Web Store listing (metadata + screenshots)

## Acceptance criteria
- [ ] Extension loads without errors in Chrome/Firefox
- [ ] User can input API key in options page (stored in extension storage)
- [ ] Popup shows 3 recent opportunities
- [ ] Badge shows count if matching opportunities on current page
- [ ] "Copy Draft & Reply" button opens opportunity detail + copy
- [ ] Current URL sent securely to API (HTTPS only)
- [ ] No data logged/tracked beyond API calls
- [ ] Works on Reddit, Quora, forums (tested URLs)
- [ ] Manifest V3 compliant (no insecure APIs)
- [ ] Icon visible in toolbar

## Cross-module contracts
- Calls API-001 (`/extension/opportunities` endpoint)
- Uses UserData + OpportunityEvent contracts
- Stores API key in extension storage (encrypted best-effort)
