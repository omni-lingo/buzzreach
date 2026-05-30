# ATOM: FEAT-002 — Advanced Filtering System

**Layer:** L2
**Module:** features
**Effort:** M
**Depends on:** FILT-002, FE-002

## Inputs (what this atom reads/consumes)
- `src/backend/services/filter_service.py` — existing keyword filter
- `src/backend/models/opportunity.py` — Opportunity schema

## Outputs (what this atom produces)
- `src/backend/services/advanced_filter_service.py`:
  - `regex_filter(opportunities, patterns)` — reject if URL/title/content matches regex
  - `not_filter(opportunities, keywords)` — exclude if contains these words
  - `field_filter(opportunities, filters)` — filter by score, age, platform, domain
  - `composite_filter(opportunities, rules)` — combine AND/OR/NOT logic
- `src/backend/models/filter_rule.py` — store user-defined rules:
  - `id`, `user_id`, `name`, `rule_type` (regex/not/field/composite)
  - `patterns` (JSON), `description`, `enabled` (bool)
  - `created_at`, `updated_at`
- `src/frontend/pages/FiltersPage.tsx` — UI for creating rules:
  - "New Rule" form (type dropdown, pattern input, test button)
  - Rule list with enable/disable toggles
  - Delete rule button
  - Test rule against sample opportunities (preview)
- `src/backend/api/filters.py` — routes:
  - GET `/api/v1/filters` — list user's rules
  - POST `/api/v1/filters` — create rule
  - PUT `/api/v1/filters/{id}` — update rule
  - DELETE `/api/v1/filters/{id}` — delete rule
  - POST `/api/v1/filters/{id}/test` — test rule (return count of hits)
- Pipeline update (PIPE-001): after keyword pre-filter, apply user rules
- `tests/test_advanced_filters.py` — regex, NOT, field, composite filters

## Acceptance criteria
- [ ] Regex filter correctly matches/rejects URLs (test against common patterns)
- [ ] NOT filter case-insensitive keyword exclusion works
- [ ] Field filter on score range, platform, age works
- [ ] Composite filter with AND/OR logic works
- [ ] Rules stored persistently per user
- [ ] Pipeline applies rules in order (can disable to test)
- [ ] Test button shows preview of results
- [ ] Invalid regex rejected with helpful error
- [ ] Performance: 1000 opportunities filtered in <100ms
- [ ] Rules respect plan limits (free: max 3 rules, pro: max 20)

## Cross-module contracts
- Reads Opportunity model
- Integrates into pipeline (PIPE-001)
- Respects user's plan limits (BILL-002)
- Logged for audit trail (AUDIT-002)
