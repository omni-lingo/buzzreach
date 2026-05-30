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

## frontend
- [ ] FE-001 Settings & Configuration UI
- [ ] FE-002 Opportunities Dashboard (live feed)

## onboarding
- [ ] ONBOARD-001 Signup / Registration Flow
- [ ] ONBOARD-002 Email Verification Service
- [ ] ONBOARD-003 First-Run Setup Wizard
- [ ] ONBOARD-004 Password Reset / Account Recovery

## billing
- [ ] BILL-001 Stripe Payment Integration
- [ ] BILL-002 Subscription Plans & Management
- [ ] BILL-003 Usage Metering & Quotas
- [ ] BILL-004 Customer Portal

## admin
- [ ] ADMIN-001 Team Management (members, roles, invites)
- [ ] ADMIN-002 Workspace Management

## features
- [ ] FEAT-001 Draft Editor & Customization
- [ ] FEAT-002 Advanced Filtering System
- [ ] FEAT-003 Post-Action Tracking & Conversion Analytics
- [ ] FEAT-004 Search Profiles & Scheduling
- [ ] FEAT-005 Tone Detection
- [ ] FEAT-006 Bulk Actions (dismiss, regenerate)

## mobile
- [ ] MOBILE-001 Mobile App (React Native) Base Setup
- [ ] MOBILE-002 Push Notifications (iOS/Android)
- [ ] MOBILE-003 Mobile Opportunity Feed
- [ ] MOBILE-004 One-Click Copy & URL Launcher

## extensions
- [ ] EXT-001 Browser Extension (Chrome/Firefox/Edge)
- [ ] EXT-002 Slack Bot Integration
- [ ] EXT-003 Webhook Delivery Handler

## parsers
- [ ] PARSE-001 Reddit-Specific Parser
- [ ] PARSE-002 Quora-Specific Parser
- [ ] PARSE-003 Blog/Forum Comment Parser

## site
- [ ] SITE-001 Landing Page & Marketing Website
- [ ] SITE-002 Documentation Site

## quality
- [ ] QUALITY-001 Dark Mode Theme
- [ ] QUALITY-002 Keyboard Shortcuts
- [ ] QUALITY-003 Draft Templates Library
- [ ] QUALITY-004 Niche Bundles (pre-configured)

## desktop
- [ ] DESKTOP-001 Electron Desktop App
