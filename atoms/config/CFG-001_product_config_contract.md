# ATOM: CFG-001 — Product config contract

**Layer:** L2
**Module:** config
**Effort:** S
**Depends on:** INFRA-001

## Inputs (what this atom reads/consumes)
- BUZZREACH.md §2 / §7 — config holds: product URL, one-line pitch, niche, keywords, tone/persona, what to mention naturally, search freshness window
- `src/backend/settings.py` — `config_dir`

## Outputs (what this atom produces)
- `contracts/config/__init__.py`
- `contracts/config/product_config.py` — `ProductConfig` Pydantic model: `slug` (str), `product_url` (HttpUrl), `pitch` (str), `niche` (str), `keywords` (list[str], min 1), `tone` (str), `mention` (str), `freshness` (Literal["h","d","w"], default "d"), `max_queries` (int, default 5). Strict validation; no extra fields.
- `tests/test_product_config.py` — valid config parses; missing keywords / bad URL / empty slug rejected

## Acceptance criteria
- [ ] `ProductConfig` rejects empty keyword list and invalid URLs with clear validation errors
- [ ] `freshness` constrained to `h|d|w` (maps to Google `tbs=qdr:` in DISC-001)
- [ ] No `any`-equivalent loose typing; strict Pydantic config
- [ ] `test_product_config.py` passes

## Cross-module contracts
- CFG-002 (loader), DISC-001 (query builder), FILT-002 (keyword filter), AI-002/AI-003 (scoring/draft prompts) all import `ProductConfig`. It is the single source of truth for per-product settings.
