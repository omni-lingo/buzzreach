# BuzzReach Architecture

## Overview

BuzzReach is an AI-powered opportunity discovery platform. It scans the web for business opportunities, scores relevance with Claude AI, drafts personalized outreach messages, and delivers digests to users.

**Core Value:** Turn raw web signals into actionable, personalized opportunities at scale.

## Layered Architecture

The system is built in 5 layers following strict dependency rules:

```
┌─────────────────────────────────────┐
│  L5: Tests & Integration            │  Anti-silo validation
├─────────────────────────────────────┤
│  L4: Frontend                       │  User UI (React)
├─────────────────────────────────────┤
│  L3: API & Routes                   │  HTTP layer
├─────────────────────────────────────┤
│  L2: Services & Business Logic      │  Pure functions, no I/O
├─────────────────────────────────────┤
│  L1: Models & Database              │  Schema source of truth
└─────────────────────────────────────┘
```

**Rule:** L3 cannot import L3 or higher. L2 cannot import L3+. L1 stands alone.

## Module Map

### L1: Data Layer

**Models & Migrations**
- User (auth, API keys, settings)
- Opportunity (discovered URL, title, relevance score, status)
- SeenUrl (dedup table for discovery)
- AuditLog (compliance, security tracking)
- Metrics (product health)

**Contracts** (`contracts/`)
- `opportunity.json` — opportunity event schema
- `opportunity_event.py` — Python type definition
- `schema.json` — full database schema

### L2: Services (Pure Logic)

**Discovery Service**
- Builds search queries
- Calls search providers (Google, Bing, etc.)
- Returns raw URLs + snippets

**Content Extraction**
- Downloads page content
- Extracts structured data
- Returns JSON/text

**Filter Service**
- Dedup (SQL lookup against SeenUrl)
- Keyword pre-filter (fast reject)
- Returns deduplicated opportunities

**AI Service**
- Relevance scorer (Claude Haiku) — is this relevant to the user?
- Draft generator (Claude Sonnet) — write personalized outreach

**Pipeline Orchestrator**
- Chains the above services
- Handles tiering (score low-value early, stop)
- Returns ranked opportunities

**Delivery Service**
- Builds HTML digest
- Sends email or posts to Slack

**Scheduled Job Service**
- Cron entrypoint
- Orchestrates full scan + delivery flow

### L3: API Layer

**REST Endpoints**
- `POST /api/v1/opportunities` — list discovered opportunities
- `POST /api/v1/scan` — trigger immediate scan
- `GET /api/v1/settings` — user config
- `POST /api/v1/settings` — update config

**Authentication**
- API key validation middleware
- Rate limiting (token bucket)
- Audit logging

### L4: Frontend

**Dashboard**
- Live feed of discovered opportunities
- Filter & search
- Mark as "interested" / "archived"
- View scheduled digests

**Settings**
- Configure search parameters
- Set delivery schedule (daily/weekly)
- Choose delivery method (email/Slack)
- API key management

### L5: Tests

**Unit Tests** (pytest)
- Every function with logic
- Mocked I/O (database, API calls)

**Integration Tests** (pytest + live DB)
- End-to-end service flows
- Real database state changes

**E2E Tests** (Playwright)
- Critical user journeys
- Dashboard → scan → digest delivery

**Contract Tests**
- Verify cross-module boundaries
- Type checking (Pydantic, TypeScript)

## Data Flow

### Scan Flow (Triggered by cron or API)

```
[User Settings] 
    ↓
[Search Query Builder] → search terms
    ↓
[Search Provider] → raw URLs
    ↓
[Content Extractor] → structured data
    ↓
[Dedup Filter] → seen URLs filtered
    ↓
[Keyword Pre-Filter] → low-quality rejected
    ↓
[Relevance Scorer (Haiku)] → scored
    ↓
[Pipeline Orchestrator] → tiered, ranked
    ↓
[Opportunity Model] → persisted to DB
    ↓
[Digest Builder] → HTML email
    ↓
[Delivery Service] → email/Slack
```

### Live Dashboard Flow

```
[User Views Dashboard]
    ↓
[API /opportunities] 
    ↓
[Opportunity Model Query] → recent opportunities
    ↓
[Filter by User Settings] → relevant only
    ↓
[Return JSON]
    ↓
[Frontend Renders]
```

## Cross-Module Contracts

When a module's output feeds another module's input, both import a shared contract:

```python
# contracts/opportunities/opportunity_event.py
@dataclass
class OpportunityCreatedEvent:
    id: UUID
    user_id: UUID
    url: str
    title: str
    score: float
    created_at: datetime
```

The service module that *creates* this event defines it in `contracts/`.
The module that *consumes* it imports from `contracts/`, not directly from the service.

This catches contract breaks at import time, not runtime.

## Technology Stack

| Layer | Language | Framework |
|-------|----------|-----------|
| L1 | Python | SQLAlchemy + Alembic |
| L2 | Python | Pydantic + asyncio |
| L3 | Python | FastAPI |
| L4 | TypeScript | React + Tailwind |
| L5 | Python + TS | pytest + Playwright |

## Key Design Decisions

See [DECISIONS.md](DECISIONS.md) for rationale on:
- Why Haiku for scoring, Sonnet for drafting
- Why token-bucket rate limiting, not sliding-window
- Why dedup happens before scoring (cost vs. quality)
- Why scheduled jobs, not pub/sub

## Security & Compliance

**Authentication**
- API key in `X-Api-Key` header
- Keys hashed + salted in database
- No passwords (API-first)

**Audit Logging**
- Every action logged (create, read, update, delete)
- User ID, action, timestamp, IP
- Immutable append-only table

**Data Privacy**
- User URLs stored (necessary for dedup)
- Content extracted but not stored (score only)
- Retention policy: 90 days

## Scaling Considerations

**Current:** Single-process, in-memory rate limiter, sequential scanning

**Future:** 
- Async job queue (Celery + Redis)
- Persistent rate limiter (Redis)
- Horizontal pod scaling (Kubernetes)
- Caching layer (Redis)

Atoms are designed to be easy to scale without major refactors.

## Observability

**Metrics** (Prometheus)
- Scan duration, opportunities found, score distribution
- API latency, error rate, rate limit hits
- Cost per scan (API calls spent)

**Logging** (Structured JSON)
- Every service call logged with context
- Errors logged with stack traces
- Audit trail immutable

**Tracing** (OpenTelemetry)
- Full request → response tracing
- Service-to-service latency visibility

**Alerting**
- Scan failures → page oncall
- Score distribution shift → investigate quality
- Cost spike → investigate efficiency
