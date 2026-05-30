# ATOM: FILT-001 — Dedup service (SQL lookup)

**Layer:** L2
**Module:** filter
**Effort:** S
**Depends on:** CORE-002

## Inputs (what this atom reads/consumes)
- `src/backend/models/seen_url.py` — `SeenUrl`
- `src/backend/db/session.py` — session
- `contracts/discovery/candidate.py` — `Candidate`
- BUZZREACH.md AD-4 — dedup is a $0 SQL lookup against our own actions

## Outputs (what this atom produces)
- `src/backend/services/filter/__init__.py`
- `src/backend/services/filter/dedup.py` — `filter_unseen(candidates, niche, session) -> list[Candidate]` (drops URLs already in `seen_urls` for that niche) and `mark_seen(url, niche, angle_covered, shown_to, session)`.
- `tests/test_dedup.py` — already-seen URL filtered out; `mark_seen` is idempotent on `(url, niche)`

## Acceptance criteria
- [ ] Parameterized queries only (gate 8) — never f-string SQL
- [ ] `filter_unseen` removes candidates whose `(url, niche)` already exists
- [ ] `mark_seen` respects the `(url, niche)` unique constraint (no duplicate rows)
- [ ] `test_dedup.py` passes against a real SQLite session

## Cross-module contracts
- PIPE-001 calls `filter_unseen` (stage 2) and `mark_seen` (after drafting). Writes only `SeenUrl`.
