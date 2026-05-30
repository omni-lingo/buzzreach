# ATOM: ONBOARD-004 — Password Reset & Account Recovery

**Layer:** L3/L4
**Module:** onboarding
**Effort:** S
**Depends on:** ONBOARD-002

## Inputs (what this atom reads/consumes)
- `src/backend/services/email_service.py` — email sending
- `src/backend/models/user.py` — User model

## Outputs (what this atom produces)
- `src/frontend/pages/ForgotPassword.tsx` — forgot password form:
  - Email input field
  - Submit button → calls `/api/v1/auth/forgot-password`
  - Success message: "Check your email for reset link"
- `src/frontend/pages/ResetPassword.tsx` — reset form (linked from email):
  - New password field
  - Confirm password field
  - Submit button → calls `/api/v1/auth/reset-password` with token
  - Success → redirect to login
- `src/backend/api/auth.py` — new routes:
  - POST `/api/v1/auth/forgot-password` — email → password reset token
  - POST `/api/v1/auth/reset-password` — token + new password → set password
- `src/backend/services/auth_service.py`:
  - `send_password_reset_email(email)` — generate token, send
  - `reset_password(token, new_password)` — verify token, hash, save
- Token same as ONBOARD-002 (6 hour expiry, single-use)
- Password validation: min 8 chars, complexity check (same as signup)
- `tests/test_password_reset.py` — forgot, reset, invalid token, expired token

## Acceptance criteria
- [ ] "Forgot password" link on login page
- [ ] Email sent with reset link (contains token)
- [ ] Reset link opens form with token pre-filled (URL param)
- [ ] Password reset validates new password (min 8 chars, complexity)
- [ ] Token verified before allowing reset
- [ ] Expired token rejected with clear message
- [ ] Reset invalidates all existing sessions (user must login again)
- [ ] Rate limiting: max 3 reset attempts per hour per user
- [ ] No tokens logged or exposed in errors
- [ ] Mobile responsive

## Cross-module contracts
- Uses email_service (ONBOARD-002)
- Extends User model (password_hash)
- Integrates with login flow (AUTH-002)
