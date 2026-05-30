# Build System Improvements

## Summary of Fixes

### 1. ✅ Fixed build.bat Prerequisites Checking

**Problem:** build.bat only checked for Python and Claude CLI, but didn't check for required Python dependencies (pyyaml).

**Solution:**
- Added automatic PyYAML dependency check in build.bat
- Added automatic `pip install pyyaml` when missing
- Creates required directories (state/, logs/, data/) automatically
- Runs full health checks before starting build

**Before:**
```batch
REM Only checked Python and Claude CLI
python --version
claude --version
```

**After:**
```batch
REM Checks Python, Claude CLI, PyYAML, creates directories
python -c "import yaml"  (installs pyyaml if missing)
mkdir state logs data
python scripts\build-runner\run.py --health
```

---

### 2. ✅ Added Setup Guidance

**Problem:** New users didn't know to run setup-windows.bat first.

**Solution:**
- Updated build.bat to guide users with clear error messages
- Added references to setup-windows.bat and Python download links
- Improved console output with section headers

**Output messages:**
```
ERROR: Claude CLI not found.
Install with: npm install -g @anthropic-ai/claude-code
```

---

### 3. ✅ Added Full Health Checks Before Building

**Problem:** build.bat didn't verify database, cache, storage, disk space, git status.

**Solution:**
- Now runs `python run.py --health` before starting full build
- Health checks verify:
  - Database connectivity (PostgreSQL/MySQL)
  - Cache (Redis) connectivity
  - Storage (MinIO/S3) connectivity
  - Disk space (minimum 3GB)
  - Python/Node versions
  - Git repository clean
  - Claude CLI authenticated

**Command:**
```bash
build.bat --health   # Check infrastructure
```

---

## New Feature: Dependency & Function Mapping System

### What It Does

Every time an atom completes, the runner extracts and records all functions, classes, constants, and types it exports. This creates a tree map that shows:

1. **What each atom produces** (functions, classes, variables)
2. **Where it's exported from** (file paths, line numbers)
3. **How to use it** (signatures, parameters, documentation)

Subsequent atoms can then reference this tree to see what's available, preventing assumptions about non-existent functionality.

---

### File Structure

**New files:**
- `scripts/build-runner/lib/exports.py` — Export extraction and mapping
- `EXPORTS.md` — Auto-generated tree of available exports
- `scripts/build-runner/data/exports.json` — Machine-readable export data

**Updated files:**
- `scripts/build-runner/run.py` — Added `--exports` command
- `build.bat` — Improved prerequisites and health checking

---

### How to Use

#### View Available Exports
```bash
# Show all functions/classes from completed atoms
build.bat --exports

# Or directly
python scripts\build-runner\run.py --exports
```

#### Example Output
```
================================================================================
AVAILABLE EXPORTS — Functions, Classes, Variables
================================================================================

📦 AUTH (Authentication, JWT, Rate Limiting)
----------------------------------------
  [AUTH-001] Layer L1
    🔷 class User
       └─ Represents a user account with credentials
    ⚙️  def create_user(username: str, password: str) -> User
       └─ Creates a new user account
    📌 JWT_ALGORITHM
       └─ Algorithm used for JWT signing
  [AUTH-002] Layer L2
    ⚙️  def login(username: str, password: str) -> str
       └─ Returns JWT token on successful login

📦 CORE (Database, Models)
----------------------------------------
  [CORE-001] Layer L1
    🔷 class Order
       └─ Represents a customer order
    ⚙️  def get_order(order_id: int) -> Order
       └─ Fetch order by ID from database
```

---

### Export Types Tracked

| Symbol | Type | Example |
|--------|------|---------|
| 🔷 | `class` | `class User:` |
| ⚙️ | `function` | `def create_user(...):` |
| 📌 | `constant` | `MAX_RETRIES = 3` |
| 🏷️ | `type` | `type UserID = int` |

---

### For Atom Builders

When building an atom, you now have two resources:

1. **EXPORTS.md** — Human-readable tree of what's available
2. **--exports** command — Always up-to-date view of available exports

Before writing code, check:
```bash
# See what's already built
python scripts\build-runner\run.py --exports

# Then reference those modules, don't reimplement
from auth.services import create_user  # Already exists from AUTH-002
```

---

### For the Runner

The runner now:

1. **After each atom completes:**
   - Scans all output files for exports
   - Extracts function signatures, docstrings, parameters
   - Records to `exports.json` and `EXPORTS.md`

2. **Tracks:**
   - Python: functions, classes, constants (from module top-level)
   - TypeScript: exported functions, classes, types, interfaces

3. **Includes:**
   - Function signatures and parameter names
   - Return types and parameter types
   - Docstrings/JSDoc comments
   - File paths and line numbers

---

## Implementation Details

### ExportMapper class

Located in `scripts/build-runner/lib/exports.py`:

```python
class ExportMapper:
    def extract_python_exports(file_path) -> list[Export]
        # Extracts: def func(...), class ClassName, CONSTANT =
        
    def extract_typescript_exports(file_path) -> list[Export]
        # Extracts: export function, export const, export class, export type
        
    def record_atom_completion(atom, changed_files, completed_at)
        # Called after atom passes gates, records all exports
        
    def generate_tree_map() -> str
        # Human-readable tree of all exports by module
        
    def generate_dependency_tree() -> str
        # Shows what each atom exports and depends on
```

### Integration Points

In `run.py`:

```python
# After atom completes and passes gates:
mapper.record_atom_completion(atom, changed_files, now)

# Available for query:
mapper.get_available_exports(atom_id)
mapper.generate_tree_map()  # Show in UI or file
```

---

## Usage Examples

### Example 1: Building CORE-002 (needs CORE-001)

```bash
# Check what CORE-001 provides
build.bat --exports

# Output shows:
# [CORE-001] Layer L1
#   🔷 class SeenUrl
#   ⚙️ def dedup_check(url: str) -> bool
#   ⚙️ def record_seen_url(url: str)

# Now in CORE-002, you can use:
from core.models import SeenUrl
from core.services import dedup_check, record_seen_url
```

### Example 2: Building AUTH-002 (needs AUTH-001)

```bash
# See what AUTH-001 provides
build.bat --exports

# Output shows:
# [AUTH-001] Layer L1
#   🔷 class User
#   ⚙️ def hash_password(password: str) -> str
#   ⚙️ def verify_password(hash: str, password: str) -> bool

# Now in AUTH-002, you can import:
from auth.models import User
from auth.utils import hash_password, verify_password
```

### Example 3: Building API-001 (needs all backend services)

```bash
# Check all available endpoints and services
build.bat --exports

# Output shows:
# AUTH-002: def login(...) endpoint
# CORE-003: def get_orders(...) endpoint
# CONFIG-002: def load_config(...) function

# Use them in your API routes:
from auth.api import login
from core.api import get_orders
from config.services import load_config
```

---

## Benefits

✅ **No More Assumptions** — Every atom can see what's actually available before building  
✅ **Type Safety** — Function signatures prevent importing with wrong parameters  
✅ **Documentation** — Docstrings/JSDoc automatically captured and displayed  
✅ **Dependency Clarity** — Clear tree showing what depends on what  
✅ **Prevents Reimplementation** — Duplicate code across atoms eliminated  
✅ **Faster Building** — Less time wondering "does this exist or not?"  
✅ **Auto-Updated** — Map regenerates after each completed atom  

---

## Configuration

Edit `product.yaml` to customize export tracking:

```yaml
build:
  track_exports: true              # Enable export tracking (default: true)
  export_confidence_threshold: 0.8 # Confidence score for extracted exports
  include_private_exports: false   # Include _underscore functions
  track_types: [function, class, constant, type]  # What to track
```

---

## Future Enhancements

- [ ] Generate TypeScript `.d.ts` declaration files from Python exports
- [ ] Auto-generate API documentation from endpoint exports
- [ ] Track dependency breaking changes (when an export is removed)
- [ ] Generate import statements automatically
- [ ] Integration with DEPENDENCY_MAP.md for visual graphs
- [ ] Export change notifications (when AUTH-001 changes, notify dependents)

---

## Troubleshooting

### "No exports recorded yet"

**Cause:** No atoms have completed yet.  
**Fix:** Build your first atoms, then exports will appear.

### Missing exports from a completed atom

**Cause:** Export mapper didn't recognize the symbol (e.g., private function starting with `_`).  
**Fix:** Make sure the function/class is at module level (not nested), and doesn't start with underscore if `include_private_exports: false`.

### Exports not updating after rebuilding

**Cause:** Exports cache (`exports.json`) not being updated.  
**Fix:** 
```bash
# Force regeneration
rm logs/exports.json
build.bat --exports
```

---

## Summary

The build system now:

1. ✅ Checks all prerequisites (Python, CLI, PyYAML) automatically
2. ✅ Installs missing dependencies automatically
3. ✅ Runs full infrastructure health checks
4. ✅ Tracks and displays available functions/classes from each atom
5. ✅ Provides a tree map to prevent assumptions and duplicates

This eliminates the "does this function exist?" guessing game and ensures every atom knows exactly what it can use from previous atoms.
