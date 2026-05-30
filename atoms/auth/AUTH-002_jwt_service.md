# ATOM: AUTH-002 — JWT service (sign, verify, refresh)

**Layer:** L2
**Module:** auth
**Effort:** M
**Depends on:** AUTH-001

## Inputs (what this atom reads/consumes)
- `src/backend/models/user.py` — `User`
- `contracts/auth/user.py` — `UserData`
- `src/backend/settings.py` — `jwt_secret_key` (from env, HMAC HS256)
- `src/backend/db/session.py` — session (to verify user exists)

## Outputs (what this atom produces)
- `src/backend/services/auth/__init__.py`
- `src/backend/services/auth/jwt_service.py` — `JwtService`. Methods:
  - `create_token(user_id: UUID) -> str` (JWT claims: `sub=user_id`, `iat`, `exp` (expires in 1 hour, configurable))
  - `verify_token(token: str) -> UUID` (returns user_id; raises `AppError(code="TOKEN_INVALID")` / `code="TOKEN_EXPIRED"`)
  - `refresh_token(old_token: str) -> str` (verifies old token, issues new one)
  - `hash_password(plaintext: str) -> str` and `verify_password(plaintext, hash) -> bool` (bcrypt)
- `contracts/auth/jwt.py` — `JwtPayload` DTO (for testing/transparency)
- `tests/test_jwt_service.py` — create token, verify it, expired token rejected, invalid token raises coded error, password hash round-trip

## Acceptance criteria
- [ ] Token signed with `jwt_secret_key` from env (gate 9 — no hardcoded key)
- [ ] Invalid/expired tokens raise `AppError` with specific code (never bare `ValueError`)
- [ ] Password hashing uses bcrypt (industry standard)
- [ ] All cryptographic ops use secure libraries (no custom crypto)
- [ ] `test_jwt_service.py` passes

## Cross-module contracts
- API-001 uses `verify_token()` in a FastAPI dependency to protect routes
- AUTH-001 contract imported for user context
