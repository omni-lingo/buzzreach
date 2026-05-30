# BuzzReach

> Find the conversations where your customers are already asking for help. Draft the reply. You paste it.

**Status:** Concept / pre-MVP
**Author:** Sathish
**Last updated:** 2026-05-31

---

## 1. The Problem

Marketing is a universal, recurring, and increasingly expensive problem for every product. Paid ads keep getting more expensive and convert poorly for low-priced consumer products (proven first-hand: the IRS Penalty Calculator spent ~$80+ on Google Ads for **zero** conversions, while ParkingAppealMate made its only sales — 5-6 of them — **organically** through Google search).

The cheapest, highest-trust marketing channel is **organic community participation** — showing up on Reddit, forums, Quora, and blog comment sections where people are actively asking for help with the exact problem your product solves, and being genuinely helpful.

**But nobody keeps it up.** It is tedious, repetitive, and time-consuming:
- You have to *find* the right threads (out of thousands, across many platforms).
- You have to find them *early* (replies to hours-old threads get visibility; replies to old threads get buried).
- You have to *read* each one and decide if it's worth answering.
- You have to *write* a genuinely helpful reply that mentions your product without sounding like spam.
- You have to do this **every single day**, forever.

Solo founders and small teams quit after two weeks. The channel that works best is the one nobody can sustain.

### What BuzzReach is NOT solving
- **Directory submissions** (ProductHunt, G2, Capterra) — one-time form fills, ~30 total, just do them manually.
- **Fully automated posting** — explicitly out of scope (see Architectural Decisions).
- **Paid ad management** — different category.

---

## 2. The Solution

BuzzReach automates the **finding, filtering, and drafting** — the boring 90%. The human does the **reading and pasting** — the 10% that keeps it safe and authentic.

### The loop

```
1. CONFIGURE (once)
   - What you sell (product URL + one-line pitch)
   - Keywords your customers use ("can't pay IRS", "got CP14 notice")
   - Tone / persona / what to mention naturally

2. DISCOVER (every few hours, automatically)
   - Google time-filtered search finds FRESH conversations
   - Across Reddit, forums, Quora, blog comments — anywhere

3. FILTER (automatically)
   - Dedup against threads already seen / already answered
   - Keyword pre-filter (free, no AI)
   - AI relevance score: "Is this person seeking help? Is the angle already covered?"

4. DRAFT (automatically)
   - AI writes a genuinely helpful reply that mentions the product naturally
   - Reads existing comments so it doesn't repeat what's already been said

5. DELIVER
   - Push notification: "New opportunity in r/tax — draft ready"

6. HUMAN ACTS (manual, by design)
   - User taps -> reply copied to clipboard -> thread opens
   - User reads the thread, confirms it fits, pastes, posts
   - Or swipes to skip
```

**One sentence:** BuzzReach turns the endless grind of organic community marketing into a 10-minute-a-day paste job.

---

## 3. Why It's a Good SaaS

| Reason | Detail |
|--------|--------|
| **Universal pain** | Every product needs marketing; it keeps getting more expensive. This is a "shovel." |
| **Niche-agnostic** | Same tool, any niche — tax software, parking appeals, dog food, SaaS. Only the keywords change. |
| **Clean margins** | ~$7/user/month cost vs. ~$49/user price = ~85% margin. Google does the hard discovery work essentially for free. |
| **No platform risk** | We query Google, not Reddit/Quora APIs. A human pastes, so there is no bot fingerprint to detect. |
| **Self-validating** | Used in-house to market 3 owned products across 3 different niches — a live, real-numbers case study instead of fake testimonials. |
| **Recurring need** | The daily grind never ends, which is exactly what makes it subscription-worthy. |

### The dogfooding advantage
BuzzReach is built first as an **internal tool** to market the author's own products:
- **ParkingAppealMate** -> r/parking, r/legaladvice, parking/legal blog comments
- **IRS Penalty Calculator** -> r/tax, r/IRS, r/personalfinance
- **BuzzReach itself** -> r/SaaS, r/startups, r/indiehackers, r/marketing

**Floor outcome (even if never sold):** if it lifts the two existing products from ~$39/mo to a few hundred/mo, it pays for itself many times over at ~$50/mo running cost. Selling it is upside, not a requirement.

---

## 4. Architectural Decisions

### AD-1: Search Google, don't scrape platforms
**Decision:** Discovery is powered by Google search (with time filters), not per-platform scrapers or APIs.

**Why:**
- Every niche lives on *different* platforms (tax -> Avvo, TurboTax community; Shopify -> community.shopify.com; etc.). Maintaining a scraper per platform doesn't scale.
- Google already indexes all of them. One search interface = universal reach.
- Reddit's API has rate limits and policy risk; Quora has no API and walls scrapers. Google sidesteps both.
- Time filters (`tbs=qdr:h` / `qdr:d`) return only *fresh* conversations — critical because early replies get visibility.

**Trade-off:** Dependent on a search provider (SerpAPI / Google Custom Search) and their pricing. Page content still needs extraction after discovery (see AD-5).

### AD-2: Human-in-the-loop posting (never auto-post)
**Decision:** BuzzReach copies the draft to the clipboard and opens the thread. The **user** reads and pastes manually.

**Why:**
- Automated posting (even "human-paced") gets detected by anti-spam systems (BotDefense, PerimeterX, DataDome) via browser fingerprinting and behavioral patterns -> permanent account bans.
- A real human pasting into their own logged-in session is **indistinguishable from genuine activity** because it *is* genuine activity.
- Reading-before-posting also improves quality: the user skips drafts that don't fit, building trust instead of spamming.

**Trade-off:** Less "magic" than one-click automation. This is a deliberate quality/safety choice, and it's the reason the product survives long-term where fully-automated competitors get their users banned.

### AD-3: Server-side processing, thin mobile client
**Decision:** All heavy work (search, fetch, scoring, drafting) runs on a cheap server. The phone app is a notification inbox + clipboard + URL launcher.

**Why:**
- Phones kill background tasks (iOS ~30s limit; Android Doze). A reliable "scan every 2 hours" loop cannot live on a phone.
- LLM inference and search orchestration can't realistically run on-device.
- Keeps the app trivial to build (React Native, ~3 screens) and the intelligence centralized and improvable.

**Trade-off:** Requires a server (~$5-40/mo VPS) and centralized AI billing. Mitigated by the shared-work dedup in AD-4.

### AD-4: Cache our own actions, never cache the web
**Decision:** We do **not** store Reddit/the web. We store a tiny table of *what we've already seen and what angle was already covered*.

**Why:**
- Caching the web = millions of pages = infra we don't have and an AI bill that explodes.
- The only thing we need to avoid duplicate work is a record of our own activity: `url | niche | angle_covered | shown_to | timestamp`.
- A duplicate check is then a **SQL lookup ($0)** instead of a re-fetch + re-score ($0.03-0.10).
- This also solves the multi-user spam problem: if a thread's helpful angle is already covered (by us, or visible in existing comments), the AI simply doesn't surface it again — the same thing a thoughtful human would do.

**Storage scale:** ~1.2M rows/month at 1,000 users, ~200 bytes each = ~240MB/month. Trivial for SQLite/Postgres.

### AD-5: Lightweight content extraction, expand on demand
**Decision:** After Google returns a URL, extract content with a generic Readability-style extractor. Build site-specific parsers only for the platforms users actually care about.

**Why:**
- A generic extractor (à la Mozilla Readability) handles ~80% of pages (post body + comments) with zero per-site maintenance.
- The remaining ~20% gets custom parsers *driven by real demand*, not speculation.

**Trade-off:** Some pages extract imperfectly. Acceptable — the AI only needs enough context (the question + existing replies) to judge relevance and draft.

### AD-6: Tiered AI pipeline (cheap filter first, expensive draft last)
**Decision:** Layer the pipeline so the expensive model only runs on confirmed opportunities.

```
Google results
  -> dedup vs. seen_urls         (SQL, $0)
  -> keyword pre-filter          (string match, $0)
  -> relevance score (Haiku)     (~$0.003 each)
  -> draft reply (Sonnet)        (~$0.01 each, only for passes)
```

**Why:** Most candidates die in the free stages. AI cost stays at roughly ~$7/user/month instead of exploding.

**Trade-off:** Keyword pre-filter may miss oddly-worded threads. Acceptable for cost control; can tune keyword lists per customer.

---

## 5. Cost Model

### Per user (solo, ~5 search queries, 12 cycles/day)
| Step | Volume/day | Cost/month |
|------|-----------|------------|
| Google searches (time-filtered) | ~60 | included below |
| Dedup + keyword filter | all | $0 |
| Relevance scoring (Haiku) | ~tens | ~$2 |
| Draft replies (Sonnet) | ~tens | ~$3.60 |
| Search provider share | — | ~$1-3 |
| **Total per user** | | **~$7** |

### At ~1,000 users (with cross-user query dedup)
| Item | Cost/month |
|------|-----------|
| Search provider (deduped unique queries) | ~$75 |
| AI scoring (unique posts only) | ~$200-450 |
| AI drafting (per matched opportunity) | ~$300-600 |
| VPS + DB | ~$40 |
| **Total** | **~$400-1,100** |
| **Revenue @ $49 x 1,000** | **~$49,000** |

Scraping/discovery cost is *shared* across users (everyone searching "IRS penalty help" = one query). Only drafting scales per-user, and that's the cheap part.

---

## 6. Honest Risks & Limitations

| Risk | Reality |
|------|---------|
| **Distribution** | Getting users is the same marketing problem we're selling a fix for. Dogfooding is the answer, but it's still unproven at scale. |
| **Retention** | Users may churn once they realize they still must paste manually every day. The drafts must be good enough that pasting feels worth it. |
| **AI draft quality** | Generic AI replies get downvoted and called out. Niche tone-matching is hard. This is the make-or-break quality bar. |
| **"Reads like AI" backlash** | Communities increasingly flag AI-sounding replies, even genuine ones. Drafts must be human, specific, and lead with real help. |
| **Competition** | BizReply ($59/mo), Redreach ($29/mo), ReplyGuy, and ~10 others already exist. None have broken out — the market is small and churny. |
| **Search provider dependency** | Pricing/policy changes at SerpAPI/Google affect unit economics. |
| **Founder focus** | Author has 2 prior products at ~$39 total revenue. The real risk is building the tool instead of doing the marketing it enables. |

### The validation test (before over-investing)
The tool only matters if manual community marketing actually converts for these products. The honest first step is to **do it manually for ~2 weeks** on the IRS calculator + ParkingAppealMate, track threads found / replies posted / clicks / conversions. If manual works -> build BuzzReach to scale what already works. If it doesn't -> the tool wouldn't have helped anyway.

---

## 7. MVP Scope (proposed, ~2 weeks)

**Goal:** Get real reply opportunities onto the phone for ParkingAppealMate + IRS Calculator. Internal tool only — no landing page, no billing, no multi-tenant onboarding.

**In scope:**
- Config file per product (URL, pitch, keywords, tone) — JSON, not a UI
- Scheduled job (cron) running Google time-filtered searches
- `seen_urls` dedup table (SQLite)
- Keyword pre-filter
- Haiku relevance scoring + Sonnet draft generation
- Delivery: start with email/Slack digest (simplest), phone app later
- Each item includes: thread URL, why it matched, the draft reply

**Out of scope (for MVP):**
- Mobile app (use email/push digest first)
- Multi-user / accounts / billing
- Custom per-platform parsers (generic extractor only)
- Auto-posting (never)
- Directory submissions

**First success metric:** Author uses the daily digest to post helpful replies, and at least one product gets measurable referral clicks within 2 weeks.

---

## 8. Naming

Working name: **BuzzReach** ("buzz" = the conversations/mentions found; "reach" = the marketing payoff). Internal repo: `buzzreach`. Domain/name finalization deferred until there's a working tool and real usage — it's the least important decision and easily changed later.
