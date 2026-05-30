# ATOM: DELIV-001 — Digest builder

**Layer:** L2
**Module:** delivery
**Effort:** S
**Depends on:** CORE-003

## Inputs (what this atom reads/consumes)
- `contracts/opportunity/opportunity.py` — `OpportunityData`
- `src/backend/models/opportunity.py` + `src/backend/db/session.py`
- BUZZREACH.md §7 — each item shows: thread URL, why it matched, the draft reply

## Outputs (what this atom produces)
- `src/backend/services/delivery/__init__.py`
- `src/backend/services/delivery/digest.py` — `build_digest(opportunities) -> Digest` rendering each opportunity (url, why_matched, score, draft_reply) into a plain-text + HTML body. Also `fetch_new_opportunities(session, niche=None) -> list[OpportunityData]` selecting rows with `status="new"`.
- `contracts/delivery/digest.py` — `Digest` DTO: `subject`, `text_body`, `html_body`, `opportunity_ids`
- `tests/test_digest.py` — N opportunities render into a digest containing each URL + draft; empty set yields an "empty" digest

## Acceptance criteria
- [ ] Digest includes URL, why_matched, and the full draft_reply for every item
- [ ] Empty input produces a valid empty digest (no crash)
- [ ] `fetch_new_opportunities` only returns `status="new"` rows (parameterized query)
- [ ] `test_digest.py` passes

## Cross-module contracts
- DELIV-002 sends the `Digest`. JOB-001 calls `fetch_new_opportunities` + `build_digest`.
- `contracts/delivery/digest.py` imported by DELIV-002.
