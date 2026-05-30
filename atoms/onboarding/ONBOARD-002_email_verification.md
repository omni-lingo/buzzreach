# ATOM: ONBOARD-002 — Email Verification Service

**Layer:** L2
**Module:** onboarding
**Effort:** S
**Depends on:** ONBOARD-001

## Inputs (what this atom reads/consumes)
- `src/backend/models/user.py` — User model with email_verified field
- Email service (Twilio SendGrid, AWS SES, or Resend)

## Outputs (what this atom produces)
- `src/backend/services/email_service.py`:
  - `send_verification_email(user_id, email)` — send link with token
  - `send_password_reset_email(user_id)` — send reset link
  - `send_invitation_email(email, team_id)` — team invite
- `src/backend/models/email_token.py`:
  - `id`, `user_id`, `token` (secure random)
  - `type` (verification/password_reset)
  - `expires_at` (6 hours)
  - `used` (bool)
- Email templates (HTML + plain text):
  - Verification email with button link
  - Password reset email with button link
  - Invitation email
- Rate limiting: max 3 emails per user per hour (prevent spam)
- `tests/test_email_service.py` — send, verify, expiration

## Acceptance criteria
- [ ] Email sent immediately after signup
- [ ] Token in DB before email sent (atomicity)
- [ ] Token expires after 6 hours
- [ ] Token single-use (mark used after verification)
- [ ] Email link includes secure token (unguessable)
- [ ] Rate limiting enforced (max 3 per hour)
- [ ] Resend button works (generate new token)
- [ ] Email templates are readable/professional
- [ ] No tokens logged or exposed

## Cross-module contracts
- Extends User model
- Called by ONBOARD-001 (signup), ONBOARD-004 (password reset)
- External: email service (SendGrid/SES)
