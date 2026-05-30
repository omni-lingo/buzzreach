# ATOM: AI-002 — Relevance scorer (Haiku)

**Layer:** L2
**Module:** ai
**Effort:** M
**Depends on:** AI-001, EXT-001, CFG-001

## Inputs (what this atom reads/consumes)
- `src/backend/services/ai/client.py` — `AiClient`, `HAIKU`
- `contracts/extraction/extracted_content.py` — `ExtractedContent`
- `contracts/config/product_config.py` — `ProductConfig`
- BUZZREACH.md AD-6 — "Is this person seeking help? Is the angle already covered?"

## Outputs (what this atom produces)
- `src/backend/services/ai/scorer.py` — `score(content, config, client) -> RelevanceResult`. Builds a Haiku prompt from the question + existing comments + product pitch; parses a structured JSON verdict.
- `contracts/scoring/relevance.py` — `RelevanceResult` Pydantic model: `score` (0-1 float), `is_seeking_help` (bool), `angle_already_covered` (bool), `reason` (str)
- `tests/test_scorer.py` — given a mocked Haiku JSON response, returns a valid `RelevanceResult`; malformed model output handled gracefully

## Acceptance criteria
- [ ] Uses the `HAIKU` model constant (cheap stage)
- [ ] Returns a validated `RelevanceResult`; `score` clamped to 0-1
- [ ] Malformed AI output raises `AppError(code="AI_BAD_OUTPUT")` rather than crashing
- [ ] AI client mocked in tests
- [ ] `test_scorer.py` passes

## Cross-module contracts
- PIPE-001 calls `score()` as stage 4 and only proceeds to drafting when `is_seeking_help` and not `angle_already_covered` and `score` ≥ threshold.
- `contracts/scoring/relevance.py` imported by pipeline.
