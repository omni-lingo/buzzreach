# GitHub Integration

BuzzReach automatically manages code on GitHub through the build runner.

## Repository

**URL:** https://github.com/omni-lingo/buzzreach  
**Owner:** omni-lingo  
**Access:** Public

## Automatic Workflow

### Per-Atom Pushes

After each atom completes:
1. ✅ Claude Code commits with message `[ATOM_ID] Description`
2. ✅ Build runner detects success
3. ✅ Runner pushes to GitHub (`git push origin master`)

```
Claude builds AUTH-001 
    ↓
Commits: "[AUTH-001] User model & API key contract"
    ↓
build_atom() returns SUCCESS
    ↓
github.push_atom(AUTH_ID) 
    ↓
git push origin master
    ↓
Commit on GitHub ✓
```

### Per-Wave Pull Requests

After all atoms in a wave complete:
1. ✅ Runner detects wave completion
2. ✅ Creates GitHub PR with wave summary
3. ✅ PR lists all atoms in the wave
4. ✅ Auto-ready for review and merge

```
Wave 1: [AUTH-001, AUTH-002, RATE-001, AUDIT-002]
    ↓
All 4 atoms complete
    ↓
github.create_wave_pr(1, atom_ids)
    ↓
gh pr create --title "Wave 1: AUTH-001, ..."
    ↓
PR on GitHub (ready for review) ✓
```

**Example PR:**
```
Title: Wave 1: AUTH-001, AUTH-002, RATE-001, AUDIT-002

## Wave 1 — 4 atoms

Atoms in this wave:
- AUTH-001
- AUTH-002
- RATE-001
- AUDIT-002

All atoms in this wave are complete and tested. Ready for review and merge.

### Testing
- [x] All atoms passed build gates
- [x] Tests pass
- [x] No lint errors
- [x] Cross-module imports verified

### Deployment
This can be merged to `main` for deployment.
```

## Post-Layer Hooks & Documentation

After all atoms in a layer complete:

| Layer | Hook | Output | Auto-Pushed |
|-------|------|--------|-------------|
| L1 | `after_l1.py` | `contracts/schema_columns.json` | ✅ Yes |
| L3 | `after_l3.py` | `openapi.json`, `API_SURFACE.md` | ✅ Yes |

### L1 Hooks (Models)

**Trigger:** All model atoms complete
**Script:** `scripts/build-runner/hooks/after_l1.py`
**Generates:** `contracts/schema_columns.json`

```
CORE-001, CORE-002, CORE-003, CORE-004, CORE-005 complete
    ↓
check_layer_complete(state, atoms, "L1") → True
    ↓
hook_runner.run_after_layer("L1")
    ↓
after_l1.py executes
    ↓
Generates contracts/schema_columns.json
    ↓
git add contracts/schema_columns.json
    ↓
git commit "[DOCS] Auto-generated documentation update"
    ↓
git push origin master ✓
```

### L3 Hooks (API)

**Trigger:** All route atoms complete
**Script:** `scripts/build-runner/hooks/after_l3.py`
**Generates:** 
- `openapi.json` (OpenAPI 3.0 spec)
- `API_SURFACE.md` (Human-readable endpoint list)

```
API-001 (and all L3 atoms) complete
    ↓
check_layer_complete(state, atoms, "L3") → True
    ↓
hook_runner.run_after_layer("L3")
    ↓
after_l3.py executes
    ↓
Generates openapi.json, API_SURFACE.md
    ↓
git add openapi.json API_SURFACE.md
    ↓
git commit "[DOCS] Auto-generated documentation update"
    ↓
git push origin master ✓
```

## Manual Operations

### Push Docs Only

```bash
# After manually editing docs
cd d:\BuzzReach
git add *.md contracts/
git commit -m "[DOCS] Manual documentation update"
git push
```

### Check Auth

The runner verifies GitHub auth on startup:

```bash
# If "GitHub auth failed" appears in logs, fix with:
gh auth login
# Then re-run the build
python scripts/build-runner/run.py
```

### View Build Progress on GitHub

```bash
# List all commits by atom
gh repo list

# View a specific PR
gh pr view 1

# List all PRs
gh pr list

# View commits
git log --oneline
```

## Build State & GitHub Synchronization

| State | On GitHub | In `state/build_state.json` |
|-------|-----------|---------------------------|
| pending | Not yet pushed | `"status": "pending"` |
| complete | Pushed ✓ | `"status": "complete"` |
| failed | Not pushed | `"status": "failed"` |
| blocked | Not pushed | `"status": "blocked"` |

**Key:** `state/build_state.json` is the source of truth. GitHub is a mirror of successful atoms only.

## Troubleshooting

### "GitHub auth failed"

```bash
# Re-authenticate
gh auth logout
gh auth login
# Then retry the build
python scripts/build-runner/run.py
```

### Push Failed, But Atom Built

If GitHub push fails but the atom built locally:

```bash
# Check git status
git status

# Push manually
git push origin master

# Retry runner
python scripts/build-runner/run.py --atom AUTH-001
```

### PR Not Created

If a wave completed but no PR was created:

```bash
# Check logs
tail -f logs/build-runner.log

# Manually create PR
gh pr create --title "Wave 1: ..." --body "..."
```

### Want to Reset GitHub

⚠️ **Warning:** This is destructive. Only do this if you want to start over.

```bash
# CAREFUL: Force push entire history
# git push origin master --force

# Better: Create a new repo
# gh repo create buzzreach-v2 --public
# git remote set-url origin https://github.com/omni-lingo/buzzreach-v2
# git push origin master
```

## GitHub Workflows (Future)

The system is designed to support GitHub Actions workflows:

```yaml
# .github/workflows/build.yml (future)
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: pytest tests/
      - run: ruff check src/
```

But for now, testing is handled by Claude during atom builds.

## Summary

**Automatic:**
- ✅ Each atom pushed after success
- ✅ Each wave gets a PR
- ✅ Docs auto-generated and pushed at L1, L3
- ✅ GitHub auth checked on startup

**Manual:**
- Push docs: `git add *.md && git commit && git push`
- Check auth: `gh auth login`
- View progress: `gh pr list`, `git log`

**Source of Truth:**
- Local: `state/build_state.json` (atoms being built)
- Remote: `https://github.com/omni-lingo/buzzreach` (completed atoms only)
