# ATOM: EXT-001 — Content extractor

**Layer:** L2
**Module:** extraction
**Effort:** M
**Depends on:** INFRA-001

## Inputs (what this atom reads/consumes)
- BUZZREACH.md AD-5 — generic Readability-style extractor (post body + comments); no per-site parsers in MVP
- `src/backend/settings.py` — timeouts

## Outputs (what this atom produces)
- `src/backend/services/extraction/__init__.py`
- `src/backend/services/extraction/extractor.py` — `extract(url, fetcher=...) -> ExtractedContent`. Fetches the page via `httpx`, runs `readability-lxml` + `beautifulsoup4` to pull the main body and visible comment text. Truncates to a configurable char budget so downstream AI cost stays bounded. Raises `AppError(code="EXTRACTION_FAILED")` on unrecoverable fetch/parse errors.
- `contracts/extraction/extracted_content.py` — `ExtractedContent` Pydantic model: `url`, `title`, `body`, `comments` (list[str]), `truncated` (bool)
- `tests/test_extractor.py` — a saved HTML fixture extracts body + comments; fetch failure raises coded error (HTTP mocked)

## Acceptance criteria
- [ ] Extraction runs on a local HTML fixture with no live network in tests
- [ ] Output truncated to the char budget; `truncated` flag set correctly
- [ ] Fetch/parse failure → `AppError(code="EXTRACTION_FAILED")`
- [ ] No `eval`/`innerHTML`/unsafe HTML execution (gate 11)
- [ ] `test_extractor.py` passes

## Cross-module contracts
- AI-002 (scorer) and AI-003 (draft) consume `ExtractedContent` (question + existing replies) so the draft does not repeat what's already said.
- PIPE-001 calls `extract()` after dedup/keyword filtering.
