# Build State

> Human-readable progress index. The runner regenerates this from `state/build_state.json`
> (the machine-readable source of truth). All atoms start `pending`.
> Build order is topological by `Depends on`; layers run L1 → L5.

## infra
- [ ] INFRA-001 Project scaffold & settings

## auth
- [ ] AUTH-001 User model & API key contract
- [ ] AUTH-002 JWT service (sign, verify, refresh)
- [ ] RATE-001 Rate limiter (token bucket, in-memory)
- [ ] AUDIT-002 Audit logging service

## core
- [ ] CORE-001 Database base, engine & session
- [ ] CORE-002 SeenUrl model (own-actions dedup table)
- [ ] CORE-003 Opportunity model + contract
- [ ] CORE-004 AuditLog model (compliance & security)
- [ ] CORE-005 Metrics model (product health tracking)

## config
- [ ] CFG-001 Product config contract
- [ ] CFG-002 Config loader service

## discovery
- [ ] DISC-001 Search query builder
- [ ] DISC-002 Search provider client
- [ ] DISC-003 Discovery service

## extraction
- [ ] EXT-001 Content extractor

## filter
- [ ] FILT-001 Dedup service (SQL lookup)
- [ ] FILT-002 Keyword pre-filter

## ai
- [ ] AI-001 Anthropic client wrapper
- [ ] AI-002 Relevance scorer (Haiku)
- [ ] AI-003 Draft generator (Sonnet)

## pipeline
- [ ] PIPE-001 Tiered pipeline orchestrator

## delivery
- [ ] DELIV-001 Digest builder
- [ ] DELIV-002 Digest sender (email / Slack)

## jobs
- [ ] JOB-001 Scheduled scan job (cron entrypoint)

## api
- [ ] API-001 Opportunities API

## observability
- [ ] OBSERV-001 Observability service (metrics & instrumentation)
- [ ] MONITOR-001 Health monitor & alerting

## dashboard
- [ ] DASH-001 Metrics dashboard (user sees what's working)

## tests
- [ ] TEST-001 End-to-end integration (anti-silo)
