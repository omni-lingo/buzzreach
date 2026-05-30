# BUILD RULES — What Claude Must Follow While Writing Product Code

> **Audience:** Every Claude session building atoms for this product.
> **Size:** ~280 lines. Context loading table selects which sections to load per atom type — not all sections load every time.
> **[CODE]** = Runner gates enforce it. You'll get a fix prompt if you violate it.
> **[CONVENTION]** = No gate catches it. You must follow it yourself.

---

## 1. File & Function Limits [CODE]

| Metric | Limit | What happens if violated |
|--------|-------|--------------------------|
| Lines per file | 300 | Gate blocks commit. Fix prompt sent. |
| Lines per function | 50 | Gate blocks commit. Fix prompt sent. |
| Cyclomatic complexity | 10 | Lint catches it. |
| Nesting depth | 4 | Lint catches it. |

Split files by domain, not by size. If `order_service.py` hits 300 lines, extract `order_validation.py` — not `order_service_part2.py`.

---

## 2. Architecture [CONVENTION]

### Layered build order

```
L1: Models & migrations      → database schema
L2: Services & business logic → pure logic, no HTTP
L3: Routes & API endpoints    → HTTP layer, calls L2
L4: Frontend pages            → calls L3 via API client
L5: Tests & integration       → validates L1-L4 together
```

Never skip a layer. L3 must not contain business logic. L2 must not import from L3.

### Schema-qualified models — always

```python
class Order(Base):
    __tablename__ = "orders"
    __table_args__ = {"schema": "your_schema"}  # MANDATORY
```

No exceptions. Unqualified table names collide when sharing a database.

### Cross-module contracts are code

If module A's output feeds module B's input, both import a shared contract:

```python
# contracts/orders/order_event.py — shared type
@dataclass
class OrderCreatedEvent:
    order_id: UUID
    customer_id: UUID
    total_amount: Decimal
```

Module B imports this. If module A changes the contract, module B's import breaks at compile time, not runtime.

---

## 3. Forbidden Patterns [CODE]

These are caught by gates. You'll get a fix prompt if you use them.

| Pattern | Why |
|---------|-----|
| `from app.models import *` | Hides dependencies |
| `allow_origins = ["*"]` | Security: open CORS |
| `f"SELECT ... {user_input}"` | SQL injection |
| `password = "hardcoded"` | Leaked secret |
| `: any` (TypeScript) | Defeats type system |
| `eval()`, `.innerHTML =`, `document.write()` | XSS / code injection |
| `# type: ignore` without reason | Hides type errors |
| `console.log` in production code | Noise |
| Commented-out code | Dead code |
| Unused imports / variables | Dead code |

---

## 4. Required Patterns [CONVENTION]

| Pattern | Example |
|---------|---------|
| Type hints on all functions | `def create(item: Item) -> Order:` |
| Strict TypeScript | `const x: string`, never `any` |
| Parameterized queries only | `text("SELECT * WHERE id = :id"), {"id": val}` |
| Schema-qualified table names | `__table_args__ = {"schema": "your_schema"}` |
| Structured logging | `log.info("created", extra={"order_id": id})` |
| Error codes, not just messages | `raise AppError(code="ORDER_NOT_FOUND", ...)` |
| Pydantic schemas on API responses | `response_model=OrderResponse` |
| API versioning | All endpoints under `/api/v1/` |

---

## 5. Atom Spec Format [CONVENTION]

Every atom you build has this spec. Follow it exactly.

```markdown
# ATOM: {MODULE}-{NNN} — {Title}

**Layer:** L1|L2|L3|L4|L5
**Module:** {module_name}
**Effort:** S|M|L
**Depends on:** {ATOM_IDs or "none"}

## Inputs (what this atom reads/consumes)
- `path/to/file.py` — what you need from it

## Outputs (what this atom produces)
- `path/to/new_file.py` — what you'll create
- `tests/test_new_file.py` — test for it

## Acceptance criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Cross-module contracts
- Which other modules will import from your outputs
- Which contracts you must maintain compatibility with
```

**Rules:**
- Every file in Outputs MUST exist on disk after you commit. The runner verifies this.
- Every file in Outputs that is a source file MUST have a corresponding test.
- Cross-module contracts section is NOT optional. If nothing depends on this atom, write "None — leaf module."

---

## 6. Testing [CODE + CONVENTION]

### Test pyramid

```
      /  E2E (Playwright)  \          ← Critical journeys only
     /  Integration (API)    \        ← Every endpoint
    /  Unit (pytest/vitest)    \      ← Every function with logic
   /  Contracts (type check)     \    ← Every cross-module boundary
  /  Static Analysis (lint/mypy)   \  ← Every file
```

### Rules

| Rule | Enforced by |
|------|-------------|
| Changed module has test file | Gate 12 |
| Tests pass | Gate 13 |
| New function → test first (TDD) | Convention |
| Bug fix → regression test first | Convention |
| Cross-module boundary → contract test | Convention |
| No "add tests later" | Gate 12 |

### Anti-silo test pattern

For every cross-module dependency, write an integration test that exercises BOTH sides:

```python
async def test_dashboard_shows_orders():
    order = await create_order({"item": "Widget", "qty": 5})
    dashboard = await get_dashboard()
    assert any(o["id"] == order["id"] for o in dashboard["recent_orders"])
```

If module A produces data and module B consumes it, there must be a test that runs A then checks B.

---

## 7. Doc Maintenance [CONVENTION]

**Rule: Never commit code changes without updating corresponding docs.**

| If you changed... | Update... |
|---|---|
| Models / migrations | `contracts/schema.json`, `SCHEMA.md` |
| Services / logic | `SYSTEM_MAP.md` |
| Routes / API | `API_SURFACE.md`, `openapi.json` |
| Background jobs | `SYSTEM_MAP.md` (jobs section) |
| Middleware / auth | `SECURITY.md` |
| Frontend routes | `ROUTES.md` |
| Dependencies | `DEPENDENCIES.md` |
| Architecture decisions | `DECISIONS.md` (append-only) |
| Conventions | `CONVENTIONS.md` |
| New public symbols (class, function, endpoint) | `DEPENDENCY_MAP.md` |

The runner auto-generates some docs after specific layers:

| Layer | Auto-generated |
|-------|---------------|
| L1 (models) | `contracts/schema_columns.json` |
| L3 (routes) | `API_SURFACE.md`, `openapi.json` |
| All | `DEPENDENCY_MAP.md` freshness check (gate warns if stale) |

You still update the rest manually.

---

## 8. Naming [CONVENTION]

| Thing | Convention | Example |
|-------|-----------|---------|
| Python files | `snake_case.py` | `order_service.py` |
| Python classes | `PascalCase` | `OrderService` |
| Python functions | `snake_case` | `create_order()` |
| TypeScript files | `PascalCase.tsx` (components), `camelCase.ts` (utils) | `OrderList.tsx`, `orderApi.ts` |
| Database tables | `snake_case`, plural | `orders`, `order_items` |
| API endpoints | `/api/v1/{resource}`, plural | `/api/v1/orders` |
| Atom IDs | `{MODULE}-{NNN}` | `AUTH-001` |

---

## 9. Error Handling [CONVENTION]

```python
# At system boundaries (user input, external APIs): validate everything
@router.post("/orders")
async def create_order(req: OrderCreate):  # Pydantic validates
    ...

# Internal code: trust your types
def calculate_total(items: list[OrderItem]) -> Decimal:
    return sum(item.price * item.quantity for item in items)
    # Don't: if not items: raise ValueError("empty")
```

- Generic errors to client (never stack traces)
- Detailed errors to server logs (structured JSON)
- Error codes on every error response (`error_code`, not just `message`)

---

## 10. Logging [CONVENTION]

```python
# Structured, with context
log.info("Order created", extra={"order_id": order.id, "user_id": user.id})

# NEVER:
log.info(f"Order {order.id} created by {user.id}")
print(f"order created")
```

---

## 11. What The Runner Handles (Don't Think About These)

The runner handles these silently. You don't need to think about them:

| Concern | Runner handles it |
|---------|-------------------|
| Which model to use (Sonnet/Opus) | Auto-selected by atom effort (S/M/L) |
| How many turns you get | Set by effort: S=30, M=50, L=75 |
| What happens if gates fail | Fix loop re-invokes you with just the errors |
| What happens on rate limit | Runner waits, unclaims, retries later |
| What happens on timeout | Runner retries with continue prompt |
| What happens on crash | State saved, handover written, resume on restart |
| Cost tracking | Runner logs tokens + USD per atom |
| Parallel safety | Claim system prevents collisions |
| Cross-module validation | Runner checks importers after every commit |
| Doc auto-generation | Runner triggers per-layer scripts |
| Push to remote | Runner pushes after every successful atom |
| Commit message format | Runner commits as `[ATOM_ID] description` |
| Branch creation/merge | Runner creates `atom/ATOM_ID` branches |
| Completion signal | Runner detects commit, no signal needed from you |

**Your job: write correct code that follows the rules above. The runner handles everything else.**

---

## 12. Anti-Silo Awareness [CONVENTION]

Before writing any code, check:

1. **Does my atom's input come from another module?** → Import from `contracts/`, not directly from the other module's internals.
2. **Will another module consume my output?** → Declare the contract in `contracts/`. List it in atom spec's "Cross-module contracts" section.
3. **Am I changing a model that other modules read?** → The runner will catch import breaks after your commit, but YOU should proactively check `DEPENDENCY_MAP.md` to see who depends on what you're changing.
4. **Am I changing an API response shape?** → Check if any frontend service files reference this endpoint. Update the contract.

The runner validates cross-module integrity after every atom. But catching issues before commit is faster than fixing them after a gate failure.
