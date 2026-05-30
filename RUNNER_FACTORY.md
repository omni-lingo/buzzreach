# Build Runner Blueprint — Battle-Tested Framework for AI-Driven Product Development

> **What this is:** A complete, project-agnostic instruction set for building software products using Claude Code as the build engine. Drop this into a fresh Claude session alongside your product spec, and it will build your product using patterns proven across 6 production systems (1,500+ atoms delivered). Every rule in this document exists because violating it caused a real failure.
>
> **What this is NOT:** Documentation for a specific product. Every reference to past projects exists only as a "lesson learned" so the pattern is never repeated.
>
> **Target audience:** A Claude Code session that will build your product from scratch.
>
> **Platforms:** Linux (primary), Windows (Section 27), macOS (same as Linux with Homebrew).

---

## Table of Contents

1. [How To Use This Document](#1-how-to-use-this-document)
2. [The Silo Problem — Why This Exists](#2-the-silo-problem)
3. [Product Definition Template](#3-product-definition-template)
4. [Architecture Decisions](#4-architecture-decisions)
5. [Atom-Based Development](#5-atom-based-development)
6. [The Runner — Core Loop (26 Steps)](#6-the-runner)
7. [Validation Gates (21 Gates)](#7-validation-gates)
8. [Self-Healing Fix Loop](#8-fix-loop)
9. [Cross-Module Communication — The Anti-Silo Core](#9-cross-module-communication)
10. [Event Bus Pattern](#10-event-bus-pattern)
11. [Dependency Graph & Wave Planning](#11-dependency-graph)
12. [State Management & Claim System](#12-state-management)
13. [Context Loading Table](#13-context-loading)
14. [Prompt Differentiation (3 Types)](#14-prompt-types)
15. [Error Categorization & Recovery Paths](#15-error-categorization)
16. [Cost & Budget Tracking](#16-cost-tracking)
17. [Health Checks & Preflight](#17-health-checks)
18. [Git & Commit Discipline](#18-git-discipline)
19. [Code Quality Rules](#19-code-quality)
20. [Testing Strategy](#20-testing)
21. [Live API Verification](#21-live-api-verification)
22. [Doc Maintenance — Mandatory](#22-doc-maintenance)
23. [Crash Recovery & Two-Level Retry](#23-crash-recovery)
24. [Parallel Execution & Worktree Isolation](#24-parallel-execution)
25. [Multi-Product / Multi-Schema Builds](#25-multi-product)
26. [Unattended & Cloud Builds](#26-unattended-builds)
27. [Windows Adaptation](#27-windows)
28. [Runner Implementation (Python)](#28-runner-code)
29. [Unit Test Plan](#29-unit-tests)
30. [E2E Test Plan](#30-e2e-tests)
31. [Conventions](#31-conventions)
32. [Decisions Log Template](#32-decisions-log)
33. [Troubleshooting](#33-troubleshooting)
34. [Checklist — Before First Build](#34-checklist)
35. [Appendix A — Lessons Learned (6 Systems)](#appendix-a)
36. [Appendix B — Quick Reference Card](#appendix-b)
37. [Appendix C — Domain-Specific Gate Extension](#appendix-c)

---

## 1. How To Use This Document

### For a new product build

1. Copy this file into your new project root as `BUILD_RUNNER_BLUEPRINT.md`
2. Fill in Section 3 (Product Definition) with your product's details
3. Create your atom specs (Section 5)
4. Copy the runner code from Section 28 into `scripts/build-runner/`
5. Run `python3 scripts/build-runner/run.py --health` to verify infrastructure
6. Run `python3 scripts/build-runner/run.py --dry-run` to see the plan
7. Run `python3 scripts/build-runner/run.py` to start building

### For a Claude Code session

Paste this at the start of your session or reference it in your CLAUDE.md:

```
Read BUILD_RUNNER_BLUEPRINT.md before doing any work.
Follow it exactly — especially Sections 7, 8, 14, 15, 17.
```

### Key principle

**Every module you build must be stitched to every other module it touches.** If module A produces data that module B consumes, the build must validate that connection *at build time*, not after you ship. This is the #1 lesson from building 6 products. See Section 9.

---

## 2. The Silo Problem

### What happens without this blueprint

You build 10 modules. Each module works perfectly in isolation. You ship. Nothing works together because:

- Module A changed its database schema; Module B still queries the old columns
- Module C's API returns a different shape than Module D expects
- Module E's background job writes to a table that Module F reads — but nobody tested them together
- The auth module works, the dashboard module works, but the dashboard never actually checks auth
- You built a forecasting service and a procurement service on the same database, but they don't know about each other's tables

### Why it happens

Builders (human or AI) optimize for the task in front of them. When you say "build the orders module," the builder focuses on orders. It doesn't check whether the orders module's output format matches what the dashboard module expects, because it doesn't know the dashboard module exists.

### How this blueprint prevents it

1. **Every atom declares its inputs and outputs** (Section 5)
2. **Every atom runs cross-module validation after completing** (Section 9)
3. **An event bus notifies dependent modules when something changes** (Section 10)
4. **A dependency graph tracks who reads what** (Section 11)
5. **State is unified across all modules** (Section 12)
6. **21 validation gates catch structural breaks before commit** (Section 7)
7. **Self-healing fix loops auto-correct gate failures** (Section 8)
8. **Claim system prevents parallel collision** (Section 12)

The cost of stitching at build time is ~5% overhead. The cost of stitching after shipping is 10x.

---

## 3. Product Definition Template

Fill this in for YOUR product. This is the first thing the runner reads.

```yaml
# product.yaml — edit this for your project
product:
  name: "YourProduct"
  description: "One-line description"
  version: "0.1.0"

infrastructure:
  database:
    type: postgres       # postgres | mysql | sqlite
    version: "15"
    schemas:
      - name: "your_schema"
        owner: "this_product"
      - name: "shared"
        owner: "shared"
        read_only: true  # other products own this
  cache:
    type: redis
    version: "7"
    db: 0
  storage:
    type: minio          # minio | s3 | local
    bucket: "your-bucket"
  message_queue: null    # rabbitmq | redis-streams | null

backend:
  framework: fastapi     # fastapi | django | express | nestjs
  language: python       # python | typescript | go
  language_version: "3.12"
  directory: "src/backend"
  port: 8000
  orm: sqlalchemy        # sqlalchemy | prisma | typeorm | none
  migration_tool: alembic  # alembic | prisma-migrate | typeorm | knex

frontend:
  framework: react       # react | nextjs | vue | svelte | none
  bundler: vite          # vite | webpack | turbopack
  language: typescript
  directory: "src/frontend"
  port: 3000
  state_management: zustand  # zustand | redux | tanstack-query | pinia
  styling: tailwind      # tailwind | css-modules | styled-components

jobs:
  framework: celery      # celery | bull | cron | none
  queues: ["default"]
  beat_schedule: true

auth:
  type: jwt              # jwt | session | oauth2 | none
  algorithm: RS256

# Modules this product is divided into.
# List the major functional areas.
modules:
  - name: "auth"
    depends_on: []
  - name: "core"
    depends_on: ["auth"]
  - name: "dashboard"
    depends_on: ["core"]
  # ... add your modules

# If this product shares a database with other products,
# list the cross-product reads here.
cross_product_reads:
  - source_schema: "other_product_schema"
    tables: ["orders", "customers"]
    read_only: true
    notes: "We read orders for reporting. Never write."

# Custom gates beyond the base 21 (see Appendix C).
custom_gates: []
  # - name: "tenant_isolation"
  #   severity: "hard"
  #   check_command: "python3 scripts/check_tenant_isolation.py"
  #   description: "Verify all queries filter by tenant_id"
```

---

## 4. Architecture Decisions

These are non-negotiable decisions baked into the runner. They come from building 6 products and discovering what works.

### 4.1 Layered build order

Build in this order. Never skip a layer.

```
Layer 1 (L1): Models & migrations     — database schema, the foundation
Layer 2 (L2): Services & business logic — pure logic, no HTTP
Layer 3 (L3): Routes & API endpoints   — HTTP layer, calls L2
Layer 4 (L4): Frontend pages           — calls L3 via API client
Layer 5 (L5): Tests & integration      — validates L1-L4 work together
```

**Why:** L3 depends on L2 depends on L1. Building out of order creates mocks that drift from reality.

### 4.2 One atom, one commit

Each atom (Section 5) produces exactly one commit. No multi-atom commits. No commits without all gates passing.

**Why:** If atom 47 breaks something, you can `git revert` exactly one commit. Multi-atom commits make rollback a nightmare.

### 4.3 Schema-qualified models

Every database model declares its schema explicitly:

```python
# Python/SQLAlchemy
class Order(Base):
    __tablename__ = "orders"
    __table_args__ = {"schema": "your_schema"}

# TypeScript/Prisma
model Order {
  @@schema("your_schema")
}
```

**Why:** When you share a database with other products, unqualified table names collide. Learned this the hard way when two products both had a `users` table.

### 4.4 No wildcard imports, no wildcard CORS, no wildcard anything

```python
# WRONG
from app.models import *
allow_origins = ["*"]

# RIGHT
from app.models.order import Order
allow_origins = ["http://localhost:3000", "https://yourdomain.com"]
```

**Why:** Wildcards hide dependencies. You can't grep for "who uses Order" if everything is `import *`.

### 4.5 Cross-module contracts are code, not documentation

If module A's output feeds module B's input, there must be a shared type/schema that both import:

```python
# shared/contracts/order_event.py — both modules import this
@dataclass
class OrderCreatedEvent:
    order_id: UUID
    customer_id: UUID
    total_amount: Decimal
    created_at: datetime
```

**Why:** Documentation lies. Code doesn't compile if the contract breaks.

---

## 5. Atom-Based Development

### What is an atom?

An atom is the smallest unit of work that produces a working, tested, committed change. Every atom has:

```markdown
# ATOM: AUTH-001 — User login endpoint

**Layer:** L3 (Route)
**Module:** auth
**Effort:** M
**Depends on:** AUTH-000 (User model), AUTH-000b (JWT service)

## Inputs (what this atom reads/consumes)
- `models/user.py` — User model with password_hash column
- `services/auth/jwt.py` — create_token() function

## Outputs (what this atom produces)
- `api/v1/auth.py` — POST /api/v1/auth/login endpoint
- `schemas/auth.py` — LoginRequest, LoginResponse Pydantic schemas
- `tests/test_auth_login.py` — Unit test for login endpoint

## Acceptance criteria
- [ ] POST /login with valid credentials returns JWT
- [ ] POST /login with invalid credentials returns 401
- [ ] JWT contains user_id, role, expiry
- [ ] Test covers both paths

## Cross-module contracts
- Dashboard module will import LoginResponse schema
- All protected routes will use the JWT dependency from this atom
```

### Effort field

Every atom declares its effort level. The runner uses this for model selection and turn allocation.

| Effort | Description | Max Turns | Model |
|--------|-------------|-----------|-------|
| `S` | < 3 files, < 100 lines, simple changes | 30 | Sonnet |
| `M` | 3-10 files, moderate logic | 50 | Opus |
| `L` | > 10 files, refactor, complex logic | 75 | Opus |

If no effort is declared, the runner defaults to `M`.

### Why atoms work

1. **Bounded scope** — the builder knows exactly what to produce
2. **Explicit dependencies** — the runner knows what must exist before starting
3. **Testable output** — every atom has acceptance criteria
4. **Cross-module visibility** — the "Inputs" and "Outputs" sections prevent silos
5. **Effort-calibrated resources** — model and turn limits match atom complexity

### Atom naming convention

```
{MODULE}-{NUMBER}{VARIANT}

Examples:
  AUTH-001     First auth atom
  AUTH-001b    Variant (split from AUTH-001 because it was too big)
  CORE-015    15th core atom
  DASH-003    3rd dashboard atom
```

### Atom file location

```
atoms/
├── auth/
│   ├── AUTH-001_user_login.md
│   ├── AUTH-002_jwt_refresh.md
│   └── AUTH-003_role_middleware.md
├── core/
│   ├── CORE-001_order_model.md
│   └── CORE-002_order_service.md
└── dashboard/
    └── DASH-001_overview_page.md
```

### BUILD_STATE.md

Track completion in a single file:

```markdown
# Build State

## Auth
- [x] AUTH-001 User login endpoint
- [x] AUTH-002 JWT refresh
- [ ] AUTH-003 Role middleware

## Core
- [ ] CORE-001 Order model
- [ ] CORE-002 Order service

## Dashboard
- [ ] DASH-001 Overview page
```

The runner reads this to know what's done and what's next. The JSON state file (Section 12) is the machine-readable source of truth; BUILD_STATE.md is regenerated from it.

---

## 6. The Runner

### What it does — 26 steps

The runner executes this loop for every atom:

| Step | Action | Details |
|------|--------|---------|
| 1 | **Startup cleanup** | Release stale claims from prior crashed sessions. Prune orphaned worktrees. Clean dirty git state (stash if uncommitted changes). |
| 2 | **Preflight health checks** | Verify DB, cache, storage, Claude CLI, disk space, Python/Node versions (Section 17). |
| 3 | **Read product.yaml** | Load tech stack, module list, custom gates, cross-product reads. |
| 4 | **Import BUILD_STATE.md to unified state** | Parse markdown checkboxes into JSON state. Reconcile with `state/build_state.json` — JSON wins on conflict. |
| 5 | **Build dependency graph, detect cycles** | Topological sort of all atoms. If cycle detected, print the cycle and abort. |
| 6 | **Find ready atoms** | Filter atoms where all `depends_on` entries have status `complete`. |
| 7 | **Sort by priority** | Priority order: gate-critical-path atoms > lower layer number > module alphabetical > atom number. |
| 8 | **Claim atom** | Atomic claim via SQLite (Section 12). If another agent holds the claim, skip to next ready atom. |
| 9 | **Detect atom type** | Infer type from filename pattern: `infra`, `auth`, `backend`, `frontend`, `fullstack`, `ai` (Section 13). |
| 10 | **Load context docs per atom type** | Load only the docs relevant to this atom type (Section 13). Cuts token usage 40-60%. |
| 11 | **Build prompt** | Select `fresh_prompt()`, `continue_prompt()`, or `fix_prompt()` based on atom state (Section 14). |
| 12 | **Set max_turns** | `S=30`, `M=50`, `L=75` based on atom effort field. |
| 13 | **Select model** | `S` effort -> Sonnet, `M`/`L` effort -> Opus. Override with `--model`. |
| 14 | **Invoke Claude Code session** | `claude --print --model {model} --max-turns {turns} -p "{prompt}"` with timeout. |
| 15 | **Categorize result** | Parse exit code and output into one of 9 failure modes (Section 15). |
| 16 | **If rate limited** | Unclaim atom, wait `retry_delay` seconds, continue loop from step 6. |
| 17 | **If context overflow / max turns** | Mark atom `blocked`, write handover file (Section 23), continue to next atom. |
| 18 | **If auth error** | Stop immediately. Print: `BLOCKED: Claude auth failed. Run 'claude auth' manually.` |
| 19 | **Verify deliverables exist** | Check that every file listed in atom's `Outputs` section actually exists on disk. Catches Claude claiming it created files it didn't. |
| 20 | **Run 21 validation gates** | Execute all gates (Section 7). Collect results. |
| 21 | **If gates fail** | Run self-healing fix loop (Section 8) — up to 3 cycles with regression guard. |
| 22 | **Run cross-module validation** | Anti-silo check (Section 9). Verify dependent modules still compile/import. |
| 23 | **Run layer-triggered post-scripts** | L1 atom -> extract schema columns JSON. L3 atom -> export openapi.json. L4 atom -> verify routes registered. |
| 24 | **Publish event** | `atom.complete` or `atom.failed` to event bus (Section 10). |
| 25 | **Record cost** | Extract tokens from Claude JSON response, compute USD, append to CSV (Section 16). |
| 26 | **Update state, push, repeat** | Mark atom complete/failed in JSON state. Regenerate BUILD_STATE.md. Git push. Loop to step 6. |

### CLI

```bash
# Build next ready atom
python3 scripts/build-runner/run.py

# Build specific atom
python3 scripts/build-runner/run.py --atom AUTH-001

# Build specific module
python3 scripts/build-runner/run.py --module auth

# Dry run — show wave plan with parallelizable atoms
python3 scripts/build-runner/run.py --dry-run

# Status
python3 scripts/build-runner/run.py --status

# Health check
python3 scripts/build-runner/run.py --health

# Budget cap
python3 scripts/build-runner/run.py --budget 50

# Model override
python3 scripts/build-runner/run.py --model claude-opus-4-6

# Max atoms per session
python3 scripts/build-runner/run.py --max-atoms 5

# Timeout per atom (seconds)
python3 scripts/build-runner/run.py --timeout 1800

# Parallel agents (worktree-isolated)
python3 scripts/build-runner/run.py --parallel 2
```

---

## 7. Validation Gates (21 Gates)

Every atom must pass ALL hard gates before its commit is accepted. No exceptions.

### Gate registry

| # | Gate | What it checks | Severity | Skip for |
|---|------|----------------|----------|----------|
| 1 | `syntax_check` | `py_compile` on all changed Python files | Hard | -- |
| 2 | `lint` | `ruff check` (Python) — zero errors | Hard | -- |
| 3 | `format` | `ruff format --check` (Python) or `prettier --check` (TS) | Hard | -- |
| 4 | `type_check` | `mypy` (Python) or `tsc --noEmit` (TS) — zero errors | Hard | -- |
| 5 | `file_size` | Every changed file <= 300 lines | Hard | Config files |
| 6 | `function_size` | Every function/method <= 50 lines | Hard | -- |
| 7 | `no_wildcard_cors` | No `allow_origins = ["*"]` in non-dev code | Hard | -- |
| 8 | `no_sql_injection` | No f-string/template SQL — parameterized only | Hard | -- |
| 9 | `no_hardcoded_secrets` | No passwords/keys/tokens in source (except test fixtures) | Hard | Test files |
| 10 | `no_unsafe_types` | No `any` (TS), no `# type: ignore` without reason (Python) | Hard | -- |
| 11 | `no_dangerous_patterns` | No `eval()`, `innerHTML`, `document.write`, `new Function()` | Hard | -- |
| 12 | `tests_exist` | Changed module has corresponding test file | Hard | Infra atoms |
| 13 | `tests_pass` | `pytest` (Python) or `vitest` (TS) — zero failures | Hard | -- |
| 14 | `migration_integrity` | `alembic check` (or equivalent) — no drift | Hard | Non-DB atoms |
| 15 | `contract_check` | Cross-module contracts still valid (Section 9) | Hard | -- |
| 16 | `cross_module_validation` | Dependent modules still import/compile (Section 9) | Soft (warn) | -- |
| 17 | `eslint` | `eslint --max-warnings 0` on all changed `.ts`/`.tsx` files | Hard | Non-frontend atoms |
| 18 | `vitest` | `vitest run` on changed frontend test files — zero failures | Hard | Non-frontend atoms |
| 19 | `import_sanity` | Try importing every changed Python module (`python -c "import ..."`) | Hard | -- |
| 20 | `dependency_map_freshness` | Warn if new exported symbols added without updating DEPENDENCY_MAP.md | Soft (warn) | -- |
| 21 | `deliverable_verification` | Every file listed in atom's `Outputs` section exists on disk | Hard | -- |

### Gate implementation pattern

```python
@dataclass
class GateResult:
    name: str
    passed: bool
    output: str = ""
    severity: str = "hard"  # hard = block commit, soft = warn only

class Gate:
    name: str
    severity: str = "hard"

    def check(self, project_root: Path, changed_files: list[str]) -> GateResult:
        raise NotImplementedError

class FileSizeGate(Gate):
    name = "file_size"

    def check(self, project_root, changed_files):
        violations = []
        for f in changed_files:
            path = project_root / f
            if path.suffix in (".py", ".ts", ".tsx") and path.exists():
                lines = len(path.read_text().splitlines())
                if lines > 300:
                    violations.append(f"{f}: {lines} lines (max 300)")
        return GateResult(
            self.name,
            passed=len(violations) == 0,
            output="\n".join(violations),
        )

class EslintGate(Gate):
    name = "eslint"

    def check(self, project_root, changed_files):
        ts_files = [
            f for f in changed_files
            if f.endswith((".ts", ".tsx")) and not f.endswith(".d.ts")
        ]
        if not ts_files:
            return GateResult(self.name, passed=True, output="No TS files changed")
        result = subprocess.run(
            ["npx", "eslint", "--max-warnings", "0"] + ts_files,
            capture_output=True, text=True, cwd=project_root / "src/frontend",
        )
        return GateResult(
            self.name,
            passed=result.returncode == 0,
            output=result.stdout + result.stderr,
        )

class ImportSanityGate(Gate):
    name = "import_sanity"

    def check(self, project_root, changed_files):
        py_files = [f for f in changed_files if f.endswith(".py")]
        failures = []
        for f in py_files:
            module = f.replace("/", ".").replace(".py", "")
            result = subprocess.run(
                ["python3", "-c", f"import {module}"],
                capture_output=True, text=True, cwd=project_root,
            )
            if result.returncode != 0:
                failures.append(f"{module}: {result.stderr.strip()}")
        return GateResult(
            self.name,
            passed=len(failures) == 0,
            output="\n".join(failures),
        )

class DeliverableVerificationGate(Gate):
    name = "deliverable_verification"

    def check(self, project_root, changed_files):
        """Check that files listed in atom Outputs actually exist on disk."""
        # This gate is called with atom_outputs injected via context
        missing = []
        for output_path in self._expected_outputs:
            full = project_root / output_path
            if not full.exists():
                missing.append(f"MISSING: {output_path}")
        return GateResult(
            self.name,
            passed=len(missing) == 0,
            output="\n".join(missing),
        )
```

### Extending the gate registry

See Appendix C for domain-specific gate extensions declared in `product.yaml`.

---

## 8. Self-Healing Fix Loop

### The problem

Gates fail. Previously, a gate failure meant the atom failed, a handover was written, and a human intervened. Across 6 products, 60% of gate failures were fixable by re-invoking Claude with just the error output. The fix loop automates this.

### How it works

```
Gate failure detected
  |
  v
Cycle 1: Re-invoke Claude with fix_prompt(gate_output)
  |
  v
Run gates again
  |-- All pass → commit, continue
  |-- Still failing →
      |
      v
      Cycle 2: Re-invoke with updated gate_output
        |
        v
        Run gates again
        |-- All pass → commit, continue
        |-- Still failing →
            |
            v
            Cycle 3: Final attempt
              |
              v
              Run gates again
              |-- All pass → commit, continue
              |-- Still failing → write handover, mark failed
```

### Validation vs. regression fixes

The fix loop distinguishes two types of fixes:

| Type | Example | Strategy |
|------|---------|----------|
| **Validation fix** | mypy error, lint warning, file too long | Fix the specific error. Low risk. |
| **Regression fix** | E2E test broke after fixing a backend gate | Higher risk. Needs regression guard. |

### Regression guard

After every fix cycle, run the FULL test suite — not just the failing gate. If a fix introduces a new failure:

```python
def fix_loop(atom, config, gates, max_cycles=3):
    for cycle in range(1, max_cycles + 1):
        # Snapshot test state before fix
        pre_fix_results = run_all_gates(config, atom.changed_files)
        pre_fix_passing = {g.name for g in pre_fix_results if g.passed}

        # Invoke Claude with fix prompt
        fix_output = invoke_claude(fix_prompt(atom, gate_failures))

        # Run all gates again
        post_fix_results = run_all_gates(config, atom.changed_files)
        post_fix_passing = {g.name for g in post_fix_results if g.passed}

        # Regression guard: did the fix break something that was passing?
        regressions = pre_fix_passing - post_fix_passing
        if regressions:
            log.warning(
                "Fix cycle %d introduced regressions: %s — reverting",
                cycle, regressions,
            )
            subprocess.run(["git", "checkout", "."], cwd=config.project_root)
            # Try next cycle with different approach
            gate_failures = [
                g for g in post_fix_results if not g.passed
            ]
            continue

        # Check if all hard gates pass
        hard_failures = [
            g for g in post_fix_results
            if not g.passed and g.severity == "hard"
        ]
        if not hard_failures:
            return "FIXED"

        gate_failures = hard_failures

    return "FAILED"  # Exhausted all cycles
```

### Key rules

1. **Max 3 fix cycles.** After that, the problem needs human eyes.
2. **fix_prompt only.** Never re-send the full atom context during fixes. Only send gate output + "fix these errors" (Section 14).
3. **Regression guard is mandatory.** If an E2E fix breaks backend tests, auto-revert the last commit and try a different approach.
4. **Never fix soft gates.** Soft gates (warn-only) don't trigger the fix loop.

---

## 9. Cross-Module Communication — The Anti-Silo Core

**This is the most important section.** Everything else in this document supports this.

### The problem it solves

You build Module A. It creates a `users` table with columns `(id, name, email)`. Later, you build Module B. It queries `SELECT id, name, email, role FROM users`. It compiles. It passes its own tests. It fails at runtime because `role` doesn't exist.

### Three mechanisms to prevent this

#### Mechanism 1: Contract files

Every module that produces data declares a contract. Every module that consumes data imports that contract.

```
contracts/
├── auth/
│   ├── user_schema.py          # What the users table looks like
│   └── auth_response.py        # What POST /login returns
├── orders/
│   ├── order_schema.py         # What the orders table looks like
│   └── order_event.py          # What the "order.created" event payload looks like
└── shared/
    └── pagination.py           # Shared pagination types
```

**Rule:** If module B reads module A's data, module B must import module A's contract. If the contract changes, module B's import breaks at compile time, not at runtime.

#### Mechanism 2: Post-atom cross-module check

After every atom completes, the runner runs this check:

```python
def cross_module_check(changed_files: list[str], project_root: Path) -> list[str]:
    """Check if changes in this atom break other modules."""
    issues = []

    # 1. Did we change a model/schema?
    schema_changes = [f for f in changed_files if "models/" in f or "schema" in f]
    if schema_changes:
        # Find all files that import from the changed modules
        for sf in schema_changes:
            module_name = extract_module_name(sf)
            importers = grep_imports(project_root, module_name)
            for importer in importers:
                # Try to compile/import the dependent file
                if not try_import(importer):
                    issues.append(
                        f"CROSS-MODULE BREAK: {sf} changed, "
                        f"but {importer} (which imports it) no longer compiles"
                    )

    # 2. Did we change an API route's response shape?
    route_changes = [f for f in changed_files if "api/" in f or "routes/" in f]
    if route_changes:
        # Check if any frontend service files reference this endpoint
        for rf in route_changes:
            endpoints = extract_endpoints(rf)
            for ep in endpoints:
                consumers = grep_endpoint_consumers(project_root, ep)
                if consumers:
                    issues.append(
                        f"API CONTRACT: {ep} changed in {rf}. "
                        f"Consumers: {', '.join(consumers)}. Verify shapes match."
                    )

    # 3. Did we change a migration?
    migration_changes = [f for f in changed_files if "migration" in f or "alembic" in f]
    if migration_changes:
        # Check all cross-schema reads still work
        issues.extend(check_cross_schema_reads(project_root))

    return issues
```

#### Mechanism 3: Event bus

When an atom completes, it fires an event. Other modules can subscribe.

```python
# After AUTH-001 completes:
event_bus.publish({
    "type": "atom.complete",
    "module": "auth",
    "atom_id": "AUTH-001",
    "changed_files": ["models/user.py", "api/v1/auth.py"],
    "outputs": ["POST /api/v1/auth/login"],
})

# The dashboard module's subscription:
event_bus.subscribe("atom.complete", lambda e:
    validate_dashboard_still_works(e) if "auth" in e["module"] else None
)
```

### When silos sneak in anyway

Even with these mechanisms, silos creep in when:

1. **Atom specs don't declare cross-module contracts** — Fix: make "Inputs" and "Outputs" mandatory in every atom spec (Section 5)
2. **The runner skips cross-module checks to save time** — Fix: gate 15 (contract_check) is HARD, not soft
3. **Two modules use the same table name in different schemas** — Fix: schema-qualified models always (Section 4.3)
4. **A background job writes data that a service reads, but they never run together in tests** — Fix: integration tests run producer + consumer together (Section 20)
5. **Frontend calls an API endpoint that changed shape** — Fix: generate TypeScript types from OpenAPI spec after every L3 atom

---

## 10. Event Bus Pattern

### Purpose

The event bus ensures that when module A changes, module B knows about it. Without this, each module is built in a vacuum.

### Implementation

```python
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Callable, Any

@dataclass
class Event:
    type: str                    # "atom.complete", "schema.changed", etc.
    module: str                  # Which module fired it
    data: dict = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

class EventBus:
    def __init__(self, events_file: Path):
        self._file = events_file
        self._subscribers: dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        self._subscribers.setdefault(event_type, []).append(callback)

    def publish(self, event: Event):
        # Persist
        with open(self._file, "a") as f:
            f.write(json.dumps(asdict(event)) + "\n")
        # Notify
        for cb in self._subscribers.get(event.type, []):
            try:
                cb(event)
            except Exception as e:
                print(f"[EventBus] Subscriber error: {e}")

    def replay(self, since: str | None = None) -> list[Event]:
        """Replay events from disk (for crash recovery)."""
        events = []
        if self._file.exists():
            for line in self._file.read_text().splitlines():
                if line.strip():
                    data = json.loads(line)
                    if since and data["timestamp"] < since:
                        continue
                    events.append(Event(**data))
        return events
```

### Well-known event types

| Event | When | Subscribers should |
|-------|------|--------------------|
| `atom.complete` | Atom passes all gates and commits | Validate dependent modules still compile |
| `atom.failed` | Atom exhausted retries | Alert, skip dependents |
| `schema.changed` | Model or migration file modified | Re-validate all modules that read from that table |
| `api.changed` | Route file modified | Re-validate all consumers of that endpoint |
| `contract.changed` | Contract file modified | Re-compile all importers |
| `build.started` | Runner starts | -- |
| `build.finished` | Runner done | Summary report |
| `test.regression` | A previously-passing test now fails | Investigate root cause |

---

## 11. Dependency Graph & Wave Planning

### What it tracks

```
AUTH-001 (User model)
  +-- AUTH-002 (Login endpoint) <- depends on AUTH-001
       +-- DASH-001 (Dashboard) <- depends on AUTH-002
            +-- DASH-002 (Charts) <- depends on DASH-001

CORE-001 (Order model)
  +-- CORE-002 (Order service) <- depends on CORE-001
       |-- CORE-003 (Order API) <- depends on CORE-002
       +-- REPORT-001 (Order report) <- depends on CORE-002
```

### Two types of dependencies

| Type | Example | How it's declared |
|------|---------|-------------------|
| **Build dependency** | AUTH-002 needs AUTH-001's User model to exist | `Depends on: AUTH-001` in atom spec |
| **Runtime dependency** | Dashboard calls POST /api/v1/auth/login | `Inputs: POST /api/v1/auth/login` in atom spec |

Build dependencies are hard — the runner won't start an atom until its deps are complete.

Runtime dependencies are checked by the cross-module validator (Section 9).

### Topological sort

The runner builds atoms in topological order:

```python
def find_ready_atoms(build_state: dict, atoms: list) -> list:
    """Return atoms whose dependencies are ALL complete."""
    completed = {a["id"] for a in atoms if build_state.get(a["id"]) == "complete"}
    return [
        a for a in atoms
        if build_state.get(a["id"]) == "pending"
        and all(dep in completed for dep in a["depends_on"])
    ]
```

### Cycle detection

If A depends on B and B depends on A, the runner refuses to start and prints the cycle. Fix by splitting one of them.

### Wave plan visualization

The `--dry-run` flag outputs a numbered wave plan showing which atoms can run in parallel:

```
$ python3 run.py --dry-run

Wave Plan (4 waves, 12 atoms):

Wave 1 (parallel):
  AUTH-001  [L1] User model          (Effort: S)
  CORE-001  [L1] Order model         (Effort: S)
  CORE-004  [L1] Inventory model     (Effort: S)

Wave 2 (parallel):
  AUTH-002  [L2] Auth service         (Effort: M, deps: AUTH-001)
  CORE-002  [L2] Order service        (Effort: M, deps: CORE-001)
  CORE-005  [L2] Inventory service    (Effort: M, deps: CORE-004)

Wave 3 (parallel):
  AUTH-003  [L3] Login endpoint       (Effort: S, deps: AUTH-002)
  CORE-003  [L3] Order API            (Effort: M, deps: CORE-002)
  REPORT-001 [L3] Order report API    (Effort: L, deps: CORE-002)

Wave 4 (parallel):
  DASH-001  [L4] Dashboard page       (Effort: L, deps: AUTH-003, CORE-003)
  DASH-002  [L4] Charts component     (Effort: M, deps: DASH-001)
  REPORT-002 [L4] Report page         (Effort: M, deps: REPORT-001)

Estimated cost: $18.50 (3 S @ $0.50, 6 M @ $1.50, 3 L @ $2.50)
Estimated time: 4h sequential, 1.5h parallel (--parallel 3)
```

Implementation:

```python
def compute_waves(atoms: list[dict], state: dict) -> list[list[dict]]:
    """Group atoms into waves. Atoms in the same wave have no
    inter-dependencies and can run in parallel."""
    completed = {a["id"] for a in atoms if state.get(a["id"]) == "complete"}
    remaining = [a for a in atoms if state.get(a["id"]) != "complete"]
    waves = []
    while remaining:
        wave = [
            a for a in remaining
            if all(d in completed for d in a["depends_on"])
        ]
        if not wave:
            # Remaining atoms all have unresolvable deps
            log.error("Blocked atoms: %s", [a["id"] for a in remaining])
            break
        waves.append(wave)
        completed |= {a["id"] for a in wave}
        remaining = [a for a in remaining if a["id"] not in completed]
    return waves
```

---

## 12. State Management & Claim System

### Unified state file

All build state lives in one JSON file:

```json
{
  "atoms": {
    "AUTH-001": {
      "status": "complete",
      "started_at": "2026-05-30T10:00:00Z",
      "completed_at": "2026-05-30T10:05:00Z",
      "attempts": 1,
      "agent_id": "agent-01",
      "claimed_by": null,
      "claimed_at": null
    },
    "AUTH-002": {
      "status": "building",
      "started_at": "2026-05-30T10:06:00Z",
      "attempts": 1,
      "claimed_by": "agent-02",
      "claimed_at": "2026-05-30T10:06:00Z"
    },
    "CORE-001": {
      "status": "pending",
      "claimed_by": null,
      "claimed_at": null
    }
  },
  "last_updated": "2026-05-30T10:06:00Z"
}
```

### Status lifecycle

```
pending --> claimed --> building --> complete
                   |            |
                   |            +--> failed
                   |            |
                   |            +--> blocked
                   |
                   +--> unclaimed (on rate limit or crash recovery)
```

| Status | Meaning |
|--------|---------|
| `pending` | Not started, no agent assigned |
| `claimed` | Agent has reserved this atom, about to start |
| `building` | Claude session active, work in progress |
| `complete` | All gates passed, committed, pushed |
| `failed` | Exhausted retries, handover written |
| `blocked` | Cannot proceed (context overflow, missing dep, etc.) |

### SQLite-backed atomic claim system

For parallel execution, the JSON state file is not safe for concurrent writes. The claim system uses SQLite with WAL mode for atomic operations:

```python
import sqlite3
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

STALE_CLAIM_MINUTES = 30  # Claims older than this are auto-released

class ClaimStore:
    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._conn = sqlite3.connect(str(db_path), isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                atom_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                claimed_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'claimed'
            )
        """)

    def claim(self, atom_id: str, agent_id: str) -> bool:
        """Atomically claim an atom. Returns True if successful."""
        try:
            self._conn.execute(
                "INSERT INTO claims (atom_id, agent_id, claimed_at, status) "
                "VALUES (?, ?, ?, 'claimed')",
                (atom_id, agent_id, datetime.now(timezone.utc).isoformat()),
            )
            return True
        except sqlite3.IntegrityError:
            return False  # Already claimed by another agent

    def unclaim(self, atom_id: str, agent_id: str) -> bool:
        """Release a claim. Only the owning agent can unclaim."""
        cursor = self._conn.execute(
            "DELETE FROM claims WHERE atom_id = ? AND agent_id = ?",
            (atom_id, agent_id),
        )
        return cursor.rowcount > 0

    def update_status(self, atom_id: str, agent_id: str, status: str):
        """Update claim status. Only the owning agent can update."""
        self._conn.execute(
            "UPDATE claims SET status = ? "
            "WHERE atom_id = ? AND agent_id = ?",
            (status, atom_id, agent_id),
        )

    def release_stale_claims(self):
        """Release claims from crashed sessions (older than threshold)."""
        cutoff = (
            datetime.now(timezone.utc) - timedelta(minutes=STALE_CLAIM_MINUTES)
        ).isoformat()
        cursor = self._conn.execute(
            "DELETE FROM claims WHERE claimed_at < ? AND status IN ('claimed', 'building')",
            (cutoff,),
        )
        if cursor.rowcount > 0:
            log.info("Released %d stale claims", cursor.rowcount)

    def is_claimed(self, atom_id: str) -> bool:
        """Check if an atom is currently claimed."""
        row = self._conn.execute(
            "SELECT 1 FROM claims WHERE atom_id = ?", (atom_id,)
        ).fetchone()
        return row is not None

    def close(self):
        self._conn.close()
```

### Startup cleanup

At runner startup, always call `release_stale_claims()` to recover from prior crashes:

```python
def startup_cleanup(claim_store: ClaimStore, project_root: Path):
    """Run at startup before any atom processing."""
    # 1. Release stale claims from crashed sessions
    claim_store.release_stale_claims()

    # 2. Prune orphaned git worktrees
    subprocess.run(
        ["git", "worktree", "prune"],
        cwd=project_root, capture_output=True,
    )

    # 3. Clean dirty git state
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=project_root,
    )
    if result.stdout.strip():
        log.warning("Dirty git state at startup — stashing")
        subprocess.run(
            ["git", "stash", "--include-untracked"],
            cwd=project_root, capture_output=True,
        )
```

### Why not just BUILD_STATE.md?

BUILD_STATE.md is human-readable but:
- Can't track attempts, timestamps, or agent assignments
- Can't express cross-module dependencies
- Merge conflicts when parallel agents update it simultaneously
- Not safe for concurrent writes

The JSON state + SQLite claims are the source of truth. BUILD_STATE.md is generated from them for human readability.

---

## 13. Context Loading Table

### The problem

Loading the full project context (CLAUDE.md, CONVENTIONS.md, DECISIONS.md, API_SURFACE.md, SYSTEM_MAP.md, DEPENDENCIES.md, DESIGN_SYSTEM.md, ...) into every Claude session wastes 40-60% of tokens on irrelevant docs. An infra atom doesn't need DESIGN_SYSTEM.md. A frontend atom doesn't need SCHEMA.md.

### Atom type detection

The runner infers atom type from the atom filename and its declared layer/module:

```python
def detect_atom_type(atom: dict) -> str:
    """Detect atom type for context loading."""
    atom_id = atom["id"].lower()
    layer = atom.get("layer", "").lower()
    module = atom.get("module", "").lower()
    outputs = " ".join(atom.get("outputs", [])).lower()

    if module in ("infra", "docker", "deploy"):
        return "infra"
    if module in ("auth", "rbac", "security"):
        return "auth"
    if layer in ("l4", "l5") or "frontend" in outputs or ".tsx" in outputs:
        return "frontend"
    if module in ("intelligence", "ml", "ai", "llm"):
        return "ai"
    if layer in ("l1", "l2", "l3") and "frontend" not in outputs:
        return "backend"
    # Touches both backend and frontend
    if any(ext in outputs for ext in [".py", ".tsx", ".ts"]):
        return "fullstack"

    return "backend"  # default
```

### Context loading matrix

| Doc | infra | auth | backend | frontend | fullstack | ai |
|-----|-------|------|---------|----------|-----------|----|
| `CLAUDE.md` | Y | Y | Y | Y | Y | Y |
| `CONVENTIONS.md` | Y | Y | Y | Y | Y | Y |
| `DEPENDENCY_MAP.md` | Y | Y | Y | Y | Y | Y |
| `DECISIONS.md` | -- | Y | Y | -- | Y | Y |
| `API_SURFACE.md` | -- | Y | Y | Y | Y | -- |
| `SYSTEM_MAP.md` | -- | -- | Y | -- | Y | Y |
| `DESIGN_SYSTEM.md` | -- | -- | -- | Y | Y | -- |
| `SCHEMA.md` | -- | Y | Y | -- | Y | -- |
| `DEPLOYMENT.md` | Y | -- | -- | -- | -- | -- |
| `TROUBLESHOOTING.md` | Y | -- | -- | -- | -- | -- |
| `SECURITY.md` | Y | Y | -- | -- | -- | -- |
| `contracts/` (relevant) | -- | Y | Y | Y | Y | -- |
| Recent atom outputs | -- | -- | Y | Y | Y | Y |

**`DEPENDENCY_MAP.md` is ALWAYS loaded**, regardless of atom type. It's the single source of truth for what connects to what.

### Implementation

```python
CONTEXT_MATRIX = {
    "infra": [
        "CLAUDE.md", "CONVENTIONS.md", "DEPENDENCY_MAP.md",
        "DEPLOYMENT.md", "TROUBLESHOOTING.md", "SECURITY.md",
    ],
    "auth": [
        "CLAUDE.md", "CONVENTIONS.md", "DEPENDENCY_MAP.md",
        "DECISIONS.md", "API_SURFACE.md", "SCHEMA.md", "SECURITY.md",
    ],
    "backend": [
        "CLAUDE.md", "CONVENTIONS.md", "DEPENDENCY_MAP.md",
        "DECISIONS.md", "API_SURFACE.md", "SYSTEM_MAP.md", "SCHEMA.md",
    ],
    "frontend": [
        "CLAUDE.md", "CONVENTIONS.md", "DEPENDENCY_MAP.md",
        "API_SURFACE.md", "DESIGN_SYSTEM.md",
    ],
    "fullstack": [
        "CLAUDE.md", "CONVENTIONS.md", "DEPENDENCY_MAP.md",
        "DECISIONS.md", "API_SURFACE.md", "SYSTEM_MAP.md",
        "DESIGN_SYSTEM.md", "SCHEMA.md",
    ],
    "ai": [
        "CLAUDE.md", "CONVENTIONS.md", "DEPENDENCY_MAP.md",
        "DECISIONS.md", "SYSTEM_MAP.md",
    ],
}

def load_context(atom_type: str, project_root: Path) -> str:
    """Load only the docs relevant to this atom type."""
    docs = CONTEXT_MATRIX.get(atom_type, CONTEXT_MATRIX["backend"])
    context_parts = []
    for doc_name in docs:
        doc_path = project_root / doc_name
        if doc_path.exists():
            content = doc_path.read_text()
            context_parts.append(f"# {doc_name}\n{content}")
        elif doc_path.is_dir():
            # For directories like contracts/, load relevant files
            for f in sorted(doc_path.rglob("*.py")):
                content = f.read_text()
                context_parts.append(
                    f"# {f.relative_to(project_root)}\n{content}"
                )
    return "\n\n---\n\n".join(context_parts)
```

### Token savings

Measured across 3 products:

| Product scale | Full context tokens | Typed context tokens | Savings |
|---------|--------------------|--------------------|---------|
| Large (408 atoms, 56 models) | ~45K per session | ~22K per session | 51% |
| Medium (120 atoms, 30 models) | ~30K per session | ~14K per session | 53% |
| Small (85 atoms, 15 models) | ~25K per session | ~15K per session | 40% |

---

## 14. Prompt Differentiation (3 Types)

### Why three prompt types

Sending the same prompt for every invocation wastes tokens and confuses the model. A retry doesn't need the full product context. A fix doesn't need the atom spec — it needs the error.

### 1. fresh_prompt() — First invocation

Used when: atom status is `pending` (first attempt).

```python
def fresh_prompt(atom: dict, context: str, config: dict) -> str:
    return f"""You are building a software product. Follow the instructions exactly.

## Project Context
{context}

## Your Task
Build this atom:

{atom['spec_content']}

## Rules
- Read all files in the Inputs section before writing any code
- Produce ALL files listed in the Outputs section
- Write tests FIRST, then implement
- Every file must be under 300 lines
- Every function must be under 50 lines
- Use schema-qualified table names
- Update cross-module contracts if you change any interface

## When done
- Run the test suite for your changes
- Commit with message: [{atom['id']}] {atom['title']}
"""
```

### 2. continue_prompt() — Retry with partial work

Used when: atom status is `building` (prior attempt made progress but didn't complete).

```python
def continue_prompt(atom: dict, context: str, config: dict) -> str:
    # Get git status to show what was already done
    git_status = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True, text=True, cwd=config["project_root"],
    ).stdout

    git_diff = subprocess.run(
        ["git", "diff", "--stat"],
        capture_output=True, text=True, cwd=config["project_root"],
    ).stdout

    return f"""You are CONTINUING work on an atom that was partially completed.

## Atom
{atom['id']}: {atom['title']}

## What was already done (git status)
```
{git_status}
```

## Changes so far (git diff --stat)
```
{git_diff}
```

## Original atom spec
{atom['spec_content']}

## Context (abbreviated)
{context}

## Instructions
1. Review what was already done
2. Complete the remaining work
3. Run tests
4. Commit with message: [{atom['id']}] {atom['title']}

Do NOT redo work that is already complete. Focus on what's missing.
"""
```

### 3. fix_prompt() — Gate failed, minimal context

Used when: gates failed after the atom was built. This prompt is deliberately minimal — only the error and one instruction.

```python
def fix_prompt(atom: dict, gate_failures: list[GateResult]) -> str:
    failure_text = "\n\n".join(
        f"### Gate: {g.name} (FAILED)\n```\n{g.output}\n```"
        for g in gate_failures
    )

    return f"""The following validation gates FAILED for atom {atom['id']}.
Fix each error. Do not change anything else.

{failure_text}

Rules:
- Fix ONLY the errors listed above
- Do not refactor or improve unrelated code
- Do not add new features
- Run the failing checks again after fixing
- If a fix would break other tests, find a different approach
"""
```

### Prompt selection logic

```python
def select_prompt(atom: dict, state: dict, context: str, config: dict,
                  gate_failures: list[GateResult] | None = None) -> str:
    atom_state = state["atoms"].get(atom["id"], {})
    status = atom_state.get("status", "pending")

    if gate_failures:
        return fix_prompt(atom, gate_failures)
    elif status == "building":
        return continue_prompt(atom, context, config)
    else:
        return fresh_prompt(atom, context, config)
```

---

## 15. Error Categorization & Recovery Paths

### The 9 failure modes

Every Claude session exit is categorized into exactly one of these 9 modes. Each has a specific recovery path.

| # | Category | Detection | Recovery | Auto-recoverable? |
|---|----------|-----------|----------|--------------------|
| 1 | `timeout` | Process killed by timeout | Retry with `continue_prompt`. Same atom, attempt +1. | Yes (up to 3) |
| 2 | `rate_limit` | Output contains "rate_limit", "429", "too many requests", "hit your limit" | Unclaim atom. Wait `retry_delay` seconds. Re-enter main loop. | Yes |
| 3 | `auth_error` | Output contains "unauthorized", "auth", "invalid token", "please authenticate" | Stop immediately. Print manual fix instruction. | No |
| 4 | `context_overflow` | Output contains "context window", "too long", "token limit" | Mark atom `blocked`. Write handover. Move to next atom. | No (split atom) |
| 5 | `max_turns` | Claude exits with max turns reached | Retry with `continue_prompt` and +25 more turns. If still fails, write handover. | Partial (1 retry) |
| 6 | `nested_session` | Output contains "CLAUDE_CODE", "nested session", "already running" | Stop immediately. Fix env: `unset CLAUDECODE`. | No |
| 7 | `session_fail` | Non-zero exit code not matching above patterns | Retry with `fresh_prompt`. Attempt +1. | Yes (up to 3) |
| 8 | `gate_fail` | Session succeeded but gates failed | Run fix loop (Section 8). Up to 3 fix cycles. | Yes (fix loop) |
| 9 | `success` | Zero exit code, all gates pass | Commit, push, publish event. | N/A |

### Implementation

```python
def categorize_result(
    exit_code: int,
    stdout: str,
    stderr: str,
    timed_out: bool,
) -> str:
    """Categorize a Claude session result into one of 9 failure modes."""
    output = (stdout + stderr).lower()

    if timed_out:
        return "timeout"

    if any(kw in output for kw in ["rate_limit", "429", "too many requests", "hit your limit"]):
        return "rate_limit"

    if any(kw in output for kw in ["unauthorized", "invalid token", "please authenticate"]):
        return "auth_error"

    if any(kw in output for kw in ["context window", "too long", "token limit"]):
        return "context_overflow"

    if any(kw in output for kw in ["max turns", "maximum number of turns"]):
        return "max_turns"

    if any(kw in output for kw in ["claude_code", "claudecode", "nested session", "already running"]):
        return "nested_session"

    if exit_code != 0:
        return "session_fail"

    return "success"  # Gates checked separately after this
```

### Recovery dispatcher

```python
def handle_failure(
    category: str,
    atom: dict,
    config: dict,
    state: dict,
    claim_store: ClaimStore,
    attempt: int,
) -> str:
    """Handle a categorized failure. Returns action for main loop."""
    agent_id = config["agent_id"]

    if category == "timeout":
        if attempt < 3:
            state["atoms"][atom["id"]]["status"] = "building"
            return "RETRY"
        return "FAILED"

    if category == "rate_limit":
        claim_store.unclaim(atom["id"], agent_id)
        state["atoms"][atom["id"]]["status"] = "pending"
        return "RATE_LIMITED"

    if category == "auth_error":
        log.error("BLOCKED: Claude auth failed. Run 'claude auth' manually.")
        return "STOP"

    if category == "context_overflow":
        state["atoms"][atom["id"]]["status"] = "blocked"
        write_handover(atom, "Context window exceeded. Split this atom.")
        return "SKIP"

    if category == "max_turns":
        if attempt < 2:
            # Retry with more turns
            config["extra_turns"] = 25
            return "RETRY"
        state["atoms"][atom["id"]]["status"] = "blocked"
        write_handover(atom, "Max turns exceeded even with extension.")
        return "SKIP"

    if category == "nested_session":
        log.error(
            "BLOCKED: Nested Claude session detected. "
            "Unset CLAUDECODE env var and restart."
        )
        return "STOP"

    if category == "session_fail":
        if attempt < 3:
            return "RETRY"
        return "FAILED"

    return "FAILED"
```

---

## 16. Cost & Budget Tracking

### Per-atom cost ledger

```csv
timestamp,atom_id,session_type,cost_usd,input_tokens,output_tokens,cache_read_tokens,cache_creation_tokens,model,duration_ms,effort
2026-05-30T10:00:00Z,AUTH-001,build,0.45,12000,5000,8000,4000,claude-opus-4-6,120000,M
2026-05-30T10:05:00Z,AUTH-001,fix_gates,0.12,3000,1500,2000,1000,claude-opus-4-6,30000,M
```

### Token extraction from Claude JSON response

Claude Code returns a JSON response that includes token usage. Extract it:

```python
import json

def extract_token_usage(claude_output: str) -> dict:
    """Extract token counts from Claude's JSON response."""
    try:
        # Claude --print --output-format json returns structured output
        data = json.loads(claude_output)
        usage = data.get("usage", {})
        return {
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
        }
    except (json.JSONDecodeError, KeyError):
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        }

def compute_cost(tokens: dict, model: str) -> float:
    """Compute USD cost from token counts."""
    # Pricing as of 2026-05 (update when pricing changes)
    PRICING = {
        "claude-opus-4-6": {
            "input": 15.0 / 1_000_000,
            "output": 75.0 / 1_000_000,
            "cache_read": 1.5 / 1_000_000,
            "cache_creation": 18.75 / 1_000_000,
        },
        "claude-sonnet-4-6": {
            "input": 3.0 / 1_000_000,
            "output": 15.0 / 1_000_000,
            "cache_read": 0.3 / 1_000_000,
            "cache_creation": 3.75 / 1_000_000,
        },
    }
    p = PRICING.get(model, PRICING["claude-opus-4-6"])
    return (
        tokens["input_tokens"] * p["input"]
        + tokens["output_tokens"] * p["output"]
        + tokens["cache_read_input_tokens"] * p["cache_read"]
        + tokens["cache_creation_input_tokens"] * p["cache_creation"]
    )
```

### Budget enforcement

```python
if total_cost > config.budget:
    log.warning(f"Budget exceeded: ${total_cost:.2f} > ${config.budget:.2f}")
    # Stop building, don't crash — save state for resume
    break
```

### Effort-based turn allocation

| Atom effort | Max turns | Model | Estimated cost/atom |
|-------------|-----------|-------|---------------------|
| `S` (Small: < 3 files, < 100 lines) | 30 | Sonnet | $0.30 - $0.80 |
| `M` (Medium: 3-10 files) | 50 | Opus | $1.00 - $3.00 |
| `L` (Large: > 10 files, refactor) | 75 | Opus | $2.00 - $5.00 |

Override with `--model` for consistency when quality matters more than cost.

---

## 17. Health Checks & Preflight

Before any build, verify infrastructure:

```python
def preflight_checks(config) -> list[HealthResult]:
    return [
        check_disk_space(min_gb=3),
        check_database(config.database),
        check_cache(config.cache),
        check_storage(config.storage),
        check_claude_cli_auth(),
        check_git_clean(),
        check_python_version(min_version="3.11"),
        check_node_version(min_version="18"),
        check_claudecode_env_unset(),
        check_atom_checksums(config.atoms_dir),
        check_db_git_reconciliation(config),
    ]
```

### Check catalog

| Check | What it verifies | Failure action |
|-------|-----------------|----------------|
| Disk space | >= 3 GB free | Stop — can't build |
| Database | Connection + schemas exist | Stop — can't test |
| Cache | Redis PING/PONG | Warn — some features may fail |
| Storage | MinIO/S3 health | Warn — file upload tests skip |
| Claude CLI | `claude --version` succeeds | Stop — can't build |
| Git clean | No uncommitted changes | Stash or stop |
| Python version | >= 3.11 | Stop |
| Node version | >= 18 (if frontend exists) | Stop |
| CLAUDECODE env unset | `CLAUDECODE` env var is NOT set | Stop — prevents nested session errors |
| Atom checksums | Atom spec files haven't been tampered with mid-build | Warn — atom may produce different results |
| DB/git reconciliation | If an atom's commit exists in git but state says `building`, reconcile to `complete` | Auto-fix — update state to match reality |

### CLAUDECODE env var check

Claude Code sets a `CLAUDECODE` environment variable when running. If this var is set when the runner starts, it means the runner is being invoked from inside a Claude session — which causes cryptic "nested session" failures.

```python
def check_claudecode_env_unset() -> HealthResult:
    """Ensure CLAUDECODE env var is not set (prevents nested sessions)."""
    if os.environ.get("CLAUDECODE"):
        return HealthResult(
            name="claudecode_env_unset",
            passed=False,
            output=(
                "CLAUDECODE env var is set. This means you're running "
                "inside a Claude session. Run the builder from a plain "
                "terminal: unset CLAUDECODE && python3 run.py"
            ),
        )
    return HealthResult("claudecode_env_unset", passed=True)
```

### Atom checksum verification

Detect if atom spec files changed during a build (e.g., someone edited an atom spec while the builder was running):

```python
import hashlib

def check_atom_checksums(atoms_dir: Path, stored_checksums: dict) -> HealthResult:
    """Verify atom specs haven't changed since build started."""
    mismatches = []
    for atom_file in atoms_dir.rglob("*.md"):
        current_hash = hashlib.sha256(atom_file.read_bytes()).hexdigest()
        stored = stored_checksums.get(str(atom_file))
        if stored and stored != current_hash:
            mismatches.append(str(atom_file))
    return HealthResult(
        "atom_checksums",
        passed=len(mismatches) == 0,
        output=f"Changed atoms: {mismatches}" if mismatches else "",
        severity="soft",
    )
```

### DB/git reconciliation

If the runner crashed after committing but before updating state, reconcile:

```python
def check_db_git_reconciliation(config: dict) -> HealthResult:
    """If a chunk was committed to git but not marked complete, fix it."""
    state = load_state(config["state_dir"])
    reconciled = []
    for atom_id, atom_state in state["atoms"].items():
        if atom_state["status"] in ("claimed", "building"):
            # Check if this atom's commit exists in git
            result = subprocess.run(
                ["git", "log", "--oneline", f"--grep=[{atom_id}]", "-1"],
                capture_output=True, text=True, cwd=config["project_root"],
            )
            if result.stdout.strip():
                atom_state["status"] = "complete"
                atom_state["completed_at"] = datetime.now(timezone.utc).isoformat()
                reconciled.append(atom_id)
    if reconciled:
        save_state(state, config["state_dir"])
    return HealthResult(
        "db_git_reconciliation",
        passed=True,
        output=f"Auto-reconciled: {reconciled}" if reconciled else "",
    )
```

---

## 18. Git & Commit Discipline

### Commit format

```
[ATOM_ID] brief description

Examples:
[AUTH-001] Add user login endpoint with JWT
[CORE-003] Wire order service to API routes
[DASH-001] Build overview dashboard page
```

### Rules

| Rule | Enforcement |
|------|-------------|
| No commits without all gates passing | Runner blocks commit if gates fail |
| One commit per atom | Runner enforces single-commit-per-atom |
| No `--no-verify` | Runner refuses to skip hooks |
| No force push to main/master | Runner refuses |
| Commit message must start with atom ID | Runner validates format |
| No secrets in commits | Gate 9 checks |
| No files > 300 lines in commits | Gate 5 checks |
| Push after every atom | Runner auto-pushes on success |

### Branch strategy

```
main                    <- stable, always passes all gates
  +-- build/session-001  <- runner creates per-session branch
       +-- atom/AUTH-001  <- one branch per atom (merged to session branch)
```

### Merge conflict auto-resolution (parallel builds)

When parallel agents merge back to the session branch, conflicts arise in predictable files. Auto-resolution rules:

| File type | Resolution strategy | Rationale |
|-----------|-------------------|-----------|
| `state/build_state.json` | Take theirs (other agent's version) | State is reconciled at startup anyway |
| `BUILD_STATE.md` | Regenerate from JSON state | It's a derived file |
| `events/events.jsonl` | Concatenate both versions | Events are append-only |
| `logs/cost_tracking.csv` | Concatenate both versions | Costs are append-only |
| `contracts/schema_columns.json` | Regenerate from models | It's a derived file |
| `API_SURFACE.md` | Regenerate from routes | It's a derived file |
| `openapi.json` | Regenerate from running server | It's a derived file |
| Source code (`.py`, `.ts`, `.tsx`) | **ABORT merge. Do not auto-resolve.** | Code merges need human/AI review |

```python
def auto_resolve_conflict(file_path: str) -> str | None:
    """Return resolution strategy or None if manual resolution needed."""
    state_files = ["build_state.json", "BUILD_STATE.md"]
    append_files = ["events.jsonl", "cost_tracking.csv"]
    regen_files = ["schema_columns.json", "API_SURFACE.md", "openapi.json"]

    basename = Path(file_path).name

    if basename in state_files:
        return "theirs"
    if basename in append_files:
        return "concatenate"
    if basename in regen_files:
        return "regenerate"
    return None  # Manual resolution required — abort this merge
```

---

## 19. Code Quality Rules

### File limits

| Metric | Limit | Enforcement |
|--------|-------|-------------|
| Lines per file | 300 | Gate 5 |
| Lines per function | 50 | Gate 6 |
| Cyclomatic complexity | 10 | Lint rule |
| Nesting depth | 4 | Lint rule |

### Forbidden patterns

| Pattern | Why | Gate |
|---------|-----|------|
| `import *` | Hides dependencies | Lint |
| `type: ignore` without reason | Hides type errors | Gate 10 |
| `any` (TypeScript) | Defeats type system | Gate 10 |
| `eval()`, `innerHTML` | Security | Gate 11 |
| f-string SQL | SQL injection | Gate 8 |
| Hardcoded secrets | Security | Gate 9 |
| `allow_origins = ["*"]` | Security | Gate 7 |
| `console.log` in production code | Noise | Lint |
| Commented-out code | Dead code | Lint |
| Unused imports/variables | Dead code | Lint |

### Required patterns

| Pattern | Why |
|---------|-----|
| Type hints on all functions (Python) | mypy enforcement |
| Strict TypeScript (no `any`) | Type safety |
| Parameterized queries only | SQL injection prevention |
| Schema-qualified table names | Multi-schema safety |
| Structured logging (JSON) | Parseable in production |
| Error codes (not just messages) | Machine-readable errors |

---

## 20. Testing Strategy

### Test pyramid

```
      /  E2E (Playwright)  \          <- Critical journeys only
     /  Integration (API)    \        <- Every endpoint
    /  Unit (pytest/vitest)    \      <- Every function with logic
   /  Contracts (type check)     \    <- Every cross-module boundary
  /  Static Analysis (lint/mypy)   \  <- Every file
```

### Rules

| Rule | Description |
|------|-------------|
| New function -> test first | Write the test, watch it fail, then implement |
| New endpoint -> integration test | Request -> response validation |
| New page -> E2E test | Playwright browser test |
| Bug fix -> regression test | Failing test first, then fix |
| Cross-module boundary -> contract test | Import the contract, verify shapes match |
| No "add tests later" | Gate 12 enforces test file exists for every changed module |

### Anti-silo test pattern

For every cross-module dependency, write an integration test that exercises both sides:

```python
# test_order_dashboard_integration.py
# Tests that the dashboard correctly reads from the orders module

async def test_dashboard_shows_orders():
    # Create an order via the orders API
    order = await create_order({"item": "Widget", "qty": 5})

    # Verify the dashboard API returns it
    dashboard = await get_dashboard()
    assert any(o["id"] == order["id"] for o in dashboard["recent_orders"])
```

This catches silos that unit tests miss.

---

## 21. Live API Verification

### The problem

Tests mock the server. Gates check syntax and types. But neither actually starts the server and hits endpoints with real HTTP requests. Across 6 products, 8% of atoms passed all gates but had runtime errors (missing middleware, wrong route prefix, auth not wired).

### When to run

Live API verification runs after any L3 (route) atom passes gates. It is NOT a gate (too slow for every atom) but is triggered as a post-script (step 23 in the runner loop).

### Auth flow verification

```python
import httpx
import time

def verify_auth_flow(base_url: str, config: dict) -> list[str]:
    """Verify the full auth flow: login -> JWT -> refresh -> protected route."""
    issues = []
    client = httpx.Client(base_url=base_url, timeout=10)

    # 1. Login
    resp = client.post("/api/v1/auth/login", json={
        "username": config["test_user"],
        "password": config["test_password"],
    })
    if resp.status_code != 200:
        issues.append(f"Login failed: {resp.status_code} {resp.text}")
        return issues  # Can't continue without auth

    token = resp.json().get("access_token")
    if not token:
        issues.append("Login response missing access_token field")
        return issues

    # 2. Protected route with token
    resp = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code != 200:
        issues.append(f"Protected route failed: {resp.status_code}")

    # 3. Protected route WITHOUT token
    resp = client.get("/api/v1/users/me")
    if resp.status_code not in (401, 403):
        issues.append(
            f"Unauthed request should return 401/403, got {resp.status_code}"
        )

    return issues
```

### Multi-role assertions

```python
def verify_role_access(base_url: str, config: dict) -> list[str]:
    """Verify role-based access control for each test role."""
    issues = []
    client = httpx.Client(base_url=base_url, timeout=10)

    ROLE_EXPECTATIONS = {
        "admin": {"/api/v1/admin/users": 200, "/api/v1/orders": 200},
        "viewer": {"/api/v1/admin/users": 403, "/api/v1/orders": 200},
        "vendor": {"/api/v1/admin/users": 403, "/api/v1/orders": 403},
    }

    for role, endpoints in ROLE_EXPECTATIONS.items():
        token = login_as(client, role, config)
        for endpoint, expected_status in endpoints.items():
            resp = client.get(
                endpoint,
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code != expected_status:
                issues.append(
                    f"Role {role} on {endpoint}: "
                    f"expected {expected_status}, got {resp.status_code}"
                )

    return issues
```

### Response shape verification

```python
def verify_response_shapes(base_url: str, endpoints: list[dict]) -> list[str]:
    """Verify API responses match expected shapes."""
    issues = []
    client = httpx.Client(base_url=base_url, timeout=10)

    for ep in endpoints:
        resp = client.request(
            ep["method"], ep["path"],
            json=ep.get("body"),
            headers=ep.get("headers", {}),
        )
        body = resp.json()

        for required_field in ep.get("required_fields", []):
            if required_field not in body:
                issues.append(
                    f"{ep['method']} {ep['path']}: "
                    f"missing required field '{required_field}'"
                )

    return issues
```

### Server lifecycle

```python
import subprocess
import time

def with_running_server(config: dict, check_fn):
    """Start the server, run checks, stop the server."""
    proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "18000"],
        cwd=config["backend_dir"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        # Wait for server to be ready
        for _ in range(30):
            try:
                httpx.get("http://127.0.0.1:18000/health", timeout=1)
                break
            except httpx.ConnectError:
                time.sleep(1)
        else:
            raise RuntimeError("Server did not start within 30 seconds")

        return check_fn("http://127.0.0.1:18000")
    finally:
        proc.terminate()
        proc.wait(timeout=5)
```

### Per-domain check scripts

For domain-specific verification, the runner looks for check scripts in `scripts/verify/`:

```
scripts/verify/
├── verify_auth.py        # Auth flow checks
├── verify_orders.py      # Order CRUD checks
├── verify_dashboard.py   # Dashboard data checks
└── verify_reports.py     # Report generation checks
```

Each script follows the same pattern: start server, run checks, return list of issues. The runner auto-discovers and runs scripts matching the atom's module.

---

## 22. Doc Maintenance — Mandatory

**Rule: Never commit code changes without updating corresponding docs.**

### What to update

| If you changed... | Update... |
|---|---|
| Models / migrations | `contracts/schema.json`, `SCHEMA.md` |
| Services / logic | `SYSTEM_MAP.md` |
| Routes / API | `API_SURFACE.md`, `openapi.json` |
| Background jobs | `SYSTEM_MAP.md` (jobs section) |
| Middleware / auth | `SECURITY.md` |
| Frontend routes | `ROUTES.md` |
| Dependencies | `DEPENDENCIES.md` |
| Architecture decisions | `DECISIONS.md` (append-only) |
| Conventions | `CONVENTIONS.md` |

### Layer-triggered auto-generation scripts

The runner automatically runs generation scripts after atoms in specific layers:

| Trigger | Script | Output |
|---------|--------|--------|
| Any L1 atom completes | `scripts/generate_schema_columns.py` | `contracts/schema_columns.json` |
| Any L3 atom completes | `scripts/export_openapi.py` | `openapi.json`, `API_SURFACE.md` |
| Any L4 atom completes | `scripts/verify_route_registration.py` | Warnings if routes not registered |
| Any migration atom | `scripts/generate_migration_audit.py` | `MIGRATION_AUDIT.md` |

```python
LAYER_SCRIPTS = {
    "L1": [
        ("scripts/generate_schema_columns.py", "contracts/schema_columns.json"),
    ],
    "L3": [
        ("scripts/export_openapi.py", "openapi.json"),
        ("scripts/generate_api_surface.py", "API_SURFACE.md"),
    ],
    "L4": [
        ("scripts/verify_route_registration.py", None),  # Check only, no output
    ],
}

def run_layer_scripts(layer: str, project_root: Path) -> list[str]:
    """Run auto-generation scripts for the given layer."""
    issues = []
    for script, output_file in LAYER_SCRIPTS.get(layer, []):
        script_path = project_root / script
        if not script_path.exists():
            continue
        result = subprocess.run(
            ["python3", str(script_path)],
            capture_output=True, text=True, cwd=project_root,
        )
        if result.returncode != 0:
            issues.append(f"Layer script {script} failed: {result.stderr}")
        elif output_file:
            # Stage the generated file
            subprocess.run(
                ["git", "add", output_file],
                cwd=project_root, capture_output=True,
            )
    return issues
```

### Conflict audit log

Every gate failure and fix attempt is recorded in an append-only conflict audit log. This log is never truncated — it provides a forensic record for post-build analysis.

```python
CONFLICT_LOG = "logs/conflict_audit.jsonl"

def log_conflict(project_root: Path, atom_id: str, event_type: str, details: str):
    """Append a conflict/failure event to the audit log."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "atom_id": atom_id,
        "event_type": event_type,  # "gate_fail", "fix_attempt", "regression", "merge_conflict"
        "details": details,
    }
    log_path = project_root / CONFLICT_LOG
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
```

---

## 23. Crash Recovery & Two-Level Retry

### Two retry strategies

The runner uses two levels of retry to prevent both premature failure and infinite loops:

#### Level 1: Within-atom retry

Claude produces changes but doesn't reach a committable state. The runner retries with `continue_prompt` (preserving partial work).

```
Attempt 1: fresh_prompt() -> Claude makes partial progress, session ends
Attempt 2: continue_prompt() -> Claude sees git status, continues
Attempt 3: continue_prompt() -> Final try
(exhausted) -> write handover, mark failed
```

| Attempt | Prompt type | Delay | Max turns |
|---------|-------------|-------|-----------|
| 1 | `fresh_prompt` | 0 | Effort-based (S=30, M=50, L=75) |
| 2 | `continue_prompt` | 60s | Same |
| 3 | `continue_prompt` | 120s | Same + 25 bonus |

#### Level 2: Across-atom retry

An atom fails after exhausting all within-atom retries. The runner skips it and moves to the next ready atom. But if too many atoms fail consecutively, something systemic is wrong.

```python
consecutive_fails = 0
MAX_CONSECUTIVE_FAILS = 3

while True:
    atom = get_next_ready_atom()
    if not atom:
        break

    result = build_atom(atom)

    if result == "DONE":
        consecutive_fails = 0  # Reset on success
    elif result == "FAILED":
        consecutive_fails += 1
        log.warning(
            "Atom %s failed. Consecutive failures: %d/%d",
            atom["id"], consecutive_fails, MAX_CONSECUTIVE_FAILS,
        )
        if consecutive_fails >= MAX_CONSECUTIVE_FAILS:
            log.error(
                "3 consecutive failures — systemic issue. Stopping."
            )
            break
        # Skip to next atom
        continue
    elif result == "RATE_LIMITED":
        # Don't count rate limits as failures
        time.sleep(config.retry_delay)
        continue
```

### Handover files

On crash or exhausted retries, write:

```markdown
# HANDOVER: AUTH-002

## What was attempted
Login endpoint JWT refresh

## What was done
- Created `api/v1/auth.py` with refresh route
- Tests partially written

## What failed
- mypy gate: return type mismatch on line 42
- 3 attempts, all same error
- Fix loop: 3 cycles, regression guard triggered on cycle 2

## Recovery
1. `git stash pop` to recover partial work
2. Fix the mypy error manually
3. Re-run: `python3 run.py --atom AUTH-002`
```

### Rate limiting

```python
def is_rate_limited(output: str) -> bool:
    indicators = ["rate_limit", "hit your limit", "429", "too many requests"]
    return any(i in output.lower() for i in indicators)

# If rate limited, wait and retry
if is_rate_limited(result):
    wait_time = config.retry_delays[attempt]
    log.info(f"Rate limited, waiting {wait_time}s")
    time.sleep(wait_time)
```

### Key rules

1. **Within-atom retries use `continue_prompt`, not `fresh_prompt`.** Don't throw away partial work.
2. **Across-atom failures are counted consecutively.** A success resets the counter.
3. **Rate limits don't count as failures.** The atom gets unclaimed and retried later.
4. **Max 3 consecutive across-atom failures before stopping.** This prevents the runner from burning budget on a systemic issue.

---

## 24. Parallel Execution & Worktree Isolation

### Why parallel execution

With wave planning (Section 11), atoms in the same wave have no inter-dependencies. Building them sequentially wastes time. A 4-wave build with 3 atoms per wave takes 12 atom-durations sequentially but only 4 atom-durations with 3 parallel agents.

### Architecture: wave-based parallel execution

```
Phase 1: Sequential worktree creation
  |
  v
Phase 2: Parallel Claude sessions (one per worktree)
  |
  v
Phase 3: Sequential merge + validate
```

### Worktree creation

Each parallel agent gets its own git worktree to avoid file conflicts:

```python
def create_worktree(project_root: Path, atom_id: str, session_branch: str) -> Path:
    """Create an isolated git worktree for parallel execution."""
    worktree_dir = project_root / ".worktrees" / atom_id.lower().replace("-", "_")
    branch_name = f"atom/{atom_id}"

    # Create branch from session branch
    subprocess.run(
        ["git", "branch", branch_name, session_branch],
        cwd=project_root, capture_output=True,
    )

    # Create worktree
    subprocess.run(
        ["git", "worktree", "add", str(worktree_dir), branch_name],
        cwd=project_root, capture_output=True, check=True,
    )
    return worktree_dir

def remove_worktree(project_root: Path, worktree_dir: Path):
    """Clean up a worktree after merge."""
    subprocess.run(
        ["git", "worktree", "remove", str(worktree_dir), "--force"],
        cwd=project_root, capture_output=True,
    )
```

### Parallel execution

```python
import concurrent.futures

def build_wave_parallel(
    wave: list[dict],
    config: dict,
    state: dict,
    claim_store: ClaimStore,
    max_parallel: int,
) -> list[tuple[str, str]]:
    """Build all atoms in a wave in parallel. Returns [(atom_id, result)]."""
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as pool:
        futures = {}
        for atom in wave[:max_parallel]:
            # Claim atom first (sequential, atomic)
            if not claim_store.claim(atom["id"], config["agent_id"]):
                continue

            # Create worktree (sequential)
            worktree = create_worktree(
                config["project_root"], atom["id"], config["session_branch"]
            )

            # Submit parallel build
            future = pool.submit(
                build_atom_in_worktree, atom, config, worktree
            )
            futures[future] = (atom, worktree)

        # Collect results
        for future in concurrent.futures.as_completed(futures):
            atom, worktree = futures[future]
            try:
                result = future.result()
                results.append((atom["id"], result))
            except Exception as e:
                log.error("Atom %s crashed: %s", atom["id"], e)
                results.append((atom["id"], "FAILED"))

    return results
```

### Sequential merge + validate

After all parallel atoms complete, merge them one at a time:

```python
def merge_parallel_results(
    results: list[tuple[str, str]],
    config: dict,
    project_root: Path,
    session_branch: str,
):
    """Merge completed worktree branches back to session branch."""
    subprocess.run(
        ["git", "checkout", session_branch],
        cwd=project_root, capture_output=True, check=True,
    )

    for atom_id, result in results:
        if result != "DONE":
            continue

        branch_name = f"atom/{atom_id}"
        merge_result = subprocess.run(
            ["git", "merge", branch_name, "--no-ff",
             "-m", f"Merge {atom_id} from parallel build"],
            cwd=project_root, capture_output=True, text=True,
        )

        if merge_result.returncode != 0:
            # Check if auto-resolvable
            conflicts = get_conflicted_files(project_root)
            resolvable = all(
                auto_resolve_conflict(f) is not None for f in conflicts
            )

            if resolvable:
                for f in conflicts:
                    strategy = auto_resolve_conflict(f)
                    apply_resolution(project_root, f, strategy)
                subprocess.run(
                    ["git", "add", "."],
                    cwd=project_root, capture_output=True,
                )
                subprocess.run(
                    ["git", "commit", "--no-edit"],
                    cwd=project_root, capture_output=True,
                )
            else:
                # Source code conflict — abort merge, mark atom for retry
                subprocess.run(
                    ["git", "merge", "--abort"],
                    cwd=project_root, capture_output=True,
                )
                log.error(
                    "Merge conflict in source code for %s — aborting. "
                    "Will retry sequentially.", atom_id,
                )

        # Clean up worktree
        worktree_dir = project_root / ".worktrees" / atom_id.lower().replace("-", "_")
        remove_worktree(project_root, worktree_dir)

        # Clean up branch
        subprocess.run(
            ["git", "branch", "-d", branch_name],
            cwd=project_root, capture_output=True,
        )
```

### BUILD_STATE.md conflict resolution

BUILD_STATE.md is regenerated after every merge, so its conflicts are always auto-resolved:

```python
def regenerate_build_state_md(state: dict, project_root: Path):
    """Regenerate BUILD_STATE.md from JSON state."""
    lines = ["# Build State\n"]
    modules = {}
    for atom_id, atom_state in sorted(state["atoms"].items()):
        module = atom_id.split("-")[0]
        modules.setdefault(module, []).append((atom_id, atom_state))

    for module, atoms in sorted(modules.items()):
        lines.append(f"\n## {module}\n")
        for atom_id, atom_state in atoms:
            check = "x" if atom_state["status"] == "complete" else " "
            lines.append(f"- [{check}] {atom_id}\n")

    (project_root / "BUILD_STATE.md").write_text("".join(lines))
```

### Merge conflict rules summary

| File category | Conflict resolution |
|---------------|-------------------|
| State files (`build_state.json`, `BUILD_STATE.md`) | Take theirs, then regenerate |
| Generated files (`openapi.json`, `schema_columns.json`, `API_SURFACE.md`) | Regenerate from source |
| Append-only files (`events.jsonl`, `cost_tracking.csv`, `conflict_audit.jsonl`) | Concatenate both versions |
| Source code (`.py`, `.ts`, `.tsx`) | **ABORT merge. Retry atom sequentially.** |

---

## 25. Multi-Product / Multi-Schema Builds

### When you have multiple products sharing a database

The silo problem is 10x worse when multiple products share infrastructure. Here's how to handle it:

#### Shared product registry

```yaml
# products.yaml — all products in the ecosystem
products:
  - name: product_a
    schema: product_a
    root: /opt/product_a
    port: 8000
    reads_from: [shared, product_b]
  - name: product_b
    schema: product_b
    root: /opt/product_b
    port: 8001
    reads_from: [shared, product_a]
  - name: product_c
    schema: product_c
    root: /opt/product_c
    port: 8002
    reads_from: [shared]
```

#### Cross-product validation

After any atom that changes a migration or model:

1. **Scan all other products** for files that reference the changed table
2. **Try to import** those files — do they still compile?
3. **Fire an event** so the other product's runner knows something changed
4. **Log a warning** — human review required before deploying

#### Cross-product event propagation

```python
# Product A changes the "orders" table
event_bus.publish(Event(
    type="schema.changed",
    module="orders",
    data={
        "product": "product_a",
        "table": "orders",
        "change": "added column 'priority'",
    }
))

# Product B's subscription
# (Product B reads orders via cross-schema read)
event_bus.subscribe("schema.changed", lambda e:
    revalidate_cross_schema_reads(e)
    if e.data["table"] in MY_CROSS_SCHEMA_TABLES
    else None
)
```

#### Golden rule

**If product A writes to table X, and product B reads from table X, then product A's runner must notify product B's runner when table X changes.** This notification is not optional. Without it, you have a silo.

---

## 26. Unattended & Cloud Builds

### The problem

You want to kick off a build and walk away — overnight, on a cloud VM, without monitoring. The runner must handle its own shutdown, capture final state, and optionally power off the VM.

### Auto-shutdown watcher pattern

```python
import signal
import subprocess
import sys

def run_with_auto_shutdown(runner_fn, config: dict):
    """Run the builder and shut down the VM when done."""
    shutdown_on_complete = config.get("auto_shutdown", False)

    # Capture SIGTERM for graceful shutdown
    def handle_sigterm(signum, frame):
        log.info("SIGTERM received — saving state and shutting down")
        save_final_state(config)
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)

    try:
        runner_fn(config)
    except Exception as e:
        log.error("Runner crashed: %s", e)
    finally:
        save_final_state(config)

        if shutdown_on_complete:
            log.info("Build complete — shutting down VM in 60 seconds")
            # Give time for logs to flush
            time.sleep(10)
            # Push final state to git
            subprocess.run(
                ["git", "add", "-A"],
                cwd=config["project_root"], capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", "[BUILD] Final state snapshot"],
                cwd=config["project_root"], capture_output=True,
            )
            subprocess.run(
                ["git", "push"],
                cwd=config["project_root"], capture_output=True,
            )
            # Shutdown VM
            detect_and_shutdown_vm()

def detect_and_shutdown_vm():
    """Detect cloud provider and issue shutdown command."""
    # GCP
    gcp_check = subprocess.run(
        ["curl", "-sf", "-H", "Metadata-Flavor: Google",
         "http://metadata.google.internal/computeMetadata/v1/instance/zone"],
        capture_output=True, timeout=3,
    )
    if gcp_check.returncode == 0:
        subprocess.run(["sudo", "shutdown", "-h", "+1"])
        return

    # AWS
    aws_check = subprocess.run(
        ["curl", "-sf", "http://169.254.169.254/latest/meta-data/instance-id"],
        capture_output=True, timeout=3,
    )
    if aws_check.returncode == 0:
        subprocess.run(["sudo", "shutdown", "-h", "+1"])
        return

    # Not on cloud — just exit
    log.info("Not on cloud VM — skipping shutdown")

def save_final_state(config: dict):
    """Save final build state and summary."""
    state = load_state(config["state_dir"])
    total = len(state["atoms"])
    complete = sum(1 for a in state["atoms"].values() if a["status"] == "complete")
    failed = sum(1 for a in state["atoms"].values() if a["status"] == "failed")
    blocked = sum(1 for a in state["atoms"].values() if a["status"] == "blocked")
    pending = total - complete - failed - blocked

    summary = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "total_atoms": total,
        "complete": complete,
        "failed": failed,
        "blocked": blocked,
        "pending": pending,
        "total_cost_usd": load_total_cost(config["logs_dir"]),
    }

    summary_path = config["state_dir"] / "build_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    log.info(
        "Build summary: %d/%d complete, %d failed, %d blocked, $%.2f spent",
        complete, total, failed, blocked, summary["total_cost_usd"],
    )
```

### Overnight build pattern

```bash
# Start a build that will shut down the VM when done
nohup python3 scripts/build-runner/run.py \
    --budget 200 \
    --max-atoms 100 \
    --auto-shutdown \
    > logs/overnight_build.log 2>&1 &

echo "Build started (PID: $!). VM will shut down when complete."
echo "Monitor: tail -f logs/overnight_build.log"
```

### CLI flag

```python
parser.add_argument(
    "--auto-shutdown",
    action="store_true",
    help="Shut down VM when build completes (GCP/AWS auto-detected)",
)
```

### Cloud cost savings

| Scenario | Without auto-shutdown | With auto-shutdown | Savings |
|----------|----------------------|-------------------|---------|
| 4-hour overnight build on n2-standard-4 ($0.19/hr) | Runs until morning (10hr = $1.90) | 4hr + shutdown ($0.76) | 60% |
| Weekend build on c3-standard-8 ($0.34/hr) | Runs all weekend (48hr = $16.32) | 6hr + shutdown ($2.04) | 87% |

---

## 27. Windows Adaptation

### Prerequisites

```powershell
# Install via winget
winget install Python.Python.3.12
winget install Git.Git
winget install OpenJS.NodeJS.LTS
winget install PostgreSQL.PostgreSQL.15

# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Install Python tools
pip install ruff mypy pyyaml pytest
```

### Path handling

All runner code uses `pathlib.Path`, which handles Windows paths automatically. However:

```python
# WRONG — hardcoded separator
config_path = root + "/src/backend/config.py"

# RIGHT — pathlib handles both OS
config_path = root / "src" / "backend" / "config.py"
```

### Shell command differences

| Linux | Windows | Runner strategy |
|-------|---------|-----------------|
| `curl -sf URL` | N/A | Use `urllib.request` instead |
| `pg_isready` | `pg_isready` | Same (installed with PostgreSQL) |
| `redis-cli ping` | `redis-cli ping` | Same (if Redis CLI installed) |
| `grep -r "pattern" .` | `findstr /s "pattern" *` | Use Python `re` instead |
| `wc -l file` | N/A | Use `len(file.read_text().splitlines())` |

**Strategy:** The runner uses Python stdlib for everything except external tool invocations (ruff, mypy, pytest, eslint). Those tools are cross-platform.

### Line endings

Add `.gitattributes`:

```
*.py text eol=lf
*.ts text eol=lf
*.tsx text eol=lf
*.json text eol=lf
*.md text eol=lf
```

### Docker Desktop

If using Docker, everything is identical on both platforms. Docker abstracts the OS.

### Entry script

Create `run.bat`:
```batch
@echo off
python "%~dp0run.py" %*
```

Or `run.ps1`:
```powershell
python "$PSScriptRoot\run.py" @args
```

### Windows checklist

- [ ] Python 3.12+ installed and in PATH
- [ ] Git installed and in PATH
- [ ] Node.js 18+ installed and in PATH
- [ ] Claude Code installed: `npm install -g @anthropic-ai/claude-code`
- [ ] Claude authenticated: `claude auth`
- [ ] PostgreSQL installed (or Docker Desktop)
- [ ] Python tools: `pip install ruff mypy pyyaml pytest`
- [ ] `.gitattributes` added with LF line endings
- [ ] `product.yaml` filled in with Windows paths
- [ ] Run `python run.py --health` — all checks pass

---

## 28. Runner Implementation (Python)

### File structure

```
scripts/build-runner/
├── run.py              # CLI entry point (< 200 lines)
├── lib/
│   ├── __init__.py
│   ├── config.py       # Product config loader (< 150 lines)
│   ├── state.py        # Build state manager (< 150 lines)
│   ├── claims.py       # SQLite claim store (< 150 lines)
│   ├── gates.py        # Code quality gates (< 300 lines)
│   ├── gates_security.py  # Security-specific gates (< 150 lines)
│   ├── gates_frontend.py  # Frontend gates: eslint, vitest (< 100 lines)
│   ├── fix_loop.py     # Self-healing fix loop (< 150 lines)
│   ├── events.py       # Event bus (< 120 lines)
│   ├── deps.py         # Dependency graph + topo sort + wave plan (< 200 lines)
│   ├── executor.py     # Claude invocation + gate pipeline (< 200 lines)
│   ├── health.py       # Preflight checks (< 200 lines)
│   ├── cost.py         # Cost tracking + token extraction (< 150 lines)
│   ├── cross_check.py  # Cross-module validator (< 150 lines)
│   ├── context.py      # Context loading table (< 100 lines)
│   ├── prompts.py      # fresh/continue/fix prompts (< 150 lines)
│   ├── errors.py       # Error categorization + recovery (< 150 lines)
│   ├── verify.py       # Live API verification (< 200 lines)
│   ├── parallel.py     # Worktree isolation + parallel build (< 200 lines)
│   ├── shutdown.py     # Unattended build + auto-shutdown (< 100 lines)
│   └── conflict_log.py # Conflict audit logger (< 50 lines)
├── tests/
│   ├── test_gates.py
│   ├── test_state.py
│   ├── test_claims.py
│   ├── test_events.py
│   ├── test_deps.py
│   ├── test_cross_check.py
│   ├── test_cost.py
│   ├── test_health.py
│   ├── test_fix_loop.py
│   ├── test_context.py
│   ├── test_prompts.py
│   ├── test_errors.py
│   └── test_parallel.py
├── logs/               # Execution logs (gitignored)
├── events/             # Event JSONL (gitignored)
├── state/              # State JSON + SQLite claims (gitignored)
└── handover/           # Crash recovery files (gitignored)
```

### Key design rules for the runner code itself

1. **Every file <= 300 lines** — the runner enforces this on the product code; it must also follow it
2. **Every function <= 50 lines** — same
3. **No hardcoded product names** — everything comes from `product.yaml`
4. **No hardcoded paths** — everything relative to project root
5. **Cross-platform** — use `pathlib.Path`, `subprocess.run`, Python stdlib
6. **Crash-safe** — state saved to disk after every atom
7. **Resumable** — on restart, reads state from disk and continues where it left off
8. **Budget-aware** — stops before exceeding configured budget
9. **Event-driven** — publishes events for every significant action
10. **Testable** — every module has unit tests with temp dirs (no real filesystem)

### Skeleton: run.py

```python
#!/usr/bin/env python3
"""Build runner — orchestrates atom-based development with Claude Code."""
import argparse
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import load_config
from lib.state import BuildState
from lib.claims import ClaimStore
from lib.events import EventBus
from lib.deps import find_ready_atoms, compute_waves
from lib.executor import build_atom
from lib.health import run_preflight, startup_cleanup
from lib.cost import CostTracker
from lib.errors import categorize_result, handle_failure
from lib.context import detect_atom_type, load_context
from lib.prompts import select_prompt
from lib.shutdown import run_with_auto_shutdown

log = logging.getLogger("build-runner")

def main():
    # Block nested sessions
    if os.environ.get("CLAUDECODE"):
        print("ERROR: Cannot run inside a Claude session. "
              "Unset CLAUDECODE and retry.")
        sys.exit(1)

    args = parse_args()
    config = load_config(args.config or "product.yaml")
    setup_logging(config)

    if args.health:
        results = run_preflight(config)
        print_health(results)
        sys.exit(1 if any(not r.passed for r in results) else 0)

    if args.status:
        show_status(config)
        return

    if args.dry_run:
        show_wave_plan(config)
        return

    if args.auto_shutdown:
        run_with_auto_shutdown(lambda c: run_build(c, args), config)
    else:
        run_build(config, args)

def run_build(config, args):
    state = BuildState(config.state_dir)
    claim_store = ClaimStore(config.state_dir / "claims.db")
    events = EventBus(config.events_dir / "events.jsonl")
    costs = CostTracker(config.logs_dir)

    # Step 1: Startup cleanup
    startup_cleanup(claim_store, config.project_root)

    events.publish_build_started(config)

    atoms_done = 0
    consecutive_fails = 0

    while True:
        if not costs.within_budget(config.budget):
            log.warning("Budget exceeded: $%.2f", costs.total())
            break

        ready = find_ready_atoms(state, config.atoms_dir)
        if not ready:
            log.info("No atoms ready. Build complete or blocked.")
            break

        if args.max_atoms and atoms_done >= args.max_atoms:
            break

        atom = ready[0]  # Topological order — first is highest priority

        # Step 8: Claim
        if not claim_store.claim(atom.id, config.agent_id):
            continue  # Already claimed by another agent

        # Steps 9-14: Build
        result = build_atom(atom, config, state, events, costs, claim_store)

        # Steps 15-26: Handle result
        if result == "DONE":
            atoms_done += 1
            consecutive_fails = 0
        elif result == "RATE_LIMITED":
            time.sleep(config.retry_delays[-1])
        elif result == "FAILED":
            consecutive_fails += 1
            if consecutive_fails >= 3:
                log.error("3 consecutive failures — stopping")
                break
        elif result == "STOP":
            break

    claim_store.close()
    events.publish_build_finished(atoms_done, costs.total())
    log.info("Done. %d atoms built. Cost: $%.2f", atoms_done, costs.total())
```

### Skeleton: lib/cross_check.py

**This is the anti-silo module.** It runs after every atom.

```python
"""Cross-module validation — the anti-silo check."""
import re
import subprocess
from pathlib import Path

def cross_module_check(
    project_root: Path,
    changed_files: list[str],
    config: dict,
) -> list[str]:
    """Return list of cross-module issues found."""
    issues = []

    # 1. Schema/model changes -> check all importers
    model_files = [f for f in changed_files if "models/" in f and f.endswith(".py")]
    for mf in model_files:
        module = _module_from_path(mf)
        importers = _find_importers(project_root, module)
        for imp in importers:
            if imp in changed_files:
                continue  # Same atom — already handled
            if not _try_compile(project_root / imp):
                issues.append(
                    f"BREAK: {mf} changed -> {imp} no longer compiles"
                )

    # 2. API route changes -> check frontend consumers
    route_files = [f for f in changed_files if "api/" in f and f.endswith(".py")]
    for rf in route_files:
        endpoints = _extract_endpoints(project_root / rf)
        for ep in endpoints:
            consumers = _grep(project_root, ep, "src/frontend/")
            for c in consumers:
                issues.append(
                    f"API: {ep} changed in {rf} -> consumed by {c}"
                )

    # 3. Contract file changes -> check importers
    contract_files = [f for f in changed_files if "contracts/" in f]
    for cf in contract_files:
        importers = _find_importers(project_root, _module_from_path(cf))
        for imp in importers:
            if not _try_compile(project_root / imp):
                issues.append(
                    f"CONTRACT: {cf} changed -> {imp} no longer compiles"
                )

    return issues
```

---

## 29. Unit Test Plan

### Required tests per module

| Module | Tests | What's tested |
|--------|-------|---------------|
| `test_gates.py` | 24+ | Every gate (21): pass case, fail case, edge case (no files, wrong extension) |
| `test_state.py` | 12+ | CRUD, mark complete/failed, dependency resolution, persistence, import from BUILD_STATE.md |
| `test_claims.py` | 10+ | Claim, unclaim, stale release, concurrent claim attempt, is_claimed |
| `test_events.py` | 10+ | Publish, subscribe, filtering, persistence (JSONL), replay, error handling |
| `test_deps.py` | 10+ | Topological sort, cycle detection, ready atom finding, wave computation, cross-module deps |
| `test_cross_check.py` | 8+ | Schema change detection, API change detection, contract break detection |
| `test_cost.py` | 8+ | Token extraction, cost computation, budget enforcement, persistence, restart |
| `test_health.py` | 11+ | Disk space, DB check, CLAUDECODE check, checksum, reconciliation, format report |
| `test_fix_loop.py` | 8+ | Fix succeeds, regression guard triggers, max cycles exhausted |
| `test_context.py` | 6+ | Atom type detection, context loading per type |
| `test_prompts.py` | 6+ | fresh_prompt, continue_prompt, fix_prompt, selection logic |
| `test_errors.py` | 9+ | Each of 9 failure modes detected correctly, recovery dispatch |
| `test_parallel.py` | 6+ | Worktree creation/removal, merge conflict resolution, wave execution |

### Test patterns

```python
# Every test uses temp directories — no real filesystem
@pytest.fixture
def tmp_project(tmp_path):
    (tmp_path / "src/backend/app/models").mkdir(parents=True)
    (tmp_path / "src/frontend/src").mkdir(parents=True)
    return tmp_path

# Every gate has a pass test and a fail test
class TestFileSizeGate:
    def test_passes_under_limit(self, tmp_project):
        (tmp_project / "app.py").write_text("x = 1\n" * 100)
        result = FileSizeGate().check(tmp_project, ["app.py"])
        assert result.passed

    def test_fails_over_limit(self, tmp_project):
        (tmp_project / "app.py").write_text("x = 1\n" * 350)
        result = FileSizeGate().check(tmp_project, ["app.py"])
        assert not result.passed
        assert "350" in result.output

# Fix loop tests
class TestFixLoop:
    def test_fix_succeeds_on_first_cycle(self, tmp_project, mock_claude):
        mock_claude.set_response("fixed the lint error")
        result = fix_loop(atom, config, gates=[failing_lint_gate])
        assert result == "FIXED"

    def test_regression_guard_reverts(self, tmp_project, mock_claude):
        # Fix breaks a passing test
        mock_claude.set_response("fixed lint but broke tests")
        result = fix_loop(atom, config, gates=[failing_lint_gate])
        # Verify git checkout was called (revert)
        assert mock_claude.git_checkout_called

# Error categorization tests
class TestErrorCategorization:
    @pytest.mark.parametrize("output,expected", [
        ("rate_limit exceeded", "rate_limit"),
        ("HTTP 429 Too Many Requests", "rate_limit"),
        ("context window exceeded", "context_overflow"),
        ("CLAUDECODE is set", "nested_session"),
    ])
    def test_categorizes_correctly(self, output, expected):
        result = categorize_result(exit_code=1, stdout=output, stderr="", timed_out=False)
        assert result == expected
```

---

## 30. E2E Test Plan

### Scenarios

| Scenario | Steps | Expected |
|----------|-------|----------|
| **Single atom build** | `run.py --atom AUTH-001` | Atom completes, state updated, event published, cost recorded |
| **Dependency ordering** | Create A->B dependency, run | B builds only after A completes |
| **Gate failure + fix loop** | Create atom that violates file_size gate | Fix loop runs, either fixes or writes handover after 3 cycles |
| **Budget exceeded** | Set `--budget 0.001`, run | Stops immediately with budget warning |
| **Cross-module break** | Change a model, run dependent atom | Warning about cross-module impact |
| **Dry run wave plan** | `run.py --dry-run` | Shows numbered waves with parallelizable atoms |
| **Health check** | `run.py --health` | Reports pass/fail for each check (including CLAUDECODE) |
| **Crash recovery** | Kill mid-atom, restart | Releases stale claim, resumes from state file |
| **Rate limiting** | Simulate rate limit | Unclaims atom, waits, retries |
| **Parallel build** | `run.py --parallel 2` | Two atoms build simultaneously in worktrees, merge sequentially |
| **Consecutive failures** | 3 atoms fail in a row | Runner stops with "systemic issue" message |
| **Context loading** | Build backend atom, then frontend atom | Backend loads SYSTEM_MAP.md, frontend loads DESIGN_SYSTEM.md |
| **Deliverable verification** | Claude claims files exist but doesn't create them | Gate 21 catches and fails |
| **Nested session block** | Set CLAUDECODE env var, run | Runner refuses to start |
| **Auto-shutdown** | `run.py --auto-shutdown` on GCP VM | Build completes, state pushed, VM shuts down |

---

## 31. Conventions

### Naming

| Thing | Convention | Example |
|-------|-----------|---------|
| Python files | `snake_case.py` | `order_service.py` |
| Python classes | `PascalCase` | `OrderService` |
| Python functions | `snake_case` | `create_order()` |
| TypeScript files | `PascalCase.tsx` (components), `camelCase.ts` (utils) | `OrderList.tsx`, `orderApi.ts` |
| Database tables | `snake_case`, plural | `orders`, `order_items` |
| API endpoints | `/api/v1/{resource}`, plural | `/api/v1/orders` |
| Atom IDs | `{MODULE}-{NNN}` | `AUTH-001` |
| Branches | `atom/{ATOM_ID}` | `atom/AUTH-001` |
| Commits | `[ATOM_ID] description` | `[AUTH-001] Add login endpoint` |

### Error handling

```python
# At system boundaries (user input, external APIs): validate everything
@router.post("/orders")
async def create_order(req: OrderCreate):  # Pydantic validates input
    ...

# Internal code: trust your types, don't re-validate
def calculate_total(items: list[OrderItem]) -> Decimal:
    return sum(item.price * item.quantity for item in items)
    # No: if not items: raise ValueError("empty") — let the caller handle that
```

### Logging

```python
# Structured, with context
log.info("Order created", extra={"order_id": order.id, "user_id": user.id})

# NOT: log.info(f"Order {order.id} created by {user.id}")
# NOT: print(f"order created")
```

---

## 32. Decisions Log Template

Keep this file in your project as `DECISIONS.md`. Append-only — never rewrite history.

```markdown
# Decisions

| Date | Decision | Rationale | Alternatives Considered |
|------|----------|-----------|------------------------|
| 2026-06-01 | Use PostgreSQL 15, not MySQL | JSONB support, schema-qualified tables, cross-product reads | MySQL 8 (no schema support), SQLite (no concurrency) |
| 2026-06-01 | Use event bus for cross-module communication | Prevents silos, crash-recoverable via JSONL | Direct function calls (tight coupling), message queue (overkill for single-VM) |
| 2026-06-01 | Atom-based development with topological sort | Bounded scope per build step, dependency-aware ordering | Sprint-based (too large), PR-based (no dependency tracking) |
| 2026-06-01 | SQLite for claim system, not file locks | Atomic operations, WAL mode for concurrent reads, survives crashes | File locks (not atomic), Redis (extra dependency) |
| 2026-06-01 | Three prompt types (fresh/continue/fix) | 40-60% token savings, faster fix cycles | Single prompt (wasteful), two types (fix cycle too slow) |
| ... | ... | ... | ... |
```

---

## 33. Troubleshooting

### Runner issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| "No atoms ready" but atoms are pending | Unmet dependency | Check `--status`, find blocking atom |
| Gate keeps failing on same error | Atom spec is ambiguous | Read the handover file, add more detail to atom spec |
| Budget exceeded after 3 atoms | Model too expensive for small atoms | Use `--model sonnet` for small atoms, or add `Effort: S` to atom spec |
| Atom produces no changes | Prompt too vague | Add explicit file list to atom spec Outputs section |
| Cross-module check warns but code works | False positive — file references a string, not an import | Add to ignore list or make gate soft |
| Rate limited every 5 minutes | Too many sequential invocations | Increase retry delay, reduce `--max-atoms` |
| Tests fail in CI but pass locally | Missing test fixtures or env vars | Check CI environment matches local |
| "Cannot run inside a Claude session" | CLAUDECODE env var set | Run from a plain terminal: `unset CLAUDECODE && python3 run.py` |
| "Nested session" errors from Claude | Runner invoked from within Claude Code | Same fix as above — unset CLAUDECODE |
| Fix loop always hits regression guard | Fixes are too broad — changing unrelated code | Improve fix_prompt to be more targeted |
| Stale claims after crash | Runner crashed without cleanup | Restart — startup cleanup auto-releases stale claims |
| Merge conflict on source code | Parallel agents edited same file | Runner aborts merge; retry atom sequentially |
| Deliverable verification fails | Claude claimed to create files but didn't | Re-run atom with more explicit Outputs section |

### Silo detection

Run these checks periodically:

```bash
# Find modules with no cross-module tests
find tests/ -name "test_*integration*" | wc -l
# Should be > 0 for every pair of dependent modules

# Find imports between modules (should use contracts, not direct imports)
grep -r "from app.services.orders" app/services/dashboard/
# If this returns results, it's a tight coupling — should import from contracts/

# Find tables referenced without schema qualification
grep -rn "__tablename__" app/models/ | grep -v "schema"
# Every result is a potential silo hazard
```

---

## 34. Checklist — Before First Build

### Infrastructure

- [ ] Database running and accessible
- [ ] Schemas created
- [ ] Cache (Redis) running
- [ ] Storage (MinIO/S3) running — if needed
- [ ] `python run.py --health` all green

### Project setup

- [ ] `product.yaml` filled in completely
- [ ] `CLAUDE.md` created with product context
- [ ] `CONVENTIONS.md` created
- [ ] `DECISIONS.md` created (at least initial decisions)
- [ ] `DEPENDENCY_MAP.md` created (even if empty — it's always loaded)
- [ ] `.gitattributes` added (LF line endings)
- [ ] `.gitignore` includes: `logs/`, `events/`, `state/`, `handover/`, `.env`, `__pycache__/`, `.worktrees/`

### Atom specs

- [ ] All atoms created in `atoms/` directory
- [ ] Every atom has: Layer, Module, Effort, Depends on, Inputs, Outputs, Acceptance criteria
- [ ] Every atom's Outputs section lists cross-module contracts
- [ ] `BUILD_STATE.md` created with all atoms listed as `- [ ]`
- [ ] Dependency graph has no cycles (`run.py --check-deps`)

### Runner

- [ ] `scripts/build-runner/` directory created
- [ ] `run.py` and `lib/` copied from Section 28
- [ ] `run.py --dry-run` shows correct wave plan
- [ ] `run.py --status` shows all atoms as pending

### Validation

- [ ] Python tools installed: `ruff`, `mypy`, `pytest`
- [ ] Node tools installed (if frontend): `eslint`, `vitest`, `prettier`
- [ ] Claude Code installed and authenticated
- [ ] CLAUDECODE env var is NOT set (run from plain terminal)
- [ ] Git repo initialized with initial commit

### Parallel execution (if using --parallel)

- [ ] SQLite available (Python stdlib, no extra install)
- [ ] Enough disk space for worktrees (each is a full checkout)
- [ ] `git worktree list` shows only the main worktree

---

## Appendix A: Lessons Learned From 6 Production Systems

These are not theoretical concerns. Each lesson was learned by shipping a product and discovering the problem in production or during integration.

### Lesson 1: Schema-qualified tables are mandatory

**What happened:** Two products shared a PostgreSQL database. Both had a `users` table. Unqualified queries returned rows from the wrong product.

**Rule:** Every model declares `__table_args__ = {"schema": "your_schema"}`. Every query uses schema-qualified names.

### Lesson 2: Cross-schema reads must be read-only

**What happened:** Product A read from product B's tables for reporting. A developer accidentally added a write path. Product B's data got corrupted.

**Rule:** Cross-product reads go through a dedicated `cross_schema/` directory. Models in that directory are read-only — no INSERT/UPDATE/DELETE.

### Lesson 3: Validation gates must be hard, not advisory

**What happened:** Gates were set to "warn" during development to move faster. Three months later, 200 gate violations had accumulated. Nobody fixed them because they were "just warnings."

**Rule:** Gates are hard (block commit) from day 1. If a gate is wrong, fix the gate — don't make it soft.

### Lesson 4: Cost tracking prevents budget surprises

**What happened:** A build session ran overnight without budget controls. $400 in Claude API costs.

**Rule:** Budget cap with per-atom tracking. Runner stops when budget is exceeded.

### Lesson 5: Crash recovery is not optional

**What happened:** A build session crashed mid-atom. On restart, the runner re-built the atom from scratch — duplicating 30 minutes of work and creating merge conflicts.

**Rule:** State saved to disk after every atom. Handover files on crash. Runner resumes from last known state.

### Lesson 6: Doc maintenance must be enforced, not requested

**What happened:** Documentation was "important" but not enforced. After 200 atoms, docs were 6 months out of date. New team members got wrong information.

**Rule:** Section 22 — mandatory doc updates after every code change. The runner checks.

### Lesson 7: The event bus would have prevented 3 production incidents

**What happened (3 separate incidents):**
1. Product A renamed a column. Product B's cross-schema read crashed.
2. Product A changed an API response shape. Product B's frontend showed blank data.
3. A migration in Product A locked a shared table for 20 minutes. Products B and C timed out.

**Rule:** Event bus notifies all products when something changes. Cross-module validation catches breaking changes before they deploy.

### Lesson 8: Parallel runners need worktree isolation

**What happened:** Two parallel agents edited the same file. Git merge conflict. Both agents' work was lost.

**Rule:** Each parallel agent gets its own git worktree. Changes are merged back one at a time.

### Lesson 9: Model selection matters more than you think

**What happened:** Small atoms (add one field) were built with Opus ($0.50/atom). Could have used Sonnet ($0.05/atom). Over 200 small atoms, that's $90 wasted.

**Rule:** Effort-based model selection. Small atoms use Sonnet. Complex atoms use Opus.

### Lesson 10: Test-before-implement is the only pattern that works at scale

**What happened:** 400 atoms built test-after-implement. 30% of tests were written to pass the existing (buggy) code, not to verify correct behavior.

**Rule:** Write the test first. Watch it fail. Then implement. The failing test is the spec.

### Lesson 11: Fix loops save 60% of manual intervention

**What happened:** Across 3 products, 60% of gate failures were simple lint/type/format errors that Claude could fix when shown the error output. Humans were manually re-running builds for trivially fixable issues.

**Rule:** Self-healing fix loop (Section 8). Re-invoke Claude with just the gate output. 3 cycles max. Regression guard prevents cascading breakage.

### Lesson 12: Context loading tables cut token costs by 40-60%

**What happened:** Every atom loaded the full project context (8-12 docs, ~45K tokens). Frontend atoms don't need SCHEMA.md. Infra atoms don't need DESIGN_SYSTEM.md. 40-60% of tokens were wasted on irrelevant context.

**Rule:** Context loading table (Section 13). Map atom type to docs. Only load what's relevant. DEPENDENCY_MAP.md is always loaded regardless.

### Lesson 13: Deliverable verification catches phantom files

**What happened:** 5% of atoms across 3 products had Claude claiming "Created `api/v1/orders.py`" in its output but the file didn't actually exist on disk. The atom was marked complete. The dependent atom failed with an import error.

**Rule:** Gate 21 (deliverable_verification). Check that every file listed in atom Outputs actually exists on disk. Trust but verify.

### Lesson 14: Two-level retry prevents infinite loops on stuck atoms

**What happened:** A stuck atom kept retrying indefinitely. The runner burned $40 on a single atom before a human noticed.

**Rule:** Two-level retry (Section 23). Within-atom: 3 attempts with continue_prompt. Across-atom: skip and move on. Stop after 3 consecutive failures.

### Lesson 15: Claim systems are mandatory for parallel agents

**What happened:** Two parallel agents picked up the same atom. Both built it. Both committed. Merge conflict. Both agents' work was partially lost.

**Rule:** SQLite-backed atomic claim system (Section 12). Claim before building. Only the owning agent can update status. Release stale claims on startup.

### Lesson 16: Nested session blocking prevents cryptic failures

**What happened:** The runner was invoked from inside a Claude session (via a tool call). Claude Code sets a `CLAUDECODE` env var. The inner Claude session failed with cryptic "already running" errors. 30 minutes of debugging.

**Rule:** Preflight check: verify `CLAUDECODE` env var is NOT set. If set, refuse to start with a clear error message.

### Lesson 17: Auto-shutdown saves cloud costs on overnight builds

**What happened:** An overnight build completed at 2 AM. The cloud VM ran until 9 AM when someone noticed. 7 hours of idle compute billed.

**Rule:** `--auto-shutdown` flag (Section 26). Detect cloud provider, push final state, shut down VM. Saves 60-87% on cloud costs for overnight builds.

---

## Appendix B: Quick Reference Card

```
BUILD:
  python3 run.py                      # Build next ready atom
  python3 run.py --atom AUTH-001      # Build specific atom
  python3 run.py --module auth        # Build all atoms in module
  python3 run.py --dry-run            # Show wave plan
  python3 run.py --max-atoms 5        # Limit atoms per session
  python3 run.py --parallel 2         # Parallel agents (worktree-isolated)

CHECK:
  python3 run.py --health             # Infrastructure health
  python3 run.py --status             # Build progress
  python3 run.py --check-deps         # Dependency graph

CONFIGURE:
  python3 run.py --budget 100         # Budget cap (USD)
  python3 run.py --model opus         # Model override
  python3 run.py --timeout 1800       # Per-atom timeout (seconds)
  python3 run.py --auto-shutdown      # Shut down VM when done

FILES:
  product.yaml                        # Product definition
  BUILD_STATE.md                      # Human-readable progress (generated)
  atoms/{module}/{ATOM_ID}.md         # Atom specifications
  state/build_state.json              # Machine state (gitignored)
  state/claims.db                     # SQLite claim store (gitignored)
  events/events.jsonl                 # Event log (gitignored)
  logs/cost_tracking.csv              # Cost ledger (gitignored)
  logs/conflict_audit.jsonl           # Conflict audit log (gitignored)
  handover/HANDOVER_{ATOM_ID}.md      # Crash recovery

GATES (21):
  1. syntax_check     8. no_sql_injection  15. contract_check
  2. lint             9. no_secrets        16. cross_module
  3. format          10. no_unsafe_types   17. eslint
  4. type_check      11. no_dangerous      18. vitest
  5. file_size       12. tests_exist       19. import_sanity
  6. function_size   13. tests_pass        20. dep_map_freshness
  7. no_wildcard_cors 14. migration_ok     21. deliverable_verify

EFFORT LEVELS:
  S (Small):  30 turns, Sonnet, $0.30-$0.80/atom
  M (Medium): 50 turns, Opus,   $1.00-$3.00/atom
  L (Large):  75 turns, Opus,   $2.00-$5.00/atom

FAILURE MODES (9):
  timeout | rate_limit | auth_error | context_overflow | max_turns
  nested_session | session_fail | gate_fail | success

PROMPT TYPES (3):
  fresh_prompt()    — first invocation, full context
  continue_prompt() — retry with partial work, includes git status
  fix_prompt()      — gate failed, minimal context, just errors
```

---

## Appendix C: Domain-Specific Gate Extension

### The problem

The base 21 gates cover universal code quality. But specific products have domain-specific requirements:
- Multi-tenant SaaS: every query must filter by `tenant_id`
- AI products: LLM outputs must include evidence scoring
- Microservices: no cross-service direct imports (only via API)
- Regulated industries: audit logging on every mutation

### Gate registry extension via product.yaml

Declare custom gates in `product.yaml`. They're loaded at startup and added to the base 21.

```yaml
# product.yaml
custom_gates:
  - name: "tenant_isolation"
    severity: "hard"
    check_command: "python3 scripts/gates/check_tenant_isolation.py"
    description: "Every DB query must filter by tenant_id"
    skip_for: ["infra", "auth"]

  - name: "rls_on_tenant_tables"
    severity: "hard"
    check_command: "python3 scripts/gates/check_rls.py"
    description: "Row-level security enabled on all tenant-scoped tables"
    skip_for: ["frontend"]

  - name: "evidence_scoring"
    severity: "hard"
    check_command: "python3 scripts/gates/check_evidence_scoring.py"
    description: "AI outputs include confidence score and source citations"
    skip_for: ["infra", "auth", "frontend"]

  - name: "cross_service_import_ban"
    severity: "hard"
    check_command: "python3 scripts/gates/check_cross_service_imports.py"
    description: "No direct imports between service boundaries"
    skip_for: []
```

### Custom gate implementation pattern

Custom gates follow the same interface as base gates but are implemented as standalone scripts:

```python
#!/usr/bin/env python3
"""scripts/gates/check_tenant_isolation.py
Custom gate: verify all queries filter by tenant_id.
Exit 0 = pass, exit 1 = fail. Stdout = details."""

import sys
import re
from pathlib import Path

def check_tenant_isolation(changed_files: list[str]) -> list[str]:
    issues = []
    for f in changed_files:
        if not f.endswith(".py"):
            continue
        path = Path(f)
        if not path.exists():
            continue
        content = path.read_text()

        # Check for queries on tenant-scoped tables without tenant_id filter
        if "select(" in content.lower() or ".query(" in content.lower():
            if "tenant_id" not in content:
                issues.append(
                    f"{f}: Query found without tenant_id filter"
                )

    return issues

if __name__ == "__main__":
    # Changed files passed as args
    files = sys.argv[1:]
    issues = check_tenant_isolation(files)
    if issues:
        print("\n".join(issues))
        sys.exit(1)
    sys.exit(0)
```

### Loading custom gates at runtime

```python
def load_custom_gates(config: dict) -> list[Gate]:
    """Load custom gates from product.yaml at startup."""
    custom_gates = []
    for gate_def in config.get("custom_gates", []):
        gate = ExternalGate(
            name=gate_def["name"],
            severity=gate_def["severity"],
            command=gate_def["check_command"],
            skip_for=gate_def.get("skip_for", []),
            description=gate_def.get("description", ""),
        )
        custom_gates.append(gate)
    return custom_gates

class ExternalGate(Gate):
    """Gate backed by an external script."""

    def __init__(self, name, severity, command, skip_for, description):
        self.name = name
        self.severity = severity
        self._command = command
        self._skip_for = skip_for
        self.description = description

    def check(self, project_root, changed_files, atom_type=None):
        # Skip if atom type is in skip list
        if atom_type and atom_type in self._skip_for:
            return GateResult(self.name, passed=True, output="Skipped for atom type")

        result = subprocess.run(
            self._command.split() + changed_files,
            capture_output=True, text=True, cwd=project_root,
        )
        return GateResult(
            self.name,
            passed=result.returncode == 0,
            output=result.stdout + result.stderr,
            severity=self.severity,
        )
```

### Combined gate execution

```python
def run_all_gates(
    config: dict,
    changed_files: list[str],
    atom_type: str,
) -> list[GateResult]:
    """Run base gates + custom gates."""
    base_gates = get_base_gates()  # 21 base gates
    custom_gates = load_custom_gates(config)
    all_gates = base_gates + custom_gates

    results = []
    for gate in all_gates:
        result = gate.check(
            config["project_root"], changed_files, atom_type=atom_type
        )
        results.append(result)
        if not result.passed and result.severity == "hard":
            log.warning("Gate FAILED: %s — %s", gate.name, result.output[:200])
    return results
```

### Example: complete custom gate registry for a multi-tenant AI product

```yaml
custom_gates:
  # Multi-tenancy
  - name: "tenant_isolation"
    severity: "hard"
    check_command: "python3 scripts/gates/check_tenant_isolation.py"
    description: "Every DB query on tenant tables must include tenant_id filter"
    skip_for: ["infra"]

  - name: "rls_policies"
    severity: "hard"
    check_command: "python3 scripts/gates/check_rls.py"
    description: "Row-level security policies exist for all tenant-scoped tables"
    skip_for: ["frontend", "ai"]

  # AI quality
  - name: "evidence_scoring"
    severity: "hard"
    check_command: "python3 scripts/gates/check_evidence.py"
    description: "AI response schemas include confidence_score and sources fields"
    skip_for: ["infra", "auth", "frontend"]

  - name: "llm_output_sanitization"
    severity: "hard"
    check_command: "python3 scripts/gates/check_llm_sanitize.py"
    description: "LLM outputs are sanitized before display (no raw HTML/script)"
    skip_for: ["infra", "auth", "backend"]

  # Service boundaries
  - name: "cross_service_import_ban"
    severity: "hard"
    check_command: "python3 scripts/gates/check_service_boundaries.py"
    description: "Services communicate via API/events only, no direct imports"
    skip_for: []
```
