# ATOM: AI-001 — Anthropic client wrapper

**Layer:** L2
**Module:** ai
**Effort:** M
**Depends on:** INFRA-001

## Inputs (what this atom reads/consumes)
- `src/backend/settings.py` — `anthropic_api_key`
- BUZZREACH.md AD-6 — tiered models: Haiku for scoring, Sonnet for drafting

## Outputs (what this atom produces)
- `src/backend/services/ai/__init__.py`
- `src/backend/services/ai/client.py` — `AiClient` wrapping the `anthropic` SDK. `complete(model, system, user, max_tokens) -> str`. Enables prompt caching on the system block. Model ids surfaced as constants: `HAIKU = "claude-haiku-4-5-20251001"`, `SONNET = "claude-sonnet-4-6"`. Retries on rate limit; raises `AppError(code="AI_PROVIDER_ERROR")` on hard failure.
- `tests/test_ai_client.py` — client builds the request and parses text (SDK mocked, no live call); error path raises coded error

## Acceptance criteria
- [ ] API key sourced only from settings/env (gate 9 — no hardcoded key)
- [ ] Haiku and Sonnet model ids exposed as named constants
- [ ] Prompt caching enabled on the static system prompt
- [ ] SDK fully mocked in tests; failure → `AppError(code="AI_PROVIDER_ERROR")`
- [ ] `test_ai_client.py` passes

## Cross-module contracts
- AI-002 (scorer) and AI-003 (draft) depend on `AiClient` and the model constants. This is the only module that talks to the Anthropic API.
