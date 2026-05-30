# ATOM: QUALITY-003 — Draft Templates Library

**Layer:** L4
**Module:** quality
**Effort:** M
**Depends on:** FEAT-001

## Inputs (what this atom reads/consumes)
- Existing drafts (for learning)
- User feedback on drafts

## Outputs (what this atom produces)
- `src/backend/models/draft_template.py` — store templates:
  - `id`, `user_id` (owner, or null for global), `name`
  - `category` (platform: reddit/quora/blog, or style: technical/casual/etc.)
  - `description`, `text` (template with `{placeholders}`)
  - `created_at`, `updated_at`
- Global templates (provided by BuzzReach):
  - "Technical Support" (for programming topics)
  - "Legal Advice" (for legal questions)
  - "Product Recommendation" (for product comparison threads)
  - "Experience Share" (for story-based questions)
  - etc. (5-10 total)
- `src/frontend/pages/TemplatesPage.tsx` — library UI:
  - Browse templates by category
  - Search by name/description
  - Preview template text (with sample placeholders filled)
  - Create custom template button
- `src/frontend/components/TemplateSelector.tsx` — in draft editor:
  - "Use template" button
  - Select from list of relevant templates
  - Apply template → populate draft field
  - Edit applied template
- `src/backend/api/templates.py` — routes:
  - GET `/api/v1/templates?category=reddit` — list templates
  - POST `/api/v1/templates` — create custom template
  - PUT `/api/v1/templates/{id}` — update
  - DELETE `/api/v1/templates/{id}` — delete
- Template variable interpolation:
  - `{product_name}`, `{product_url}`, `{user_name}`, etc.
  - Auto-fill from user settings where possible
- `tests/test_templates.py` — create, apply, edit

## Acceptance criteria
- [ ] Global templates available without login
- [ ] Users can create custom templates
- [ ] Template text can include placeholders ({variable})
- [ ] Template selector available in draft editor
- [ ] Apply template pre-fills draft field
- [ ] Custom templates saved per user
- [ ] Templates shareable via link (optional)
- [ ] Search/filter works
- [ ] Performance: template list loads <100ms

## Cross-module contracts
- Used by draft editor (FEAT-001)
- Stored per user (AUTH-001)
- Optional: shared between team members (ADMIN-001)
