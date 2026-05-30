# BuzzReach

**AI-powered opportunity discovery and outreach automation for business growth.**

BuzzReach intelligently scans the web for business opportunities, scores relevance with Claude AI, drafts personalized outreach, and delivers digests via email or Slack.

## Quick Start

```bash
# Initialize environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your API keys

# Run build
python scripts/build-runner/run.py --status
```

## Architecture

- **L1 Models** — Database schema, contracts
- **L2 Services** — Business logic (discovery, filtering, scoring, generation)
- **L3 API** — REST endpoints
- **L4 Frontend** — Dashboard & settings UI
- **L5 Tests** — Integration & E2E tests

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.

## Build System

Uses atom-based development with Claude Code. Each atom is a complete, testable unit that follows strict build rules.

```bash
# View build progress
python scripts/build-runner/run.py --status

# Build next ready atom
python scripts/build-runner/run.py

# Build specific atom
python scripts/build-runner/run.py --atom AUTH-001

# Dry run (show wave plan)
python scripts/build-runner/run.py --dry-run
```

See [BUILD_RULES.md](BUILD_RULES.md) for code requirements.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design & module map
- [BUILD_RULES.md](BUILD_RULES.md) — Code standards & gates
- [BUILD_STATE.md](BUILD_STATE.md) — Current build progress
- [API_SURFACE.md](API_SURFACE.md) — REST API endpoints (auto-generated)
- [SCHEMA.md](SCHEMA.md) — Database schema (auto-generated)
- [DECISIONS.md](DECISIONS.md) — Architecture decision records

## Development

### Prerequisites
- Python 3.11+
- Claude CLI (`npm install -g @anthropic-ai/claude-code`)
- Git

### Workflow

1. Pick an atom from [BUILD_STATE.md](BUILD_STATE.md)
2. Run `python scripts/build-runner/run.py --atom {ATOM_ID}`
3. Claude Code builds the atom end-to-end
4. Tests pass, code committed, docs updated, pushed to GitHub automatically

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Project Structure

```
BuzzReach/
├── scripts/build-runner/      # Build automation (runner)
│   ├── run.py                 # Main orchestrator
│   ├── build.bat              # Windows entry point
│   ├── lib/                   # Runner libraries
│   │   ├── executor.py        # Atom builder
│   │   ├── gates.py           # Build validation gates
│   │   ├── github.py          # GitHub integration
│   │   └── ...
│   └── hooks/                 # Post-layer scripts
├── src/                       # Product code
│   ├── api/                   # L3: REST API
│   ├── services/              # L2: Business logic
│   ├── models/                # L1: Database models
│   └── ...
├── tests/                     # L5: Tests
├── atoms/                     # Atom specifications
├── contracts/                 # Cross-module contracts
├── state/                     # Build state (gitignored)
├── logs/                      # Build logs (gitignored)
├── product.yaml              # Build config
├── BUILD_RULES.md            # Code standards (enforced)
├── BUILD_STATE.md            # Build progress
└── ARCHITECTURE.md           # System design
```

## Status

**Build Progress:** See [BUILD_STATE.md](BUILD_STATE.md)

| Module | Atoms | Status |
|--------|-------|--------|
| infra | 1 | pending |
| auth | 4 | pending |
| core | 5 | pending |
| config | 2 | pending |
| discovery | 3 | pending |
| extraction | 1 | pending |
| filter | 2 | pending |
| ai | 3 | pending |
| pipeline | 1 | pending |
| delivery | 2 | pending |
| jobs | 1 | pending |
| api | 1 | pending |
| observability | 2 | pending |
| dashboard | 1 | pending |
| tests | 1 | pending |

**Total:** 30 atoms | **Complete:** 0 | **In Progress:** 0

## License

Proprietary — BuzzReach © 2025

## Contact

For questions or feedback, reach out to the team at omnilingoapp@gmail.com
