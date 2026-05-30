# BuzzReach Build Runner

Automated build system for the 30-atom MVP. Orchestrates Claude Code sessions to build each atom in topological order, validating gates and handling errors.

## Quick Start (Windows)

```bash
# Full build in background (Opus 4.6, max effort)
build.bat

# Check progress
tail -f logs/build-runner.log    # Linux/macOS
Get-Content logs/build-runner.log -Wait  # PowerShell

# Or foreground (for debugging)
build-foreground.bat
```

## Usage

### Full Build
```bash
build.bat                          # All 30 atoms, Opus 4.6
```

### Partial Builds
```bash
build.bat --atom AUTH-001          # Single atom
build.bat --module auth            # All auth atoms
build.bat --max-atoms 5            # First 5 atoms, then stop
```

### Status & Planning
```bash
build.bat --status                 # Show progress
build.bat --dry-run                # Show wave plan (parallelizable atoms)
build.bat --health                 # Infrastructure checks
```

### Advanced
```bash
build-foreground.bat --timeout 3600           # 1h per atom
build-foreground.bat --budget 100             # Stop if cost > $100
```

## What It Does

1. **Load Config**: Reads `product.yaml` (tech stack, modules, build config)
2. **Discover Atoms**: Scans `atoms/**/*.md` for atom specs
3. **Topological Sort**: Orders atoms by dependencies
4. **State Management**: Tracks progress in `state/build_state.json`
5. **Atomic Claims**: Prevents parallel conflicts via SQLite
6. **Invoke Claude**: For each atom, runs `claude --print` with the atom spec
7. **Validate Gates**: 21 gates (lint, type check, tests pass, etc.)
8. **Handle Errors**: Categorizes failures (rate limit, context overflow, etc.)
9. **Track Cost**: Logs token usage and USD cost per atom
10. **Commit**: Each atom commits to git after all gates pass

## Build Output

### Logs
- `logs/build-runner.log` — timestamped build events
- `logs/cost_tracking.csv` — cost per atom (model, tokens, USD)

### State
- `state/build_state.json` — which atoms complete/failed/blocked
- `state/claims.db` — SQLite lock table (for parallel safety)

### Git
- One commit per atom: `[ATOM-ID] title description`
- Branch: defaults to `main` (set in product.yaml)

## Architecture

### Main Entry Point
- `scripts/build-runner/run.py` — CLI, main loop, orchestration

### Library Modules (`lib/`)
- `config.py` — Load product.yaml
- `state.py` — Build state (JSON + SQLite)
- `deps.py` — Dependency graph, topological sort, atom parsing
- `executor.py` — Invoke Claude, parse results
- `health.py` — Preflight checks (Claude CLI, Git, Python version, disk)
- `context.py` — Context loading per atom type (Section 13)
- `prompts.py` — Prompt selection (fresh/continue/fix)
- `claims.py` — Atomic claim system (parallel safety)
- `cost.py` — Cost tracking (CSV ledger)

## Key Settings (product.yaml)

```yaml
build:
  model: "claude-opus-4-6"   # All atoms use Opus (not Sonnet for small atoms)
  model_override: true       # Ignore effort-based model selection
```

Effort levels still set max-turns:
- `S` (Small): 30 turns
- `M` (Medium): 50 turns
- `L` (Large): 75 turns

## Wave Planning (Parallelization)

The runner computes a "wave plan" — atoms that can run in parallel (no inter-dependencies):

```
Wave 1: INFRA-001 (3 atoms in parallel)
Wave 2: CORE-001/002/003, CFG-001, DISC-001 (6 atoms)
Wave 3: AI-001, FILT-001, EXT-001, DISC-002 (4 atoms)
...
```

Run with `--dry-run` to see parallelizable waves (useful for `--parallel N` in future versions).

## Cost Estimation

Per atom (Opus 4.6):
- S (Small): ~$0.80
- M (Medium): ~$1.50
- L (Large): ~$2.50

Full 30-atom build (mix of S/M/L): ~$45–60 total.

## Error Handling

Failures are categorized into 9 modes:

| Mode | Cause | Recovery |
|---|---|---|
| **timeout** | Process killed after 30min | Retry (max 3 times) |
| **rate_limit** | Hit Claude rate limit | Unclaim, wait 1min, retry |
| **auth_error** | Invalid Claude API key | Stop (manual fix) |
| **context_overflow** | Atom spec too large | Block atom, continue |
| **max_turns** | Exhausted turn budget | Retry with more turns (1x) |
| **session_fail** | Non-zero exit, no category match | Retry (max 3 times) |
| **gate_fail** | Linting/tests fail (after build succeeds) | Fix loop (auto-retry, max 3 cycles) |
| **success** | All gates pass | Commit, continue |

## Monitoring Background Build

### Windows PowerShell
```powershell
# Watch log in real-time
Get-Content logs/build-runner.log -Wait

# Check status
python scripts/build-runner/run.py --status

# Show wave plan
python scripts/build-runner/run.py --dry-run
```

### Windows Command Prompt
```cmd
REM Watch log (polling)
:loop
cls
type logs\build-runner.log
timeout /t 10
goto loop

REM Or use tail if installed (Git Bash / MSYS2)
tail -f logs\build-runner.log
```

### Stop Build
The runner has no built-in stop command. To cancel:
1. Kill the Python process: `taskkill /F /IM python.exe` (kills all Python, be careful)
2. Or manually update `state/build_state.json` to mark atoms as "blocked"

## Resuming a Failed Build

The runner is resumable by design:

1. **Stale Claim Recovery**: On startup, releases claims older than 30 minutes (crash recovery)
2. **State Reconciliation**: If a commit exists in git but state says "building", auto-fixes to "complete"
3. **Continue Prompt**: If an atom was partially built, next run uses `continue_prompt()` (includes git status)

To resume:
```bash
build.bat                          # Just run again; picks up where it left off
```

## Future Enhancements

### Currently Not Implemented (but in blueprint)
- Parallel execution (`--parallel N`) with worktree isolation
- Multi-region build (distribute atoms to multiple machines)
- Advanced fix loop (regression guards, max 3 cycles)
- Custom gates from product.yaml (Appendix C)
- Live API verification (L3 atoms call themselves after build)
- Unattended builds (auto-shutdown, email summaries)

### CLI Flags Reserved
- `--parallel N` — Run N atoms in parallel (worktree-isolated)
- `--auto-shutdown` — Shut down after build (VPS only)
- `--report email@example.com` — Email summary on done
- `--no-push` — Build locally, don't push to remote

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

### "rate_limit" errors
The runner automatically unclaims and retries. If persistent, check:
- `ANTHROPIC_API_KEY` is set
- Daily token quota (contact Anthropic)

### "context_overflow" on an atom
The atom spec is too large for a single Claude session. Split it into two atoms.

### Build hung (no output for 30+ min)
The atom is building but hasn't finished. Check:
```bash
tasklist /FI "IMAGENAME eq python.exe"    # Is Python running?
Get-Content logs/build-runner.log -Tail 20 # Last 20 log lines
```

If Python is stuck, kill and resume:
```bash
taskkill /F /IM python.exe
build.bat                                   # Resume
```

## Architecture Decisions

See `RUNNER_FACTORY.md` Section 4 for architectural decisions that shaped this runner.

### Key Invariants
1. **One atom, one commit** — atomic rollback via `git revert`
2. **Schema-qualified models** — multi-tenancy safe (Section 4.3)
3. **Parameterized queries only** — no SQL injection risk
4. **Gates before commit** — no invalid code in repo
5. **Anti-silo validation** — dependent modules checked post-atom

## References

- `RUNNER_FACTORY.md` — Complete blueprint (60+ KB specification)
- `BUILD_RULES.md` — Code quality gates and naming conventions
- `product.yaml` — Build configuration
- `BUILD_STATE.md` — Human-readable progress (auto-generated from state/build_state.json)
