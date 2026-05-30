# ATOM: PARSE-002 — Quora-Specific Content Parser

**Layer:** L2
**Module:** parsers
**Effort:** S
**Depends on:** EXT-001

## Inputs (what this atom reads/consumes)
- Quora HTML structure
- `src/backend/services/content_extractor.py` — generic extractor

## Outputs (what this atom produces)
- `src/backend/services/quora_parser.py`:
  - `parse_quora_question(html, url)` → extract question, answers, upvotes
  - Returns: { title (question), author, followers_count, answers: [{author, upvotes, text}, ...] }
  - Handles Quora's client-side rendering (optional JS parsing if needed, fallback to server-side)
- Parser activated when URL contains "quora.com"
- Falls back to generic extractor on parse failure
- Handles truncated/collapsed answers (expand hints)
- `tests/test_quora_parser.py` — test with sample Quora URLs

## Acceptance criteria
- [ ] Extracts question title + author correctly
- [ ] Gets answer count (or at least top answers)
- [ ] Extracts upvotes for each answer
- [ ] Works on main Quora domain (quora.com)
- [ ] Handles collapsed/truncated answers gracefully
- [ ] Performance: parse in <500ms
- [ ] Fallback to generic on any error
- [ ] Handles deleted questions (graceful failure)

## Cross-module contracts
- Integrates into EXT-001 pipeline
- Returns same schema as generic extractor
- Used by AI scorer (AI-002) for relevance
