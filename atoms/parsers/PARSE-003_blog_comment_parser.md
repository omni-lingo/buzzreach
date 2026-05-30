# ATOM: PARSE-003 — Blog & Forum Comment Parser

**Layer:** L2
**Module:** parsers
**Effort:** S
**Depends on:** EXT-001

## Inputs (what this atom reads/consumes)
- Blog/forum HTML (WordPress, Disqus, custom comment systems)
- `src/backend/services/content_extractor.py` — generic extractor

## Outputs (what this atom produces)
- `src/backend/services/blog_parser.py`:
  - `parse_blog_post(html, url)` → extract article + comment thread
  - Returns: { title, author, content (excerpt), comments: [{author, text, date}, ...] }
  - `parse_forum_thread(html, url)` → similar for forum posts
- Detects common comment systems:
  - Disqus (script-based, may need fallback)
  - WordPress native comments
  - Custom comment systems (by HTML pattern matching)
- Extracts:
  - Post title + author + publication date
  - Comment count
  - Top 5-10 comments (text, author, date)
  - Comment replies/threading (if available)
- Falls back to generic extractor if specific parser unavailable
- `tests/test_blog_parser.py` — test with sample blog URLs

## Acceptance criteria
- [ ] Extracts blog post title + content correctly
- [ ] Gets comments (author, text, date)
- [ ] Handles Disqus embedded comments
- [ ] Handles WordPress native comments
- [ ] Works on various blog platforms (Medium, Dev.to, custom)
- [ ] Performance: parse in <500ms
- [ ] Fallback to generic on any error
- [ ] Handles pagination (first N comments)

## Cross-module contracts
- Integrates into EXT-001 pipeline
- Returns same schema as generic extractor
- Used by AI scorer (AI-002)
