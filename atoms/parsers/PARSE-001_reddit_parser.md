# ATOM: PARSE-001 — Reddit-Specific Content Parser

**Layer:** L2
**Module:** parsers
**Effort:** S
**Depends on:** EXT-001

## Inputs (what this atom reads/consumes)
- Reddit HTML structure
- `src/backend/services/content_extractor.py` — generic extractor

## Outputs (what this atom produces)
- `src/backend/services/reddit_parser.py`:
  - `parse_reddit_post(html, url)` → extract post title, author, upvotes, comment count, top comments
  - Returns: { title, author, score, num_comments, post_body, top_comments: [{author, score, body}, ...] }
  - Handles both old/new Reddit layouts
- Parser activated when URL contains "reddit.com"
- Falls back to generic extractor if parsing fails
- Caches parser result (same URL → same result)
- `tests/test_reddit_parser.py` — test with sample HTML/URLs

## Acceptance criteria
- [ ] Extracts post title + author correctly
- [ ] Gets upvote count (score)
- [ ] Extracts comment count
- [ ] Extracts top 5-10 comments (author, score, text)
- [ ] Works on new Reddit (reddit.com) and old (old.reddit.com)
- [ ] Handles deleted/removed posts gracefully
- [ ] Performance: parse in <500ms
- [ ] Fallback to generic extractor on any error
- [ ] Comments include user scores (upvotes)

## Cross-module contracts
- Integrates into EXT-001 pipeline
- Returns same schema as generic extractor
- Used by AI scorer (AI-002) for relevance
