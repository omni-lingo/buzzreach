# ATOM: FILT-002 — Keyword pre-filter

**Layer:** L2
**Module:** filter
**Effort:** S
**Depends on:** CFG-001

## Inputs (what this atom reads/consumes)
- `contracts/config/product_config.py` — `keywords`
- `contracts/discovery/candidate.py` — `Candidate` (title + snippet)
- BUZZREACH.md AD-6 — free string-match stage before any AI cost

## Outputs (what this atom produces)
- `src/backend/services/filter/keyword_filter.py` — `keyword_match(candidates, config) -> list[Candidate]`. Case-insensitive match of any configured keyword against `title + snippet`. Pure, no I/O, no AI.
- `tests/test_keyword_filter.py` — candidate containing a keyword kept; unrelated candidate dropped; matching is case-insensitive

## Acceptance criteria
- [ ] Zero network / zero AI calls (free stage)
- [ ] Case-insensitive substring match against title+snippet
- [ ] Pure function, deterministic
- [ ] `test_keyword_filter.py` passes

## Cross-module contracts
- PIPE-001 runs `keyword_match` as stage 3 (after dedup, before Haiku scoring) to keep AI cost down.
