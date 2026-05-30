# ATOM: PIPE-001 — Tiered pipeline orchestrator

**Layer:** L2
**Module:** pipeline
**Effort:** L
**Depends on:** DISC-003, EXT-001, FILT-001, FILT-002, AI-002, AI-003, CORE-002, CORE-003, AUDIT-002, OBSERV-001

## Inputs (what this atom reads/consumes)
- `src/backend/services/discovery/discovery_service.py` — `discover`
- `src/backend/services/auth/rate_limiter.py` — `RateLimiter` injected to discovery
- `src/backend/services/filter/dedup.py` — `filter_unseen`, `mark_seen`
- `src/backend/services/filter/keyword_filter.py` — `keyword_match`
- `src/backend/services/extraction/extractor.py` — `extract`
- `src/backend/services/ai/scorer.py` — `score`, `RelevanceResult`
- `src/backend/services/ai/draft.py` — `draft_reply`
- `src/backend/services/auth/audit_service.py` — `AuditService` to log opportunities generated
- `src/backend/services/observability/metrics.py` — `MetricsRecorder` to track candidates found, AI tokens, drafts generated
- `src/backend/models/opportunity.py` + `contracts/opportunity/opportunity.py`
- `contracts/config/product_config.py` — `ProductConfig`
- BUZZREACH.md AD-6 — order the stages so the expensive model runs last

## Outputs (what this atom produces)
- `src/backend/services/pipeline/__init__.py`
- `src/backend/services/pipeline/runner.py` — `run_pipeline(config, deps, session) -> list[OpportunityData]`. Executes: discover → dedup (SQL) → keyword pre-filter → extract → Haiku score → (gate) → Sonnet draft → persist `Opportunity` → audit log `'opportunity_generated'` with niche + draft length → `mark_seen` with `angle_covered`. Dependencies injected (so each stage is mockable). Keep each function ≤ 50 lines (split stage helpers into `src/backend/services/pipeline/stages.py` if needed).
- `src/backend/services/pipeline/stages.py` — per-stage helpers (if the runner would exceed limits)
- `tests/test_pipeline_runner.py` — full pipeline with every external dep stubbed (audit_service included): a seeking-help candidate produces a persisted `Opportunity` + an audit log row + a `seen_urls` row; an already-seen candidate is skipped before any AI call (audit not called)

## Acceptance criteria
- [ ] Stage order matches AD-6; AI scoring/drafting only runs on candidates surviving the free stages
- [ ] Drafting runs only when scorer says seeking-help, angle not covered, score ≥ threshold
- [ ] Each processed opportunity creates exactly one `Opportunity` row and one `seen_urls` row
- [ ] Each draft generation logs metrics: candidates found, AI tokens used, drafts generated (metric recorder injected)
- [ ] Already-seen candidates never reach the AI stages (assert AI mocks not called)
- [ ] All deps injected; no module reaches across to another's internals (anti-silo, gate 15/16)
- [ ] `test_pipeline_runner.py` passes (metrics_recorder mocked); every file ≤ 300 lines, every function ≤ 50 lines

## Cross-module contracts
- Consumes the contracts from discovery, extraction, scoring; writes `Opportunity` (CORE-003) and `SeenUrl` (CORE-002).
- JOB-001 calls `run_pipeline` per product config. DELIV-001 reads the resulting `Opportunity` rows.
