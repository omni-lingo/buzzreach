# ATOM: AUTH-001 — User model & API key contract

**Layer:** L1
**Module:** auth
**Effort:** S
**Depends on:** CORE-001

## Inputs (what this atom reads/consumes)
- `src/backend/db/base.py` — `Base`
- BUILD_RULES.md §2 — schema-qualified models always

## Outputs (what this atom produces)
- `src/backend/models/user.py` — `User` model, `__tablename__ = "users"`, `__table_args__ = ({"schema": "buzzreach"},)`. Columns: `id` (UUID PK), `username` (str, unique), `email` (str, unique), `password_hash` (str, never plain-text), `api_key` (str, unique, indexed, generated on create), `is_active` (bool, default True), `created_at`, `updated_at`. No actual password field — hashing is service-layer (AUTH-002).
- `contracts/auth/user.py` — `UserData` Pydantic model: `id`, `username`, `email`, `is_active` (DTO for cross-module use, never includes `password_hash` or `api_key`)
- `migrations/versions/<rev>_create_users.py` — Alembic migration
- `tests/test_user_model.py` — create a user row; query by username/email/api_key; is_active flag works

## Acceptance criteria
- [ ] Schema-qualified to `buzzreach`
- [ ] Unique constraint on `username`, `email`, `api_key` prevents collisions
- [ ] No plain-text password stored (column is `password_hash` only)
- [ ] `UserData` contract never exposes `password_hash` or `api_key`
- [ ] Migration + `alembic check` pass (gate 14)
- [ ] `test_user_model.py` passes

## Cross-module contracts
- AUTH-002 (JWT service) reads User to validate credentials
- API-001 reads User via JWT token
- `contracts/auth/user.py` is imported by AUTH-002 and API-001 (the boundary contract)
