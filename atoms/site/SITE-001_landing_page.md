# ATOM: SITE-001 — Landing Page & Marketing Website

**Layer:** L4
**Module:** site
**Effort:** M
**Depends on:** none (separate project)

## Inputs (what this atom reads/consumes)
- Product messaging from BUZZREACH.md
- Design/branding (TBD)

## Outputs (what this atom produces)
- `marketing/` — Next.js or static site project
- `marketing/pages/index.tsx` — homepage:
  - Hero section (headline, subheading, CTA button → /signup)
  - Problem section (screenshots of manual community marketing pain)
  - Solution section (how BuzzReach automates it)
  - Features section (discover, filter, draft, paste)
  - Pricing section (free/pro/premium tiers)
  - Testimonials (dogfood products: ParkingAppealMate, IRS Calc)
  - FAQ
  - Footer (contact, legal, social)
- `marketing/pages/pricing.tsx` — pricing page with plan comparison
- `marketing/pages/docs/` — documentation site:
  - Getting started guide
  - API docs (auto-generated from OpenAPI)
  - FAQ
  - Contact page
- `marketing/public/` — assets (logo, screenshots, icons)
- `marketing/next.config.js` — next.js config

## Acceptance criteria
- [ ] Homepage loads in <3 seconds (Lighthouse score >90)
- [ ] Mobile responsive (tested on 320px+)
- [ ] /signup links to auth app (or redirects to app.buzzreach.com/signup)
- [ ] Pricing page shows all tiers + feature comparison
- [ ] All links work (no 404s)
- [ ] Social sharing metadata (Open Graph, Twitter Card)
- [ ] Contact form sends to email (or Slack)
- [ ] Legal pages (ToS, Privacy Policy) exist
- [ ] Google Analytics / tracking pixel installed
- [ ] Form submissions logged (marketing analytics)

## Cross-module contracts
- Separate codebase from backend/frontend
- Links to app instance for signup/login
- Displays public pricing info (BILL-002)
