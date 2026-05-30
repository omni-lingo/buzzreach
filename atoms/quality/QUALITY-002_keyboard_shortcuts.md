# ATOM: QUALITY-002 — Keyboard Shortcuts

**Layer:** L4
**Module:** quality
**Effort:** S
**Depends on:** FE-002, MOBILE-003

## Inputs (what this atom reads/consumes)
- React components (FE-002, FEAT-001, etc.)

## Outputs (what this atom produces)
- `src/frontend/hooks/useKeyboardShortcuts.ts` — hook for binding shortcuts
- `src/frontend/utils/keyboard.ts` — helper functions
- Shortcuts on Dashboard (FE-002):
  - `j` → next opportunity
  - `k` → previous opportunity
  - `c` → copy draft to clipboard
  - `o` → open thread in new tab
  - `a` → archive opportunity
  - `p` → mark as posted
  - `r` → regenerate draft
  - `?` → show help modal (list all shortcuts)
  - `Shift+P` → show posted opportunities
  - `Escape` → close modal
- Settings page (FE-001):
  - `s` → scroll to search
  - `g` then `s` → go to settings
- Global:
  - `Ctrl+/` or `Cmd+/` → toggle command palette (Slack-style)
  - `Ctrl+K` → search opportunities
- Help modal (`src/frontend/components/KeyboardHelp.tsx`):
  - Shows all available shortcuts
  - Contextual (different shortcuts per page)
  - Keyboard-navigable (arrow keys to select)
- Disable shortcuts input in text fields (no `j` while typing in draft editor)
- Mobile: optional shortcut bar (buttons with letters) for accessibility
- `tests/e2e/keyboard-shortcuts.spec.ts` — test `j/k`, `c`, `p`, escape

## Acceptance criteria
- [ ] Shortcuts work on Dashboard page (j/k navigation)
- [ ] Copy shortcut (c) adds draft to clipboard
- [ ] Open shortcut (o) opens thread
- [ ] Archive shortcut (a) removes from feed
- [ ] Mark posted shortcut (p) logs action
- [ ] Regenerate shortcut (r) calls API (if available)
- [ ] Help modal shows with `?`
- [ ] Shortcuts don't interfere with text input
- [ ] Escape closes modals
- [ ] Mobile has optional shortcut bar

## Cross-module contracts
- Used by all frontend modules
- No backend changes needed
