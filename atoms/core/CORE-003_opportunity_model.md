# ATOM: CORE-003 — Opportunity model + contract

**Layer:** L1
**Module:** core
**Effort:** M
**Depends on:** CORE-001

## Inputs (what this atom reads/consumes)
- `src/backend/db/base.py` — `Base`
- BUZZREACH.md §7 — each delivered item carries: thread URL, why it matched, the draft reply

## Outputs (what this atom produces)
- `src/backend/models/opportunity.py` — `Opportunity` model, `__tablename__ = "opportunities"`, `__table_args__ = ({"schema": "buzzreach"},)`. Columns: `id`, `niche`, `url`, `title`, `source` (e.g. reddit/quora), `why_matched` (text), `relevance_score` (float), `draft_reply` (text), `status` (enum: `new`/`delivered`/`acted`/`skipped`, default `new`), `created_at`, `delivered_at` (nullable)
- `contracts/opportunity/opportunity.py` — `OpportunityData` Pydantic model mirroring the row shape (the cross-module DTO)
- `migrations/versions/<rev>_create_opportunities.py` — Alembic migration
- `tests/test_opportunity_model.py` — insert, status transitions, `OpportunityData.from_orm` round-trip

## Acceptance criteria
- [ ] Schema-qualified to `buzzreach`
- [ ] `status` constrained to the four allowed values
- [ ] `OpportunityData` contract validates against a persisted row
- [ ] Migration + `alembic check` pass (gate 14)
- [ ] `test_opportunity_model.py` passes

## Cross-module contracts
- PIPE-001 writes `Opportunity` rows. DELIV-001 and API-001 read them via `OpportunityData`.
- `contracts/opportunity/opportunity.py` is imported by pipeline, delivery, and api — changing it breaks their imports at compile time (BUILD_RULES §2).
