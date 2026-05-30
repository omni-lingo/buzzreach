# ATOM: AI-003 — Draft generator (Sonnet)

**Layer:** L2
**Module:** ai
**Effort:** M
**Depends on:** AI-001, EXT-001, CFG-001

## Inputs (what this atom reads/consumes)
- `src/backend/services/ai/client.py` — `AiClient`, `SONNET`
- `contracts/extraction/extracted_content.py` — `ExtractedContent`
- `contracts/config/product_config.py` — `tone`, `pitch`, `mention`, `product_url`
- BUZZREACH.md §6 — drafts must read human, lead with real help, mention the product naturally, not repeat existing comments

## Outputs (what this atom produces)
- `src/backend/services/ai/draft.py` — `draft_reply(content, config, client) -> str`. Builds a Sonnet prompt that: leads with genuine help, matches `config.tone`, mentions the product naturally per `config.mention`, and is told the existing comments so it does not repeat them.
- `contracts/scoring/draft_request.py` — (optional helper) `DraftContext` DTO bundling content+config for the prompt
- `tests/test_draft.py` — given a mocked Sonnet response, returns the reply string; prompt includes existing comments and tone (assert on the constructed prompt)

## Acceptance criteria
- [ ] Uses the `SONNET` model constant (quality stage)
- [ ] Prompt includes existing comments so the reply avoids repetition
- [ ] Prompt incorporates `tone`, `pitch`, `mention`, `product_url`
- [ ] AI client mocked in tests; no live call
- [ ] `test_draft.py` passes

## Cross-module contracts
- PIPE-001 calls `draft_reply()` as stage 5 (only on confirmed opportunities) and stores the result in `Opportunity.draft_reply`.
