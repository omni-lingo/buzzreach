# ATOM: ONBOARD-001 — Signup / Registration Flow

**Layer:** L3/L4
**Module:** onboarding
**Effort:** M
**Depends on:** AUTH-001, BILL-002

## Inputs (what this atom reads/consumes)
- `src/backend/models/user.py` — User model
- `src/backend/models/subscription.py` — Subscription model
- Twilio SendGrid or similar for email verification

## Outputs (what this atom produces)
- `src/frontend/pages/Signup.tsx` — registration form:
  - Email, username, password fields
  - Password strength meter
  - "Agree to ToS" checkbox
  - Submit → POST `/api/v1/auth/signup`
  - Link to login page
- `src/frontend/pages/VerifyEmail.tsx` — after signup:
  - Message: "Check your email for verification link"
  - Resend button (rate-limited to 3x per hour)
- `src/backend/api/auth.py` — new routes:
  - POST `/api/v1/auth/signup` — create user, generate verification token, send email
  - GET `/api/v1/auth/verify?token=<token>` — mark email as verified
  - POST `/api/v1/auth/resend-verification` — re-send email
- `src/backend/services/auth_service.py`:
  - `register_user(email, username, password_hash)` → create User + Subscription (free)
  - `generate_verification_token(user_id)` → secure token (6-hour expiry)
  - `verify_email(token)` → set user.email_verified, delete token
  - Password hashing (bcrypt or argon2)
- `migrations/versions/<rev>_add_email_verification.py` — add `email_verified` bool, `verification_token` table
- `tests/test_signup.py` — register, verify email, resend, duplicate email rejection

## Acceptance criteria
- [ ] Signup form validates email format (RFC 5322)
- [ ] Password strength requirement: min 8 chars, uppercase, number (or equivalent)
- [ ] Duplicate email rejected with clear message
- [ ] Username conflicts rejected
- [ ] Verification email sent immediately after signup
- [ ] Email link is one-time use (token deleted after verify)
- [ ] Token expires after 6 hours
- [ ] Verified user can login
- [ ] Unverified users cannot access app (redirect to /verify-email)
- [ ] CSRF protection on signup form (token in session)
- [ ] Rate-limiting on resend (max 3 per hour per user)

## Cross-module contracts
- Creates User (AUTH-001) + Subscription (BILL-002)
- Calls email service (external)
- Sets JWT after verification (AUTH-002)
