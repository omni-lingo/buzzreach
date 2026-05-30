# BuzzReach MVP Build — Quick Start

## In 3 Minutes

```bash
# Windows
cd scripts/build-runner
setup-windows.bat              # One-time setup (installs deps)

# Start full build in background (Opus 4.6, all 30 atoms, max effort)
build.bat

# Watch progress
Get-Content logs/build-runner.log -Wait  # PowerShell
tail -f logs/build-runner.log            # WSL/Git Bash
```

## What's Being Built

**30 atoms across 8 modules:**

| Module | Atoms | Purpose |
|--------|-------|---------|
| infra | 1 | Project scaffold, settings, env vars |
| auth | 4 | User model, JWT, rate limiting, audit logging |
| core | 5 | DB base, SeenUrl, Opportunity, AuditLog, Metrics models |
| config | 2 | Product config contract & loader |
| discovery | 3 | Google search (query builder, client, service) |
| extraction | 1 | Content extractor (Readability-style) |
| filter | 2 | Dedup + keyword pre-filter |
| ai | 3 | Anthropic client, relevance scorer, draft generator |
| pipeline | 1 | Tiered orchestrator (discover→filter→score→draft) |
| delivery | 2 | Digest builder & sender (email/Slack) |
| jobs | 1 | Cron scan entrypoint + health monitor |
| api | 1 | Opportunities API (JWT-protected) |
| observability | 2 | Metrics & alerting |
| dashboard | 1 | Dashboard API (see what's working) |
| tests | 1 | E2E integration test (anti-silo validation) |

**Total effort:** ~45 hours (30 atoms × 90 min avg) with Claude Opus 4.6 at max effort.
**Estimated cost:** ~$45–60 USD.

## Timeline

- **Sequential:** ~60 min per atom × 30 = ~30 hours
- **With parallelization:** ~15 waves × ~2 hours = ~30 hours (build runner doesn't parallelize yet, reserved for future)

The runner is designed to be resumable—if it fails, just run `build.bat` again and it picks up where it left off.

## What Happens During Build

For each atom:

1. **Parse spec** (inputs, outputs, dependencies, acceptance criteria)
2. **Load context** (only relevant docs per atom type—BUILD_RULES.md, CONVENTIONS.md, etc.)
3. **Invoke Claude Code** session with the atom spec + context
4. **Validate gates** (21 automated checks: lint, type check, tests pass, no SQL injection, etc.)
5. **Auto-fix** if gates fail (up to 3 retry cycles with fix-specific prompts)
6. **Commit** to git if all gates pass
7. **Track cost** (tokens, USD per atom)
8. **Continue** to next atom

## Output Artifacts

### Logs
- `logs/build-runner.log` — Build events (timestamps, atom progress, errors)
- `logs/cost_tracking.csv` — Per-atom cost ledger (model, tokens, USD)

### State
- `state/build_state.json` — Which atoms complete/failed/blocked (machine-readable)
- `BUILD_STATE.md` — Human-readable progress (auto-updated from JSON)
- `state/claims.db` — SQLite lock table (for crash recovery & parallel safety)

### Code
- One git commit per atom: `[ATOM-ID] atom title`
- All atoms complete successfully = clean git history, 30 commits

## Key Settings

**product.yaml:**
```yaml
build:
  model: "claude-opus-4-6"   # Force Opus for all atoms (even small ones)
  model_override: true       # Ignore effort-based model selection
```

**Effort levels still apply for turn limits:**
- S (Small): 30 turns, ~20 min
- M (Medium): 50 turns, ~30 min
- L (Large): 75 turns, ~45 min

## Commands

### Build
```bash
build.bat                      # All 30 atoms, Opus 4.6, max effort (background)
build-foreground.bat           # Same, but in console (for debugging)
build.bat --atom AUTH-001      # Single atom
build.bat --module auth        # All atoms in auth module (4 atoms)
build.bat --max-atoms 5        # First 5 atoms, then stop
```

### Status & Planning
```bash
python scripts/build-runner/run.py --status                 # Progress
python scripts/build-runner/run.py --dry-run                # Wave plan
python scripts/build-runner/run.py --health                 # Health check
```

## Monitoring (Windows)

### PowerShell (recommended)
```powershell
# Watch log in real-time
Get-Content logs/build-runner.log -Wait

# Or: tail-like behavior (requires PSReadLine)
Get-Content logs/build-runner.log -Tail 20 -Wait
```

### Command Prompt
```cmd
# Check status
python scripts/build-runner/run.py --status

# Last 20 lines of log
type logs/build-runner.log | powershell -Command "Get-Content | Select-Object -Last 20"

# Or use tail if installed (Git Bash)
tail -f logs/build-runner.log
```

## Resuming a Failed Build

If the build crashes, stalls, or is interrupted:

```bash
# Just run again—it picks up where it left off
build.bat

# Or check status first
python scripts/build-runner/run.py --status

# Show which atoms are blocked/failed
cat state/build_state.json | python -m json.tool | grep -A2 '"status"'
```

The runner handles crash recovery automatically:
- Releases stale claims (older than 30 min)
- Reconciles git commits vs. state
- Uses `continue_prompt()` for partial work

## Stopping the Build

### Graceful (let current atom finish)
Just close the build window or interrupt with Ctrl+C.

### Forced Stop
```bash
taskkill /F /IM python.exe     # Kill all Python processes
```

Then:
```bash
python scripts/build-runner/run.py --status    # Check status
build.bat                                      # Resume when ready
```

## Troubleshooting

### "Claude CLI not found"
```bash
npm install -g @anthropic-ai/claude-code
```

### "Python 3.11+ required"
```bash
python --version
# If < 3.11, install from https://www.python.org/downloads/
```

### Build hung (no output for 30+ min)
1. Check if Python is running: `tasklist /FI "IMAGENAME eq python.exe"`
2. Check log tail: `type logs/build-runner.log | powershell -Command "Select-Object -Last 50"`
3. Kill and resume if stuck: `taskkill /F /IM python.exe && build.bat`

### "rate_limit" errors
The runner automatically unclaims and retries. If persistent:
- Check `ANTHROPIC_API_KEY` is set
- Wait a few minutes and resume
- Contact Anthropic if quota is exhausted

## Architecture

The runner is built from the **Build Runner Blueprint** (RUNNER_FACTORY.md):

- **26 steps** in the main loop (startup → claim → build → validate → commit → repeat)
- **21 validation gates** (lint, type check, tests, no secrets, etc.)
- **9 error categories** (timeout, rate limit, context overflow, etc.)
- **Automatic fix loop** (up to 3 retry cycles if gates fail)
- **Anti-silo validation** (cross-module contracts checked after every atom)
- **Atomic claims** (SQLite-backed, safe for parallel builds)

See `scripts/build-runner/README.md` for full documentation.

## Next Steps (After Build Complete)

1. **Verify all tests pass:**
   ```bash
   pytest                # Run full test suite
   ```

2. **Manual testing (if time permits):**
   - Start the cron job: `python -m src.backend.jobs.scan`
   - Check results: `curl http://localhost:8000/api/v1/dashboard`
   - Verify email/Slack digest arrived

3. **Dogfood the product:**
   - Use BuzzReach to market the IRS Penalty Calculator + ParkingAppealMate
   - Track: opportunities found, conversion rate, cost per conversion

4. **Optimize & iterate:**
   - Tune prompt for draft quality (if replies get low engagement)
   - Add custom site parsers as needed (Quora, Avvo, Reddit, etc.)
   - Monitor costs and consider rate limiting tweaks

## Files

```
d:\BuzzReach\
├── product.yaml                      # Tech stack, modules, build config
├── BUILD_RULES.md                    # Code quality gates
├── RUNNER_FACTORY.md                 # Complete runner blueprint
├── BUZZREACH.md                      # Product spec
├── BUILD_STATE.md                    # Progress (auto-generated)
├── atoms/                            # 30 atom specs
│   ├── infra/
│   ├── auth/
│   ├── core/
│   ├── config/
│   ├── discovery/
│   ├── extraction/
│   ├── filter/
│   ├── ai/
│   ├── pipeline/
│   ├── delivery/
│   ├── jobs/
│   ├── api/
│   ├── observability/
│   ├── dashboard/
│   └── tests/
├── scripts/build-runner/             # Runner implementation
│   ├── run.py                        # Main entry point
│   ├── build.bat                     # Windows background launcher
│   ├── build-foreground.bat          # Windows console (debug)
│   ├── setup-windows.bat             # One-time setup
│   ├── README.md                     # Full runner docs
│   └── lib/                          # Library modules
│       ├── config.py
│       ├── state.py
│       ├── claims.py
│       ├── executor.py
│       ├── deps.py
│       ├── health.py
│       ├── context.py
│       ├── prompts.py
│       ├── errors.py
│       ├── events.py
│       └── cost.py
├── state/                            # Build state (gitignored)
│   ├── build_state.json
│   └── claims.db
└── logs/                             # Build logs (gitignored)
    ├── build-runner.log
    └── cost_tracking.csv
```

## Enjoy!

The MVP is ready to build. Fire up `build.bat` and watch Claude assemble your product.

```
BuzzReach Build Runner (Windows Background)

Starting build runner...
Log: logs\build-runner.log

Build started in background. Monitor progress with:
  Get-Content logs\build-runner.log -Wait

---

✓ Build complete: 30 atoms, $52.34
Log: logs\build-runner.log
```

—The BuzzReach Build Team
