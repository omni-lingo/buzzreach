# ATOM: QUALITY-004 — Niche Bundles (Pre-configured profiles)

**Layer:** L4
**Module:** quality
**Effort:** S
**Depends on:** FEAT-004

## Inputs (what this atom reads/consumes)
- Pre-configured niche settings (keywords, platforms, tone, templates)

## Outputs (what this atom produces)
- Pre-built search profile bundles (FEAT-004):
  - **Legal Services** — keywords: "lawsuit advice", "legal help", platforms: Reddit r/legaladvice, Avvo, etc.
  - **SaaS** — keywords: "alternative to", "which tool for", "best app for", platforms: Reddit r/SaaS, Product Hunt
  - **E-commerce** — keywords: "where to buy", "need recommendation", "best seller", platforms: Reddit r/ecommerce, forums
  - **Fitness** — keywords: "how to", "best workout", "effective", platforms: Reddit r/fitness, r/running
  - **Tech Support** — keywords: "error", "not working", "how to fix", platforms: Stack Overflow, Reddit r/techsupport
  - etc. (10-15 total)
- Each bundle includes:
  - Pre-configured keywords (copy-paste ready)
  - Recommended platforms
  - Suggested tone ("professional", "friendly", "technical")
  - 2-3 draft templates for that niche
  - Example product config (editable)
- `src/frontend/pages/NicheBundles.tsx` — bundle picker:
  - Show available bundles with descriptions
  - Click "Use this niche" → auto-populate settings
  - OR custom pick keywords from bundle + edit
- `src/backend/models/niche_bundle.py` — store bundles:
  - `id`, `name`, `description`, `keywords`, `platforms`, `templates`, `tone_guide`
- Applied bundle creates FEAT-004 search profile from template
- `tests/test_niche_bundles.py` — load, apply

## Acceptance criteria
- [ ] Bundles load from backend (or embedded JSON)
- [ ] 10+ pre-built niches available
- [ ] Click "use" → populates search profile
- [ ] Bundles editable after selection
- [ ] Templates included with each bundle
- [ ] Tone guide visible per bundle
- [ ] Mobile responsive

## Cross-module contracts
- Extends search profiles (FEAT-004)
- Uses templates (QUALITY-003)
- Helps onboarding flow (ONBOARD-003)
