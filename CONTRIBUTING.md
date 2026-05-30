# Contributing to BuzzReach

## Atom-Based Development

BuzzReach uses atom-based development. Each atom is a complete, testable unit of work that produces working code, tests, and documentation updates.

## Before You Start

1. **Read the build rules:** [BUILD_RULES.md](BUILD_RULES.md)
   - File limits (≤ 300 lines), function limits (≤ 50 lines)
   - Required patterns (type hints, parameterized queries, error codes)
   - Forbidden patterns (import *, hardcoded secrets, SQL injection)

2. **Check build progress:** [BUILD_STATE.md](BUILD_STATE.md)
   - Pick a pending atom
   - Check its dependencies (blocked on another atom?)

3. **Understand the architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
   - Layer rules (L2 doesn't import L3, etc.)
   - Cross-module contracts
   - Data flow

## Building an Atom

### 1. Find a Ready Atom

```bash
python scripts/build-runner/run.py --status
```

Look for a pending atom with all dependencies complete.

### 2. Read the Atom Spec

Atom specs are in `atoms/{module}/{ATOM_ID}.md`. Example:

```markdown
# ATOM: AUTH-001 — User model & API key contract

**Layer:** L1
**Module:** auth
**Effort:** S
**Depends on:** INFRA-001

## Inputs
- `product.yaml` — project config

## Outputs
- `src/models/user.py` — User model
- `src/models/migrations/001_user.py` — migration
- `tests/test_user.py` — tests

## Acceptance Criteria
- [ ] User model with email, hashed_password, api_key fields
- [ ] Tests pass: pytest tests/test_user.py
- [ ] Migration applied to schema

## Cross-module Contracts
- Exported as: `contracts/auth/user.py`
- Used by: AUTH-002 (JWT service)
```

### 3. Build the Atom

```bash
# Manual: Read spec, write code, test locally
# Automated: Let Claude Code do it
python scripts/build-runner/run.py --atom AUTH-001
```

### 4. What the Runner Validates

After you commit, the runner checks (gates):

- ✅ All files in Outputs section exist
- ✅ File size ≤ 300 lines
- ✅ Function size ≤ 50 lines
- ✅ No forbidden patterns (import *, secrets, etc.)
- ✅ Tests pass
- ✅ Test file exists for each source file
- ✅ Lint passes (ruff, mypy)
- ✅ Cross-module imports don't break

If any gate fails, you get a fix prompt. The runner re-runs the gate loop until all pass.

## Testing

### Test Pyramid

```
     E2E (Playwright)     ← Critical journeys only
   Integration (API)      ← Every endpoint
 Unit (pytest/vitest)     ← Every function with logic
Contracts (type check)    ← Every cross-module boundary
Static Analysis (lint)    ← Every file
```

### Anti-Silo Test Pattern

For cross-module dependencies, write integration tests that exercise both sides:

```python
# tests/test_discovery_to_dashboard.py
async def test_dashboard_shows_discovered_opportunities():
    # L2: trigger discovery
    opps = await discovery_service.scan(user.id, search_params)
    
    # L1: verify persisted
    db_opps = await db.query(Opportunity).filter_by(user_id=user.id).all()
    assert len(db_opps) == len(opps)
    
    # L3: check API returns them
    resp = await client.post("/api/v1/opportunities", json={"user_id": user.id})
    assert len(resp.json()["opportunities"]) == len(opps)
    
    # L4: check dashboard renders
    dashboard = await page.goto("/dashboard")
    opp_tiles = await page.query_selector_all(".opportunity-card")
    assert len(opp_tiles) == len(opps)
```

### Running Tests

```bash
# Unit + integration
pytest tests/

# Specific module
pytest tests/test_auth.py -v

# With coverage
pytest --cov=src tests/

# E2E (requires server running)
playwright test tests/e2e/
```

## Code Style

### Python

```python
# Type hints required
def create_opportunity(
    user_id: UUID,
    url: str,
    title: str,
    score: float
) -> Opportunity:
    """Create and persist an opportunity."""
    opp = Opportunity(
        user_id=user_id,
        url=url,
        title=title,
        score=score,
    )
    db.session.add(opp)
    db.session.commit()
    return opp

# Structured logging
log.info("opportunity_created", extra={
    "opportunity_id": opp.id,
    "user_id": user_id,
    "score": score,
})

# Error codes, not just messages
if not user.api_key:
    raise AppError(
        code="AUTH_MISSING_API_KEY",
        message="API key required",
        status=401,
    )
```

### TypeScript

```typescript
// No `any` type
const opportunities: Opportunity[] = [];

// Type exports
export type OpportunityResponse = {
  id: string;
  title: string;
  score: number;
  url: string;
};
```

## Documentation Updates

When you change code, update the corresponding docs:

| Changed | Update |
|---------|--------|
| Models/migrations | `SCHEMA.md`, `contracts/schema.json` |
| Services/logic | `SYSTEM_MAP.md` |
| Routes/API | `API_SURFACE.md`, `openapi.json` |
| Architecture decision | `DECISIONS.md` (append-only) |

The runner auto-generates some docs after specific layers:
- L1 (models) → `contracts/schema_columns.json`
- L3 (routes) → `API_SURFACE.md`, `openapi.json`

## Committing

```bash
# Commit message format (runner enforces this)
[ATOM_ID] Brief description

More detail if needed. Explain WHY, not WHAT (code is self-explanatory).

# Example:
[AUTH-001] User model & API key contract

Added User model with password hashing and API key generation.
JWT service (AUTH-002) will consume the key_hash field.
```

## Review & Merge

1. **Gates pass** ✓ (runner checks)
2. **Tests pass** ✓ (gate 13)
3. **Code review** ✓ (team feedback)
4. **GitHub PR approved** ✓
5. **Merge to main** ✓
6. **Auto-push by runner** ✓

The runner automatically pushes each completed atom to GitHub.

## Debugging Failed Atoms

If an atom fails:

```bash
# View the failure
python scripts/build-runner/run.py --status

# See details
tail -f logs/build-runner.log

# Retry
python scripts/build-runner/run.py --atom AUTH-001
```

Common failures:
- **Files don't exist:** Outputs section missing files
- **Tests fail:** Logic error or missing test coverage
- **Lint error:** Code style violation (ruff, mypy)
- **Gate failure:** See BUILD_RULES.md

## Questions?

- **Build system:** See [README.md](README.md) Quick Start
- **Code standards:** See [BUILD_RULES.md](BUILD_RULES.md)
- **Architecture:** See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Current progress:** See [BUILD_STATE.md](BUILD_STATE.md)
