# ATOM: ADMIN-001 — Team Management (members, roles, invites)

**Layer:** L2/L4
**Module:** admin
**Effort:** M
**Depends on:** AUTH-001, BILL-002

## Inputs (what this atom reads/consumes)
- `src/backend/models/user.py` — User model
- `src/backend/models/subscription.py` — Subscription model

## Outputs (what this atom produces)
- `src/backend/models/team.py` — Workspace/team model:
  - `id`, `owner_id` (FK), `name`, `created_at`
- `src/backend/models/team_member.py` — membership:
  - `id`, `team_id`, `user_id`, `role` (owner/admin/member)
  - `invited_at`, `joined_at`, `created_at`
- `src/backend/models/team_invitation.py` — invites:
  - `id`, `team_id`, `email`, `role`, `token` (one-time)
  - `created_at`, `expires_at` (24 hours)
- `src/backend/services/team_service.py`:
  - `create_team(owner_id, name)` → new workspace
  - `invite_member(team_id, email, role)` → generate invite token, send email
  - `accept_invitation(token)` → user joins team
  - `change_member_role(team_id, user_id, new_role)` → owner/admin only
  - `remove_member(team_id, user_id)` → delete membership
  - `list_team_members(team_id)` → all members + roles
- `src/backend/api/teams.py` — routes:
  - POST `/api/v1/teams` — create team
  - GET `/api/v1/teams/{id}/members` — list members
  - POST `/api/v1/teams/{id}/invitations` — send invite
  - POST `/api/v1/invitations/{token}/accept` — join team
  - PUT `/api/v1/teams/{id}/members/{user_id}` — change role
  - DELETE `/api/v1/teams/{id}/members/{user_id}` — remove member
- `src/frontend/pages/TeamPage.tsx` — manage team:
  - List current members + roles
  - Invite form (email input)
  - Remove button (owner/admin only)
  - Change role dropdown (owner/admin only)
- Opportunities now scoped to team (not individual user)
- Plan limit: free = 1 user, pro = 3 users, premium = unlimited
- `tests/test_team_management.py` — CRUD operations, permissions

## Acceptance criteria
- [ ] Owner can create team
- [ ] Team member list shows all users + roles
- [ ] Invite email sent with accept link
- [ ] Invite token single-use + expires 24h
- [ ] Only team owner can invite/remove members
- [ ] Role changes respected (admin can't remove owner)
- [ ] Opportunities shared across team
- [ ] Plan member limits enforced (free = 1, pro = 3)
- [ ] Leaving team removes access
- [ ] Audit log tracks team changes (AUDIT-002)

## Cross-module contracts
- Extends User, Subscription models
- Opportunities scoped by team_id
- Integrates with plan limits (BILL-002)
