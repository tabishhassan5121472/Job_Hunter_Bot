# PRD — JobHunter v2

**Author**: BMAD PM agent
**Date**: 2026-04-30
**Source briefs**: `01-project-brief.md`, `02-market-research.md`
**Target release**: v2.0 (over 4 BMAD sprints)

## 1. Problem statement
The current JobHunter bot scrapes 11 sources but **3 return zero useful data** (Himalayas, RemoteOK, Jobicy), **2 return non-React noise** (Arbeitnow German jobs, Remotive irrelevant titles), and **1 surfaces fellow job-seekers as employers** (Reddit r/forhire). The single highest-signal channel — direct ATS feeds from remote-first companies (Vercel, Stripe, Supabase, etc.) — is **completely missing**. As a result, only ~5 of 15 daily opportunities are genuinely worth applying to.

## 2. Success criteria (measurable)
| KPI | Baseline | v2 target | Method |
|---|---:|---:|---|
| % of digest's top-15 that user marks "would apply" | ~30% | **≥70%** | manual rating after each run |
| New jobs / day from Tier-1 sources (WW Full-stack + ATS) | 0 | **≥25** | bot stats |
| False positives (post-review reject rate) | ~40% | **<15%** | tracker/applied.py rating |
| Time bot run → cover letter ready | ~10 min | **<3 min** | bot logs |
| Pakistan-friendly precision (top-10 hits) | unknown | **≥80%** | manual flag |

## 3. Personas (single-user product)
- **Tabish** — frontend dev, applies in evening (UTC+5), wants 5–7 strong leads/day, will tune scoring weights, will set API keys.

## 4. Epics & stories

### EPIC 1 — Source Quality Overhaul (P0, 1 sprint)
**Goal**: Replace dead sources with high-signal ones. Get to 25+ React jobs/day.

| ID | Story | Acceptance criteria |
|---|---|---|
| E1.S1 | Drop broken sources (Himalayas, RemoteOK API, Jobicy) | `config.yaml` has them disabled; fetcher modules archived to `sources/_deprecated/` |
| E1.S2 | Add WW Full-stack RSS source | `sources/boards/weworkremotely_fullstack.py` returns ≥25 React jobs/run |
| E1.S3 | Add Greenhouse ATS multi-company source | `sources/ats/greenhouse.py` iterates curated `ats_companies.yaml` (30 firms); returns ≥30 React jobs/run |
| E1.S4 | Add Lever ATS multi-company source | `sources/ats/lever.py`, same pattern |
| E1.S5 | Fix Reddit flair filter | Only posts with `link_flair_text == "Hiring"` accepted |
| E1.S6 | Curate ATS company list | `config/ats_companies.yaml` with 30 remote-first firms (Vercel, Stripe, Supabase, Cal.com, Hugging Face, Clerk, Linear, Webstudio, PostHog, Replicate, Hashnode, Codecov, GitLab, Discord, Cloudflare, Replit, Render, Fly.io, Railway, Neon, PlanetScale, Notion, Pipedream, RetoolHQ, Sentry, Atlassian, Lemon.io, Toptal, etc.) |

### EPIC 2 — Smart Scoring (P0, 1 sprint)
**Goal**: Replace keyword-counting with CV-aware semantic scoring.

| ID | Story | Acceptance criteria |
|---|---|---|
| E2.S1 | Add Pakistan-friendly classifier | New field `geo_friendly` ∈ {green, yellow, red}; red items hard-rejected |
| E2.S2 | Add timezone overlap detector | Detect "PST core hours / EST 9-5 / Asia welcome" → store `tz_match` ∈ {good, marginal, bad} |
| E2.S3 | Add seniority-fit detector | Match "senior/staff/principal" against user CV's stated 4+ yrs; reject "Lead 10+ yrs" |
| E2.S4 | Add rate extractor | Regex + LLM fallback to extract `min_rate_usd`, `max_rate_usd` from JD text |
| E2.S5 | Embedding-based JD↔CV match | Use Claude `claude-haiku-20240307` or local `all-MiniLM` for cosine similarity; weight 35% |
| E2.S6 | Rebalance scoring weights | New formula reflects multi-criteria: stack 30% / embedding 35% / freshness 15% / geo+tz 15% / rate 5% |

### EPIC 3 — Dedup & Tracking (P1, 0.5 sprint)
**Goal**: One job = one entry; user can mark applied/rejected/interview.

| ID | Story | Acceptance criteria |
|---|---|---|
| E3.S1 | Cross-source dedup | Hash on (normalized_company + normalized_title); same job from 2 sources collapsed |
| E3.S2 | Auto-populate tracker | After digest, top-N seeded as "to_review" rows in `applied.db` |
| E3.S3 | Feedback loop | `tracker mark <id> <good|bad|applied|interview|rejected>` updates a `feedback.jsonl` |
| E3.S4 | Use feedback in next run | Penalize companies/sources with multiple `bad` flags |

### EPIC 4 — Cover Letter Quality (P1, 0.5 sprint)
**Goal**: Drafts don't need editing more than 2 minutes.

| ID | Story | Acceptance criteria |
|---|---|---|
| E4.S1 | Inject portfolio URLs | Cover letter references 2-3 most relevant deployed Netlify projects per JD |
| E4.S2 | Match-evidence inclusion | Letter cites specific JD requirements + user's matching experience |
| E4.S3 | Tone variants | `--tone formal|casual|enthusiastic` flag |
| E4.S4 | A/B prompt selection | Log which prompts get applied with — adjust over time |

### EPIC 5 — Multi-Agent Reasoning (P2, 1 sprint) — *this is "Option B" from BMAD plan*
**Goal**: Embed BMAD-style multi-agent evaluation in scoring.

| ID | Story | Acceptance criteria |
|---|---|---|
| E5.S1 | Define agent roles | Analyst (fit) / Researcher (company) / Strategist (pitch angle) — 3 prompts |
| E5.S2 | Run agents only on top-20 | Cost control — full multi-agent only for finalists |
| E5.S3 | Aggregate agent verdicts | Score adjustment + structured `agent_verdict.md` per opportunity |
| E5.S4 | Caching | Re-runs reuse agent verdicts via 7-day TTL on company-level keys |

## 5. Out-of-scope (v2)
- LinkedIn scraping (ToS)
- Auto-applying
- Web UI / dashboard
- Email/SMS delivery (Telegram already works)
- Hosting beyond launchd

## 6. Dependencies & risks
- **Anthropic API key required** for E2.S5, E4, E5. User has one (per HANDOFF.md, `tabishhassan01998@gmail.com`).
- **Cost guard**: cap LLM spend at $0.50/run via `top_n` + Haiku for rerank, Sonnet only for top-5 cover letters.
- **Greenhouse/Lever rate limits**: stay under 30 req/min; cache responses 1h.

## 7. Sprint sequence
1. **Sprint 1** — EPIC 1 (sources) — most user-visible win
2. **Sprint 2** — EPIC 2 (smart scoring) — biggest precision lift
3. **Sprint 3** — EPIC 3 + EPIC 4 — feedback loop closes
4. **Sprint 4** — EPIC 5 — multi-agent depth (Option B)

→ Next: Architect designs the technical approach. See `04-architecture.md`.
