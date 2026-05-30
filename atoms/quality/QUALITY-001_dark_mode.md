# ATOM: QUALITY-001 — Dark Mode Theme

**Layer:** L4
**Module:** quality
**Effort:** S
**Depends on:** FE-002

## Inputs (what this atom reads/consumes)
- Existing React components (FE-001, FE-002, etc.)
- Tailwind CSS configuration

## Outputs (what this atom produces)
- `src/frontend/hooks/useTheme.ts` — theme context:
  - `useTheme()` hook returns { theme, toggleTheme }
  - Theme stored in localStorage (persist user preference)
  - System preference detected (prefers-color-scheme media query)
- `src/frontend/context/ThemeProvider.tsx` — wrapper component
- `src/frontend/styles/dark.css` — dark mode color overrides:
  - CSS custom properties (--bg-primary, --text-primary, --border-color, etc.)
  - Semantic naming (not light/dark-specific)
- Update all React components to use CSS vars instead of hardcoded colors
- Tailwind `dark:` prefix support in `tailwind.config.js`
- Toggle button in header (sun/moon icon)
- Mobile respects system setting by default
- `tests/e2e/dark-mode.spec.ts` — toggle theme, verify colors change

## Acceptance criteria
- [ ] User preference persists across sessions (localStorage)
- [ ] Light/dark mode toggle visible in header
- [ ] All text readable in both modes (sufficient contrast, WCAG AA)
- [ ] Images/screenshots look good in both modes
- [ ] System preference respected on first load
- [ ] No hard-coded colors in component styles (use CSS vars/Tailwind)
- [ ] Mobile app respects user's system dark mode setting
- [ ] Performance: no flicker when switching themes
- [ ] Print mode unaffected

## Cross-module contracts
- Used by all frontend modules (FE-001, FE-002, MOBILE-003, etc.)
- No backend changes needed
