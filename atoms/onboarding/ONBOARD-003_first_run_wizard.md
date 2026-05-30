# ATOM: ONBOARD-003 — First-Run Setup Wizard

**Layer:** L4
**Module:** onboarding
**Effort:** M
**Depends on:** FE-001, BILL-002

## Inputs (what this atom reads/consumes)
- User settings schema (FE-001)
- Onboarding best practices

## Outputs (what this atom produces)
- `src/frontend/pages/OnboardingWizard.tsx` — 5-step wizard (shown to new users):
  1. **Welcome** — hero message, "Let's set up BuzzReach"
  2. **What do you sell?** — product URL, one-line pitch, logo upload (optional)
  3. **Target audience** — keywords they search for (form fields + AI suggestions)
  4. **Tone & style** — persona (professional/casual/humorous), examples, tone guide
  5. **Choose your plan** — free/pro/premium comparison, optional upgrade
- Each step has:
  - Clear explanation + example
  - Form fields + validation
  - Skip option (except last) → use defaults
  - Next/Back buttons
  - Progress indicator (Step 1 of 5)
- `src/frontend/hooks/useOnboarding.ts` — state management
- Wizard saves to user config after each step (auto-save)
- After completion:
  - User sees empty dashboard with "Your first opportunities coming soon..."
  - Background job started (initial scan queued)
  - Tutorial overlay (optional) on dashboard
- Desktop vs Mobile:
  - Desktop: side-by-side (wizard on left, preview on right)
  - Mobile: full-screen steps
- `tests/e2e/onboarding.spec.ts` — complete wizard flow

## Acceptance criteria
- [ ] Wizard loads for new users (first login)
- [ ] Each step validates before next
- [ ] Product URL validated (non-empty, valid URL)
- [ ] Keywords form accepts multiple entries (textarea or chip input)
- [ ] Tone selection shows examples
- [ ] Plan comparison clear (feature list side-by-side)
- [ ] Config saved after step 5 (no "Save" button needed)
- [ ] Initial scan triggered after wizard complete
- [ ] Wizard skippable (skip button on steps 1-4)
- [ ] Mobile responsive (vertical layout)
- [ ] Tutorial tooltip shows on dashboard after wizard

## Cross-module contracts
- Writes to user settings (FE-001)
- Reads plan tiers (BILL-002)
- Triggers initial scan (DISC-003)
- Integrates with dashboard (FE-002)
